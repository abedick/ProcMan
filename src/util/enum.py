from enum import Enum

class RemoteState(Enum):
    RUNNING = 1
    KILLED = 2
    FAILED = 3
    STABLE = 4
    UNINITIALIZED = 5