"""
A spamfilter that tries to prevent players from spamming the chat
"""

from time import time

from base_extension import BaseExtension


class SpamFilter(BaseExtension):

    def __init__(self, *args):
        super().__init__(*args)
        self.name = "spamfilter"
        self.players = {}

    def on_player_message(self, sender, message):
        sender = sender.username

        if sender not in self.players:
            self.players[sender] = {'message': message, 'timestamp': time(), 'count': 0, 'warns': 0, 'kicks': 0}

        else:
            cmds = None

            if self.players[sender]['timestamp'] + 0.03 > time():
                self.players[sender]['count'] += 3

            elif self.players[sender]['timestamp'] + 5 > time() and self.players[sender]['message'] == message:
                self.players[sender]['count'] += 1

            elif self.players[sender]['timestamp'] + 0.05 * len(message) + 0.5 > time():
                self.players[sender]['count'] += 1

            if self.players[sender]['count'] >= 2:
                self.players[sender]['count'] = 0
                self.players[sender]['warns'] += 1

                if self.players[sender]['warns'] > self.config["warns_before_kick"]:

                    self.players[sender]['warns'] = 0
                    self.players[sender]['kicks'] += 1

                    if self.players[sender]['kicks'] > self.config["kicks_before_ban"]:
                        cmds = self.config["ban_cmd"]
                    else:
                        cmds = self.config["kick_cmd"]
                else:
                    cmds = self.config["warn_cmd"]

            if cmds is not None:
                for cmd in cmds:
                    cmd = cmd.replace("\n", "\\n")
                    self.wrapper.server.send(cmd.replace("{{{}}}".format("sender"), sender))

            if self.players[sender]['timestamp'] + 10 <= time():
                self.players[sender]['count'] = 0

            if self.players[sender]['timestamp'] + self.config["warn_cooldown"] <= time():
                self.players[sender]['warns'] = 0

            if self.players[sender]['timestamp'] + self.config["kick_cooldown"] <= time():
                self.players[sender]['kicks'] = 0

            self.players[sender]['message'] = message
            self.players[sender]['timestamp'] = time()

    def on_reload(self):

        try:
            self.config = self.load_json_config(name=self.name, default={
                "enabled": False,
                "kicks_before_ban": 2,
                "warns_before_kick": 2,
                "warn_cooldown": 30,
                "kick_cooldown": 300,
                "warn_cmd": ["tell {sender} Please watch the spam!"],
                "kick_cmd": ["kick {sender} Please watch the spam!"],
                "ban_cmd": ["ban {sender} Spam."]
            })
        except Exception:
            pass
