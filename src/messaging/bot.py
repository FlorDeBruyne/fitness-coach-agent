import os
from datetime import datetime
from dotenv import load_dotenv
import logging
from src.coaching.llm import main as llm_main
from src.coaching.extraction import parse_goal_value, parse_goal_intro
from src.users.onboarding import check_onboarding, save_onboarding
from src.users.goals import save_goal, get_active_goals, complete_goal, GOAL_TYPES
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
GOAL_INTRO, GOAL_TYPE_FALLBACK, GOAL_TARGET_CONFIRM, GOAL_TARGET_VALUE, GOAL_UNIT, GOAL_DEADLINE_FALLBACK = range(5, 11)
COMPLETE_SELECT = 11

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

def _goal_type_keyboard() -> list:
    return [GOAL_TYPES[i:i + 2] for i in range(0, len(GOAL_TYPES), 2)]

async def goals_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Nieuw doel! Stuur /cancel om te stoppen met praten met mij.\n\n"
        "Vertel me over je doel — wat wil je bereiken en tegen wanneer?",
        reply_markup=ReplyKeyboardRemove()
    )
    return GOAL_INTRO

async def _ask_next_goal_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("goal_type"):
        await update.message.reply_text(
            "Wat voor soort doel is het?",
            reply_markup=ReplyKeyboardMarkup(_goal_type_keyboard(), one_time_keyboard=True)
        )
        return GOAL_TYPE_FALLBACK

    if "goal_deadline" not in context.user_data:
        await update.message.reply_text(
            "Wat is de deadline? (formaat JJJJ-MM-DD), of stuur 'geen' als er geen deadline is.",
            reply_markup=ReplyKeyboardRemove()
        )
        return GOAL_DEADLINE_FALLBACK

    if "suggested_target_value" in context.user_data:
        value = context.user_data["suggested_target_value"]
        unit = context.user_data["suggested_unit"]
        await update.message.reply_text(
            f"Ik vermoed dat je doel {value:g}{unit} is — klopt dat? "
            "Stuur 'ja' om te bevestigen, of geef de juiste waarde."
        )
        return GOAL_TARGET_CONFIRM

    await update.message.reply_text(
        "Wat is je targetwaarde? (bv. 25 voor 25 minuten, of 70 voor 70kg)"
    )
    return GOAL_TARGET_VALUE

async def goal_intro_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data["goal_description"] = text

    parsed = await parse_goal_intro(text)

    if parsed["type"]:
        context.user_data["goal_type"] = parsed["type"]

    if parsed["deadline"]:
        try:
            context.user_data["goal_deadline"] = datetime.strptime(parsed["deadline"], "%Y-%m-%d").date()
        except ValueError:
            pass

    if parsed["target_value"] is not None and parsed["unit"]:
        context.user_data["suggested_target_value"] = parsed["target_value"]
        context.user_data["suggested_unit"] = parsed["unit"]

    return await _ask_next_goal_step(update, context)

async def goal_target_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.lower() in ("ja", "yes"):
        context.user_data["goal_target_value"] = context.user_data.pop("suggested_target_value")
        context.user_data["goal_unit"] = context.user_data.pop("suggested_unit")
        return await save_and_complete_goal(update, context)

    context.user_data.pop("suggested_target_value", None)
    context.user_data.pop("suggested_unit", None)
    return await goal_unit(update, context)

async def goal_type_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goal_type = update.message.text.strip().lower()
    if goal_type not in GOAL_TYPES:
        await update.message.reply_text(
            "Kies een van de opties hieronder.",
            reply_markup=ReplyKeyboardMarkup(_goal_type_keyboard(), one_time_keyboard=True)
        )
        return GOAL_TYPE_FALLBACK

    context.user_data["goal_type"] = goal_type
    return await _ask_next_goal_step(update, context)

async def goal_deadline_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deadline_text = update.message.text.strip()

    if deadline_text.lower() == "geen":
        context.user_data["goal_deadline"] = None
    else:
        try:
            context.user_data["goal_deadline"] = datetime.strptime(deadline_text, "%Y-%m-%d").date()
        except ValueError:
            await update.message.reply_text(
                "Dat was geen geldige datum, probeer opnieuw. (formaat JJJJ-MM-DD, of 'geen')"
            )
            return GOAL_DEADLINE_FALLBACK

    return await _ask_next_goal_step(update, context)

async def goal_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parsed = await parse_goal_value(update.message.text)

    if parsed["value"] is None:
        await update.message.reply_text(
            "Dat kon ik niet als getal herkennen, probeer opnieuw. (bv. 25 voor 25 minuten, of 70 voor 70kg)"
        )
        return GOAL_TARGET_VALUE

    context.user_data["goal_target_value"] = parsed["value"]

    if not parsed["unit"]:
        await update.message.reply_text(
            "Wat is de eenheid van je doel? (bv. 'min', 'kg', 'reps')"
        )
        return GOAL_UNIT

    context.user_data["goal_unit"] = parsed["unit"]
    return await save_and_complete_goal(update, context)

async def goal_unit_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["goal_unit"] = update.message.text
    return await save_and_complete_goal(update, context)

async def save_and_complete_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.message.from_user

    db_user = await get_record_by_telegram(User, str(chat_id))
    if not db_user:
        await update.message.reply_text("Ik kon je gebruikersprofiel niet vinden. Rond eerst /start af.")
        return ConversationHandler.END

    if await save_goal({
        "user_id": db_user.id,
        "type": context.user_data["goal_type"],
        "description": context.user_data["goal_description"],
        "target_value": context.user_data["goal_target_value"],
        "unit": context.user_data["goal_unit"],
        "deadline": context.user_data.get("goal_deadline"),
    }):
        await update.message.reply_text("Dit doel is opgeslagen!")
        logger.info("Goal saved for user %s", user.first_name)
    else:
        await update.message.reply_text("Er ging iets mis bij het opslaan van je doel.")
        logger.warning("Failed to save goal for user %s", user.first_name)

    return ConversationHandler.END

def _build_goal_labels(goals: list) -> dict:
    type_counts = {}
    for goal in goals:
        type_counts[goal.type] = type_counts.get(goal.type, 0) + 1

    labels = {}
    for goal in goals:
        if type_counts[goal.type] > 1:
            label = f"{goal.type} — {goal.target_value:g}{goal.unit or ''}"
        else:
            label = goal.type
        labels[label] = goal.id
    return labels

async def complete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db_user = await get_record_by_telegram(User, str(chat_id))
    if not db_user:
        await update.message.reply_text("Ik kon je gebruikersprofiel niet vinden. Rond eerst /start af.")
        return ConversationHandler.END

    active_goals = await get_active_goals(db_user.id)
    if not active_goals:
        await update.message.reply_text("Je hebt geen actieve doelen.")
        return ConversationHandler.END

    labels = _build_goal_labels(active_goals)
    context.user_data["complete_options"] = labels

    reply_keyboard = [[label] for label in labels.keys()]
    await update.message.reply_text(
        "Welk doel heb je voltooid? Stuur /cancel om te stoppen.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return COMPLETE_SELECT

async def complete_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    label = update.message.text
    options = context.user_data.get("complete_options", {})
    goal_id = options.get(label)

    if not goal_id:
        reply_keyboard = [[option] for option in options.keys()]
        await update.message.reply_text(
            "Kies een van de opties hieronder.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return COMPLETE_SELECT

    if await complete_goal(goal_id):
        await update.message.reply_text(
            "Goed bezig! Dit doel is gemarkeerd als voltooid.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            "Er ging iets mis bij het voltooien van je doel.",
            reply_markup=ReplyKeyboardRemove()
        )

    return ConversationHandler.END

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        user = await get_record_by_telegram(User, str(chat_id))
        logger.info("Aquired User: %s", user if user else "None")
        coach_result = await llm_main(message=update.message.text, user=user)
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
            GOAL_INTRO: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_intro_received)],
            GOAL_TYPE_FALLBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_type_fallback)],
            GOAL_TARGET_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_target_confirm)],
            GOAL_TARGET_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_unit)],
            GOAL_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_unit_fallback)],
            GOAL_DEADLINE_FALLBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_deadline_fallback)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    complete_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("complete", complete_start)],
        states={
            COMPLETE_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, complete_select)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(goals_conv_handler)
    application.add_handler(complete_conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_message))

    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
