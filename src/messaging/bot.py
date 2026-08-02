import os
from datetime import datetime
from dotenv import load_dotenv
import logging
from src.coaching.llm import main as llm_main
from src.users.onboarding import check_onboarding, save_onboarding
from src.users.goals import save_goal, get_active_goals
from src.users.crud import get_record_by_telegram
from src.users.models import User

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

FIRSTNAME, LASTNAME, AGE, GENDER, FITNESSLEVEL = range(5)
GOAL_TYPE, GOAL_DESCRIPTION, GOAL_TARGET_VALUE, GOAL_UNIT, GOAL_DEADLINE = range(5, 10)

__all__ = ['main', 'send_proactive_message']

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not await check_onboarding(telegram_chat_id=str(chat_id)):
        await update.message.reply_text(
            "Hi! Ik ben je fitness coach en zal je helpen met je fitness doelen.\n"
            "Stuur /cancel om te stoppen met praten met mij.\n\n"
            "Wat is je voornaam?"
        )

        return FIRSTNAME
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="The setup is already done")

async def lastname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["firstname"] = update.message.text
    user = update.message.from_user
    logger.info("Hallo %s", FIRSTNAME)
    await update.message.reply_text(
        "Okay super, zeg me nu je achternaam.",
        reply_markup=ReplyKeyboardRemove()
    )

    return LASTNAME

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    context.user_data["lastname"] = update.message.text

    await update.message.reply_text(
        "Wat is je leeftijd?"
    )
    return AGE

async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    context.user_data["age"] = update.message.text
    reply_keyboard = [['Male', 'Female']]

    await update.message.reply_text(
        "Wat is je gender?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Male or Female?"
        )
    )
    return GENDER

async def fitness_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    context.user_data["gender"] = update.message.text

    reply_keyboard = [
        ['Inactive', 'Lightly Active'],
        ['Moderately Active', 'Very Active'],
        ['Athlete']
    ]
    await update.message.reply_text(
        "Wat is je huidige fitness level?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Inactive - Athlete"
        ),
    )

    return FITNESSLEVEL

async def save_and_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.message.from_user
    context.user_data["fitness_level"] = update.message.text
    await context.bot.send_message(chat_id=chat_id, text="Dit was de setup dank u!")
    if await save_onboarding({
        "firstname": context.user_data["firstname"],
        "lastname": context.user_data["lastname"],
        "age": int(context.user_data["age"]),
        "gender": context.user_data["gender"],
        "fitness_level": context.user_data["fitness_level"],
        "telegram_chat_id": str(chat_id),
        "onboarding_completed": True
      }):
        logger.info("User %s saved successfully.", user.first_name)
    else:
        logger.warning("Failed to save user %s", user.first_name)
    return ConversationHandler.END

async def goals_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Nieuw doel! Stuur /cancel om te stoppen met praten met mij.\n\n"
        "Wat voor soort doel is het? (bv. '5K tijd', 'gewicht', 'kracht')"
    )
    return GOAL_TYPE

async def goal_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["goal_type"] = update.message.text
    await update.message.reply_text(
        "Okay, geef nu een korte beschrijving van je doel."
    )
    return GOAL_DESCRIPTION

async def goal_target_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["goal_description"] = update.message.text
    await update.message.reply_text(
        "Wat is je targetwaarde? (bv. 25 voor 25 minuten, of 70 voor 70kg)"
    )
    return GOAL_TARGET_VALUE

async def goal_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["goal_target_value"] = update.message.text
    await update.message.reply_text(
        "Wat is de eenheid van je doel? (bv. 'min', 'kg', 'reps')"
    )
    return GOAL_UNIT

async def goal_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["goal_unit"] = update.message.text
    await update.message.reply_text(
        "Wat is de deadline? (formaat JJJJ-MM-DD), of stuur 'geen' als er geen deadline is."
    )
    return GOAL_DEADLINE

async def save_and_complete_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.message.from_user
    deadline_text = update.message.text.strip()

    db_user = await get_record_by_telegram(User, str(chat_id))
    if not db_user:
        await update.message.reply_text("Ik kon je gebruikersprofiel niet vinden. Rond eerst /start af.")
        return ConversationHandler.END

    try:
        target_value = float(context.user_data["goal_target_value"])
    except ValueError:
        await update.message.reply_text("Dat was geen geldig getal, probeer opnieuw met /goals.")
        return ConversationHandler.END

    deadline = None
    if deadline_text.lower() != "geen":
        try:
            deadline = datetime.strptime(deadline_text, "%Y-%m-%d").date()
        except ValueError:
            await update.message.reply_text("Dat was geen geldige datum, probeer opnieuw met /goals.")
            return ConversationHandler.END

    if await save_goal({
        "user_id": db_user.id,
        "type": context.user_data["goal_type"],
        "description": context.user_data["goal_description"],
        "target_value": target_value,
        "unit": context.user_data["goal_unit"],
        "deadline": deadline,
    }):
        await update.message.reply_text("Dit doel is opgeslagen!")
        logger.info("Goal saved for user %s", user.first_name)
    else:
        await update.message.reply_text("Er ging iets mis bij het opslaan van je doel.")
        logger.warning("Failed to save goal for user %s", user.first_name)

    return ConversationHandler.END

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        user = await get_record_by_telegram(User, str(chat_id))
        logger.info("Aquired User: %s", user if user else "None")
        user_context = {}
        if user:
            active_goals = await get_active_goals(user.id)
            user_context = {
                "user_context": {"firstname": user.firstname, "lastname": user.lastname},
                "goals": [
                    {
                        "type": goal.type,
                        "description": goal.description,
                        "target_value": goal.target_value,
                        "current_value": goal.current_value,
                        "unit": goal.unit,
                        "deadline": goal.deadline.isoformat() if goal.deadline else None,
                    }
                    for goal in active_goals
                ],
            }
        coach_result = await llm_main(message=update.message.text, context=user_context)
        await context.bot.send_message(chat_id=chat_id, text=coach_result)
    except Exception as e:
        logger.error("Failed to send message: %s", e)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Challas!", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

async def send_proactive_message(text: str):
    bot = Bot(token=str(os.getenv("TELEGRAM_ACCESS_TOKEN")))
    async with bot:
        await bot.send_message(text=text, chat_id=str(os.getenv("TELEGRAM_CHAT_ID")))

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(str(os.getenv("TELEGRAM_ACCESS_TOKEN"))).build()

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FIRSTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, lastname)],
            LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, fitness_level)],
            FITNESSLEVEL: [MessageHandler(filters.Regex("(?i)^(Inactive|Lightly active|Moderately Active|Very Active|Athlete)$"),
                                          save_and_complete)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    goals_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("goals", goals_start)],
        states={
            GOAL_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_description)],
            GOAL_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_target_value)],
            GOAL_TARGET_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_unit)],
            GOAL_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_deadline)],
            GOAL_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_and_complete_goal)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(goals_conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_message))

    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
