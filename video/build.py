"""Generates the CommerceGuard Ep1 HyperFrames projects from one scene list.

python build.py            -> ./ (YouTube 1920x1080 film)
python build.py reels      -> ../reels/part1..7 (1080x1920, each ends on a hook to the next part)
Inputs: ../recording (vo, words, cells, boxes.json, cells.json), assets/data.json. Numbers come from the notebook run.
"""
import json, re, shutil, sys
from html import escape
from pathlib import Path

HERE = Path(__file__).parent
REC = HERE.parent / "recording"
LEAD, TAIL = 0.35, 0.45
INK, AMB, RED, GRN, GROUND = "#F3F0E8", "#FFB224", "#FF5C4D", "#3CC6A4", "#141517"

SCENES = {s["id"]: s for s in json.loads((REC / "vo/scenes.json").read_text())}
OUTROS = {s["id"]: s for s in json.loads((REC / "vo/outros.json").read_text())}
BOXES = json.loads((REC / "boxes.json").read_text())
DATA = json.loads((HERE / "assets/data.json").read_text())
CELLRUN = {c["i"]: c for c in json.loads((REC / "cells.json").read_text())}


def words(sid):
    return json.loads((REC / f"words/{sid}.words.json").read_text())


def norm(t):
    return re.sub(r"[^a-z0-9.%]", "", t.lower())


def at(sid, token, nth=0, default=None):
    """Scene-local time (s) of the word containing `token` (nth match)."""
    tok, hits = norm(token), []
    for w in words(sid):
        if tok and tok in norm(w["text"]):
            hits.append(round(LEAD + w["start"], 2))
    if len(hits) > nth:
        return hits[nth]
    if default is not None:
        return default
    if hits:
        print(f"  ~ {sid}: '{token}' #{nth} missing, using last match"); return hits[-1]
    print(f"  ! {sid}: '{token}' not in transcript, placed mid-scene")
    return round(LEAD + (SCENES.get(sid) or OUTROS[sid])["dur"] * 0.5, 2)


HOLD = {"S24": 1.2, "S25": 0.8, "S28": 0.8, "S31": 1.5, "C03": 0.8, "C08": 1.0, "C06": 0.4}


def dur(sid):
    s = SCENES.get(sid) or OUTROS[sid]
    return round(LEAD + s["dur"] + TAIL + HOLD.get(sid, 0), 2)


# ---------------------------------------------------------------- scene building blocks
class Scene:
    def __init__(self, sid, W, H):
        self.sid, self.W, self.H = sid, W, H
        self.P = H > W
        self.u = min(W, H) / 1080
        self.html, self.css, self.js, self.n = [], [], [], 0

    def id(self, name):
        return f"{self.sid.lower()}-{name}"

    def px(self, v):
        return f"{round(v * self.u)}px"

    def add(self, html, css="", js=""):
        self.html.append(html); self.css.append(css); self.js.append(js)

    def appear(self, sel, t, y=30, d=0.5):
        if t <= 0.05:
            return  # on screen from frame 0
        self.js.append(f'tl.fromTo("#{sel}",{{opacity:0,y:{y}}},{{opacity:1,y:0,duration:{d},ease:"power3.out"}},{t});')

    def render(self):
        W, H = self.W, self.H
        grid = "linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px)"
        return f"""<template>
<style>
#root{{position:absolute;inset:0;overflow:hidden;background:{GROUND};background-image:{grid};background-size:{self.px(120)} {self.px(120)};
 font-family:Inter,sans-serif;color:{INK};}}
#root .mono{{font-family:'JetBrains Mono',monospace;}}
{''.join(self.css)}
</style>
<div id="root" data-composition-id="{self.sid.lower()}" data-width="{W}" data-height="{H}">
{''.join(self.html)}
</div>
<script>
const tl = gsap.timeline({{paused:true}});
{''.join(self.js)}
window.__timelines["{self.sid.lower()}"] = tl;
</script>
</template>"""


def kinetic(sc, lines, top=None, size=92, align="left"):
    """lines: [(text, anchor_time, color)] stacked, each lands on its word."""
    W, H, u = sc.W, sc.H, sc.u
    fs = size * (0.92 if sc.P else 1)
    left = W * (0.08 if not sc.P else 0.07)
    y = top if top is not None else H * (0.30 if not sc.P else 0.30)
    for i, (text, t, color) in enumerate(lines):
        el = sc.id(f"k{i}")
        big = fs if i == 0 or color != INK else fs * 0.8
        sc.add(f'<div id="{el}" class="kl">{text}</div>',
               f"#{el}{{position:absolute;left:{left}px;top:{y}px;width:{W - 2 * left}px;font-weight:800;font-size:{big * u}px;"
               f"line-height:1.05;letter-spacing:-0.03em;color:{color};text-align:{align};}}")
        sc.appear(el, t)
        y += big * u * (1.18 * (2 if len(text) > (18 if sc.P else 34) else 1)) + 18 * u


def label(sc, name, text, x, y, size=34, color=INK, t=0, weight=700, mono=False, anchor="left", w=None):
    el = sc.id(name)
    tx = {"left": "0", "center": "-50%", "right": "-100%"}[anchor]
    sc.add(f'<div id="{el}"><div style="transform:translateX({tx})">{text}</div></div>',
           f"#{el}{{position:absolute;left:{x}px;top:{y}px;font-size:{size * sc.u}px;font-weight:{weight};color:{color};"
           f"{'font-family:JetBrains Mono,monospace;' if mono else ''}{f'width:{w}px;' if w else 'white-space:nowrap;'}line-height:1.15;}}")
    sc.appear(el, t, y=20)
    return el


def chapter(sc, text, t=0.0):
    """Small chapter tag in the top-left, e.g. 'PHASE 3 · TARGET'."""
    x, y = (sc.W * 0.08, sc.H * 0.08) if not sc.P else (sc.W * 0.07, sc.H * 0.115)
    el = label(sc, "chap", text, x, y, size=32, color=AMB, t=t, weight=800, w=(sc.W * 0.86) if sc.P else None)
    sc.css.append(f"#{el}{{z-index:10;}}#{el}>div{{background:rgba(20,21,23,.85);padding:{6 * sc.u}px {14 * sc.u}px;border-radius:{8 * sc.u}px;margin-left:{-14 * sc.u}px;}}")


def capture(sc, segs):
    """segs: [{cell, start, end, hl:[(string, time)], zoom}] real Jupyter cell captures with a camera and amber marker boxes."""
    W, H, P = sc.W, sc.H, sc.P
    for k, seg in enumerate(segs):
        c = seg["cell"]
        img = f"assets/cells/cell_{c:02d}.png"
        iw, ih = 2500, seg["h"]
        Dw = W * (0.80 if not P else 0.96)
        f = Dw / iw
        Dh = ih * f
        x0 = (W - Dw) / 2
        y0 = max(H * (0.17 if not P else 0.22), (H - Dh) / 2) if Dh < H * 0.72 else H * (0.17 if not P else 0.22)
        cam, sheet = sc.id(f"cam{k}"), sc.id(f"sheet{k}")
        sc.add(f'<div id="{cam}"><img id="{sheet}" src="{img}"/>'
               + "".join(f'<div id="{sc.id(f"hl{k}_{j}")}" class="hl"></div>' for j in range(len(seg["hl"]))) + "</div>",
               f"#{cam}{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;}}"
               f"#{sheet}{{position:absolute;left:{x0}px;top:{y0}px;width:{Dw}px;border-radius:{14 * sc.u}px;"
               f"box-shadow:0 {40 * sc.u}px {90 * sc.u}px rgba(0,0,0,.55);background:#fff;}}"
               f"#root .hl{{position:absolute;border:{5 * sc.u}px solid {AMB};border-radius:{8 * sc.u}px;opacity:0;"
               f"box-shadow:0 0 0 {4000 * sc.u}px rgba(20,21,23,.5);}}")
        s0, s1 = seg["start"], seg["end"]
        sc.js.append(f'tl.fromTo("#{cam}",{{opacity:0,y:{40 * sc.u}}},{{opacity:1,y:0,duration:.5,ease:"power3.out"}},{s0});')
        if k < len(segs) - 1:
            sc.js.append(f'tl.to("#{cam}",{{opacity:0,duration:.3,ease:"power2.in"}},{s1 - 0.3});')
        sc.js.append(f'tl.set("#{cam}",{{transformOrigin:"0 0"}},0);')
        prev = None
        for j, (s, t) in enumerate(seg["hl"]):
            b = BOXES.get(str(c), {}).get(s)
            if not b:
                print(f"  ! no box for cell {c} '{s}'"); continue
            pad = 10
            bx, by, bw, bh = x0 + (b[0] - pad) * f, y0 + (b[1] - pad) * f, (b[2] + 2 * pad) * f, (b[3] + 2 * pad) * f
            hl = sc.id(f"hl{k}_{j}")
            sc.css.append(f"#{hl}{{left:{bx}px;top:{by}px;width:{bw}px;height:{bh}px;}}")
            z = min(seg.get("zoom", 2.4), (W * 0.62) / bw, (H * 0.5) / bh)
            z = max(z, 1.0)
            cx, cy = bx + bw / 2, by + bh / 2
            tx, ty = W / 2 - z * cx, H * (0.48 if not P else 0.45) - z * cy
            sc.js.append(f'tl.to("#{cam}",{{x:{tx:.1f},y:{ty:.1f},scale:{z:.3f},duration:.9,ease:"sine.inOut"}},{max(s0, t - 0.6):.2f});')
            sc.js.append(f'tl.fromTo("#{hl}",{{opacity:0,scaleX:.6}},{{opacity:1,scaleX:1,duration:.3,ease:"power3.out"}},{t + 0.25:.2f});')
            if prev:
                sc.js.append(f'tl.to("#{prev}",{{opacity:0,duration:.2}},{t:.2f});')
            prev = hl


def bars(sc, items, top, unit="", fmt="{:.3f}", vmax=None, height=96, title=None, title_t=0):
    """Horizontal bars with direct labels. items: [(label, value, color, t)]."""
    W, H, u, P = sc.W, sc.H, sc.u, sc.P
    left = W * (0.08 if not P else 0.07)
    lab_w = (W * 0.30) if not P else W - 2 * left
    bar_x = left + lab_w + 24 * u if not P else left
    bar_w = W - bar_x - left - 220 * u
    vmax = vmax or max(v for _, v, _, _ in items) * 1.05
    y = top
    if title:
        label(sc, "btitle", title, left, y - 100 * u, size=52, t=title_t, weight=800)
    for i, (lab, v, color, t) in enumerate(items):
        bid, lid, vid = sc.id(f"b{i}"), sc.id(f"bl{i}"), sc.id(f"bv{i}")
        ly = y if not P else y - 0
        sc.add(f'<div id="{lid}">{lab}</div><div id="{bid}"></div><div id="{vid}" class="mono">{fmt.format(v)}{unit}</div>',
               f"#{lid}{{position:absolute;left:{left}px;top:{ly}px;width:{lab_w}px;font-size:{44 * u}px;font-weight:700;line-height:{(height if not P else 56) * u}px;}}"
               f"#{bid}{{position:absolute;left:{bar_x}px;top:{y + (64 * u if P else 0)}px;height:{height * u}px;width:{max(6, bar_w * v / vmax)}px;"
               f"background:{color};border-radius:{6 * u}px;transform-origin:left center;}}"
               f"#{vid}{{position:absolute;left:{bar_x + max(6, bar_w * v / vmax) + 20 * u}px;top:{y + (64 * u if P else 0)}px;"
               f"font-size:{56 * u}px;font-weight:700;line-height:{height * u}px;color:{color};}}")
        sc.appear(lid, t, y=10)
        sc.js.append(f'tl.fromTo("#{bid}",{{scaleX:0}},{{scaleX:1,duration:.7,ease:"power3.out"}},{t});')
        sc.appear(vid, t + 0.45, y=10, d=0.3)
        y += (height + (40 if not P else 100)) * u
    return y


def image(sc, name, src, x, y, w, t=0.0, shadow=True):
    el = sc.id(name)
    sc.add(f'<img id="{el}" src="{src}"/>',
           f"#{el}{{position:absolute;left:{x}px;top:{y}px;width:{w}px;border-radius:{12 * sc.u}px;"
           f"{'box-shadow:0 30px 80px rgba(0,0,0,.5);' if shadow else ''}background:#fff;}}")
    sc.appear(el, t, y=30)
    return el


# ---------------------------------------------------------------- typed code (real notebook code, real output)
CODES = json.loads((HERE / "codes.json").read_text())
KW = set("def return for in if else import from as not and or None True False lambda assert print".split())
SYN = {"kw": "#8FB8FF", "str": "#A8D5A2", "num": "#F3C77A", "com": "#7C7A75", "fn": "#F3F0E8", "op": "#B8B5AE", "id": "#D9D6CE"}


def highlight_py(line):
    out = []
    pat = re.compile(r'(?P<com>#.*)|(?P<str>[fr]?"[^"]*"?|[fr]?\'[^\']*\'?)|(?P<num>\b\d[\d_.]*\b)|(?P<word>[A-Za-z_]\w*)|(?P<sp>\s+)|(?P<op>.)')
    for m in pat.finditer(line):
        k, txt = m.lastgroup, m.group()
        if k == "word":
            k = "kw" if txt in KW else ("fn" if line[m.end():m.end() + 1] == "(" else "id")
        out.append(txt if k == "sp" else f'<span style="color:{SYN[k]}">{escape(txt)}</span>')
    return "".join(out)


def code_scene(sc, key):
    spec = CODES[key]; sid = sc.sid
    W, H, u, P = sc.W, sc.H, sc.u, sc.P
    L = W * (0.08 if not P else 0.035)
    pad = 24 * u
    n, no = len(spec["code"]), len(spec["out"])
    maxlen = max(len(l) for l in spec["code"] + spec["out"])
    fs_w = (W - 2 * L - 2 * pad) / (0.6 * maxlen)
    avail = H * (0.80 if not P else 0.72) - H * 0.12 - (60 if not P else 100) * u - 4 * pad - 22 * u
    fs_h = avail / (1.42 * n + 1.4 * no)
    fs = max(28 * u, min(36 * u, fs_w, fs_h))
    lh = fs * 1.42
    block = (60 if not P else 100) * u + n * lh + 4 * pad + 22 * u + no * fs * 1.4
    top = H * 0.12 if not P else max(H * 0.15, (H * 0.76 - block) / 2 + H * 0.06)
    hdr = sc.id("hdr")
    sc.add(f'<div id="{hdr}" class="mono">cell {spec["cell"]} · {escape(spec["title"])}{" · excerpt" if spec.get("excerpt") else ""}</div>',
           f"#{hdr}{{position:absolute;left:{L}px;top:{top}px;width:{W - 2 * L}px;font-size:{30 * u}px;font-weight:700;color:{AMB};}}")
    panel_top = top + (60 if not P else 100) * u
    panel = sc.id("code")
    sc.add(f'<div id="{panel}"></div>', f"#{panel}{{position:absolute;left:{L}px;width:{W - 2 * L}px;top:{panel_top}px;height:{n * lh + 2 * pad}px;"
           f"background:#0D0E10;border:{2 * u}px solid #2A2B2E;border-radius:{14 * u}px;box-shadow:0 30px 70px rgba(0,0,0,.5);}}")
    chars = sum(max(1, len(l)) for l in spec["code"])
    d = dur(sid)
    t0, rate = 0.3, max(40.0, chars / (d * 0.45))
    t = t0
    for i, line in enumerate(spec["code"]):
        el = sc.id(f"l{i}")
        sc.add(f'<div id="{el}" class="cl">{highlight_py(line)}</div>', f"#{el}{{top:{panel_top + pad + i * lh}px;}}")
        k = max(1, len(line)); dd = k / rate
        sc.js.append(f'tl.fromTo("#{el}",{{clipPath:"inset(0 100% 0 0)"}},{{clipPath:"inset(0 0% 0 0)",duration:{dd:.2f},ease:"steps({k})"}},{t:.2f});')
        t += dd + 0.04
    typed_end = t
    sc.css.append(f"#root .cl{{position:absolute;left:{L + pad}px;font-family:'JetBrains Mono',monospace;font-size:{fs}px;line-height:{lh}px;white-space:pre;"
                  f"color:{SYN['id']};clip-path:inset(0 100% 0 0);}}")
    for j, (a, b, tok) in enumerate(spec["hl"]):
        hl = sc.id(f"hl{j}")
        ta = max(at(sid, tok), min(typed_end, d - 2.5))
        sc.add(f'<div id="{hl}"></div>', f"#{hl}{{position:absolute;left:{L + 6 * u}px;width:{W - 2 * L - 12 * u}px;top:{panel_top + pad + a * lh - 2 * u}px;"
               f"height:{(b - a + 1) * lh + 4 * u}px;background:rgba(255,178,36,.13);border-left:{6 * u}px solid {AMB};border-radius:{4 * u}px;opacity:0;}}")
        sc.js.append(f'tl.fromTo("#{hl}",{{opacity:0}},{{opacity:1,duration:.25}},{ta:.2f});')
        if j + 1 < len(spec["hl"]):
            nxt = max(at(sid, spec["hl"][j + 1][2]), min(typed_end, d - 2.5))
            if nxt > ta + 0.6:
                sc.js.append(f'tl.to("#{hl}",{{opacity:0,duration:.2}},{nxt:.2f});')
    out_top = panel_top + n * lh + 2 * pad + 22 * u
    to = min(max(at(sid, spec["out_t"]), typed_end + 0.2), d - 2.4)
    olh = fs * 1.4
    box = sc.id("out")
    sc.add(f'<div id="{box}"></div>', f"#{box}{{position:absolute;left:{L}px;width:{W - 2 * L}px;top:{out_top}px;height:{len(spec['out']) * olh + 2 * pad}px;"
           f"background:#F6F4EE;border-radius:{14 * u}px;}}")
    sc.js.append(f'tl.fromTo("#{box}",{{opacity:0,y:{20 * u}}},{{opacity:1,y:0,duration:.35,ease:"power3.out"}},{to:.2f});')
    for i, line in enumerate(spec["out"]):
        el = sc.id(f"o{i}")
        txt = escape(line)
        if spec.get("out_hl") and spec["out_hl"] in line:
            txt = txt.replace(escape(spec["out_hl"]), f'<span class="ohl">{escape(spec["out_hl"])}</span>', 1)
        sc.add(f'<div id="{el}" class="ol">{txt}</div>', f"#{el}{{top:{out_top + pad + i * olh}px;}}")
        sc.js.append(f'tl.fromTo("#{el}",{{opacity:0}},{{opacity:1,duration:.15}},{to + 0.25 + i * 0.12:.2f});')
    sc.css.append(f"#root .ol{{position:absolute;left:{L + pad}px;font-family:'JetBrains Mono',monospace;font-size:{fs}px;line-height:{olh}px;white-space:pre;color:#1B1C1F;opacity:0;}}"
                  f"#root .ohl{{outline:{4 * u}px solid {AMB};outline-offset:{3 * u}px;border-radius:{3 * u}px;background:rgba(255,178,36,.3);}}")
    TYPING[(sid, W)] = (t0, typed_end)


TYPING = {}


# ---------------------------------------------------------------- the scenes
def S(sid, W, H):
    sc = Scene(sid, W, H); u, P = sc.u, sc.P
    L = W * (0.08 if not P else 0.07)
    if sid == "S01":
        kinetic(sc, [("What if an online store", 0, INK), ("could see a loss coming", at(sid, "loss"), INK),
                     ("before it happens?", at(sid, "before"), AMB)], size=104)
    elif sid == "S02":
        # parcels stream past; three go wrong as the voice names them
        n = 7
        for i in range(n):
            el = sc.id(f"p{i}")
            x = L + i * ((W - 2 * L) / n) if not P else L + (i % 3) * (W - 2 * L) / 3
            y = H * 0.40 if not P else H * 0.30 + (i // 3) * 260 * u
            sc.add(f'<div id="{el}" class="parcel"><div class="tape"></div></div>',
                   f"#{el}{{position:absolute;left:{x}px;top:{y}px;}}")
            sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,y:{-60 * u}}},{{opacity:1,y:0,duration:.45,ease:"power3.out"}},{0.3 + i * 0.25:.2f});')
        sc.css.append(f"#root .parcel{{width:{170 * u}px;height:{150 * u}px;background:#C49A6C;border-radius:{10 * u}px;"
                      f"box-shadow:0 {20 * u}px {40 * u}px rgba(0,0,0,.45);}}#root .tape{{position:absolute;left:44%;width:12%;top:0;bottom:0;background:#E3C79F;}}")
        tags = [("Rejected at the door", "reject", 1), ("Cancelled again and again", "cancelled", 3), ("Refund eats the profit", "refunds", 5)]
        for j, (txt, tok, pi) in enumerate(tags):
            t = at(sid, tok)
            x = L + pi * ((W - 2 * L) / n) if not P else L + (pi % 3) * (W - 2 * L) / 3
            y = H * 0.40 if not P else H * 0.30 + (pi // 3) * 260 * u
            sc.js.append(f'tl.to("#{sc.id(f"p{pi}")}",{{backgroundColor:"{RED}",duration:.3}},{t});')
            label(sc, f"t{j}", txt, x + 85 * u, y + (180 if j % 2 == 0 else -70) * u, size=30, color=RED, t=t, anchor="center")
        label(sc, "every", "Thousands of orders, every day", L, H * (0.18 if not P else 0.16), size=56, t=at(sid, "every"), weight=800)
    elif sid == "S03":
        kinetic(sc, [("Most businesses find out", 0.3, INK), ("after the damage is done.", at(sid, "after"), RED),
                     ("What if we saw the warning signs earlier?", at(sid, "warning"), AMB)], size=86)
    elif sid == "S04":
        el = sc.id("logo")
        sc.add(f'<div id="{el}"><span>Commerce</span><span style="color:{AMB}">Guard</span></div>',
               f"#{el}{{position:absolute;left:0;right:0;top:{H * (0.30 if not P else 0.28)}px;text-align:center;font-weight:800;"
               f"font-size:{(150 if not P else 118) * u}px;letter-spacing:-0.04em;clip-path:inset(0 100% 0 0);}}")
        sc.js.append(f'tl.fromTo("#{el}",{{clipPath:"inset(0 100% 0 0)"}},{{clipPath:"inset(0 0% 0 0)",duration:1.0,ease:"power3.inOut"}},{at(sid, "commerceguard", default=at(sid, "commerce", default=0.6))});')
        items = [("✕  No ready-made AI", "no", 0, RED), ("✕  No large language models", "language", 0, RED),
                 ("✓  Real data", "real", 0, GRN), ("✓  Honest testing", "honest", 0, GRN), ("✓  Models that explain themselves", "explain", 0, GRN)]
        y = H * (0.55 if not P else 0.46)
        for i, (txt, tok, n_, col) in enumerate(items):
            label(sc, f"r{i}", txt, W / 2 if not P else L, y, size=40, color=col, t=at(sid, tok, n_), anchor="center" if not P else "left")
            y += 62 * u
    elif sid == "S05":
        mods = [("Delivery failure", "delivery"), ("Suspicious orders", "suspicious"), ("Refund abuse", "refund"), ("Customer behavior", "behavior")]
        y = H * (0.22 if not P else 0.2)
        for i, (m, tok) in enumerate(mods):
            label(sc, f"m{i}", m, L, y, size=46, color="#8B8A86", t=at(sid, tok), weight=700)
            y += 76 * u
        q = sc.id("q")
        sc.add(f'<div id="{q}">When a customer clicks <span style="color:{AMB}">Buy</span>,<br>will the delivery promise be broken?</div>',
               f"#{q}{{position:absolute;left:{L}px;width:{W - 2 * L}px;top:{y + 60 * u}px;font-weight:800;font-size:{(70 if not P else 64) * u}px;line-height:1.1;letter-spacing:-0.02em;}}")
        sc.appear(q, at(sid, "clicks"))
    elif sid == "S06":
        chapter(sc, "THE DATA · OLIST")
        tables = ["orders", "order items", "payments", "customers", "sellers", "products", "reviews", "locations", "categories"]
        cx, cy = W / 2, H * (0.52 if not P else 0.45)
        rad = (min(W, H) * 0.36) if not P else W * 0.40
        import math
        hub = sc.id("hub")
        sc.add(f'<div id="{hub}" class="mono">100,000 orders</div>',
               f"#{hub}{{position:absolute;left:{cx}px;top:{cy}px;transform:translate(-50%,-50%);font-size:{50 * u}px;font-weight:700;color:{AMB};}}")
        sc.js.append(f'tl.fromTo("#{hub}",{{opacity:0}},{{opacity:1,duration:.4}},{at(sid, "100")});')
        svg = [f'<svg id="{sc.id("lines")}" width="{W}" height="{H}" style="position:absolute;left:0;top:0">']
        for i, tname in enumerate(tables):
            a = -math.pi / 2 + i * 2 * math.pi / len(tables)
            x, y = cx + rad * math.cos(a) * (1.35 if not P else 1), cy + rad * math.sin(a) * (0.82 if not P else 1.3)
            t = at(sid, "tables") + 0.15 * i if i < 1 else at(sid, tname.split()[-1].rstrip("s"), default=at(sid, "tables") + 0.3 * i)
            svg.append(f'<line id="{sc.id(f"ln{i}")}" x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="rgba(243,240,232,.25)" stroke-width="{2 * u}"/>')
            label(sc, f"tb{i}", tname, x, y - 22 * u, size=34, t=t, anchor="center", mono=True)
            sc.js.append(f'tl.fromTo("#{sc.id(f"ln{i}")}",{{opacity:0}},{{opacity:1,duration:.3}},{t});')
        sc.add("".join(svg) + "</svg>")
    elif sid in ("S07", "S15") or sid.startswith("C"):
        code_scene(sc, sid)
    elif sid == "S08":
        chapter(sc, "PHASE 1 · FIRST SURPRISE")
        capture(sc, [{"cell": 6, "h": 380, "start": 0.2, "end": dur(sid), "hl": [("3.1%", at(sid, "3.1"))], "zoom": 2.6}])
    elif sid == "S09":
        chapter(sc, "PHASE 2 · CLEANING")
        t_keep = at(sid, "kept")
        capture(sc, [{"cell": 8, "h": 1632, "start": 0.2, "end": t_keep, "hl": [("2016-09", at(sid, "2016")), ("2018-09", at(sid, "last"))], "zoom": 1.8},
                     {"cell": 9, "h": 334, "start": t_keep, "end": dur(sid), "hl": [("89,852", at(sid, "89"))], "zoom": 2.4}])
        lk = label(sc, "lock", "🔒 July 2018 locked away", W - L, H * (0.08 if not P else 0.16), size=36, color=AMB, t=at(sid, "locked"), anchor="right")
        sc.css.append(f"#{lk}{{z-index:10;}}")
    elif sid == "S10":
        chapter(sc, "PHASE 3 · THE TARGET")
        y = bars(sc, [("Promised (median)", 24, "#8B8A86", at(sid, "promise", 1)), ("Actual (median)", 11, GRN, at(sid, "actual", 1))],
                 top=H * (0.30 if not P else 0.3), unit=" days", fmt="{:.0f}", vmax=28)
        label(sc, "early", "13 days early…", L, y + 10 * u, size=56, color=GRN, t=at(sid, "13"), weight=800)
        label(sc, "late", "…and still 6.8% late", L, y + 90 * u, size=56, color=RED, t=at(sid, "still"), weight=800)
    elif sid == "S11":
        kinetic(sc, [("The problem isn't speed.", at(sid, "problem"), INK), ("It's knowing which orders", at(sid, "knowing"), INK),
                     ("will go wrong.", at(sid, "wrong"), AMB)], size=96)
    elif sid == "S12":
        chapter(sc, "PHASE 4 · EXPLORE")
        capture(sc, [{"cell": 15, "h": 1558, "start": 0.2, "end": dur(sid), "hl": [("0.180", at(sid, "18")), ("0.144", at(sid, "14"))], "zoom": 2.4}])
    elif sid == "S13":
        chapter(sc, "PHASE 5 · FEATURES (LIVE RUN · 0.4×)")
        c = CELLRUN[17]
        v = sc.id("live")
        vw = W * (0.62 if not P else 1.3)
        sc.add(f'<video id="{v}" class="clip" src="assets/live_run.mp4" muted playsinline data-start="0.2" data-duration="{dur(sid) - 0.2:.2f}" '
               f'data-media-start="{CELLRUN[16]["start"] - 0.2:.2f}" data-hf-media-start-basis="local" data-playback-rate="0.4" data-track-index="1"></video>',
               f"#{v}{{position:absolute;left:{L if not P else -W * 0.1}px;top:{H * (0.16 if not P else 0.18)}px;width:{vw}px;"
               f"border-radius:{14 * u}px;box-shadow:0 40px 90px rgba(0,0,0,.55);}}")
        feats = [("order time", "time"), ("items · price · freight", "freight"), ("weight", "weight"), ("payment type", "payment"),
                 ("customer state → seller state", "seller"), ("distance from postcodes", "distance")]
        y = H * (0.20 if not P else 0.66)
        for i, (f_, tok) in enumerate(feats):
            if P:
                el = label(sc, f"f{i}", "+ " + f_, L, y, size=40, color=AMB if i == 5 else INK, t=at(sid, tok), mono=True, w=W - 2 * L)
                if i + 1 < len(feats):
                    sc.js.append(f'tl.to("#{el}",{{opacity:0,duration:.15}},{at(sid, feats[i + 1][1]) - 0.05:.2f});')
                continue
            label(sc, f"f{i}", "+ " + f_, (L + vw + 50 * u) if not P else L, y + i * (92 if not P else 58) * u, size=36, w=(W - vw - 2 * L - 50 * u) if not P else None,
                  color=AMB if i == 5 else INK, t=at(sid, tok), mono=True)
    elif sid == "S14":
        chapter(sc, "NO PEEKING AT THE FUTURE")
        ax_y, x0, x1 = H * 0.55, L, W - L
        now = x0 + (x1 - x0) * 0.62
        sc.add(f'<div id="{sc.id("axis")}"></div>', f'#{sc.id("axis")}{{position:absolute;left:{x0}px;width:{x1 - x0}px;top:{ax_y}px;height:{3 * u}px;background:rgba(243,240,232,.4);}}')
        sc.appear(sc.id("axis"), 0.3, y=0)
        import random
        rnd = random.Random(7)
        for i in range(14):
            x = x0 + (x1 - x0) * (0.04 + i * 0.068)
            late = rnd.random() < 0.25
            el = sc.id(f"d{i}")
            sc.add(f'<div id="{el}" class="dot"></div>', f"#{el}{{left:{x}px;top:{ax_y - 13 * u}px;background:{RED if late else INK};}}")
            sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,scale:0}},{{opacity:1,scale:1,duration:.25}},{0.6 + i * 0.08:.2f});')
            if x > now:
                sc.js.append(f'tl.to("#{el}",{{opacity:.15,duration:.3}},{at(sid, "nothing", default=at(sid, "future", default=8))});')
        sc.css.append(f"#root .dot{{position:absolute;width:{28 * u}px;height:{28 * u}px;border-radius:50%;}}")
        nl = sc.id("now")
        sc.add(f'<div id="{nl}"></div>', f"#{nl}{{position:absolute;left:{now}px;top:{ax_y - 140 * u}px;width:{4 * u}px;height:{280 * u}px;background:{AMB};}}")
        sc.appear(nl, at(sid, "placed"), y=0)
        label(sc, "nowl", "order placed", now, ax_y - 200 * u, size=36, color=AMB, t=at(sid, "placed"), anchor="center", mono=True)
        label(sc, "past", "counted: finished before", (x0 + now) / 2, ax_y + 60 * u, size=34, color=GRN, t=at(sid, "already"), anchor="center")
        label(sc, "fut", "ignored: future", (now + x1) / 2, ax_y + 60 * u, size=34, color="#8B8A86", t=at(sid, "nothing", default=at(sid, "future", default=8)), anchor="center")
        label(sc, "ttl", "Seller's past late rate", L, H * (0.22 if not P else 0.22), size=60, t=at(sid, "seller"), weight=800)
    elif sid == "S16":
        chapter(sc, "PHASE 6 · SPLIT BY TIME")
        x0, x1, y = L, W - L, H * (0.42 if not P else 0.40)
        segs = [("TRAIN 70%", 0.70, "#5B5A57", "70", "Jan 2017 → Mar 2018"), ("VAL 15%", 0.15, "#8B8A86", "validate", "Mar → May 2018"),
                ("TEST 15%", 0.15, AMB, "test", "May → Jun 2018")]
        x = x0
        total = (x1 - x0) * 0.86
        for i, (name, frac, col, tok, dates) in enumerate(segs):
            w = total * frac
            el = sc.id(f"s{i}")
            sc.add(f'<div id="{el}"><b>{name.split()[0] if P and i else name}</b></div>', f"#{el}{{position:absolute;left:{x}px;top:{y}px;width:{w - 6 * u}px;height:{120 * u}px;background:{col};"
                   f"border-radius:{8 * u}px;color:{"#141517" if col == AMB else INK};font-size:{(34 if not P else 30) * u}px;display:flex;align-items:center;justify-content:center;transform-origin:left;}}")
            sc.js.append(f'tl.fromTo("#{el}",{{clipPath:"inset(0 100% 0 0)"}},{{clipPath:"inset(0 0% 0 0)",duration:.6,ease:"power3.out"}},{at(sid, tok):.2f});')
            label(sc, f"dt{i}", dates, x + w / 2, y + 140 * u + (i % 2) * 48 * u, size=30, color="#B8B5AE", t=at(sid, tok) + 0.3, anchor="center", mono=True)
            x += w
        jl = sc.id("jul")
        sc.add(f'<div id="{jl}">🔒</div>', f"#{jl}{{position:absolute;left:{x + 10 * u}px;top:{y}px;width:{total * 0.14}px;height:{120 * u}px;border:{3 * u}px dashed {AMB};"
               f"border-radius:{8 * u}px;font-size:{50 * u}px;display:flex;align-items:center;justify-content:center;}}")
        sc.appear(jl, at(sid, "split") + 0.3, y=0)
        label(sc, "jl2", "July 2018", x + total * 0.07 + 10 * u, y - 52 * u, size=30, color=AMB, t=at(sid, "split") + 0.3, anchor="center", mono=True)
        label(sc, "q", "Predict the future from the past.", L, H * (0.72 if not P else 0.66), size=58, t=at(sid, "future"), weight=800)
    elif sid == "S17":
        chapter(sc, "PHASE 7–8 · MODELS (VALIDATION)")
        y = bars(sc, [("Random guess", 0.097, "#8B8A86", at(sid, "random")), ("Logistic Regression", 0.220, INK, at(sid, "logistic")),
                      ("LightGBM", 0.299, AMB, at(sid, "gbm"))], top=H * (0.3 if not P else 0.3), vmax=0.34, title="PR-AUC (higher is better)", title_t=at(sid, "precision"))
        label(sc, "top", "Top 10% riskiest orders → 35% of all late ones", L, y + 20 * u, size=40, color=AMB, t=at(sid, "35"), weight=800, w=W - 2 * L)
    elif sid == "S18":
        el = sc.id("lock")
        sc.add(f'<div id="{el}">🔒</div>', f"#{el}{{position:absolute;left:0;right:0;top:{H * 0.28}px;text-align:center;font-size:{180 * u}px;}}")
        sc.appear(el, 0.3)
        sc.js.append(f'tl.to("#{el}",{{rotate:-12,scale:1.1,duration:.3,ease:"power2.out"}},{at(sid, "opened")});')
        sc.js.append(f'tl.call(()=>{{}},[],{at(sid, "opened")});')
        label(sc, "cal", "Scores calibrated on validation", W / 2, H * (0.58 if not P else 0.52), size=44, t=at(sid, "calibrated"), anchor="center")
        label(sc, "once", "TEST SET · OPENED ONCE", W / 2, H * (0.68 if not P else 0.6), size=70, color=AMB, t=at(sid, "once"), anchor="center", weight=800)
    elif sid == "S19":
        chapter(sc, "PHASE 10 · THE TEST")
        y = bars(sc, [("LightGBM · validation", 0.299, "#8B8A86", 0.4), ("LightGBM · test", 0.102, RED, at(sid, "scored")),
                      ("Random · test", 0.040, "#8B8A86", at(sid, "random"))], top=H * (0.3 if not P else 0.28), vmax=0.34, title="PR-AUC", title_t=0.3)
        label(sc, "x", "≈ 2.5× better than guessing", L, y + 20 * u, size=54, color=AMB, t=at(sid, "two"), weight=800)
    elif sid == "S20":
        chapter(sc, "PHASE 11 · REVIEW BANDS (TEST)")
        y = bars(sc, [("Low risk", 3.3, GRN, at(sid, "low")), ("Moderate", 11.3, AMB, at(sid, "moderate")), ("High", 20.0, RED, at(sid, "high"))],
                 top=H * (0.3 if not P else 0.28), unit="%", fmt="{:.1f}", vmax=23, title="Actually late, by band", title_t=at(sid, "turning"))
        label(sc, "list", "A list a support team can work through.", L, y + 20 * u, size=44, t=at(sid, "list"), weight=800, w=W - 2 * L)
    elif sid == "S21":
        chapter(sc, "PHASE 12 · EXPLAIN (SHAP)")
        w = W * (0.58 if not P else 0.94)
        x, y = (W - w) / 2, H * (0.16 if not P else 0.24)
        image(sc, "shap", "assets/shap_importance.png", x, y, w, t=at(sid, "shap"))
        f = w / 1600
        rows = [("month", 158, "month"), ("customer_state", 238, "state"), ("promised_days", 318, "promised"), ("seller_late_rate", 398, "seller")]
        for i, (_, ry, tok) in enumerate(rows):
            el = sc.id(f"r{i}")
            sc.add(f'<div id="{el}" class="hl2"></div>', f"#{el}{{left:{x + 20 * f}px;top:{y + (ry - 34) * f}px;width:{1520 * f}px;height:{68 * f}px;}}")
            sc.js.append(f'tl.fromTo("#{el}",{{opacity:0}},{{opacity:1,duration:.25}},{at(sid, tok):.2f});')
        sc.css.append(f"#root .hl2{{position:absolute;border:{4 * u}px solid {AMB};border-radius:{8 * u}px;opacity:0;}}")
    elif sid == "S22":
        kinetic(sc, [("The #1 factor:", 0.3, INK), ("the calendar month.", at(sid, "calendar"), AMB),
                     ("It partly memorised last year's bad months.", at(sid, "memorised", default=at(sid, "memorized", default=4)), RED)], size=90)
    elif sid == "S23":
        chapter(sc, "PHASE 13 · A BETTER PROMISE?")
        kinetic(sc, [("Don't just flag risk.", at(sid, "flagging"), INK), ("Promise a better date.", at(sid, "promise"), AMB)], top=H * 0.25, size=88)
        label(sc, "how", "quantile regression on delivery days · level chosen on validation", L, H * (0.62 if not P else 0.58), size=34,
              color="#B8B5AE", t=at(sid, "trained"), mono=True, w=W - 2 * L)
    elif sid == "S24":
        chapter(sc, "EXPERIMENT 1 · TEST MONTHS")
        y = bars(sc, [("Olist promise", 25.9, "#8B8A86", 0.4), ("My promise", 16.6, GRN, at(sid, "9.3"))], top=H * (0.28 if not P else 0.26),
                 unit=" d", fmt="{:.1f}", vmax=30, title="Mean promised days", title_t=0.3)
        y = bars_y = y + 40 * u
        sc2 = bars(sc, [("Olist · late", 4.0, "#8B8A86", at(sid, "against")), ("Mine · late", 10.9, RED, at(sid, "10.9"))], top=y + 60 * u,
                   unit="%", fmt="{:.1f}", vmax=13) if False else None
        lab = label(sc, "late", "but 10.9% arrived late  (Olist: 4.0%)", L, y, size=52, color=RED, t=at(sid, "10.9"), weight=800, w=W - 2 * L)
        st = sc.id("stamp")
        sc.add(f'<div id="{st}">EXPERIMENT 1 FAILED</div>',
               f"#{st}{{position:absolute;left:{W / 2}px;top:{H * (0.66 if not P else 0.66)}px;transform:translateX(-50%) rotate(-4deg);border:{6 * u}px solid {RED};color:{RED};"
               f"font-weight:800;font-size:{(72 if not P else 60) * u}px;padding:{10 * u}px {30 * u}px;border-radius:{10 * u}px;white-space:nowrap;}}")
        sc.js.append(f'tl.fromTo("#{st}",{{opacity:0,scale:1.6}},{{opacity:1,scale:1,duration:.25,ease:"power4.in"}},{at(sid, "failed"):.2f});')
    elif sid == "S25":
        chapter(sc, "WHY? THE WORLD CHANGED")
        wk = DATA["weekly"]
        cx0, cx1 = L, W - L
        cy0, cy1 = H * (0.22 if not P else 0.25), H * (0.64 if not P else 0.60)
        n = len(wk)
        X = lambda i: cx0 + (cx1 - cx0) * i / (n - 1)
        Y = lambda v: cy1 - (cy1 - cy0) * v / 0.28
        iv = next(i for i, w in enumerate(wk) if w["week"] >= "2018-03-05")
        it = next(i for i, w in enumerate(wk) if w["week"] >= "2018-04-30")
        pts = " ".join(f"{X(i):.1f},{Y(w['late']):.1f}" for i, w in enumerate(wk))
        band = lambda a, b, col, nm: f'<rect id="{sc.id(nm)}" x="{X(a)}" y="{cy0}" width="{X(b) - X(a)}" height="{cy1 - cy0}" fill="{col}"/>'
        sc.add(f'<svg width="{W}" height="{H}" style="position:absolute;left:0;top:0">'
               + band(iv, it, "rgba(255,92,77,.16)", "bv") + band(it, n - 1, "rgba(60,198,164,.16)", "bt")
               + f'<line x1="{cx0}" y1="{cy1}" x2="{cx1}" y2="{cy1}" stroke="rgba(243,240,232,.35)" stroke-width="{2 * u}"/>'
               + f'<polyline id="{sc.id("ln")}" points="{pts}" fill="none" stroke="{INK}" stroke-width="{4 * u}" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/></svg>')
        sc.js.append(f'tl.fromTo("#{sc.id("ln")}",{{attr:{{"stroke-dashoffset":1}}}},{{attr:{{"stroke-dashoffset":0}},duration:2.4,ease:"none"}},{at(sid, "weekly"):.2f});')
        sc.js.append(f'tl.fromTo("#{sc.id("bv")}",{{opacity:0}},{{opacity:1,duration:.4}},{at(sid, "validation"):.2f});')
        sc.js.append(f'tl.fromTo("#{sc.id("bt")}",{{opacity:0}},{{opacity:1,duration:.4}},{at(sid, "calmed"):.2f});')
        ip = max(range(n), key=lambda i: wk[i]["late"])
        label(sc, "pk", "26% late", X(ip), Y(wk[ip]["late"]) - 60 * u, size=40, color=RED, t=at(sid, "26"), anchor="center", mono=True)
        label(sc, "vl", "validation", (X(iv) + X(it)) / 2, cy1 + 16 * u, size=30, color=RED, t=at(sid, "validation"), anchor="center", mono=True)
        label(sc, "tl", "test", (X(it) + X(n - 1)) / 2, cy1 + (16 if not P else 52) * u, size=30, color=GRN, t=at(sid, "calmed"), anchor="center", mono=True)
        for i, yr in enumerate(["Jan 2017", "Jan 2018", "Jun 2018"]):
            k = {0: 0, 1: next(j for j, w in enumerate(wk) if w["week"] >= "2018-01-01"), 2: n - 1}[i]
            label(sc, f"yr{i}", yr, X(k), cy1 + (64 if not P else 100) * u, size=30, color="#8B8A86", t=at(sid, "weekly"), anchor=["left", "center", "right"][i], mono=True)
        label(sc, "msg", "The world changed. My model had no way to know.", L, H * (0.76 if not P else 0.70), size=50, t=at(sid, "world"), weight=800, w=W - 2 * L)
    elif sid == "S26":
        chapter(sc, "EXPERIMENT 2 · ONE NEW SIGNAL")
        kinetic(sc, [("How late have deliveries been", at(sid, "how"), INK), ("in the last 30 days?", at(sid, "thirty", default=at(sid, "30")), AMB)], top=H * 0.25, size=84)
        label(sc, "two", "overall  +  to the customer's state", L, H * (0.58 if not P else 0.55), size=40, color="#B8B5AE", t=at(sid, "overall"), mono=True)
        label(sc, "only", "only deliveries already finished", L, H * (0.66 if not P else 0.61), size=40, color=GRN, t=at(sid, "finished"), mono=True)
    elif sid == "S27":
        el = sc.id("lock")
        sc.add(f'<div id="{el}">🔓</div>', f"#{el}{{position:absolute;left:0;right:0;top:{H * 0.24}px;text-align:center;font-size:{170 * u}px;}}")
        sc.appear(el, at(sid, "unlocked"))
        label(sc, "jul", "JULY 2018", W / 2, H * (0.50 if not P else 0.46), size=96, color=AMB, t=at(sid, "july"), anchor="center", weight=800)
        label(sc, "n", "6,156 orders · never touched", W / 2, H * (0.63 if not P else 0.56), size=48, t=at(sid, "6,156"), anchor="center", mono=True)
    elif sid == "S28":
        chapter(sc, "FINAL · JULY 2018 (UNTOUCHED)")
        t1 = at(sid, "promise")
        capture(sc, [{"cell": 47, "h": seg_h(47), "start": 0.2, "end": t1, "hl": [("0.066", at(sid, "twice")), ("0.034", at(sid, "random"))], "zoom": 2.6}])
        y = bars(sc, [("Olist promise", 20.3, "#8B8A86", t1 + 0.2), ("CommerceGuard", 17.0, GRN, at(sid, "17"))], top=H * (0.28 if not P else 0.3),
                 unit=" d", fmt="{:.1f}", vmax=24, title="Mean promised days", title_t=t1)
        label(sc, "late", "late: 3.4% → 5.8%", L, y + 20 * u, size=60, color=RED, t=at(sid, "went"), weight=800, mono=True)
        sc.js.append(f'tl.to("#{sc.id("cam0")}",{{opacity:0,duration:.3}},{t1 - 0.3:.2f});')
    elif sid == "S29":
        kinetic(sc, [("Not a magic win.", 0.3, INK), ("A real trade-off.", at(sid, "trade"), AMB)], top=H * 0.18, size=96)
        label(sc, "a", "Promise faster  →  a few more late parcels", L, H * (0.50 if not P else 0.48), size=46, color=GRN, t=at(sid, "promise"), w=W - 2 * L)
        label(sc, "b", "Safe promise  →  slower, but on time", L, H * (0.60 if not P else 0.58), size=46, color="#B8B5AE", t=at(sid, "safe"), w=W - 2 * L)
        label(sc, "c", "Decide with numbers, not guesses.", L, H * (0.74 if not P else 0.70), size=60, color=AMB, t=at(sid, "numbers"), weight=800, w=W - 2 * L)
    elif sid == "S30":
        chapter(sc, "HONEST LIMITS · WHAT'S NEXT")
        label(sc, "a", "Data from Brazil", L, H * 0.24, size=50, t=at(sid, "brazil"), weight=700)
        label(sc, "b", "Late ≠ failed delivery", L, H * 0.24 + 80 * u, size=50, t=at(sid, "same"), weight=700)
        label(sc, "nx", "Next: cash-on-delivery failures", L, H * (0.52 if not P else 0.48), size=66, color=AMB, t=at(sid, "cash"), weight=800, w=W - 2 * L)
        label(sc, "bd", "with real data from Bangladeshi sellers", L, H * (0.52 if not P else 0.48) + 150 * u, size=46, t=at(sid, "bangladeshi", default=at(sid, "real")), w=W - 2 * L)
    elif sid == "S31":
        el = sc.id("logo")
        sc.add(f'<div id="{el}"><span>Commerce</span><span style="color:{AMB}">Guard</span></div>',
               f"#{el}{{position:absolute;left:0;right:0;top:{H * (0.30 if not P else 0.30)}px;text-align:center;font-weight:800;font-size:{(140 if not P else 112) * u}px;letter-spacing:-0.04em;}}")
        sc.appear(el, at(sid, "commerce"))
        label(sc, "tg", "Predict risk. Understand behavior. Reduce preventable losses.", W / 2, H * (0.30 if not P else 0.30) + 190 * u, size=36,
              t=at(sid, "predict"), anchor="center" if not P else "center", w=None if not P else None)
        label(sc, "gh", "Notebook: link in the description", W / 2, H * (0.62 if not P else 0.56), size=40, color="#B8B5AE", t=at(sid, "notebook"), anchor="center", mono=True)
        label(sc, "st", "One step at a time. One model at a time.", W / 2, H * (0.70 if not P else 0.62), size=44, color=AMB, t=at(sid, "step"), anchor="center", weight=800)
    return sc


def seg_h(c):
    import struct
    return struct.unpack(">II", (HERE / f"assets/cells/cell_{c:02d}.png").read_bytes()[16:24])[1]


# ---------------------------------------------------------------- captions
FIX = [(["olis"], "Olist"), (["alis"], "Olist"), (["ollis"], "Olist"), (["olist"], "Olist"), (["o-list"], "Olist"), (["olist's"], "Olist's"),
       (["light", "gbm"], "LightGBM"), (["lightdbm"], "LightGBM"), (["lightgbm"], "LightGBM"), (["marania"], "Maranhão"), (["maranha"], "Maranhão"),
       (["say", "our", "raw"], "Ceará"), (["siraar"], "Ceará"), (["commerce", "guard"], "CommerceGuard"), (["than", "the", "target"], "Then the target"),
       (["as", "late", "if"], "is late if"), (["guesses", "that", "random"], "guesses at random"), (["their", "light", "gbm"], "Then LightGBM"),
       (["i'd", "also", "ask"], "I also asked"), (["sit", "sits"], "set sits"), (["i", "stop", "my"], "I stopped my"), (["match", "people"], "matched people")]


def caption_words(sid):
    """Script wording on transcript timing. Digits come from the transcript ("0.097"), every other word from the script,
    so recogniser slips ("Leith", "apostles") never reach the screen."""
    import difflib
    A = [dict(w) for w in words(sid)]
    S_ = (SCENES.get(sid) or OUTROS[sid])["text"].split()
    key = lambda t: re.sub(r"[^a-z0-9]", "", t.lower())
    sm = difflib.SequenceMatcher(None, [key(w["text"]) for w in A], [key(t) for t in S_], autojunk=False)
    out = []
    digit = lambda t: bool(re.search(r"\d", t))
    for op, a0, a1, s0, s1 in sm.get_opcodes():
        if op == "equal":
            out += [{"text": S_[s0 + k], "start": A[a0 + k]["start"], "end": A[a0 + k]["end"]} for k in range(a1 - a0)]
        elif any(digit(w["text"]) for w in A[a0:a1]):
            # spoken numbers: digits from the transcript, every other word from the script
            NUMW = set("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen "
                       "eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand point percent and".split())
            dig = [w for w in A[a0:a1] if digit(w["text"])]
            oth = [w for w in A[a0:a1] if not digit(w["text"])]
            k, prev_num = 0, False
            for tok in S_[s0:s1]:
                isnum = key(tok) in NUMW
                if isnum and not prev_num and dig:
                    d = dig.pop(0)
                    tail = re.sub(r"[\w%.]", "", tok)[-1:] if not re.search(r"[,.?!]$", d["text"]) else ""
                    out.append({**d, "text": d["text"] + tail})
                elif not isnum:
                    ref = oth[min(k, len(oth) - 1)] if oth else (out[-1] if out else A[a0])
                    out.append({"text": tok, "start": ref["start"], "end": ref["end"]}); k += 1
                prev_num = isnum
            out += dig  # any digit token the script didn't anchor
        elif s1 > s0:
            t0 = A[a0]["start"] if a1 > a0 else (A[a0 - 1]["end"] if a0 > 0 else 0)
            t1 = A[a1 - 1]["end"] if a1 > a0 else (A[a0]["start"] if a0 < len(A) else t0 + 0.3 * (s1 - s0))
            step = max(0.05, (t1 - t0) / (s1 - s0))
            out += [{"text": S_[s0 + k], "start": t0 + k * step, "end": t0 + (k + 1) * step} for k in range(s1 - s0)]
    return out


def captions(W, H, timeline):
    P = H > W; u = min(W, H) / 1080
    groups = []
    for sid, t0 in timeline:
        cur = []
        for w in caption_words(sid):
            cur.append(w)
            if len(cur) >= (6 if not P else 4) or w["text"][-1:] in ".,?!":
                groups.append((t0 + LEAD + cur[0]["start"], t0 + LEAD + cur[-1]["end"] + 0.15, cur)); cur = []
        if cur:
            groups.append((t0 + LEAD + cur[0]["start"], t0 + LEAD + cur[-1]["end"] + 0.15, cur))
    html, js = [], []
    for k, (a, b, ws) in enumerate(groups):
        nxt = groups[k + 1][0] if k + 1 < len(groups) else b + 1
        b = min(b + 0.6, nxt)
        text = " ".join(f'<span style="color:{AMB}">{escape(w["text"])}</span>' if re.search(r"\d", w["text"]) else escape(w["text"]) for w in ws)
        html.append(f'<div id="cap{k}" class="cap">{text}</div>')
        js.append(f'tl.set("#cap{k}",{{opacity:1}},{a:.2f});tl.set("#cap{k}",{{opacity:0}},{b:.2f});')
    top = H * 0.86 if not P else H * 0.78
    return f"""<template>
<style>#root{{position:absolute;inset:0;}}
#root .cap{{position:absolute;left:50%;top:{top}px;transform:translateX(-50%);max-width:{W * 0.8}px;width:max-content;text-align:center;opacity:0;
 font-family:Inter,sans-serif;font-weight:700;font-size:{(40 if not P else 50) * u}px;line-height:1.2;color:#F3F0E8;
 background:rgba(20,21,23,.82);padding:{8 * u}px {22 * u}px;border-radius:{10 * u}px;}}</style>
<div id="root" data-composition-id="captions" data-width="{W}" data-height="{H}">{''.join(html)}</div>
<script>const tl=gsap.timeline({{paused:true}});{''.join(js)}window.__timelines["captions"]=tl;</script>
</template>"""


# ---------------------------------------------------------------- assemble a project
import subprocess
SFXLEN = {f.stem: round(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)], capture_output=True, text=True).stdout), 2) for f in (HERE / "assets/sfx").glob("*.mp3")}
SFX = {"S04": ("whoosh-cinematic", 0.0), "S06": ("whoosh", 0.0), "S12": ("whoosh-short", 0.0), "S17": ("whoosh", 0.0), "S20": ("whoosh-short", 0.0),
       "S23": ("whoosh-cinematic", 0.0), "S26": ("whoosh", 0.0), "S30": ("whoosh-short", 0.0)}


def project(out, W, H, ids, reel=None):
    out.mkdir(parents=True, exist_ok=True)
    (out / "compositions").mkdir(exist_ok=True)
    if out != HERE:
        if (out / "assets").exists():
            shutil.rmtree(out / "assets")
        shutil.copytree(HERE / "assets", out / "assets")
    t, hosts, audio, timeline = 0.0, [], [], []
    if reel:
        ids = list(ids)
    for k, sid in enumerate(ids):
        sc = outro(sid, W, H, reel) if sid.startswith("R") else S(sid, W, H)
        d = dur(sid) + (2.4 if sid.startswith("R") else 0)
        (out / f"compositions/{sid.lower()}.html").write_text(sc.render())
        hosts.append(f'<div id="{sid.lower()}" data-composition-id="{sid.lower()}" data-composition-src="compositions/{sid.lower()}.html" '
                     f'data-start="{t:.2f}" data-duration="{d:.2f}" data-track-index="1" data-track-kind="graphics" data-width="{W}" data-height="{H}"></div>')
        vd = (SCENES.get(sid) or OUTROS[sid])["dur"]
        audio.append(f'<audio id="vo-{sid.lower()}" class="clip" src="assets/vo/{sid}.wav" data-start="{t + LEAD:.2f}" data-duration="{vd:.2f}" data-track-index="10" data-volume="1"></audio>')
        if sid in SFX and k > 0:
            name, off = SFX[sid]
            audio.append(f'<audio id="sfx-{sid.lower()}" class="clip" src="assets/sfx/{name}.mp3" data-start="{max(0, t - 0.25 + off):.2f}" data-duration="{SFXLEN[name]}" data-track-index="11" data-volume="0.35"></audio>')
        if sid == "S24":
            tf = t + at("S24", "failed")
            audio.append(f'<audio id="sfx-riser" class="clip" src="assets/sfx/riser.mp3" data-start="{max(t, tf - 2.0):.2f}" data-duration="2.0" data-track-index="12" data-volume="0.25"></audio>')
            audio.append(f'<audio id="sfx-impact" class="clip" src="assets/sfx/impact-bass-1.mp3" data-start="{tf + 0.03:.2f}" data-duration="{SFXLEN['impact-bass-1']}" data-track-index="13" data-volume="0.45"></audio>')
        if sid == "S13":
            audio.append(f'<audio id="sfx-typing" class="clip" src="assets/sfx/typing.mp3" data-start="{t + 0.3:.2f}" data-duration="{min(SFXLEN['typing'], 6)}" data-track-index="12" data-volume="0.12"></audio>')
        if (sid, W) in TYPING:
            a_, b_ = TYPING[(sid, W)]
            audio.append(f'<audio id="sfx-type-{sid.lower()}" class="clip" src="assets/sfx/typing.mp3" data-start="{t + a_:.2f}" data-duration="{min(SFXLEN['typing'], b_ - a_):.2f}" data-track-index="14" data-volume="0.10"></audio>')
        if not sid.startswith("R"):
            timeline.append((sid, t))
        t += d
    total = round(t, 2)
    (out / "compositions/captions.html").write_text(captions(W, H, timeline))
    hosts.append(f'<div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{total}" '
                 f'data-track-index="5" data-track-kind="captions" data-width="{W}" data-height="{H}" style="z-index:5"></div>')
    if reel:
        hosts.append(part_badge(out, W, H, reel, total))
    (out / "index.html").write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width={W}, height={H}"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:{W}px;height:{H}px;overflow:hidden;background:{GROUND}}}</style></head>
<body><div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="{W}" data-height="{H}">
{chr(10).join(hosts)}
{chr(10).join(audio)}
</div>
<script>window.__timelines["main"] = gsap.timeline({{paused:true}});</script>
</body></html>""")
    print(f"{out.name}: {len(ids)} scenes, {total:.1f}s")
    return total


ORDER = ["S01", "S02", "S03", "S04", "S05", "S06", "C01", "S07", "S08", "C02", "S09", "S10", "C03", "S11",
         "S12", "S13", "S14", "C04", "S15", "S16", "C06", "S17", "C07", "S18", "S19",
         "S20", "S21", "S22", "S23", "C08", "S24", "S25", "S26", "C09", "S27", "S28", "S29", "S30", "S31"]
REELS = {1: ("THE IDEA & THE DATA", ORDER[:ORDER.index("C03")]), 2: ("NO CHEATING & THE TEST", ORDER[ORDER.index("C03"):ORDER.index("S21")]),
         3: ("WHAT WENT WRONG", ORDER[ORDER.index("S21"):])}
_OLD_REELS = {1: ("THE IDEA", ["S01", "S02", "S03", "S04", "S05"]), 2: ("THE DATA", ["S06", "S07", "S08", "S09", "S10", "S11"]),
         3: ("NO CHEATING", ["S12", "S13", "S14", "S15", "S16"]), 4: ("THE TEST", ["S17", "S18", "S19"]),
         5: ("WHAT DRIVES RISK", ["S20", "S21", "S22"]), 6: ("EXPERIMENT 1 FAILED", ["S23", "S24", "S25"]),
         7: ("THE FIX", ["S26", "S27", "S28", "S29", "S30"])}


def outro(rid, W, H, reel):
    sc = Scene(rid, W, H); u = sc.u; L = W * 0.07
    n = int(rid[1])
    if n < 3:
        label(sc, "nx", f"NEXT · PART {n + 1}/3", L, H * 0.30, size=40, color=AMB, t=0.2, weight=800)
        label(sc, "hk", OUTROS[rid]["card"], L, H * 0.36, size=72, t=0.4, weight=800, w=W - 2 * L)
    else:
        label(sc, "nx", "FULL EPISODE ON YOUTUBE", L, H * 0.30, size=44, color=AMB, t=0.2, weight=800)
        label(sc, "hk", "▶ @csfunda.official", L, H * 0.36, size=84, t=0.4, weight=800)
    label(sc, "h1", "Follow CS Funda", L, H * 0.62, size=48, t=dur(rid) - 0.1, weight=800)
    label(sc, "h2", "IG @csfunda.official_  ·  YT @csfunda.official", L, H * 0.62 + 70 * u, size=34, color="#B8B5AE", t=dur(rid) - 0.1, mono=True, w=W - 2 * L)
    return sc


def part_badge(out, W, H, reel, total):
    n, (title, _) = reel, REELS[reel]
    u = min(W, H) / 1080
    (out / "compositions/badge.html").write_text(f"""<template>
<style>#root{{position:absolute;inset:0;}}
#root #bd{{position:absolute;left:{W * 0.07}px;top:{H * 0.05}px;font-family:Inter,sans-serif;font-weight:800;color:#F3F0E8;font-size:{34 * u}px;}}
#root #bd b{{color:{AMB}}}
#root .pg{{position:absolute;top:{H * 0.05 + 54 * u}px;height:{6 * u}px;width:{(W * 0.86 - 2 * 8 * u) / 3}px;border-radius:3px;background:rgba(243,240,232,.25);}}</style>
<div id="root" data-composition-id="badge" data-width="{W}" data-height="{H}">
<div id="bd">CommerceGuard · <b>PART {n}/3</b> · {title}</div>
{''.join(f'<div class="pg" style="left:{W * 0.07 + i * ((W * 0.86 - 2 * 8 * u) / 3 + 8 * u)}px;{"background:" + AMB if i < n else ""}"></div>' for i in range(3))}
</div><script>const tl=gsap.timeline({{paused:true}});tl.set("#bd",{{opacity:1}},0);window.__timelines["badge"]=tl;</script></template>""")
    return (f'<div id="badge" data-composition-id="badge" data-composition-src="compositions/badge.html" data-start="0" data-duration="{total}" '
            f'data-track-index="6" data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index:6"></div>')


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reels":
        LEAD, TAIL = 0.2, 0.25  # tighter pacing so each part stays under Instagram's 3:00 limit
        shutil.rmtree(HERE.parent / "reels", ignore_errors=True)
        for n, (_, ids) in REELS.items():
            project(HERE.parent / f"reels/part{n}", 1080, 1920, ids + [f"R{n}"], reel=n)
    else:
        project(HERE, 1920, 1080, ORDER)
