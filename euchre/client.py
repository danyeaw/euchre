from __future__ import annotations

import random

import pygame

from euchre.cards import Team, card_label, suit_symbol
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
from euchre.ui.input import apply_if_legal, handle_event, is_human_turn
from euchre.ui.renderer import HEIGHT, WIDTH, Renderer

ACTION_DELAY_MS = 1200


def describe_action(action: Action) -> str:
    if isinstance(action, PassAction):
        return "passes"
    if isinstance(action, OrderUpAction):
        return f"orders up {suit_symbol(action.suit)}"
    if isinstance(action, DiscardAction):
        return f"discards {card_label(action.card)}"
    if isinstance(action, PlayCardAction):
        return f"plays {card_label(action.card)}"
    return str(action)


def bot_choose_action(game: GameState) -> Action:
    return random.choice(legal_actions(game))


def game_over_message(game: GameState) -> str:
    if game.score[Team.NORTH_SOUTH] >= 10:
        return "North/South win!"
    return "East/West win!"


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Euchre")
    clock = pygame.time.Clock()
    renderer = Renderer()

    game = create_game()
    game.apply(PassAction())

    message = "You are South, partnered with North."
    running = True

    pending_bot_action: Action | None = None
    pending_bot_player: str | None = None
    bot_apply_at: int = 0
    pending_phase_advance_at: int = 0

    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif game.phase != Phase.GAME_OVER and is_human_turn(game):
                action = handle_event(event, game, renderer.layout)
                if action is not None and apply_if_legal(game, action):
                    message = f"You {describe_action(action)}"

        if game.phase in (Phase.DEALING, Phase.SCORING):
            pending_bot_action = None
            pending_bot_player = None
            if pending_phase_advance_at == 0:
                pending_phase_advance_at = now + ACTION_DELAY_MS
            elif now >= pending_phase_advance_at:
                game.apply(PassAction())
                pending_phase_advance_at = 0
        elif game.phase != Phase.GAME_OVER and not is_human_turn(game):
            pending_phase_advance_at = 0
            if pending_bot_action is None:
                pending_bot_action = bot_choose_action(game)
                pending_bot_player = game.current_player.name
                bot_apply_at = now + ACTION_DELAY_MS
            elif now >= bot_apply_at:
                game.apply(pending_bot_action)
                message = f"{pending_bot_player} {describe_action(pending_bot_action)}"
                pending_bot_action = None
                pending_bot_player = None
        else:
            pending_phase_advance_at = 0
            pending_bot_action = None
            pending_bot_player = None

        over_text = game_over_message(game) if game.phase == Phase.GAME_OVER else None
        renderer.draw(screen, game, message, game_over_text=over_text)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
