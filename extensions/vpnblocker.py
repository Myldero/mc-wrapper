"""
An extension that uses the VPN Blocker API to detect VPNs and act upon it
"""

from base_extension import BaseExtension
import requests


class VPNBlocker(BaseExtension):

    def __init__(self, *args):
        super().__init__(*args)
        self.name = "vpnblocker"
        self.insecure_url = "http://api.vpnblocker.net/v2"
        self.secure_url = "https://api.vpnblocker.net/v2"

    def on_player_join(self, player):

        # TODO: Add database to minimize use

        if self.config['api_key']:
            response = requests.get(self.secure_url + "/json/{}/{}".format(player.ip, self.config['api_key'])).json()
        else:
            response = requests.get(self.insecure_url + "/json/{}".format(player.ip)).json()

        if "error" in response:
            return

        is_vpn = response["host-ip"]

        if is_vpn:
            for cmd in self.config["commands"]:
                cmd = cmd.replace("{{player}}", player.username)
                self.wrapper.server.send(cmd)

    def on_reload(self):

        try:
            self.config = self.load_json_config(name=self.name, default={
                'enabled': False,
                'api_key': '',
                'commands': [
                    'kick {player} Your IP address was detected as a VPN'
                ]
            })
        except Exception:
            pass
