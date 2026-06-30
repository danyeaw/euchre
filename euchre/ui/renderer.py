from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from euchre.cards import (
    Card,
    Player,
    Rank,
    RANK_LABEL,
    Suit,
    Team,
    SUIT_SYMBOL,
    suit_symbol,
)
from euchre.ui.card_images import CardImages
from euchre.ui.text import blit_text, symbol_font
from euchre.game import (
    Action,
    DiscardAction,
    GameState,
    OrderUpAction,
    PassAction,
    Phase,
    PlayCardAction,
    legal_actions,
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


def rank_label(rank: Rank) -> str:
    return RANK_LABEL[rank]


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
        if game.upcard is not None and game.phase in (
            Phase.ORDERING_1,
            Phase.ORDERING_2,
        ):
            self._draw_upcard(surface, game.upcard)
        self._draw_south_hand(surface, game)
        self._draw_bid_buttons(surface, game)
        if game_over_text:
            self._draw_game_over(surface, game_over_text)
        return self.layout

    def _draw_hud(self, surface: pygame.Surface, game: GameState, message: str) -> None:
        trump_part = suit_symbol(game.trump) if game.trump is not None else "none"
        hud = (
            f"NS {game.score[Team.NORTH_SOUTH]}  |  EW {game.score[Team.EAST_WEST]}"
            f"     Trump: {trump_part}"
            f"     Dealer: {game.dealer.name}"
            f"     Turn: {game.current_player.name}"
        )
        blit_text(
            surface,
            (16, 12),
            hud,
            self._title_font,
            WHITE,
            symbol_color=_symbol_color,
        )
        blit_text(
            surface,
            (16, 42),
            message,
            self._font,
            LIGHT_GRAY,
            symbol_color=_symbol_color,
        )

    def _player_by_name(self, game: GameState, name: str) -> Player:
        return next(player for player in game.players if player.name == name)

    def _draw_players(self, surface: pygame.Surface, game: GameState) -> None:
        positions = {
            "North": (WIDTH // 2, 100),
            "East": (WIDTH - 120, HEIGHT // 2 - 40),
            "West": (120, HEIGHT // 2 - 40),
            "South": (WIDTH // 2, HEIGHT - 250),
        }
        taken_anchors = {
            "North": (WIDTH // 2 - 50, 170, 1),
            "East": (WIDTH - 200, HEIGHT // 2 - 26, -1),
            "West": (200, HEIGHT // 2 - 26, 1),
            "South": (WIDTH // 2 - 120, HEIGHT - 310, 1),
        }
        for name, (x, y) in positions.items():
            player = self._player_by_name(game, name)
            label = player.name
            if player == game.dealer:
                label += " (D)"
            if player == game.current_player and game.phase not in (
                Phase.DEALING,
                Phase.SCORING,
                Phase.GAME_OVER,
            ):
                label += " *"
            text = self._font.render(label, True, WHITE)
            rect = text.get_rect(center=(x, y - 30))
            surface.blit(text, rect)
            anchor_x, anchor_y, stack_dir = taken_anchors[name]
            self._draw_taken_tricks(
                surface, game, player, anchor_x, anchor_y, stack_direction=stack_dir
            )
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
            if count > 0:
                count_text = self._small_font.render(str(count), True, WHITE)
                surface.blit(count_text, (x + 30, y))

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
        if game.phase not in (Phase.PLAYING, Phase.SCORING):
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
            "North": (WIDTH // 2, HEIGHT // 2 - CARD_H * 3 // 4),
            "East": (WIDTH // 2 + CARD_W + 20, HEIGHT // 2),
            "West": (WIDTH // 2 - CARD_W - 20, HEIGHT // 2),
            "South": (WIDTH // 2, HEIGHT // 2 + CARD_H * 3 // 4),
        }
        for play in game.current_trick.plays:
            pos = trick_positions[play.player.name]
            rect = pygame.Rect(0, 0, CARD_W, CARD_H)
            rect.center = pos
            self._draw_card(surface, play.card, rect, game.trump)

    def _draw_upcard(self, surface: pygame.Surface, card: Card) -> None:
        rect = pygame.Rect(
            WIDTH // 2 - CARD_W // 2, HEIGHT // 2 - CARD_H // 2, CARD_W, CARD_H
        )
        label = self._small_font.render("Upcard", True, GOLD)
        surface.blit(label, label.get_rect(center=(rect.centerx, rect.top - 14)))
        self._draw_card(surface, card, rect, None)

    def _legal_cards(self, game: GameState) -> list[Card]:
        actions = legal_actions(game)
        cards: list[Card] = []
        for action in actions:
            if isinstance(action, (PlayCardAction, DiscardAction)):
                cards.append(action.card)
        return cards

    def _south_hand_cards(self, game: GameState) -> list[Card]:
        human = next(player for player in game.players if player.is_human)
        if game.phase == Phase.DEALER_DISCARD and game.dealer.is_human:
            cards = list(game.dealer.cards)
            if game.upcard is not None:
                cards.append(game.upcard)
            return cards
        return list(human.cards)

    def _draw_south_hand(self, surface: pygame.Surface, game: GameState) -> None:
        cards = self._south_hand_cards(game)
        if not cards:
            return
        legal = self._legal_cards(game)
        selectable = game.phase in (Phase.PLAYING, Phase.DEALER_DISCARD) and (
            (game.phase == Phase.PLAYING and game.current_player.is_human)
            or (game.phase == Phase.DEALER_DISCARD and game.dealer.is_human)
        )
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
        if game.phase not in (Phase.ORDERING_1, Phase.ORDERING_2):
            return
        if not game.current_player.is_human:
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
        rank_text = self._font.render(rank_label(card.rank), True, color)
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
