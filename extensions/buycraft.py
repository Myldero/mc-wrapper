"""
An extension to add a BuyCraft store (Now called Tebex) to your server

https://github.com/minecrafter/buycraft-python
"""

import re
import requests
from time import sleep

from base_extension import BaseExtension


class BuycraftException(Exception):
    pass


class Buycraft(BaseExtension):

    def __init__(self, *args):
        super().__init__(*args)
        self.name = "buycraft"

        self.url = 'https://plugin.buycraft.net'
        self.get = {}

        self.player_list = self.wrapper.server.list

    def on_start(self):
        while self.enabled:

            self.get = self.get_due_players()

            if self.get["meta"]["execute_offline"]:
                offline = self.get_offline_commands()

                done = []

                for command in offline["commands"]:
                    command["player"]["username"] = command["player"]["name"]

                    # Because it's very likely that there's json in the commands
                    for key in command["player"]:
                        command["command"] = command["command"].replace("{{{}}}".format(key), command["player"][key])

                    self.wrapper.server.send(command["command"])

                    done.append(command["id"])

                if done:
                    self.mark_commands_completed(done)

            self.online_commands()

            n = 0
            # Keep checking if the wrapper is closed every second
            while self.enabled and n < self.get["meta"]["next_check"]:
                n += 1
                sleep(1)

    def online_commands(self):

        done = []

        for player in list(self.get["players"]):
            if any(player["name"] == i.username for i in self.player_list):
                commands = self.get_player_commands(player["id"])

                for command in commands["commands"]:
                    player["username"] = player["name"]

                    for key in player:
                        command["command"] = command["command"].replace("{{{}}}".format(key), "{}".format(player[key]))

                    self.wrapper.server.send(command["command"])
                    done.append(command["id"])

                self.get["players"].remove(player)

        if done:
            self.mark_commands_completed(done)

    def on_player_join(self, player):
        self.online_commands()

    def on_reload(self):

        try:
            self.config = self.load_json_config(name=self.name, default={'enabled': False, 'key': ''})
        except Exception:
            pass
        else:
            self.secret = self.config['key']

    def _getjson(self, url):
        response = requests.get(url, headers={'X-Buycraft-Secret': self.secret}).json()
        if 'error_code' in response:
            raise BuycraftException('Error code ' + str(response['error_code']) + ': ' + response['error_message'])
        return response

    def information(self):
        """Returns information about the server and the webstore.
        """
        return self._getjson(self.url + '/information')

    def listing(self):
        """Returns a listing of all packages available on the webstore.
        """
        return self._getjson(self.url + '/listing')

    def get_due_players(self, page=None):
        """Returns a listing of all players that have commands available to run.

        :param page: the page number to use
        """
        if page is None:
            return self._getjson(self.url + '/queue')
        elif isinstance(page, int):
            return self._getjson(self.url + '/queue?page=' + str(page))
        else:
            raise BuycraftException("page parameter is not valid")

    def get_offline_commands(self):
        """Returns a listing of all commands that can be run immediately.
        """
        return self._getjson(self.url + '/queue/offline-commands')

    def get_player_commands(self, player_id):
        """Returns a listing of all commands that require a player to be run.
        """
        if isinstance(player_id, int):
            return self._getjson(self.url + '/queue/online-commands/' + str(player_id))
        else:
            raise BuycraftException("player_id parameter is not valid")

    def mark_commands_completed(self, command_ids):
        """Marks the specified commands as complete.

        :param command_ids: the IDs of the commands to mark completed
        """
        resp = requests.delete(self.url + '/queue', params={'ids[]': command_ids},
                               headers={'X-Buycraft-Secret': self.secret})
        return resp.status_code == 204

    def recent_payments(self, limit):
        """Gets the rest of recent payments made for this webstore.

        :param limit: the maximum number of payments to return. The API will only return a maximum of 100.
        """
        if isinstance(limit, int):
            return self._getjson(self.url + '/payments')
        else:
            raise BuycraftException("limit parameter is not valid")

    def create_checkout_link(self, username, package_id):
        """Creates a checkout link for a package.

        :param username: the username to use for this package
        :param package_id: the package ID to check out
        """
        if not isinstance(username, str) or len(username) > 16 or not re.match(r'\w', username):
            raise BuycraftException("Username is not valid")

        if not isinstance(package_id, int):
            raise BuycraftException("Package ID is not valid")

        response = requests.post(self.url + '/checkout', params={'package_id': package_id, 'username': username},
                                 headers={'X-Buycraft-Secret': self.secret}).json()
        if 'error_code' in response:
            raise BuycraftException('Error code ' + str(response['error_code']) + ': ' + response['error_messages'])
        return response
