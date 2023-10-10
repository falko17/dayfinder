# Dayfinder Telegram bot

This is a Telegram bot that allows users to create polls to find a date everyone is available.

![image](https://github.com/falko17/dayfinder/assets/10247603/7beec8b3-f253-47eb-9bce-7d092062b4de)

## Table of contents
- [**Usage**](#usage): Describes how to use the bot to create and share polls.
- [**Setup**](#setup): Instructs how to set up and run your own instance of the bot on a server.
- [**Developer information**](#developer-information): Contains information about the development (e.g., source code structure) of the bot.

## Usage
The bot is available on Telegram as [@dayfinderbot](https://t.me/dayfinderbot).
Alternatively, you can [host your own instance of the bot](#setup).

### Creating a poll
To create a poll:
1. Send the bot the `/start` command.
    - Alternatively, you can also tap on "Create new poll" in [inline mode](#inline-mode).
2. In the message that appears, click on the attached "Create new poll" button to open the Mini App.
3. In the form that appears, enter a title, an optional description, and the possible dates. If you choose to make the poll anonymous, note that you won't be able to see who voted for which dates. Additionally, you can choose to receive a notification whenever someone votes in your poll.
4. Click on "Create poll" to create the poll.
5. The bot will send you a message with the voting link. You can share this link with others to let them vote in your poll. You can also use [inline mode](#inline-mode) to share the poll.

### Voting in a poll
To vote in a poll, simply click on the voting link you received from the poll creator. 
In the Mini App that opens, you can select "Yes/No/Maybe" for each available date.
When you are done, click on "Confirm vote" to submit your vote.
After you have voted, you can [view the results](#viewing-results) of the poll.

> [!note]
> To edit your vote, click on the voting link again and change your vote. Your previous vote will be overwritten.

### Viewing results
To get a link to the results of a poll, you have the following options:
- Click on the voting link you received from the poll creator, and select "View results" in the Mini App.
- If you are on the results page already, click on "Share with chat" to share the results with another Telegram chat.
- If you are the creator of the poll:
    - [List your polls](#listing-your-polls), and click on the poll you want to view the results of.
    - Use [inline mode](#inline-mode) to search for the poll and select "View results".

On the results page, you can see the number of yes/no/maybe votes for each date.
If the poll is not anonymous, you can also click on these numbers to see who voted for which dates.
By clicking on "Expand all," you can see the names of all voters at once.
Clicking on a voter's name also reveals the date and time at which they voted.

### Deleting a poll
To delete a poll, open the [results page](#viewing-results) of the poll and click on "Delete poll."

### Listing your polls
To list your polls, you can either send the bot the `/polls` command, or use [inline mode](#inline-mode).
Clicking on one of your polls after having sent the `/polls` command will open the [results page](#viewing-results) of the poll.

### Inline Mode
To use the bot in inline mode, simply type `@dayfinderbot` in any chat.
You can optionally enter the name of a poll after it (e.g., `@dayfinderbot my poll`) to search for a specific poll, otherwise all of your polls will be listed.

For each poll of yours, you will get the option to send the voting link or the results to the current chat – just click on the corresponding button in the list that pops open.
Alternatively, you can click on the small icon to the left of the option to open the page yourself without sending it.

## Setup
> [!note]
> You only need to consult this section if you want to host your own instance of the bot.
> If you just want to use the bot, you can use `@dayfinderbot` on Telegram.

### Prerequisites
- [Python 3.11+](https://www.python.org/downloads/)
  - Verify your installation by running `python3 --version`.
- All dependencies listed in [`requirements.txt`](requirements.txt) (can be installed with `pip install -r requirements.txt`):
    - [python-telegram-bot](https://python-telegram-bot.org/), which is used to interact with the Telegram Bot API
    - [Quart](https://palletsprojects.com/p/quart/), which is used to run the web server hosting the Mini App
- A [Telegram bot](#creating-a-telegram-bot) token
    - Can be obtained by talking to [@BotFather](https://t.me/BotFather) on Telegram. You can use the `/newbot` command to create a new bot.
    - You will receive a token for your bot. Keep this token secret, as it allows anyone to control your bot.
- A domain name and an SSL certificate for your domain
    - The domain name is used to host the Mini App.
    - The SSL certificate is required to use the Mini App in Telegram, since only HTTPS links are supported.
    - You can obtain a free SSL certificate from [Let's Encrypt](https://letsencrypt.org/getting-started).

### Preparing the web server
Before you start, you need to think about how you want to host the web app,
since it needs to be accessible from the outside.
The recommended way is to use a reverse proxy, such as [nginx](https://www.nginx.com/),
to forward requests to the web app.
This way, you can host the web app on a local port and let the reverse proxy handle the HTTPS encryption.
Going into detail on how to set up a reverse proxy is beyond the scope of this guide, but there are plenty of good resources available online (for example, you can take a look at [the nginx documentation](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/).

Alternatively, you can pass the SSL certificate and keyfile to the web app directly and let it handle the HTTPS encryption.
Note that if you do this and use a port other than 443, you will have to specify the port in the Mini App URL (e.g., `https://example.com:8080`).

### Preparing the Telegram bot
This assumes you have a bot already (see [Prerequisites](#prerequisites)).
All these steps can be done by talking to [@BotFather](https://t.me/BotFather) on Telegram.

1. Use `/newapp` to setup the `vote` webapp. 
    - When asked for the web app URL, enter the URL where the web app will be hosted with the path `/vote` appended (e.g., `https://dayfinder.example.com/vote`). 
    - When asked for the short name for the web app, enter `vote`.
2. Repeat the above step for the `results` webapp, i.e., substitute `/vote` with `/results` and `vote` with `results`.
3. Enable inline mode for your bot by using the `/setinline` command.
4. Set the menu button to open the create page by using the `/setmenubutton` command and submitting the URL of the webapp with the path `/create` appended (e.g., `https://dayfinder.example.com/create`).
5. (Optional) Talk to [@BotFather](https://t.me/BotFather) on Telegram and use the `/setcommands` command to set the bot's commands to the following: 
```
start - Create a new poll
polls - View your polls
help - Get help for this bot
```

### Running Dayfinder
> [!important]
> These steps assume you are using a Linux server.
> If you are using a different operating system, you will have to adapt the commands accordingly.

1. Clone this repository (`git clone https://github.com/falko17/dayfinder`) and change into the cloned directory (`cd dayfinder`).
2. Create a virtual environment for the bot (`python3 -m venv venv`) and activate it (`source venv/bin/activate`).
    - Whenever you reopen your terminal, you will have to activate the virtual environment again.
3. Install the dependencies listed in [`requirements.txt`](requirements.txt) (`pip install -r requirements.txt`).
4. The web app and the Telegram bot run in parallel, so you only need to execute one command to run both: `python3 bot.py --token TOKEN --web-url URL`, where `TOKEN` is the token of your Telegram bot and `URL` is the URL where the web app (e.g., `https://dayfinder.example.com`) will be hosted.
    - By default, the web app will listen on port 8080 and host 0.0.0.0. You can change these settings with the `--web-port` and `--web-host` options.
    - If you are *not* using a reverse proxy, you will have to pass the SSL certificate and keyfile to the web app with the `--web-certfile` and `--web-keyfile` options. If these options are not passed, the web app will use HTTP.
    - Review all available options with `python3 bot.py --help`.
5. Start testing the bot by sending it the `/start` command on Telegram.
6. To stop the program, press Ctrl+C. Note that it may take a few seconds for the program to shut down properly.

## Developer information
See [`DEVELOPMENT.md`](DEVELOPMENT.md) for developer information.

## License
This project is licensed under the terms of the [MIT license](LICENSE).