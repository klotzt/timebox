#!/usr/bin/python

import os
import subprocess
import sys
from shutil import copyfile

class IdMapper:
    def __init__(self):
        self.mapFile="/home/pi/wiegand/map.txt"
        self.outFile="/home/pi/wiegand/out.txt"
        self.backupFile="/boot/out.txt"
        
        
    def readFile(self):
        self.masterMap={}
        self.stamp = os.stat(self.mapFile).st_mtime
        with open(self.mapFile) as f:
            content = f.readlines()

        for oneLine in content:
            splitted=oneLine.split('\t')
            if (len(splitted)==2):
                self.masterMap[splitted[0]]=splitted[1].strip()
            else:
                print >> sys.stderr, "Malformed line: {}".format(oneLine)
           
    def run(self):
        self.readFile()
        proc = subprocess.Popen(['/home/pi/wiegand/wiegand_rpi'],stdout=subprocess.PIPE)
        
        while True:
            line=proc.stdout.readline().strip()
            value=line.split (',')
            if (len(value)==2):
                id=value[0]
                time=value[1]
                if id in self.masterMap:
                    mapped_id=self.masterMap[id]
                else:
                    mapped_id=id
                with open (self.outFile, "a+") as out_file:                
                    outStr="{},{}\n".format (mapped_id, time)
                    print "Found transponder: {}".format(outStr)
                    out_file.write (outStr)
                copyfile (self.outFile, self.backupFile)
            else:
                print >> sys.stderr, "Malformed input: {}".format(line)
            new_stamp = os.stat(self.mapFile).st_mtime
            if (new_stamp!=self.stamp):
                self.readFile()

    
if __name__ == "__main__":
    app=IdMapper()
    app.run()