# Local grading — practice trials

Kit env server run locally (no Docker here, so no grade-local).
Same env, house engines, scorer formula.

## Trial-0 (compressed main.py, 50,000 nodes/move)

| Game | Opponent (anchor) | Colour | Result | Reason | Plies |
| --- | --- | --- | --- | --- | --- |
| 1 | depth-2 (855) | white | win | checkmate | 81 |
| 2 | depth-3 (1073) | black | win | checkmate | 128 |
| 3 | depth-4 (1199) | white | win | checkmate | 113 |
| 4 | nodes-100k (1392) | black | draw | threefold repetition | 106 |
| 5 | nodes-250k (1497) | white | win | checkmate | 131 |
| 6 | nodes-500k (1596) | black | loss | checkmate | 109 |

Points 4.5/6 — **Elo 1545**. Exit 0, no move lost on time
(~3 s/move, limit 10 s). Trial wall time ~12 minutes.

## Trials 1–2 (same engine)

- Trial-1: 4.0/6, Elo 1451 (wins vs depth-2, depth-4,
  nodes-250k; draws vs depth-3, nodes-100k; loss vs nodes-500k).
- Trial-2: 3.5/6, Elo 1364 (wins vs depth-2, nodes-250k;
  draws vs depth-4, nodes-100k, nodes-500k; losses vs depth-3,
  nodes-100k).
- **Mean Elo over the three practice trials: 1453.**

A 65k-node + repetition-avoidance variant scored lower (mean
1367) and was reverted; trial-0 re-run after the revert
reproduced this table exactly.

## Correctness

Perft exact (startpos d4 197,281; Kiwipete d3 97,862).
Eval(startpos)=0. ~17k nodes/s.
