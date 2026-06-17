import os
from dotenv import load_dotenv
import logging
from src.coaching import llm
from src.users.onboarding import check_onboarding, save_onboarding

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, Bot
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

load_dotenv()
logger = logging.getLogger(__name__)

FIRSTNAME, LASTNAME, FITNESSLEVEL = range(3)

__all__ = ['main', 'send_message']

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not await check_onboarding(telegram_chat_id=str(chat_id)):
        await update.message.reply_text(
            "Hi! Ik ben je fitness coach en zal je helpen met je fitness doelen."
            "Stuur /cancel om te stoppen met praten met mij.\n\n"
            "Wat is je voornaam?"
        )

        return FIRSTNAME

async def lastname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["firstname"] = update.message.text
    user = update.message.from_user
    logger.info("Hallo %s %s", FIRSTNAME, user.last_name | update.message.text)
    await update.message.reply_text(
        "Okay super, zeg me nu je achternaam.",
        reply_markup=ReplyKeyboardRemove()
    )

    return LASTNAME

async def fitness_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    context.user_data["lastname"] = update.message.text
    reply_keyboard = ['Inactive', 'Lightly Active', 'Moderately Active', 'Very Active', 'Athlete']
    await update.message.reply_text(
        "Wat is je huidige fitness level?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Inactive - Athlete"
        ),
    )

    return FITNESSLEVEL

async def save_and_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    context.user_data["fitness_level"] = update.message.text
    await context.send_message(chat_id=update.effective_chat.id, text="Dit was de setup dank u!")
    if await save_onboarding({"firstname": context.user_data["firstname"],
                              "lastname": context.user_data["lastname"],
                              "fitness_level": context.user_data["fitness_level"]}):
        logger.info("User %s saved successfully.", user.first_name)
    logger.warning("Failed to save user %s", user.first_name)
    return ConversationHandler.END

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coach_result = await llm.main(message=update.message.text)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=coach_result)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Challas!", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(str(os.getenv("TELEGRAM_ACCESS_TOKEN"))).build()

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FIRSTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, lastname)],
            LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, fitness_level)],
            FITNESSLEVEL: [MessageHandler(filters.Regex("(?i)^(Inactive|Lightly active|Moderately Active|Very Active|Athlete)$"),
                                          save_and_complete)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("send_message", send_message))

    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()