from django.core.management.base import BaseCommand
from django.conf import settings
from telegram import Bot
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater
from telegram.ext import CommandHandler 
from telegram.utils.request import Request

from models.models import Message
from models.models import Profile 
from models.models import Group 

import re


def log_errors(f):

    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_message = f'ERROR: {e}'
            print(error_message)
            raise e

    return inner


@log_errors
def do_echo(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    text = update.message.text

    profile, _ = Profile.objects.get_or_create(
        external_id=chat_id,
        defaults={
            'name': update.message.from_user.username,
        }
    )
    Message(
        profile=profile,
        text=text,
    ).save()
    

    reply_text = "ID={}\n\n{}".format(chat_id, text)
    update.message.reply_text(
        text=reply_text,
    )


@log_errors 
def do_message_proc(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    text = update.message.text

    profile, _ = Profile.objects.get_or_create(
        external_id=chat_id,
        defaults={
            'name': update.message.from_user.username,
        }
    )

    first_text_word = re.split('\s+', text)[0]
    user_group_names = Group.objects.filter(profile__external_id = chat_id)


    if user_group_names.filter(group_name = first_text_word).exists():
        Message(
            profile=profile,
            text=text,
            group_name=first_text_word,
        ).save()
        update.message.reply_text(
            text=f"Message saved in group {first_text_word}"
        )
    else:
        update.message.reply_text(
            text=f"Group {first_text_word} does not exist. Message ignored"
        )


@log_errors
def do_create_group(update: Update, context: CallbackContext):
    
    chat_id = update.message.chat_id

    profile, _ = Profile.objects.get_or_create(
        external_id=chat_id,
        defaults={
            'name': update.message.from_user.username,
        }
    )

    command_text = update.message.text 
    first_line = re.split('\n', command_text)[0]
    tokens = re.split('\s+', first_line)
    non_empty_tokens = filter(lambda string: string != '', tokens)
    _, *args = non_empty_tokens 
    
    if len(args) > 0:
        group_name = args[0].lower()
        user_group_names = Group.objects.filter(profile__external_id = update.message.chat_id)


        if user_group_names.filter(group_name = group_name).exists():
            update.message.reply_text(
                text=f"Group {group_name} already exists"
            )
        else:
            Group(
                group_name=group_name,
                profile=profile 
            ).save()

    else:
        update.message.reply_text(
            text="To create a new group input valid group name"
        )
    

@log_errors
def do_show_groups(update: Update, context: CallbackContext):
    group_names = Group.objects.filter(profile__external_id = update.message.chat_id).values_list('group_name', flat=True)
    
    update.message.reply_text(
        text='\n'.join(group_names)
    )


@log_errors
def do_show_tail(update: Update, context: CallbackContext):
    pass


@log_errors
def do_show_head(update: Update, context: CallbackContext):
    pass


@log_errors
def do_count_group_msgs(update: Update, context: CallbackContext):
    pass


@log_errors
def do_show_nth_group_msg(update: Update, context: CallbackContext):
    pass


class Command(BaseCommand):
    help = 'Telegram bot'

    def handle(self, *args, **options):
        request = Request(
            connect_timeout=0.5,
            read_timeout=1.0,
        )
        bot = Bot(
            request=request,
            token=settings.TOKEN,
        )
        print(bot.get_me())


        updater = Updater(
            bot=bot, 
            use_context=True,
            )


        add_group_handler = CommandHandler('new', do_create_group)
        updater.dispatcher.add_handler(add_group_handler) 

        show_all_groups_handler = CommandHandler('show', do_show_groups)
        updater.dispatcher.add_handler(show_all_groups_handler)

        message_handler = MessageHandler(Filters.text, do_message_proc)
        updater.dispatcher.add_handler(message_handler)


        updater.start_polling()
        updater.idle()