import asyncio
import json
import os

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    CallbackContext,
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
    get_today_news,
    get_high_point_news,
    get_high_comment_news,
)
from utils import logger


reply_keyboard = [["Today", "AI", "High Comments", "High Points"]]
CHOOSE_NEWS = 1


async def start(update: Update, context: CallbackContext) -> None:
    logger.info("User %s issued /start command", update.message.from_user.first_name)
    await update.message.reply_text(
        "Welcome to MatGPT! Please select a command:",
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("User %s issued /cancel command", update.message.from_user.first_name)
    context.chat_data.clear()
    await update.message.reply_text(
        "Ok, the process is canceled.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def send_news(update: Update, context: CallbackContext, news_func) -> None:
    """
    Fetch and send news using the provided news function.
    """
    try:
        logger.info(
            "Getting news for User %s ", update.message.from_user.first_name
        )
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

    await update.message.reply_text(reply_message, parse_mode=ParseMode.HTML)


async def ai_news(update: Update, context: CallbackContext) -> None:
    logger.info(
        "User %s chose AI news", update.message.from_user.first_name
    )
    await send_news(update, context, get_ai_news)


async def high_point_news(update: Update, context: CallbackContext) -> None:
    logger.info(
        "User %s chose high points news", update.message.from_user.first_name
    )
    await send_news(update, context, get_high_point_news)


async def high_comment_news(update: Update, context: CallbackContext) -> None:
    logger.info(
        "User %s chose high comments news", update.message.from_user.first_name
    )
    await send_news(update, context, get_high_comment_news)


async def today_news(update: Update, context: CallbackContext) -> None:
    logger.info(
        "User %s chose today news", update.message.from_user.first_name
    )
    await send_news(update, context, get_today_news)


async def news(update: Update, context: CallbackContext) -> int:
    logger.info(
        "User %s issued a news command", update.message.from_user.first_name
    )
    await update.message.reply_text(
        "Select an option:",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
        ),
    )
    return CHOOSE_NEWS


async def handle_news_text(update: Update, context: CallbackContext) -> int:
    """
    Handle the callback queries from the inline keyboard buttons.
    """
    query = update.message.text

    if query == "Today":
        await today_news(update, context)
    elif query == "AI":
        await ai_news(update, context)
    elif query == "High Comments":
        await high_comment_news(update, context)
    elif query == "High Points":
        await high_point_news(update, context)

    return ConversationHandler.END


async def main(event, context):
    event_body = event.get("body")
    if not event_body:
        return {
            'statusCode': 500,
            'body': 'event body not available'
        }

    application = (
        Application.builder().token(os.environ["MAT_GPT_TOKEN"]).build()
    )

    application.add_handler(CommandHandler("start", start))

    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("news", news)],
            states={
                CHOOSE_NEWS: [
                    MessageHandler(
                        filters.Regex(f'^({"|".join(reply_keyboard[0])})$'),
                        handle_news_text,
                    )
                ]
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
    )

    try:
        await application.initialize()
        await application.process_update(Update.de_json(json.loads(event["body"]), application.bot))
        return {
            'statusCode': 200,
            'body': 'Success'
        }
    except Exception as ex:
        logger.error("An error occurred: %s", str(ex))
        return {
            'statusCode': 500,
            'body': f'Failure: {str(ex)}'
        }


def lambda_handler(event, context):
    return asyncio.get_event_loop().run_until_complete(main(event, context))
