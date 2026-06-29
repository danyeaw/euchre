from __future__ import annotations

import logging
from importlib.resources import files

import pygame

from euchre.cards import Card, PLAYING_RANKS, Rank, Suit

logger = logging.getLogger(__name__)

_RANK_NAMES = {
    Rank.NINE: "9",
    Rank.TEN: "10",
    Rank.JACK: "jack",
    Rank.QUEEN: "queen",
    Rank.KING: "king",
    Rank.ACE: "ace",
}


def card_filename(card: Card) -> str:
    rank = _RANK_NAMES[card.rank]
    suit = card.suit.name.lower()
    return f"{rank}_of_{suit}.png"


class CardImages:
    def __init__(self) -> None:
        self._faces: dict[tuple[Suit, Rank], pygame.Surface] = {}
        self._back: pygame.Surface | None = None
        self._scaled: dict[tuple, pygame.Surface] = {}
        self._load()

    def _assets_dir(self):
        return files("euchre") / "assets" / "cards"

    def _load_image(self, name: str) -> pygame.Surface | None:
        path = self._assets_dir() / name
        try:
            with path.open("rb") as handle:
                return pygame.image.load(handle).convert_alpha()
        except (FileNotFoundError, OSError):
            logger.warning("missing card image: %s", name)
            return None

    def _load(self) -> None:
        for suit in Suit:
            for rank in PLAYING_RANKS:
                card = Card(suit, rank)
                image = self._load_image(card_filename(card))
                if image is not None:
                    self._faces[(suit, rank)] = image
        self._back = self._load_image("back.png")

    def _scale(self, surface: pygame.Surface, size: tuple[int, int]) -> pygame.Surface:
        if surface.get_size() == size:
            return surface
        src_w, src_h = surface.get_size()
        dst_w, dst_h = size
        if dst_w % src_w == 0 and dst_h % src_h == 0 and dst_w // src_w == dst_h // src_h:
            return pygame.transform.scale(surface, size)
        return pygame.transform.smoothscale(surface, size)

    def face(self, card: Card, size: tuple[int, int]) -> pygame.Surface | None:
        source = self._faces.get((card.suit, card.rank))
        if source is None:
            return None
        key = ("face", card.suit, card.rank, size)
        cached = self._scaled.get(key)
        if cached is None:
            cached = self._scale(source, size)
            self._scaled[key] = cached
        return cached

    def back(self, size: tuple[int, int]) -> pygame.Surface | None:
        if self._back is None:
            return None
        key = ("back", size)
        cached = self._scaled.get(key)
        if cached is None:
            cached = self._scale(self._back, size)
            self._scaled[key] = cached
        return cached
