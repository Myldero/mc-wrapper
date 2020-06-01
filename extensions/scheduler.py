"""
An extension to allow scheduling commands like restarting the server or creating backups
"""

from base_extension import BaseExtension
import datetime
import time
import heapq


class Scheduler(BaseExtension):

    def __init__(self, *args):
        super().__init__(*args)
        self.name = "scheduler"
        self.schedule = None

    def on_start(self):
        while self.enabled:

            while self.schedule[0][0] > str(datetime.datetime.now().replace(microsecond=0)):
                time.sleep(1 - time.time() % 1)

                if not self.enabled:
                    return

            _, i, cmd = heapq.heappop(self.schedule)

            self.wrapper.server.send("\n".join(cmd["commands"]))
            print("\n".join(cmd["commands"]))

            cmd["time"] += cmd["delta"]
            # Use i to run schedule from top to bottom when two are equal in time
            heapq.heappush(self.schedule, (str(cmd["time"]), i, cmd))

    def on_reload(self):

        try:
            self.config = self.load_json_config(name=self.name, default={
                "enabled": False,
                "schedule": [
                    {
                        "type": "at",
                        "time": {
                            "hours": 6
                        },
                        "commands": [
                            "!restart"
                        ]
                    },
                    {
                        "type": "every",
                        "time": {
                            "minutes": 10,
                            "seconds": 1
                        },
                        "commands": [
                            "say 10 minutes and 1 second have passed (Example in scheduler.json)"
                        ]
                    }
                ]})
        except Exception:
            pass
        else:
            if not self.config["enabled"]:
                return

            today = datetime.date.today()
            start = datetime.datetime(year=today.year, month=today.month, day=today.day)
            now = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(seconds=15)

            self.schedule = []

            for i in range(len(self.config["schedule"])):
                sched = self.config["schedule"][i]
                sched["delta"] = datetime.timedelta(**sched["time"])

                if sched["type"] == "at":
                    sched["time"] = start + sched["delta"]
                    sched["delta"] = datetime.timedelta(days=1)

                    if sched["time"] < now:
                        sched["time"] += sched["delta"]

                elif sched["type"] == "every":

                    # By using the same offset, the resulting timestamps will be consistent
                    d = (datetime.datetime(year=1970, month=1, day=1, hour=1) + sched["delta"]).timestamp()
                    sched["time"] = datetime.datetime.fromtimestamp(
                        (now.timestamp() - start.timestamp()) // d * d + d + start.timestamp())

                heapq.heappush(self.schedule, (str(sched["time"]), i, sched))
