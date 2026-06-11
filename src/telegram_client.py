import os
import asyncio
from dotenv import load_dotenv

import llm_client
import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CallbackContext, CommandHandler
from telegram.ext import filters, MessageHandler

load_dotenv()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"Hello I'm your fitness coach")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = ' '.join(context.args).upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

async def send_message_to_coach(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coach_result = await llm_client.main(message=update.message.text)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=coach_result)


async def send_message(message: str):
    bot = telegram.Bot(token=str(os.getenv("TELEGRAM_ACCESS_TOKEN")))
    async with bot:
        await bot.send_message(text=message, chat_id=str(os.getenv("TELEGRAM_CHAT_ID")))


if __name__ == "__main__":
    application = ApplicationBuilder().token(str(os.getenv("TELEGRAM_ACCESS_TOKEN"))).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), send_message_to_coach)
    application.add_handler(message_handler)

    caps_handler = CommandHandler('caps', caps)
    application.add_handler(caps_handler)

    application.run_polling(drop_pending_updates=True)