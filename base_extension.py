import json
import os
import threading


class BaseExtension:

    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.config = {'enabled': False}
        self.name = None
        self.thread = None
        self.enabled = False

    def on_start(self):
        """Is called in a new thread"""
        pass

    def on_stop(self):
        pass

    def on_reload(self):
        pass

    def on_server_start(self):
        pass

    def on_server_stop(self):
        pass

    def on_player_join(self, player):
        pass

    def on_player_leave(self, player):
        pass

    def on_player_message(self, sender, message):
        pass

    def on_server_message(self, message):
        """
        Gets all 'INFO' messages and strips the first part to be more useful
        E.g. all messages that start with [12:34:56] [Server thread/INFO]:
        """
        pass

    def on_server_all_messages(self, message):
        """Gets full raw data from the server logs"""
        pass

    def on_server_command(self, *args):
        """Define custom server commands to be run by !extname args"""
        pass

    def start(self):
        if not self.enabled and self.config["enabled"]:
            print("Starting {}".format(self.name))
            self.enabled = True
            self.thread = threading.Thread(target=self.on_start)
            self.thread.start()

    def stop(self):
        if self.enabled:
            print("Stopping {}".format(self.name))
            self.enabled = False
            self.on_stop()

    def wait_stop(self):
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=5)
            if self.thread.is_alive():
                print("{} will not stop".format(self.name))

    @staticmethod
    def load_json_config(name, default):
        """Loads a json config file and sets default value if it does not exist"""

        path = "config/{}.json".format(name)
        if not os.path.isfile(path):
            with open(path, 'w') as f:
                f.write(json.dumps(default, indent=4))

        try:
            with open(path, 'r') as f:
                config = json.loads(f.read())
        except Exception as e:
            print("There was an error in {}.json!".format(name))
            print(e)
            raise
        else:
            return config
