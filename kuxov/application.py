import io
import re
from datetime import datetime

import telebot
from dateparser.date import DateDataParser
from telebot import types
from telebot.util import quick_markup

from .assets import NameNotFoundException, PhoneNotFoundException, AgeNotFoundException, COUNTRIES, \
    ResidenceNotFoundException, GENDERS, GenderNotFoundException, JOBS_LIST, JobNotFoundException, NoMarkup, \
    get_jobs_list
from .cdn import CDN
from .scenario import db
from bson import ObjectId
import phonenumbers
from PIL import Image
from pymongo.collection import Collection, ReturnDocument

from .state import Status

ddp = DateDataParser(languages=['ru'])


class Application(object):
    FIELDS = [
        "user_id",
        "submitted",
        "status",
        "reason",
        "job",
        "name",
        "gender",
        "phone",
        "age",
        "residence",
        "photo_ids",
    ]

    MAIN_FIELDS = [
        "job",
        "name",
        "gender",
        "phone",
        "age",
        "residence",
        "photo_ids",
    ]

    applications: Collection = db.applications
    cdn = CDN()

    def __init__(self, application_id: ObjectId,
                 data=None):
        super(Application, self).__init__()
        self._id = ObjectId(application_id)
        self.__data = data

    @classmethod
    def new(cls):
        application_id = cls.applications.insert_one({}).inserted_id
        return Application(application_id=application_id, data={
            '_id': ObjectId(application_id)
        })

    def delete(self):
        self.del_passport_photos()
        self.applications.delete_one({"_id": self._id})
        self.__data = None
        return None

    def reset(self):
        self.del_passport_photos()
        self.__data = self.applications.find_one_and_update({"_id": self._id},
                                                            {"$unset": {f: ""
                                                                                for f in self.FIELDS}},
                                                            return_document=ReturnDocument.AFTER)
        return self

    def save(self, tg_id):
        self.__data = self.applications.find_one_and_update({'_id': self._id},
                                                             {"$set": {
                                                                 "submitted": True,
                                                                 "user_id": tg_id
                                                             }},
                                                            return_document=ReturnDocument.AFTER)
        return self

    @property
    def id(self):
        return self._id

    @property
    def data(self):
        if self.__data is None:
            self.__data = self.applications.find_one({
                "_id": ObjectId(self._id)
            })
        return self.__data

    @staticmethod
    def remain_basic_job_fields(obj):
        if "job" not in obj:
            return obj
        obj['job'] = {
            "объект": obj['job']["объект"],
            "должность": obj['job']["должность"],
            "пол": obj['job']["пол"],
        }
        return obj

    @property
    def name(self):
        return self.data.get("name")

    @property
    def job(self):
        return self.data.get("job")

    @property
    def gender(self):
        return self.data.get("gender")

    @property
    def phone(self):
        return self.data.get("phone")

    @property
    def age(self) -> datetime:
        return self.data.get("age")

    @property
    def residence(self):
        return self.data.get("residence")

    @property
    def passport_photo(self):
        raise NotImplementedError()

    def sync(self):
        self.__data = self.applications.find_one({
            "_id": ObjectId(self._id)
        })

    def exists(self):
        self.__data = None
        return self.data is not None

    def set_name(self, name: str):
        self.__data = self.applications.find_one_and_update({"_id": self._id},
                                                            {"$set": {"name": name}},
                                                            return_document=ReturnDocument.AFTER)
        return self

    def set_gender(self, gender: str):
        self.__data = self.applications.find_one_and_update({"_id": self._id},
                                                            {"$set": {"gender": gender}},
                                                            return_document=ReturnDocument.AFTER)
        return self

    @staticmethod
    def extract_job(text: str,
                    access_db,
                    tg_id: int):
        jobs_list = get_jobs_list()
        jobs_keys = [f"{job['объект']}|{job['должность']}|{job['пол']}"
                     for job in jobs_list]
        try:
            return jobs_list[jobs_keys.index(text)]
        except:
            raise JobNotFoundException(access_db=access_db,
                                       tg_id=tg_id,
                                       text=text)

    @staticmethod
    def extract_name(text: str):
        text = text.strip().replace('.', ' ').replace('!', ' ').lower()
        if not re.match("^[а-яА-Я -]+$", text):
            raise NameNotFoundException()
        text = '-'.join([txt.strip().capitalize()
                         for txt in text.split('-')
                         if len(txt.strip()) > 0])
        text = ' '.join([txt.strip().capitalize()
                         for txt in text.split(' ')
                         if len(txt.strip()) > 0])
        return text

    def set_phone(self, phone: str):
        self.__data = self.applications.find_one_and_update({"_id": self._id},
                                                            {"$set": {"phone": phone}},
                                                            return_document=ReturnDocument.AFTER)
        return self

    def set_job(self, job: dict):
        self.__data = self.applications.find_one_and_update({"_id": self._id},
                                                            {"$set": {"job": job}},
                                                            return_document=ReturnDocument.AFTER)
        return self

    @staticmethod
    def extract_phone(text: str):
        text = text.strip()
        try:
            z = phonenumbers.parse(text, 'RU')
        except:
            raise PhoneNotFoundException()
        if not phonenumbers.is_valid_number(z):
            raise PhoneNotFoundException()
        return '+' + str(z.country_code) + str(z.national_number)

    def set_age(self, dt: datetime):
        self.__data = self.applications.find_one_and_update({"_id": self._id},
                                                            {"$set": {"age": dt}},
                                                            return_document=ReturnDocument.AFTER)
        return self

    @staticmethod
    def extract_age(text: str):
        text = text.strip()
        dt = ddp.get_date_data(text).date_obj
        if dt is None:
            raise AgeNotFoundException()
        return dt

    def set_residence(self, residence: str):
        self.__data = self.applications.find_one_and_update({"_id": self._id},
                                                            {"$set": {"residence": residence}},
                                                            return_document=ReturnDocument.AFTER)
        return self

    @staticmethod
    def extract_residence(text: str):
        text = str(text)
        for country in COUNTRIES:
            if country.lower() in text.lower():
                return country
        raise ResidenceNotFoundException()

    @staticmethod
    def extract_gender(text: str):
        text = str(text)
        for gender in GENDERS:
            if gender.lower() in text.lower():
                return gender
        raise GenderNotFoundException()

    def del_passport_photos(self):
        if self.data is None:
            return
        photo_ids = self.data.get('photo_ids', [])
        for photo_id in photo_ids:
            self.cdn.delete(photo_id)
        self.applications.update_one({"_id": self._id},
                                     {"$set": {"photo_ids": []}})

    def add_passport_photo(self, photo: Image.Image = None,
                           photo_content: bytes = None):

        if photo is None:
            f = io.BytesIO(photo_content)
            photo = Image.open(f).convert('RGB')
        photo_id = self.cdn.host_photo(photo)
        self.applications.update_one({"_id": self._id},
                                     {"$push": {"photo_ids": photo_id}})
        if self.__data is not None:
            if "photo_ids" not in self.__data:
                self.__data["photo_ids"] = []
            self.__data["photo_ids"].append(photo_id)
        return self

    @property
    def passport_files(self):
        photo_ids = self.data["photo_ids"]
        return [self.cdn.url_for(photo_id)
                for photo_id in photo_ids]

    @property
    def photo_ids(self):
        return self.data.get('photo_ids', [])

    @classmethod
    def list(cls, user_id=None):
        return [Application(obj['_id'],
                            data=obj)
                for obj in cls.applications.find({"user_id": user_id if user_id is not None else {"$exists": True}})]

    @classmethod
    def list_not_accepted(cls, user_id=None):
        return [Application(obj['_id'],
                            data=obj)
                for obj in cls.applications.find({"user_id": user_id if user_id is not None else {"$exists": True},
                                                  "status": {"$ne": Status.ACCEPTED.value}})]

    @classmethod
    def list_accepted(cls, user_id=None):
        return [Application(obj['_id'],
                            data=obj)
                for obj in cls.applications.find({"user_id": user_id if user_id is not None else {"$exists": True},
                                                  "status": Status.ACCEPTED.value})]

    @classmethod
    def list_declined(cls, user_id=None):
        return [Application(obj['_id'],
                            data=obj)
                for obj in cls.applications.find({"user_id": user_id if user_id is not None else {"$exists": True},
                                                  "status": Status.DECLINED.value})]

    @classmethod
    def list_not_verified(cls, user_id=None):
        return [Application(obj['_id'],
                            data=obj)
                for obj in cls.applications.find({"user_id": user_id if user_id is not None else {"$exists": True},
                                                  "status": {"$exists": False},
                                                  **{main_field: {"$exists": True}
                                                     for main_field in Application.MAIN_FIELDS}})]

    def present_to(self, bot: telebot.TeleBot, chat_id):
        markup = None
        if self.status != Status.ACCEPTED:
            markup = quick_markup({
                "Редактировать": {'callback_data': f"appedit_{self._id}"}
            }, row_width=1)

        urls = '\n'.join(self.passport_files)
        caption = f"""
Должность: {self.job['объект']}|{self.job['должность']}|{self.job['пол']}|от {self.job['возраст_от']} до {self.job['возраст_до']}
ФИО: {self.name}
Пол: {self.gender}
Телефон: {self.phone}
Дата рождения: {self.age.strftime('%d.%m.%Y')} ({(datetime.now() - self.age).days // 365} лет)
Резиденство: {self.residence}
Ко-во документов: {len(self.photo_ids)}
Документы:\n{urls}
        """
        bot.send_photo(chat_id,
                       photo=self.cdn.retrieve_content(self.photo_ids[0]),
                       caption=caption,
                       reply_markup=markup)

    def send_to(self, bot: telebot.TeleBot, chat_id,
                edit_message_id=None):
        markup = quick_markup({
            'Сохранить': {'callback_data': "save"},
            'Удалить': {'callback_data': "del"},
            'Сменить имя': {'callback_data': "edit_name"},
            'Сменить тел': {'callback_data': "edit_phone"},
            'Сменить пол': {'callback_data': "edit_gender"},
            'Сменить возраст': {'callback_data': "edit_age"},
            'Сменить резиденство': {'callback_data': "edit_residence"},
            'Заново добавить документы': {'callback_data': "edit_passport"},
            'Добавить документ': {'callback_data': "add_document"},
            'Сменить вакансию': {'callback_data': "edit_job"},
        }, row_width=2)
        urls = '\n'.join(self.passport_files)
        caption = f"""
Должность: {self.job['объект']}|{self.job['должность']}|{self.job['пол']}|от {self.job['возраст_от']} до {self.job['возраст_до']}
ФИО: {self.name}
Пол: {self.gender}
Телефон: {self.phone}
Дата рождения: {self.age.strftime('%d.%m.%Y')} ({(datetime.now() - self.age).days // 365} лет)
Резиденство: {self.residence}
Ко-во документов: {len(self.photo_ids)}
Документы:\n{urls}
"""
        bot.delete_message(chat_id,
                           bot.send_message(chat_id, "Создание меню...",
                                            reply_markup=NoMarkup).message_id)
        if edit_message_id is None:
            bot.send_photo(chat_id,
                           photo=self.cdn.retrieve_content(self.photo_ids[0]),
                           caption=caption,
                           reply_markup=markup)
        else:
            bot.edit_message_media(chat_id=chat_id,
                                   message_id=edit_message_id,
                                   media=types.InputMediaPhoto(self.cdn.retrieve_content(self.photo_ids[0])))
            bot.edit_message_caption(chat_id=chat_id,
                                     caption=caption,
                                     message_id=edit_message_id,
                                     reply_markup=markup)

    def __repr__(self):
        return f"Application({self.data})"

    def accept(self, reason=""):
        self.__data = self.applications.find_one_and_update({"_id": self._id},
                                                            {"$set": {"status": Status.ACCEPTED.value,
                                                                      "reason": reason}},
                                                            return_document=ReturnDocument.AFTER)
        return self

    def decline(self, reason=""):
        self.__data = self.applications.find_one_and_update({"_id": self._id},
                                                            {"$set": {"status": Status.DECLINED.value,
                                                                      "reason": reason}},
                                                            return_document=ReturnDocument.AFTER)
        return self

    @property
    def status(self):
        status = self.data.get("status")
        if status is not None:
            status = Status(status)
        return status
