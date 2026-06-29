from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Union

from euchre.cards import (
    Card,
    Hand,
    Player,
    Suit,
    Team,
    Trick,
    standard_deck,
)


class Phase(Enum):
    DEALING = auto()
    ORDERING_1 = auto()
    DEALER_DISCARD = auto()
    ORDERING_2 = auto()
    PLAYING = auto()
    SCORING = auto()
    GAME_OVER = auto()


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


@dataclass
class GameState:
    players: list[Player]
    dealer: Player
    trump: Suit | None
    trump_caller: Player | None
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
        deck_iter = iter(deck.cards)

        self.trump = None
        self.trump_caller = None
        self.upcard = None
        self.current_trick = None
        self.trick_history = []
        self.tricks_won = {team: 0 for team in Team}

        for player in self.players:
            player.hand.cards = [next(deck_iter) for _ in range(2)]

        for player in self.players:
            player.hand.cards.extend([next(deck_iter) for _ in range(3)])

        self.upcard = next(deck_iter)
        self.current_player = self.players[
            (self.players.index(self.dealer) + 1) % len(self.players)
        ]
        self.phase = Phase.ORDERING_1

    def _handle_ordering_1(self, action: Action) -> None:
        raise NotImplementedError

    def _handle_dealer_discard(self, action: Action) -> None:
        raise NotImplementedError

    def _handle_ordering_2(self, action: Action) -> None:
        raise NotImplementedError

    def _handle_playing(self, action: Action) -> None:
        raise NotImplementedError

    def _handle_scoring(self) -> None:
        raise NotImplementedError

    def _handle_game_over(self) -> None:
        pass


def create_game() -> GameState:
    players: list[Player] = []
    specs = [
        ("North", False, Team.NORTH_SOUTH),
        ("East", False, Team.EAST_WEST),
        ("South", True, Team.NORTH_SOUTH),
        ("West", False, Team.EAST_WEST),
    ]
    for name, is_human, team in specs:
        player = Player(name=name, hand=Hand(cards=[], owner=None), is_human=is_human, team=team)
        player.hand.owner = player
        players.append(player)

    dealer = players[0]
    return GameState(
        players=players,
        dealer=dealer,
        trump=None,
        trump_caller=None,
        upcard=None,
        current_player=dealer,
        phase=Phase.DEALING,
        tricks_won={team: 0 for team in Team},
        score={team: 0 for team in Team},
        current_trick=None,
        trick_history=[],
    )
