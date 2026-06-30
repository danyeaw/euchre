from __future__ import annotations

import pygame

from euchre.game import (
    Action,
    DiscardAction,
    GameState,
    Phase,
    PlayCardAction,
    legal_actions,
)
from euchre.ui.renderer import Layout


def is_human_turn(game: GameState) -> bool:
    if not game.accepts_player_input:
        return False
    if game.phase == Phase.DEALER_DISCARD:
        return game.dealer.is_human
    return game.current_player.is_human


def handle_event(
    event: pygame.event.Event, game: GameState, layout: Layout
) -> Action | None:
    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return None
    if not is_human_turn(game):
        return None

    pos = event.pos
    if game.phase in (Phase.ORDERING_1, Phase.ORDERING_2):
        for button in layout.buttons:
            if button.rect.collidepoint(pos):
                return button.action
        return None

    if game.phase in (Phase.PLAYING, Phase.DEALER_DISCARD):
        for hit in layout.hand_cards:
            if hit.enabled and hit.rect.collidepoint(pos):
                if game.phase == Phase.PLAYING:
                    return PlayCardAction(hit.card)
                return DiscardAction(hit.card)
        return None

    return None


def apply_if_legal(game: GameState, action: Action) -> bool:
    if action in legal_actions(game):
        game.apply(action)
        return True
    return False
