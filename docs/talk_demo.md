# Live demo script — Michigan Python talk

Use this during rehearsal and at the podium. The REPL demos work without a display; the GUI demo needs pygame and a screen.

## Before the room

```bash
conda activate ./devenv   # or your venv
pip install -e ".[dev]"
pytest -q                 # should pass in ~1s
euchre                    # confirm window opens
```

Keep a terminal tab with imports pre-typed (see REPL section below).

**If pygame fails** (headless machine, display issues): skip the GUI and run REPL + pytest only. That still proves the architecture.

## REPL demo — Layer 1: bowers (no pygame)

```python
from euchre.cards import Card, Rank, Suit

trump = Suit.HEARTS
left_bower = Card(Suit.DIAMONDS, Rank.JACK)   # same color as hearts
right_bower = Card(Suit.HEARTS, Rank.JACK)

left_bower.effective_rank(trump)    # 15
right_bower.effective_rank(trump)   # 16
```

Talking point: bowers live on `Card` as methods, not scattered `if` checks at trick time.

## REPL demo — Layer 2: rules engine

```python
from euchre.game import create_game, legal_actions, PassAction, OrderUpAction, InvalidAction
from euchre.game import PlayCardAction
from euchre.cards import Card, Rank, Suit

g = create_game()
g.apply(PassAction())       # deal; moves to ORDERING_1

g.phase
legal_actions(g)            # [PassAction(), OrderUpAction(...)]

# Illegal play raises:
# g.apply(PlayCardAction(Card(Suit.CLUBS, Rank.ACE)))  # InvalidAction
```

Optional: order up and show phase change:

```python
up_suit = g.upcard.suit
g.apply(OrderUpAction(up_suit))
g.phase                     # DEALER_DISCARD or PLAYING after discard
```

## pytest demo — testable core (~30 seconds)

```bash
pytest -q
```

Or run one test live:

```bash
pytest tests/test_game.py::test_bower_ranks -v
```

## GUI demo — Layer 3: pygame shell

```bash
euchre
```

Narration path:

1. Point out HUD: trump, dealer `(D)`, current player `*`
2. Click **Pass** or order up the upcard suit
3. Play one trick as South — illegal cards are grayed out
4. Let bots play (1.2s delay) — they call `legal_actions()` same as clicks
5. Mention `accepts_player_input` — no clicks during deal/resolve/score

## What to avoid live

- Editing `renderer.py` layout math
- Walking through every `_handle_*` in `game.py` — pick dealing OR one trick

## Fallback order

1. REPL (bowers + `create_game`) — always works
2. `pytest -q` — always works
3. GUI — nice to have
