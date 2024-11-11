import io
import re
from datetime import datetime, timedelta

import telebot
from dateparser.date import DateDataParser
from telebot import types
from telebot.util import quick_markup

from .assets import NameNotFoundException, PhoneNotFoundException, AgeNotFoundException, COUNTRIES, \
    ResidenceNotFoundException, GENDERS, GenderNotFoundException, JOBS_LIST, JobNotFoundException, NoMarkup, \
    get_jobs_list, DateOnObjectNotFoundException
from .cdn import CDN
from .scenario import db, bot, ACCEPT_ID, DECLINE_ID
from bson import ObjectId
import phonenumbers
from PIL import Image
import tempfile
import os
from pathlib import Path
from pymongo.collection import Collection, ReturnDocument

from .utils import calculate_age

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
        "comment",
    ]

    MAIN_FIELDS = [
        "job",
        "name",
        "gender",
        "phone",
        "age",
        "date_on_object",
        "residence",
        "photo_ids",
        "comment",
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
        self.delete_passport()
        self.applications.delete_one({"_id": self._id})
        self.__data = None
        return None

    def reset(self):
        self.delete_passport()
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

    def submit(self):
        self.__data = self.applications.find_one_and_update({'_id': self._id},
                                                            {"$set": {
                                                                "submitted": True,
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
    def prepare_for_api(obj):
        if "job" not in obj:
            return obj
        obj['job'] = {
            "объект": obj['job']["объект"],
            "должность": obj['job']["должность"],
            "пол": obj['job']["пол"],
        }
        obj['phone'] = "+7" + phonenumbers.format_number(phonenumbers.parse(obj['phone'], 'RU'),
                                                         phonenumbers.PhoneNumberFormat.NATIONAL)[1:]
        if "comment" in obj:
            obj['comment'] = f"СНП Бот: {obj['comment']}" if obj['comment'] else "СНП Бот: "
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
    def date_on_object(self) -> datetime:
        return self.data.get("date_on_object")

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
        jobs_list = access_db.filter_jobs(tg_id, jobs_list)
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
        if not re.match("^[а-яА-ЯёË -]+$", text):
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

    def set_date_on_object(self, dt: datetime):
        self.__data = self.applications.find_one_and_update({"_id": self._id},
                                                            {"$set": {"date_on_object": dt}},
                                                            return_document=ReturnDocument.AFTER)
        return self

    @staticmethod
    def extract_age(text: str):
        text = text.strip()
        dt: datetime = ddp.get_date_data(text).date_obj
        if dt is None:
            raise AgeNotFoundException()
        if calculate_age(dt) < 16 or calculate_age(dt) > 100:
            raise AgeNotFoundException()
        return dt

    @staticmethod
    def extract_date_on_object(text: str):
        text = text.strip()
        dt: datetime = ddp.get_date_data(text).date_obj
        if dt is None:
            raise DateOnObjectNotFoundException()

        current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if dt < current_date:
            raise DateOnObjectNotFoundException()
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

    def delete_passport(self):
        if self.data is None:
            return
        self.cdn.delete(*self.photo_ids)
        self.del_passport_pdf()
        self.__data = self.applications.find_one_and_update({"_id": self._id},
                                                            {"$set": {"photo_ids": []},
                                                             "$unset": {"photo_pdf": 1}})

    def del_passport_pdf(self):
        pdf_id = self.data.get("photo_pdf")
        if pdf_id is not None:
            self.cdn.delete(pdf_id, ext="pdf")
            self.data["photo_pdf"] = None

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

    def add_passport_pdf(self):
        self.del_passport_pdf()

        photos = [
            self.cdn.retrieve_photo(photo_id) for
            photo_id in self.photo_ids
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, "passport.pdf")
            if len(photos) > 1:
                photos[0].save(pdf_path, format="PDF", save_all=True,
                               append_images=photos[1:])
            elif len(photos) == 1:
                photos[0].save(pdf_path, format="PDF")
            else:
                Image.open("./assets/nophoto.png").save(pdf_path, format="PDF")
            pdf_id = self.cdn.host(Path(pdf_path), ext="pdf")
            self.applications.update_one({"_id": self._id},
                                            {"$set": {"photo_pdf": pdf_id}})
            self.data["photo_pdf"] = pdf_id

    @property
    def passport_pdf(self):
        pdf_id = self.data.get("photo_pdf")
        if pdf_id is None:
            self.add_passport_pdf()
            pdf_id = self.data.get("photo_pdf")
        return self.cdn.retrieve_pdf(pdf_id)

    @classmethod
    def list(cls, user_id=None):
        dt = ObjectId.from_datetime(datetime.now() - timedelta(days=2))
        return [Application(obj['_id'],
                            data=obj)
                for obj in cls.applications.find({"user_id": user_id if user_id is not None else {"$exists": True},
                                                  "$or": [{"_id": {"$gt": dt}},
                                                          {"status": {"$ne": Status.ACCEPTED.value}}]})]

    @classmethod
    def list_not_accepted(cls, user_id=None):
        return [Application(obj['_id'],
                            data=obj)
                for obj in cls.applications.find({"user_id": user_id if user_id is not None else {"$exists": True},
                                                  "status": {"$ne": Status.ACCEPTED.value}})]

    @classmethod
    def list_accepted(cls, user_id=None):
        dt = ObjectId.from_datetime(datetime.now() - timedelta(days=2))
        return [Application(obj['_id'],
                            data=obj)
                for obj in cls.applications.find({"user_id": user_id if user_id is not None else {"$exists": True},
                                                  "status": Status.ACCEPTED.value,
                                                  "_id": {"$gt": dt}})]

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

    def create_caption(self):
        job_info = "Не указана"
        if self.job:
            job_info = f"{self.job['объект']}|{self.job['должность']}|{self.job['пол']}|от {self.job['возраст_от']} до {self.job['возраст_до']}"
            
        caption = f"""
*Должность:* {job_info}
*ФИО:* {self.name}
*Пол:* {self.gender}
*Телефон:* {self.phone}
*Дата рождения:* {self.age.strftime('%d.%m.%Y')} ({calculate_age(self.age)} лет)
*Дата прибытия на объект:* {self.date_on_object.strftime('%d.%m.%Y')}
*Резиденство:* {self.residence}
*Кол-во документов:* {len(self.photo_ids)} шт.
*Комментарий:* {self.comment or 'Нет комментария'}
        """
        return caption

    def present_to(self, bot: telebot.TeleBot, chat_id):
        markup = quick_markup({
            "Редактировать": {'callback_data': f"appedit_{self._id}"}
        }, row_width=1)
        caption = self.create_caption()
        bot.send_document(chat_id,
                          types.InputFile(self.passport_pdf, "passport.pdf"),
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
            'Сменить дату прибытия': {'callback_data': "edit_date_on_object"},
            'Сменить резиденство': {'callback_data': "edit_residence"},
            'Заново добавить документы': {'callback_data': "edit_passport"},
            'Добавить документ': {'callback_data': "add_document"},
            'Сменить вакансию': {'callback_data': "edit_job"},
        }, row_width=2)
        caption = self.create_caption()
        bot.delete_message(chat_id,
                           bot.send_message(chat_id, "Создание меню...",
                                            reply_markup=NoMarkup).message_id)
        if edit_message_id is None:
            bot.send_document(chat_id,
                              types.InputFile(self.passport_pdf, "passport.pdf"),
                              caption=caption,
                              reply_markup=markup)
        else:
            bot.edit_message_media(chat_id=chat_id,
                                   message_id=edit_message_id,
                                   media=types.InputMediaDocument(types.InputFile(self.passport_pdf, "passport.pdf")))
            bot.edit_message_caption(chat_id=chat_id,
                                     caption=caption,
                                     message_id=edit_message_id,
                                     reply_markup=markup)

    def __repr__(self):
        return f"Application({self.data})"

    def accept(self, reason=""):
        obj = db.access.find_one({"tg_id": self.data.get("user_id")})
        ka = ""
        if obj is not None:
            ka = obj.get("name", "")
        for tg_id in ACCEPT_ID:
            bot.send_message(tg_id, f"Анкета корректна у КА: *{ka}*:")
            bot.send_document(tg_id,
                              types.InputFile(self.passport_pdf, "passport.pdf"),
                              caption=self.create_caption())
        self.__data = self.applications.find_one_and_update({"_id": self._id},
                                                            {"$set": {"status": Status.ACCEPTED.value,
                                                                      "reason": reason}},
                                                            return_document=ReturnDocument.AFTER)
        return self

    def decline(self, reason=""):
        obj = db.access.find_one({"tg_id": self.data.get("user_id")})
        ka = ""
        if obj is not None:
            ka = obj.get("name", "")
        for tg_id in DECLINE_ID:
            bot.send_message(tg_id, f"Найден дубликат заявки у КА *{ka}*:")
            bot.send_document(tg_id,
                              types.InputFile(self.passport_pdf, "passport.pdf"),
                              caption=self.create_caption())
        self.__data = self.applications.find_one_and_update({"_id": self._id},
                                                            {"$set": {"status": Status.DECLINED.value,
                                                                      "reason": reason}},
                                                            return_document=ReturnDocument.AFTER)
        return self

    def reset_status(self):
        self.__data = self.applications.find_one_and_update({"_id": self._id},
                                                            {"$unset": {
                                                                "status": 1,
                                                                "reason": 1},
                                                             "$set": {"edited": True}},
                                                            return_document=ReturnDocument.AFTER)
        return self

    @property
    def status(self):
        status = self.data.get("status")
        if status is not None:
            status = Status(status)
        return status

    @classmethod
    def count_apps(cls, user_id=None):
        dt = ObjectId.from_datetime(datetime.now() - timedelta(days=2))
        return cls.applications.count_documents({
            **{"user_id": user_id if user_id is not None else {"$exists": True}},
            "$or": [{"status": {"$ne": Status.ACCEPTED.value,}},
                    {"_id": {"$gt": dt},}],
        })

    @classmethod
    def count_accepted_apps(cls, user_id=None):
        dt = ObjectId.from_datetime(datetime.now() - timedelta(days=2))
        return cls.applications.count_documents({"status": Status.ACCEPTED.value,
                                                 "_id": {"$gt": dt},
                                                 **{"user_id": user_id if user_id is not None else {"$exists": True}}})

    @classmethod
    def count_declined_apps(cls, user_id=None):
        return cls.applications.count_documents({"status": Status.DECLINED.value,
                                                 **{"user_id": user_id if user_id is not None else {"$exists": True}}})

    @classmethod
    def count_new_apps(cls, user_id=None):
        return cls.applications.count_documents({"status": {"$exists": False},
                                                 **{"user_id": user_id if user_id is not None else {"$exists": True}},
                                                 **{main_field: {"$exists": True}
                                                    for main_field in Application.MAIN_FIELDS}})

    @property
    def comment(self):
        return self.data.get("comment")
    
    def set_comment(self, comment: str):
        self.__data = self.applications.find_one_and_update({"_id": self._id},
                                                            {"$set": {"comment": comment}},
                                                            return_document=ReturnDocument.AFTER)
        return self

