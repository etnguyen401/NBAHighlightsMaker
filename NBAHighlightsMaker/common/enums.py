from enum import Enum

class EventMsgType(Enum):
    FIELD_GOAL_MADE = 1
    FIELD_GOAL_MISSED = 2
    FREE_THROW_ATTEMPT = 3
    REBOUND = 4
    TURNOVER = 5
    FOUL = 6