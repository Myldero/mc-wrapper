"""
An extension using TheMrGong's API for detecting MCLeaks accounts and acting upon it
"""

from base_extension import BaseExtension
import requests


class MCLeaks(BaseExtension):

    def __init__(self, *args):
        super().__init__(*args)
        self.name = "mcleaks"
        self.url = "https://mcleaks.themrgong.xyz/api/v3"

    def on_player_join(self, player):
        response = requests.get(self.url + "/isuuidmcleaks/{}".format(player.uuid)).json()

        if "error" in response:
            return

        is_mcleaks = response["isMcleaks"]

        if is_mcleaks:
            for cmd in self.config["commands"]:
                cmd = cmd.replace("{{player}}", player.username)
                self.wrapper.server.send(cmd)

    def on_reload(self):

        try:
            self.config = self.load_json_config(name=self.name, default={
                'enabled': False,
                'commands': [
                    'kick {player} Your account was detected as compromised'
                ]
            })
        except Exception:
            pass
