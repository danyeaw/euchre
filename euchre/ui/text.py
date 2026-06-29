from __future__ import annotations

from collections.abc import Callable

import pygame

from euchre.cards import SUIT_SYMBOL

SUIT_SYMBOL_CHARS = frozenset(SUIT_SYMBOL.values())

_SYMBOL_FONT_CANDIDATES = (
    "Apple Symbols",
    "Segoe UI Symbol",
    "DejaVu Sans",
    "Symbol",
    "Helvetica",
)

_symbol_fonts: dict[int, pygame.font.Font] = {}


def _font_renders_suit_symbols(font: pygame.font.Font) -> bool:
    return font.render("♥", True, (255, 255, 255)).get_width() >= 12


def symbol_font(size: int) -> pygame.font.Font:
    cached = _symbol_fonts.get(size)
    if cached is not None:
        return cached
    for name in _SYMBOL_FONT_CANDIDATES:
        font = pygame.font.SysFont(name, size)
        if _font_renders_suit_symbols(font):
            _symbol_fonts[size] = font
            return font
    font = pygame.font.SysFont(None, size)
    _symbol_fonts[size] = font
    return font


def blit_text(
    surface: pygame.Surface,
    pos: tuple[int, int],
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    *,
    symbol_color: Callable[[str], tuple[int, int, int]] | None = None,
) -> int:
    x, y = pos
    sym_font = symbol_font(font.get_height())
    y_adjust = font.get_ascent() - sym_font.get_ascent()
    for char in text:
        if char in SUIT_SYMBOL_CHARS:
            chosen_font = sym_font
            chosen_color = symbol_color(char) if symbol_color else color
            char_y = y + y_adjust
        else:
            chosen_font = font
            chosen_color = color
            char_y = y
        rendered = chosen_font.render(char, True, chosen_color)
        surface.blit(rendered, (x, char_y))
        x += rendered.get_width()
    return x
