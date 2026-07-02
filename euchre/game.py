from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum, auto
from typing import Union

from euchre.cards import (
    Card,
    Play,
    Player,
    Seat,
    Suit,
    Team,
    Trick,
    standard_deck,
)

BOT_NAMES = (
    "R2-D2",
    "C-3PO",
    "HAL 9000",
    "WALL-E",
    "EVE",
    "Bender",
    "Rosie",
    "Marvin",
    "Baymax",
    "Robby The Robot",
    "Porygon",
    "Johnny 5",
)


class Phase(Enum):
    DEALING = auto()
    ORDERING_1 = auto()
    DEALER_DISCARD = auto()
    ORDERING_2 = auto()
    PLAYING = auto()
    TRICK_RESOLVING = auto()
    SCORING = auto()
    GAME_OVER = auto()


AUTO_ADVANCE_PHASES = frozenset(
    {Phase.DEALING, Phase.SCORING, Phase.TRICK_RESOLVING}
)
NON_INTERACTIVE_PHASES = frozenset({*AUTO_ADVANCE_PHASES, Phase.GAME_OVER})
ORDERING_PHASES = frozenset({Phase.ORDERING_1, Phase.ORDERING_2})
HAND_INPUT_PHASES = frozenset({Phase.PLAYING, Phase.DEALER_DISCARD})
TRICKS_VISIBLE_PHASES = frozenset(
    {Phase.PLAYING, Phase.SCORING, Phase.TRICK_RESOLVING}
)


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

CARD_ACTIONS = (PlayCardAction, DiscardAction)


class InvalidAction(Exception):
    def __init__(self, action: Action) -> None:
        self.action = action
        super().__init__(f"Invalid action: {action!r}")


def playable_cards(game: GameState) -> list[Card]:
    if game.trump is None or game.current_trick is None:
        return []
    hand = game.current_player.cards
    if not game.current_trick.plays:
        return list(hand)
    led_suit = game.current_trick.led_suit
    if led_suit is None:
        return list(hand)
    following = [card for card in hand if card.effective_suit(game.trump) == led_suit]
    return following if following else list(hand)


def _dealer_discard_cards(game: GameState) -> list[Card]:
    cards = list(game.dealer.cards)
    if game.upcard is not None:
        cards.append(game.upcard)
    return cards


def legal_actions(game: GameState) -> list[Action]:
    match game.phase:
        case Phase.DEALING:
            return [PassAction()]
        case Phase.ORDERING_1:
            if game.upcard is None:
                return []
            return [PassAction(), OrderUpAction(game.upcard.suit)]
        case Phase.ORDERING_2:
            if game.upcard is None:
                return []
            return [PassAction()] + [
                OrderUpAction(suit) for suit in Suit if suit != game.upcard.suit
            ]
        case Phase.DEALER_DISCARD:
            return [DiscardAction(card) for card in _dealer_discard_cards(game)]
        case Phase.PLAYING:
            return [PlayCardAction(card) for card in playable_cards(game)]
        case Phase.TRICK_RESOLVING:
            return [PassAction()]
        case Phase.SCORING | Phase.GAME_OVER:
            return []


def is_human_turn(game: GameState) -> bool:
    if not game.accepts_player_input:
        return False
    if game.phase == Phase.DEALER_DISCARD:
        return game.dealer.is_human
    return game.current_player.is_human


def legal_cards(game: GameState) -> list[Card]:
    return [
        action.card
        for action in legal_actions(game)
        if isinstance(action, CARD_ACTIONS)
    ]


def human_hand_cards(game: GameState) -> list[Card]:
    human = next(player for player in game.players if player.is_human)
    if game.phase == Phase.DEALER_DISCARD and game.dealer.is_human:
        return _dealer_discard_cards(game)
    return list(human.cards)


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
    tricks_played: int
    trick_winner: Player | None

    @property
    def auto_advances(self) -> bool:
        return self.phase in AUTO_ADVANCE_PHASES

    @property
    def accepts_player_input(self) -> bool:
        return self.phase not in NON_INTERACTIVE_PHASES

    @property
    def is_game_over(self) -> bool:
        return self.phase == Phase.GAME_OVER

    def apply(self, action: Action) -> None:
        if self.phase not in NON_INTERACTIVE_PHASES:
            if action not in legal_actions(self):
                raise InvalidAction(action)
        match self.phase:
            case Phase.DEALING:
                self._handle_dealing()
            case Phase.ORDERING_1:
                self._handle_ordering_1(action)
            case Phase.DEALER_DISCARD:
                if isinstance(action, DiscardAction):
                    self._handle_dealer_discard(action)
            case Phase.ORDERING_2:
                self._handle_ordering_2(action)
            case Phase.PLAYING:
                if isinstance(action, PlayCardAction):
                    self._handle_playing(action)
            case Phase.TRICK_RESOLVING:
                if isinstance(action, PassAction):
                    self._finalize_trick()
            case Phase.SCORING:
                self._handle_scoring()
            case Phase.GAME_OVER:
                pass

    def _handle_dealing(self) -> None:
        deck_iter = iter(standard_deck())

        self.trump = None
        self.trump_caller = None
        self.upcard = None
        self.current_trick = None
        self.trick_winner = None
        self.tricks_played = 0
        self.tricks_won = {team: 0 for team in Team}

        for player in self.players:
            player.cards = [next(deck_iter) for _ in range(2)]
            player.tricks_taken = []

        for player in self.players:
            player.cards.extend([next(deck_iter) for _ in range(3)])

        self.upcard = next(deck_iter)
        self.current_player = self.players[
            (self.players.index(self.dealer) + 1) % len(self.players)
        ]
        self.phase = Phase.ORDERING_1

    def _player_index(self, player: Player) -> int:
        return self.players.index(player)

    def _next_player(self, player: Player) -> Player:
        index = self._player_index(player)
        return self.players[(index + 1) % len(self.players)]

    def _left_of_dealer(self) -> Player:
        index = self._player_index(self.dealer)
        return self.players[(index + 1) % len(self.players)]

    def _rotate_dealer_and_deal(self) -> None:
        index = self._player_index(self.dealer)
        self.dealer = self.players[(index + 1) % len(self.players)]
        self.phase = Phase.DEALING
        self._handle_dealing()

    def _start_playing(self, trump: Suit) -> None:
        self.trump = trump
        self.phase = Phase.PLAYING
        self.current_player = self._left_of_dealer()
        self.current_trick = Trick(plays=[], led_suit=None, trump=trump)

    def _handle_ordering_1(self, action: Action) -> None:
        if self.upcard is None:
            return

        if isinstance(action, OrderUpAction):
            self.trump = action.suit
            self.trump_caller = self.current_player
            self.current_player = self.dealer
            self.phase = Phase.DEALER_DISCARD
            return

        first_bidder = self._left_of_dealer()
        next_player = self._next_player(self.current_player)
        if next_player == first_bidder:
            self.phase = Phase.ORDERING_2
        self.current_player = next_player

    def _handle_dealer_discard(self, action: DiscardAction) -> None:
        upcard = self.upcard
        trump = self.trump
        if upcard is None or trump is None:
            return

        self.dealer.cards.append(upcard)
        self.upcard = None
        self.dealer.cards.remove(action.card)
        self._start_playing(trump)

    def _handle_ordering_2(self, action: Action) -> None:
        if self.upcard is None:
            return

        if isinstance(action, OrderUpAction):
            self.trump = action.suit
            self.trump_caller = self.current_player
            self._start_playing(action.suit)
            return

        first_bidder = self._left_of_dealer()
        next_player = self._next_player(self.current_player)
        if next_player == first_bidder:
            self._rotate_dealer_and_deal()
        else:
            self.current_player = next_player

    def _handle_playing(self, action: PlayCardAction) -> None:
        trump = self.trump
        trick = self.current_trick
        if trump is None or trick is None:
            return

        card = action.card
        self.current_player.cards.remove(card)

        if not trick.plays:
            trick.led_suit = card.effective_suit(trump)
        trick.plays.append(Play(self.current_player, card))

        if len(trick.plays) == 4:
            winner = trick.winner()
            winning_card = next(p.card for p in trick.plays if p.player is winner)
            winner.tricks_taken.append(winning_card)
            self.tricks_won[winner.seat.team] += 1
            self.tricks_played += 1
            self.trick_winner = winner
            self.phase = Phase.TRICK_RESOLVING
        else:
            self.current_player = self._next_player(self.current_player)

    def _finalize_trick(self) -> None:
        trump = self.trump
        winner = self.trick_winner
        if trump is None or winner is None:
            return

        self.trick_winner = None
        self.current_trick = None

        if self.tricks_played == 5:
            self.phase = Phase.SCORING
        else:
            self.current_trick = Trick(plays=[], led_suit=None, trump=trump)
            self.current_player = winner
            self.phase = Phase.PLAYING

    def _handle_scoring(self) -> None:
        trump_caller = self.trump_caller
        if trump_caller is None:
            return
        calling_team = trump_caller.seat.team
        defending_team = calling_team.opponent()
        tricks = self.tricks_won[calling_team]

        if tricks == 5:
            self.score[calling_team] += 2
        elif tricks >= 3:
            self.score[calling_team] += 1
        else:
            self.score[defending_team] += 2

        if self.score[Team.TEAM_ONE] >= 10 or self.score[Team.TEAM_TWO] >= 10:
            self.phase = Phase.GAME_OVER
        else:
            self._rotate_dealer_and_deal()


def create_game() -> GameState:
    players: list[Player] = []
    bot_names = random.sample(BOT_NAMES, 3)
    specs = [
        (Seat.NORTH, bot_names[0], False),
        (Seat.EAST, bot_names[1], False),
        (Seat.SOUTH, "You", True),
        (Seat.WEST, bot_names[2], False),
    ]
    for seat, name, is_human in specs:
        players.append(
            Player(
                name=name,
                seat=seat,
                cards=[],
                is_human=is_human,
            )
        )

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
        tricks_played=0,
        trick_winner=None,
    )
