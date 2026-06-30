from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto

LEFT_BOWER_RANK = 15
RIGHT_BOWER_RANK = 16


class Suit(Enum):
    CLUBS = 1
    DIAMONDS = 2
    HEARTS = 3
    SPADES = 4

    def bower_partner(self) -> Suit:
        same_color = (
            {Suit.CLUBS, Suit.SPADES}
            if self in (Suit.CLUBS, Suit.SPADES)
            else {Suit.DIAMONDS, Suit.HEARTS}
        )
        return next(s for s in same_color if s != self)


class Rank(Enum):
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


PLAYING_RANKS = (
    Rank.NINE,
    Rank.TEN,
    Rank.JACK,
    Rank.QUEEN,
    Rank.KING,
    Rank.ACE,
)

SUIT_SYMBOL = {
    Suit.CLUBS: "♣",
    Suit.DIAMONDS: "♦",
    Suit.HEARTS: "♥",
    Suit.SPADES: "♠",
}

RANK_LABEL = {
    Rank.NINE: "9",
    Rank.TEN: "10",
    Rank.JACK: "J",
    Rank.QUEEN: "Q",
    Rank.KING: "K",
    Rank.ACE: "A",
}


def suit_symbol(suit: Suit) -> str:
    return SUIT_SYMBOL[suit]


def card_label(card: Card) -> str:
    return f"{RANK_LABEL[card.rank]}{SUIT_SYMBOL[card.suit]}"


@dataclass
class Card:
    suit: Suit
    rank: Rank

    def __str__(self) -> str:
        name = self.rank.name[0] if self.rank != Rank.TEN else "10"
        return f"{name}{self.suit.name[0]}"

    def effective_suit(self, trump: Suit) -> Suit:
        if self.rank == Rank.JACK and self.suit == trump.bower_partner():
            return trump
        return self.suit

    def effective_rank(self, trump: Suit) -> int:
        if self.rank == Rank.JACK:
            if self.suit == trump.bower_partner():
                return LEFT_BOWER_RANK
            if self.suit == trump:
                return RIGHT_BOWER_RANK
        return self.rank.value


def standard_deck() -> list[Card]:
    cards = [Card(suit, rank) for suit in Suit for rank in PLAYING_RANKS]
    random.shuffle(cards)
    return cards


class Seat(Enum):
    NORTH = auto()
    EAST = auto()
    SOUTH = auto()
    WEST = auto()


class Team(Enum):
    TEAM_ONE = 0
    TEAM_TWO = 1

    def opponent(self) -> Team:
        return Team.TEAM_TWO if self == Team.TEAM_ONE else Team.TEAM_ONE


def team_label(team: Team) -> str:
    return "Team 1" if team == Team.TEAM_ONE else "Team 2"


def team_color(team: Team) -> tuple[int, int, int]:
    if team == Team.TEAM_ONE:
        return (70, 140, 230)
    return (230, 130, 50)


@dataclass
class Player:
    name: str
    seat: Seat
    cards: list[Card]
    is_human: bool
    team: Team
    tricks_taken: list[Card] = field(default_factory=list)


@dataclass
class Play:
    player: Player
    card: Card


@dataclass
class Trick:
    plays: list[Play]
    led_suit: Suit | None
    trump: Suit

    def winner(self) -> Player:
        trump_plays = [
            play
            for play in self.plays
            if play.card.effective_suit(self.trump) == self.trump
        ]
        if trump_plays:
            return max(
                trump_plays,
                key=lambda play: play.card.effective_rank(self.trump),
            ).player
        led_plays = [
            play
            for play in self.plays
            if play.card.effective_suit(self.trump) == self.led_suit
        ]
        return max(
            led_plays,
            key=lambda play: play.card.effective_rank(self.trump),
        ).player
