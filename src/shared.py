import enum
import uuid
from argparse import Namespace
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from telegram.ext import Application


class VoteType(enum.StrEnum):
    """
    Enum for the different types of votes.
    """

    yes = "yes"
    no = "no"
    maybe = "maybe"


@dataclass
class SharedContext:
    """
    Contains data shared across both the Telegram bot and the web server.

    Attributes:
        telegram_app: The Telegram bot's Application object.
        args: The command line arguments.
    """

    telegram_app: Application = None
    args: Optional[Namespace] = None


@dataclass
class Event:
    """
    Represents an event that users can vote on.

    Attributes:
        title: The title of the event.
        owner_id: The Telegram ID of the user who created the event.
        days: A list of the days on which the event can be held.
        notify: Whether to notify users when the event is created.
        anonymous: Whether to hide the names of users who voted.
        votes: A list of the votes cast on the event.
        description: A description of the event.
        id: The UUID of the event.
        time_created: The time at which the event was created.
    """

    title: str
    owner_id: int
    days: list[str]
    notify: bool
    anonymous: bool
    votes: list["EventVote"] = field(default_factory=list)
    description: str = ""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    time_created: datetime = field(default_factory=datetime.now)

    def num_votes(self, day: str, *vote_types: VoteType | str) -> int:
        """
        Returns the number of votes of the given types on the given day.
        :param day: The day whose votes to count.
        :param vote_types: The types of votes to count. If none are given, all votes are counted.
        :return: The number of votes of the given types on the given day.
        """
        return len(self.day_votes(day, *vote_types))

    def day_votes(self, day: str, *vote_types: VoteType | str) -> list["EventVote"]:
        """
        Returns the votes of the given types on the given day.
        :param day: The day whose votes to return.
        :param vote_types: The types of votes to return. If none are given, all votes are returned.
        :return: The votes of the given types on the given day.
        """
        # We do this so that we can pass in strings as well as VoteType enums.
        if len(vote_types) == 0:
            typeset = set(map(str, VoteType))
        else:
            typeset = set(map(str, vote_types))
        return [v for v in self.votes if str(v.vote[day]) in typeset]

    def max_votes(self, *vote_types: VoteType | str) -> int:
        """
        Returns the maximum number of votes of the given types over all days.
        :param vote_types: The types of votes to count. If none are given, all votes are counted.
        :return: The maximum number of votes of the given types on any day.
        """
        return max(self.num_votes(day, *vote_types) for day in self.days)

    def best_days(self) -> set[str]:
        """
        Determines the most suitable days for the event.
        Most suitable, in this case, means the days with the largest number of yes votes.
        If there are multiple such days, we choose from these the ones with the largest number of maybe votes.
        If there are no days with at least one yes vote, we return an empty list.
        :return: A list of the most suitable days for the event.
        """
        max_yes = self.max_votes(VoteType.yes)
        if max_yes == 0:
            return set()

        best_days = set(
            day for day in self.days if self.num_votes(day, VoteType.yes) == max_yes
        )
        if len(best_days) == 1:
            # Just one best day, so we return immediately.
            return best_days

        # We need to get max_maybe from best_days, so we can't just use self.max_votes.
        max_maybe = max(self.num_votes(day, VoteType.maybe) for day in best_days)
        best_days = set(
            day for day in best_days if self.num_votes(day, VoteType.maybe) == max_maybe
        )
        return best_days


@dataclass
class EventVote:
    """
    Represents a vote on an event.

    Attributes:
        user_id: The Telegram ID of the user who cast the vote.
                 Will be saved even if this is an anonymous vote, so that we can still count the votes.
        user_name: The name (first name and last name, space-separated) of the user who cast the vote.
                   Can be empty if this is an anonymous vote.
        vote: A dictionary mapping days to the type of vote cast on that day.
        time_created: The time at which the vote was cast.
    """

    user_id: int
    user_name: str
    vote: dict[str, VoteType] = field(default_factory=dict)
    time_created: datetime = field(default_factory=datetime.now)


shared_context: SharedContext = SharedContext()
