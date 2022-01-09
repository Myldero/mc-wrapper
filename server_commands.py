"""
Commands for the server to run.
They start with '!'
"""

import shutil, os, threading
from textwrap import dedent
from time import sleep


def cmd_help(cmd=None):
    """
    Usage: !help [command]
    """

    if cmd is None:
        # Show all commands
        print("Commands:")

        for name in sorted(globals()):
            if name.startswith("cmd_"):
                print(" !"+name[4:])

    else:
        for name, value in globals().items():
            if name == "cmd_"+cmd:
                print(dedent(value.__doc__).strip())
                return

        print("Unknown command. Try !help")


def cmd_start():
    """
    Usage: !start
    """

    try:
        if wrapper.server.jar.poll() is not None:
            wrapper.server.start()
    except Exception as e:
        print(e)


def cmd_stop():
    """
    Usage: !stop
    """

    wrapper.server.send("kick @a The server is stopping")
    raise KeyboardInterrupt


def cmd_restart():
    """
    Usage: !restart
    """

    if wrapper.server.jar.poll() is None:  # If server is running

        wrapper.server.send("kick @a {}".format(wrapper.server.config["restart_message"]))

        wrapper.server.send("stop")
        sleep(1)
        wrapper.server.jar.wait()
    wrapper.server.send("!start")


def cmd_backup(name=None):
    """
    Usage: !backup [backup_name]
    """

    threading.Thread(target=_backup, args=[name]).start()


def cmd_list():
    """
    Usage: !list
    """

    print("There are currently {0} players online:\n{1}".format(len(wrapper.server.list), ", ".join(sorted([i.username for i in wrapper.server.list], key=lambda x: x.upper()))))


def cmd_reload(arg=None):
    """
    Usage: !reload [full]
    """

    try:
        if arg == "full":
            wrapper.full_reload()
        else:
            wrapper.reload()
    except Exception as e:
        print(e)
    else:
        print("Reloaded config!")


def cmd_extension(ext_name, cmd):
    """
    Usage !extension <name> <start|stop|restart>
    """

    try:
        ext = wrapper.extensions[ext_name]
    except KeyError:
        print("Unknown extension")
    else:

        if cmd == "start":
            if not ext.enabled:
                ext.start()
            else:
                print("{} is already started".format(ext_name))
        elif cmd == "stop":
            if ext.enabled:
                ext.stop()
                ext.wait_stop()
            else:
                print("{} is already stopped".format(ext_name))
        elif cmd == "restart":

            if ext.enabled:
                ext.stop()
                ext.wait_stop()

            ext.start()


def _backup(name=None):

    wrapper.server.send("save-all flush")

    sleep(2)

    world_name = wrapper.server.properties["level-name"]

    if name is None:
        name = world_name

    world_path = os.path.join(wrapper.server.config["file_path"], world_name)

    shutil.make_archive(os.path.join(wrapper.server.config["backups_folder"], name), 'zip', world_path)

    print("Backed up world as \"{}\"".format(name))
