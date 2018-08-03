from subprocess import Popen, PIPE
from time import sleep, time

import threading, re, os, importlib

import config, server_commands
from extensions import buycraft, votifier, scheduler, mcleaks, spamfilter


class Wrapper:
    def __init__(self):
        self.config = None

        self.server = Server(self)

        self.extensions = {"buycraft": buycraft.Buycraft(self), "votifier": votifier.Votifier(self), "scheduler": scheduler.Scheduler(self)}

        self.server.start()

        for extension in self.extensions.values():
            extension.start()


    def reload(self):
        '''Reloads config'''

        conf = None
        try:
            conf = config.get(self)

        except Exception as e:
            print("There was an error in the config file!")
            print(e)
            if self.config == None:
                exit()

        else:
            self.config = conf

            for extension in self.extensions.values():
                extension.setConfig(self.config)

            self.server.config = self.config["server"]

            importlib.reload(server_commands)
            server_commands.wrapper = self

            importlib.reload(spamfilter)
            spamfilter.wrapper = self
            spamfilter.config = self.config["spamfilter"]



class Server:
    def __init__(self, wrapper):
        self.wrapper = wrapper

        self.running = False
        self.list = []
        self.version = "Unknown"
        self.stdout_queue = []
        self.has_stopped = False
        self.properties = {}


    def start(self):

        self.wrapper.reload()

        del self.list[:] # Empty player list without creating new object

        self.cmd = [i.format(**self.config) for i in ("java", "-Xmx{memory}M", "-Xms{memory}M", "-jar", "{file_name}", "nogui")]
        self.jar = Popen(self.cmd, stdin=PIPE, stdout=PIPE, universal_newlines=True, bufsize = 1, cwd=self.config['file_path'])

        threading.Thread(target=self.stdout).start()
        self.has_stopped = False

        try:
            with open(os.path.join(self.config['file_path'], "server.properties"), 'r') as f:
                for line in f:
                    if line.startswith("#"): continue

                    a, b = line.split("=")
                    self.properties[a] = b.rstrip()

        except Exception:
            pass


    def send(self, cmd, result=False):
        cmd = cmd.rstrip()

        if cmd == "":
            return


        with open('logs/sent.log', 'a') as f:
            f.write(cmd + "\n")



        if cmd.startswith("!"):

            t = cmd[1:].split()
            try:
                func = getattr(server_commands, "cmd_"+t[0])
            except (NameError, AttributeError):
                print("Unknown command. Try !help")
            else:
                try:
                    func(*t[1:])
                except Exception:
                    print(func.__doc__)




        elif self.jar.poll() == None and self.running:

            if result == True:
                t = StringObject()
                self.stdout_queue.append(t)

            if cmd == "stop":
                self.has_stopped = True

            self.jar.stdin.write(cmd + "\n")


            if result == True:
                while t.value == None:
                    sleep(0.1)

                return t.value


    def stdout(self):
        for line in iter(self.jar.stdout.readline, ""):
            line = line.rstrip()
            print(line)

            threading.Thread(target=self.regex, args=[line]).start()



        self.jar.stdout.close()

    def get_sender(self, namestring):
        for name in self.list:
            if name in namestring:
                return name
        return None

    def regex(self, line):

        text = re.search(r'^\[[0-9]{2}\:[0-9]{2}\:[0-9]{2}\] \[[A-Za-z ]+/INFO\]\: (.*)$', line)

        if text == None:
            return

        text = text.group(1)

        if re.search(r'^<', text):

            t, message = re.findall(r'^<(.+)> (.*)$', text)[0]
            sender = self.get_sender(t)


            if self.wrapper.config["spamfilter"]["enabled"]:
                spamfilter.on_message(sender, message)

            for exp in self.wrapper.config["commands"]:

                match = re.search(exp["match"], message)

                if match != None:

                    match = [match.group(0)] + list(match.groups())

                    special_characters = zip(("\\", "\"", "\'"), ("\\\\", "\\\"", "\\\'")) # Important order
                    for i in range(len(match)):  # Escape special characters
                        for key, value in special_characters:
                            match[i] = match[i].replace(key, value)

                    if exp["type"] == "command":

                        for command in exp["run"]:
                            cmd = command

                            for i in range(len(match)):
                                cmd = cmd.replace("{{{}}}".format(i), match[i])

                            cmd = cmd.replace("{{{}}}".format("sender"), sender)

                            self.send(cmd)

                    elif exp["type"] == "function":
                        exp["run"](sender, match)


        elif re.search(r'^[A-Za-z0-9_]+ lost connection', text):

            t = re.findall(r'^([A-Za-z0-9_]+) lost connection', text)[0]
            if t in self.list:
                self.list.remove(t)


        elif re.search(r'^[A-Za-z0-9_]+\[/[0-9\.:]+\] logged in', text):

            t = re.findall(r'^([A-Za-z0-9_]+)\[/[0-9\.:]+\] logged in', text)[0]
            self.list.append(t)
            sleep(0.5)

            if self.wrapper.config["mcleaks"]["enabled"] and mcleaks.check(t):
                self.send("kick {} Your account was detected as compromised".format(t))

        elif re.search(r'^Stopping ', text):
            self.running = False
            del self.list[:]

            if not self.has_stopped:
                sleep(5)
                self.send("!start")

        elif re.search(r'^Done \(', text):
            self.running = True

        elif re.search(r'^Starting minecraft server version', text):
            t = re.findall(r'^Starting minecraft server version (.*)$', text)[0]
            self.version = t
        elif re.search(r'^(You whisper|Kicked|Banned|Unbanned|handleDisconnection)', text):
            pass
        else:
            t = re.search(r'^\[[0-9]{2}\:[0-9]{2}\:[0-9]{2}\] \[Server thread/INFO\]\: ([A-Za-z0-9].*)$', line)
            if t and len(self.stdout_queue) > 0:
                p = self.stdout_queue.pop(0)
                p.value = t.group(1)




class StringObject:
    def __init__(self):
        self.value = None

    def __repr__(self):
        return "StringObject(\"{}\")".format(self.value)




if __name__ == "__main__":
    wrapper = Wrapper()

    try:
        while True:
            wrapper.server.send(input())

    except KeyboardInterrupt:
        pass

    finally:

        wrapper.server.send("stop")

        for extension in wrapper.extensions.values():
            extension.stop()

        wrapper.server.jar.wait()
