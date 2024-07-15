from bson import ObjectId
from pymongo.collection import Collection

from .scenario import db
from .application import Application
from .state import State, EnterMode
from .scenario import ADMIN_IDS


class UsersDb:
    users = db.users

    def __init__(self):
        super(UsersDb, self).__init__()

    def get_all_user_ids(self):
        return [user['tg_id'] for user in self.users.find({})]

    def reset_state(self, tg_id):
        self.set_current_state(tg_id,
                               State.FIRST_INTERACTION)
        self.set_entering_mode(tg_id,
                               EnterMode.FILLING)
        application = self.get_current_application(tg_id)
        if application.data is None or application.data.get('submitted'):
            self.set_current_application(tg_id, Application.new().id)
        else:
            self.get_current_application(tg_id).reset()

    def get_current_state(self, tg_id):
        user = self.users.find_one({"tg_id": tg_id})
        if user is None:
            return State.FIRST_INTERACTION
        state = user.get("state", State.FIRST_INTERACTION)
        return State(state)

    def get_entering_mode(self, tg_id):
        user = self.users.find_one({"tg_id": tg_id})
        if user is None:
            return EnterMode.FILLING, None
        mode = user.get("mode", EnterMode.FILLING)
        return EnterMode(mode), user.get("edit_message_id")

    def set_current_state(self, tg_id,
                          state: State):
        self.users.update_one({"tg_id": tg_id},
                              {"$set": {"state": state.value}},
                              upsert=True)

    def set_entering_mode(self, tg_id,
                          mode: EnterMode,
                          edit_message_id=None):
        self.users.update_one({"tg_id": tg_id},
                              {"$set": {"mode": mode.value,
                                        "edit_message_id": edit_message_id}},
                              upsert=True)

    def delete_message_after(self, tg_id, *message_ids):
        message_ids = list(message_ids)
        self.users.update_one({"tg_id": tg_id},
                              {"$push": {"delete_message_ids": {"$each": message_ids}}},
                              upsert=True)

    def delete_messages(self, bot, tg_id):
        obj = self.users.find_one({"tg_id": tg_id})
        if obj is None:
            return
        for message_id in obj.get("delete_message_ids", []):
            try:
                bot.delete_message(chat_id=tg_id,
                                   message_id=message_id)
            except:
                pass
        self.users.update_one({"tg_id": tg_id},
                              {"$set": {"delete_message_ids": []}},
                              upsert=True)

    def is_admin(self, tg_id):
        return int(tg_id) in ADMIN_IDS

    def get_current_application(self, tg_id) -> Application:
        obj = self.users.find_one({"tg_id": tg_id})
        if obj is None:
            raise RuntimeError("Can't find user")
        if 'application_id' not in obj:
            application = Application.new()
            self.set_current_application(tg_id,
                                         application.id)
            print(application)
            return application
        application = Application(obj['application_id'])
        print(application)
        return application

    def set_current_application(self, tg_id,
                                application_id):
        self.users.update_one({"tg_id": tg_id},
                              {"$set": {"application_id": ObjectId(application_id)}},
                              upsert=True)

    def unset_current_application(self, tg_id):
        self.users.update_one({"tg_id": tg_id},
                              {"$unset": {"application_id": ""}},
                              upsert=True)


class AccessDb:
    access: Collection = db.access

    def __init__(self):
        super(AccessDb, self).__init__()

    def grant_access(self, tg_id, access_list):
        tg_id = int(tg_id)
        if "all" in access_list:
            access_list = ["all"]
        self.access.update_one({"tg_id": tg_id},
                               {"$addToSet": {"access_list": {"$each": access_list}}},
                               upsert=True)

    def deny_access(self, tg_id, access_list):
        tg_id = int(tg_id)
        if "all" in access_list:
            self.access.update_one({"tg_id": tg_id},
                                   {"$set": {"access_list": []}},
                                   upsert=True)
        else:
            self.access.update_one({"tg_id": tg_id},
                                   {"$pull": {"access_list": {"$each": access_list}}},
                                   upsert=True)

    def get_access_list(self, tg_id):
        tg_id = int(tg_id)
        obj = self.access.find_one({"tg_id": tg_id})
        if obj is None:
            return ["all"]
        else:
            return obj.get("access_list", ["all"])

    def filter_jobs(self, tg_id, jobs_list):
        access_list = self.get_access_list(tg_id)
        if "all" in access_list:
            return jobs_list
        return list(filter(lambda x: x["объект"] in access_list,
                           jobs_list))

    def clear(self):
        self.access.delete_many({})
