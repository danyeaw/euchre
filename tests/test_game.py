from __future__ import annotations

import pytest

from euchre.cards import Card, Play, Player, Rank, Seat, Suit, Team, Trick
from euchre.game import (
    GameState,
    InvalidAction,
    OrderUpAction,
    PassAction,
    Phase,
    PlayCardAction,
    create_game,
    legal_actions,
    playable_cards,
)


def test_bower_ranks() -> None:
    trump = Suit.HEARTS
    left_bower = Card(Suit.DIAMONDS, Rank.JACK)
    right_bower = Card(Suit.HEARTS, Rank.JACK)

    assert left_bower.effective_suit(trump) == Suit.HEARTS
    assert right_bower.effective_suit(trump) == Suit.HEARTS
    assert left_bower.effective_rank(trump) == 15
    assert right_bower.effective_rank(trump) == 16
    assert right_bower.effective_rank(trump) > left_bower.effective_rank(trump)


def test_deal_advances_to_ordering() -> None:
    game = create_game()
    game.apply(PassAction())

    assert game.phase == Phase.ORDERING_1
    assert all(len(player.cards) == 5 for player in game.players)
    assert game.upcard is not None
    assert game.trump is None


def test_ordering_legal_actions() -> None:
    game = create_game()
    game.apply(PassAction())

    actions = legal_actions(game)

    assert PassAction() in actions
    assert any(
        isinstance(action, OrderUpAction) and action.suit == game.upcard.suit
        for action in actions
    )


def test_playable_cards_must_follow_suit() -> None:
    trump = Suit.HEARTS
    leader = Player("North", Seat.NORTH, [], False)
    follower = Player("South", Seat.SOUTH, [], True)
    heart = Card(Suit.HEARTS, Rank.NINE)
    club = Card(Suit.CLUBS, Rank.ACE)
    follower.cards = [heart, club]

    trick = Trick(
        plays=[Play(leader, Card(Suit.HEARTS, Rank.TEN))],
        led_suit=Suit.HEARTS,
        trump=trump,
    )
    game = GameState(
        players=[leader, follower],
        dealer=leader,
        trump=trump,
        trump_caller=follower,
        upcard=None,
        current_player=follower,
        phase=Phase.PLAYING,
        tricks_won={team: 0 for team in Team},
        score={team: 0 for team in Team},
        current_trick=trick,
        tricks_played=0,
        trick_winner=None,
    )

    assert playable_cards(game) == [heart]


def test_trick_winner_trump_beats_led_suit() -> None:
    trump = Suit.HEARTS
    north = Player("North", Seat.NORTH, [], False)
    east = Player("East", Seat.EAST, [], False)
    trick = Trick(
        plays=[
            Play(north, Card(Suit.SPADES, Rank.ACE)),
            Play(east, Card(Suit.HEARTS, Rank.NINE)),
        ],
        led_suit=Suit.SPADES,
        trump=trump,
    )

    assert trick.winner() is east


def test_invalid_play_raises() -> None:
    game = create_game()
    game.apply(PassAction())

    with pytest.raises(InvalidAction):
        game.apply(PlayCardAction(Card(Suit.CLUBS, Rank.ACE)))
