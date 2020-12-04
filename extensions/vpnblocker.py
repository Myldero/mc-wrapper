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
        self.cache = {}
        self.whitelist = set()

    def on_player_join(self, player):

        if player.ip in self.whitelist or player.username in self.whitelist:
            is_vpn = False
        elif player.ip in self.cache:
            is_vpn = self.cache[player.ip]
        else:
            if self.config['api_key']:
                response = requests.get(self.secure_url + "/json/{}/{}".format(player.ip, self.config['api_key'])).json()
            else:
                response = requests.get(self.insecure_url + "/json/{}".format(player.ip)).json()

            if "error" in response:
                return

            is_vpn = response["host-ip"]
            self.cache[player.ip] = is_vpn

        if is_vpn:
            for cmd in self.config["commands"]:
                cmd = cmd.replace("{player}", player.username)
                self.wrapper.server.send(cmd)

    def on_server_command(self, *args):
        """
        Usage:
        !vpnblocker whitelist add <player|ip>
        !vpnblocker whitelist remove <player|ip>
        """

        if args[0] == "whitelist":
            if args[1] == "add":
                if args[2] in self.whitelist:
                    print("{} is already in the whitelist".format(args[2]))
                else:
                    self.whitelist.add(args[2])
                    with open('data/vpnblocker_whitelist.txt', 'w') as f:
                        for value in self.whitelist:
                            print(value, file=f)

            elif args[1] == "remove":
                if args[2] not in self.whitelist:
                    print("{} is not in the whitelist".format(args[2]))
                else:
                    self.whitelist.remove(args[2])
                    with open('data/vpnblocker_whitelist.txt', 'w') as f:
                        for value in self.whitelist:
                            print(value, file=f)
            else:
                raise Exception()
        else:
            raise Exception()

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
        else:
            try:
                with open('data/vpnblocker_whitelist.txt') as f:
                    self.whitelist = set([line.strip() for line in f])
            except Exception:
                self.whitelist = set()
