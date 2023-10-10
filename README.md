# Dayfinder Telegram bot

This is a Telegram bot that allows users to create polls to find a date everyone is available.

TODO: Image here

## Table of contents
- [**Usage**](#usage): Describes how to use the bot to create and share polls.
- [**Setup**](#setup): Instructs how to set up and run your own instance of the bot on a server.
- [**Development**](#development): Contains information about the development (e.g., source code structure) of the bot.

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

![image](https://github.com/falko17/dayfinder/assets/10247603/cd159add-a233-4ca4-958b-6b1f278aacc6)

### Voting in a poll
To vote in a poll, simply click on the voting link you received from the poll creator. 
In the Mini App that opens, you can select "Yes/No/Maybe" for each available date.
When you are done, click on "Confirm vote" to submit your vote.
After you have voted, you can [view the results](#viewing-results) of the poll.

![image](https://github.com/falko17/dayfinder/assets/10247603/7beec8b3-f253-47eb-9bce-7d092062b4de)


> [!note]
> To edit your vote, click on the voting link again and change your vote. Your previous vote will be overwritten.

### Viewing results
To get a link to the results of a poll, you have the following options:
- Click on the voting link you received from the poll creator, and select "View results" in the Mini App.
- If you are on the results page already, click on "Share with chat" to share the results with another Telegram chat.
- If you are the creator of the poll:
    - [List your polls](#listing-your-polls), and click on the poll you want to view the results of.
    - Use [inline mode](#inline-mode) to search for the poll and select "View results".

![image](https://github.com/falko17/dayfinder/assets/10247603/bd3471bd-36c4-4918-be94-5998946adc2a)


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
TODO

## Development
TODO

## Troubleshooting
TODO
