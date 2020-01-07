import socket
import sys
from datetime import datetime
from threading import Thread


class RRConnection():
    def __init__(self):
        self._listenerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._inSock = None
        self._inThread = Thread(target=self.inLoop)
        self._isRunning = True
        self._notify = False
        self._allPassings = []

    def start(self):
        print("Starting thread for in-loop")
        self._inThread.start()

    def stop(self):
        self._isRunning = False
        self._listenerSocket.close()
        self._inSock.close()

    def inLoop(self):
        self._listenerSocket.bind(('', 3601))
        self._listenerSocket.listen(1)
        while self._isRunning:
            print("Starting listener socket on port 3601")
            self._inSock, addr = self._listenerSocket.accept()
            print("Got connection from {}".format(addr))
            keepReceiving = True
            while keepReceiving:
                received = self._inSock.recv(1024 * 1024)
                if len(received) > 0:
                    self.parseCommand(received.decode())
                else:
                    keepReceiving = False

    def parseCommand(self, cmd):
        allCmd = cmd.strip().split("\r\n")
        for oneCmd in allCmd:
            if oneCmd.strip() != "":
                print("Parsing command {}".format(oneCmd))
                f = oneCmd.split(';')
                if hasattr(self, f[0].strip()):
                    getattr(self, f[0].strip())(oneCmd)
                else:
                    print("Function {} not known".format(f[0]))

    def sendAnswer(self, answer):
        if self._inSock:
            print("Sending: {}".format(answer))
            fullAnswer = answer + "\r\n"
            self._inSock.send(fullAnswer.encode())
        else:
            print("Not connected!")

    def addPassing(self, Bib, Date, Time):
        PassingNo = len(self._allPassings) + 1
        # Bib is param
        # Date
        # Time
        EventID = ""
        Hits = "1"
        MaxRSSI = "31"
        InternalData = ""
        IsActive = "0"
        Channel = "1"
        LoopID = ""
        LoopOnly = ""
        WakeupCounter = ""
        Battery = ""
        Temperature = ""
        InternalActiveData = ""
        BoxName = "SwimBox"
        FileNumber = "1"
        MaxRSSIAntenna = "1"
        BoxId = "1"
        # entry = f"{PassingNo};{Bib};{Date};{Time};{EventID};{Hits};{MaxRSSI};{InternalData};{IsActive};{Channel};{LoopID};{LoopOnly};{WakeupCounter};{Battery};{Temperature};{InternalActiveData};{BoxName};{FileNumber};{MaxRSSIAntenna};{BoxId}"
        entry = "{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{}".format(PassingNo, Bib, Date, Time,
                                                                                     EventID, Hits, MaxRSSI,
                                                                                     InternalData, IsActive, Channel,
                                                                                     LoopID, LoopOnly, WakeupCounter,
                                                                                     Battery, Temperature,
                                                                                     InternalActiveData, BoxName,
                                                                                     FileNumber, MaxRSSIAntenna, BoxId)
        self._allPassings.append(entry)
        if self._notify:
            self.sendAnswer("#P;{}".format(entry))

    def SETPROTOCOL(self, str):
        print("Set protocol: {}".format(str))
        self.sendAnswer("SETPROTOCOL;2.0")

    def GETSTATUS(self, str):
        print("Get Status: {}".format(str))
        # GETSTATUS;<Date>;<Time>;<HasPower>;<Antennas>;<IsInOperationMode>;<FileNumber>;<GPSHasFix>;<Latitude>,<Longitude>;<ReaderIsHealthy>;<BatteryCharge>;<BoardTemperature>;<ReaderTemperature>;<UHFFrequency>;<ActiveExtConnected>;[<Channel>];[<LoopID>];[<LoopPower>];[<LoopConnected>];[<LoopUnderPower>];<TimeIsRunning>;<TimeSource>;<ScheduledStandbyEnabled>;<IsInStandby>
        # GETSTATUS;0000-00-00;00:02:39.942;1;11111111;1;50;1;49.721,8.254939;1;0;;;;;;;1;0<CrLf>
        Date = datetime.now().strftime("%Y-%m-%d")
        Time = datetime.now().strftime("%H:%M:%S.%f")
        HasPower = "0"
        Antennas = "10000000"
        IsInOperationMode = "1"
        FileNumber = "1"
        GPSHasFix = "0"
        Latitude = "0.0"
        Longitude = "0.0"
        ReaderIsHealthy = "1"
        BatteryCharge = "100"
        BoardTemperature = "20"
        ReaderTemperature = "20"
        UHFFrequency = "0"
        ActiveExtConnected = "0"
        Channel = ""
        LoopID = ""
        LoopPower = ""
        LoopConnected = ""
        LoopUnderPower = ""
        TimeIsRunning = "1"
        TimeSource = "0"
        ScheduledStandbyEnabled = "0"
        IsInStandby = "0"
        ErrorFlags = "0"
        # self.sendAnswer(
        #    f"GETSTATUS;{Date};{Time};{HasPower};{Antennas};{IsInOperationMode};{FileNumber};{GPSHasFix};{Latitude},{Longitude};{ReaderIsHealthy};{BatteryCharge};{BoardTemperature};{ReaderTemperature};{UHFFrequency};{ActiveExtConnected};{Channel};{LoopID};{LoopPower};{LoopConnected};{LoopUnderPower};{TimeIsRunning};{TimeSource};{ScheduledStandbyEnabled};{IsInStandby};{ErrorFlags}")
        self.sendAnswer(
            "GETSTATUS;{};{};{};{};{};{};{};{},{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{}".format(Date, Time,
                                                                                                          HasPower,
                                                                                                          Antennas,
                                                                                                          IsInOperationMode,
                                                                                                          FileNumber,
                                                                                                          GPSHasFix,
                                                                                                          Latitude,
                                                                                                          Longitude,
                                                                                                          ReaderIsHealthy,
                                                                                                          BatteryCharge,
                                                                                                          BoardTemperature,
                                                                                                          ReaderTemperature,
                                                                                                          UHFFrequency,
                                                                                                          ActiveExtConnected,
                                                                                                          Channel,
                                                                                                          LoopID,
                                                                                                          LoopPower,
                                                                                                          LoopConnected,
                                                                                                          LoopUnderPower,
                                                                                                          TimeIsRunning,
                                                                                                          TimeSource,
                                                                                                          ScheduledStandbyEnabled,
                                                                                                          IsInStandby,
                                                                                                          ErrorFlags))

    def GETCONFIG(self, s):
        parts = s.split(";")
        if parts[1] == "GENERAL":
            if parts[2] == "BOXNAME":
                self.sendAnswer(s.strip() + ";SwimBox;1")
            elif parts[2] == "TIMEZONE":
                self.sendAnswer(s.strip() + ";Europe/Amsterdam")
            else:
                print("Unknown general request: {}".format(parts[2]))
                self.sendAnswer(s.strip() + ";ERROR")
        elif parts[1] == "DETECTION":
            if parts[2] == "DEADTIME":
                self.sendAnswer(s.strip() + ";10")
            elif parts[2] == "REACTIONTIME":
                self.sendAnswer(s.strip() + ";10")
            elif parts[2] == "NOTIFICATION":
                self.sendAnswer(s.strip() + ";1")
            else:
                print("Unknown detection request: {}".format(parts[2]))
                self.sendAnswer(s.strip() + ";ERROR")
        else:
            print("Unknown config category: {}".format(parts[1]))
            self.sendAnswer(s.strip() + ";ERROR")

    def GETFIRMWAREVERSION(self, s):
        self.sendAnswer("GETFIRMWAREVERSION;1.0")

    def GETACTIVESTATUS(self, s):
        self.sendAnswer("GETACTIVESTATUS;ERROR")

    def PASSINGS(self, s):
        self.sendAnswer("PASSINGS;{};1".format(len(self._allPassings))

    def SETPUSHPASSINGS(self, s):
        parts = s.split(";")
        if parts[1] == "1":
            self._notify = True
        else:
            self.notify = False
        if parts[2] == "1":
            pass
            # shall send all existing here
        self.sendAnswer(s)


if __name__ == '__main__':
    foo = RRConnection()
    foo.start()
    while True:
        try:
            print("You can enter new passings in the format <bib> (current time will be taken")
            newEntry = int(input())
            newTime = datetime.now()
            foo.addPassing(newEntry, newTime.strftime("%Y-%m-%d"), newTime.strftime("%H:%M:%S.%f"))
        except KeyboardInterrupt:
            print("Exiting...")
            foo.stop()
            sys.exit(1)
