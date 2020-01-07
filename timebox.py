#!/usr/bin/python3
import datetime
import os
import subprocess
import sys
from shutil import copyfile

from RRConnection import RRConnection


class IdMapper:
    def __init__(self):
        self.mapFile = "/home/pi/timebox/map.txt"
        self.outFile = "/home/pi/timebox/out.txt"
        self.backupFile = "/boot/out.txt"

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
                    print("Malformed line in mapfile: {}".format(oneLine), file=sys.stderr)

    def readPrevious(self, rrConnection):
        with open(self.outFile) as f:
            content = f.readlines()

        for oneLine in content:
            splitted = oneLine.split(',')
            if (len(splitted) == 2):
                rrConnection.addPassing(splitted[0], datetime.datetime.now().strftime("%Y-%m-%d"), splitted[1].strip())
            else:
                print("Malformed line in result: {}".format(oneLine), file=sys.stderr)

    def run(self):
        self.readFile()
        proc = subprocess.Popen(['/home/pi/timebox/wiegand_rpi'], stdout=subprocess.PIPE)
        rr = RRConnection()
        # read previous passings into RR adapter...
        try:
            self.readPrevious(rr)
        except FileNotFoundError:
            print ("No previous result file, ignoring")
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
                    rr.addPassing(mapped_id, datetime.datetime.now().strftime("%Y-%m-%d"), time)
                    with open(self.outFile, "a+") as out_file:
                        outStr = "{},{}\n".format(mapped_id, time)
                        print("Found transponder: {}".format(outStr))
                        out_file.write(outStr)
                    copyfile(self.outFile, self.backupFile)
                else:
                    print >> sys.stderr, "Malformed line in wiegand output: {}".format(line)
            new_stamp = os.stat(self.mapFile).st_mtime
            if (new_stamp != self.stamp):
                self.readFile()


if __name__ == "__main__":
    app = IdMapper()
    app.run()
