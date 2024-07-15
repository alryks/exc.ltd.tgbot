import json
import os.path

from telebot import types


SEND_ALL_MESSAGE = """
Отправьте сообщение, которое хотите отправить всем.
"""

SEND_ALL_SUCCESS_MESSAGE = """
Сообщение отправлено всем.
"""

SEND_ALL_FAIL_MESSAGE = """
Не удалось отправить сообщение всем.
"""

WELCOME_MESSAGE = """
Здравствуйте, это тестовый бот ввода информации о кандидатах.
"""

FIRST_INTERACTION_MESSAGE = """
Спасибо, что зарегестрировались в боте.
Ваш уровень доступа: {access}.
"""


ENTER_JOBS_MESSAGE = """
Выберите должность из списка.
"""


INVALID_JOBS_LIST_MESSAGE = """
Список объектов сейчас невалидный
"""

ENTER_NAME_MESSAGE = """
Введите ФИО.
"""

ENTER_GENDER_MESSAGE = """
Введите пол.
"""

ENTER_PHONE_MESSAGE = """
Введите номер телефона.
"""

ENTER_AGE_MESSAGE = """
Введите дату рождения.
"""


ENTER_DATE_ON_OBJECT_MESSAGE = """
Введите дату прибытия на объект.
"""

ENTER_RESIDENCE_MESSAGE = """
Введите гражданство.
"""

ENTER_PHOTO_MESSAGE = """
Отправьте фото паспорта.
"""

APPLICATION_DELETE_MESSAGE = """
Анкета удалена. Начинаем ввод новой анкеты.
"""

APPLICATION_SAVE_MESSAGE = """
Анкета сохранена. Начинаем ввод новой анкеты.
"""

DONT_UNDERSTOOD_MESSAGE = """
Не понял вас.
"""


def create_send_all_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("Отмена"))
    return markup

def create_redidence_markup(countries):
    markup = types.ReplyKeyboardMarkup()
    for country in countries:
        button = types.KeyboardButton(country)
        markup.row(button)
    markup.row(types.KeyboardButton("В главное меню"))
    return markup


COUNTRIES = [
    "Россия",
    "Беларусь",
    "Киргизия",
    "Казахстан",
]


def create_gender_markup(genders):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(*[types.KeyboardButton(gender)
                 for gender in genders])
    markup.row(types.KeyboardButton("В главное меню"))
    return markup


GENDERS = [
    "Мужской",
    "Женский"
]


def create_commands_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("Новая анкета"),
               types.KeyboardButton("Список анкет"))
    return markup


def create_list_commands_markup(tg_id):
    from .application import Application

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton(f"Все анкеты ({Application.count_apps(tg_id)})"),
               types.KeyboardButton(f"Новые анкеты ({Application.count_new_apps(tg_id)})"), )
    markup.row(types.KeyboardButton(f"Принятые анкеты ({Application.count_accepted_apps(tg_id)})"),
               types.KeyboardButton(f"Отклоненные анкеты ({Application.count_declined_apps(tg_id)})"),)
    markup.row(types.KeyboardButton("В главное меню"))
    return markup


def get_jobs_list():
    if os.path.exists("jobs.json"):
        with open("jobs.json", 'r') as f:
            jobs_list = json.load(f)
    else:
        jobs_list = JOBS_LIST
    jobs_list = sorted(jobs_list,
                       key=lambda x: x['объект'].lower())
    return jobs_list


def create_prefix_jobs_markup(access_db, tg_id,
                              start_letter=''):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    jobs_list = get_jobs_list()
    jobs_list = access_db.filter_jobs(tg_id, jobs_list)
    jobs_list = [job
                 for job in jobs_list
                 if job['объект'].lower().startswith(start_letter.lower())]
    prefix_list = list(set([job['объект'][:1 + len(start_letter)].lower()
                            for job in jobs_list]))
    for i in range(2 + len(start_letter),
                   5 + len(start_letter)):
        new_prefix_list = list(set([job['объект'][:i].lower()
                                    for job in jobs_list]))
        if len(new_prefix_list) > 32:
            print(new_prefix_list)
            break
        prefix_list = new_prefix_list

    prefix_list = sorted(prefix_list)
    for key in prefix_list:
        button = types.KeyboardButton(key.lower())
        markup.row(button)
    return markup


def create_jobs_markup(access_db, tg_id,
                       start_letter='',
                       gte_letter='а',
                       lte_letter='я'):
    max_jobs = 25

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    jobs_list = get_jobs_list()
    jobs_list = access_db.filter_jobs(tg_id, jobs_list)
    jobs_list = [job
                 for job in jobs_list
                 if job['объект'].lower().startswith(start_letter.lower())
                 and (job['объект'].lower()[:len(gte_letter)] >= gte_letter)
                 and (job['объект'].lower()[:len(lte_letter)] <= lte_letter)]
    print(f"JOBS NUM: {len(jobs_list)}")
    if jobs_list:
        button = types.KeyboardButton(f"В начало")
        markup.row(button)

        jobs_list = jobs_list[slice(0, max_jobs)]
        if jobs_list:
            if lte_letter == 'я':
                first_key = jobs_list[0]['объект'].lower()[:2]
                last_key = jobs_list[-1]['объект'].lower()[:2]
                for job in jobs_list:
                    key = f"{job['объект']}|{job['должность']}|{job['пол']}"
                    button = types.KeyboardButton(key)
                    markup.row(button)
            else:
                first_key = jobs_list[0]['объект'].lower()[:2]
                last_key = jobs_list[-1]['объект'].lower()[:2]
                for job in jobs_list:
                    key = f"{job['объект']}|{job['должность']}|{job['пол']}"
                    button = types.KeyboardButton(key)
                    markup.row(button)

            button_prev = types.KeyboardButton(f"Предыдущие [<={first_key}]")
            button_next = types.KeyboardButton(f"Следующие [>={last_key}]")
            markup.row(button_prev, button_next)

    markup.row(types.KeyboardButton("В главное меню"))
    return markup


def create_another_document_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("Закончить ввод фото"))
    markup.row(types.KeyboardButton("В главное меню"))
    return markup


JOBS_LIST = [
    {
        "объект": "Восток-Запад СПБ",
        "должность": "Комплектовщик",
        "возраст_от": 18,
        "возраст_до": 45,
        "гражданство": "РФ, РБ, Казахстан, Киргизия",
        "пол": "Мужской",
        "тип_работы": "Вахта",
        "вид_внешности": "славянская и не славянская внешность"
    },
    {
        "объект": "Восток-Запад СПБ",
        "должность": "Комплектовщик",
        "возраст_от": 18,
        "возраст_до": 45,
        "гражданство": "любое с документами",
        "пол": "Женский",
        "тип_работы": "Местные",
        "вид_внешности": "славянская внешность"
    }
] * 10


ResidenceReplyMarkup = create_redidence_markup(COUNTRIES)
GenderReplyMarkup = create_gender_markup(GENDERS)
NoMarkup = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton("В главное меню"))
AnotherDocumentReplyMarkup = create_another_document_markup()


class BadInformationException(Exception):
    MESSAGE = ("Не возможно распознать информацию. "
               "Проверьте информацию и повторите.")

    def MARKUP(self):
        return NoMarkup


class NameNotFoundException(BadInformationException):
    MESSAGE = ("Не возможно распознать введенное имя. "
               "Проверьте информацию и повторите.")

    def MARKUP(self):
        return NoMarkup


class JobNotFoundException(BadInformationException):
    MESSAGE = ("Не возможно распознать введенную должность. "
               "Проверьте информацию и повторите.")

    def __init__(self, access_db, tg_id, text):
        super(JobNotFoundException, self).__init__()
        self.access_db = access_db
        self.tg_id = tg_id
        self.text = text

    def MARKUP(self):
        return create_jobs_markup(access_db=self.access_db,
                                  tg_id=self.tg_id,
                                  start_letter=self.text.lower())


class GenderNotFoundException(BadInformationException):
    MESSAGE = ("Не возможно распознать введенный пол. "
               "Проверьте информацию и повторите.")

    def MARKUP(self):
        return GenderReplyMarkup


class PhoneNotFoundException(BadInformationException):
    MESSAGE = ("Не возможно распознать введенный телефон. "
               "Проверьте информацию и повторите.")

    def MARKUP(self):
        return NoMarkup


class AgeNotFoundException(BadInformationException):
    MESSAGE = ("Не возможно распознать введенный возраст. "
               "Проверьте информацию и повторите.")

    def MARKUP(self):
        return NoMarkup


class DateOnObjectNotFoundException(BadInformationException):
    MESSAGE = ("Не возможно распознать введенную дату. "
               "Проверьте информацию и повторите.")

    def MARKUP(self):
        return NoMarkup


class ResidenceNotFoundException(BadInformationException):
    MESSAGE = ("Не возможно распознать введенный адрес. "
               "Проверьте информацию и повторите.")

    def MARKUP(self):
        return ResidenceReplyMarkup


class PassportNotFoundException(BadInformationException):
    MESSAGE = ("Не нашли в вашем сообщении паспорт. "
               "Проверьте информацию и повторите."
               "или нажмите на Закончить")

    def MARKUP(self):
        return AnotherDocumentReplyMarkup


class PassportNotEnoughException(BadInformationException):
    MESSAGE = ("Добавьте хотя бы один документ.")

    def MARKUP(self):
        return AnotherDocumentReplyMarkup


def exception_handler(bot, db):
    def temp_decorator(func):

        def temp(message):
            tg_id = message.from_user.id
            try:
                func(message)
            except BadInformationException as e:
                db.delete_message_after(tg_id,
                                        message.message_id,
                                        bot.reply_to(message, e.MESSAGE,
                                                     reply_markup=e.MARKUP()).message_id)
                return

        return temp

    return temp_decorator
