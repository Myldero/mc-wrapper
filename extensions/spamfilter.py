'''
A spamfilter that tries to prevent players from spamming the chat
It needs a lot of improvement!
'''

from time import time

players = {}

def on_message(sender, message):
    if sender not in players:
        players[sender] = {'message': message, 'timestamp': time(), 'count': 0, 'warns': 0, 'kicks': 0}

    else:
        cmd = None

        if players[sender]['timestamp'] + 0.03 > time():
            players[sender]['count'] += 3

        elif players[sender]['timestamp'] + 5 > time() and players[sender]['message'] == message:
            players[sender]['count'] += 1

        elif players[sender]['timestamp'] + 0.05 * len(message) + 0.5 > time():
            players[sender]['count'] += 1




        if players[sender]['count'] >= 2:
            players[sender]['count'] = 0
            players[sender]['warns'] += 1

            if players[sender]['warns'] > config["warns_before_kick"]:

                players[sender]['warns'] = 0
                players[sender]['kicks'] += 1

                if players[sender]['kicks'] > config["kicks_before_ban"]:
                    cmd = config["ban_cmd"]
                else:
                    cmd = config["kick_cmd"]
            else:
                cmd = config["warn_cmd"]


        if cmd != None:
            wrapper.server.send(cmd.replace("{{{}}}".format("sender"), sender))


        if players[sender]['timestamp'] + 10 <= time():
            players[sender]['count'] = 0

        if players[sender]['timestamp'] + config["warn_cooldown"] <= time():
            players[sender]['warns'] = 0

        if players[sender]['timestamp'] + config["kick_cooldown"] <= time():
            players[sender]['kicks'] = 0


        players[sender]['message'] = message
        players[sender]['timestamp'] = time()
