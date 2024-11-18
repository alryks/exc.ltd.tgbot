from bson import ObjectId
from parse import parse
from telebot import types
from kuxov.application import Application
from kuxov.scenario import bot, SPREADSHEET_RANGE_LOGS
from kuxov.assets import SEND_ALL_MESSAGE, SEND_ALL_SUCCESS_MESSAGE, SEND_ALL_FAIL_MESSAGE, create_send_all_markup, \
    FIRST_INTERACTION_MESSAGE, ENTER_NAME_MESSAGE, ENTER_PHONE_MESSAGE, ENTER_AGE_MESSAGE, \
    ENTER_RESIDENCE_MESSAGE, ENTER_PHOTO_MESSAGE, NameNotFoundException, PhoneNotFoundException, AgeNotFoundException, \
    ResidenceNotFoundException, PassportNotFoundException, APPLICATION_DELETE_MESSAGE, APPLICATION_SAVE_MESSAGE, \
    ResidenceReplyMarkup, WELCOME_MESSAGE, NoMarkup, GenderNotFoundException, ENTER_GENDER_MESSAGE, GenderReplyMarkup, \
    create_jobs_markup, exception_handler, ENTER_JOBS_MESSAGE, AnotherDocumentReplyMarkup, create_commands_markup, \
    create_list_commands_markup, DONT_UNDERSTOOD_MESSAGE, PassportNotEnoughException, INVALID_JOBS_LIST_MESSAGE, \
    ENTER_DATE_ON_OBJECT_MESSAGE, ENTER_COMMENT_MESSAGE, SkipCommentReplyMarkup
from kuxov.db import UsersDb, AccessDb
from kuxov.state import State, EnterMode, ListMode
from kuxov.utils import update_table


db = UsersDb()
access_db = AccessDb()


@bot.message_handler(commands=['start'],)
@bot.message_handler(func=lambda message: message.text == "В главное меню")
@exception_handler(bot, db)
def welcome(message: types.Message):
    raise NotImplementedError()
    tg_id = message.from_user.id
    db.set_current_state(tg_id, State.MAIN_MENU)
    bot.reply_to(message, WELCOME_MESSAGE,
                 reply_markup=create_commands_markup())


@bot.message_handler(func=lambda message: db.is_admin(message.from_user.id),
                     commands=['sendall'],)
@exception_handler(bot, db)
def start_send_all(message: types.Message):
    tg_id = message.from_user.id
    db.set_current_state(tg_id, State.SEND_ALL)
    bot.reply_to(message, SEND_ALL_MESSAGE, reply_markup=create_send_all_markup())


@bot.message_handler(func=lambda message: db.get_current_state(message.from_user.id) == State.SEND_ALL and db.is_admin(message.from_user.id),
                     content_types=['audio', 'photo', 'voice', 'video', 'document', 'text', 'location', 'contact', 'sticker'])
@exception_handler(bot, db)
def send_all(message: types.Message):
    if message.text == "Отмена":
        return welcome(message)
    user_ids = db.get_all_user_ids()
    try:
        for user_id in user_ids:
            bot.copy_message(user_id, message.chat.id, message.message_id)
        bot.reply_to(message, SEND_ALL_SUCCESS_MESSAGE)
    except:
        bot.reply_to(message, SEND_ALL_FAIL_MESSAGE)
    return welcome(message)


@bot.message_handler(func=lambda message: message.text == "Новая анкета")
@exception_handler(bot, db)
def reset(message: types.Message):
    tg_id = message.from_user.id
    db.reset_state(tg_id)
    try:
        bot.send_message(tg_id,
                         ENTER_JOBS_MESSAGE,
                         reply_markup=create_jobs_markup(access_db=access_db,
                                                         tg_id=tg_id))
    except:
        with open("jobs.json", 'r') as f:
            jobs_list_content = f.read()
        bot.send_message(tg_id,
                         INVALID_JOBS_LIST_MESSAGE + f"\n```{jobs_list_content}```")
        return
    db.set_current_state(tg_id,
                         State.ENTER_JOB)


@bot.message_handler(func=lambda message: any(message.text.startswith(com)
                                              for com in ["Список анкет",
                                                          "Все анкеты",
                                                          "Новые анкеты",
                                                          "Принятые анкеты",
                                                          "Отклоненные анкеты"]))
@exception_handler(bot, db)
def list_welcome(message: types.Message):
    tg_id = message.from_user.id
    db.set_current_state(tg_id, State.LIST_MENU)

    if message.text.startswith("Все анкеты"):
        list_mode = ListMode.ALL
        applications = Application.list(tg_id)
    elif message.text.startswith("Список анкет"):
        list_mode = ListMode.ALL
        applications = None
    elif message.text.startswith("Новые анкеты"):
        list_mode = ListMode.NEW
        applications = Application.list_not_verified(tg_id)
    elif message.text.startswith("Отклоненные анкеты"):
        list_mode = ListMode.DECLINED
        applications = Application.list_declined(tg_id)
        bot.send_message(tg_id, "Обратитесь к вашему менеджеру по поводу отклоненных анкет.")
    elif message.text.startswith("Принятые анкеты"):
        list_mode = ListMode.ACCEPTED
        applications = Application.list_accepted(tg_id)
    else:
        applications = []

    if applications is not None:
        if len(applications) == 0:
            bot.send_message(tg_id, "Пусто.")
        else:
            send_applications_page(bot, tg_id, applications, 0, list_mode)

    bot.send_message(tg_id,
                     "Какие анкеты интересуют ?",
                     reply_markup=create_list_commands_markup(tg_id))

@exception_handler(bot, db)
def send_applications_page(bot, tg_id, applications, page, list_mode):
    APPS_PER_PAGE = 5
    total_pages = (len(applications) + APPS_PER_PAGE - 1) // APPS_PER_PAGE
    
    start_idx = page * APPS_PER_PAGE
    end_idx = min(start_idx + APPS_PER_PAGE, len(applications))
    
    message_text = ""
    for i, app in enumerate(applications[start_idx:end_idx], 1):
        message_text += f"{i}. {app.get_list_item()}\n"
    
    markup = types.InlineKeyboardMarkup(row_width=5)

    app_buttons = []
    for i in range(1, end_idx - start_idx + 1):
        app_buttons.append(types.InlineKeyboardButton(
            str(i),
            callback_data=f"show_app_{applications[start_idx + i - 1].id}"
        ))
    markup.add(*app_buttons)
    
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(types.InlineKeyboardButton("<<", callback_data=f"page_{list_mode.name}_{page-1}"))
        nav_buttons.append(types.InlineKeyboardButton(
            f"{page + 1}/{total_pages}",
            callback_data="current_page"
        ))
        if page < total_pages - 1:
            nav_buttons.append(types.InlineKeyboardButton(">>", callback_data=f"page_{list_mode.name}_{page+1}"))
        markup.row(*nav_buttons)
    
    bot.send_message(tg_id, message_text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith(('page_', 'show_app_', 'current_page')))
@exception_handler(bot, db)
def handle_pagination(call):
    tg_id = call.from_user.id
    if call.data == 'current_page':
        bot.answer_callback_query(call.id)
        return
        
    if call.data.startswith('page_'):
        list_mode = ListMode[call.data.split('_')[1]]
        page = int(call.data.split('_')[2])
        if list_mode == ListMode.ALL:
            applications = Application.list(tg_id)
        elif list_mode == ListMode.NEW:
            applications = Application.list_not_verified(tg_id)
        elif list_mode == ListMode.DECLINED:
            applications = Application.list_declined(tg_id)
        elif list_mode == ListMode.ACCEPTED:
            applications = Application.list_accepted(tg_id)
        else:
            raise NotImplementedError()
        if applications:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_applications_page(bot, tg_id, applications, page, list_mode)
            
    elif call.data.startswith('show_app_'):
        app_id = ObjectId(call.data.split('_')[2])
        application = Application(app_id)
        application.present_to(bot, tg_id)
            
    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: True,
                     content_types=["text", "photo"])
@exception_handler(bot, db)
def send_welcome(message: types.Message):
    tg_id = message.from_user.id
    db.delete_messages(bot, tg_id)
    state = db.get_current_state(tg_id=tg_id)
    mode, edit_message_id = db.get_entering_mode(tg_id)
    application = db.get_current_application(tg_id)

    if state == State.FIRST_INTERACTION:
        access = "user" if not db.is_admin(tg_id) else "admin"
        bot.reply_to(message,
                     FIRST_INTERACTION_MESSAGE.format(access=access))
        bot.send_message(tg_id,
                         ENTER_JOBS_MESSAGE,
                         reply_markup=create_jobs_markup(access_db=access_db,
                                                         tg_id=tg_id))
        db.set_current_state(tg_id,
                             State.ENTER_JOB)

    elif state == State.ENTER_JOB:
        if message.text.startswith(f"Следующие"):
            key = parse("Следующие [>={}]",
                        message.text).fixed[0]
            bot.delete_message(tg_id,
                               message.message_id)
            db.delete_message_after(tg_id,
                                    bot.send_message(tg_id,
                                                     ENTER_JOBS_MESSAGE,
                                                     reply_markup=create_jobs_markup(access_db=access_db,
                                                                                     tg_id=tg_id,
                                                                                     gte_letter=key)).message_id)
            return
        if message.text.startswith(f"В начало"):
            bot.delete_message(tg_id,
                               message.message_id)
            db.delete_message_after(tg_id,
                                    bot.send_message(tg_id,
                                                     ENTER_JOBS_MESSAGE,
                                                     reply_markup=create_jobs_markup(access_db=access_db,
                                                                                     tg_id=tg_id)).message_id)
            return

        if message.text.startswith(f"Предыдущие"):
            key = parse("Предыдущие [<={}]",
                        message.text).fixed[0]
            bot.delete_message(tg_id,
                               message.message_id)
            db.delete_message_after(tg_id,
                                    bot.send_message(tg_id,
                                                     ENTER_JOBS_MESSAGE,
                                                     reply_markup=create_jobs_markup(access_db=access_db,
                                                                                     tg_id=tg_id,
                                                                                     lte_letter=key)).message_id)
            return
        job = application.extract_job(message.text,
                                      access_db=access_db,
                                      tg_id=tg_id)
        application.set_job(job)
        if mode == EnterMode.FILLING:
            bot.send_message(tg_id,
                             ENTER_NAME_MESSAGE,
                             reply_markup=NoMarkup)
            db.set_current_state(tg_id,
                                 State.ENTER_NAME)
        elif mode == EnterMode.EDITING:
            bot.delete_message(tg_id,
                               message.message_id)
            application.send_to(bot, message.chat.id,
                                edit_message_id=edit_message_id)
            db.set_entering_mode(message.chat.id, EnterMode.FILLING)

    elif state == State.ENTER_NAME:
        name = application.extract_name(message.text)
        application.set_name(name)

        if mode == EnterMode.FILLING:
            bot.send_message(message.chat.id, ENTER_GENDER_MESSAGE,
                             reply_markup=GenderReplyMarkup)
            db.set_current_state(message.chat.id, State.ENTER_GENDER)
        elif mode == EnterMode.EDITING:
            bot.delete_message(tg_id,
                               message.message_id)
            application.send_to(bot, message.chat.id,
                                edit_message_id=edit_message_id)
            db.set_entering_mode(message.chat.id, EnterMode.FILLING)

    elif state == State.ENTER_GENDER:
        gender = application.extract_gender(message.text)
        application.set_gender(gender)

        if mode == EnterMode.FILLING:
            bot.send_message(message.chat.id, ENTER_PHONE_MESSAGE,
                             reply_markup=NoMarkup)
            db.set_current_state(message.chat.id, State.ENTER_PHONE)
        elif mode == EnterMode.EDITING:
            bot.delete_message(tg_id,
                               message.message_id)
            application.send_to(bot, message.chat.id,
                                edit_message_id=edit_message_id)
            db.set_entering_mode(message.chat.id, EnterMode.FILLING)

    elif state == State.ENTER_PHONE:
        phone = application.extract_phone(message.text)
        application.set_phone(phone)

        if mode == EnterMode.FILLING:
            bot.send_message(message.chat.id,
                             ENTER_AGE_MESSAGE,
                             reply_markup=NoMarkup)
            db.set_current_state(message.chat.id, State.ENTER_AGE)
        elif mode == EnterMode.EDITING:
            bot.delete_message(message.chat.id,
                               message.message_id)
            application.send_to(bot, message.chat.id,
                                edit_message_id=edit_message_id)
            db.set_entering_mode(message.chat.id, EnterMode.FILLING)
    elif state == State.ENTER_AGE:
        age = application.extract_age(message.text)
        application.set_age(age)

        if mode == EnterMode.FILLING:
            bot.send_message(message.chat.id,
                             ENTER_DATE_ON_OBJECT_MESSAGE,
                             reply_markup=NoMarkup)
            db.set_current_state(message.chat.id, State.ENTER_DATE_ON_OBJECT)
        elif mode == EnterMode.EDITING:
            bot.delete_message(message.chat.id,
                               message.message_id)
            application.send_to(bot, message.chat.id,
                                edit_message_id=edit_message_id)
            db.set_entering_mode(message.chat.id, EnterMode.FILLING)
    elif state == State.ENTER_DATE_ON_OBJECT:
        date_on_object = application.extract_date_on_object(message.text)
        application.set_date_on_object(date_on_object)

        if mode == EnterMode.FILLING:
            bot.send_message(message.chat.id,
                             ENTER_RESIDENCE_MESSAGE,
                             reply_markup=ResidenceReplyMarkup)
            db.set_current_state(message.chat.id, State.ENTER_RESIDENCE)
        elif mode == EnterMode.EDITING:
            bot.delete_message(message.chat.id,
                               message.message_id)
            application.send_to(bot, message.chat.id,
                                edit_message_id=edit_message_id)
            db.set_entering_mode(message.chat.id, EnterMode.FILLING)
    elif state == State.ENTER_RESIDENCE:
        residence = application.extract_residence(message.text)
        application.set_residence(residence)
        if mode == EnterMode.FILLING:
            bot.send_message(message.chat.id,
                             ENTER_PHOTO_MESSAGE,
                             reply_markup=NoMarkup)
            db.set_current_state(message.chat.id, State.ENTER_PHOTO)
        elif mode == EnterMode.EDITING:
            bot.delete_message(message.chat.id,
                               message.message_id)
            application.send_to(bot, message.chat.id,
                                edit_message_id=edit_message_id)
            db.set_entering_mode(message.chat.id,
                                 EnterMode.FILLING)
    elif state == State.ENTER_PHOTO:
        if message.text == "Закончить ввод фото" and len(application.photo_ids) > 0:
            bot.send_message(message.chat.id,
                             ENTER_COMMENT_MESSAGE,
                             reply_markup=SkipCommentReplyMarkup)
            db.set_current_state(message.chat.id, State.ENTER_COMMENT)
            return

        if message.photo:
            for photo in message.photo[-1:]:
                file_id = photo.file_id
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                application.add_passport_photo(photo_content=downloaded_file)

            if mode == EnterMode.FILLING:
                bot.send_message(message.chat.id,
                                 ENTER_PHOTO_MESSAGE,
                                 reply_markup=AnotherDocumentReplyMarkup)
            elif mode == EnterMode.EDITING:
                bot.delete_message(message.chat.id,
                                   message.message_id)
                application.add_passport_pdf()
                application.send_to(bot, message.chat.id,
                                    edit_message_id=edit_message_id)
                db.set_entering_mode(message.chat.id,
                                     EnterMode.FILLING)
            return
        elif message.text == "Закончить ввод фото":
            db.delete_message_after(tg_id,
                                    message.message_id,
                                    bot.reply_to(message,
                                                 PassportNotEnoughException.MESSAGE).message_id)
            return
        else:
            db.delete_message_after(tg_id,
                                    message.message_id,
                                    bot.reply_to(message,
                                                 PassportNotFoundException.MESSAGE).message_id)
            return
    elif state == State.ENTER_COMMENT:
        if message.text != "Пропустить":
            application.set_comment(message.text)
        else:
            application.set_comment("")
        bot.delete_message(message.chat.id,
                           message.message_id)
        application.send_to(bot, message.chat.id,
                            edit_message_id=edit_message_id)
        db.set_entering_mode(message.chat.id,
                             EnterMode.FILLING)
    else:
        db.delete_message_after(tg_id,
                                bot.reply_to(message, DONT_UNDERSTOOD_MESSAGE).message_id)
        return
    update_table(SPREADSHEET_RANGE_LOGS, application.data, access_db, db)

@bot.callback_query_handler(func=lambda call: True)
def handle_clicks(call: types.CallbackQuery):
    tg_id = call.from_user.id
    # bot.delete_message(tg_id, call.message.message_id)
    if call.data.startswith("appedit_"):
        application = Application(ObjectId(call.data.split("appedit_")[1]))
        application.reset_status()
        db.set_current_application(tg_id=tg_id, application_id=application.id)
        application.send_to(bot,
                            call.message.chat.id)
        return

    application: Application = db.get_current_application(call.from_user.id)
    if call.data == "edit_passport":
        application.delete_passport()
        db.delete_message_after(call.from_user.id,
                                bot.send_message(call.from_user.id,
                                                 ENTER_PHOTO_MESSAGE).message_id)
        db.set_current_state(call.from_user.id,
                             State.ENTER_PHOTO)
        db.set_entering_mode(call.from_user.id, EnterMode.EDITING,
                             edit_message_id=call.message.message_id)
    elif call.data == "add_document":
        db.delete_message_after(call.from_user.id,
                                bot.send_message(call.from_user.id,
                                                 ENTER_PHOTO_MESSAGE,
                                                 reply_markup=AnotherDocumentReplyMarkup).message_id)
        db.set_current_state(call.from_user.id,
                             State.ENTER_PHOTO)
        db.set_entering_mode(call.from_user.id, EnterMode.EDITING,
                             edit_message_id=call.message.message_id)
    elif call.data == "edit_residence":
        db.delete_message_after(call.from_user.id,
                                bot.send_message(call.from_user.id,
                                                 ENTER_RESIDENCE_MESSAGE,
                                                 reply_markup=ResidenceReplyMarkup).message_id)
        db.set_current_state(call.from_user.id, State.ENTER_RESIDENCE)
        db.set_entering_mode(call.from_user.id, EnterMode.EDITING,
                             edit_message_id=call.message.message_id)
    elif call.data == "edit_age":
        db.delete_message_after(call.from_user.id,
                                bot.send_message(call.from_user.id, ENTER_AGE_MESSAGE).message_id)
        db.set_current_state(call.from_user.id, State.ENTER_AGE)
        db.set_entering_mode(call.from_user.id, EnterMode.EDITING,
                             edit_message_id=call.message.message_id)
    elif call.data == "edit_date_on_object":
        db.delete_message_after(call.from_user.id,
                                bot.send_message(call.from_user.id, ENTER_DATE_ON_OBJECT_MESSAGE).message_id)
        db.set_current_state(call.from_user.id, State.ENTER_DATE_ON_OBJECT)
        db.set_entering_mode(call.from_user.id, EnterMode.EDITING,
                             edit_message_id=call.message.message_id)
    elif call.data == "edit_job":
        db.delete_message_after(call.from_user.id,
                                bot.send_message(call.from_user.id,
                                                 ENTER_JOBS_MESSAGE,
                                                 reply_markup=create_jobs_markup(access_db=access_db,
                                                                                 tg_id=tg_id)).message_id)
        db.set_current_state(call.from_user.id, State.ENTER_JOB)
        db.set_entering_mode(call.from_user.id, EnterMode.EDITING,
                             edit_message_id=call.message.message_id)
    elif call.data == "edit_phone":
        db.delete_message_after(call.from_user.id,
                                bot.send_message(call.from_user.id, ENTER_PHONE_MESSAGE).message_id)
        db.set_current_state(call.from_user.id, State.ENTER_PHONE)
        db.set_entering_mode(call.from_user.id, EnterMode.EDITING,
                             edit_message_id=call.message.message_id)
    elif call.data == "edit_name":
        db.delete_message_after(call.from_user.id,
                                bot.send_message(call.from_user.id, ENTER_NAME_MESSAGE).message_id)
        db.set_current_state(call.from_user.id, State.ENTER_NAME)
        db.set_entering_mode(call.from_user.id, EnterMode.EDITING,
                             edit_message_id=call.message.message_id)
    elif call.data == "edit_gender":
        db.delete_message_after(call.from_user.id,
                                bot.send_message(call.from_user.id,
                                                 ENTER_GENDER_MESSAGE,
                                                 reply_markup=GenderReplyMarkup).message_id)
        db.set_current_state(call.from_user.id, State.ENTER_GENDER)
        db.set_entering_mode(call.from_user.id, EnterMode.EDITING,
                             edit_message_id=call.message.message_id)
    elif call.data == "del":
        application.delete()
        bot.send_message(call.from_user.id, APPLICATION_DELETE_MESSAGE)
        db.set_current_state(tg_id, State.MAIN_MENU)
        db.unset_current_application(tg_id)
        bot.send_message(tg_id, WELCOME_MESSAGE,
                         reply_markup=create_commands_markup())
    elif call.data == "save":
        application.save(call.from_user.id)
        bot.send_message(call.from_user.id, APPLICATION_SAVE_MESSAGE)
        db.set_current_state(tg_id, State.MAIN_MENU)
        db.unset_current_application(tg_id)
        bot.send_message(tg_id, WELCOME_MESSAGE,
                         reply_markup=create_commands_markup())
        update_table(SPREADSHEET_RANGE_LOGS, application.data, access_db, db)
    else:
        raise NotImplementedError()


@bot.message_handler(func=lambda message: True)
@exception_handler(bot, db)
def send_welcome_for_other(message: types.Message):
    print(message)
    return


bot.infinity_polling()
