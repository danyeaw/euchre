from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from euchre.cards import (
    Card,
    Player,
    Rank,
    RANK_LABEL,
    Seat,
    Suit,
    Team,
    SUIT_SYMBOL,
    suit_symbol,
    team_color,
    team_label,
)
from euchre.ui.card_images import CardImages
from euchre.ui.text import blit_text, symbol_font
from euchre.game import (
    Action,
    GameState,
    HAND_INPUT_PHASES,
    ORDERING_PHASES,
    OrderUpAction,
    PassAction,
    TRICKS_VISIBLE_PHASES,
    Phase,
    human_hand_cards,
    is_human_turn,
    legal_actions,
    legal_cards,
)

WIDTH = 1024
HEIGHT = 768
CARD_W = 115
CARD_H = 166
CARD_GAP = 12
TAKEN_CARD_W = 46
TAKEN_CARD_H = 66
TAKEN_STACK_GAP = 8
BACK_CARD_W = CARD_W * 4 // 5
BACK_CARD_H = CARD_H * 4 // 5

TABLE_GREEN = (34, 100, 50)
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
RED = (200, 40, 40)
GRAY = (120, 120, 120)
LIGHT_GRAY = (200, 200, 200)
GOLD = (220, 180, 40)
DISABLED_OVERLAY = (100, 100, 100, 140)

@dataclass
class CardHit:
    card: Card
    rect: pygame.Rect
    enabled: bool


@dataclass
class ButtonHit:
    action: Action
    rect: pygame.Rect
    label: str


@dataclass
class Layout:
    hand_cards: list[CardHit] = field(default_factory=list)
    buttons: list[ButtonHit] = field(default_factory=list)


def suit_color(suit: Suit) -> tuple[int, int, int]:
    if suit in (Suit.HEARTS, Suit.DIAMONDS):
        return RED
    return BLACK


def _symbol_color(char: str) -> tuple[int, int, int]:
    for suit, symbol in SUIT_SYMBOL.items():
        if symbol == char:
            return suit_color(suit)
    return WHITE


class Renderer:
    def __init__(self) -> None:
        pygame.font.init()
        self.layout = Layout()
        self._images = CardImages()
        self._font = pygame.font.SysFont(None, 24)
        self._small_font = pygame.font.SysFont(None, 20)
        self._title_font = pygame.font.SysFont(None, 28)

    def draw(
        self,
        surface: pygame.Surface,
        game: GameState,
        message: str,
        game_over_text: str | None = None,
    ) -> Layout:
        self.layout = Layout()
        surface.fill(TABLE_GREEN)
        self._draw_hud(surface, game, message)
        self._draw_players(surface, game)
        self._draw_trick(surface, game)
        if game.upcard is not None and game.phase in ORDERING_PHASES:
            self._draw_upcard(surface, game.upcard)
        self._draw_south_hand(surface, game)
        self._draw_bid_buttons(surface, game)
        if game_over_text:
            self._draw_game_over(surface, game_over_text)
        return self.layout

    def _draw_hud(self, surface: pygame.Surface, game: GameState, message: str) -> None:
        self._draw_scoreboard(surface, game)
        self._draw_status(surface, game, message)

    def _draw_scoreboard(self, surface: pygame.Surface, game: GameState) -> None:
        box_w, box_h, gap = 200, 52, 16
        total_w = box_w * 2 + gap
        start_x = (WIDTH - total_w) // 2
        y = 8
        score_one = game.score[Team.TEAM_ONE]
        score_two = game.score[Team.TEAM_TWO]
        leading = score_one != score_two

        for index, team in enumerate((Team.TEAM_ONE, Team.TEAM_TWO)):
            x = start_x + index * (box_w + gap)
            rect = pygame.Rect(x, y, box_w, box_h)
            color = team_color(team)
            fill = tuple(max(0, c // 4) for c in color)
            pygame.draw.rect(surface, fill, rect, border_radius=8)
            border_width = 3 if leading and game.score[team] == max(score_one, score_two) else 2
            pygame.draw.rect(surface, color, rect, width=border_width, border_radius=8)

            name_text = self._small_font.render(team_label(team), True, color)
            name_rect = name_text.get_rect(midtop=(rect.centerx, rect.y + 6))
            surface.blit(name_text, name_rect)

            score_text = self._title_font.render(str(game.score[team]), True, WHITE)
            score_rect = score_text.get_rect(midbottom=(rect.centerx, rect.bottom - 6))
            surface.blit(score_text, score_rect)

    def _draw_status(self, surface: pygame.Surface, game: GameState, message: str) -> None:
        trump_part = suit_symbol(game.trump) if game.trump is not None else "none"
        status = (
            f"Trump: {trump_part}"
            f"     Dealer: {game.dealer.name}"
            f"     Turn: {game.current_player.name}"
        )
        blit_text(
            surface,
            (16, 68),
            status,
            self._font,
            LIGHT_GRAY,
            symbol_color=_symbol_color,
        )
        blit_text(
            surface,
            (16, 90),
            message,
            self._font,
            LIGHT_GRAY,
            symbol_color=_symbol_color,
        )

    def _draw_players(self, surface: pygame.Surface, game: GameState) -> None:
        positions = {
            Seat.NORTH: (WIDTH // 2, 100),
            Seat.EAST: (WIDTH - 120, HEIGHT // 2 - 40),
            Seat.WEST: (120, HEIGHT // 2 - 40),
            Seat.SOUTH: (WIDTH // 2, HEIGHT - 250),
        }
        taken_anchors = {
            Seat.NORTH: (WIDTH // 2 + 90, 95, 1),
            Seat.EAST: (WIDTH - 300, HEIGHT // 2, -1),
            Seat.WEST: (300, HEIGHT // 2, 1),
            Seat.SOUTH: (WIDTH // 2 + 100, HEIGHT - 300, 1),
        }
        for player in game.players:
            x, y = positions[player.seat]
            label = player.name
            if player == game.dealer:
                label += " (D)"
            if player == game.current_player and game.accepts_player_input:
                label += " *"
            text = self._font.render(label, True, team_color(player.seat.team))
            rect = text.get_rect(center=(x, y - 30))
            surface.blit(text, rect)
            if player.is_human:
                continue
            count = len(player.cards)
            for index in range(min(count, 5)):
                back_rect = pygame.Rect(
                    x - BACK_CARD_W + index * (BACK_CARD_W // 4),
                    y + index * 2,
                    BACK_CARD_W,
                    BACK_CARD_H,
                )
                self._draw_card_back(surface, back_rect)

        for player in game.players:
            anchor_x, anchor_y, stack_dir = taken_anchors[player.seat]
            self._draw_taken_tricks(
                surface, game, player, anchor_x, anchor_y, stack_direction=stack_dir
            )

    def _draw_taken_tricks(
        self,
        surface: pygame.Surface,
        game: GameState,
        player: Player,
        anchor_x: int,
        anchor_y: int,
        *,
        stack_direction: int = 1,
    ) -> None:
        if game.phase not in TRICKS_VISIBLE_PHASES:
            return
        if not player.tricks_taken:
            return
        for index, card in enumerate(player.tricks_taken):
            x = anchor_x + index * TAKEN_STACK_GAP * stack_direction
            rect = pygame.Rect(x, anchor_y, TAKEN_CARD_W, TAKEN_CARD_H)
            self._draw_card(surface, card, rect, game.trump)

    def _draw_trick(self, surface: pygame.Surface, game: GameState) -> None:
        if game.current_trick is None or not game.current_trick.plays:
            return
        trick_positions = {
            Seat.NORTH: (WIDTH // 2, HEIGHT // 2 - CARD_H * 3 // 4),
            Seat.EAST: (WIDTH // 2 + CARD_W + 20, HEIGHT // 2),
            Seat.WEST: (WIDTH // 2 - CARD_W - 20, HEIGHT // 2),
            Seat.SOUTH: (WIDTH // 2, HEIGHT // 2 + CARD_H * 3 // 4),
        }
        winner = game.trick_winner if game.phase == Phase.TRICK_RESOLVING else None
        for play in game.current_trick.plays:
            pos = trick_positions[play.player.seat]
            rect = pygame.Rect(0, 0, CARD_W, CARD_H)
            rect.center = pos
            enabled = winner is None or play.player is winner
            self._draw_card(surface, play.card, rect, game.trump, enabled=enabled)

    def _draw_upcard(self, surface: pygame.Surface, card: Card) -> None:
        rect = pygame.Rect(
            WIDTH // 2 - CARD_W // 2, HEIGHT // 2 - CARD_H // 2, CARD_W, CARD_H
        )
        label = self._small_font.render("Upcard", True, GOLD)
        surface.blit(label, label.get_rect(center=(rect.centerx, rect.top - 14)))
        self._draw_card(surface, card, rect, None)

    def _draw_south_hand(self, surface: pygame.Surface, game: GameState) -> None:
        cards = human_hand_cards(game)
        if not cards:
            return
        legal = legal_cards(game)
        selectable = game.phase in HAND_INPUT_PHASES and is_human_turn(game)
        total_w = len(cards) * CARD_W + (len(cards) - 1) * CARD_GAP
        start_x = (WIDTH - total_w) // 2
        y = HEIGHT - CARD_H - 24
        for index, card in enumerate(cards):
            rect = pygame.Rect(start_x + index * (CARD_W + CARD_GAP), y, CARD_W, CARD_H)
            enabled = selectable and card in legal
            self._draw_card(surface, card, rect, game.trump, enabled=enabled)
            self.layout.hand_cards.append(
                CardHit(card=card, rect=rect, enabled=enabled)
            )

    def _draw_bid_buttons(self, surface: pygame.Surface, game: GameState) -> None:
        if game.phase not in ORDERING_PHASES or not is_human_turn(game):
            return
        buttons: list[tuple[str, Action]] = []
        for action in legal_actions(game):
            if isinstance(action, PassAction):
                buttons.append(("Pass", action))
            elif isinstance(action, OrderUpAction):
                buttons.append((action.suit.name.title(), action))
        self._place_buttons(surface, buttons, y=HEIGHT - CARD_H - 80)

    def _place_buttons(
        self,
        surface: pygame.Surface,
        buttons: list[tuple[str, Action]],
        y: int,
    ) -> None:
        btn_w, btn_h, gap = 110, 36, 10
        total_w = len(buttons) * btn_w + (len(buttons) - 1) * gap
        start_x = (WIDTH - total_w) // 2
        for index, (label, action) in enumerate(buttons):
            rect = pygame.Rect(start_x + index * (btn_w + gap), y, btn_w, btn_h)
            pygame.draw.rect(surface, (50, 80, 130), rect, border_radius=6)
            pygame.draw.rect(surface, WHITE, rect, width=2, border_radius=6)
            text = self._small_font.render(label, True, WHITE)
            surface.blit(text, text.get_rect(center=rect.center))
            self.layout.buttons.append(ButtonHit(action=action, rect=rect, label=label))

    def _draw_card(
        self,
        surface: pygame.Surface,
        card: Card,
        rect: pygame.Rect,
        trump: Suit | None,
        *,
        enabled: bool = True,
    ) -> None:
        image = self._images.face(card, (rect.width, rect.height))
        if image is not None:
            surface.blit(image, rect.topleft)
        else:
            self._draw_card_fallback(surface, card, rect)
        if trump is not None and card.rank == Rank.JACK:
            if card.suit == trump.bower_partner() or card.suit == trump:
                pygame.draw.rect(surface, GOLD, rect, width=3, border_radius=6)
        if not enabled:
            overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            overlay.fill(DISABLED_OVERLAY)
            surface.blit(overlay, rect.topleft)

    def _draw_card_fallback(
        self,
        surface: pygame.Surface,
        card: Card,
        rect: pygame.Rect,
    ) -> None:
        pygame.draw.rect(surface, WHITE, rect, border_radius=6)
        pygame.draw.rect(surface, BLACK, rect, width=2, border_radius=6)
        color = suit_color(card.suit)
        rank_text = self._font.render(RANK_LABEL[card.rank], True, color)
        sym_font = symbol_font(self._font.get_height())
        suit_text = sym_font.render(suit_symbol(card.suit), True, color)
        surface.blit(rank_text, (rect.x + 6, rect.y + 4))
        surface.blit(
            suit_text, (rect.centerx - suit_text.get_width() // 2, rect.centery - 8)
        )

    def _draw_card_back(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        image = self._images.back((rect.width, rect.height))
        if image is not None:
            surface.blit(image, rect.topleft)
            return
        pygame.draw.rect(surface, (40, 60, 140), rect, border_radius=4)
        pygame.draw.rect(surface, WHITE, rect, width=1, border_radius=4)

    def _draw_game_over(self, surface: pygame.Surface, text: str) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))
        rendered = self._title_font.render(text, True, GOLD)
        surface.blit(rendered, rendered.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
