from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum

LEFT_BOWER_RANK = 15
RIGHT_BOWER_RANK = 16


class Color(Enum):
    RED = 1
    BLACK = 2


class Suit(Enum):
    CLUBS = 1
    DIAMONDS = 2
    HEARTS = 3
    SPADES = 4

    def color(self) -> Color:
        if self in (Suit.CLUBS, Suit.SPADES):
            return Color.BLACK
        return Color.RED

    def bower_partner(self) -> Suit:
        return next(s for s in Suit if s != self and s.color() == self.color())


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


@dataclass
class Deck:
    cards: list[Card]


def standard_deck() -> Deck:
    cards = [Card(suit, rank) for suit in Suit for rank in PLAYING_RANKS]
    random.shuffle(cards)
    return Deck(cards)


@dataclass
class Hand:
    cards: list[Card]
    owner: Player


class Team(Enum):
    NORTH_SOUTH = 0
    EAST_WEST = 1


@dataclass
class Player:
    name: str
    hand: Hand
    is_human: bool
    team: Team


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
