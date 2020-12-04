# Minecraft Wrapper for Vanilla plugins

This is a wrapper for the Minecraft Server JAR. It contains buycraft, votifier, a scheduler and more!

## Installation
You will need Python 3.4 or later. Preferably the latest version.
Install requirements with pip:
```
python3 -m pip install -r requirements.txt
```
Run the wrapper with
```
python3 main.py
```
A config folder will appear. To get the server running, a path to the jar file must be specified in `server.json`

## Extensions

### Votifier
Votifier is an essential plugin for a Minecraft server. To get started, specify appropriate commands as vote rewards inside the commands list in `votifier.json`. When the config is ready, Votifier just needs to be setup on the voting site. To do this, get the public key by typing `!votifier key` in the server console.

### Buycraft
A simple extension that allows for a connection to Buycraft for donation rewards. Just fill in the key in `buycraft.json` and it should be ready for use.

### Scheduler
The scheduler adds ways to for example schedule restarts or backups. It supports doing something at specific times each day, or with specific intervals. Remember to remove the examples from the scheduler as they are supposed to be used as examples for creating your own scheduled tasks.

### Custom commands
Being able to add custom chat commands is very powerful. In `commands.json` it is possible to specify two types of commands. The "command" type uses the match string to directly send a command to the server, while the "function" type runs a specified function inside `commands.py` allowing for infinite possibilities. As an example, there's a command that will check the current TPS (Ticks per Second) of the server, which might be useful for making sure if the server is lagging. To match commands, regular expressions are used (See: https://pythex.org/). To use values from the match, use `{1}` for the first capture group, `{2}` for the second and so on. See examples in the `commands.json` file.
