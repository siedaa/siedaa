import sys, os
sys.argv=[sys.argv[0]]
import build2 as B2
OUT=B2.OUT2
def img(src, alt, extra='width="100%"'): return f'<img src="assets/{src}" alt="{alt}" {extra}>'
stack_md=[]
for title, items in B2.STACK:
    alt = f"{title}: " + ", ".join(l for l,_ in items)
    stack_md.append(f'#### {title}\n\n<p>\n{img("stack-"+B2.slug_of(title)+".svg", alt)}\n</p>')
md = f'''<p align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/hero-light.svg">
  {img("hero-light.svg","Hi, I’m Maha, learning backend and agentic AI by building things. I build LLM pipelines, then try to break them.")}
</picture>
</p>

<p align="center">
<b>Backend AI intern at Flyrank</b> &nbsp;·&nbsp; CS at FAST-NUCES, class of 2028<br>
Open to internships and research in backend, agentic AI and AI security
</p>

## Selected work

<p align="center">
<a href="https://github.com/siedaa/AI-Video-Interviewer">{img("card-interviewer.svg","AI Video Interviewer: a live LiveKit interviewer built with LangGraph, Gemini Live and FastMCP",'width="49%"')}</a>
<a href="https://github.com/siedaa/AI-red-teaming-toolkit-for-RAG-chatbot-security">{img("card-redteam.svg","AI Red-Teaming Toolkit for RAG Chatbots: 35 attacks, exploited share cut from 43% to 0%",'width="49%"')}</a>
</p>

<p align="center">
<a href="https://github.com/siedaa/multimodal-rag-attention-paper">{img("card-rag.svg","Multimodal RAG over Attention Is All You Need: text, tables and figures in one ChromaDB store",'width="49%"')}</a>
<a href="https://github.com/siedaa/-Lead-Generation-Agent-">{img("card-leadgen.svg","Lead Generation Agent: Groq, Playwright, Streamlit, exports to a spreadsheet",'width="49%"')}</a>
</p>

## Stack

''' + "\n\n".join(stack_md) + '''

## Also shipped

| Project | What it does | Built with |
|:--|:--|:--|
| [**RAG Chatbot: Chunking & Retrieval**](https://github.com/siedaa/Rag-chat-bot---aiseason) | Benchmarks 3 chunking strategies and 2 retrieval techniques with dedicated A/B scripts | `Python` `RAG` `LLM evaluation` |
| [**AI Image Relevance Engine**](https://github.com/siedaa/flyrank-capstone-image-relevance) | Flyrank capstone: matches image content to relevance behind a full FastAPI backend | `FastAPI` `Alembic` `Docker` |
| [**WhatsApp AI Chatbot**](https://github.com/siedaa/WhatsAPP-chat-Bot) | Routes each message to chat, grounded RAG answers, or recall of personal facts, over a plain WhatsApp Web login | `Node.js` `Baileys` `LangChain` `Groq` |
| [**PDF Report Generator**](https://github.com/siedaa/-PDF-report-generator) | SQL aggregation to HTML to downloadable PDF through headless Chromium, idempotent by design | `FastAPI` `SQLite` `Playwright` |
| [**Containerized Task API**](https://github.com/siedaa/Containerize-your-stack) | CRUD API plus PostgreSQL, app and database up together with one command | `FastAPI` `SQLModel` `PostgreSQL` `Docker` |
| [**DSA Color Palette Generator**](https://github.com/siedaa/dsa-color-palette-generator-cpp) | Desktop app that teaches data structures: stack-based undo/redo, circular-queue history, merge sort | `C++` `SFML` |
| [**M & I CandyPop!**](https://github.com/siedaa/-M-and-I-Candy-Pop-Game--OOP-Project.) | Match-and-clear game built to show OOP principles, with scoring and a GUI | `C++` `SFML` |

## Contributions

<p align="center">
''' + img("contributions.svg","GitHub contribution calendar for the last year") + '''
</p>

<p align="center">
''' + img("activity.svg","GitHub contribution activity: contributions per week over the last year") + '''
</p>

## Let’s connect

<p align="center">
<a href="https://www.linkedin.com/in/syeda-maha-fatima/">''' + img("btn-linkedin.svg","LinkedIn",'height="54"') + '''</a>
&nbsp;&nbsp;
<a href="mailto:siedaamaha@gmail.com">''' + img("btn-email.svg","Email",'height="54"') + '''</a>
</p>

<p align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://quotes-github-readme.vercel.app/api?type=horizontal&theme=dark">
  <img src="https://quotes-github-readme.vercel.app/api?type=horizontal&theme=graywhite" alt="A random quote that changes every time the page loads" width="70%">
</picture>
</p>
'''
open(f"{OUT}/README.md","w").write(md)
print("readme written", len(md))
