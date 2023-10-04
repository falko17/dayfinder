import argparse


def parse_arguments() -> argparse.Namespace:
    """
    Parses the command line arguments and returns them as a Namespace object.
    :return: The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="A Telegram bot aimed at finding days on which everyone is available. "
        "Apart from the bot itself, running this script will also start a web server "
        'which hosts the web app (or "Mini-App") for the bot.'
    )

    parser.add_argument(
        "--token",
        type=str,
        required=True,
        help="The Telegram bot token. You can get this from @BotFather.",
    )
    parser.add_argument(
        "--web-url",
        type=str,
        required=True,
        help="The URL at which the web server will be accessible. "
        "This is used to generate links to the web app. "
        "It should be a URL that is accessible from the internet, pointing to the web server.",
    )
    parser.add_argument(
        "--web-host",
        type=str,
        default="0.0.0.0",
        help="The host on which to run the web server. By default, this is set to 0.0.0.0.",
    )
    parser.add_argument(
        "--web-port",
        type=int,
        default=8080,
        help="The port on which to run the web server. The default is 8080, so that no root privileges are required.",
    )
    parser.add_argument(
        "--web-certfile",
        type=str,
        required=False,
        help="The path to the SSL certificate file to use for HTTPS. "
        "If this is not specified, the web server will use HTTP.",
    )
    parser.add_argument(
        "--web-keyfile",
        type=str,
        required=False,
        help="The path to the SSL key file to use for HTTPS. "
        "If this is not specified, the web server will use HTTP.",
    )
    parser.add_argument(
        "--admin-ids",
        metavar="ID",
        type=int,
        nargs="+",
        required=False,
        help="The Telegram IDs of the users who should be able to use admin commands. ",
    )
    parser.add_argument(
        "--persistence-file",
        type=str,
        default="persistence.pickle",
        help="The path to the file in which to store the bot's persistence data. "
        "This file will be created if it does not exist.",
    )
    parser.add_argument(
        "--enable-httpx-logging",
        action="store_true",
        help="This will enable logging of all httpx requests, i.e., requests made by python-telegram-bot. "
        "Due to the polling method of retrieving updates, this will result in a lot of logging output, "
        "and thus is disabled by default.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="This will enable the debug mode for asyncio and for hypercorn.",
    )

    args = parser.parse_args()
    if (
        args.web_certfile
        and not args.web_keyfile
        or args.web_keyfile
        and not args.web_certfile
    ):
        parser.error(
            "Both --web-certfile and --web-keyfile must be specified if either is specified."
        )

    return args
