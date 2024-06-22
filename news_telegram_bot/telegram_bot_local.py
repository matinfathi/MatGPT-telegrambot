import asyncio
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode

from hacker_news import (
    get_news,
    get_ai_news,
    get_linux_news,
    get_today_news,
    get_high_point_news,
    get_high_comment_news,
)
from utils import logger

application = Application.builder().token(os.environ["MAT_GPT_TOKEN"]).build()
reply_keyboard = [["Today", "AI", "Linux", "High Comments", "High Points"]]
CHOOSE_NEWS = 1


async def command_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("User %s issued /start command", update.message.from_user.first_name)
    await update.message.reply_text("Welcome to MatGPT! Please select a command:")
    return ConversationHandler.END


async def command_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("User %s issued /cancel command", update.message.from_user.first_name)
    context.chat_data.clear()
    await update.message.reply_text(
        "Ok, the process is canceled.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def send_news(update: Update, context: ContextTypes.DEFAULT_TYPE, news_func) -> None:
    try:
        logger.info("Getting news for User %s ", update.message.from_user.first_name)
        all_news = get_news()
        target_news = news_func(all_news)

        if not target_news:
            raise ValueError("No News!")

        reply_message = "\n\n".join(
            [
                f'- {record.title} <a href="{record.url}">Link</a> - Points: {record.points} - Comments: {record.comments}'
                for record in target_news
            ]
        ).strip()
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        reply_message = "No News!"

    await update.message.reply_text(reply_message, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())


async def ai_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("User %s chose AI news", update.message.from_user.first_name)
    await send_news(update, context, get_ai_news)


async def linux_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("User %s chose AI news", update.message.from_user.first_name)
    await send_news(update, context, get_linux_news)


async def high_point_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("User %s chose high points news", update.message.from_user.first_name)
    await send_news(update, context, get_high_point_news)


async def high_comment_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("User %s chose high comments news", update.message.from_user.first_name)
    await send_news(update, context, get_high_comment_news)


async def today_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("User %s chose today news", update.message.from_user.first_name)
    await send_news(update, context, get_today_news)


async def command_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("User %s issued a news command", update.message.from_user.first_name)
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    await update.message.reply_text("Select an option:", reply_markup=reply_markup)
    return CHOOSE_NEWS


async def handle_news_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.message.text
    logger.info(f"The user selected '{query}'")

    if query == "Today":
        await today_news(update, context)
    elif query == "AI":
        await ai_news(update, context)
    elif query == "High Comments":
        await high_comment_news(update, context)
    elif query == "High Points":
        await high_point_news(update, context)
    elif query == "Linux":
        await linux_news(update, context)
    else:
        await update.message.reply_text("Invalid option, please try again.")
        return CHOOSE_NEWS

    return ConversationHandler.END


def main() -> None:
    application.add_handler(CommandHandler("start", command_start))
    application.add_handler(CommandHandler("cancel", command_cancel))

    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("news", command_news)],
            states={CHOOSE_NEWS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_news_selection)]},
            fallbacks=[CommandHandler("cancel", command_cancel)],
        )
    )

    application.run_polling()


def lambda_handler():
    main()
