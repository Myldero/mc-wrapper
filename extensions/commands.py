"""
An extension to make it easy to add custom chat commands to your server
"""

import importlib
import re
import os

from base_extension import BaseExtension


class Commands(BaseExtension):

    def __init__(self, *args):
        super().__init__(*args)
        self.name = "commands"

    def on_player_message(self, sender, message):

        for exp in self.config["commands"]:

            match = re.search(exp["match"], message)

            if match is not None:

                match = [match.group(0)] + list(match.groups())

                special_characters = zip(("\\", "\"", "\'"), ("\\\\", "\\\"", "\\\'"))  # Important order
                for i in range(len(match)):  # Escape special characters
                    for key, value in special_characters:
                        match[i] = match[i].replace(key, value)

                if exp["type"] == "command":

                    for command in exp["run"]:
                        cmd = command

                        for i in range(len(match)):
                            cmd = cmd.replace("{{{}}}".format(i), match[i])

                        cmd = cmd.replace("{{{}}}".format("sender"), sender.username)

                        self.wrapper.server.send(cmd)

                elif exp["type"] == "function":
                    exp["run"](sender, match)

    def on_reload(self):

        try:
            config = self.load_json_config(name=self.name, default={
                "enabled": False,
                "commands": [
                    {
                        "type": "command",
                        "match": "^!send ([A-Za-z0-9_]+) (.*)",
                        "run": [
                            "tellraw {1} {\"text\":\"{sender} says {2}\"}"
                        ]
                    },
                    {
                        "type": "function",
                        "match": "([0-9]+)\\+([0-9]+)",
                        "run": "do_math"
                    },
                    {
                        "type": "function",
                        "match": "^\\.tps$",
                        "run": "tps"
                    }
                ]

            })
        except Exception:
            pass
        else:
            if not config["enabled"]:
                self.config = config
                return

            if not os.path.isfile("commands.py"):
                file_s = '''\
"""
A file for putting in custom functions for regex commands

sender is a string containing the username of the player who sent the command
match is a list containing strings matching to {0}, {1}, {2}, etc..
"""
from time import time, sleep
import re, requests

def do_math(sender, match):

    t = int(match[1]) + int(match[2])

    wrapper.server.send("say is equal to {}".format(t))


def tps(sender, match):
    def get():
        t = wrapper.server.send("time query gametime", result=True)
        a = re.findall(r'The time is ([0-9]+)', t)
        if a:
            return int(a[0])
        return None

    a = time()
    start_time = get()
    sleep(5 - time() + a) # Runs at a bit less than 5 seconds so it's precise
    end_time = get()

    delta = end_time - start_time

    wrapper.server.send("say The server TPS is {}".format(round(delta/5, 1)))
'''

                with open('commands.py', 'w') as f:
                    f.write(file_s)

            try:
                commands = importlib.import_module("commands")
                commands.wrapper = self.wrapper

                for cmd in config["commands"]:
                    cmd["match"] = re.sub(r"{([0-9]+)}", r'(?:\\\1)', cmd["match"])
                    cmd["match"] = re.compile(cmd["match"])

                    if cmd["type"] == "function":
                        cmd["run"] = getattr(commands, cmd["run"])
                    elif cmd["type"] == "command":
                        for i in range(len(cmd["run"])):
                            cmd["run"][i] = cmd["run"][i].replace("\n", "\\n")
            except Exception as e:
                print("An error occurred when reloading custom commands extension")
                print(e)
            else:
                self.config = config
