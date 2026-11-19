"""CommerceGuard Episode 2 — "One parcel, two phones".

Reuses the Episode 1 engine (../../video/build.py) for scenes, captions, code typing, glass and reels,
and adds footage, a two-person chat phone and source-cited fact cards.
python build_ep2.py          -> this folder (YouTube 1920x1080)
python build_ep2.py reels    -> ../reels/part1..3 (1080x1920)
"""
import importlib.util, json, re, sys
from html import escape
from pathlib import Path

HERE = Path(__file__).parent
EP2 = HERE.parent
spec = importlib.util.spec_from_file_location("b", HERE.parent.parent / "video/build.py")
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

# ---- point the Episode 1 engine at Episode 2's material
b.HERE = HERE
b.REC = EP2                                   # words/ and vo/ live here
REC2 = EP2.parent / "recording_ep2"
b.BOXES = json.loads((REC2 / "boxes.json").read_text()) if (REC2 / "boxes.json").exists() else {}
b.CELLRUN = {c["i"]: c for c in json.loads((REC2 / "cells.json").read_text())} if (REC2 / "cells.json").exists() else {}
meta = json.loads((EP2 / "vo/scenes.json").read_text())
b.SCENES = {k: v for k, v in meta.items() if k.startswith("E")}
cards = {"R1": "Does it work on products it never saw? And the order model", "R2": ""}
b.OUTROS = {f"R{k[1]}": {**v, "id": f"R{k[1]}", "card": cards[f"R{k[1]}"]} for k, v in meta.items() if k.startswith("F")}
for k in b.OUTROS:   # words for outros were transcribed under F ids
    src, dst = EP2 / f"words/F{k[1]}.words.json", EP2 / f"words/{k}.words.json"
    if src.exists() and not dst.exists():
        dst.write_text(src.read_text())
b.CODES = json.loads((HERE / "codes_ep2.json").read_text())
b.HOLD = {"E01": 0.6, "E04": 0.8, "E05": 1.0, "E06": 0.6, "E09": 0.5, "E10": 0.8, "E11": 0.8, "E17": 0.8, "E18": 0.8, "E19": 0.6, "E21": 0.5,
          "E22": 0.8, "E23": 0.8, "E25": 0.8, "E27": 1.4, "E31": 1.6}
b.SFX = {"E08": ("whoosh-cinematic", 0.0), "E12": ("whoosh", 0.0), "E14": ("whoosh-short", 0.0), "E20": ("whoosh", 0.0),
         "E23": ("whoosh-short", 0.0), "E26": ("whoosh-cinematic", 0.0), "E30": ("whoosh-short", 0.0)}
INK, AMB, RED, GRN = b.INK, b.AMB, b.RED, b.GRN
at, label, kinetic, chapter, bars, capture, glass, aura, sweep = b.at, b.label, b.kinetic, b.chapter, b.bars, b.capture, b.glass, b.aura, b.sweep
EXTRA = {}   # sid -> [(local_t, sfx, volume)]
FONT = "@font-face{font-family:'NotoBN';src:url('assets/fonts/NotoSansBengali.ttf');}"


def sfx(sid, t, name, vol=0.35):
    EXTRA.setdefault(sid, []).append((t, name, vol))


# ---------------------------------------------------------------- footage
CLIPLEN = {"dhaka_aerial": 16, "dhaka_street": 12, "nadia": 10.8, "typing": 13, "rafi_call": 8.8, "rafi_office": 9.5, "pack_wrap": 18, "pack_label": 17}


def footage(sc, name, x, y, w, h, t0=0.0, ms=0.0, push=(1.0, 1.07), radius=18, dim=0.0, tag=None, tag_t=0.4):
    u, d = sc.u, b.dur(sc.sid)
    frame, inner, vid = sc.id(f"{name}f"), sc.id(f"{name}i"), sc.id(f"{name}v")
    rate = round(min(1.0, (CLIPLEN[name] - ms) / max(0.1, d - t0)), 3)
    sc.add(f'<div id="{frame}"><div id="{inner}"><video id="{vid}" class="clip" src="assets/footage/{name}.mp4" muted playsinline '
           f'data-start="{t0:.2f}" data-duration="{d - t0:.2f}" data-media-start="{ms:.2f}" data-hf-media-start-basis="local" '
           f'data-playback-rate="{rate}" data-track-index="1"></video></div>'
           + (f'<div class="fdim" style="background:rgba(20,21,23,{dim})"></div>' if dim else "") + "</div>",
           f"#{frame}{{position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;overflow:hidden;border-radius:{radius * u}px;"
           f"box-shadow:0 {30 * u}px {80 * u}px rgba(0,0,0,.5);}}#{inner}{{position:absolute;inset:0;}}"
           f"#{vid}{{width:100%;height:100%;object-fit:cover;display:block;}}#root .fdim{{position:absolute;inset:0;}}")
    sc.js.append(f'tl.fromTo("#{inner}",{{scale:{push[0]}}},{{scale:{push[1]},duration:{d:.2f},ease:"none"}},0);')
    if t0 > 0.05:
        sc.js.append(f'tl.fromTo("#{frame}",{{opacity:0,y:{30 * u}}},{{opacity:1,y:0,duration:.6,ease:"expo.out"}},{t0:.2f});')
    if tag:
        el = sc.id(f"{name}tag")
        sc.add(f'<div id="{el}">{tag}</div>', f"#{el}{{position:absolute;left:{x + 24 * u}px;top:{y + h - 84 * u}px;padding:{10 * u}px {20 * u}px;"
               f"font-size:{30 * u}px;font-weight:800;background:rgba(20,21,23,.82);border-radius:{14 * u}px;}}")
        sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,x:{-20 * u}}},{{opacity:1,x:0,duration:.5,ease:"expo.out"}},{tag_t:.2f});')
    return frame


# ---------------------------------------------------------------- the chat phone (Rafi's inbox)
MSG = {
    "m1": ("in", "ভাই, অর্ডার করছি, ক্যাশ অন ডেলিভারি তো?", "I'm ordering. Cash on delivery, right?", 20),
    "r1": ("out", "জি আপু, ২-৩ দিনে পেয়ে যাবেন", "Yes, you'll get it in 2–3 days", None),
    "m2": ("in", "৩ দিন হয়ে গেল, এখনো পণ্য পাইনি", "It's been 3 days, still nothing", 90),
    "r2": ("out", "আপু, কুরিয়ারে আছে, আজকেই পাবেন", "It's with the courier, today for sure", None),
    "m3": ("in", "প্রোডাক্ট টা নকল মনে হচ্ছে, ছবির সাথে মিল নাই", "It looks fake, nothing like the photo", 95),
    "m4": ("in", "আমি রিটার্ন করবো, টাকা ফেরত চাই", "I'm returning it. I want my money back", 94),
    "m5": ("in", "Thanks bhai, product ta khub valo hoise!", "Thanks, the product is really good!", 0),
}


def phone(sc, x, y, w, h, contact, shown, new=(), scores=(), stamp=None):
    """shown: message keys already on screen; new: [(key, t)] arriving (typing dots first for 'in');
    scores: [(key, t)] risk meter fills next to that bubble."""
    u = sc.u
    ph = sc.id("phone")
    sc.css.append(FONT)
    keys = list(shown) + [k for k, _ in new]
    body_h = h - 150 * u
    sc.add(f'<div id="{ph}"><div class="ph-h"><div class="ph-av">{contact[0]}</div><div><b>{contact}</b><span>Rafi\'s Shop · inbox</span></div></div>'
           f'<div class="ph-b" id="{ph}b"></div></div>',
           f"#{ph}{{position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;border-radius:{44 * u}px;background:#0F1012;"
           f"border:{6 * u}px solid #2B2C30;box-shadow:0 {40 * u}px {90 * u}px rgba(0,0,0,.6);overflow:hidden;}}"
           f"#root .ph-h{{display:flex;align-items:center;gap:{16 * u}px;padding:{26 * u}px {26 * u}px {18 * u}px;border-bottom:{2 * u}px solid #232428;}}"
           f"#root .ph-av{{width:{64 * u}px;height:{64 * u}px;border-radius:50%;background:{AMB};color:#141517;font-weight:800;font-size:{32 * u}px;"
           f"display:flex;align-items:center;justify-content:center;}}#root .ph-h b{{display:block;font-size:{32 * u}px;}}"
           f"#root .ph-h span{{font-size:{28 * u}px;color:#8B8A86;}}"
           f"#root .ph-b{{position:absolute;left:0;right:0;top:{118 * u}px;bottom:0;}}")
    # layout: newest at the bottom; estimate heights from text length
    bw = w * 0.76
    cpl_bn, cpl_en = bw / (19 * u), bw / (15 * u)
    est = lambda k: (max(1, -(-len(MSG[k][1]) // int(cpl_bn))) * 56 + max(1, -(-len(MSG[k][2]) // int(cpl_en))) * 38 + 46) * u
    ys, yy = {}, body_h - 70 * u
    for k in reversed(keys):
        yy -= est(k); ys[k] = yy; yy -= 18 * u
    arrive = dict(new)
    keys = [k for k in keys if ys[k] >= 8 * u or k in arrive]   # older bubbles have scrolled out of view, like a real chat
    for k in keys:
        side, bn, en, _ = MSG[k]
        el = sc.id(f"bb{k}")
        left = (24 * u) if side == "in" else (w - bw - 24 * u - 12 * u)
        col = "#25262A" if side == "in" else "#3A3220"
        html = f'<div id="{el}" class="bub"><div class="bn">{escape(bn)}</div><div class="en">{escape(en)}</div></div>'
        sc.html[-1] = sc.html[-1][:-len("</div></div>")] + html + "</div></div>"
        sc.css.append(f"#{el}{{left:{left}px;top:{118 * u + ys[k]}px;width:{bw}px;background:{col};"
                      f"border-radius:{26 * u}px {26 * u}px {26 * u if side == 'in' else 6 * u}px {6 * u if side == 'in' else 26 * u}px;}}")
        if k in arrive:
            t = arrive[k]
            if side == "in":
                dots = sc.id(f"dt{k}")
                sc.html[-1] = sc.html[-1][:-len("</div></div>")] + f'<div id="{dots}" class="dots"><i></i><i></i><i></i></div>' + "</div></div>"
                sc.css.append(f"#{dots}{{left:{left}px;top:{118 * u + ys[k] + est(k) - 70 * u}px;}}")
                sc.js.append(f'tl.fromTo("#{dots}",{{opacity:0,scale:.6}},{{opacity:1,scale:1,duration:.2}},{max(0.05, t - 0.9):.2f});'
                             f'tl.to("#{dots}",{{opacity:0,duration:.1}},{t - 0.05:.2f});')
                for j in range(3):
                    sc.js.append(f'tl.fromTo("#{dots} i:nth-child({j + 1})",{{y:0}},{{y:{-8 * u},duration:.18,yoyo:true,repeat:3,ease:"sine.inOut"}},{max(0.05, t - 0.85) + j * 0.1:.2f});')
            sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,scale:.75,transformOrigin:"{"0% 100%" if side == "in" else "100% 100%"}"}},'
                         f'{{opacity:1,scale:1,duration:.32,ease:"back.out(1.6)"}},{t:.2f});')
            sfx(sc.sid, t, "pop", 0.25)
    sc.css.append(f"#root .bub{{position:absolute;padding:{14 * u}px {20 * u}px;}}#root .bub .bn{{font-family:'NotoBN',Inter,sans-serif;font-size:{34 * u}px;line-height:1.5;color:{INK};}}"
                  f"#root .bub .en{{font-size:{28 * u}px;line-height:1.35;color:#9C9A94;margin-top:{4 * u}px;}}"
                  f"#root .dots{{position:absolute;display:flex;gap:{8 * u}px;padding:{18 * u}px {22 * u}px;background:#25262A;border-radius:{26 * u}px;opacity:0;}}"
                  f"#root .dots i{{width:{12 * u}px;height:{12 * u}px;border-radius:50%;background:#8B8A86;display:block;}}")
    for k, t in scores:
        s = MSG[k][3]
        col = GRN if s < 30 else (AMB if s < 70 else RED)
        el = sc.id(f"sc{k}")
        sc.html[-1] = sc.html[-1][:-len("</div></div>")] + f'<div id="{el}" class="meter"><span>{s}%</span> unhappy</div>' + "</div></div>"
        sc.css.append(f"#{el}{{left:{w - 24 * u - 250 * u}px;top:{118 * u + ys[k] - 34 * u}px;border-color:{col};}}#{el} span{{color:{col};}}")
        sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,y:{10 * u}}},{{opacity:1,y:0,duration:.3,ease:"expo.out"}},{t:.2f});')
        sfx(sc.sid, t, "click-soft", 0.3)
    sc.css.append(f"#root .meter{{position:absolute;width:{250 * u}px;text-align:center;padding:{6 * u}px 0;border:{3 * u}px solid;border-radius:{30 * u}px;"
                  f"background:#141517;font-weight:800;font-size:{28 * u}px;color:{INK};z-index:3;}}#root .meter span{{font-size:{30 * u}px;}}")
    if stamp:
        txt, t = stamp
        el = sc.id("stamp")
        sc.html[-1] = sc.html[-1][:-len("</div></div>")] + f'<div id="{el}" class="dstamp">{txt}</div>' + "</div></div>"
        sc.css.append(f"#{el}{{left:{w / 2}px;top:{130 * u}px;z-index:4;}}#root .dstamp{{position:absolute;transform:translateX(-50%);padding:{6 * u}px {18 * u}px;"
                      f"border-radius:{20 * u}px;background:#232428;color:#B8B5AE;font-size:{28 * u}px;font-weight:700;white-space:nowrap;}}")
        sc.appear(el, t, y=0)
    return ph


def layout(sc):
    """footage box and phone box for a split-screen chat scene."""
    W, H, u = sc.W, sc.H, sc.u
    if not sc.P:
        return (W * 0.06, H * 0.13, W * 0.54, H * 0.64), (W * 0.64, H * 0.06, W * 0.30, H * 0.78)
    return (W * 0.05, H * 0.11, W * 0.90, H * 0.27), (W * 0.08, H * 0.40, W * 0.84, H * 0.37)


def source(sc, text, t):
    el = label(sc, "src", "Source: " + text, sc.W * (0.06 if not sc.P else 0.05), sc.H * (0.80 if not sc.P else 0.74), size=28,
               color="#8B8A86", t=t, w=sc.W * 0.88)
    return el


# ---------------------------------------------------------------- scenes
def S2(sid, W, H):
    sc = b.Scene(sid, W, H); u, P = sc.u, sc.P
    L = W * (0.06 if not P else 0.05)
    if sid == "E01":
        footage(sc, "dhaka_aerial", 0, 0, W, H, push=(1.0, 1.10), radius=0, dim=0.30)
        label(sc, "t1", "This is Dhaka.", L, H * (0.30 if not P else 0.30), size=110, weight=800, t=0)
        label(sc, "t2", "Thousands of small online shops. Thousands of parcels, every day.", L, H * (0.30 if not P else 0.30) + 140 * u,
              size=44, t=at(sid, "thousands"), w=W * (0.6 if not P else 0.9))
        label(sc, "t3", "This one belongs to Rafi.", L, H * (0.62 if not P else 0.56), size=56, color=AMB, weight=800, t=at(sid, "rafi"))
    elif sid in ("E02", "E03", "E04", "E05"):
        (fx, fy, fw, fh), (px, py, pw, phh) = layout(sc)
        if sid == "E02":
            footage(sc, "nadia", fx, fy, fw, fh, tag="Nadia · customer, Dhaka", tag_t=at(sid, "nadia"))
            phone(sc, px, py, pw, phh, "Nadia", [], new=[("m1", at(sid, "message"))])
        elif sid == "E03":
            footage(sc, "pack_wrap", fx, fy, fw, fh, tag="Rafi · online seller", tag_t=0.4)
            phone(sc, px, py, pw, phh, "Nadia", ["m1"], new=[("r1", at(sid, "yes"))])
        elif sid == "E04":
            footage(sc, "typing", fx, fy, fw, fh, tag="Nadia", tag_t=0.4)
            phone(sc, px, py, pw, phh, "Nadia", ["m1", "r1"], new=[("m2", at(sid, "writes")), ("r2", at(sid, "tone") + 0.2)], stamp=("3 days later", 0.3))
        else:
            footage(sc, "pack_label", fx, fy, fw, fh, tag="At the door", tag_t=0.4)
            phone(sc, px, py, pw, phh, "Nadia", ["r2"], new=[("m3", at(sid, "photo"))])
            el = sc.id("refused")
            sc.add(f'<div id="{el}">REFUSED AT THE DOOR</div>',
                   f"#{el}{{position:absolute;left:{fx + fw / 2}px;top:{fy + fh / 2}px;transform:translate(-50%,-50%) rotate(-6deg);border:{7 * u}px solid {RED};color:{RED};"
                   f"font-weight:800;font-size:{(78 if not P else 60) * u}px;padding:{10 * u}px {30 * u}px;border-radius:{12 * u}px;white-space:nowrap;background:rgba(20,21,23,.55);}}")
            t = at(sid, "refuses")
            sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,scale:1.7}},{{opacity:1,scale:1,duration:.22,ease:"power4.in"}},{t:.2f});')
            sfx(sid, t + 0.2, "impact-bass-1", 0.45)
    elif sid == "E06":
        fw = W * (0.50 if not P else 0.90)
        footage(sc, "rafi_office", L, H * (0.13 if not P else 0.11), fw, H * (0.64 if not P else 0.30), tag="Rafi", tag_t=0.3)
        items = [("✕  No payment", "money"), ("✕  Delivery charge, both ways", "charge"), ("✕  The dress comes back used", "used")]
        x0, y0 = (W * 0.62, H * 0.24) if not P else (L, H * 0.47)
        label(sc, "hd", "One refused parcel costs Rafi:", x0, y0 - 90 * u, size=40, weight=800, t=0.5, w=W * (0.34 if not P else 0.9))
        for i, (tx, tok) in enumerate(items):
            el = sc.id(f"ls{i}")
            sc.add(f'<div id="{el}" class="gl">{tx}</div>', f"#{el}{{left:{x0}px;top:{y0 + i * 110 * u}px;width:{W * (0.32 if not P else 0.9)}px;}}")
            sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,x:{40 * u}}},{{opacity:1,x:0,duration:.5,ease:"expo.out"}},{at(sid, tok):.2f});')
        sc.css.append(f"#root .gl{{position:absolute;padding:{20 * u}px {26 * u}px;font-size:{36 * u}px;font-weight:800;color:{RED};{glass(sc)}}}")
    elif sid == "E07":
        footage(sc, "dhaka_street", 0, 0, W, H, radius=0, dim=0.72, push=(1.05, 1.12))
        label(sc, "big", "75–85%", L, H * (0.24 if not P else 0.26), size=(220 if not P else 170), color=AMB, weight=800, t=at(sid, "courier"), mono=False)
        label(sc, "sub", "of parcels a typical shop actually delivers", L, H * (0.24 if not P else 0.26) + (260 if not P else 210) * u, size=48, weight=800, t=at(sid, "delivers"), w=W * 0.88)
        source(sc, "Pathao (courier) blog, industry estimate", at(sid, "delivers") + 0.4)
    elif sid == "E08":
        footage(sc, "dhaka_street", 0, 0, W, H, radius=0, dim=0.80, ms=4)
        label(sc, "q", "Why does Bangladesh pay cash at the door?", L, H * 0.24, size=72, weight=800, t=0, w=W * 0.86)
        el = label(sc, "yr", "2021", L, H * (0.46 if not P else 0.42), size=(240 if not P else 200), color=AMB, weight=800, t=at(sid, "2021"))
    elif sid == "E09":
        aura(sc, (RED, AMB))
        chapter(sc, "2021 · THE COLLAPSE")
        names = [("Evaly", "evaly"), ("e-Orange", "orange")]
        for i, (n_, tok) in enumerate(names):
            el = sc.id(f"pl{i}")
            x = L + i * (W * (0.30 if not P else 0.45))
            sc.add(f'<div id="{el}" class="plat">{n_}</div>', f"#{el}{{left:{x}px;top:{H * 0.26}px;}}")
            sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,y:{30 * u}}},{{opacity:1,y:0,duration:.5,ease:"expo.out"}},{min(at(sid, tok, default=0.6 + i * 0.6), 0.4 + i * 0.5):.2f});')
        sc.css.append(f"#root .plat{{position:absolute;padding:{24 * u}px {40 * u}px;font-size:{60 * u}px;font-weight:800;{glass(sc)}}}")
        label(sc, "a", "Pay first. Huge discounts.", L, H * 0.48, size=60, weight=800, t=at(sid, "advance"), w=W * 0.88)
        label(sc, "b2", "Then the deliveries stopped.", L, H * 0.60, size=60, color=RED, weight=800, t=at(sid, "stopped"), w=W * 0.88)
    elif sid == "E10":
        chapter(sc, "THE MONEY")
        top = H * (0.22 if not P else 0.24)
        label(sc, "a", "≈ Tk 3,000 crore", L, top, size=(120 if not P else 96), color=RED, weight=800, t=0.5)
        label(sc, "a2", "stuck in Evaly, e-Orange and Dhamaka (official estimate)", L, top + 150 * u, size=36, t=at(sid, "3,000", default=2) + 0.3, w=W * 0.88)
        label(sc, "c", "Tk 252 crore", L, top + (300 if not P else 330) * u, size=(120 if not P else 96), color=GRN, weight=800, t=at(sid, "250", default=at(sid, "september")))
        label(sc, "c2", "returned by September 2022, to 28,867 customers", L, top + (450 if not P else 480) * u, size=36, t=at(sid, "29,000", default=at(sid, "customers")), w=W * 0.88)
        source(sc, "The Daily Observer; Dhaka Tribune / Financial Express (Ministry of Commerce)", at(sid, "29,000", default=8) + 0.4)
    elif sid == "E11":
        aura(sc, (AMB, RED))
        cy = H * (0.44 if not P else 0.40)
        bx, sx = (W * 0.20, W * 0.68) if not P else (W * 0.22, W * 0.62)
        for nm, x, txt in [("buy", bx, "Buyer"), ("sel", sx, "Seller")]:
            el = sc.id(nm)
            sc.add(f'<div id="{el}" class="who"><b>{txt}</b></div>', f"#{el}{{left:{x}px;top:{cy}px;}}")
            sc.appear(el, 0.3)
        sc.css.append(f"#root .who{{position:absolute;width:{300 * u}px;height:{300 * u}px;border-radius:50%;{glass(sc)}border-radius:50%;display:flex;"
                      f"align-items:center;justify-content:center;font-size:{52 * u}px;}}")
        sh = sc.id("shield")
        sc.add(f'<div id="{sh}">🛡</div>', f"#{sh}{{position:absolute;left:{W / 2 - 60 * u}px;top:{cy - 220 * u}px;font-size:{120 * u}px;}}")
        sc.js.append(f'tl.fromTo("#{sh}",{{opacity:0,x:0}},{{opacity:1,x:{bx - W / 2 + 120 * u:.1f},duration:.8,ease:"power2.inOut"}},{at(sid, "shield"):.2f});')
        rk = sc.id("risk")
        sc.add(f'<div id="{rk}">RISK →</div>', f"#{rk}{{position:absolute;left:{bx + (260 if not P else 0) * u}px;top:{cy + (90 if not P else 290) * u}px;font-size:{56 * u}px;font-weight:800;color:{RED};}}")
        sc.js.append(f'tl.fromTo("#{rk}",{{opacity:0,x:0}},{{opacity:1,x:{(sx - bx) * 0.45:.1f},duration:.8,ease:"power2.inOut"}},{at(sid, "seller"):.2f});')
        label(sc, "cap", "Cash on delivery protects the buyer. The seller carries the risk.", L, H * (0.72 if not P else 0.64), size=44, weight=800,
              t=at(sid, "moves"), w=W * 0.88)
    elif sid == "E12":
        fw = W * (0.40 if not P else 0.90)
        footage(sc, "rafi_call", L if not P else L, H * (0.13 if not P else 0.11), fw, H * (0.64 if not P else 0.30), tag="Rafi", tag_t=0.3)
        kx = (L + fw + 60 * u) if not P else L
        label(sc, "q1", "Can ML warn Rafi", kx, H * (0.30 if not P else 0.48), size=72, weight=800, t=at(sid, "machine"), w=(W - kx - L) if not P else W * 0.9)
        label(sc, "q2", "before the parcel leaves?", kx, H * (0.30 if not P else 0.48) + 100 * u, size=72, color=AMB, weight=800, t=at(sid, "leaves"), w=(W - kx - L) if not P else W * 0.9)
    elif sid == "E13":
        import math
        aura(sc)
        cx, cy = (W * 0.5, H * 0.46) if not P else (W * 0.5, H * 0.42)
        R = (330 if not P else 300) * u
        core = sc.id("core")
        sc.add(f'<div id="{core}"><b>Commerce<span style="color:{AMB}">Guard</span></b><small>v2</small></div>',
               f"#{core}{{position:absolute;left:{cx - 150 * u}px;top:{cy - 150 * u}px;width:{300 * u}px;height:{300 * u}px;{glass(sc)}border-radius:50%;"
               f"display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:{40 * u}px;}}#{core} small{{font-size:{30 * u}px;color:{AMB};}}")
        sc.appear(core, 0.2)
        mods = [("1 · Customer voice", "first"), ("2 · Order risk", "second"), ("3 · Delivery risk (Ep 1)", "third")]
        for i, (m, tok) in enumerate(mods):
            a = -math.pi / 2 + i * 2 * math.pi / 3
            el = sc.id(f"md{i}")
            sc.add(f'<div id="{el}" class="mod">{m}</div>', f"#{el}{{left:{cx + R * math.cos(a) * (1.3 if not P else 1)}px;top:{cy + R * math.sin(a)}px;}}")
            sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,scale:.6,xPercent:-50,yPercent:-50}},{{opacity:1,scale:1,xPercent:-50,yPercent:-50,duration:.45,ease:"back.out(1.5)"}},{at(sid, tok):.2f});')
        sc.css.append(f"#root .mod{{position:absolute;white-space:nowrap;padding:{18 * u}px {30 * u}px;font-size:{36 * u}px;font-weight:800;{glass(sc)}}}")
    elif sid == "E14":
        chapter(sc, "MODEL 1 · CUSTOMER VOICE (BANGLADESH)")
        el = sc.id("ds")
        sc.add(f'<div id="{el}" class="dsc"><b>Daraz + Pickaboo reviews</b><span>78,130 reviews · Bangla + English · 2023</span>'
               f'<small>Rashid et al., Mendeley Data · CC BY 4.0</small></div>',
               f"#{el}{{left:{L}px;top:{H * (0.17 if not P else 0.17)}px;width:{W * (0.88)}px;}}")
        sc.appear(el, 0.3)
        sc.css.append(f"#root .dsc{{position:absolute;padding:{24 * u}px {30 * u}px;{glass(sc)}}}#root .dsc b{{display:block;font-size:{48 * u}px;}}"
                      f"#root .dsc span{{display:block;font-size:{34 * u}px;color:{AMB};margin-top:{8 * u}px;}}#root .dsc small{{display:block;font-size:{28 * u}px;color:#8B8A86;margin-top:{8 * u}px;}}")
        capture(sc, [{"cell": 4, "h": b.seg_h(4), "start": at(sid, "78,000", default=4) - 0.6, "end": b.dur(sid),
                      "hl": [("Bangla reviews: 37.1%", at(sid, "bangla"))], "zoom": 1.6}])
    elif sid == "E15":
        chapter(sc, "TRAP 1 · COPIES")
        capture(sc, [{"cell": 5, "h": b.seg_h(5), "start": 0.2, "end": b.dur(sid),
                      "hl": [("13983", max(1.4, at(sid, "14,000", default=at(sid, "copies")))), ("64147", at(sid, "64,000", default=at(sid, "left")))], "zoom": 2.4}])
    elif sid == "E16":
        chapter(sc, "WHAT UNHAPPY CUSTOMERS TALK ABOUT")
        iw = W * (0.56 if not P else 0.90)
        fr = sc.id("tp")
        sc.add(f'<div id="{fr}"><img src="assets/figs/ep2_topics.png"/></div>',
               f"#{fr}{{position:absolute;left:{L}px;top:{H * (0.15 if not P else 0.16)}px;width:{iw}px;padding:{14 * u}px;{glass(sc)}}}#{fr} img{{width:100%;display:block;border-radius:{10 * u}px;background:#fff;}}")
        sc.appear(fr, 0.3)
        kx, ky = (L + iw + 50 * u, H * 0.24) if not P else (L, H * 0.52)
        label(sc, "x15", "15×", kx, ky, size=120, color=RED, weight=800, t=at(sid, "15"))
        label(sc, "x15b", "more talk of returns & refunds", kx, ky + 140 * u, size=36, weight=800, t=at(sid, "15") + 0.2, w=W * (0.30 if not P else 0.9))
        label(sc, "x12", "12×", kx, ky + 260 * u, size=120, color=RED, weight=800, t=at(sid, "12"))
        label(sc, "x12b", "more talk of damaged products", kx, ky + 400 * u, size=36, weight=800, t=at(sid, "12") + 0.2, w=W * (0.30 if not P else 0.9))
    elif sid in ("E17", "E18", "E23"):
        b.code_scene(sc, sid)
    elif sid == "E19":
        chapter(sc, "MODEL 1 · TEST (PRODUCTS NEVER SEEN)")
        y = bars(sc, [("Random guess", 0.170, "#8B8A86", at(sid, "random")), ("All reviews", 0.821, AMB, at(sid, "0.82")),
                      ("Bangla reviews", 0.859, GRN, at(sid, "0.86"))], top=H * (0.30 if not P else 0.30), vmax=0.95, title="PR-AUC (higher is better)", title_t=0.4)
    elif sid == "E20":
        chapter(sc, "MODEL 2 · ORDER RISK (COD MARKET)")
        el = sc.id("ds")
        sc.add(f'<div id="{el}" class="dsc"><b>Pakistan\'s Largest E-Commerce Dataset</b><span>580,286 order items · 2016–2018 · COD market</span>'
               f'<small>No public Bangladeshi order outcomes exist, so this is the closest real data</small></div>',
               f"#{el}{{left:{L}px;top:{H * 0.17}px;width:{W * 0.88}px;}}")
        sc.appear(el, at(sid, "closest"))
        sc.css.append(f"#root .dsc{{position:absolute;padding:{24 * u}px {30 * u}px;{glass(sc)}}}#root .dsc b{{display:block;font-size:{46 * u}px;}}"
                      f"#root .dsc span{{display:block;font-size:{34 * u}px;color:{AMB};margin-top:{8 * u}px;}}#root .dsc small{{display:block;font-size:{28 * u}px;color:#8B8A86;margin-top:{8 * u}px;}}")
        capture(sc, [{"cell": 14, "h": b.seg_h(14), "start": at(sid, "half") - 0.4, "end": b.dur(sid), "hl": [("580286", at(sid, "half") + 1.3)], "zoom": 2.2}])
    elif sid == "E21":
        chapter(sc, "THE SURPRISE")
        y = bars(sc, [("Cash on delivery", 8.1, GRN, at(sid, "8%")), ("Paid online", 57.8, RED, at(sid, "58%"))], top=H * 0.32,
                 unit="%", fmt="{:.1f}", vmax=65, title="Order items cancelled", title_t=at(sid, "cancelled"))
        label(sc, "n", "many online cancellations are simply abandoned payments", L, y + 20 * u, size=34, color="#B8B5AE", t=at(sid, "abandoned"), w=W * 0.88)
    elif sid == "E22":
        chapter(sc, "BUT…")
        y = bars(sc, [("Cash on delivery", 20.2, RED, at(sid, "20%")), ("Paid online", 4.2, GRN, at(sid, "4%"))], top=H * 0.32,
                 unit="%", fmt="{:.1f}", vmax=25, title="Order items refunded", title_t=at(sid, "refunded"))
        el = sc.id("x5")
        sc.add(f'<div id="{el}">≈ 5× MORE REFUNDS · RAFI\'S PROBLEM</div>',
               f"#{el}{{position:absolute;left:{L}px;top:{y + 30 * u}px;border:{6 * u}px solid {RED};color:{RED};font-weight:800;font-size:{(56 if not P else 42) * u}px;"
               f"padding:{10 * u}px {26 * u}px;border-radius:{10 * u}px;}}")
        sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,scale:1.4}},{{opacity:1,scale:1,duration:.25,ease:"power4.in"}},{at(sid, "exactly"):.2f});')
    elif sid == "E24":
        chapter(sc, "MODEL 2 · TEST (USED ONCE)")
        y = bars(sc, [("Cancel · random", 0.455, "#8B8A86", at(sid, "0.46")), ("Cancel · model", 0.789, AMB, at(sid, "0.79")),
                      ("Refund · random", 0.172, "#8B8A86", at(sid, "0.17")), ("Refund · model", 0.349, RED, at(sid, "0.35"))],
                 top=H * (0.28 if not P else 0.26), vmax=0.9, title="PR-AUC", title_t=at(sid, "cancellation"))
    elif sid == "E25":
        chapter(sc, "THE COMMERCEGUARD ENGINE")
        iw = W * (0.54 if not P else 0.9)
        fr = sc.id("lc")
        sc.add(f'<div id="{fr}"><img src="assets/figs/ep2_loss_curve.png"/></div>',
               f"#{fr}{{position:absolute;left:{L}px;top:{H * (0.14 if not P else 0.34)}px;width:{iw}px;padding:{14 * u}px;{glass(sc)}}}#{fr} img{{width:100%;display:block;border-radius:{10 * u}px;background:#fff;}}")
        sc.appear(fr, at(sid, "ranks"))
        kx, ky = (L + iw + 60 * u, H * 0.18) if not P else (L, H * 0.13)
        label(sc, "f", "expected loss = P(cancel) × cost + P(refund) × value × 15%", kx, ky, size=30, color="#B8B5AE", mono=True, t=at(sid, "expected"), w=(W - kx - L) if not P else W * 0.9)
        label(sc, "a", "Top 10%", kx, ky + (130 if not P else 90) * u, size=(100 if not P else 80), color=AMB, weight=800, t=at(sid, "10%"))
        label(sc, "a2", "of order items → 51% of the loss", kx, ky + (250 if not P else 190) * u, size=44, weight=800, t=at(sid, "51%"), w=(W - kx - L) if not P else W * 0.9)
        if not P:
            label(sc, "c", "costs are illustrative inputs", kx, ky + 420 * u, size=30, color="#8B8A86", t=at(sid, "51%") + 0.5)
    elif sid == "E26":
        (fx, fy, fw, fh), _ = layout(sc)
        hw = (fw - 20 * u) / 2 if not P else fw
        footage(sc, "nadia", fx, fy, hw if not P else fw, fh if not P else fh / 2 - 10 * u, tag="Nadia", tag_t=0.2)
        footage(sc, "rafi_call", fx + (hw + 20 * u if not P else 0), fy + (0 if not P else fh / 2 + 10 * u), hw if not P else fw, fh if not P else fh / 2 - 10 * u, tag="Rafi", tag_t=0.3)
        kx, ky = (W * 0.64, H * 0.30) if not P else (L, H * 0.46)
        label(sc, "k", "Same chat.", kx, ky, size=72, weight=800, t=0.4, w=W * (0.32 if not P else 0.9))
        label(sc, "k2", "Now CommerceGuard reads it.", kx, ky + 100 * u, size=64, color=AMB, weight=800, t=at(sid, "read"), w=W * (0.32 if not P else 0.9))
    elif sid in ("E27", "E28"):
        aura(sc, (RED, AMB) if sid == "E27" else (GRN, AMB))
        sc.css.append(FONT)
        rows = [("m1", "first"), ("m2", "waiting"), ("m3", "fake"), ("m4", "refund")] if sid == "E27" else [("m5", "0%")]
        chapter(sc, "COMMERCEGUARD READS THE CHAT" if sid == "E27" else "A HAPPY CUSTOMER")
        y = H * (0.17 if not P else 0.17)
        bw_ = W * (0.56 if not P else 0.90)
        for i_, (k, tok) in enumerate(rows):
            side, bn, en, s_ = MSG[k]
            col = GRN if s_ < 30 else (AMB if s_ < 70 else RED)
            t_ = at(sid, tok, default=at(sid, "roman", default=1.0)) if sid == "E28" else at(sid, tok)
            bub, trk, fil, num = sc.id(f"rb{i_}"), sc.id(f"rt{i_}"), sc.id(f"rf{i_}"), sc.id(f"rn{i_}")
            mx, my = (L + bw_ + 40 * u, y + 30 * u) if not P else (L, y + 150 * u)
            mw = (W - mx - L) if not P else W * 0.62
            sc.add(f'<div id="{bub}" class="rbub"><div class="bn">{escape(bn)}</div><div class="en">{escape(en)}</div></div>'
                   f'<div id="{trk}" class="rtrk"><div id="{fil}" class="rfil"></div></div><div id="{num}" class="rnum">{s_}% unhappy</div>',
                   f"#{bub}{{left:{L}px;top:{y}px;width:{bw_}px;}}#{trk}{{left:{mx}px;top:{my}px;width:{mw * 0.62}px;}}"
                   f"#{fil}{{width:{max(2, s_)}%;background:{col};}}#{num}{{left:{mx + mw * 0.62 + 20 * u}px;top:{my - 14 * u}px;color:{col};}}")
            sc.js.append(f'tl.fromTo("#{bub}",{{opacity:0,y:{20 * u}}},{{opacity:1,y:0,duration:.4,ease:"expo.out"}},{0.2 + i_ * 0.25:.2f});')
            sc.js.append(f'tl.fromTo("#{trk}",{{opacity:0}},{{opacity:1,duration:.3}},{0.4 + i_ * 0.25:.2f});')
            sc.js.append(f'tl.fromTo("#{fil}",{{scaleX:0}},{{scaleX:1,duration:.7,ease:"expo.out"}},{t_:.2f});')
            sc.js.append(f'tl.fromTo("#{num}",{{opacity:0}},{{opacity:1,duration:.25}},{t_ + 0.3:.2f});')
            sfx(sid, t_, "click-soft", 0.3)
            y += (150 if not P else 250) * u
        sc.css.append(f"#root .rbub{{position:absolute;padding:{16 * u}px {24 * u}px;background:#25262A;border-radius:{26 * u}px {26 * u}px {26 * u}px {6 * u}px;}}"
                      f"#root .rbub .bn{{font-family:'NotoBN',Inter,sans-serif;font-size:{36 * u}px;line-height:1.45;}}#root .rbub .en{{font-size:{28 * u}px;color:#9C9A94;}}"
                      f"#root .rtrk{{position:absolute;height:{22 * u}px;border-radius:{11 * u}px;background:rgba(243,240,232,.12);overflow:hidden;}}"
                      f"#root .rfil{{height:100%;border-radius:{11 * u}px;transform-origin:left center;}}"
                      f"#root .rnum{{position:absolute;font-size:{40 * u}px;font-weight:800;white-space:nowrap;}}")
        if sid == "E27":
            t = at(sid, "94")
            sfx(sid, max(0.1, t - 2.0), "riser", 0.22); sfx(sid, t + 0.05, "impact-bass-1", 0.4)
        else:
            label(sc, "n1", "Never trained on these messages.", L, H * (0.48 if not P else 0.50), size=52, weight=800, t=at(sid, "never"), w=W * 0.88)
            label(sc, "n2", "It learned from real reviews.", L, H * (0.48 if not P else 0.50) + 90 * u, size=52, color=GRN, weight=800, t=at(sid, "learned"), w=W * 0.88)
    elif sid == "E29":
        aura(sc)
        label(sc, "h", "What Rafi can do, by risk", L, H * 0.14, size=64, weight=800, t=0.3, w=W * 0.88)
        acts = [("📞  Call to confirm", "call"), ("৳  Ask a small advance", "advance"), ("📷  Send clearer photos", "photo")]
        for i, (tx, tok) in enumerate(acts):
            el = sc.id(f"ac{i}")
            x, y = (L + i * W * 0.30, H * 0.36) if not P else (L, H * 0.30 + i * 170 * u)
            sc.add(f'<div id="{el}" class="act">{tx}</div>', f"#{el}{{left:{x}px;top:{y}px;width:{W * (0.27 if not P else 0.88)}px;}}")
            sc.js.append(f'tl.fromTo("#{el}",{{opacity:0,y:{30 * u}}},{{opacity:1,y:0,duration:.5,ease:"expo.out"}},{at(sid, tok):.2f});')
        sc.css.append(f"#root .act{{position:absolute;padding:{30 * u}px {26 * u}px;font-size:{40 * u}px;font-weight:800;{glass(sc)}font-family:Inter,'NotoBN',sans-serif;}}")
        sc.css.append(FONT)
        label(sc, "f", "Small steps, decided by risk, not by guesswork.", L, H * (0.62 if not P else 0.66), size=48, color=AMB, weight=800, t=at(sid, "small"), w=W * 0.88)
    elif sid == "E30":
        chapter(sc, "HONEST LIMITS")
        lim = [("Reviews are a proxy for complaints", "proxy"), ("Order data is from Pakistan, not Bangladesh", "pakistan"), ("Costs are examples", "costs")]
        for i, (tx, tok) in enumerate(lim):
            label(sc, f"l{i}", "· " + tx, L, H * 0.22 + i * 90 * u, size=46, weight=700, t=at(sid, tok), w=W * 0.88)
        label(sc, "n", "Next: real data from Bangladeshi sellers", L, H * (0.60 if not P else 0.56), size=60, color=AMB, weight=800, t=at(sid, "real"), w=W * 0.88)
    elif sid == "E31":
        el = sc.id("logo")
        sc.add(f'<div id="{el}"><span>Commerce</span><span style="color:{AMB}">Guard</span></div>',
               f"#{el}{{position:absolute;left:0;right:0;top:{H * 0.28}px;text-align:center;font-weight:800;font-size:{(140 if not P else 112) * u}px;letter-spacing:-0.04em;}}")
        sc.appear(el, 0.3)
        sweep(sc, el, 1.0)
        label(sc, "v", "Version 2 · from one model to a system", W / 2, H * 0.28 + 190 * u, size=40, color=AMB, t=at(sid, "two", default=1.5), anchor="center", weight=800)
        label(sc, "t", "Predict risk. Understand behavior. Reduce preventable losses.", W / 2, H * 0.28 + 270 * u, size=34, t=at(sid, "predict"), anchor="center", w=None if not P else None)
        label(sc, "s", "One step at a time. One model at a time.", W / 2, H * (0.66 if not P else 0.60), size=44, t=at(sid, "step"), anchor="center", weight=800)
    return sc


ORDER = [f"E{i:02d}" for i in range(1, 32)]
b.S = S2
b.ORDER = ORDER
b.REELS = {1: ("THE STORY & THE DATA", ORDER[:17]), 2: ("THE MODELS & THE ENGINE", ORDER[17:])}
NPARTS = len(b.REELS)


def outro2(rid, W, H, reel):
    sc = b.Scene(rid, W, H); u = sc.u; L = W * 0.07
    n = int(rid[1])
    if n < NPARTS:
        label(sc, "nx", f"NEXT · PART {n + 1}/{NPARTS}", L, H * 0.30, size=40, color=AMB, t=0.2, weight=800)
        label(sc, "hk", b.OUTROS[rid]["card"], L, H * 0.36, size=70, t=0.4, weight=800, w=W - 2 * L)
    else:
        label(sc, "nx", "FULL EPISODE ON YOUTUBE", L, H * 0.30, size=44, color=AMB, t=0.2, weight=800)
        label(sc, "hk", "▶ @csfunda.official", L, H * 0.36, size=84, t=0.4, weight=800)
    label(sc, "h1", "Follow CS Funda", L, H * 0.62, size=48, t=b.dur(rid) - 0.1, weight=800)
    label(sc, "h2", "IG @csfunda.official_  ·  YT @csfunda.official", L, H * 0.62 + 70 * u, size=34, color="#B8B5AE", t=b.dur(rid) - 0.1, mono=True, w=W - 2 * L)
    return sc


def badge2(out, W, H, reel, total):
    title = b.REELS[reel][0]; u = min(W, H) / 1080; n = reel; N = NPARTS
    seg = (W * 0.86 - (N - 1) * 8 * u) / N
    bars_ = "".join(f'<div class="pg" style="left:{W * 0.07 + i * (seg + 8 * u)}px;{"background:" + AMB if i < n else ""}"></div>' for i in range(N))
    (out / "compositions/badge.html").write_text(f"""<template>
<style>#root{{position:absolute;inset:0;}}
#root #bd{{position:absolute;left:{W * 0.07}px;top:{H * 0.05}px;font-family:Inter,sans-serif;font-weight:800;color:#F3F0E8;font-size:{34 * u}px;}}
#root #bd b{{color:{AMB}}}
#root .pg{{position:absolute;top:{H * 0.05 + 54 * u}px;height:{6 * u}px;width:{seg}px;border-radius:3px;background:rgba(243,240,232,.25);}}</style>
<div id="root" data-composition-id="badge" data-width="{W}" data-height="{H}">
<div id="bd">CommerceGuard Ep 2 · <b>PART {n}/{N}</b> · {title}</div>{bars_}
</div><script>const tl=gsap.timeline({{paused:true}});tl.set("#bd",{{opacity:1}},0);window.__timelines["badge"]=tl;</script></template>""")
    return (f'<div id="badge" data-composition-id="badge" data-composition-src="compositions/badge.html" data-start="0" data-duration="{total}" '
            f'data-track-index="6" data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index:6"></div>')


b.outro = outro2
b.part_badge = badge2


def add_extra_audio(out):
    idx = out / "index.html"
    h = idx.read_text()
    starts = {s.upper(): float(a) for s, a in re.findall(r'compositions/(e\d+)\.html" data-start="([\d.]+)"', h)}
    lines = []
    for sid, evs in EXTRA.items():
        if sid not in starts:
            continue
        for k, (t, name, vol) in enumerate(evs):
            lines.append(f'<audio id="x-{sid.lower()}-{k}" class="clip" src="assets/sfx/{name}.mp3" data-start="{starts[sid] + t:.2f}" '
                         f'data-duration="{b.SFXLEN[name]}" data-track-index="{30 + k % 6}" data-volume="{vol}"></audio>')
    h = h.replace("</div>\n<script>", "\n".join(lines) + "\n</div>\n<script>", 1)
    idx.write_text(h)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reels":
        b.LEAD, b.TAIL = 0.2, 0.25
        import shutil
        shutil.rmtree(EP2 / "reels", ignore_errors=True)
        for n, (_, ids) in b.REELS.items():
            EXTRA.clear()
            out = EP2 / f"reels/part{n}"
            b.project(out, 1080, 1920, ids + [f"R{n}"], reel=n)
            add_extra_audio(out)
    else:
        b.project(HERE, 1920, 1080, ORDER)
        add_extra_audio(HERE)
