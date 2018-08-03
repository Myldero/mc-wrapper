'''
Commands for the server to run.
They start with '!'
'''

import shutil, os, threading
from time import sleep


def cmd_help(cmd=None):
    '''Usage: !help [command]'''

    if cmd == None:
        # Show all commands
        print("Commands:")

        for name in sorted(globals()):
            if name.startswith("cmd_"):
                print(" !"+name[4:])

    else:
        for name, value in globals().items():
            if name == "cmd_"+cmd:
                print(value.__doc__)
                return

        print("Unknown command. Try !help")


def cmd_start():
    '''Usage: !start'''

    if wrapper.server.jar.poll() != None:
        wrapper.server.start()


def cmd_stop():
    '''Usage: !stop'''

    raise KeyboardInterrupt


def cmd_restart():
    '''Usage: !restart'''

    if wrapper.server.jar.poll() == None: # If server is running

        for player in wrapper.server.list:
            wrapper.server.send("kick {} {}".format(player, wrapper.config["server"]["restart_message"]))

        wrapper.server.send("stop")
        sleep(1)
        wrapper.server.jar.wait()
    wrapper.server.send("!start")


def cmd_backup(name=None):
    '''Usage: !backup [backup_name]'''

    threading.Thread(target=_backup, args=[name]).start()


def cmd_list():
    '''Usage: !list'''

    print("There are currently {0} players online:\n{1}".format(len(wrapper.server.list), ", ".join(sorted(wrapper.server.list, key=lambda x: x.upper()))))


def cmd_reload():
    '''Usage: !reload'''

    try:
        wrapper.reload()
    except Exception as e:
        print(e)
    else:
        print("Reloaded config!")


def cmd_votifier(arg):
    '''Usage: !votifier key'''

    if arg == "key":
        print(wrapper.extensions["votifier"].getKey())





def _backup(name=None):

    wrapper.server.send("save-all flush")

    sleep(2)

    world_name = wrapper.server.properties["level-name"]

    if name == None:
        name = world_name

    world_path = os.path.join(wrapper.config["server"]["file_path"], world_name)

    shutil.make_archive(os.path.join(wrapper.config["server"]["backups_folder"], name), 'zip', world_path)

    print("Backed up world as \"{}\"".format(name))
