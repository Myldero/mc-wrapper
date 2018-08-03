'''
A file for putting in custom functions for regex commands

sender is a string containing the username of the player who sent the command
match is a list containing strings matching to {0}, {1}, {2}, etc..
'''
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
