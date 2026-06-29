from euchre.cards import Card, Team
from euchre.game import GameState, PassAction, create_game


def show_hand(player_name: str, cards: list[Card]) -> None:
    card_str = " ".join(str(card) for card in cards)
    print(f"{player_name}: {card_str}")


def show_table(game: GameState) -> None:
    print(f"\nPhase: {game.phase.name}")
    print(f"Dealer: {game.dealer.name}")
    print(f"Upcard: {game.upcard}")
    print(f"Trump: {game.trump or 'none'}")
    print(f"Score — NS: {game.score[Team.NORTH_SOUTH]}, EW: {game.score[Team.EAST_WEST]}")
    print(f"Turn: {game.current_player.name}")


def main() -> None:
    game = create_game()
    game.apply(PassAction())
    show_table(game)
    for player in game.players:
        if player.is_human:
            show_hand(player.name, player.hand.cards)


if __name__ == "__main__":
    main()
