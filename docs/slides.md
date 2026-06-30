# Building a Card Game Without Spaghetti

Michigan Python — slide content (copy into your slide tool of choice)

---

## Slide 1: Spaghetti vs. actions

### How card-game logic turns into spaghetti

| Spaghetti | This project |
|-----------|--------------|
| `if pygame.mouse` inside scoring | `handle_event()` returns an `Action` |
| Phase checks in 10 files | `Phase` enum + `GameState.apply()` |
| "Can I play this?" in UI *and* rules | `legal_actions()` — one source of truth |
| Bowers as special cases at trick end | `Card.effective_suit()` / `effective_rank()` |

**One boundary:** game logic never imports pygame.

---

## Slide 2: Three layers

```
┌─────────────────────────────────────┐
│  Presentation (pygame)              │
│  client.py · ui/renderer · input    │
│  read state · draw · emit actions   │
└──────────────┬──────────────────────┘
               │ Action
               ▼
┌─────────────────────────────────────┐
│  Rules engine (pure Python)         │
│  game.py                            │
│  legal_actions() · apply()            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Domain (pure Python)               │
│  cards.py                           │
│  Card · Trick · Player · bowers     │
└─────────────────────────────────────┘
```

**Loop:** click → `Action` → `apply_if_legal` → `draw`

Bots: `random.choice(legal_actions(game))` — same API as humans.

---

## Slide 3: Euchre table layout

```
              [North]
                N
         partner of South
                │
   [West] W ────┼──── E [East]
                │
              [South]
              You (human)
```

- **Teams:** North + South vs East + West
- **Deck:** 24 cards (9–A × 4 suits)
- **Trump:** bid in two rounds; dealer picks up upcard or names suit
- **Bowers:** Jack of trump (right) + Jack of same-color suit (left)
- **Hand:** 5 tricks; call team needs 3+ to score
- **Win:** first team to **10** points

Repo: ~1,200 lines · 1 dependency (`pygame`) · core rules testable without a window
