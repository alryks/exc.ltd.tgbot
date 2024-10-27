from enum import Enum, auto


class State(Enum):
    FIRST_INTERACTION = auto()
    MAIN_MENU = auto()
    SEND_ALL = auto()
    ENTER_JOB = auto()
    ENTER_NAME = auto()
    ENTER_GENDER = auto()
    ENTER_PHONE = auto()
    ENTER_AGE = auto()
    ENTER_DATE_ON_OBJECT = auto()
    ENTER_RESIDENCE = auto()
    ENTER_PHOTO = auto()
    LIST_MENU = auto()
    ENTER_COMMENT = auto()  # Добавляем новое состояние


class Status(Enum):
    ACCEPTED = "accepted"
    DECLINED = "declined"


class EnterMode(Enum):
    FILLING = auto()
    EDITING = auto()
