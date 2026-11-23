# Tiny Chess — a 4 KB Python chess engine

A negamax alpha-beta engine in at most 4,096 bytes of Python
(`main.py`, built by the kit's `compress` from `src/engine.py`).
It talks to the make.fun env only, over HTTP, and plays the house
gauntlet: 6 games, alternating colours, from the book openings.

## Design

- **Board:** 0x88, signed-int pieces, incremental Zobrist hash.
- **Move gen:** full legal moves — castling, en passant, promotion.
  Perft-verified: startpos d4 197,281; Kiwipete d3 97,862; three
  more standard positions, all exact.
- **Search:** iterative deepening on a fixed node budget (50,000
  nodes/move, never a clock — replays are deterministic),
  transposition table, MVV-LVA + killer + history ordering.
- **Quiescence:** captures and promotions; full evasions in check.
- **Eval:** material (100/320/330/500/900) + piece-square tables,
  bishop pair, doubled/isolated/passed pawns, rooks on open
  files, king safety blended opening-to-endgame by phase.
  ~17k nodes/s in CPython; depth 4 midgame, 8–12 endgame.
## Grade it locally

No Docker here, so graded against the kit's env server locally;
see TRIAL.md.

## Submit

From inside the unpacked kit, with the connected keypair:

    node cli/makefun.mjs bundle
    node cli/makefun.mjs check
    node cli/makefun.mjs submit tiny-chess-01 \
      --repo https://github.com/<owner>/<repo> --commit <sha>

The repo must be public, created after the competition opened
(2026-11-10), MIT licence (see LICENSE). `src/engine.py` is the
readable source the bundle sends; it is not committed, because
the whole tree must stay under 8,192 bytes — `main.py` is the
whole graded entry.
