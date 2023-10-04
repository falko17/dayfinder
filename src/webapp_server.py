import datetime
import hmac
import json
import logging
import os
from typing import Optional
from urllib.parse import parse_qs

from quart import Quart, request, render_template
from telegram.error import TelegramError

from src.shared import shared_context, Event, EventVote, VoteType

webapp = Quart(__name__, root_path=os.getcwd())


@webapp.route("/poll", methods=["POST"])
async def create_poll():
    """
    Creates a new poll based on the data sent by the user.
    Intended to be called by the Telegram webapp's JavaScript code.
    """
    data = await request.json
    init_data = parse_qs(data["initData"])
    if (error := await check_validation(init_data)) is not None:
        return error

    user_info = json.loads(init_data["user"][0])
    # We convert the days to a dict (ordered on Python 3.7+) and back to a list to remove duplicates.
    event = Event(
        title=data["title"],
        days=list(dict.fromkeys(data["days"])),
        description=data["description"],
        notify=data["notification"],
        owner_id=user_info["id"],
    )
    if "events" not in shared_context.telegram_app.bot_data:
        shared_context.telegram_app.bot_data["events"] = {}
    shared_context.telegram_app.bot_data["events"][str(event.id)] = event
    await shared_context.telegram_app.update_persistence()
    url = f"https://t.me/{shared_context.telegram_app.bot.username}/vote?startapp={str(event.id)}"
    await shared_context.telegram_app.bot.send_message(
        chat_id=user_info["id"],
        text=f'Created new poll "{data["title"]}"!\n\n'
        f"You can share the link to the poll with your friends:\n"
        f"{url}\n\n"
        f"Use /polls to view the results of your polls "
        f"at any time.",
    )
    return "OK"


@webapp.route("/poll", methods=["PATCH"])
async def vote_poll():
    """
    Casts a vote on a poll based on the data sent by the user.
    If the user has already voted, the vote is edited.
    Intended to be called by the Telegram webapp's JavaScript code.
    """
    data = await request.json
    init_data = parse_qs(data["initData"])
    if (error := await check_validation(init_data)) is not None:
        return error

    user_info = json.loads(init_data["user"][0])
    if (
        init_data["start_param"][0]
        not in shared_context.telegram_app.bot_data["events"]
    ):
        # Most likely scenario: user voted on a poll that was deleted by the owner.
        return "This poll does not exist (anymore).", 404
    event = shared_context.telegram_app.bot_data["events"][init_data["start_param"][0]]
    # Verify that the days match
    if event.days != list(data["days"].keys()):
        return "Days do not match with days of the event.", 400

    vote_days = {k: VoteType[v] for k, v in data["days"].items()}
    old_vote = None
    if (
        event_vote := next(
            filter(lambda x: x.user_id == int(user_info["id"]), event.votes), None
        )
    ) is not None:
        # User already voted, edit vote accordingly
        old_vote = event_vote.vote
        event_vote.vote = vote_days
        exists = True
    else:
        user_name = user_info["first_name"]
        if "last_name" in user_info and user_info["last_name"] != "":
            user_name += f' {user_info["last_name"]}'
        event_vote = EventVote(
            user_id=user_info["id"], user_name=user_name, vote=vote_days
        )
        event.votes.append(event_vote)
        exists = False
    await shared_context.telegram_app.update_persistence()

    # Only notify if the user has enabled notifications and if the vote has changed.
    if event.notify and old_vote != vote_days:
        try:
            await shared_context.telegram_app.bot.send_message(
                chat_id=event.owner_id,
                text=f'{"Edited" if exists else "New"} vote on your poll'
                f' "{event.title}" by {event_vote.user_name}!\n\n'
                "You can view the results of your polls at any time"
                f" using /polls.",
            )
        except TelegramError:
            # User probably blocked bot, this is fine. We should create a warning, though.
            logging.warning(
                f"User {event.owner_id} blocked bot, could not send notification."
            )

    return "OK"


@webapp.route("/poll", methods=["GET"])
async def vote_results() -> dict[str, str | dict[str, VoteType]] | tuple[str, int]:
    """
    Returns JSON-encoded existing vote for user, along with the results link,
    based on init_data sent by Telegram webapp.
    Intended to be called by the Telegram webapp's JavaScript code.

    The returned JSON object has the following structure::

        {
            "results": "https://t.me/.../results?startapp=...",
            "votes": {
                "day1": "yes",
                "day2": "no",
                "day3": "maybe"
            }
        }

    Note that if an error occurs, this will instead return a tuple of the error message and the HTTP status code.

    :return: The JSON-encoded existing vote and results link, or an error message and HTTP status code.
    """
    init_data = request.args.to_dict(flat=False)
    if (error := await check_validation(init_data)) is not None:
        return error

    user_info = json.loads(init_data["user"][0])
    poll_id = init_data["start_param"][0]
    if poll_id not in shared_context.telegram_app.bot_data["events"]:
        return "This poll does not exist (anymore).", 404
    poll = shared_context.telegram_app.bot_data["events"][poll_id]
    event_vote = next(
        filter(lambda x: x.user_id == int(user_info["id"]), poll.votes), None
    )
    url = f"https://t.me/{shared_context.telegram_app.bot.username}/results?startapp={str(poll.id)}"
    if event_vote is None:
        return {"results": url, "votes": {}}
    else:
        return {"results": url, "votes": event_vote.vote}


@webapp.route("/poll", methods=["DELETE"])
async def delete_poll():
    """
    Deletes a poll, identified by the poll ID sent by the user.
    Intended to be called by the Telegram webapp's JavaScript code.
    """
    data = await request.json
    init_data = parse_qs(data["initData"])
    if (error := await check_validation(init_data)) is not None:
        return error

    user_info = json.loads(init_data["user"][0])
    poll_id = data["pollId"]
    if poll_id not in shared_context.telegram_app.bot_data["events"]:
        return "This poll does not exist (anymore).", 404
    poll = shared_context.telegram_app.bot_data["events"][poll_id]
    if poll.owner_id != user_info["id"]:
        return "You are not the owner of this poll.", 403
    del shared_context.telegram_app.bot_data["events"][poll_id]
    await shared_context.telegram_app.update_persistence()

    try:
        await shared_context.telegram_app.bot.send_message(
            chat_id=user_info["id"], text=f'Deleted poll "{poll.title}".'
        )
    except TelegramError:
        # User probably blocked bot, this is fine. We should create a warning, though.
        logging.warning(
            f'User {user_info["id"]} blocked bot, could not send notification.'
        )
    return "OK"


async def check_validation(
    init_data: dict[str, list[str]]
) -> Optional[tuple[str, int]]:
    """
    Checks whether the data received by the Telegram webapp is valid.
    If yes, returns None. If no, returns a tuple of the error message and the HTTP status code.

    :param init_data: The data received by the Telegram webapp.
    :return: None if the data is valid, otherwise a tuple of the error message and the HTTP status code.
    """
    timestamp = datetime.datetime.fromtimestamp(int(init_data["auth_date"][0]))
    if not validate(init_data):
        return "Invalid data was sent.", 400
    elif (datetime.datetime.now() - timestamp) > datetime.timedelta(minutes=60):
        return "Sent data is too old (more than 60 minutes old).", 400

    return None


def validate(init_data: dict[str, list[str]]) -> bool:
    """
    Cryptographically validates the data received by the Telegram webapp.
    :param init_data: The data received by the Telegram webapp.
    :return: Whether the data is valid.
    """
    # See https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    secret_key = hmac.digest(
        b"WebAppData", shared_context.args.token.encode(), "sha256"
    )
    data_check_string = "\n".join(
        list(
            map(
                lambda x: f"{x}={init_data[x][0]}",
                filter(lambda x: x != "hash", sorted(key for key in init_data.keys())),
            )
        )
    )
    return hmac.digest(
        secret_key, data_check_string.encode(), "sha256"
    ) == bytes.fromhex(init_data["hash"][0])


@webapp.route("/create")
async def create():
    """
    Renders the create page.
    """
    # TODO: anonymous poll
    return await render_template("create.html")


@webapp.route("/vote")
async def vote():
    """
    Renders the vote page.
    """
    poll_id = request.args.get("tgWebAppStartParam")
    if poll_id is None:
        return await render_template("error.html", error="No poll ID supplied."), 400
    elif poll_id not in shared_context.telegram_app.bot_data["events"]:
        return (
            await render_template("error.html", error="Poll does not exist (anymore)."),
            404,
        )
    poll = shared_context.telegram_app.bot_data["events"][poll_id]
    return await render_template("vote.html", poll=poll)


@webapp.route("/results")
async def results():
    """
    Renders the results page.
    """
    poll_id = request.args.get("poll_id")
    if poll_id is None:
        poll_id = request.args.get("tgWebAppStartParam")

    if poll_id is None:
        return await render_template("error.html", error="No poll ID supplied."), 400
    elif poll_id not in shared_context.telegram_app.bot_data["events"]:
        return (
            await render_template("error.html", error="Poll does not exist (anymore)."),
            404,
        )
    poll = shared_context.telegram_app.bot_data["events"][poll_id]
    # TODO: Expand days if more than N / list voting date on click?
    return await render_template("results.html", poll=poll, best_days=poll.best_days())


@webapp.route("/")
async def index():
    """
    'Renders' the index page.
    It's really just a string of text, so there's not a lot to render.
    """
    return "The DayFinder WebApp is hosted here. There's nothing on this page, though."


async def run_webapp_server():
    await webapp.run_task(
        host=shared_context.args.web_host,
        port=shared_context.args.web_port,
        debug=shared_context.args.debug,
        certfile=shared_context.args.web_certfile,
        keyfile=shared_context.args.web_keyfile,
    )
