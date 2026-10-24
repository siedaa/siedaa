#!/usr/bin/env python3
"""v2 of the profile README assets. Palette: pine, lichen, stone, dusty rose."""
import json, math, os, random, shutil, subprocess, sys
SCR = os.path.dirname(os.path.abspath(__file__))
OUT2 = f"{SCR}/out2"
sys.argv = [sys.argv[0], OUT2]
sys.path.insert(0, SCR)
import build_readme as B          # reuses Font / Svg / text-to-outline helpers
from build_readme import FONT, tw, fit, wrap, Svg, arrow
from fontTools.pens.svgPathPen import SVGPathPen

PINE0, PINE1, PINE2, PINE3 = "#2d2f33", "#383a3f", "#43464b", "#585b61"   # warm charcoal (names kept from v1)
LICHEN, MIST, STONE = "#a3a5aa", "#c9cbcf", "#eeeff0"
ROSE, ROSE_BG, ROSE_DK = "#d99a96", "#3a2f33", "#a8505a"
PAPER, PAPER_LN, INKT, INK_SOFT, INK_MUTE = "#e7e8ea", "#c8cacd", "#25262a", "#3f4146", "#6a6c72"
ICONS = json.load(open(f"{SCR}/icons.json"))


def lum(hexc):
    r, g, b = [int(hexc[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def icon(s, slug, x, y, size=18, on="dark"):
    """Draw a simple-icons logo in its brand colour; colours that vanish on the background fall back."""
    ic = ICONS[slug]
    col = "#" + ic["hex"]
    if on == "dark" and lum(ic["hex"]) < 0.06:
        col = STONE
    if on == "light":
        if lum(ic["hex"]) > 0.7:
            col = INKT
        elif lum(ic["hex"]) > 0.35:       # pale brand colours: deepen so they read on paper
            rgb = [int(ic["hex"][i:i + 2], 16) for i in (0, 2, 4)]
            col = "#%02x%02x%02x" % tuple(int(c * 0.62) for c in rgb)
    k = size / 24
    s.raw(f'<path d="{ic["path"]}" transform="translate({x:.1f} {y:.1f}) scale({k:.4f})" fill="{col}"/>')


# =====================================================================
# HERO
# =====================================================================
def contours(s, cx, cy, n=11, r0=26, step=19, seed=3):
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6.28) for _ in range(4)]
    for i in range(n):
        r = r0 + i * step
        pts = []
        for a in range(0, 361, 6):
            t = math.radians(a)
            wob = (1 + 0.10 * math.sin(2 * t + ph[0] + i * .15) + 0.07 * math.sin(3 * t + ph[1])
                   + 0.045 * math.sin(5 * t + ph[2] + i * .3))
            pts.append((cx + r * 1.32 * wob * math.cos(t), cy + r * wob * math.sin(t)))
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"
        s.raw(f'<path d="{d}" fill="none" stroke="{PINE2 if i % 4 else PINE3}" stroke-width="1.1" '
              f'stroke-linejoin="round" opacity="{max(.25, 1 - i * .07):.2f}"/>')


def node(s, cx, cy, w, label, hot=False):
    x, y = cx - w / 2, cy - 17
    s.raw(f'<rect x="{x:.1f}" y="{y}" width="{w}" height="34" rx="11" fill="{ROSE_BG if hot else PINE1}" '
          f'stroke="{ROSE if hot else PINE3}" stroke-width="{1.4 if hot else 1}"/>')
    s.text(cx, cy + 5, label, "MM", 13.5, ROSE if hot else STONE, anchor="middle")


def edge(s, d, ex, ey):
    s.raw(f'<path d="{d}" fill="none" stroke="{LICHEN}" stroke-width="1.4" stroke-linecap="round"/>')
    s.raw(f'<path d="M{ex-4.5} {ey-8} L{ex} {ey} L{ex+4.5} {ey-8} Z" fill="{LICHEN}"/>')


def hero():
    W, H = 1000, 364
    s = Svg(W, H, "Hi, I’m Maha, learning backend and agentic AI by building things",
            "Computer Science student at FAST-NUCES. I build LLM pipelines, then try to break them. "
            "Decorative graph: query, retrieve, guard, answer.")
    s.comment("Clip shape so the contour lines stay inside the rounded panel")
    s.raw(f'<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="22"/></clipPath></defs>')
    s.comment("Panel background, topographic contour lines and border")
    s.raw(f'<rect width="{W}" height="{H}" rx="22" fill="{PINE0}"/>')
    s.raw('<g clip-path="url(#c)">')
    contours(s, 830, 190)
    s.raw(f'<ellipse cx="830" cy="190" rx="280" ry="230" fill="{PINE0}" opacity=".35"/>')
    s.raw("</g>")
    s.raw(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="21.5" fill="none" stroke="{PINE3}"/>')

    s.comment("Headline and intro lines")
    lines = [[("Hi, I’m Maha, learning", "IS", STONE)],
             [("backend & agentic AI", "IS", STONE)],
             [("by building things.", "IS", ROSE)]]
    size = min(fit(l, 540, 56) for l in lines)
    y = 98
    for l in lines:
        s.runs(48, y, l, size); y += size * 1.2
    for i, ln in enumerate(["CS student at FAST-NUCES.", "I build LLM pipelines, then try to break them."]):
        s.text(52, y + 6 + i * 29, ln, "BG", 19.5, MIST)

    # decorative agent graph: query -> retrieve -> guard -> answer
    s.comment("Decorative agent graph: query, retrieve, guard, answer")
    d = 22
    node(s, 706, 78 + d, 100, "query")
    node(s, 862, 128 + d, 116, "retrieve")
    node(s, 722, 204 + d, 100, "guard", hot=True)
    node(s, 862, 268 + d, 108, "answer")
    edge(s, f"M756 {78+d} C 830 {78+d}, 862 {86+d}, 862 {110+d}", 862, 111 + d)
    edge(s, f"M804 {128+d} C 740 {128+d}, 722 {152+d}, 722 {185+d}", 722, 187 + d)
    edge(s, f"M772 {204+d} C 840 {204+d}, 862 {226+d}, 862 {249+d}", 862, 251 + d)
    s.save("hero.svg")


# =====================================================================
# PROJECT CARDS
# =====================================================================
def pill(s, x, y, label, slug=None):
    w = tw([(label, "MM", "")], 9.5, 0.5)
    pw = w + 24 + (22 if slug else 0)
    s.raw(f'<rect x="{x:.1f}" y="{y}" width="{pw:.1f}" height="28" rx="14" fill="{PINE0}" stroke="{PINE3}"/>')
    tx = x + 12
    if slug:
        icon(s, slug, x + 11, y + 7, 14); tx += 21
    s.text(tx, y + 18, label, "MM", 9.5, STONE, ls=0.5)
    return pw


def squiggle(x0, x1, y, seed=1, amp=1.8, step=13):
    rnd = random.Random(seed)
    pts = [(x0, y)]
    x = x0
    while x < x1:
        x += step; pts.append((min(x, x1), y + rnd.uniform(-amp, amp)))
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(1, len(pts) - 1):
        mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
        d += f" Q{pts[i][0]:.1f} {pts[i][1]:.1f} {mx:.1f} {my:.1f}"
    d += f" T{pts[-1][0]:.1f} {pts[-1][1]:.1f}"
    return d


def card(name, idx, tag, t1, t2, big, big_label, desc, stack, alt, angle=-0.8, seed=1):
    W, H = 500, 416
    s = Svg(W, H, alt, desc)
    cx0, cy0, cw, ch = 16, 24, 468, 372
    p = 30
    L = cx0 + p
    s.raw('<defs><filter id="sh" x="-10%" y="-10%" width="120%" height="125%">'
          '<feGaussianBlur stdDeviation="7"/></filter></defs>')
    s.comment("Index card, tilted slightly: shadow, paper, tape, arrow, title, key figure, description, stack")
    s.raw(f'<g transform="rotate({angle} {W/2} {H/2})">')
    s.raw(f'<rect x="{cx0+2}" y="{cy0+9}" width="{cw}" height="{ch}" rx="5" fill="#000" opacity=".38" filter="url(#sh)"/>')
    s.raw(f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" rx="5" fill="{PAPER}" stroke="{PAPER_LN}"/>')
    s.raw(f'<g transform="translate({W/2+ (seed%3-1)*26} {cy0+1}) rotate({-3 + seed*1.5})">'
          f'<path d="M-50 -14 L50 -14 L47 -7 L50 0 L47 7 L50 14 L-50 14 L-47 7 L-50 0 L-47 -7 Z" fill="{ROSE}" opacity=".82"/>'
          f'<path d="M-44 -6 H44" stroke="#fff" stroke-opacity=".25"/></g>')
    arrow(s, cx0 + cw - p - 12, cy0 + 40, 12, INKT, 1.7)
    ty = cy0 + 76
    s.comment("Title")
    s.text(L, ty, t1, "IS", 33, INKT)
    s.text(L, ty + 41, t2, "IS", 33, INKT)
    ky = cy0 + 182
    s.comment("Key figure")
    x = L
    for part in big:
        if part == "->":
            s.raw(f'<path d="M{x+2} {ky-15} H{x+28} M{x+20} {ky-23} L{x+28} {ky-15} L{x+20} {ky-7}" fill="none" '
                  f'stroke="{INK_MUTE}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
            x += 38
        else:
            x += s.text(x, ky, part, "IS", 42, ROSE_DK) + 4
    s.text(x + 10, ky - 4, big_label, "BG", 14, INK_MUTE)
    lines = wrap(desc, "BG", 14.5, cw - 2 * p)
    s.comment("Description")
    dy = cy0 + 222
    for i, ln in enumerate(lines):
        s.text(L, dy + i * 22, ln, "BG", 14.5, INK_SOFT)
    footer_y = cy0 + ch - 24
    assert dy + (len(lines) - 1) * 22 < footer_y - 32, (name, "desc too long", len(lines))
    s.raw(f'<path d="M{L} {footer_y-26} H{cx0+cw-p}" stroke="{PAPER_LN}" stroke-dasharray="2 4" stroke-width="1.4" stroke-linecap="round"/>')
    stack_runs = [("Built with   ", "BG6", ROSE_DK), (stack, "BG", INK_SOFT)]
    assert tw(stack_runs, 13.5) <= cw - 2 * p, (name, "stack line too long")
    s.runs(L, footer_y, stack_runs, 13.5)
    s.raw("</g>")
    s.save(name)


# =====================================================================
# STACK TILES (logos)
# =====================================================================
STACK = [
    ("Languages", [("Python", "python"), ("JavaScript", "javascript"), ("C++", "cplusplus"), ("C", "c"),
                   ("C#", None), ("Java", "openjdk"), ("SQL", None)]),
    ("AI & LLM", [("LangGraph", "langgraph"), ("LangChain", "langchain"), ("MCP", "modelcontextprotocol"),
                  ("PyTorch", "pytorch"), ("Gemini", "googlegemini"), ("Claude API", "claude"),
                  ("OpenAI API", None), ("Groq", None), ("Multimodal RAG", None)]),
    ("AI Security", [("Prompt-injection testing", None), ("Jailbreak testing", None), ("LLM-as-judge evals", None),
                     ("Regex + ML guardrails", None), ("CWE classification", None), ("CVSS-style scoring", None)]),
    ("Backend & APIs", [("FastAPI", "fastapi"), ("Flask", "flask"), ("Django", "django"), ("Node.js", "nodedotjs"),
                        ("SQLModel", None), ("Alembic", None)]),
    ("Data & Storage", [("PostgreSQL", "postgresql"), ("MySQL", "mysql"), ("SQLite", "sqlite"),
                        ("ChromaDB", None), ("pandas", "pandas"), ("NumPy", "numpy")]),
    ("Realtime & Automation", [("LiveKit", "livekit"), ("Playwright", None), ("Baileys", None)]),
    ("Frontend & UI", [("React", "react"), ("HTML5", "html5"), ("CSS", "css"), ("Streamlit", "streamlit")]),
    ("Infra & Tooling", [("Docker", "docker"), ("GitHub Actions", "githubactions"), ("Vercel", "vercel"),
                         ("DigitalOcean", "digitalocean"), ("Linux", "linux"), ("Git", "git"),
                         ("GitHub", "github"), ("GitLab", "gitlab"), ("Postman", "postman")]),
    ("AI-assisted dev", [("Claude Code", "claude"), ("GitHub Copilot", "githubcopilot"), ("Cursor", "cursor"),
                         ("Codex", None)]),
]


def slug_of(title):
    return title.lower().replace(" & ", "-").replace(" ", "-").replace("+", "plus")


def tiles(title, items):
    W, TH, G, GY = 1000, 40, 10, 10
    rows, cur, curw = [], [], 0
    sizes = []
    for label, slug in items:
        w = tw([(label, "BG", "")], 14.5) + (46 if slug else 36)
        sizes.append(w)
    for it, w in zip(items, sizes):
        if cur and curw + G + w > W - 2:
            rows.append(cur); cur, curw = [], 0
        cur.append((it, w)); curw += w + (G if len(cur) > 1 else 0)
    rows.append(cur)
    H = len(rows) * TH + (len(rows) - 1) * GY + 2
    alt = f"{title}: " + ", ".join(l for l, _ in items)
    s = Svg(W, H, title, alt)
    y = 1
    for row in rows:
        x = 1
        for (label, slug), w in row:
            s.comment(f"Chip: {label}")
            s.raw(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{TH-1}" rx="8" fill="{PAPER}" stroke="{PAPER_LN}"/>')
            if slug:
                icon(s, slug, x + 14, y + (TH - 1 - 19) / 2, 19, on="light")
                s.text(x + 42, y + 25, label, "BG", 14.5, INKT)
            else:
                s.raw(f'<circle cx="{x+15:.1f}" cy="{y+(TH-1)/2:.1f}" r="3.2" fill="{ROSE_DK}"/>')
                s.text(x + 28, y + 25, label, "BG", 14.5, INKT)
            x += w + G
        y += TH + GY
    s.save(f"stack-{slug_of(title)}.svg")


def contact_pill(name, label, alt):
    W, H = 188, 54
    s = Svg(W, H, alt, alt)
    s.raw(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="9" fill="{PAPER}" stroke="{PAPER_LN}"/>')
    s.raw(f'<circle cx="26" cy="27" r="4" fill="{ROSE_DK}"/>')
    s.text(42, 32, label, "MM6", 15.5, INKT)
    arrow(s, W - 38, 21, 11, INKT, 1.7)
    s.save(name)


# =====================================================================
# GLYPHS for the contributions script
# =====================================================================
def glyph_json():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ,.:/-"
    out = {}
    for key in ("MM", "BG6"):
        f = FONT[key]
        g = {}
        for c in chars:
            gid, adv, _, _ = f.shape(c)[0]
            pen = SVGPathPen(f.gs, ntos=lambda v: str(round(v)))
            f.gs[f.order[gid]].draw(pen)
            g[c] = [adv, pen.getCommands()]
        out[key] = {"upem": f.upem, "g": g}
    os.makedirs(f"{OUT2}/.github/scripts", exist_ok=True)
    json.dump(out, open(f"{OUT2}/.github/scripts/glyphs.json", "w"), separators=(",", ":"))
    shutil.copy(f"{SCR}/contributions.py", f"{OUT2}/.github/scripts/contributions.py")


if __name__ == "__main__":
    shutil.rmtree(OUT2, ignore_errors=True)
    os.makedirs(f"{OUT2}/assets")
    hero()
    card("card-interviewer.svg", "01", "AGENTIC  /  VOICE", "AI Video", "Interviewer",
         ["5"], "MCP tools for Claude Desktop",
         "Joins a live LiveKit call with a face and a voice. Turns a job description, resume and GitHub repos into a "
         "recruiter-approved question plan, interviews with adaptive follow-ups, then writes an evidence-backed scorecard.",
         "LangGraph · Gemini Live · LiveKit · FastMCP", "AI Video Interviewer", angle=-0.9, seed=1)
    card("card-redteam.svg", "02", "AI SECURITY", "AI Red-Teaming Toolkit", "for RAG Chatbots",
         ["43%", "->", "0%"], "of attack prompts exploited",
         "35 attacks across 5 categories, scored by an LLM judge, then patched with regex and PyTorch guards. "
         "In-sample on one prompt set, so read it as a fix, not a proof.",
         "Python · PyTorch · Gemini · Groq", "AI Red-Teaming Toolkit for RAG Chatbots", angle=0.8, seed=2)
    card("card-rag.svg", "03", "RAG  /  MULTIMODAL", "Multimodal RAG over", "Attention Is All You Need",
         ["35"], "elements indexed: text, tables, figures",
         "One pipeline over the text, tables and figures of a single PDF in one ChromaDB store. Retrieved figures go to "
         "the LLM as images, so answers are grounded in the diagrams too. 28+ edge cases handled.",
         "Gemini · ChromaDB · PyMuPDF · Streamlit", "Multimodal RAG over Attention Is All You Need", angle=0.7, seed=3)
    card("card-leadgen.svg", "04", "AUTOMATION AGENT", "Lead Generation", "Agent",
         ["Prompt", "->", "Excel"], "no manual search",
         "Type “coffee shops in Karachi”. A Groq LLM parses it, Playwright searches Bing Maps and scrapes results, and "
         "contact emails found on business sites land in a spreadsheet.",
         "Playwright · Groq · Streamlit · openpyxl", "Lead Generation Agent", angle=-0.7, seed=4)
    for title, items in STACK:
        tiles(title, items)
    contact_pill("btn-linkedin.svg", "LinkedIn", "LinkedIn")
    contact_pill("btn-email.svg", "Email", "Email")
    glyph_json()
    subprocess.run([sys.executable, f"{OUT2}/.github/scripts/contributions.py", "--sample"],
                   env={**os.environ, "CONTRIB_OUT": f"{OUT2}/assets/contributions.svg"}, check=True)
    print("built", OUT2)
