from enum import Enum


class State(Enum):
    FIRST_INTERACTION = "first_interaction"
    ENTER_NAME = "enter_name"
    ENTER_GENDER = "enter_gender"
    ENTER_PHONE = "enter_phone"
    ENTER_AGE = "enter_age"
    ENTER_DATE_ON_OBJECT = "enter_date_on_object"
    ENTER_RESIDENCE = "enter_residence"
    ENTER_PHOTO = "enter_passport"
    ENTER_JOB = "enter_job"

    MAIN_MENU = "main_menu"
    LIST_MENU = "list_menu"

    SEND_ALL = "send_all"


class EnterMode(Enum):
    FILLING = "filling"
    EDITING = "editing"


class Status(Enum):
    ACCEPTED = "accepted"
    DECLINED = "declined"
