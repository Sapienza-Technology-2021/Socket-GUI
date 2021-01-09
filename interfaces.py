import threading


APP_NAME = "Tech Team Rover"
PORT = 12345
DEBUG = True

def debug(msg):
    global DEBUG
    if DEBUG is True:
        print(msg)

class RoverNotConnectedError(Exception):
    pass

class RoverInvalidOperation(Exception):
    pass

# To be implemented by the client socket
class RoverInterface:
    def __init__(self):
        self.connected = False
        self.ci = None

    def setControllerInterface(self, controllerInterface):
        self.ci = controllerInterface

    def ensureConnection(self):
        if self.connected is False:
            raise RoverNotConnectedError

    def connect(self, ip, port):
        if self.connected is True:
            raise RoverInvalidOperation
        debug("Connecting to rover @" + ip + ":" + str(port) + "...")
        return False

    def disconnect(self):
        debug("Disconnecting from rover...")
        self.connected = False

    def isConnected(self):
        return self.connected

    def move(self, speed):
        self.ensureConnection()
        debug("Rover MOVE " + str(speed))

    def moveRotate(self, speed, degPerMin):
        self.ensureConnection()
        debug("Rover MOVE " + str(speed) + " DEG/MINUTE " + str(degPerMin))

    def rotate(self, angle):
        self.ensureConnection()
        debug("Rover ROTATE " + str(angle) + "°")

    def stop(self):
        self.ensureConnection()
        debug("Rover stop")

    def setMLEnabled(self, val):
        self.ensureConnection()
        debug("Rover ML " + ("enabled" if val is True else "disabled"))

# To be implemented by the GUI and the ML classes
class ControllerInterface:
    def __init__(self):
        pass

    def updateAccel(self, xyz):
        debug("Controller update acceleration")

    def updateGyro(self, xyz):
        debug("Controller update gyroscope")

    def updateMagn(self, xyz):
        debug("Controller update magnetometer")

    def updateIrDistance(self, dist1, dist2):
        debug("Controller update IR distances")

    def updateBatt(self, val):
        debug("Controller update battery")

    def updateCpuTemp(self, val):
        debug("Controller update CPU temperature")

    def updateRPMFeedback(self, val):
        debug("Controller update RPM")

    def setMLEnabled(self, val):
        debug("Controller update Machine Learning enabled")

def InterruptableEvent():
    e = threading.Event()
    def patched_wait():
        while not e.is_set():
            e._wait(3)
    e._wait = e.wait
    e.wait = patched_wait
    return e
