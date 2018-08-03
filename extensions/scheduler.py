'''
A scheduler for running commands at specific times every day or at specific intervals
'''

import threading
import datetime
from time import sleep, time
from heapq import *

class Scheduler(threading.Thread):

    def __init__(self, wrapper):
        super().__init__()
        self.wrapper = wrapper
        self.send = self.wrapper.server.send


    def run(self):

        while self.enabled:

            while self.schedule[0][0] > str(datetime.datetime.now().replace(microsecond=0)):
                sleep(1 - time() % 1)

                if not self.enabled:
                    return

            _, i, cmd = heappop(self.schedule)

            self.send("\n".join(cmd["commands"]))
            print("\n".join(cmd["commands"]))

            cmd["time"] += cmd["delta"]
            heappush(self.schedule, (str(cmd["time"]), i, cmd)) # Use i to run schedule from top to bottom when two are equal in time


    def stop(self):
        self.enabled = False



    def setConfig(self, config):
        self.enabled = True

        today = datetime.date.today()
        start = datetime.datetime(year=today.year, month=today.month, day=today.day)
        now = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(seconds=15)

        self.schedule = []

        i = 0
        for sched in config["scheduler"]:
            sched["delta"] = datetime.timedelta(**sched["time"])

            if sched["type"] == "at":
                sched["time"] = start + sched["delta"]
                sched["delta"] = datetime.timedelta(days=1)


                if sched["time"] < now:
                    sched["time"] += sched["delta"]


            elif sched["type"] == "every":

                # This is an odd way to find the next time a task will be run whilst aligning it to the day, so "every 15 seconds" hits 00, 15, 30, 45 ..
                d = (datetime.datetime(year=1970, month=1, day=1, hour=1) + sched["delta"]).timestamp()
                sched["time"] = datetime.datetime.fromtimestamp((now.timestamp() - start.timestamp()) // d * d + d + start.timestamp())

            heappush(self.schedule, (str(sched["time"]), i, sched))

            i += 1
