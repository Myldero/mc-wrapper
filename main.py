import glob
import inspect
from subprocess import Popen, PIPE
import time

import threading
import re
import os
import importlib
from textwrap import dedent

import server_commands
from base_extension import BaseExtension


class Wrapper:
    def __init__(self):

        self.server = Server(self)

        self.extensions = {}
        self.full_reload()
        self.server.start()

    def full_reload(self):

        for ext in self.extensions.values():
            ext.stop()

        for ext in self.extensions.values():
            ext.wait_stop()

        self.extensions = {}

        for path in glob.iglob("extensions/*"):
            path = path.split(".")[0].replace("/", ".").replace("\\", ".")
            importlib.invalidate_caches()
            extension_module = importlib.import_module(path)
            importlib.reload(extension_module)

            for name, obj in inspect.getmembers(extension_module):
                if inspect.isclass(obj) and issubclass(obj, BaseExtension):
                    ext = obj(self)
                    if ext.name is not None:
                        self.extensions[ext.name] = ext

        self.reload()

    def reload(self):
        """Reloads config"""

        for folder in ("config", "logs", "data"):
            try:
                os.makedirs(folder)
            except OSError:
                pass

        try:
            server_config = BaseExtension.load_json_config(name="server", default={
                'file_name': 'server.jar',
                'file_path': '.',
                'args': [
                    "-Xmx1024M",
                    "-Xms1024M"
                ],
                'restart_message': 'The server is restarting!',
                'backups_folder': './backups/'
            })
        except Exception:
            if self.server.config is None:
                exit()
        else:
            if not os.path.isfile(os.path.join(server_config["file_path"], server_config["file_name"])):
                print("Can't find minecraft jar file")
                if self.server.jar is None:
                    exit()
            else:
                self.server.config = server_config

        for ext in self.extensions.values():
            ext.on_reload()
            if not ext.enabled and ext.config['enabled']:
                ext.start()
            elif ext.enabled and not ext.config['enabled']:
                ext.stop()

        importlib.reload(server_commands)
        server_commands.wrapper = self


class Server:
    def __init__(self, wrapper):
        self.wrapper = wrapper

        self.config = None
        self.running = False
        self.list = []
        self.version = "Unknown"
        self.stdout_queue = []
        self.has_stopped = False
        self.properties = {}
        self.jar = None
        self.uuids = {}

    def start(self):

        del self.list[:]  # Empty player list without creating new object

        cmd = ["java"] + self.config["args"] + ["-jar", self.config["file_name"], "nogui"]
        self.jar = Popen(cmd, stdin=PIPE, stdout=PIPE, universal_newlines=True, bufsize=1, cwd=self.config['file_path'])

        threading.Thread(target=self.stdout).start()
        self.has_stopped = False

        try:
            with open(os.path.join(self.config['file_path'], "server.properties"), 'r') as f:
                for line in f:
                    if line.startswith("#"): continue

                    a, b = line.split("=")
                    self.properties[a.strip()] = b.strip()

        except Exception as e:
            print(e)

    def send(self, cmd, result=False):
        cmd = cmd.rstrip()

        if cmd == "":
            return

        with open('logs/sent.log', 'a') as f:
            f.write(cmd + "\n")

        if cmd.startswith("!"):

            t = cmd[1:].split()

            if t[0] in self.wrapper.extensions.keys():
                func = self.wrapper.extensions[t[0]].on_server_command

                try:
                    func(*t[1:])
                except Exception:
                    print(dedent(func.__doc__).strip())
            else:

                try:
                    func = getattr(server_commands, "cmd_" + t[0])
                except (NameError, AttributeError):
                    print("Unknown command. Try !help")
                else:
                    try:
                        func(*t[1:])
                    except Exception:
                        print(dedent(func.__doc__).strip())

        elif self.jar.poll() is None and self.running:

            if result is True:
                t = StringObject()
                self.stdout_queue.append(t)

            if cmd == "stop":
                self.has_stopped = True

            self.jar.stdin.write(cmd + "\n")

            if result is True:
                while t.value is None:
                    time.sleep(0.1)

                return t.value

    def stdout(self):
        for line in iter(self.jar.stdout.readline, ""):
            line = line.rstrip()
            print(line)

            threading.Thread(target=self.regex, args=[line]).start()

        self.jar.stdout.close()
        # TODO: Check if jar stopped correctly or not

    def get_sender(self, namestring):
        for player in self.list:
            if player.username in namestring:
                return player
        return None

    def get_online_player(self, username):
        for player in self.list:
            if player.username == username:
                return player
        return None

    def regex(self, line):

        for ext in self.wrapper.extensions.values():
            if ext.enabled:
                ext.on_server_all_messages(line)

        text = re.search(r'^\[[0-9]{2}:[0-9]{2}:[0-9]{2}\] \[[A-Za-z0-9# ]+/INFO\]: (.*)$', line)

        if text is None:
            return

        text = text.group(1)

        for ext in self.wrapper.extensions.values():
            if ext.enabled:
                ext.on_server_message(text)

        if re.search(r'^<', text):

            namestring, message = re.findall(r'^<(.+)> (.*)$', text)[0]
            sender = self.get_sender(namestring)

            for ext in self.wrapper.extensions.values():
                if ext.enabled:
                    ext.on_player_message(sender, message)

        elif re.search(r'^UUID of player [A-Za-z0-9_]+ is [a-z0-9\-]+', text):

            username, uuid = re.findall(r'^UUID of player ([A-Za-z0-9_]+) is ([a-z0-9\-]+)', text)[0]

            self.uuids[username] = uuid

        elif re.search(r'^[A-Za-z0-9_]+ lost connection', text):

            username = re.findall(r'^([A-Za-z0-9_]+) lost connection', text)[0]
            player = self.get_online_player(username)

            if player in self.list:
                self.list.remove(player)

            for ext in self.wrapper.extensions.values():
                if ext.enabled:
                    ext.on_player_leave(player=player)

        elif re.search(r'^[A-Za-z0-9_]+\[/[0-9\.:]+\] logged in', text):

            username, ip = re.findall(r'^([A-Za-z0-9_]+)\[/([0-9\.:]+)\] logged in', text)[0]
            ip = ip.split(":")[0]
            while username not in self.uuids:
                time.sleep(0.1)
                print("Waited!")
            uuid = self.uuids[username]

            player = OnlinePlayer(username=username, uuid=uuid, ip=ip)

            if not any(player.username == i.username for i in self.list):
                self.list.append(player)

            for ext in self.wrapper.extensions.values():
                if ext.enabled:
                    ext.on_player_join(player=player)

        elif re.search(r'^Stopping ', text):
            self.running = False
            del self.list[:]

            for ext in self.wrapper.extensions.values():
                if ext.enabled:
                    ext.on_server_stop()

            if not self.has_stopped:
                time.sleep(5)
                self.send("!start")

        elif re.search(r'^Done \(', text):
            self.running = True

            for ext in self.wrapper.extensions.values():
                if ext.enabled:
                    ext.on_server_start()

        elif re.search(r'^Starting minecraft server version', text):
            self.version = re.findall(r'^Starting minecraft server version (.*)$', text)[0]
        elif re.search(r'^(You whisper|Kicked|Banned|Unbanned|handleDisconnection)', text):
            pass
        else:
            t = re.search(r'^\[[0-9]{2}:[0-9]{2}:[0-9]{2}\] \[Server thread/INFO\]: ([A-Za-z0-9].*)$', line)
            if t and len(self.stdout_queue) > 0:
                p = self.stdout_queue.pop(0)
                p.value = t.group(1)


class StringObject:
    def __init__(self):
        self.value = None

    def __repr__(self):
        return "StringObject(\"{}\")".format(self.value)


class OnlinePlayer:
    def __init__(self, username, ip=None, uuid=None):
        self.username = username
        self.uuid = uuid
        self.ip = ip


if __name__ == "__main__":
    wrapper = Wrapper()

    try:
        while True:
            wrapper.server.send(input())

    except KeyboardInterrupt:
        pass

    finally:

        wrapper.server.send("stop")


        for _ext in wrapper.extensions.values():
            if _ext.enabled:
                _ext.stop()

        wrapper.server.jar.wait()
        # TODO: Send stop signal to jar if it doesn't stop after timeout of 5(?) seconds
