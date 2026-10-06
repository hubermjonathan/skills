#!/usr/bin/env python3
"""Render a PR walkthrough page from its data file.

usage: render.py <data.json> <gather-dir> <out.html> [--css <extra.css>]

The data file holds what only the reader of the diff can write (see
reference/page-data.md). Counts, read times, links, the layout, and the reading
checkboxes come from here and from gather.sh's meta.json and files.tsv.
Errors go to stderr with exit 1. Fix the data and run it again.
"""
import html
import json
import math
import re
import sys

ROLES = {"behavior", "contract", "test", "config", "release", "docs", "generated"}
STATUSES = {"addressed", "partial", "not in this diff"}


def esc(text):
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(str(text or "")))


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

    errors, warnings = [], []
    cohorts = data.get("cohorts") or []
    housekeeping = data.get("housekeeping") or []
    if not cohorts:
        errors.append("no cohorts")
    seen, assigned = {}, {}
    for i, c in enumerate(cohorts):
        cid = c.get("id", "")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", cid) or cid in seen or cid == "housekeeping":
            errors.append(f"cohort {i + 1}: id {cid!r} must be unique kebab-case and not 'housekeeping'")
        for dep in c.get("depends_on") or []:
            if dep not in seen:
                errors.append(f"cohort {cid}: depends on {dep!r}, which isn't an earlier cohort. Reorder, or merge cohorts that depend on each other")
        seen[cid] = i
        for path, role in (c.get("files") or {}).items():
            if role not in ROLES:
                errors.append(f"cohort {cid}: {path} has role {role!r}, not one of {sorted(ROLES)}")
            assigned.setdefault(path, []).append(cid)
        if len(c.get("author_questions") or []) > 3:
            errors.append(f"cohort {cid}: more than 3 author questions")
        if not 2 <= len(c.get("review_focus") or []) <= 4:
            warnings.append(f"cohort {cid}: review focus should have 2 to 4 questions")
    for row in housekeeping:
        assigned.setdefault(row.get("path", ""), []).append("housekeeping")
    for path, owners in assigned.items():
        if path not in stats:
            errors.append(f"{path} is not in files.tsv")
        if len(owners) > 1:
            errors.append(f"{path} is in more than one cohort: {owners}")
    for path in stats:
        if path not in assigned:
            errors.append(f"{path} from files.tsv is in no cohort and not in housekeeping")
    ticket = data.get("ticket")
    for ask in (ticket or {}).get("asks") or []:
        if ask.get("status") not in STATUSES:
            errors.append(f"ask {ask.get('ask')!r}: status must be one of {sorted(STATUSES)}")
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    repo = re.search(r"github\.com/([^/]+/[^/]+)/pull", meta["url"]).group(1)
    sha = meta["headRefOid"]

    def counts(files):
        add = sum(stats[p][0] for p in files)
        dele = sum(stats[p][1] for p in files)
        code = sum(sum(stats[p]) for p, r in files.items() if r in ("behavior", "contract"))
        lines = code or add + dele
        return len(files), add, dele, max(1, math.ceil(lines / 10))

    names = {c["id"]: c["name"] for c in cohorts}
    links = lambda ids: ", ".join(f'<a href="#{d}">{esc(names[d])}</a>' for d in ids)
    nav, toc, rows, sections = [], [], [], []

    for c in cohorts:
        cid = c["id"]
        n, add, dele, minutes = counts(c.get("files") or {})
        questions = c.get("author_questions") or []
        deps = c.get("depends_on") or []
        nav.append(f'<a href="#{cid}" data-nav="{cid}">{esc(c["name"])}</a>')
        rows.append(f"<tr><td><a href=\"#{cid}\">{esc(c['name'])}</a></td><td>{esc(c.get('summary'))}</td>"
                    f"<td>{links(deps) or '–'}</td><td>{n}</td><td>+{add} / -{dele}</td><td>{minutes} min</td><td>{len(questions) or '–'}</td></tr>")
        layers = c.get("layers") or []
        toc.append(f'<p><a href="#{cid}">{esc(c["name"])}</a></p><ul>'
                   + "".join(f'<li><a href="#{cid}-layer-{j}"><code>{esc(l.get("where"))}</code></a></li>' for j, l in enumerate(layers, 1))
                   + "</ul>")
        b = c.get("behavior")
        behavior = ("<p>Behavior is unchanged.</p>" if not b else
                    f'<table class="delta"><tr class="before"><th>Before</th><td>{esc(b.get("before"))}</td></tr>'
                    f'<tr class="after"><th>After</th><td>{esc(b.get("after"))}</td></tr></table>')
        layer_items = []
        for j, l in enumerate(layers, 1):
            path = str(l.get("where", "")).split(":")[0]
            code = (f'<figure><figcaption>{esc(path)}</figcaption><pre><code>{html.escape(l["code"])}</code></pre></figure>'
                    if l.get("code") else "")
            count = f' <span class="note">{esc(l["count"])}</span>' if l.get("count") else ""
            layer_items.append(f'<li id="{cid}-layer-{j}"><code>{esc(l.get("where"))}</code>: {esc(l.get("does"))}{count}{code}</li>')
        diagram = f'<pre class="mermaid">{html.escape(c["diagram"])}</pre>' if c.get("diagram") else ""
        blast = c.get("blast_radius") or []
        blast_html = ("<ul>" + "".join(f"<li>{esc(x)}</li>" for x in blast) + "</ul>" if blast
                      else "<p>Nothing outside this diff calls the changed code.</p>")
        tests = c.get("tests") or {}
        tests_html = ("<p><strong>Asserted:</strong></p><ul>" + "".join(f"<li>{esc(x)}</li>" for x in tests.get("asserted") or ["Nothing in this diff."]) + "</ul>"
                      "<p><strong>No assertion:</strong></p><ul>" + "".join(f"<li>{esc(x)}</li>" for x in tests.get("gaps") or ["No gaps found."]) + "</ul>")
        focus = "".join(f"<li>{esc(q.get('q'))} <code>{esc(q.get('where'))}</code></li>" for q in c.get("review_focus") or [])
        asks_author = ""
        if questions:
            asks_author = ('<h3>Only the author knows</h3><p class="note">The PR description wasn\'t read, so it may already answer some of these.</p><ul>'
                           + "".join(f"<li>{esc(q.get('q'))} <code>{esc(q.get('where'))}</code><br><span class=\"note\">Looked for: {esc(q.get('looked_for'))}</span></li>" for q in questions)
                           + "</ul>")
        sections.append(f"""
<section id="{cid}">
  <h2>{esc(c['name'])} <label class="check"><input type="checkbox" data-cohort="{cid}"> I've read this</label></h2>
  <p class="deps">Depends on: {links(deps) or 'nothing'}</p>
  <p>{esc(c.get('what_changed'))}</p>
  <h3>Behavior delta</h3>{behavior}
  <h3>Layers</h3><ol>{''.join(layer_items)}</ol>
  {diagram}
  <h3>Blast radius</h3>{blast_html}
  <h3>Test coverage</h3>{tests_html}
  <h3>Review focus</h3><ul>{focus}</ul>
  {asks_author}
</section>""")

    hk_files = {r["path"]: "release" for r in housekeeping}
    if housekeeping:
        hn, hadd, hdel, _ = counts(hk_files)
        rows.append(f"<tr><td><a href=\"#housekeeping\">Housekeeping</a></td><td>{len(housekeeping)} files</td><td>–</td><td>{hn}</td><td>+{hadd} / -{hdel}</td><td>–</td><td>–</td></tr>")
        nav.append('<a href="#housekeeping" data-nav="housekeeping">Housekeeping</a>')
        bump = data.get("version_bump")
        bump_html = (f"<p>Version bump: <code>{esc(bump.get('from'))}</code> to <code>{esc(bump.get('to'))}</code>. {esc(bump.get('convention'))}</p>"
                     if bump else "")
        sections.append(f"""
<section id="housekeeping">
  <h2>Housekeeping <label class="check"><input type="checkbox" data-cohort="housekeeping"> I've read this</label></h2>
  <table><tr><th>File</th><th>Kind</th><th>Note</th></tr>
  {''.join(f"<tr><td><code>{esc(r.get('path'))}</code></td><td>{esc(r.get('kind'))}</td><td>{esc(r.get('note'))}</td></tr>" for r in housekeeping)}
  </table>{bump_html}
</section>""")

    if ticket:
        asks = "".join(f"<tr><td>{esc(a.get('ask'))}</td><td>{esc(a.get('status'))}</td><td><code>{esc(a.get('where'))}</code> {esc(a.get('note'))}</td></tr>"
                       for a in ticket.get("asks") or [])
        unasked = "".join(f"<li>{esc(x)}</li>" for x in ticket.get("unasked") or [])
        ticket_html = (f'<p><a href="{html.escape(ticket.get("url", ""))}">{esc(ticket.get("key"))}</a>: {esc(ticket.get("summary"))}</p>'
                       f"<table><tr><th>Ask</th><th>In this diff</th><th>Where</th></tr>{asks}</table>"
                       + (f"<p>Changes no ask covers:</p><ul>{unasked}</ul>" if unasked else ""))
    else:
        ticket_html = "<p>The PR title and branch carry no ticket key.</p>"

    order = " → ".join(esc(c["name"]) for c in cohorts)
    first = data.get("open_first") or {}
    labels = ", ".join(l["name"] for l in meta.get("labels") or []) or "none"
    mermaid = ('<script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"; mermaid.initialize({startOnLoad: true});</script>'
               if any(c.get("diagram") for c in cohorts) else "")
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Walkthrough of {html.escape(repo)} #{meta['number']}</title>
<style>{CSS}{extra_css}</style></head>
<body><div class="layout">
<nav class="rail"><p class="progress" data-progress></p>
  <a href="#orientation" aria-current="page">Orientation</a><a href="#ticket">Ticket</a>{''.join(nav)}</nav>
<main>
  <header><p class="eyebrow">{html.escape(repo)} #{meta['number']}</p><h1>{esc(meta['title'])}</h1>
  <p class="lede">{esc(data.get('lede'))}</p>
  <p class="facts">{esc(meta['author']['login'])} · <code>{esc(meta['baseRefName'])}</code> ← <code>{esc(meta['headRefName'])}</code> · {meta['changedFiles']} files · +{meta['additions']} / -{meta['deletions']} · labels: {esc(labels)}</p></header>
  <section id="orientation"><h2>Orientation</h2>
  <table><tr><th>Area</th><th>What changed</th><th>Depends on</th><th>Files</th><th>+ / -</th><th>Read</th><th>For the author</th></tr>{''.join(rows)}</table>
  <p>Read in this order: {order}.</p>
  <p>Open first: <code>{esc(first.get('path'))}</code>, {esc(first.get('why'))}</p></section>
  <section id="ticket"><h2>Ticket</h2>{ticket_html}</section>
  {''.join(sections)}
  <footer><p>Nothing was posted to the PR. The PR description and comments weren't read: the diff, the ticket, and the repo are the only sources. This page maps head <code>{sha}</code>.</p></footer>
</main>
<aside class="toc">{''.join(toc)}</aside>
</div>
{mermaid}
<script>
(() => {{
  const key = {json.dumps(f"pr-walkthrough:{repo}#{meta['number']}@{sha}")};
  let saved = {{}};
  try {{ saved = JSON.parse(localStorage.getItem(key) || "{{}}"); }} catch (e) {{}}
  const boxes = [...document.querySelectorAll("input[data-cohort]")];
  const progress = document.querySelector("[data-progress]");
  const update = () => {{
    const done = boxes.filter((b) => b.checked).length;
    progress.textContent = `${{done}} of ${{boxes.length}} read`;
    for (const b of boxes) {{
      for (const n of document.querySelectorAll(`[data-nav="${{b.dataset.cohort}}"]`)) n.classList.toggle("read", b.checked);
    }}
  }};
  for (const b of boxes) {{
    b.checked = !!saved[b.dataset.cohort];
    b.addEventListener("change", () => {{
      saved[b.dataset.cohort] = b.checked;
      try {{ localStorage.setItem(key, JSON.stringify(saved)); }} catch (e) {{}}
      update();
    }});
  }}
  update();
}})();
</script>
</body></html>
"""
    open(out, "w").write(page)
    print(out)


CSS = """
:root { --fg: #1d1d1f; --muted: #6e6e73; --line: #d2d2d7; --bg: #fff; --code-bg: #f5f5f7; --accent: #0066cc; --before: #fff4f2; --after: #f0f9f1; }
* { box-sizing: border-box; }
body { margin: 0; font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--fg); background: var(--bg); }
.layout { display: grid; grid-template-columns: 220px minmax(0, 1fr) 240px; gap: 32px; max-width: 1400px; margin: 0 auto; padding: 24px; }
.rail, .toc { position: sticky; top: 24px; align-self: start; max-height: calc(100vh - 48px); overflow: auto; font-size: 13px; }
.rail a { display: block; padding: 4px 0; color: var(--fg); text-decoration: none; }
.rail a[aria-current="page"] { font-weight: 600; }
.rail a.read::after { content: " \\2713"; color: var(--muted); }
.progress { color: var(--muted); margin: 0 0 12px; }
.toc ul { margin: 0 0 12px; padding-left: 16px; }
.toc a { color: var(--accent); text-decoration: none; }
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
footer { margin-top: 48px; color: var(--muted); font-size: 13px; }
@media (max-width: 1100px) { .layout { grid-template-columns: 1fr; } .rail, .toc { position: static; max-height: none; } }
"""

if __name__ == "__main__":
    main(sys.argv)
