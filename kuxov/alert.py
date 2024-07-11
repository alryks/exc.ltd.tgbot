import traceback

from .scenario import ALERT_ID, BOT_TOKEN
import telebot

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


def alert(func):
    def temp(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception:
            message = f"""<b><i>--- ALERT START ---</i></b>
<b>Error:</b>
<pre>{telebot.formatting.escape_html(traceback.format_exc())}</pre>
<b>In function:</b> <code>{telebot.formatting.escape_html(func.__name__)}</code>
<b>Arguments:</b>"""
            for i, arg in enumerate(args):
                message += f"\n<i>{i + 1}.</i>\n{telebot.formatting.escape_html(str(arg))}"
            message += "\n\n<b>Keyword arguments:</b>"
            for key, value in kwargs.items():
                message += f"\n<i>{telebot.formatting.escape_html(key)}:</i>\n{telebot.formatting.escape_html(str(value))}"
            message += "\n\n<b><i>--- ALERT END ---</i></b>"
            messages = telebot.util.split_string(message, 4096)
            for msg in messages:
                    bot.send_message(ALERT_ID, msg)
    return temp