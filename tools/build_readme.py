#!/usr/bin/env python3
"""Builds the profile README assets: SVGs with text converted to outlines
(so custom fonts render identically everywhere, no font loading needed)."""
import io, os, re, sys
from html import escape
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

SCR = os.path.dirname(os.path.abspath(__file__))
FD = f"{SCR}/fonts/node_modules/@fontsource"
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{SCR}/out"
os.makedirs(f"{OUT}/assets", exist_ok=True)

# ---------- palette ----------
INK = "#0c0d0f"; PANEL = "#131518"; LINE = "#2a2d34"; LINE2 = "#3a3e46"
BONE = "#ece7db"; SOFT = "#b9b4a8"; MUTE = "#7f838c"
EMBER = "#ff5b35"; SAGE = "#9ad1b0"; AMBER = "#f2b84b"


# ---------- fonts ----------
class Font:
    def __init__(self, path):
        tt = TTFont(path)
        self.upem = tt["head"].unitsPerEm
        self.order = tt.getGlyphOrder()
        self.gs = tt.getGlyphSet()
        tt.flavor = None
        buf = io.BytesIO(); tt.save(buf)
        self.hbfont = hb.Font(hb.Face(buf.getvalue()))

    def shape(self, text):
        b = hb.Buffer(); b.add_str(text); b.guess_segment_properties()
        hb.shape(self.hbfont, b, {"kern": True, "liga": True})
        return [(i.codepoint, p.x_advance, p.x_offset, p.y_offset)
                for i, p in zip(b.glyph_infos, b.glyph_positions)]

    def path(self, gid):
        pen = SVGPathPen(self.gs)
        self.gs[self.order[gid]].draw(pen)
        return pen.getCommands()


FONT = {
    "IS": Font(f"{FD}/kalam/files/kalam-latin-700-normal.woff2"),       # display: handwriting-style
    "ISI": Font(f"{FD}/kalam/files/kalam-latin-700-normal.woff2"),
    "MM": Font(f"{FD}/nunito/files/nunito-latin-400-normal.woff2"),     # body / labels
    "MM6": Font(f"{FD}/nunito/files/nunito-latin-700-normal.woff2"),
    "BG": Font(f"{FD}/nunito/files/nunito-latin-400-normal.woff2"),
    "BG6": Font(f"{FD}/nunito/files/nunito-latin-700-normal.woff2"),
}



FONTID = {"IS": "kalam", "ISI": "kalam", "MM": "nunito", "BG": "nunito", "MM6": "nunito-bold", "BG6": "nunito-bold"}


def wrap_path(d, indent, width=96):
    """Break long path data onto several lines (at command letters) so the file stays readable."""
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
    """Indent one element per line; wrap long path data; keep <title>text</title> on one line."""
    toks = re.findall(r"<!--.*?-->|<[^>]+>|[^<]+", svg, re.S)
    out, depth, i = [], 0, 0
    while i < len(toks):
        t = toks[i]
        ind = step * depth
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
                out.append(ind + t + nxt + toks[i + 2]); i += 2     # <title>text</title>
            else:
                out.append(ind + t)
                if not t.endswith("/>"): depth += 1
        i += 1
    return "\n".join(out) + "\n"


def tw(runs, size, ls=0):
    total = 0
    for t, fk, _ in runs:
        f = FONT[fk]; k = size / f.upem
        for _, adv, _, _ in f.shape(t):
            total += adv * k + ls
    return total - ls


def fit(runs, maxw, maxsize, ls=0):
    w = tw(runs, 100, ls)
    return min(maxsize, 100 * maxw / w)


def wrap(text, fk, size, maxw, ls=0):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if tw([(trial, fk, "")], size, ls) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur); cur = word
    if cur: lines.append(cur)
    return lines


class Svg:
    def __init__(self, w, h, title, desc):
        self.w, self.h, self.title, self.desc = w, h, title, desc
        self.defs, self.pre, self.body = {}, [], []

    def raw(self, s): self.body.append(s)

    def comment(self, text): self.body.append(f"<!-- {text} -->")

    def runs(self, x, y, runs, size, ls=0, anchor="start"):
        items, total = [], 0
        for t, fk, fill in runs:
            f = FONT[fk]; k = size / f.upem
            for gid, adv, xo, yo in f.shape(t):
                items.append((fk, gid, total + xo * k, yo * k, fill, k))
                total += adv * k + ls
        total -= ls
        off = 0 if anchor == "start" else (-total / 2 if anchor == "middle" else -total)
        out = []
        for fk, gid, px, py, fill, k in items:
            gname = re.sub(r"[^A-Za-z0-9_-]", "_", FONT[fk].order[gid])
            key = f"{FONTID[fk]}-{gname}"
            if key not in self.defs:
                self.defs[key] = FONT[fk].path(gid)
            if not self.defs[key]:
                continue
            out.append(f'<use href="#{key}" transform="translate({x+off+px:.2f} {y-py:.2f}) '
                       f'scale({k:.5f} {-k:.5f})" fill="{fill}"/>')
        said = "".join(t for t, _, _ in runs)
        self.body.append(f'<!-- text: {said.replace("--", "- -")} -->')
        self.body.append(f'<g aria-label="{escape(said, quote=True)}">' + "".join(out) + "</g>")
        return total

    def text(self, x, y, t, fk, size, fill, ls=0, anchor="start"):
        return self.runs(x, y, [(t, fk, fill)], size, ls, anchor)

    def render(self):
        glyphs = "".join(f'<path id="{k}" d="{d}"/>' for k, d in self.defs.items() if d)
        pre = "".join(self.pre)
        defs = ('<!-- Glyph outlines: all text is drawn as shapes so the fonts look identical everywhere -->' + glyphs
                + ('<!-- Patterns, gradients and filters -->' + pre if pre else ""))
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
               f'width="{self.w}" height="{self.h}" role="img" aria-labelledby="t d">'
               f'<title id="t">{escape(self.title)}</title><desc id="d">{escape(self.desc)}</desc>'
               f'<defs>{defs}</defs>{"".join(self.body)}</svg>')
        return pretty(svg)

    def save(self, name):
        with open(f"{OUT}/assets/{name}", "w") as fh:
            fh.write(self.render())


def arrow(s, x, y, size=11, color=BONE, sw=1.6):
    s.raw(f'<path d="M{x} {y+size} L{x+size} {y} M{x+size*0.28} {y} H{x+size} V{y+size*0.72}" '
          f'fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')


def corner_marks(s, x0, y0, x1, y1, m=14, color=LINE2):
    for (x, y, dx, dy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        s.raw(f'<path d="M{x} {y+dy*m} V{y} H{x+dx*m}" fill="none" stroke="{color}" stroke-width="1.2"/>')


# =====================================================================
# HERO
# =====================================================================
def hero():
    W, H = 1000, 440
    s = Svg(W, H, "Syeda Maha Fatima — Backend and agentic AI engineer",
            "Backend and agentic AI engineer from Karachi. I build LLM pipelines, then try to break them. "
            "In my RAG-chatbot red-team toolkit, the share of attack prompts that succeeded dropped from 43% to 0% "
            "after guardrails (in-sample, single LLM judge).")
    s.pre.append(f'<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
                 f'<circle cx="1" cy="1" r="1" fill="#fff" opacity=".07"/></pattern>'
                 f'<radialGradient id="glow1" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" '
                 f'gradientTransform="translate(120 20) scale(520 420)">'
                 f'<stop offset="0" stop-color="{EMBER}" stop-opacity=".16"/><stop offset="1" stop-color="{EMBER}" stop-opacity="0"/></radialGradient>'
                 f'<radialGradient id="glow2" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" '
                 f'gradientTransform="translate(960 430) scale(380 300)">'
                 f'<stop offset="0" stop-color="{SAGE}" stop-opacity=".09"/><stop offset="1" stop-color="{SAGE}" stop-opacity="0"/></radialGradient>')
    s.raw(f'<rect width="{W}" height="{H}" rx="22" fill="{INK}"/>')
    s.raw(f'<rect width="{W}" height="{H}" rx="22" fill="url(#glow1)"/>')
    s.raw(f'<rect width="{W}" height="{H}" rx="22" fill="url(#glow2)"/>')
    s.raw(f'<rect width="{W}" height="{H}" rx="22" fill="url(#dots)"/>')
    s.raw(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="21.5" fill="none" stroke="{LINE}"/>')
    corner_marks(s, 26, 26, W - 26, H - 26)

    # name tag
    s.raw(f'<circle cx="54" cy="67" r="4" fill="{EMBER}"/>')
    s.runs(68, 71, [("SYEDA MAHA FATIMA", "MM6", BONE), ("   /   KARACHI, PK", "MM", MUTE)], 12, ls=2)

    # headline
    l1 = [("Backend & ", "IS", BONE), ("agentic", "ISI", EMBER)]
    l2 = [("AI engineer.", "IS", BONE)]
    size = fit(l1, 540, 92)
    s.runs(48, 196, l1, size)
    s.runs(48, 196 + size * 0.92, l2, size)

    # subline
    sub = "I build LLM pipelines, then try to break them."
    s.text(50, 340, sub, "BG", 21, SOFT)

    # tags
    s.runs(50, 396, [("LLM PIPELINES  /  RAG  /  LANGGRAPH  /  MCP  /  AI SECURITY", "MM", MUTE)], 10, ls=1.2)

    # advisory panel
    px, py, pw, ph = 628, 48, 324, 344
    s.raw(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="16" fill="{PANEL}" stroke="{LINE}"/>')
    ix = px + 24; iw = pw - 48
    s.runs(ix, py + 36, [("FINDING", "MM6", EMBER), ("  /  RAG CHATBOT RED TEAM", "MM", MUTE)], 9.5, ls=1.6)
    s.raw(f'<path d="M{ix} {py+54} H{ix+iw}" stroke="{LINE}"/>')
    # big numbers
    bs = 88
    s.text(ix, py + 142, "43%", "IS", bs, EMBER)
    s.text(ix + iw, py + 142, "0%", "IS", bs, SAGE, anchor="end")
    mid = ix + iw / 2 + 4
    s.raw(f'<path d="M{mid-17} {py+112} H{mid+17} M{mid+8} {py+103} L{mid+17} {py+112} L{mid+8} {py+121}" '
          f'fill="none" stroke="{MUTE}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')
    s.text(ix, py + 166, "BEFORE GUARDRAILS", "MM", 8.5, MUTE, ls=1.2)
    s.text(ix + iw, py + 166, "AFTER", "MM", 8.5, MUTE, ls=1.2, anchor="end")
    # bars (20 safe / 4 partial / 11 vulnerable of 35)
    by = py + 200
    s.text(ix, by - 8, "BEFORE", "MM", 8.5, MUTE, ls=1.4)
    gap = 3; usable = iw - 2 * gap
    segs = [(20, SAGE), (4, AMBER), (11, EMBER)]
    x = ix
    for n, c in segs:
        w = usable * n / 35
        s.raw(f'<rect x="{x:.1f}" y="{by}" width="{w:.1f}" height="11" rx="3" fill="{c}"/>'); x += w + gap
    by2 = by + 44
    s.text(ix, by2 - 8, "AFTER", "MM", 8.5, MUTE, ls=1.4)
    s.raw(f'<rect x="{ix}" y="{by2}" width="{iw}" height="11" rx="3" fill="{SAGE}"/>')
    # legend
    ly = by2 + 38
    lx = ix
    for label, c in [("SAFE", SAGE), ("PARTIAL", AMBER), ("VULNERABLE", EMBER)]:
        s.raw(f'<rect x="{lx}" y="{ly-7}" width="8" height="8" rx="2" fill="{c}"/>')
        w = s.text(lx + 14, ly, label, "MM", 8.5, SOFT, ls=1)
        lx += 14 + w + 18
    # footnote
    foot = wrap("35 attack prompts across 5 categories. In-sample, one LLM judge, no human review.", "BG", 12, iw)
    for i, ln in enumerate(foot):
        s.text(ix, py + ph - 38 + i * 16, ln, "BG", 12, MUTE)
    s.save("hero.svg")


# =====================================================================
# NOW STRIP
# =====================================================================
def now_strip():
    W, H = 1000, 118
    s = Svg(W, H, "Currently", "Backend AI Engineer intern at Flyrank. Computer Science at FAST-NUCES Karachi, class of 2028. "
            "Dean's List three consecutive years. Open to internships and research in backend, agentic AI and AI security.")
    s.raw(f'<rect width="{W}" height="{H}" rx="18" fill="{PANEL}"/>')
    s.raw(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="17.5" fill="none" stroke="{LINE}"/>')
    cols = [
        ("NOW", "Backend AI Engineer", "Intern at Flyrank"),
        ("STUDYING", "Computer Science", "FAST-NUCES Karachi, class of 2028"),
        ("DISTINCTION", "Dean’s List", "3 consecutive years"),
        ("OPEN TO", "Internships & research", "backend, agentic AI, AI security"),
    ]
    cw = (W - 48) / 4
    for i, (lab, big, small) in enumerate(cols):
        x = 30 + i * cw
        if i:
            s.raw(f'<path d="M{x-14:.1f} 24 V{H-24}" stroke="{LINE}"/>')
        s.text(x, 36, lab, "MM6", 9.5, EMBER, ls=2)
        sz = fit([(big, "IS", "")], cw - 34, 30)
        s.text(x, 74, big, "IS", sz, BONE)
        sm = 13 if tw([(small, "BG", "")], 13) < cw - 30 else 12
        s.text(x, 98, small, "BG", sm, MUTE)
    s.save("now.svg")


# =====================================================================
# SECTION HEADERS
# =====================================================================
def header(name, idx, a, b, tag, alt):
    W, H = 1000, 76
    s = Svg(W, H, alt, alt)
    s.raw(f'<rect width="{W}" height="{H}" rx="16" fill="{INK}"/>')
    s.raw(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="15.5" fill="none" stroke="{LINE}"/>')
    s.text(28, 50, idx, "MM6", 12, EMBER, ls=2)
    x0 = 28 + 36
    w1 = s.runs(x0, 54, [(a, "IS", BONE), (b, "ISI", EMBER)], 44)
    tagw = tw([(tag, "MM", "")], 9.5, 1.6)
    s.raw(f'<path d="M{x0+w1+22:.1f} 44 H{W-tagw-22-28:.1f}" stroke="{LINE}"/>')
    s.text(W - 28, 48, tag, "MM", 9.5, MUTE, ls=1.6, anchor="end")
    s.save(name)


# =====================================================================
# PROJECT CARDS
# =====================================================================
def card(name, idx, tag, t1, t2, desc, tags, alt):
    W, H = 490, 380
    s = Svg(W, H, alt, desc)
    s.raw(f'<rect width="{W}" height="{H}" rx="18" fill="{PANEL}"/>')
    s.raw(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="17.5" fill="none" stroke="{LINE}"/>')
    s.raw(f'<rect width="{W}" height="{H}" rx="18" fill="url(#dots)"/>')
    s.pre.append('<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
                 '<circle cx="1" cy="1" r="1" fill="#fff" opacity=".04"/></pattern>')
    p = 30
    wi = s.text(p, 46, idx, "MM6", 11, EMBER, ls=2)
    s.text(p + wi + 14, 46, tag, "MM", 9.5, MUTE, ls=1.8)
    arrow(s, W - p - 12, 33, 12, BONE)
    s.text(p, 104, t1, "IS", 38, BONE)
    s.text(p, 104 + 40, t2, "ISI", 38, BONE)
    lines = wrap(desc, "BG", 14.5, W - 2 * p)
    for i, ln in enumerate(lines):
        s.text(p, 188 + i * 22, ln, "BG", 14.5, SOFT)
    # tags
    ty = H - 54
    s.raw(f'<path d="M{p} {ty-14} H{W-p}" stroke="{LINE}"/>')
    x = p
    for t in tags:
        w = tw([(t, "MM", "")], 9.5, 0.6)
        s.raw(f'<rect x="{x:.1f}" y="{ty}" width="{w+22:.1f}" height="26" rx="13" fill="none" stroke="{LINE2}"/>')
        s.text(x + 11, ty + 17, t, "MM", 9.5, BONE, ls=0.6)
        x += w + 22 + 8
    assert x - 8 <= W - p + 1, (name, "tags overflow", x)
    assert 188 + (len(lines) - 1) * 22 < ty - 22, (name, "desc too long", len(lines))
    s.save(name)


# =====================================================================
# STACK SHEET
# =====================================================================
STACK = [
    ("LANGUAGES", ["Python", "JavaScript", "C++", "C", "C#", "Java", "SQL"]),
    ("AI & LLM", ["LangGraph", "LangChain", "Multimodal RAG", "MCP (FastMCP)", "PyTorch",
                  "Gemini & Gemini Live", "Groq", "OpenAI API", "Claude API"]),
    ("AI SECURITY", ["Prompt-injection & jailbreak testing", "LLM-as-judge evals",
                     "Regex + ML guardrails", "CWE classification", "CVSS-style severity scoring"]),
    ("BACKEND & APIS", ["FastAPI", "Flask", "Django", "Node.js", "SQLModel", "Alembic", "REST"]),
    ("DATA & STORAGE", ["PostgreSQL", "MySQL", "SQLite", "ChromaDB", "pandas", "NumPy"]),
    ("REALTIME & AUTOMATION", ["LiveKit", "Playwright", "Baileys (WhatsApp)"]),
    ("FRONTEND & UI", ["React", "HTML5", "CSS3", "Streamlit"]),
    ("INFRA & TOOLING", ["Docker", "GitHub Actions", "Vercel", "DigitalOcean", "Linux",
                         "Git", "GitHub", "GitLab", "Postman"]),
    ("AI-ASSISTED DEV", ["Claude Code", "GitHub Copilot", "Cursor", "Codex"]),
]


def stack():
    W = 1000
    LX, IX, IW = 32, 330, 618
    size, lh, gap = 18, 30, 30
    rows = []
    for label, items in STACK:
        lines, cur, curw = [], [], 0
        for it in items:
            w = tw([(it, "BG", "")], size)
            add = w if not cur else gap + w
            if cur and curw + add > IW:
                lines.append(cur); cur, curw = [it], w
            else:
                cur.append(it); curw += add
        lines.append(cur)
        rows.append((label, lines))
    H = 14 + sum(max(1, len(l)) * lh + 36 for _, l in rows) + 4
    s = Svg(W, H, "Technical stack",
            "; ".join(f"{lab.title()}: {', '.join(its)}" for lab, its in STACK))
    s.raw(f'<rect id="bg" width="{W}" height="9999" rx="18" fill="{INK}"/>')
    y = 14
    for n, (label, lines) in enumerate(rows, 1):
        rh = len(lines) * lh + 36
        top = y
        s.raw(f'<path d="M{LX} {top:.1f} H{W-LX}" stroke="{LINE}"/>') if n > 1 else None
        hot = label == "AI SECURITY"
        s.text(LX, top + 38, f"{n:02d}", "MM6", 11, EMBER, ls=2)
        s.text(LX + 34, top + 38, label, "MM6", 10.5, EMBER if hot else BONE, ls=2)
        for li, line in enumerate(lines):
            x = IX
            by = top + 40 + li * lh
            for ii, it in enumerate(line):
                if ii:
                    s.raw(f'<circle cx="{x+gap/2:.1f}" cy="{by-6:.1f}" r="2" fill="{LINE2}"/>')
                    x += gap
                x += s.text(x, by, it, "BG", size, BONE)
        y += rh
    s.h = int(y + 14)
    s.body[0] = s.body[0].replace('height="9999"', f'height="{s.h}"')
    s.body.insert(1, f'<rect x=".5" y=".5" width="{W-1}" height="{s.h-1}" rx="17.5" fill="none" stroke="{LINE}"/>')
    s.save("stack.svg")


# =====================================================================
# CONTACT PILLS
# =====================================================================
def pill(name, label, alt):
    W, H = 188, 54
    s = Svg(W, H, alt, alt)
    s.raw(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="27" fill="{PANEL}" stroke="{LINE2}"/>')
    s.raw(f'<circle cx="26" cy="27" r="4" fill="{EMBER}"/>')
    s.text(42, 31.5, label, "MM6", 11.5, BONE, ls=1.8)
    arrow(s, W - 38, 21, 11, BONE)
    s.save(name)


if __name__ == "__main__":
    hero(); now_strip()
    header("h-work.svg", "01", "Selected ", "work", "4 PROJECTS", "01 — Selected work")
    header("h-stack.svg", "02", "The ", "stack", "9 FIELDS", "02 — The stack")
    header("h-index.svg", "03", "Also ", "shipped", "THE REST OF THE SHELF", "03 — Also shipped")
    header("h-contact.svg", "04", "Get in ", "touch", "OPEN TO OPPORTUNITIES", "04 — Get in touch")

    card("card-interviewer.svg", "01", "AGENTIC  /  REALTIME VOICE", "AI Video", "Interviewer",
         "Joins a live LiveKit call with a face and a voice. Turns a job description, resume and GitHub repos into a "
         "recruiter-approved question plan, interviews with adaptive follow-ups and instant barge-in, then writes an "
         "evidence-backed scorecard. Also exposed as an MCP server for Claude Desktop.",
         ["LangGraph", "Gemini Live", "LiveKit", "FastMCP"], "AI Video Interviewer")
    card("card-redteam.svg", "02", "AI SECURITY", "AI Red-Teaming Toolkit", "for RAG Chatbots",
         "35 attacks across 5 categories: injection, jailbreak, role confusion, prompt leakage and data extraction. "
         "An LLM judge scores every answer; regex and PyTorch guards then cut the exploited share from 43% to 0% "
         "on this prompt set (in-sample, so read it as a fix, not a proof).",
         ["Python", "PyTorch", "Groq", "Gemini"], "AI Red-Teaming Toolkit for RAG Chatbots")
    card("card-rag.svg", "03", "RAG  /  MULTIMODAL", "Multimodal RAG over", "Attention Is All You Need",
         "One pipeline over the text, tables and figures of a single PDF, all embedded into one ChromaDB store. "
         "Retrieved figures are handed to the LLM as images, so answers are grounded in the diagrams too. "
         "28+ edge cases handled across extraction, retrieval and UI.",
         ["Gemini", "ChromaDB", "PyMuPDF", "Streamlit"], "Multimodal RAG over Attention Is All You Need")
    card("card-leadgen.svg", "04", "AUTOMATION AGENT", "Lead Generation", "Agent",
         "Type “coffee shops in Karachi” and walk away. A Groq LLM parses the prompt, Playwright searches Bing Maps "
         "and scrapes the results, contact emails are discovered from business websites, and everything lands in "
         "an Excel sheet.",
         ["Playwright", "Groq", "Streamlit", "openpyxl"], "Lead Generation Agent")

    stack()
    pill("btn-linkedin.svg", "LINKEDIN", "LinkedIn")
    pill("btn-email.svg", "EMAIL", "Email")
    print("built to", OUT)
