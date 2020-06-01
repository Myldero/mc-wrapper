"""
An extension that replicates the Votifier plugin to send rewards for voting on vote websites
"""

import os
import re
import socket
import threading
import time

import requests

from base_extension import BaseExtension
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto import Random


class Votifier(BaseExtension):

    def __init__(self, *args):
        super().__init__(*args)
        self.name = "votifier"

        self.private_key = None
        self.cipher = None
        self.buffer = 256
        self.is_running = False

    @staticmethod
    def generate_keys():
        generator = Random.new().read

        private_key = RSA.generate(2048, generator)
        public_key = private_key.publickey()

        with open('config/private.pem', 'w') as f:
            f.write(private_key.export_key(format='PEM').decode())

        with open('config/public.pem', 'w') as f:
            f.write(public_key.export_key(format='PEM').decode())

    def get_key(self):
        public_key = self.private_key.publickey().export_key(format='PEM').decode()

        return re.findall(r'^-----BEGIN PUBLIC KEY-----([\s\S]+)-----END PUBLIC KEY-----$', public_key)[0].replace("\n", "")

    def check_player(self, username):
        if not re.search(r'^[A-Za-z0-9_]+$', username):
            return False

        try:
            uuid = self.get_uuid(username)

            file_path = self.wrapper.server.config["file_path"]
            world_name = self.wrapper.server.properties["level-name"]

            return os.path.exists(os.path.join(file_path, world_name, "playerdata", "{}.dat".format(uuid)))

        except Exception:
            return False

    @staticmethod
    def get_uuid(username):
        """
        Gets the UUID of a player formatted with dashes
        """

        url = "https://api.mojang.com/users/profiles/minecraft/" + username
        response = requests.get(url).json()
        uuid = response["id"]
        uuid = uuid[:8] + "-" + uuid[8:12] + "-" + uuid[12:16] + "-" + uuid[16:20] + "-" + uuid[20:]

        return uuid

    def handle_vote(self, conn, addr):
        try:
            code = self.cipher.decrypt(conn.recv(self.buffer), b"")

            if b"VOTE" in code:

                vote = {}
                vote["service_name"], vote["username"], vote["address"], vote["timestamp"] = [i.decode() for i in
                                                                                              code.split(b"VOTE")[
                                                                                                  1].split()[:4]]

                if not self.config["check_players"] or self.check_player(vote["username"]):

                    out = ""
                    for command in self.config["commands"]:
                        for key in vote:  # Because it's very likely that there's json in the commands
                            command = command.replace("{{{}}}".format(key), vote[key])

                        out += command + "\n"

                    self.wrapper.server.send(out)

                    with open('logs/votifier.log', 'a') as f:
                        f.write("{timestamp} : {username} ({address}) has voted on {service_name}\n".format(**vote))

        except ValueError:
            pass
        except AttributeError:
            pass
        finally:
            conn.close()

    def on_start(self):
        self.is_running = True
        serversocket = socket.socket()
        serversocket.bind((self.config["ip"], self.config["port"]))
        serversocket.listen(5)

        try:
            while self.enabled:
                conn, addr = serversocket.accept()
                conn.settimeout(10)
                threading.Thread(target=self.handle_vote, args=(conn, addr)).start()
        finally:
            serversocket.close()

        self.is_running = False

    def on_stop(self):
        # Connect to socket, so it'll check self.running again:
        socket.socket().connect((self.config["ip"], self.config["port"]))
        while self.is_running:
            time.sleep(0.1)

    def on_server_command(self, arg):
        """
        Usage: !votifier key
        """

        if arg == "key":
            print(self.get_key())

    def on_reload(self):

        try:
            self.config = self.load_json_config(name=self.name, default={
                'enabled': False,
                'check_players': True,
                'ip': '0.0.0.0',
                'port': 8192,
                'commands': [
                    'tellraw @a {"text":"{username} has just voted on {service_name}!","color":"gold"}',
                    'scoreboard players add {username} votes 1'
                ]
            })
        except Exception:
            pass
        else:
            if not self.config["enabled"]:
                return

            for i in range(len(self.config["commands"])):
                self.config["commands"][i] = self.config["commands"][i].replace("\n", "\\n")

            if not os.path.isfile('config/private.pem'):
                self.generate_keys()

            with open('config/private.pem', 'r') as f:
                self.private_key = RSA.import_key(f.read())

            self.cipher = PKCS1_v1_5.new(self.private_key)
