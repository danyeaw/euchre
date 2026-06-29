from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from euchre.cards import Card, Player, Rank, Suit, Team
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

WIDTH = 900
HEIGHT = 700
CARD_W = 64
CARD_H = 92
CARD_GAP = 8

TABLE_GREEN = (34, 100, 50)
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
RED = (200, 40, 40)
GRAY = (120, 120, 120)
LIGHT_GRAY = (200, 200, 200)
GOLD = (220, 180, 40)
DISABLED_OVERLAY = (100, 100, 100, 140)

SUIT_SYMBOL = {
    Suit.CLUBS: "♣",
    Suit.DIAMONDS: "♦",
    Suit.HEARTS: "♥",
    Suit.SPADES: "♠",
}

RANK_LABEL = {
    Rank.NINE: "9",
    Rank.TEN: "10",
    Rank.JACK: "J",
    Rank.QUEEN: "Q",
    Rank.KING: "K",
    Rank.ACE: "A",
}


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


def rank_label(rank: Rank) -> str:
    return RANK_LABEL[rank]


class Renderer:
    def __init__(self) -> None:
        pygame.font.init()
        self.layout = Layout()
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
        if game.upcard is not None and game.phase in (Phase.ORDERING_1, Phase.ORDERING_2):
            self._draw_upcard(surface, game.upcard)
        self._draw_south_hand(surface, game)
        self._draw_bid_buttons(surface, game)
        if game_over_text:
            self._draw_game_over(surface, game_over_text)
        return self.layout

    def _draw_hud(self, surface: pygame.Surface, game: GameState, message: str) -> None:
        trump_text = game.trump.name.lower() if game.trump else "none"
        hud = (
            f"NS {game.score[Team.NORTH_SOUTH]}  |  EW {game.score[Team.EAST_WEST]}"
            f"     Trump: {trump_text}"
            f"     Dealer: {game.dealer.name}"
            f"     Turn: {game.current_player.name}"
        )
        surface.blit(self._title_font.render(hud, True, WHITE), (16, 12))
        surface.blit(self._font.render(message, True, LIGHT_GRAY), (16, 42))

    def _player_by_name(self, game: GameState, name: str) -> Player:
        return next(player for player in game.players if player.name == name)

    def _draw_players(self, surface: pygame.Surface, game: GameState) -> None:
        positions = {
            "North": (WIDTH // 2, 100),
            "East": (WIDTH - 120, HEIGHT // 2 - 40),
            "West": (120, HEIGHT // 2 - 40),
            "South": (WIDTH // 2, HEIGHT - 180),
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
            if player.is_human:
                continue
            count = len(player.cards)
            for index in range(min(count, 5)):
                back_rect = pygame.Rect(
                    x - 40 + index * 12,
                    y + index * 2,
                    CARD_W // 2,
                    CARD_H // 2,
                )
                self._draw_card_back(surface, back_rect)
            if count > 0:
                count_text = self._small_font.render(str(count), True, WHITE)
                surface.blit(count_text, (x + 30, y))

    def _draw_trick(self, surface: pygame.Surface, game: GameState) -> None:
        if game.current_trick is None or not game.current_trick.plays:
            return
        trick_positions = {
            "North": (WIDTH // 2, HEIGHT // 2 - 70),
            "East": (WIDTH // 2 + 80, HEIGHT // 2),
            "West": (WIDTH // 2 - 80, HEIGHT // 2),
            "South": (WIDTH // 2, HEIGHT // 2 + 70),
        }
        for play in game.current_trick.plays:
            pos = trick_positions[play.player.name]
            rect = pygame.Rect(0, 0, CARD_W, CARD_H)
            rect.center = pos
            self._draw_card(surface, play.card, rect, game.trump)

    def _draw_upcard(self, surface: pygame.Surface, card: Card) -> None:
        rect = pygame.Rect(WIDTH // 2 - CARD_W // 2, HEIGHT // 2 - CARD_H // 2, CARD_W, CARD_H)
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
        human = self._player_by_name(game, "South")
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
            self.layout.hand_cards.append(CardHit(card=card, rect=rect, enabled=enabled))

    def _draw_bid_buttons(self, surface: pygame.Surface, game: GameState) -> None:
        if game.phase not in (Phase.ORDERING_1, Phase.ORDERING_2):
            return
        if not game.current_player.is_human:
            return
        buttons: list[tuple[str, Action]] = [("Pass", PassAction())]
        if game.phase == Phase.ORDERING_1 and game.upcard is not None:
            suit_name = game.upcard.suit.name.title()
            buttons.append((f"Order {suit_name}", OrderUpAction(game.upcard.suit)))
        elif game.phase == Phase.ORDERING_2 and game.upcard is not None:
            for suit in Suit:
                if suit == game.upcard.suit:
                    continue
                buttons.append((suit.name.title(), OrderUpAction(suit)))
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
        pygame.draw.rect(surface, WHITE, rect, border_radius=6)
        pygame.draw.rect(surface, BLACK, rect, width=2, border_radius=6)
        color = suit_color(card.suit)
        rank_text = self._font.render(rank_label(card.rank), True, color)
        suit_text = self._font.render(SUIT_SYMBOL[card.suit], True, color)
        surface.blit(rank_text, (rect.x + 6, rect.y + 4))
        surface.blit(suit_text, (rect.centerx - suit_text.get_width() // 2, rect.centery - 8))
        if trump is not None and card.rank == Rank.JACK:
            if card.suit == trump.bower_partner() or card.suit == trump:
                pygame.draw.rect(surface, GOLD, rect, width=3, border_radius=6)
        if not enabled:
            overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            overlay.fill(DISABLED_OVERLAY)
            surface.blit(overlay, rect.topleft)

    def _draw_card_back(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(surface, (40, 60, 140), rect, border_radius=4)
        pygame.draw.rect(surface, WHITE, rect, width=1, border_radius=4)

    def _draw_game_over(self, surface: pygame.Surface, text: str) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))
        rendered = self._title_font.render(text, True, GOLD)
        surface.blit(rendered, rendered.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
