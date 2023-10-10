#!/usr/bin/env python
import asyncio
import html
import itertools
import logging
import pprint
from asyncio import AbstractEventLoop
from datetime import datetime
from ssl import SSLError
from typing import Any

from telegram import (
    Update,
    WebAppInfo,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineQueryResultsButton,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.constants import ParseMode
from telegram.error import TimedOut, TelegramError
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    PicklePersistence,
    InlineQueryHandler,
    Application,
    filters,
    CallbackQueryHandler,
)

from src.arguments import parse_arguments
from src.shared import shared_context, Event, VoteType
from src.webapp_server import run_webapp_server, webapp


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Called when the user starts the bot.
    """
    if "events" not in context.bot_data:
        context.bot_data["events"] = {}
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hi there! Use me to find a date everyone is available. You can use /help to get a list of commands.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Create new poll",
                        web_app=WebAppInfo(url=f"{shared_context.args.web_url}/create"),
                    )
                ]
            ]
        ),
    )


async def results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Called when the user sends the /results command.
    This command is mainly intended for debugging,
    as users would normally use the inline query, or a link, to view results.
    """
    if not context.args or len(context.args) != 1:
        await update.effective_message.reply_text(
            "Please specify the poll ID, i.e., do <code>/results ID-HERE</code>.",
            parse_mode=ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await update.effective_message.reply_text(
        get_result_text(context.args[0]),
        parse_mode=ParseMode.HTML,
    )


async def polls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Called when the user sends the /polls command.
    Displays a list of all polls the user has created.
    """
    events = context.bot_data["events"]
    relevant = sorted(
        filter(lambda poll: poll.owner_id == update.effective_user.id, events.values()),
        key=lambda poll: poll.time_created,
        reverse=True,
    )
    if not relevant:
        await update.effective_message.reply_text("You have no polls yet.")
        return

    text = "Choose a poll whose results you want to see."
    if len(relevant) > 20:
        text += "\n\n<i>Only the 20 most recent polls are shown.</i>"
        relevant = relevant[:20]

    await update.effective_message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(poll.title, callback_data=str(poll.id))]
                for poll in relevant
            ]
        ),
    )


async def generate_poll_buttons(
    relevant_polls: list[Event],
) -> list[list[InlineKeyboardButton]]:
    """
    Generates a list of a list of buttons for the given polls,
    intended to be used in an InlineKeyboardMarkup.
    :param relevant_polls: The polls to generate buttons for.
    :return: A list of lists of buttons.
    """
    return [
        [
            InlineKeyboardButton(
                poll.title,
                web_app=WebAppInfo(
                    url=f"{shared_context.args.web_url}/results?poll_id={poll.id}"
                ),
            )
        ]
        for poll in relevant_polls
    ]


async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Called when the user clicks a button in a /polls message.
    Displays the results for the clicked poll.
    """
    query = update.callback_query
    if query.data not in context.bot_data["events"]:
        await query.answer("This poll no longer exists.")
        await query.message.delete()
        return

    poll = context.bot_data["events"][query.data]
    if poll.owner_id != query.from_user.id:
        await query.answer("You are not the owner of this poll.")
        await query.message.delete()
        return

    await query.answer()
    await query.message.edit_text(
        text=get_result_text(query.data), parse_mode=ParseMode.HTML
    )


def get_result_text(poll_id: str) -> str:
    """
    Generates the text for the results of the given poll.
    :param poll_id: The ID of the poll for which results shall be generated.
    :return: The text for the results of the given poll.
    """
    poll: Event = shared_context.telegram_app.bot_data["events"][poll_id]
    best_days = poll.best_days()
    result_text = f"Results for <i>{html.escape(poll.title)}</i>\n\n"
    for day in poll.days:
        yes_votes = poll.num_votes(day, VoteType.yes)
        maybe_votes = poll.num_votes(day, VoteType.maybe)
        no_votes = poll.num_votes(day, VoteType.no)
        # We want to make the top options bold
        if day in best_days:
            result_text += "<b>"
        parsed_day = datetime.strptime(day, "%Y-%m-%d")
        result_text += f"{parsed_day.strftime('%d %b %Y')}: {yes_votes} yes, {maybe_votes} maybe, {no_votes} no"
        if day in best_days:
            result_text += "</b>"
        result_text += "\n"

    result_text += (
        f"\n\n<a href='https://t.me/{shared_context.telegram_app.bot.username}"
        f"/results?startapp={str(poll.id)}'>Click for details</a>"
    )
    return result_text


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Called when the user sends an inline query.
    """
    query = update.inline_query.query

    inline_results = []
    events = context.bot_data["events"]
    if not query:
        relevant = filter(
            lambda poll: poll.owner_id == update.effective_user.id, events.values()
        )
    elif query in events:
        relevant = [events[query]]
    else:
        relevant = filter(
            lambda poll: query.lower() in poll.title.lower()
            and poll.owner_id == update.effective_user.id,
            events.values(),
        )
    inline_results += itertools.chain.from_iterable(
        get_inline_query_results(poll, context.bot.username, update.effective_user.id)
        for poll in relevant
    )

    await update.inline_query.answer(
        inline_results,
        button=InlineQueryResultsButton("Create new poll", start_parameter="new"),
    )


def get_inline_query_results(
    poll: Event, bot_name: str, user_id: int
) -> list[InlineQueryResultArticle]:
    """
    Generates the inline query results for the given poll.
    :param poll: The poll to generate results for.
    :param bot_name: The bot's username.
    :param user_id: The ID of the user who sent the inline query.
    :return: The inline query results for the given poll.
    """
    result_articles = [
        InlineQueryResultArticle(
            id=str(poll.id) + "-results",
            title=f'Results for "{poll.title}"'[:70],
            description="Click to send the results page for this poll.",
            url=f"https://t.me/{bot_name}/results?startapp={str(poll.id)}",
            hide_url=True,
            input_message_content=InputTextMessageContent(
                message_text=get_result_text(str(poll.id)),
                parse_mode=ParseMode.HTML,
            ),
        ),
    ]
    if poll.owner_id == user_id:
        result_articles.append(
            InlineQueryResultArticle(
                id=str(poll.id) + "-vote",
                title=f'Voting page for "{poll.title}"'[:70],
                description="Click to send the voting page for this poll.",
                url=f"https://t.me/{bot_name}/vote?startapp={str(poll.id)}",
                hide_url=True,
                input_message_content=InputTextMessageContent(
                    message_text=f"<a href='https://t.me/{bot_name}/vote?startapp={str(poll.id)}'>"
                    f'Click here to vote on "{poll.title}"</a>',
                    parse_mode=ParseMode.HTML,
                ),
            ),
        )

    return result_articles


async def dump(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Called when the user sends the /dump command.
    Sends a dump of the bot's data to the user.
    This should only be callable by admins.
    """
    pprint.pprint(context.bot_data["events"])
    try:
        await update.effective_message.reply_text(str(context.bot_data["events"]))
    except TelegramError as e:
        # Message is probably too long.
        logging.warning(
            f"Could not send dump to user {update.effective_user.id}: {e.message}"
        )


@webapp.before_serving
async def startup():
    """
    Sets up the Telegram bot.
    """
    await shared_context.telegram_app.initialize()
    await shared_context.telegram_app.start()
    await shared_context.telegram_app.updater.start_polling()


@webapp.after_serving
async def shutdown():
    """
    Shuts down the Telegram bot.
    """
    try:
        await shared_context.telegram_app.updater.stop()
    except TimedOut:
        # This can be safely ignored. It just means we had to cancel an ongoing request.
        pass
    await shared_context.telegram_app.stop()


async def post_init(app: Application):
    """
    Called after the app has been initialized.
    Sets up the bot data.
    :param app: The app that has been initialized.
    """
    if "events" not in app.bot_data:
        app.bot_data["events"] = {}
    await app.update_persistence()


def exception_handler(loop: AbstractEventLoop, context: dict[str, Any]):
    """
    Called when an exception in the event loop occurs.
    :param loop: The event loop in which the exception occurred.
    :param context: Context information about the exception.
    """
    ignored_ssl_errors = (
        # See hypercorn issue: https://github.com/pgjones/hypercorn/issues/67
        "APPLICATION_DATA_AFTER_CLOSE_NOTIFY",
    )
    if (
        isinstance(context["exception"], SSLError)
        and context["exception"].reason in ignored_ssl_errors
    ):
        return

    logging.error(context["exception"])


async def help_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Called when the user sends the /help command.
    """
    await update.effective_message.reply_text(
        "This bot allows you to create polls to find a date everyone is available.\n\n"
        "To create a new poll, click the button below or send /start.\n"
        "To view a list of all your polls (and see results), send /polls.\n\n"
        "You can also use this bot in inline mode: "
        f"Just type <code>@{context.bot.username}</code> in any chat, then type the name of the poll you want to find. "
        "This way, you can send the results page or the voting page to the current chat.",
        parse_mode=ParseMode.HTML,
    )


async def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO if not shared_context.args.debug else logging.DEBUG,
    )

    if not shared_context.args.enable_httpx_logging:
        # httpx is python-telegram-bot's HTTP client library.
        logging.getLogger("httpx").setLevel(logging.WARNING)

    persistence = PicklePersistence(shared_context.args.persistence_file)
    shared_context.telegram_app = (
        ApplicationBuilder()
        .token(shared_context.args.token)
        .persistence(persistence)
        .post_init(post_init)
        .build()
    )

    # Register handlers
    handlers = [
        CommandHandler("start", start, filters=filters.ChatType.PRIVATE),
        CommandHandler("results", results),
        CommandHandler("polls", polls),
        CommandHandler("help", help_text),
        CallbackQueryHandler(callback_query),
        InlineQueryHandler(inline_query),
    ]
    if shared_context.args.admin_ids is None:
        logging.warning("No admin IDs specified. Admin commands will not be available.")
    else:
        handlers.append(
            CommandHandler(
                "dump",
                dump,
                filters=filters.User(user_id=shared_context.args.admin_ids),
            )
        )

    for handler in handlers:
        shared_context.telegram_app.add_handler(handler)

    asyncio.get_event_loop().set_exception_handler(exception_handler)
    # This next command will run until the server stops.
    # Afterward, our after_serving hook will stop the bot as well.
    await run_webapp_server()


if __name__ == "__main__":
    shared_context.args = parse_arguments()
    asyncio.run(main(), debug=shared_context.args.debug)
