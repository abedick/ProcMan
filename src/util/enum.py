from enum import Enum

class RemoteState(Enum):
    RUNNING = 1
    KILLED = 2
    FAILED = 3
    STABLE = 4
    UNINITIALIZED = 5


class ProcessState(Enum):
    RUNNING = 1
    KILLED = 2
    FAILED = 3
    STABLE = 4
    UNINITIALIZED = 5
    RESTARTING = 6
    SHUTDOWN = 7