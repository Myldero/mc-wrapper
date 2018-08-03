'''
MCLeaks checker for checking if an account has been compromised
'''

import requests

def check(player, url="https://mcleaks.themrgong.xyz/api/v3"):
    response = requests.get(url + "/isnamemcleaks/{}".format(player)).json()

    if "error" in response: # Ignore errors
        return None

    return response["isMcleaks"]
