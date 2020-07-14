#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram_util import splitCommand, log_on_fail
from telegram.ext import Updater, MessageHandler, Filters
import export_to_telegraph
import time
import yaml
from db import DB
import threading
import link_extractor

with open('credential') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)
export_to_telegraph.token = credential['telegraph_token']

tele = Updater(credential['bot_token'], use_context=True) #@matters_subscribe_bot
debug_group = tele.bot.get_chat(420074357)

db = DB()

@log_on_fail(debug_group)
def processNote(note, channels):
	if not db.existing.add(note):
		return
	note = export_to_telegraph.export(note, force=True) or note
	for channel in channels:
		time.sleep(10)
		channel.send_message(note)
		
@log_on_fail(debug_group)
def loopImp():
	for user_id in db.sub.subscriptions():
		channels = list(db.sub.channels(user_id, tele.bot))
		domain = 'https://matters.news/'
		user_url = domain + user_id
		for note, _ in link_extractor.getLinks(user_url):
			processNote(note, channels)

def mattersLoop():
	loopImp()
	threading.Timer(60 * 60 * 2, mattersLoop).start()

@log_on_fail(debug_group)
def handleCommand(update, context):
	msg = update.effective_message
	if not msg or not msg.text.startswith('/m'):
		return
	command, text = splitCommand(msg.text)
	if 'remove' in command:
		db.sub.remove(msg.chat_id, text)
	elif 'add' in command:
		db.sub.add(msg.chat_id, text)
	msg.reply_text(db.sub.get(msg.chat_id), 
		parse_mode='markdown', disable_web_page_preview=True)

HELP_MESSAGE = '''
Commands:
/m_add - add Matters user / user link
/m_remove - remove Matters user
/m_view - view subscription

Can be used in group/channel also.

Github： https://github.com/gaoyunzhi/matters_subscribe_bot
'''

def handleHelp(update, context):
	update.message.reply_text(HELP_MESSAGE)

def handleStart(update, context):
	if 'start' in update.message.text:
		update.message.reply_text(HELP_MESSAGE)

if __name__ == '__main__':
	threading.Timer(1, mattersLoop).start() 
	dp = tele.dispatcher
	dp.add_handler(MessageHandler(Filters.command, handleCommand))
	dp.add_handler(MessageHandler(Filters.private & (~Filters.command), handleHelp))
	dp.add_handler(MessageHandler(Filters.private & Filters.command, handleStart), group=2)
	tele.start_polling()
	tele.idle()