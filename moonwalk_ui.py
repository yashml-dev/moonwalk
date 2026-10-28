"""MOONWALK design system for Streamlit: scoped CSS + small HTML building blocks.

Palette (fixed):  paper #F7F6F2 · ink #171717 · grey #777777 · vermilion #FF4D32
Contrast notes:   vermilion is never used for small text on paper (3.1:1). It is used as a
                  fill with ink text (5.6:1), or for large display type. Small grey metadata
                  uses a darker tint of the same grey (--mw-grey-ink) to stay above 4.5:1.
"""
from __future__ import annotations

import base64
import re
from html import escape
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).resolve().parent / "assets"


def _flat(markup: str) -> str:
    """Collapse indentation so Markdown never treats the HTML as a code block."""
    return "".join(line.strip() for line in markup.strip().splitlines())


def html(markup: str, target=None):
    (target or st).markdown(_flat(markup), unsafe_allow_html=True)


THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700&family=Space+Grotesk:wght@500;700&display=swap');

:root{
  --mw-paper:#F7F6F2; --mw-ink:#171717; --mw-grey:#777777; --mw-grey-ink:#5C5C5C; --mw-red:#FF4D32;
  --mw-display:'Space Grotesk','Helvetica Neue',Arial,sans-serif;
  --mw-body:'Manrope','Helvetica Neue',Arial,sans-serif;
  --mw-gutter:clamp(16px,4vw,48px);
}

/* ---------- Streamlit chrome, stripped back ---------- */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"]{display:none !important}
[data-testid="stHeader"]{background:transparent !important; height:0}
.stApp{background:var(--mw-paper); color:var(--mw-ink); font-family:var(--mw-body)}
html{scroll-behavior:smooth}
[data-testid="stMainBlockContainer"], .block-container{
  max-width:1280px !important; padding:0 var(--mw-gutter) 4rem !important;}
.stApp p, .stApp li, .stApp label{font-family:var(--mw-body)}
.stApp h1,.stApp h2,.stApp h3{font-family:var(--mw-display); color:var(--mw-ink)}
[data-testid="stVerticalBlock"]{gap:1rem}
[data-testid="stImage"] img, [data-testid="stVideo"] video{border-radius:0 !important; border:1.5px solid var(--mw-ink)}
::selection{background:var(--mw-red); color:var(--mw-ink)}

/* ---------- Focus: always visible ---------- */
.stApp a:focus-visible, .stApp button:focus-visible, .stApp input:focus-visible,
.stApp [tabindex]:focus-visible, .stApp summary:focus-visible, .stApp [role="slider"]:focus-visible{
  outline:3px solid var(--mw-ink) !important; outline-offset:3px !important; box-shadow:0 0 0 6px var(--mw-red) !important;}

/* ---------- Masthead ---------- */
.mw-mast{display:flex; align-items:flex-end; justify-content:space-between; gap:1.5rem; flex-wrap:wrap;
  padding:1.4rem 0 1rem; border-bottom:1.5px solid var(--mw-ink); margin-bottom:0}
.stApp a.mw-word, .mw-word{font-family:var(--mw-display); font-weight:700; font-size:1.7rem; letter-spacing:-.03em; line-height:1; color:var(--mw-ink) !important; text-decoration:none !important}
.mw-word i{display:inline-block; width:.5em; height:.5em; border-radius:50%; background:var(--mw-red); margin-left:.12em; vertical-align:baseline}
.mw-desc{font-size:.68rem; letter-spacing:.14em; text-transform:uppercase; color:var(--mw-grey-ink); margin-top:.45rem; font-weight:500}
.mw-nav{display:flex; gap:1.6rem; flex-wrap:wrap}
.stApp .mw-nav a{font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; font-weight:700; color:var(--mw-ink); text-decoration:none;
  padding:.35rem 0; border-bottom:2px solid transparent; transition:border-color .15s ease}
.mw-nav a:hover{border-bottom-color:var(--mw-red)}

/* ---------- Hero ---------- */
.mw-hero{display:grid; grid-template-columns:repeat(12,1fr); gap:0 1.5rem; padding:clamp(1.8rem,5vw,4rem) 0 1.5rem; align-items:end}
.mw-hero .mw-h1{grid-column:1 / span 9; margin:0; padding:0; font-weight:700; text-transform:uppercase;
  font-size:clamp(2.6rem,7.4vw,7.4rem); line-height:.88; letter-spacing:-.055em}
.mw-hero .mw-h1 em{font-style:normal; color:var(--mw-red)}
.mw-hero aside{grid-column:10 / span 3; padding-bottom:.6rem; border-top:1.5px solid var(--mw-ink); padding-top:.9rem}
.mw-hero aside p{font-size:1.05rem; line-height:1.45; margin:0 0 1rem; font-weight:500}
.mw-meta{font-size:.68rem; letter-spacing:.14em; text-transform:uppercase; color:var(--mw-grey-ink); font-weight:700; line-height:1.9}
.mw-fig{position:relative; margin:1.2rem 0 0; overflow:hidden; border-bottom:1.5px solid var(--mw-ink)}
.mw-fig img{display:block; width:100%; height:clamp(160px,26vw,340px); object-fit:cover; filter:grayscale(1) contrast(1.08); }
.mw-cap{display:flex; justify-content:space-between; gap:1rem; flex-wrap:wrap; padding:.55rem 0; }
@media (max-width:860px){
  .mw-hero .mw-h1,.mw-hero aside{grid-column:1 / -1}
  .mw-hero .mw-h1{font-size:clamp(2.6rem,14vw,6rem)}
  .mw-hero aside{margin-top:1.4rem}
}

/* ---------- Section heads ---------- */
.mw-sec{display:grid; grid-template-columns:repeat(12,1fr); gap:0 1.5rem; border-top:1.5px solid var(--mw-ink);
  margin-top:clamp(2.2rem,6vw,4.5rem); padding:.9rem 0 1.2rem; scroll-margin-top:1rem; animation:mw-rise .5s ease both}
.mw-sec .mw-meta{grid-column:1 / span 3}
.mw-sec .mw-h2{grid-column:4 / -1; margin:0; padding:0; font-weight:700; text-transform:uppercase; letter-spacing:-.04em;
  font-size:clamp(2rem,5.4vw,4.6rem); line-height:.92}
.mw-sec .mw-h2 em{font-style:normal; color:var(--mw-red)}
.mw-lede{max-width:46ch; font-size:1.02rem; line-height:1.55; margin:1rem 0 .5rem}
@media (max-width:860px){.mw-sec .mw-meta,.mw-sec .mw-h2{grid-column:1 / -1} .mw-sec .mw-meta{margin-bottom:.6rem}}
@keyframes mw-rise{from{opacity:0; transform:translateY(10px)} to{opacity:1; transform:none}}

/* ---------- Steps list ---------- */
.mw-steps{list-style:none; margin:1.2rem 0 0; padding:0; border-top:1px solid var(--mw-ink)}
.mw-steps li{display:grid; grid-template-columns:2.2rem 1fr; padding:.8rem 0; border-bottom:1px solid var(--mw-ink); font-size:.95rem; line-height:1.4}
.mw-steps b{font-family:var(--mw-display); font-size:.8rem; letter-spacing:.08em}

/* ---------- Dropzone ---------- */
[data-testid="stFileUploader"] label{display:none}
[data-testid="stFileUploaderDropzone"]{
  position:relative; min-height:280px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:1.4rem;
  background:transparent; border:2px dashed var(--mw-ink); border-radius:0; padding:2rem 1rem;
  transition:transform .15s ease, box-shadow .15s ease, background-color .15s ease}
[data-testid="stFileUploaderDropzone"]:hover{transform:translate(-3px,-3px); box-shadow:6px 6px 0 var(--mw-ink); background:#fff}
[data-testid="stFileUploaderDropzoneInstructions"]{display:none}
[data-testid="stFileUploaderDropzone"]::before{
  content:"Drop your evidence here"; text-transform:uppercase; text-align:center; max-width:12ch;
  font-family:var(--mw-display); font-weight:700; font-size:clamp(2rem,4.6vw,3.6rem); line-height:.95; letter-spacing:-.04em; color:var(--mw-ink)}
[data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"]{
  font-size:0 !important; background:var(--mw-ink) !important; color:var(--mw-paper) !important; border:1.5px solid var(--mw-ink) !important;
  border-radius:0 !important; padding:.7rem 1.4rem !important; min-height:0 !important; transition:background-color .15s ease, color .15s ease}
[data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"]::after{
  content:"Browse files"; font-size:.74rem; letter-spacing:.14em; text-transform:uppercase; font-weight:700; font-family:var(--mw-body)}
[data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"]:hover{background:var(--mw-red) !important; color:var(--mw-ink) !important}
[data-testid="stFileUploaderFile"]{border-top:1px solid var(--mw-ink); border-radius:0; padding:.6rem 0; background:transparent}
[data-testid="stFileUploaderFileName"]{font-weight:700}
[data-testid="stFileUploaderDeleteBtn"] button{border-radius:0 !important}
.mw-types{display:flex; gap:.5rem; flex-wrap:wrap; margin:1.1rem 0 .6rem}
.mw-types span{font-size:.68rem; letter-spacing:.12em; font-weight:700; text-transform:uppercase; border:1px solid var(--mw-ink); padding:.25rem .55rem}

/* ---------- Buttons: rectangular, tactile ---------- */
.stButton > button, .stDownloadButton > button, [data-testid^="stBaseLinkButton"], .stLinkButton a{
  border-radius:0 !important; border:1.5px solid var(--mw-ink) !important; min-height:3.1rem; padding:.7rem 1.5rem !important;
  text-transform:uppercase; letter-spacing:.12em; font-weight:700 !important; font-size:.78rem !important; font-family:var(--mw-body) !important;
  text-decoration:none !important; transition:transform .15s ease, box-shadow .15s ease, background-color .15s ease}
.stButton > button p, .stDownloadButton > button p, .stLinkButton a p{font-size:.78rem !important; font-weight:700 !important; letter-spacing:.12em; text-transform:uppercase}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"], .stLinkButton a[kind="primary"],
[data-testid="stBaseButton-primary"], [data-testid="stBaseLinkButton-primary"]{
  background:var(--mw-red) !important; color:var(--mw-ink) !important; box-shadow:4px 4px 0 var(--mw-ink)}
.stButton > button[kind="secondary"], .stDownloadButton > button[kind="secondary"], .stLinkButton a[kind="secondary"],
[data-testid="stBaseButton-secondary"], [data-testid="stBaseLinkButton-secondary"]{
  background:transparent !important; color:var(--mw-ink) !important}
.stButton > button:hover:not(:disabled), .stDownloadButton > button:hover, .stLinkButton a:hover{
  transform:translate(-2px,-2px); box-shadow:6px 6px 0 var(--mw-ink); color:var(--mw-ink) !important}
.stButton > button:active:not(:disabled), .stDownloadButton > button:active, .stLinkButton a:active{transform:translate(1px,1px); box-shadow:1px 1px 0 var(--mw-ink)}
.stButton > button:disabled{background:transparent !important; color:var(--mw-grey-ink) !important; border-color:var(--mw-grey) !important; box-shadow:none; cursor:not-allowed}
[data-testid="stFileUploaderDropzone"] button{box-shadow:none !important}

/* ---------- Inputs ---------- */
[data-testid="stNumberInput"] input, [data-testid="stTextInput"] input{
  border-radius:0 !important; background:transparent !important; border:0 !important; border-bottom:1.5px solid var(--mw-ink) !important; padding-left:0 !important;
  font-family:var(--mw-body); font-weight:500}
[data-testid="stNumberInput"] > div > div, [data-testid="stTextInput"] > div > div{border:0 !important; border-radius:0 !important; background:transparent !important; box-shadow:none !important}
[data-testid="stNumberInput"] button{border-radius:0 !important}
.stApp label p, [data-testid="stWidgetLabel"] p{font-size:.68rem !important; letter-spacing:.14em; text-transform:uppercase; font-weight:700; color:var(--mw-grey-ink)}
[data-testid="stCheckbox"] label p, [data-testid="stCheckbox"] p{font-size:.9rem !important; letter-spacing:0; text-transform:none; color:var(--mw-ink); font-weight:500}
[data-testid="stSlider"] [role="slider"]{background:var(--mw-red); border:2px solid var(--mw-ink)}
[data-testid="stExpander"]{border:0; border-top:1px solid var(--mw-ink); border-bottom:1px solid var(--mw-ink); border-radius:0; background:transparent}
[data-testid="stExpander"] summary{padding:.7rem 0}
[data-testid="stExpander"] summary p{font-size:.72rem !important; letter-spacing:.14em; text-transform:uppercase; font-weight:700}
[data-testid="stExpander"] details{border:0}

/* ---------- Native alerts, flattened ---------- */
[data-testid="stAlert"]{border-radius:0; background:transparent; border:0; border-left:4px solid var(--mw-ink); color:var(--mw-ink)}

/* ---------- Notices ---------- */
.mw-note{border-left:4px solid var(--mw-ink); padding:.15rem 0 .15rem .9rem; margin:.9rem 0; font-size:.93rem; line-height:1.5; max-width:60ch}
.mw-note b{display:block; font-size:.68rem; letter-spacing:.14em; text-transform:uppercase; margin-bottom:.2rem}
.mw-note.warn{border-left-color:var(--mw-red); border-left-width:6px}
.mw-note.err{background:var(--mw-ink); color:var(--mw-paper); border-left:6px solid var(--mw-red); padding:.8rem 1rem}

/* ---------- Facts (dl) ---------- */
.mw-facts{margin:0; border-top:1.5px solid var(--mw-ink)}
.mw-facts div{display:grid; grid-template-columns:9.5rem 1fr; gap:1rem; padding:.7rem 0; border-bottom:1px solid var(--mw-ink); align-items:baseline}
.mw-facts dt{font-size:.66rem; letter-spacing:.14em; text-transform:uppercase; font-weight:700; color:var(--mw-grey-ink)}
.mw-facts dd{margin:0; font-size:.98rem; font-weight:500; line-height:1.4; overflow-wrap:anywhere}
.mw-facts dd.big{font-family:var(--mw-display); font-weight:700; font-size:1.25rem; letter-spacing:-.02em}
@media (max-width:560px){.mw-facts div{grid-template-columns:1fr; gap:.15rem}}

/* ---------- Status dot (GPS) ---------- */
.mw-status{display:flex; align-items:center; gap:.6rem; font-size:.68rem; letter-spacing:.14em; text-transform:uppercase; font-weight:700; margin-bottom:.8rem}
.mw-dot{width:.7rem; height:.7rem; border-radius:50%; background:var(--mw-grey); display:inline-block}
.mw-dot.on{background:var(--mw-red)}

/* ---------- Scan ---------- */
.mw-scan{position:relative; overflow:hidden; border:1.5px solid var(--mw-ink); background:var(--mw-ink)}
.mw-scan img{display:block; width:100%; max-height:560px; object-fit:contain; filter:grayscale(.4) contrast(1.05)}
.mw-scan::after{content:""; position:absolute; inset:0; background:rgba(23,23,23,.28)}
.mw-line{position:absolute; left:0; right:0; top:0; height:3px; background:var(--mw-red); z-index:2; animation:mw-sweep 1.9s ease-in-out infinite alternate}
@keyframes mw-sweep{from{top:0} to{top:calc(100% - 3px)}}
.mw-scan .mw-tag{position:absolute; left:0; bottom:0; z-index:3; background:var(--mw-red); color:var(--mw-ink); padding:.45rem .8rem;
  font-size:.7rem; letter-spacing:.14em; text-transform:uppercase; font-weight:700}
.mw-bar{height:6px; background:transparent; border:1px solid var(--mw-ink); margin:.8rem 0 .4rem}
.mw-bar span{display:block; height:100%; background:var(--mw-red); transition:width .2s linear}

/* ---------- Result ---------- */
.mw-reveal{animation:mw-reveal .7s cubic-bezier(.2,.7,.2,1) both}
@keyframes mw-reveal{from{clip-path:inset(0 100% 0 0)} to{clip-path:inset(0 0 0 0)}}
.mw-frame{border:1.5px solid var(--mw-ink); background:#fff}
.mw-frame img{display:block; width:100%}
.mw-count{font-family:var(--mw-display); font-weight:700; font-size:clamp(6rem,15vw,12rem); line-height:.8; letter-spacing:-.07em; margin:0}
.mw-count.zero{color:var(--mw-grey)}
.mw-count em{font-style:normal; color:var(--mw-red)}
.mw-label{font-size:.7rem; letter-spacing:.14em; text-transform:uppercase; font-weight:700; margin:.6rem 0 1rem}

/* ---------- Map ---------- */
iframe[src*="openstreetmap.org"]{filter:grayscale(1) contrast(1.05); border:1.5px solid var(--mw-ink) !important; border-radius:0 !important}

/* ---------- Report ---------- */
.mw-report{border:1.5px solid var(--mw-ink); background:#fff; padding:clamp(1rem,3vw,2rem)}
.mw-report-top{display:flex; justify-content:space-between; gap:1rem; flex-wrap:wrap; border-bottom:1.5px solid var(--mw-ink); padding-bottom:.8rem; margin-bottom:1.2rem; align-items:flex-end}
.mw-report .mw-h3{font-family:var(--mw-display); font-weight:700; text-transform:uppercase; letter-spacing:-.04em; line-height:.95; font-size:clamp(1.8rem,4.6vw,3.6rem); margin:0 0 1.2rem; padding:0}
.mw-stamp{display:inline-block; border:2px solid var(--mw-ink); padding:.3rem .6rem; font-size:.68rem; letter-spacing:.14em; text-transform:uppercase; font-weight:700}
.mw-foot{border-top:1.5px solid var(--mw-ink); margin-top:clamp(3rem,8vw,6rem); padding-top:1rem; display:grid; grid-template-columns:repeat(12,1fr); gap:1rem 1.5rem}
.mw-foot p{grid-column:span 4; font-family:var(--mw-display); font-weight:700; text-transform:uppercase; letter-spacing:-.02em; font-size:clamp(1rem,1.8vw,1.35rem); line-height:1.1; margin:0}
.mw-foot small{grid-column:1 / -1; font-size:.72rem; color:var(--mw-grey-ink); line-height:1.6; max-width:80ch}
@media (max-width:860px){.mw-foot p{grid-column:1 / -1}}

/* ---------- Reduced motion ---------- */
@media (prefers-reduced-motion: reduce){
  *,*::before,*::after{animation-duration:.001ms !important; animation-iteration-count:1 !important; transition-duration:.001ms !important; scroll-behavior:auto !important}
  .mw-line{animation:none; top:50%}
}
</style>
"""


def _minify(css: str) -> str:
    """Blank lines or 4-space indents would make Markdown cut a <style> block short, so flatten it."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return _flat(css)


def inject_theme():
    st.markdown(_minify(THEME_CSS + EXTRA_CSS), unsafe_allow_html=True)


def _b64(path: Path, mime="image/jpeg") -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def masthead():
    html("""
    <header class="mw-mast">
      <div>
        <a class="mw-word" href="#top" aria-label="MOONWALK home">MOONWALK<i aria-hidden="true"></i></a>
        <div class="mw-desc">Urban infrastructure / Field reporting</div>
      </div>
      <nav class="mw-nav" aria-label="Primary">
        <a href="#scan">Scan</a><a href="#location">Location</a><a href="#file">File a report</a><a href="#privacy">Privacy</a>
      </nav>
    </header>
    """)


def hero(issue: str):
    img = ASSETS / "hero.jpg"
    fig = f'<img src="{_b64(img)}" alt="Water-filled potholes on a wet asphalt street">' if img.exists() else ""
    html(f"""
    <section class="mw-hero" id="top">
      <div class="mw-h1" role="heading" aria-level="1">Bad roads.<br>Good receipts<em>.</em></div>
      <aside>
        <div class="mw-meta">Issue {escape(issue)}</div>
        <p>Spot a pothole. Pin the location. Get the report ready.</p>
      </aside>
    </section>
    <figure class="mw-fig" style="margin-left:0;margin-right:0">{fig}
      <figcaption class="mw-cap mw-meta"><span>Fig. 01 / Street-level damage</span><span>The street is the source</span></figcaption>
    </figure>
    """)


def section(anchor: str, number: str, label: str, title: str, lede: str | None = None):
    lede_html = f'<div class="mw-lede" style="grid-column:4 / -1">{lede}</div>' if lede else ""
    html(f"""
    <div class="mw-sec" id="{anchor}">
      <div class="mw-meta">{escape(number)} / {escape(label)}</div>
      <div class="mw-h2" role="heading" aria-level="2">{title}</div>{lede_html}
    </div>
    """)


def note(kind: str, title: str, body: str, target=None):
    cls = {"warn": "warn", "err": "err"}.get(kind, "")
    html(f'<div class="mw-note {cls}" role="{"alert" if kind == "err" else "note"}"><b>{escape(title)}</b>{body}</div>', target)


def facts(rows, target=None):
    """rows: iterable of (label, value_html, big?)"""
    inner = "".join(
        f'<div><dt>{escape(l)}</dt><dd class="{"big" if big else ""}">{v}</dd></div>' for l, v, big in rows)
    html(f'<dl class="mw-facts">{inner}</dl>', target)


def scan_overlay(img_data_uri: str, tag: str) -> str:
    return _flat(f"""
    <div class="mw-scan" role="img" aria-label="{escape(tag)}">
      <img src="{img_data_uri}" alt="">
      <div class="mw-line"></div><div class="mw-tag">{escape(tag)}</div>
    </div>""")


def progress_bar(done: int, total: int) -> str:
    pct = 0 if total <= 0 else min(100, round(100 * done / total))
    return _flat(f"""
    <div class="mw-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{pct}"><span style="width:{pct}%"></span></div>
    <div class="mw-meta">Frame {done} of {total} · {pct}%</div>""")


def footer():
    html("""
    <footer class="mw-foot">
      <p>The street is the source.</p><p>The damage is the evidence.</p><p>The report is the action.</p>
      <small>MOONWALK prepares reports; it never files or sends a complaint for you. Detections are suggestions, not proof &mdash; review every result before you file.</small>
    </footer>
    """)


EXTRA_CSS = """
<style>
.mw-report-grid{display:grid; grid-template-columns:7fr 5fr; gap:1.5rem; align-items:start}
@media (max-width:860px){.mw-report-grid{grid-template-columns:1fr}}
.mw-report a{color:var(--mw-ink); text-underline-offset:3px}
.mw-report a:hover{text-decoration-color:var(--mw-red); text-decoration-thickness:2px}
</style>
"""

EXTRA_CSS += """
<style>
[data-testid="stCheckbox"] label p, [data-testid="stCheckbox"] p{white-space:normal !important; overflow:visible !important; text-overflow:clip !important}
.stLinkButton a, .stLinkButton a p, .stButton > button p, .stDownloadButton > button p{white-space:normal !important; overflow:visible !important; text-overflow:clip !important}
</style>
"""
