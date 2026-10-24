#!/usr/bin/env python3
"""Renders assets/contributions.svg: a contribution calendar in the profile palette.

Usage:
  GH_TOKEN=... GH_LOGIN=siedaa python .github/scripts/contributions.py   # real data (used by the workflow)
  python .github/scripts/contributions.py --sample                       # fake data, for design previews
  python .github/scripts/contributions.py --empty                        # empty grid placeholder

Text is drawn from outlined glyphs (glyphs.json) so the SVG looks the same everywhere.
Stdlib only.
"""
import datetime, json, os, random, re, sys, urllib.request
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("CONTRIB_OUT") or os.path.join(HERE, "..", "..", "assets", "contributions.svg")

PINE0, PINE3 = "#2d2f33", "#585b61"
LICHEN, STONE, ROSE = "#a3a5aa", "#eeeff0", "#d99a96"
LEVELS = ["#3f4146", "#665056", "#8f6169", "#bf8087", "#e4a8a3"]

G = json.load(open(os.path.join(HERE, "glyphs.json")))
FONTID = {"MM": "nunito", "BG6": "nunito-bold"}


def wrap_path(d, indent, width=96):
    segs = re.findall(r"[A-Za-z][^A-Za-z]*", d)
    lines, cur = [], ""
    for sg in segs:
        sg = sg.strip()
        if cur and len(cur) + len(sg) + 1 > width:
            lines.append(cur); cur = sg
        else:
            cur = (cur + " " + sg).strip() if cur else sg
    if cur: lines.append(cur)
    return ("\n" + indent).join(lines)


def pretty(svg, step="  "):
    toks = re.findall(r"<!--.*?-->|<[^>]+>|[^<]+", svg, re.S)
    out, depth, i = [], 0, 0
    while i < len(toks):
        t = toks[i]; ind = step * depth
        if t.startswith("<!--"):
            out.append(ind + t)
        elif t.startswith("</"):
            depth -= 1; out.append(step * depth + t)
        elif t.startswith("<"):
            m = re.search(r' d="([^"]{100,})"', t)
            if m:
                t = t.replace(m.group(0), ' d="' + wrap_path(m.group(1), ind + step * 2) + '"')
            nxt = toks[i + 1] if i + 1 < len(toks) else ""
            if not t.endswith("/>") and nxt and not nxt.startswith("<") and i + 2 < len(toks) and toks[i + 2].startswith("</"):
                out.append(ind + t + nxt + toks[i + 2]); i += 2
            else:
                out.append(ind + t)
                if not t.endswith("/>"): depth += 1
        i += 1
    return "\n".join(out) + "\n"



def width(font, text, size, ls=0.0):
    f = G[font]; k = size / f["upem"]
    return sum(f["g"][c][0] * k + ls for c in text) - ls


class Doc:
    def __init__(self): self.defs, self.body = {}, []

    def text(self, x, y, text, font, size, fill, ls=0.0, anchor="start"):
        f = G[font]; k = size / f["upem"]
        w = width(font, text, size, ls)
        cx = x - (w if anchor == "end" else w / 2 if anchor == "middle" else 0)
        out = []
        for c in text:
            adv, d = f["g"][c]
            if d:
                key = f"{FONTID[font]}-{c if c.isalnum() else 'U%04X' % ord(c)}"
                self.defs[key] = d
                out.append(f'<use href="#{key}" transform="translate({cx:.2f} {y:.2f}) scale({k:.5f} {-k:.5f})" fill="{fill}"/>')
            cx += adv * k + ls
        self.body.append(f'<!-- text: {text} -->')
        self.body.append(f'<g aria-label="{escape(text, quote=True)}">' + "".join(out) + "</g>")
        return w


def fetch(login, token):
    q = ("query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{"
         "totalContributions weeks{contributionDays{date contributionCount}}}}}}")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "contrib-svg"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in cal["weeks"]]
    return weeks, cal["totalContributions"]


def sample():
    rnd = random.Random(7)
    end = datetime.date(2026, 10, 24)
    start = end - datetime.timedelta(days=364)
    start -= datetime.timedelta(days=(start.weekday() + 1) % 7)  # back to Sunday
    weeks, d = [], start
    while d <= end:
        wk = []
        for _ in range(7):
            if d <= end:
                busy = 0.15 + 0.6 * (d.month in (7, 8, 9, 10))
                n = 0 if rnd.random() > busy else int(rnd.expovariate(1 / 4)) + 1
                wk.append((d.isoformat(), n))
            d += datetime.timedelta(days=1)
        weeks.append(wk)
    return weeks, sum(n for w in weeks for _, n in w)


def empty():
    weeks, total = sample()
    return [[(d, 0) for d, _ in w] for w in weeks], 0


def render(weeks, total):
    W = 1000
    nw = len(weeks)
    x0, right = 66, 34
    pitch = (W - x0 - right) / nw
    cell = pitch - 3.6
    y0 = 92
    H = int(y0 + 7 * pitch + 64)
    counts = sorted(n for w in weeks for _, n in w if n)
    def q(p): return counts[min(len(counts) - 1, int(len(counts) * p))] if counts else 1
    t1, t2, t3 = q(.25), q(.5), q(.75)
    def level(n): return 0 if n == 0 else 1 if n <= t1 else 2 if n <= t2 else 3 if n <= t3 else 4

    d = Doc()
    d.body.append('<!-- Panel background and border -->')
    d.body.append(f'<rect width="{W}" height="{H}" rx="20" fill="{PINE0}"/>')
    d.body.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="19.5" fill="none" stroke="{PINE3}"/>')
    # title
    n_txt = f"{total:,}"
    w1 = d.text(32, 46, n_txt, "BG6", 20, ROSE)
    d.text(32 + w1 + 8, 46, "contributions in the last year", "BG6", 20, STONE)
    # month labels
    last_label_col, last_month = -9, None
    for i, wk in enumerate(weeks):
        if not wk: continue
        day = datetime.date.fromisoformat(wk[0][0])
        if day.month != last_month:
            if i - last_label_col >= 3 and not (i == 0 and len(weeks) > 1 and
                    datetime.date.fromisoformat(weeks[1][0][0]).month != day.month):
                d.text(x0 + i * pitch, 82, day.strftime("%b"), "MM", 12, LICHEN)
                last_label_col = i
            last_month = day.month
    # weekday labels (Sun-first rows)
    for row, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        d.text(32, y0 + row * pitch + cell * 0.8, lab, "MM", 11, LICHEN)
    # cells
    d.body.append('<!-- Calendar cells: one square per day, shade = number of contributions (hover for the exact count) -->')
    for i, wk in enumerate(weeks):
        for j, (date, n) in enumerate(wk):
            x, y = x0 + i * pitch, y0 + j * pitch
            tip = f"{n} contribution{'s' if n != 1 else ''} on {date}"
            d.body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="3.4" '
                          f'fill="{LEVELS[level(n)]}"><title>{escape(tip)}</title></rect>')
    # legend
    d.body.append('<!-- Legend -->')
    ly = y0 + 7 * pitch + 28
    lx = W - 32
    lw = width("MM", "More", 12)
    d.text(lx, ly + 10, "More", "MM", 12, LICHEN, anchor="end")
    lx -= lw + 10
    for c in reversed(LEVELS):
        lx -= cell + 4
        d.body.append(f'<rect x="{lx:.1f}" y="{ly:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="3.4" fill="{c}"/>')
    d.text(lx - 10, ly + 10, "Less", "MM", 12, LICHEN, anchor="end")

    defs = "".join(f'<path id="{k}" d="{v}"/>' for k, v in d.defs.items())
    desc = f"Contribution calendar for the last year: {total} contributions."
    return pretty(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
                  f'aria-labelledby="t d"><title id="t">GitHub contributions</title><desc id="d">{escape(desc)}</desc>'
                  f'<defs><!-- Glyph outlines used by the labels -->{defs}</defs>{"".join(d.body)}</svg>')


def render_activity(weeks, total):
    """Line graph of contributions per week over the last year."""
    W, H = 1000, 300
    x0, x1, y0, y1 = 70, W - 40, 84, H - 52
    sums = [sum(n for _, n in wk) for wk in weeks]
    top = max(max(sums), 4)
    step = 5 if top <= 25 else 10 if top <= 60 else 20 if top <= 120 else 50
    top = ((top + step - 1) // step) * step
    px = lambda i: x0 + i * (x1 - x0) / max(1, len(sums) - 1)
    py = lambda v: y1 - v * (y1 - y0) / top

    d = Doc()
    d.body.append('<!-- Panel background and border -->')
    d.body.append(f'<rect width="{W}" height="{H}" rx="20" fill="{PINE0}"/>')
    d.body.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="19.5" fill="none" stroke="{PINE3}"/>')
    d.text(32, 46, "Contribution activity", "BG6", 20, STONE)
    d.text(W - 32, 46, "contributions per week", "MM", 13, LICHEN, anchor="end")

    d.body.append('<!-- Horizontal grid lines and value labels -->')
    for v in range(0, top + 1, step):
        d.body.append(f'<path d="M{x0} {py(v):.1f} H{x1}" stroke="{PINE3}" stroke-width="1" stroke-dasharray="2 5" opacity=".7"/>')
        d.text(x0 - 12, py(v) + 4, str(v), "MM", 11, LICHEN, anchor="end")

    d.body.append('<!-- Month labels -->')
    last_m, last_i = None, -9
    for i, wk in enumerate(weeks):
        if not wk: continue
        day = datetime.date.fromisoformat(wk[0][0])
        if day.month != last_m and i - last_i >= 3:
            d.text(px(i), y1 + 26, day.strftime("%b"), "MM", 12, LICHEN, anchor="middle")
            last_i = i
        last_m = day.month

    pts = [(px(i), py(v)) for i, v in enumerate(sums)]
    line = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    d.body.append('<!-- Area under the line, the line itself and a dot for each week -->')
    d.body.append(f'<path d="{line} L{x1} {y1} L{x0} {y1} Z" fill="{ROSE}" opacity=".13"/>')
    d.body.append(f'<path d="{line}" fill="none" stroke="{ROSE}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>')
    for (x, y), v, wk in zip(pts, sums, weeks):
        d.body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{PINE0}" stroke="{ROSE}" stroke-width="1.6">'
                      f'<title>{v} contribution{"s" if v != 1 else ""}, week of {wk[0][0]}</title></circle>')

    defs = "".join(f'<path id="{k}" d="{v}"/>' for k, v in d.defs.items())
    desc = f"Line graph of weekly contributions over the last year: {total} in total."
    return pretty(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
                  f'aria-labelledby="t d"><title id="t">GitHub contribution activity</title><desc id="d">{escape(desc)}</desc>'
                  f'<defs><!-- Glyph outlines used by the labels -->{defs}</defs>{"".join(d.body)}</svg>')


def main():
    if "--sample" in sys.argv: weeks, total = sample()
    elif "--empty" in sys.argv: weeks, total = empty()
    else:
        token, login = os.environ.get("GH_TOKEN"), os.environ.get("GH_LOGIN", "siedaa")
        if not token: sys.exit("GH_TOKEN is required (or pass --sample / --empty)")
        weeks, total = fetch(login, token)
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    with open(OUT, "w") as fh: fh.write(render(weeks, total))
    act_out = os.path.join(os.path.dirname(os.path.abspath(OUT)), "activity.svg")
    with open(act_out, "w") as fh: fh.write(render_activity(weeks, total))
    print("wrote", OUT, "total", total)


if __name__ == "__main__":
    main()
