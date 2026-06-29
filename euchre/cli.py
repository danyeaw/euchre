import random

from euchre.cards import Card, Suit, Team
from euchre.game import (
    Action,
    DiscardAction,
    GameState,
    OrderUpAction,
    PassAction,
    Phase,
    PlayCardAction,
    create_game,
    legal_actions,
)

SUIT_KEYS = {
    "c": Suit.CLUBS,
    "d": Suit.DIAMONDS,
    "h": Suit.HEARTS,
    "s": Suit.SPADES,
}


def show_hand(player_name: str, cards: list[Card]) -> None:
    card_str = " ".join(str(card) for card in cards)
    print(f"{player_name}: {card_str}")


def show_numbered_cards(label: str, cards: list[Card]) -> None:
    print(label)
    for index, card in enumerate(cards):
        print(f"  {index}: {card}")


def show_table(game: GameState) -> None:
    print(f"\nPhase: {game.phase.name}")
    print(f"Dealer: {game.dealer.name}")
    if game.upcard:
        print(f"Upcard: {game.upcard}")
    if game.trump:
        print(f"Trump: {game.trump.name.lower()}")
    print(f"Score — NS: {game.score[Team.NORTH_SOUTH]}, EW: {game.score[Team.EAST_WEST]}")
    print(f"Turn: {game.current_player.name}")
    if game.current_trick and game.current_trick.plays:
        print("Trick:")
        for play in game.current_trick.plays:
            print(f"  {play.player.name}: {play.card}")


def describe_action(action: Action) -> str:
    if isinstance(action, PassAction):
        return "passes"
    if isinstance(action, OrderUpAction):
        return f"orders up {action.suit.name.lower()}"
    if isinstance(action, DiscardAction):
        return f"discards {action.card}"
    if isinstance(action, PlayCardAction):
        return f"plays {action.card}"
    return str(action)


def bot_choose_action(game: GameState) -> Action:
    return random.choice(legal_actions(game))


def prompt_bid(game: GameState) -> Action:
    if game.phase == Phase.ORDERING_1:
        print("Pass (p) or order up (o)? ", end="")
        choice = input().strip().lower()
        if choice == "o" and game.upcard is not None:
            return OrderUpAction(game.upcard.suit)
        return PassAction()

    print("Pass (p) or order up — clubs (c), diamonds (d), hearts (h), spades (s)? ", end="")
    choice = input().strip().lower()
    if choice in SUIT_KEYS and game.upcard and SUIT_KEYS[choice] != game.upcard.suit:
        return OrderUpAction(SUIT_KEYS[choice])
    return PassAction()


def prompt_discard(game: GameState) -> Action:
    options = [action.card for action in legal_actions(game) if isinstance(action, DiscardAction)]
    show_numbered_cards("Choose a card to discard:", options)
    choice = int(input("> "))
    return DiscardAction(options[choice])


def prompt_play(game: GameState) -> Action:
    options = [action.card for action in legal_actions(game) if isinstance(action, PlayCardAction)]
    show_numbered_cards("Legal plays:", options)
    choice = int(input("> "))
    return PlayCardAction(options[choice])


def prompt_human(game: GameState) -> Action:
    if game.phase in (Phase.ORDERING_1, Phase.ORDERING_2):
        return prompt_bid(game)
    if game.phase == Phase.DEALER_DISCARD:
        return prompt_discard(game)
    if game.phase == Phase.PLAYING:
        return prompt_play(game)
    return PassAction()


def choose_action(game: GameState) -> Action:
    while True:
        if game.current_player.is_human:
            action = prompt_human(game)
        else:
            action = bot_choose_action(game)
            print(f"{game.current_player.name} {describe_action(action)}")

        if action in legal_actions(game):
            return action
        print("Invalid choice, try again.")


def main() -> None:
    print("Euchre — you are South, partnered with North.")
    game = create_game()
    game.apply(PassAction())

    while game.phase != Phase.GAME_OVER:
        show_table(game)
        human = next(player for player in game.players if player.is_human)
        if human.cards and game.phase == Phase.PLAYING and game.current_player == human:
            show_numbered_cards("Your hand:", human.cards)

        if game.phase in (Phase.DEALING, Phase.SCORING):
            game.apply(PassAction())
            continue

        game.apply(choose_action(game))

    show_table(game)
    if game.score[Team.NORTH_SOUTH] >= 10:
        print("\nNorth/South win!")
    else:
        print("\nEast/West win!")


if __name__ == "__main__":
    main()
