import json, os, sys
import urllib.request as u
from urllib.error import HTTPError
from random import Random
ENV = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL is not set")
MATE = 100000
VAL = [0, 100, 320, 330, 500, 900, 0]
NS = (33, 31, 18, 14, -33, -31, -18, -14)
KS = (1, -1, 16, -16, 15, 17, -15, -17)
BS = (15, 17, -15, -17)
RS = (1, -1, 16, -16)
DS = BS + RS
S64 = [r * 16 + f for r in range(8) for f in range(8)]
CK = [15] * 128
CK[0] = 13; CK[7] = 14; CK[4] = 12; CK[112] = 7; CK[119] = 11; CK[116] = 3
CAP, EP, CAS, DBL = 1 << 17, 2 << 17, 4 << 17, 8 << 17
PA = (0, 0, 4, 8, 14, 24, 40, 0)
PC = (0, 0, 0, 10, 15, 10, 5, 0)
KO = (20, 25, 10, 0, 0, 10, 25, 20)
_R = Random(20261123)
Z = [[_R.getrandbits(64) for _ in range(128)] for _ in range(12)]
ZS = _R.getrandbits(64)
ZC = [_R.getrandbits(64) for _ in range(16)]
ZE = [_R.getrandbits(64) for _ in range(8)]
B = [0] * 128
STM = 1
CR = 0
EPS = -1
HASH = 0
KSQ = [4, 116]
TT = {}
KILL = [[0, 0] for _ in range(128)]
HIST = [[[0] * 128 for _ in range(128)] for _ in range(2)]
NODES = 0
LIMIT = 50000
class Abort(Exception): pass
def sq(s): return "abcdefgh"[s & 7] + str((s >> 4) + 1)
def uci(m):
    p = (m >> 14) & 7
    return sq(m & 127) + sq((m >> 7) & 127) + ("nbrq"[p - 2] if p else "")
def zi(pc): return (abs(pc) - 1) * 2 + (pc < 0)
def fen(f):
    global B, STM, CR, EPS, HASH, KSQ
    B = [0] * 128
    p = f.split()
    HASH = 0
    for i, row in enumerate(p[0].split("/")):
        r = 7 - i; fl = 0
        for c in row:
            if c.isdigit(): fl += int(c)
            else:
                pc = "PNBRQK".index(c.upper()) + 1
                if c.islower(): pc = -pc
                s = r * 16 + fl
                B[s] = pc; HASH ^= Z[zi(pc)][s]
                if abs(pc) == 6: KSQ[0 if pc > 0 else 1] = s
                fl += 1
    STM = 1 if p[1] == "w" else -1
    CR = 0
    if len(p) > 2:
        for c in p[2]: CR |= {"K": 1, "Q": 2, "k": 4, "q": 8}.get(c, 0)
    EPS = -1
    if len(p) > 3 and p[3] != "-":
        EPS = (int(p[3][1]) - 1) * 16 + ord(p[3][0]) - 97
        HASH ^= ZE[EPS & 7]
    if STM < 0: HASH ^= ZS
    HASH ^= ZC[CR]
def atk(s, w):
    def pc(x): return B[x] if not (x & 0x88) else 0
    if w:
        if pc(s - 15) == 1 or pc(s - 17) == 1: return True
    elif pc(s + 15) == -1 or pc(s + 17) == -1: return True
    for d in NS:
        if pc(s + d) == (2 if w else -2): return True
    for d in KS:
        if pc(s + d) == (6 if w else -6): return True
    bd = 3 if w else -3; rd = 4 if w else -4; qd = 5 if w else -5
    for i, d in enumerate(DS):
        t = s + d
        while not (t & 0x88):
            v = B[t]
            if v:
                if i < 4:
                    if v == bd or v == qd: return True
                elif v == rd or v == qd: return True
                break
            t += d
    return False
def gen(caps=False):
    ms = []
    w = STM > 0
    d = 16 if w else -16
    sr = 1 if w else 6
    pr = 7 if w else 0
    for s in S64:
        pc = B[s]
        if not pc or (pc > 0) != w: continue
        t = abs(pc)
        if t == 1:
            o = s + d
            if B[o] == 0 and (not caps or (o >> 4) == pr):
                if (o >> 4) == pr:
                    for q in (5, 4, 3, 2): ms.append(s | (o << 7) | (q << 14))
                else:
                    ms.append(s | (o << 7))
                    if (s >> 4) == sr and B[o + d] == 0: ms.append(s | ((o + d) << 7) | DBL)
            for o in (s + d - 1, s + d + 1):
                if o & 0x88: continue
                v = B[o]
                if v and (v > 0) != w:
                    if (o >> 4) == pr:
                        for q in (5, 4, 3, 2): ms.append(s | (o << 7) | (q << 14) | CAP)
                    else: ms.append(s | (o << 7) | CAP)
                elif o == EPS: ms.append(s | (o << 7) | CAP | EP)
        elif t == 2 or t == 6:
            for st in NS if t == 2 else KS:
                o = s + st
                if o & 0x88: continue
                v = B[o]
                if not v:
                    if not caps: ms.append(s | (o << 7))
                elif (v > 0) != w: ms.append(s | (o << 7) | CAP)
        else:
            for st in (BS if t == 3 else RS if t == 4 else BS + RS):
                o = s + st
                while not (o & 0x88):
                    v = B[o]
                    if not v:
                        if not caps: ms.append(s | (o << 7))
                    else:
                        if (v > 0) != w: ms.append(s | (o << 7) | CAP)
                        break
                    o += st
    if not caps:
        if w:
            if CR & 1 and B[5] == 0 and B[6] == 0 and B[7] == 4 and not atk(4, 0) and not atk(5, 0) and not atk(6, 0): ms.append(4 | (6 << 7) | CAS)
            if CR & 2 and B[3] == 0 and B[2] == 0 and B[1] == 0 and B[0] == 4 and not atk(4, 0) and not atk(3, 0) and not atk(2, 0): ms.append(4 | (2 << 7) | CAS)
        else:
            if CR & 4 and B[117] == 0 and B[118] == 0 and B[119] == -4 and not atk(116, 1) and not atk(117, 1) and not atk(118, 1): ms.append(116 | (118 << 7) | CAS)
            if CR & 8 and B[115] == 0 and B[114] == 0 and B[113] == 0 and B[112] == -4 and not atk(116, 1) and not atk(115, 1) and not atk(114, 1): ms.append(116 | (114 << 7) | CAS)
    return ms
def make(m):
    global STM, CR, EPS, HASH
    f = m & 127; t = (m >> 7) & 127
    pc = B[f]; fl = m & (CAP | EP | CAS | DBL); pr = (m >> 14) & 7
    cap = 0; cs = -1
    if fl & EP:
        cs = t - (16 if pc > 0 else -16); cap = B[cs]; B[cs] = 0
        HASH ^= Z[zi(cap)][cs]
    elif B[t]:
        cap = B[t]; HASH ^= Z[zi(cap)][t]
    np = (pr if pc > 0 else -pr) if pr else pc
    HASH ^= Z[zi(pc)][f] ^ Z[zi(np)][t]
    B[f] = 0; B[t] = np
    if abs(pc) == 6: KSQ[0 if pc > 0 else 1] = t
    if fl & CAS:
        a, b = {6: (7, 5), 2: (0, 3), 118: (119, 117), 114: (112, 115)}[t]
        rp = 4 if t < 100 else -4
        B[a] = 0; B[b] = rp; HASH ^= Z[zi(rp)][a] ^ Z[zi(rp)][b]
    old = (cap, CR, EPS, cs)
    CR &= CK[f] & CK[t]
    HASH ^= ZC[old[1]] ^ ZC[CR]
    if EPS >= 0: HASH ^= ZE[EPS & 7]
    EPS = (f + (16 if pc > 0 else -16)) if fl & DBL else -1
    if EPS >= 0: HASH ^= ZE[EPS & 7]
    STM = -STM; HASH ^= ZS
    return old
def unmake(m, old):
    global STM, CR, EPS, HASH
    f = m & 127; t = (m >> 7) & 127
    pc = B[t]; pr = (m >> 14) & 7; fl = m & (CAP | EP | CAS | DBL)
    STM = -STM; HASH ^= ZS
    if EPS >= 0: HASH ^= ZE[EPS & 7]
    EPS = old[2]
    if EPS >= 0: HASH ^= ZE[EPS & 7]
    HASH ^= ZC[CR] ^ ZC[old[1]]; CR = old[1]
    if fl & CAS:
        a, b = {6: (7, 5), 2: (0, 3), 118: (119, 117), 114: (112, 115)}[t]
        rp = 4 if t < 100 else -4
        B[b] = 0; B[a] = rp; HASH ^= Z[zi(rp)][b] ^ Z[zi(rp)][a]
    if pr: pc = 1 if pc > 0 else -1
    HASH ^= Z[zi(B[t])][t] ^ Z[zi(pc)][f]
    B[t] = 0; B[f] = pc
    if abs(pc) == 6: KSQ[0 if pc > 0 else 1] = f
    if old[0]:
        if fl & EP:
            B[old[3]] = old[0]; HASH ^= Z[zi(old[0])][old[3]]
        else:
            B[t] = old[0]; HASH ^= Z[zi(old[0])][t]
def leg():
    out = []
    for m in gen():
        u = make(m)
        if not atk(KSQ[0 if STM < 0 else 1], STM > 0): out.append(m)
        unmake(m, u)
    return out
def ev():
    sc = 0; np = 0; nb = [0, 0]; pw = [0] * 8; pb = [0] * 8
    wp = []; bp = []; rk = [0, 0]
    for s in S64:
        pc = B[s]
        if not pc: continue
        a = abs(pc); w = pc > 0; r = s >> 4; f = s & 7
        rr = r if w else 7 - r
        c = min(f, 7 - f) + min(rr, 7 - rr)
        if a == 1:
            v = 100 + PA[rr] + (PC[rr] if f in (3, 4) else 0)
            if w: pw[f] += 1; wp.append((f, r))
            else: pb[f] += 1; bp.append((f, r))
        elif a == 2: v = 320 + 6 * c - 20
        elif a == 3:
            v = 330 + 4 * c - 8; nb[0 if w else 1] += 1
        elif a == 4:
            v = 500 + (15 if rr == 6 else 0) + (5 if rr == 0 and f in (3, 4) else 0)
            rk[0 if w else 1] |= 1 << f
        elif a == 5: v = 900 + 2 * c - 6
        else: continue
        if a != 1: np += VAL[a]
        sc += v if w else -v
    ph = min(np, 6200)
    for i, w in enumerate((True, False)):
        s = KSQ[i]; r = s >> 4; f = s & 7
        rr = r if w else 7 - r
        c = min(f, 7 - f) + min(rr, 7 - rr)
        ko = KO[f] if rr == 0 else max(-50, -15 * rr)
        kv = (ko * ph + (8 * c - 24) * (6200 - ph)) // 6200
        sc += kv if w else -kv
    if nb[0] >= 2: sc += 30
    if nb[1] >= 2: sc -= 30
    for f in range(8):
        if pw[f] > 1: sc -= 12 * (pw[f] - 1)
        if pb[f] > 1: sc += 12 * (pb[f] - 1)
        lw = pw[f - 1] if f > 0 else 0; rw = pw[f + 1] if f < 7 else 0
        lb = pb[f - 1] if f > 0 else 0; rb = pb[f + 1] if f < 7 else 0
        if pw[f] and not lw and not rw: sc -= 8 * pw[f]
        if pb[f] and not lb and not rb: sc += 8 * pb[f]
    for f, r in wp:
        if not any(abs(x - f) <= 1 and y > r for x, y in bp): sc += 12 + 10 * r
    for f, r in bp:
        if not any(abs(x - f) <= 1 and y < r for x, y in wp): sc -= 12 + 10 * (7 - r)
    for i, w in enumerate((True, False)):
        for f in range(8):
            if rk[i] >> f & 1:
                if not pw[f] and not pb[f]: sc += 12 if w else -12
                elif not (pw[f] if w else pb[f]): sc += 6 if w else -6
    return sc if STM > 0 else -sc
def srt(ms, ply, tm):
    def k(m):
        s = 0
        if m == tm: return 1 << 30
        t = (m >> 7) & 127; v = B[t]
        if m & CAP:
            if m & EP: v = 1 if STM > 0 else -1
            s = 100000 + 10 * VAL[abs(v)] - VAL[abs(B[m & 127])] // 10
        if (m >> 14) & 7: s += 200000 + VAL[(m >> 14) & 7]
        elif m == KILL[ply][0]: s = 50000
        elif m == KILL[ply][1]: s = 40000
        else: s += HIST[0 if STM > 0 else 1][m & 127][t]
        return s
    return sorted(ms, key=k, reverse=True)
def qs(a, b, ply):
    global NODES
    NODES += 1
    if NODES >= LIMIT: raise Abort
    if ply >= 64: return ev()
    chk = atk(KSQ[0 if STM > 0 else 1], STM < 0)
    if not chk:
        st = ev()
        if st >= b: return st
        if st > a: a = st
        best = st
    else: best = -MATE - 1
    for m in srt(gen(True), ply, 0) if not chk else srt(gen(), ply, 0):
        u = make(m)
        if atk(KSQ[0 if STM < 0 else 1], STM > 0):
            unmake(m, u); continue
        s = -qs(-b, -a, ply + 1)
        unmake(m, u)
        if s > best: best = s
        if s > a: a = s
        if a >= b: return best
    if chk and best == -MATE - 1: return -MATE + ply
    return best
def sr(d, a, b, ply):
    global NODES
    if d <= 0: return qs(a, b, ply)
    NODES += 1
    if NODES >= LIMIT: raise Abort
    e = TT.get(HASH); tm = 0
    if e:
        tm = e[3]
        if e[0] >= d:
            if e[1] == 0: return e[2]
            if e[1] == 1 and e[2] >= b: return e[2]
            if e[1] == 2 and e[2] <= a: return e[2]
    a0 = a; best = -MATE - 1; bm = 0
    for m in srt(gen(), ply, tm):
        u = make(m)
        if atk(KSQ[0 if STM < 0 else 1], STM > 0):
            unmake(m, u); continue
        s = -sr(d - 1, -b, -a, ply + 1)
        unmake(m, u)
        if s > best: best = s; bm = m
        if s > a: a = s
        if a >= b:
            if not (m & CAP) and not ((m >> 14) & 7):
                if KILL[ply][0] != m:
                    KILL[ply][1] = KILL[ply][0]; KILL[ply][0] = m
                HIST[0 if STM > 0 else 1][m & 127][(m >> 7) & 127] += d * d
            break
    if best == -MATE - 1:
        return -MATE + ply if atk(KSQ[0 if STM > 0 else 1], STM < 0) else 0
    if len(TT) > 262144: TT.clear()
    TT[HASH] = (d, 2 if best <= a0 else 1 if best >= b else 0, best, bm)
    return best
def ch(f, lu):
    global NODES
    fen(f)
    ms = leg()
    by = {uci(m): m for m in ms}
    cd = [by[u] for u in lu if u in by]
    if not cd: return lu[0]
    if len(cd) == 1: return lu[0]
    NODES = 0; best = cd[0]; sc = {m: 0 for m in cd}; d = 1
    while True:
        try:
            s2 = []; al = -MATE - 1
            for m in sorted(cd, key=lambda m: -sc[m]):
                u = make(m)
                s = -sr(d - 1, -MATE - 1, -al, 1)
                unmake(m, u)
                s2.append((s, m))
                if s > al: al = s
            s2.sort(key=lambda x: -x[0])
            best = s2[0][1]; sc = {m: s for s, m in s2}
            if s2[0][0] >= MATE - 100: break
            d += 1
            if d > 32: break
        except Abort: break
    return uci(best)
def post(path, body):
    req = u.Request(ENV + path, data=json.dumps(body).encode(), headers={"content-type": "application/json"})
    try:
        with u.urlopen(req) as r: return json.load(r)
    except HTTPError as e: sys.exit(e.code)
while True:
    g = post("/game", {})
    if g["status"] == "done": break
    while g["status"] == "your_move":
        g = post("/move", {"game": g["game"], "move": ch(g["fen"], g["legal_moves"])})
