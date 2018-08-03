import json, re, os, importlib
from extensions.votifier import Votifier
import commands

def load(file):
    with open(file, 'r') as f:
        s = f.read()

    return json.loads(s)

def get(wrapper):

    importlib.reload(commands)
    commands.wrapper = wrapper

    try:
        os.makedirs("config")
    except OSError:
        pass

    try:
        os.makedirs("logs")
    except OSError:
        pass

    for file in ("server", "commands", "buycraft", "votifier", "scheduler", "mcleaks", "spamfilter"):
        path = "config/{}.json".format(file)

        if not os.path.isfile(path):
            with open(path, 'w') as f:

                if file == "server":
                    f.write(json.dumps({'file_name': 'minecraft_server.1.13.jar', 'file_path': '.', 'memory': 1024, 'restart_message': 'The server is restarting!', 'backups_folder': './backups/'}, indent=4))

                elif file == "commands":
                    f.write(json.dumps([{"type": "command", "match": "^!send ([A-Za-z0-9_]+) (.*)", "run": ["tellraw {1} {\"text\":\"{sender} says {2}\"}"]},
                                        {"type": "function", "match": "([0-9]+)\\+([0-9]+)", "run": "do_math"},
                                        {"type": "function", "match":"^tps$", "run": "tps"}], indent=4))

                elif file == "buycraft":
                    f.write(json.dumps({'enabled': False, 'key': ''}, indent=4))

                elif file == "votifier":
                    f.write(json.dumps({'enabled': False, 'check_players': True, 'ip': '0.0.0.0', 'port': 8192, 'commands': ["tellraw @a {\"text\":\"{username} has just voted on {service_name}!\",\"color\":\"gold\"}", "scoreboard players add {username} votes 1"]}, indent=4))

                elif file == "scheduler":
                    f.write(json.dumps([{"type":"at","time":{"hours":6},"command":["!restart"]}, {"type":"every","time":{"minutes": 10, "seconds": 1},"commands":["say 10 minutes and 1 second have passed :)"]}], indent=4))

                elif file == "mcleaks":
                    f.write(json.dumps({'enabled': False}, indent=4))

                elif file == "spamfilter":
                    f.write(json.dumps({"enabled": False, "kicks_before_ban": 2, "warns_before_kick": 2, "warn_cmd": "msg {sender} \"Please watch the spam!\"", "kick_cmd": "kick {sender} Please watch the spam!", "ban_cmd": "ban {sender} Spam."}))

    config = {}

    config["server"] = load('config/server.json')

    config["commands"] = load('config/commands.json')
    for cmd in config["commands"]:
        cmd["match"] = re.sub(r"{([0-9]+)}", r'(?:\\\1)', cmd["match"])
        cmd["match"] = re.compile(cmd["match"])

        if cmd["type"] == "function":
            cmd["run"] = getattr(commands, cmd["run"])
        elif cmd["type"] == "command":
            for i in range(len(cmd["run"])):
                cmd["run"][i] = cmd["run"][i].replace("\n", "\\n")


    config["buycraft"] = load('config/buycraft.json')

    config["votifier"] = load('config/votifier.json')

    for i in range(len(config["votifier"]["commands"])):
        config["votifier"]["commands"][i] = config["votifier"]["commands"][i].replace("\n", "\\n")

    if not os.path.isfile('config/private.pem'):
        Votifier.generateKeys()

    with open('config/private.pem', 'r') as f:
        config["votifier"]["private_key"] = f.read()

    config["scheduler"] = load('config/scheduler.json')

    config["mcleaks"] = load('config/mcleaks.json')

    config["spamfilter"] = load('config/spamfilter.json')



    if not os.path.isfile(os.path.join(config["server"]["file_path"], config["server"]["file_name"])):
        raise Exception("Can't find minecraft jar file")


    return config
