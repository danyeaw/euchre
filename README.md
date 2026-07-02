# euchre

A simple Euchre game in Python — built as a teaching example for separating card-game logic from UI.

## Run

```bash
pip install -e .
euchre
```

Or: `python main.py`

Install dev dependencies to run tests:

```bash
pip install -e ".[dev]"
pytest
```

## Architecture

The code is split into three layers. Game logic never imports pygame.

| Layer | Modules | Responsibility |
|-------|---------|----------------|
| **Domain** | `euchre/cards.py` | Cards, suits, ranks, bowers, tricks, players |
| **Rules engine** | `euchre/game.py` | Phases, actions, `legal_actions()`, `GameState.apply()` |
| **Presentation** | `euchre/client.py`, `euchre/ui/` | pygame loop, rendering, mouse input |

```
  client.py  ──►  game.py  ──►  cards.py
      │              ▲
      └── ui/*  ─────┘
```

**Pattern:** the UI produces *actions* (`PassAction`, `PlayCardAction`, …). The rules engine validates them via `legal_actions()` and applies them through `GameState.apply()`. Bots use the same API as human clicks.

Key properties on `GameState` for the UI:

- `accepts_player_input` — whether clicks should be handled
- `auto_advances` — dealing, trick resolution, and scoring advance on a timer
- `is_game_over` — match finished

## Euchre primer

New to Euchre? See [How to Play Euchre](https://bicyclecards.com/how-to-play/euchre) for the full rules. Quick summary:

- 4 players in teams of 2 (partners sit across from each other)
- 24-card deck (9 through Ace in each suit)
- Bid to choose trump; the Jack of the same color as trump is the left bower
- Play 5 tricks; calling team scores 1 point for 3–4 tricks, 2 for all 5, or gets euchred (opponents +2) for ≤2
- First team to 10 wins

## Assets

Face card images are from [Webisso playing-cards](https://github.com/Webisso/playing-cards) (MIT).
