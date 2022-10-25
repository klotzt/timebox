#!/usr/bin/python3
from datetime import datetime
import os
import subprocess
import sys
from shutil import copyfile
import logging
from RRConnection import RRConnection
from logging.handlers import RotatingFileHandler

class IdMapper:
    def __init__(self):
        self._log=logging.getLogger("timebox")
        handler = RotatingFileHandler('/home/pi/timebox/time.log', maxBytes=2000, backupCount=10)
        self._log.addHandler(handler)        
        self._log.setLevel(logging.DEBUG)
        self.mapFile = "/home/pi/timebox/map.txt"
        suffix=datetime.now().strftime("%Y%m%d_%H%M%S")
        self.outFile = "/home/pi/timebox/out_{}.txt".format(suffix)
        self.backupFile = "/boot/out_{}.txt".format(suffix)
        self._log.debug("Logging to {}".format(self.outFile))

    def readFile(self):
        self.masterMap = {}
        self.stamp = os.stat(self.mapFile).st_mtime
        with open(self.mapFile) as f:
            content = f.readlines()

        for oneLine in content:
            if len(oneLine.strip())>0:
                splitted = oneLine.split('\t')
                if (len(splitted) == 2):
                    self.masterMap[splitted[0]] = splitted[1].strip()
                else:
                    self._log.error("Malformed line in mapfile: {}".format(oneLine))

    def readPrevious(self, rrConnection):
        with open(self.outFile) as f:
            content = f.readlines()

        for oneLine in content:
            splitted = oneLine.split(',')
            if (len(splitted) == 2):
                rrConnection.addPassing(splitted[0], datetime.now().strftime("%Y-%m-%d"), splitted[1].strip())
            else:
                self._log.error("Malformed line in result: {}".format(oneLine))

    def run(self):
        self.readFile()
        proc = subprocess.Popen(['/home/pi/timebox/wiegand_rpi'], stdout=subprocess.PIPE)
        rr = RRConnection()
        # read previous passings into RR adapter...
        try:
            self.readPrevious(rr)
        except FileNotFoundError:
            self._log.debug ("No previous result file, ignoring")
        rr.start()

        while True:
            line = proc.stdout.readline().strip().decode()
            if len(line.strip()) > 0:
                value = line.split(',')
                if (len(value) == 2):
                    transponder = value[0]
                    time = value[1]
                    if transponder in self.masterMap:
                        mapped_id = self.masterMap[transponder]
                    else:
                        mapped_id = transponder
                    rr.addPassing(mapped_id, datetime.now().strftime("%Y-%m-%d"), time)
                    with open(self.outFile, "a+") as out_file:
                        outStr = "{},{}\n".format(mapped_id, time)
                        self._log.debug("Found transponder: {}".format(outStr))
                        out_file.write(outStr)
                    try:
                        copyfile(self.outFile, self.backupFile)
                    except PermissionError:
                        self._log.warning("Unable to backup outfile!")
                else:
                    self._log.debug ("Malformed line in wiegand output: {}".format(line))
            new_stamp = os.stat(self.mapFile).st_mtime
            if (new_stamp != self.stamp):
                self.readFile()


if __name__ == "__main__":
    app = IdMapper()
    app.run()
