#!/usr/bin/env python3
"""Render a PR walkthrough page from its data file.

usage: render.py <data.json> <gather-dir> <out.html> [--css <extra.css>]

The data file holds what only the reader of the diff can write (see
reference/page-data.md). The layout, the progress bar, the collapsible blocks,
the counts, and the reading checkboxes come from here and from gather.sh's
meta.json and files.tsv. Errors go to stderr with exit 1. Fix the data and run
it again.
"""
import html
import json
import re
import sys

ROLES = {"behavior", "contract", "test", "config", "release", "docs", "generated"}
STATUSES = {"addressed", "partial", "not in this diff"}


def esc(text):
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(str(text or "")))


def plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def block(title, body, count=None, cls="", is_open=False):
    badge = f' <span class="count">{count}</span>' if count is not None else ""
    return (f'<details class="block{" " + cls if cls else ""}"{" open" if is_open else ""}>'
            f"<summary><h3>{title}</h3>{badge}</summary><div class=\"block-body\">{body}</div></details>")


def validate(data, stats):
    errors, warnings = [], []
    cohorts = data.get("cohorts") or []
    if not cohorts:
        errors.append("no cohorts")
    seen, assigned = set(), {}
    for i, c in enumerate(cohorts):
        cid = c.get("id", "")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", cid) or cid in seen or cid in ("housekeeping", "orientation", "ticket"):
            errors.append(f"cohort {i + 1}: id {cid!r} must be unique kebab-case and not housekeeping, orientation, or ticket")
        for dep in c.get("depends_on") or []:
            if dep not in seen:
                errors.append(f"cohort {cid}: depends on {dep!r}, which isn't an earlier cohort. Reorder, or merge cohorts that depend on each other")
        seen.add(cid)
        for path, role in (c.get("files") or {}).items():
            if role not in ROLES:
                errors.append(f"cohort {cid}: {path} has role {role!r}, not one of {sorted(ROLES)}")
            assigned.setdefault(path, []).append(cid)
        if len(c.get("author_questions") or []) > 3:
            errors.append(f"cohort {cid}: more than 3 author questions")
        if not 2 <= len(c.get("review_focus") or []) <= 4:
            warnings.append(f"cohort {cid}: review focus should have 2 to 4 questions")
    for row in data.get("housekeeping") or []:
        assigned.setdefault(row.get("path", ""), []).append("housekeeping")
    for path, owners in assigned.items():
        if path not in stats:
            errors.append(f"{path} is not in files.tsv")
        if len(owners) > 1:
            errors.append(f"{path} is in more than one cohort: {owners}")
    for path in stats:
        if path not in assigned:
            errors.append(f"{path} from files.tsv is in no cohort and not in housekeeping")
    for ask in (data.get("ticket") or {}).get("asks") or []:
        if ask.get("status") not in STATUSES:
            errors.append(f"ask {ask.get('ask')!r}: status must be one of {sorted(STATUSES)}")
    return errors, warnings


def cohort_section(c, links):
    cid = c["id"]
    b = c.get("behavior")
    behavior = ("<p>Behavior is unchanged.</p>" if not b else
                f'<table class="delta"><tr class="before"><th>Before</th><td>{esc(b.get("before"))}</td></tr>'
                f'<tr class="after"><th>After</th><td>{esc(b.get("after"))}</td></tr></table>')
    diagram = f'<div class="diagram"><pre class="mermaid">{html.escape(c["diagram"])}</pre></div>' if c.get("diagram") else ""
    focus = c.get("review_focus") or []
    focus_html = "<ul>" + "".join(f"<li>{esc(q.get('q'))} <code>{esc(q.get('where'))}</code></li>" for q in focus) + "</ul>"
    questions = c.get("author_questions") or []
    author = ""
    if questions:
        author = block("Only the author knows",
                       "<p class=\"note\">The PR description wasn't read, so it may already answer some of these.</p><ul>"
                       + "".join(f"<li>{esc(q.get('q'))} <code>{esc(q.get('where'))}</code><br><span class=\"note\">Looked for: {esc(q.get('looked_for'))}</span></li>" for q in questions)
                       + "</ul>", len(questions), "author", True)
    layers = c.get("layers") or []
    items = []
    for j, l in enumerate(layers, 1):
        path = str(l.get("where", "")).split(":")[0]
        code = (f'<figure><figcaption>{esc(path)}</figcaption><pre><code>{html.escape(l["code"])}</code></pre></figure>'
                if l.get("code") else "")
        count = f' <span class="note">{esc(l["count"])}</span>' if l.get("count") else ""
        items.append(f'<li id="{cid}-layer-{j}"><code>{esc(l.get("where"))}</code>: {esc(l.get("does"))}{count}{code}</li>')
    blast = c.get("blast_radius") or []
    blast_html = ("<ul>" + "".join(f"<li>{esc(x)}</li>" for x in blast) + "</ul>" if blast
                  else "<p>Nothing outside this diff calls the changed code.</p>")
    tests = c.get("tests") or {}
    asserted, gaps = tests.get("asserted") or [], tests.get("gaps") or []
    tests_html = ("<p><strong>Asserted:</strong></p><ul>" + "".join(f"<li>{esc(x)}</li>" for x in asserted or ["Nothing in this diff."]) + "</ul>"
                  "<p><strong>No assertion:</strong></p><ul>" + "".join(f"<li>{esc(x)}</li>" for x in gaps or ["No gaps found."]) + "</ul>")
    deps = c.get("depends_on") or []
    return f"""
<section id="{cid}">
  <h2>{esc(c['name'])} <label class="check"><input type="checkbox" data-cohort="{cid}"> I've read this</label></h2>
  <p class="deps">Depends on: {links(deps) or 'nothing'}</p>
  <p>{esc(c.get('what_changed'))}</p>
  {block("Behavior delta", behavior, is_open=True)}
  {diagram}
  {block("Review focus", focus_html, len(focus), "focus", True)}
  {author}
  {block("Layers", "<ol>" + "".join(items) + "</ol>", len(layers))}
  {block("Blast radius", blast_html, len(blast))}
  {block("Test coverage", tests_html, f"{len(asserted)} asserted · {plural(len(gaps), 'gap')}")}
</section>"""


def main(argv):
    if len(argv) < 4:
        sys.exit(__doc__)
    data = json.load(open(argv[1]))
    gather, out = argv[2], argv[3]
    extra_css = open(argv[argv.index("--css") + 1]).read() if "--css" in argv else ""
    meta = json.load(open(f"{gather}/meta.json"))
    stats = {}
    for line in open(f"{gather}/files.tsv"):
        parts = line.rstrip("\n").split("\t")
        if len(parts) == 4:
            stats[parts[3]] = (int(parts[1] or 0), int(parts[2] or 0))

    errors, warnings = validate(data, stats)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    cohorts = data["cohorts"]
    housekeeping = data.get("housekeeping") or []
    repo = re.search(r"github\.com/([^/]+/[^/]+)/pull", meta["url"]).group(1)
    number = meta["number"]
    names = {c["id"]: c["name"] for c in cohorts}
    links = lambda ids: ", ".join(f'<a href="#{d}">{esc(names[d])}</a>' for d in ids)

    rows = [f"<tr><td><a href=\"#{c['id']}\">{esc(c['name'])}</a></td><td>{esc(c.get('summary'))}</td>"
            f"<td>{links(c.get('depends_on') or []) or '–'}</td></tr>" for c in cohorts]
    sections = [cohort_section(c, links) for c in cohorts]
    if housekeeping:
        rows.append(f'<tr><td><a href="#housekeeping">Housekeeping</a></td><td>{plural(len(housekeeping), "file")}</td><td>–</td></tr>')
        bumps = data.get("version_bump") or []
        bumps = [bumps] if isinstance(bumps, dict) else bumps
        bump_html = "".join(
            f"<p>Version bump{' for <code>' + esc(b['package']) + '</code>' if b.get('package') else ''}: "
            f"<code>{esc(b.get('from'))}</code> to <code>{esc(b.get('to'))}</code>. {esc(b.get('convention'))}</p>"
            for b in bumps)
        hk_rows = "".join(f"<tr><td><code>{esc(r.get('path'))}</code></td><td>{esc(r.get('kind'))}</td><td>{esc(r.get('note'))}</td></tr>" for r in housekeeping)
        sections.append(f"""
<section id="housekeeping">
  <h2>Housekeeping <label class="check"><input type="checkbox" data-cohort="housekeeping"> I've read this</label></h2>
  <div class="scroll"><table><tr><th>File</th><th>Kind</th><th>Note</th></tr>
  {hk_rows}
  </table></div>{bump_html}
</section>""")
    areas = len(cohorts) + (1 if housekeeping else 0)

    ticket = data.get("ticket")
    if ticket:
        asks = "".join(f"<tr><td>{esc(a.get('ask'))}</td><td>{esc(a.get('status'))}</td><td><code>{esc(a.get('where'))}</code> {esc(a.get('note'))}</td></tr>"
                       for a in ticket.get("asks") or [])
        asks_html = (f'<div class="scroll"><table><tr><th>Ask</th><th>In this diff</th><th>Where</th></tr>{asks}</table></div>' if asks
                     else "<p>The ticket lists no asks.</p>")
        unasked = "".join(f"<li>{esc(x)}</li>" for x in ticket.get("unasked") or [])
        ticket_html = (f'<p><a href="{html.escape(ticket.get("url", ""))}">{esc(ticket.get("key"))}</a>: {esc(ticket.get("summary"))}</p>'
                       + asks_html + (f"<p>Changes no ask covers:</p><ul>{unasked}</ul>" if unasked else ""))
    else:
        ticket_html = "<p>The PR title and branch carry no ticket key.</p>"

    m = re.match(r"([a-z]+(?:\([^)]*\))?!?:\s*(?:[A-Z][A-Z0-9]+-\d+\b)?)\s*(.+)", meta["title"])
    h1 = (f'<span class="h1-scope">{esc(m.group(1).strip())}</span> {esc(m.group(2))}' if m else esc(meta["title"]))
    labels = [l["name"] for l in meta.get("labels") or []]
    label_row = (f'<div><dt>Labels</dt><dd class="chips">{"".join(f"<span>{esc(l)}</span>" for l in labels)}</dd></div>' if labels else "")
    first = data.get("open_first") or {}
    order = " → ".join(esc(c["name"]) for c in cohorts)
    mermaid = ('<script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"; mermaid.initialize({startOnLoad: true});</script>'
               if any(c.get("diagram") for c in cohorts) else "")
    key = json.dumps(f"pr-walkthrough:{repo}#{number}@{meta['headRefOid']}")

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Lato:wght@400;700;900&display=swap" rel="stylesheet">
<title>Walkthrough of {html.escape(repo)} #{number}</title>
<style>{CSS}{extra_css}</style></head>
<body><div class="progressbar"><div class="progressbar-inner"><span class="progressbar-label" data-progress>0 of {areas} areas read</span><div class="progressbar-track" role="progressbar" aria-label="Review progress" aria-valuemin="0" aria-valuenow="0" aria-valuemax="{areas}"><div class="progressbar-fill" data-progress-fill></div></div></div></div>
<div class="layout">
<main>
  <header>
  <p class="eyebrow">{html.escape(repo)} #{number}</p>
  <h1>{h1}</h1>
  <p class="lede">{esc(data.get('lede'))}</p>
  <dl class="facts">
    <div><dt>Author</dt><dd>{esc(meta['author']['login'])}</dd></div>
    <div><dt>Branch</dt><dd><code>{esc(meta['baseRefName'])}</code> ← <code>{esc(meta['headRefName'])}</code></dd></div>
    <div><dt>Size</dt><dd>{plural(meta['changedFiles'], 'file')} · <span class="add">+{meta['additions']}</span> / <span class="del">-{meta['deletions']}</span></dd></div>
    {label_row}
  </dl>
</header>
  <section id="orientation"><h2>Orientation</h2>
  <div class="scroll"><table><tr><th>Area</th><th>What changed</th><th>Depends on</th></tr>{''.join(rows)}</table></div>
  <p>Read in this order: {order}.</p>
  <p>Open first: <code>{esc(first.get('path'))}</code>, {esc(first.get('why'))}</p></section>
  <section id="ticket"><h2>Ticket</h2>{ticket_html}</section>
  {''.join(sections)}
</main>
</div>
{mermaid}
<script>{PROGRESS_JS.replace("__KEY__", key)}</script>
<script>{HASH_JS}</script>
</body></html>
"""
    open(out, "w").write(page)
    print(out)


CSS = r'''
:root { color-scheme: dark; --brand: #00a87e; --brand-dark: #00986a; --brand-soft: rgba(0,168,126,.14); --surface: #1c1d20; --surface-2: #282a2e; --warn: #f4be19; --good: #00a87e; --bad: #e05666; --fg: #fafafa; --muted: #a3a4ab; --line: #34363c; --bg: #121212; --code-bg: #282a2e; --accent: #2cc39a; --before: rgba(224,86,102,.12); --after: rgba(0,168,126,.12); }
* { box-sizing: border-box; }
body { margin: 0; font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--fg); background: var(--bg); }
.layout { max-width: 920px; margin: 0 auto; padding: 24px; }
a { color: var(--accent); }
.eyebrow, .facts, .note, .deps { color: var(--muted); font-size: 13px; }
h1 { font-size: 26px; margin: 4px 0 8px; }
h2 { font-size: 20px; margin: 40px 0 8px; padding-top: 16px; border-top: 1px solid var(--line); display: flex; justify-content: space-between; align-items: baseline; gap: 16px; }
h3 { font-size: 15px; margin: 20px 0 6px; }
.lede { font-size: 17px; }
.check { font-size: 13px; font-weight: 400; color: var(--muted); white-space: nowrap; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { border: 1px solid var(--line); padding: 6px 8px; text-align: left; vertical-align: top; }
.delta .before { background: var(--before); }
.delta .after { background: var(--after); }
code { font: 13px ui-monospace, SFMono-Regular, Menlo, monospace; background: var(--code-bg); padding: 1px 4px; border-radius: 4px; overflow-wrap: anywhere; }
figure { margin: 8px 0; }
figcaption { font: 12px ui-monospace, Menlo, monospace; color: var(--muted); }
pre { background: var(--code-bg); padding: 10px; border-radius: 6px; overflow: auto; }
pre code { background: none; padding: 0; }

.layout { max-width: 880px; }
body { font-size: 16px; line-height: 1.65; }
p, li { max-width: 72ch; }
.lede { font-size: 18px; line-height: 1.6; color: var(--fg); }
section { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 4px 24px 20px; margin: 24px 0; }
h2 { margin: 16px 0 8px; padding-top: 0; border-top: 0; font-size: 21px; }
.deps { margin-top: 0; }
section > p:not(.deps) { color: var(--fg); }
details.block { border-top: 1px solid var(--line); margin-top: 14px; }
details.block > summary { list-style: none; cursor: pointer; display: flex; align-items: center; gap: 10px; padding: 10px 0 6px; }
details.block > summary::-webkit-details-marker { display: none; }
details.block > summary::before { content: "\25B8"; color: var(--muted); font-size: 12px; transition: transform .15s; width: 10px; }
details.block[open] > summary::before { transform: rotate(90deg); }
details.block > summary h3 { margin: 0; font-size: 13px; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); }
details.block > summary:hover h3 { color: var(--fg); }
.count { font-size: 12px; color: var(--muted); background: var(--code-bg); border-radius: 999px; padding: 1px 8px; }
.block-body { padding: 2px 0 4px 20px; }
details.author > summary h3 { color: var(--warn); }
.block-body ol, .block-body ul { padding-left: 20px; margin: 6px 0; }
.block-body li { margin: 10px 0; }
.block-body ol > li > code:first-child { display: block; width: fit-content; max-width: 100%; margin-bottom: 4px; font-size: 12px; color: var(--muted); }
.block-body p strong { font-size: 13px; text-transform: uppercase; letter-spacing: .05em; }
.delta th { width: 76px; font-size: 12px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); }
.delta td, .delta th { border: 0; padding: 10px 12px; }
.delta tr.before td, .delta tr.before th { border-left: 3px solid var(--bad); }
.delta tr.after td, .delta tr.after th { border-left: 3px solid var(--good); }
.delta tr.after th, .delta tr.before th { border-left-width: 3px; }
.delta td { border-left: 0 !important; }
.delta { border-radius: 8px; overflow: hidden; }
.scroll { overflow-x: auto; }
.scroll table { min-width: 480px; }
th { color: var(--muted); font-weight: 600; font-size: 13px; }
.focus li > code:last-child, .author li > code:last-of-type { display: block; width: fit-content; max-width: 100%; margin-top: 4px; font-size: 12px; color: var(--muted); }
.diagram { margin: 14px 0 0; padding: 12px; background: var(--code-bg); border-radius: 8px; overflow-x: auto; }
.diagram pre { margin: 0; background: none; }
.note { font-style: italic; }
@media (max-width: 640px) { .layout { padding: 12px; } section { padding: 4px 14px 14px; } .block-body { padding-left: 4px; } }

body { font-family: Lato, "Helvetica Neue", Arial, sans-serif; }
h1, h2, h3, h1 { font-weight: 900; font-size: 26px; line-height: 1.3; letter-spacing: -.01em; margin: 6px 0 12px; }
h2 { font-weight: 900; }
section { border-radius: 16px; border-color: var(--line); }
section h2 { color: var(--fg); }
section h2::before { content: ""; display: inline-block; width: 4px; height: 20px; border-radius: 2px; background: var(--brand); margin-right: 10px; vertical-align: -3px; }
h2 { justify-content: flex-start; gap: 0; }
.author li > br { display: none; }
.author li > span.note { display: block; margin-top: 6px; }
h2 .check { margin-left: auto; }
.check input { accent-color: var(--brand); width: 16px; height: 16px; vertical-align: -3px; }
details.block > summary::before { color: var(--brand); }
details.block > summary:hover h3 { color: var(--brand); }
.count { background: var(--brand-soft); color: var(--accent); font-weight: 700; }
details.author > summary h3 { color: var(--warn); }
th { background: var(--surface-2); color: var(--muted); }
.delta th { background: transparent; }
code { color: #e2e2e2; }
a { color: var(--accent); text-decoration-color: rgba(44,195,154,.4); text-underline-offset: 2px; }
a:hover { color: #fff; text-decoration-color: var(--brand); }
.diagram { border: 1px solid var(--line); }
::selection { background: rgba(0,168,126,.4); }

header { background: var(--surface); border: 1px solid var(--line); border-top: 3px solid var(--brand); border-radius: 16px; padding: 20px 24px 18px; margin: 20px 0 8px; }
header .eyebrow { margin: 0; font-size: 12px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--accent); }
.h1-scope { display: block; font-size: 14px; font-weight: 700; letter-spacing: 0; color: var(--muted); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; margin-bottom: 2px; }
header .lede { font-size: 16px; line-height: 1.65; color: #d4d5da; margin: 0 0 16px; }
dl.facts { display: grid; grid-template-columns: auto 1fr; gap: 8px 16px; margin: 0; padding-top: 14px; border-top: 1px solid var(--line); font-size: 13px; color: var(--fg); }
dl.facts > div { display: contents; }
dl.facts dt { color: var(--muted); font-weight: 700; font-size: 11px; letter-spacing: .06em; text-transform: uppercase; padding-top: 3px; }
dl.facts dd { margin: 0; min-width: 0; }
dl.facts .add { color: var(--good); font-weight: 700; }
dl.facts .del { color: var(--bad); font-weight: 700; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chips span { font-size: 12px; border: 1px solid var(--line); border-radius: 999px; padding: 1px 10px; color: var(--muted); }

h2 { align-items: center; }
h2 .check { display: inline-flex; align-items: center; gap: 8px; line-height: 1; cursor: pointer; flex-shrink: 0; }
h2 .check input { margin: 0; vertical-align: middle; width: 16px; height: 16px; flex: none; cursor: pointer; }

.progressbar { position: sticky; top: 0; z-index: 10; padding-top: env(safe-area-inset-top, 0px); background: rgba(18,18,18,.88); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-bottom: 1px solid var(--line); }
.progressbar-inner { max-width: 880px; margin: 0 auto; padding: 10px 24px; display: flex; align-items: center; gap: 14px; }
.progressbar-label { font-weight: 700; font-size: 13px; white-space: nowrap; color: var(--fg); min-width: 130px; }
.progressbar-track { flex: 1; height: 8px; border-radius: 999px; background: var(--surface-2); overflow: hidden; }
.progressbar-fill { height: 100%; width: 0; border-radius: 999px; background: linear-gradient(90deg, #00986a, #00a87e, #2cc39a); transition: width .35s ease; }
.all-read .progressbar-label { color: var(--accent); }
html { scroll-padding-top: calc(52px + env(safe-area-inset-top, 0px)); }
section { scroll-margin-top: calc(60px + env(safe-area-inset-top, 0px)); transition: opacity .2s; }
section.is-read:not(.peek) > :not(h2) { display: none !important; }
section.is-read { padding-bottom: 4px; opacity: .78; }
section.is-read:hover, section.is-read.peek { opacity: 1; }
section.is-read h2 { cursor: pointer; margin: 12px 0; }
section.is-read h2::before { background: var(--muted); }
section.is-read h2::after { content: "Read \2713  \00B7  click to show"; order: 1; margin-left: 12px; font-size: 12px; font-weight: 700; color: var(--accent); background: var(--brand-soft); border-radius: 999px; padding: 2px 10px; white-space: nowrap; }
section.is-read.peek h2::after { content: "Read \2713  \00B7  click to hide"; }
section.is-read h2 .check { order: 2; }
#orientation a.read::after { content: " \2713"; color: var(--accent); }
@media (max-width: 640px) { .progressbar-inner { padding: 8px 12px; } .progressbar-label { min-width: 0; } section.is-read h2 { flex-wrap: wrap; row-gap: 6px; } }
'''

PROGRESS_JS = r'''
(() => {
  const key = __KEY__;
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(key) || "{}"); } catch (e) {}
  const boxes = [...document.querySelectorAll("input[data-cohort]")];
  const label = document.querySelector("[data-progress]");
  const fill = document.querySelector("[data-progress-fill]");
  const bar = document.querySelector(".progressbar [role=progressbar]");
  const sectionOf = (b) => b.closest("section");
  const update = () => {
    const done = boxes.filter((b) => b.checked).length;
    if (label) label.textContent = done === boxes.length ? `All ${boxes.length} areas read` : `${done} of ${boxes.length} areas read`;
    if (fill) fill.style.width = `${boxes.length ? (done / boxes.length) * 100 : 0}%`;
    if (bar) { bar.setAttribute("aria-valuenow", String(done)); bar.setAttribute("aria-valuemax", String(boxes.length)); }
    document.documentElement.classList.toggle("all-read", done === boxes.length);
    for (const b of boxes) {
      const sec = sectionOf(b);
      if (sec) { sec.classList.toggle("is-read", b.checked); if (!b.checked) sec.classList.remove("peek"); }
      for (const a of document.querySelectorAll(`#orientation a[href="#${b.dataset.cohort}"]`)) a.classList.toggle("read", b.checked);
    }
  };
  for (const b of boxes) {
    b.checked = !!saved[b.dataset.cohort];
    b.addEventListener("change", () => {
      saved[b.dataset.cohort] = b.checked;
      try { localStorage.setItem(key, JSON.stringify(saved)); } catch (e) {}
      const sec = sectionOf(b);
      if (sec) sec.classList.remove("peek");
      update();
      if (b.checked && sec && sec.getBoundingClientRect().top < 0) sec.scrollIntoView({ block: "start" });
    });
    const h2 = b.closest("h2");
    if (h2) h2.addEventListener("click", (ev) => {
      if (ev.target.closest("label")) return;
      const sec = sectionOf(b);
      if (sec && sec.classList.contains("is-read")) sec.classList.toggle("peek");
    });
  }
  window.addEventListener("hashchange", () => {
    const el = document.getElementById(location.hash.slice(1));
    const sec = el && el.closest("section.is-read");
    if (sec && el !== sec) { sec.classList.add("peek"); el.scrollIntoView(); }
  });
  update();
})();
'''

HASH_JS = r'''
(() => {
  const openTarget = () => {
    const id = location.hash.slice(1); if (!id) return;
    const el = document.getElementById(id); const d = el && el.closest("details");
    if (d) { d.open = true; el.scrollIntoView(); }
  };
  window.addEventListener("hashchange", openTarget); openTarget();
})();
'''

if __name__ == "__main__":
    main(sys.argv)
