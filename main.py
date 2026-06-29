import random
from enum import Enum, auto
from dataclasses import dataclass
from typing import Union


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
        return next(s for s in Suit if s != self and s.color == self.color)


class Rank(Enum):
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14
    LEFT_BOWER = 15
    RIGHT_BOWER = 16



@dataclass
class Card:
    suit: Suit
    rank: Rank

    def effective_suit(self, trump: Suit) -> Suit:
        if self.rank == Rank.JACK and self.suit == trump.bower_partner():
            return trump
        return self.suit

    def effective_rank(self, trump: Suit) -> Rank:
        if self.rank == Rank.JACK:
            if self.suit == trump.bower_partner():
                return Rank.LEFT_BOWER
            if self.suit == trump:
                return Rank.RIGHT_BOWER
        return self.rank.value


def standard_deck() -> Deck:
    cards = [Card(suit, rank) for suit in Suit for rank in Rank]
    random.shuffle(cards)
    return Deck(cards)


@dataclass
class Deck:
    cards: list[Card]


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
        trump_plays = [play for play in self.plays if play.card.effective_suit(self.trump) == self.trump]
        if trump_plays:
            return max(trump_plays, key=lambda play: play.card.effective_rank(self.trump)).player
        led_plays = [play for play in self.plays if play.card.effective_suit(self.trump) == self.led_suit]
        return max(led_plays, key=lambda play: play.card.effective_rank(self.trump)).player


class Phase(Enum):
    DEALING = auto()
    ORDERING_1 = auto()
    DEALER_DISCARD = auto()
    ORDERING_2 = auto()
    PLAYING = auto()
    SCORING = auto()
    GAME_OVER = auto()


@dataclass
class GameState:
    players: list[Player]
    dealer: Player
    trump: Suit | None
    trump_caller: Player
    upcard: Card | None
    current_player: Player
    phase: Phase
    tricks_won: dict[Team, int]
    score: dict[Team, int]
    current_trick: Trick | None
    trick_history: list[Trick]

    def apply(self, action: Action) -> None:
        match self.phase:
            case Phase.DEALING:
                self._handle_dealing()
            case Phase.ORDERING_1:
                self._handle_ordering_1(action)
            case Phase.DEALER_DISCARD:
                self._handle_dealer_discard(action)
            case Phase.ORDERING_2:
                self._handle_ordering_2(action)
            case Phase.PLAYING:
                self._handle_playing(action)
            case Phase.SCORING:
                self._handle_scoring()
            case Phase.GAME_OVER:
                self._handle_game_over()

    def _handle_dealing(self) -> None:
        deck = standard_deck()
        deck_iter = iter(deck)

        # First deal 2
        for player in self.players:
            player.hand.cards = [next(deck_iter) for _ in range(2)]

        # Then deal 3
        for player in self.players:
            player.hand.cards.extend([next(deck_iter) for _ in range(3)])

        self.upcard = next(deck_iter)

        self.current_player = self.players[(self.players.index(self.dealer) + 1) % 4]
        self.phase = Phase.ORDERING_1



@dataclass
class PassAction:
    pass

@dataclass
class OrderUpAction:
    suit: Suit


@dataclass
class DiscardAction:
    card: Card


@dataclass
class PlayCardAction:
    card: Card


Action = Union[PassAction, OrderUpAction, DiscardAction, PlayCardAction]



if __name__ == '__main__':

    pass
