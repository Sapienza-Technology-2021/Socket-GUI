import json
import threading

APP_NAME = "Tech Team Rover"
PORT = 12345
DEBUG = True


def debug(msg):
    global DEBUG
    if DEBUG is True:
        print(msg)


def checkLoadJson(data):
    if data.startswith("<") and data.endswith(">"):
        debug("Received test message: " + data)
        return None
    lb = data.count("{")
    rb = data.count("}")
    if lb != rb or lb == 0 or data[0] != "{" or data[len(data) - 1] != "}":
        debug("Corrupted Json")
        return None
    count = 0
    for i in range(len(data)):
        if data[i] == "{":
            count += 1
        elif data[i] == "}":
            count -= 1
        if count == 0 and (i + 1) != len(data) and i != 0:
            debug("Corrupted Json")
            return None
    return json.loads(data)


class RoverNotConnectedError(Exception):
    pass


class RoverInvalidOperation(Exception):
    pass


def InterruptableEvent():
    e = threading.Event()

    def patched_wait():
        while not e.is_set():
            e._wait(3)

    e._wait = e.wait
    e.wait = patched_wait
    return e
