#!/usr/bin/env python3
import collections
import hashlib
import html
import json
import os
import re
import sys

ROLES = {"behavior", "contract", "config", "docs"}
SKETCH_KINDS = {"mermaid", "tree-diff"}
WORD_CAPS = {"summary": 50, "gist": 15, "change": 12, "note": 15, "question": 30, "test": 12}
ADDED, REMOVED = "#00a87e", "#e05666"
PALETTES = {
    "light": {"bg": "#ffffff", "text": "#121212", "line": "#505050", "node": "#f7f7f7", "border": "#8a8a8a",
              "added": "#def3ec", "removed": "#ffd7df", "note": "#fdf2cc", "cluster": "#fafafa"},
    "dark": {"bg": "#121215", "text": "#f7f7f7", "line": "#ababab", "node": "#282a2e", "border": "#8a8a8a",
             "added": "#0e382f", "removed": "#462329", "note": "#3f3416", "cluster": "#1e2024"},
}


def mermaid_config(mode):
    c = PALETTES[mode]
    return {
        "startOnLoad": False,
        "theme": "base",
        "themeVariables": {
            "darkMode": mode == "dark", "background": c["bg"], "fontFamily": "Lato", "fontSize": "16px",
            "textColor": c["text"], "primaryTextColor": c["text"], "lineColor": c["line"],
            "primaryColor": c["node"], "primaryBorderColor": c["border"], "secondaryColor": c["node"], "tertiaryColor": c["bg"],
            "actorBkg": c["node"], "actorBorder": c["border"], "actorTextColor": c["text"], "actorLineColor": c["border"],
            "signalColor": c["text"], "signalTextColor": c["text"],
            "labelBoxBkgColor": c["bg"], "labelBoxBorderColor": c["border"], "labelTextColor": c["text"], "loopTextColor": c["text"],
            "noteBkgColor": c["note"], "noteBorderColor": "#f4be19", "noteTextColor": c["text"],
            "edgeLabelBackground": c["bg"], "clusterBkg": c["cluster"], "clusterBorder": c["border"],
        },
        "sequence": {"mirrorActors": False, "actorMargin": 30},
        "themeCSS": (f".node.added rect,.node.added polygon,.node.added circle,.node.added path{{fill:{c['added']} !important;stroke:{ADDED} !important;stroke-width:2px !important}}"
                     f".node.removed rect,.node.removed polygon,.node.removed circle,.node.removed path{{fill:{c['removed']} !important;stroke:{REMOVED} !important;stroke-dasharray:5 3 !important}}"
                     ".node.removed .nodeLabel{text-decoration:line-through}"
                     f".flowchart-link.edge-thickness-thick{{stroke:{ADDED} !important}}"),
    }


MARKS = {"added": "rgba(0, 168, 126, 0.18)", "removed": "rgba(224, 86, 102, 0.18)"}
MARKED = re.compile(r":::(added|removed)|^\s*rect (added|removed)\s*$|==>", re.M)
KEY = [(r":::added", "box added", "Added"), (r":::removed", "box removed", "Removed"), (r"==>", "arrow", "Added arrow"),
       (r"(?m)^\s*rect added\s*$", "band added", "Added calls"), (r"(?m)^\s*rect removed\s*$", "band removed", "Removed calls")]
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec)/|\.(test|spec)\.[jt]sx?$|Tests?\.(java|kt)$|_test\.(go|py)$|(^|/)test_[^/]*\.py$")


def esc(text):
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(str(text or "")))


def split_where(where):
    m = re.fullmatch(r"(.+?):(\d+(?:-\d+)?)", str(where or ""))
    return (m.group(1), m.group(2)) if m else (str(where or ""), "")


def slug(name, taken):
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "area"
    sid, n = base, 2
    while sid in taken:
        sid, n = f"{base}-{n}", n + 1
    taken.add(sid)
    return sid


def ticket_key(meta):
    for text in (meta.get("title", ""), meta.get("headRefName", "")):
        m = re.search(r"\(([A-Z][A-Z0-9]{1,9}-\d+)\)", text) or re.search(r"\b([A-Z][A-Z0-9]{1,9}-\d+)\b", text)
        if m:
            return m.group(1)
    return ""


class Files:
    def __init__(self, repo, number, head, changed, paths):
        self.repo, self.number, self.head, self.changed = repo, number, head, changed
        by_name = collections.defaultdict(set)
        for p in paths:
            by_name[p.rsplit("/", 1)[-1]].add(p)
        self.labels = {}
        for group in by_name.values():
            for p in group:
                parts, k = p.split("/"), 1
                while k < len(parts) and sum(1 for q in group if q.split("/")[-k:] == parts[-k:]) > 1:
                    k += 1
                self.labels[p] = "/".join(parts[-k:])

    def link(self, where):
        path, lines = split_where(where)
        start = lines.split("-")[0]
        if path in self.changed:
            href = f"https://github.com/{self.repo}/pull/{self.number}/files#diff-{hashlib.sha256(path.encode()).hexdigest()}"
            href += f"R{start}" if start else ""
        else:
            href = f"https://github.com/{self.repo}/blob/{self.head}/{path}" + (f"#L{start}" if start else "")
        label = self.labels.get(path, path.rsplit("/", 1)[-1]) + (f":{lines}" if lines else "")
        return f'<a class="file" href="{html.escape(href)}" title="{html.escape(path)}"><code>{html.escape(label)}</code></a>'


def words(text):
    return len(str(text or "").split())


def normalize(a, changed, warnings):
    name = a.get("name")
    tests = a.setdefault("tests", {})
    tests.setdefault("files", [])
    rows = collections.OrderedDict()
    for c in a.get("changes") or []:
        path = split_where(c.get("where"))[0]
        if TEST_PATH.search(path):
            warnings.append(f"{name}: {path} is a test, so it moves from changes to tests.files")
            tests["files"].append(path)
            continue
        if path in rows:
            row = rows[path]
            row["change"] = f'{row["change"]}; {c.get("change")}'
            row["also"] = list(dict.fromkeys((row.get("also") or []) + (c.get("also") or [])))
            warnings.append(f"{name}: {path} has more than one row, so they merge into one")
        else:
            rows[path] = dict(c)
    a["changes"] = list(rows.values())
    tests["files"] = list(dict.fromkeys(split_where(w)[0] for w in tests["files"]))
    inside = [r for r in a.get("reach") or [] if split_where(r.get("where"))[0] in changed]
    for r in inside:
        warnings.append(f"{name}: {r.get('where')} is in this PR, so it isn't a caller outside it, and doesn't show")
    a["reach"] = [r for r in a.get("reach") or [] if r not in inside]


def check(data, changed):
    errors, warnings = [], []
    areas = data.get("areas") or []
    if not areas:
        errors.append("no areas")
    seen = set()
    for i, a in enumerate(areas, 1):
        name = a.get("name") or f"area {i}"
        if not a.get("name"):
            errors.append(f"area {i}: no name")
        sketch = a.get("sketch") or {}
        if sketch.get("kind") not in SKETCH_KINDS or not sketch.get("source"):
            errors.append(f"{name}: sketch needs kind (one of {sorted(SKETCH_KINDS)}) and source")
        elif not (MARKED.search(sketch["source"]) if sketch["kind"] == "mermaid" else
                  sketch["kind"] == "tree-diff" and re.search(r"(?m)^[+-]", sketch["source"])):
            warnings.append(f"{name}: the sketch marks nothing as added or removed")
        normalize(a, changed, warnings)
        for c in a["changes"]:
            if c.get("role", "behavior") not in ROLES:
                errors.append(f"{name}: {c.get('where')} has role {c.get('role')!r}, not one of {sorted(ROLES)}")
            seen.update([split_where(c.get("where"))[0]] + list(c.get("also") or []))
            if words(c.get("change")) > WORD_CAPS["change"]:
                warnings.append(f"{name}: the change at {c.get('where')} runs past {WORD_CAPS['change']} words")
        seen.update(a["tests"]["files"])
        if words(a.get("gist")) > WORD_CAPS["gist"]:
            warnings.append(f"{name}: gist runs past {WORD_CAPS['gist']} words")
        if len(a.get("questions") or []) > 4:
            warnings.append(f"{name}: more than 4 questions, so only the first 4 show")
        for q in a.get("questions") or []:
            if words(q.get("q")) > WORD_CAPS["question"]:
                warnings.append(f"{name}: a question runs past {WORD_CAPS['question']} words")
        for r in a["reach"]:
            if words(r.get("note")) > WORD_CAPS["note"]:
                warnings.append(f"{name}: a caller note runs past {WORD_CAPS['note']} words")
        for t in a["tests"].get("covered", []) + a["tests"].get("missing", []):
            if words(t) > WORD_CAPS["test"]:
                warnings.append(f"{name}: a test line runs past {WORD_CAPS['test']} words")
    for h in data.get("housekeeping") or []:
        seen.add(split_where(h.get("where"))[0])
    if words(data.get("summary")) > WORD_CAPS["summary"]:
        warnings.append(f"summary runs past {WORD_CAPS['summary']} words")
    for path in sorted(seen - changed):
        warnings.append(f"{path} is listed but isn't in files.tsv")
    missing = [p for p in sorted(changed) if p not in seen]
    for p in missing:
        warnings.append(f"{p} from files.tsv is in no area and not in housekeeping, so it shows under housekeeping")
    return errors, warnings, missing


CONTRACT_CHIP = '<span class="chip contract">Contract</span>'


def changes_contract(a):
    return any(c.get("role") == "contract" for c in a["changes"])


def diagram(kind, source):
    if kind == "mermaid":
        source = re.sub(r"(?m)^(\s*rect) (added|removed)\s*$", lambda m: f"{m.group(1)} {MARKS[m.group(2)]}", source)
        source = source.replace("\\n", "<br/>")
        return f'<pre class="diagram">{html.escape(source)}</pre>'
    cls = {"+": "add", "-": "del"} if kind == "tree-diff" else {}
    lines = "".join(f'<span class="{cls.get(l[:1], "ctx")}">{html.escape(l) or " "}</span>' for l in source.split("\n"))
    return f"<pre><code>{lines}</code></pre>"


def key_html(source):
    items = "".join(f'<span><i class="{cls}"></i>{label}</span>' for pattern, cls, label in KEY if re.search(pattern, source))
    return f'<p class="key">{items}</p>' if items else ""


def sketch_html(s):
    key = key_html(s["source"]) if s["kind"] == "mermaid" else ""
    return f'<div class="sketch">{diagram(s["kind"], s["source"])}{key}</div>'


def area_html(i, a, aid, files):
    b = a.get("behavior")
    delta = ('<p class="unchanged">Behavior doesn\'t change.</p>' if not b else
             f'<div class="delta"><div class="before"><span>Before</span><p>{esc(b.get("before"))}</p></div>'
             f'<div class="after"><span>After</span><p>{esc(b.get("after"))}</p></div></div>')
    rows = []
    for c in a["changes"]:
        role = c.get("role", "behavior")
        chip = CONTRACT_CHIP + " " if role == "contract" else ""
        tag = f' <span class="role">{role}</span>' if role in ("config", "docs") else ""
        also = c.get("also") or []
        more = (f'<details class="also"><summary>and {len(also)} more</summary>{" ".join(files.link(p) for p in also)}</details>' if also else "")
        rows.append(f'<li>{chip}{esc(c.get("change"))} {files.link(c.get("where"))}{tag}{more}</li>')
    changes_html = "<ul>" + "".join(rows) + "</ul>" if rows else "<p>Only tests change in this area.</p>"
    reach = a["reach"]
    reach_html = ("<ul>" + "".join(f"<li>{esc(r.get('note'))} {files.link(r.get('where'))}</li>" for r in reach) + "</ul>"
                  if reach else "<p>Nothing outside this PR calls the changed code.</p>")
    tests = a["tests"]
    covered, gaps = tests.get("covered") or [], tests.get("missing") or []
    tests_html = (f'<p><strong>Tested:</strong> {"; ".join(esc(t) for t in covered) if covered else "nothing in this PR"}.</p>'
                  f'<p><strong>Not tested:</strong> {"; ".join(esc(t) for t in gaps) if gaps else "no gaps found"}.</p>')
    qs = (a.get("questions") or [])[:4]
    questions = ""
    if qs:
        items = "".join("<li>" + ('<span class="chip">Ask the author</span> ' if q.get("ask_author") else "")
                        + f'{esc(q.get("q"))} {files.link(q.get("where"))}</li>' for q in qs)
        questions = f'<div class="questions"><p class="label">Worth a look</p><ul>{items}</ul></div>'
    return f"""
<section class="area" id="{aid}">
  <h2><span class="num">{i}</span>{esc(a.get('name'))}</h2>
  <p class="gist">{esc(a.get('gist'))}</p>
  {delta}
  {sketch_html(a['sketch'])}
  {questions}
  <dl class="facts">
    <dt>Changes</dt><dd>{changes_html}</dd>
    <dt>Callers outside this PR</dt><dd>{reach_html}</dd>
    <dt>Tests</dt><dd>{tests_html}</dd>
  </dl>
</section>"""


def theme_toggle(tokens):
    section = re.search(r"9\. Theme toggle.*?\*/", tokens, re.S)
    parts = re.findall(r'<script>.*?</script>|<button class="ou-theme-toggle".*?</button>', section.group(0) if section else "", re.S)
    if len(parts) != 3:
        sys.exit("tokens.css has no theme toggle in section 9: expected its two scripts and its button")
    return parts


def main(argv):
    if len(argv) < 5:
        sys.exit("usage: render.py <data.json> <gather-dir> <out.html> <design-dir>")
    data = json.load(open(argv[1]))
    gather, out, design = argv[2], argv[3], argv[4]
    meta = json.load(open(f"{gather}/meta.json"))
    changed = [l.rstrip("\n").split("\t")[3] for l in open(f"{gather}/files.tsv") if l.count("\t") == 3]

    errors, warnings, missing = check(data, set(changed))
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    repo = re.search(r"github\.com/([^/]+/[^/]+)/pull", meta["url"]).group(1)
    number, head = meta["number"], meta["headRefOid"]
    areas = data["areas"]
    housekeeping = list(data.get("housekeeping") or []) + [{"where": p, "note": ""} for p in missing]
    referenced = set(changed)
    for a in areas:
        referenced.update(split_where(x.get("where"))[0] for x in a["changes"] + a["reach"] + (a.get("questions") or []))
        referenced.update(p for c in a["changes"] for p in c.get("also") or [])
    files = Files(repo, number, head, set(changed), referenced)

    taken = set()
    ids = [slug(a["name"], taken) for a in areas]
    order = "".join(f'<li><a href="#{aid}">{esc(a["name"])}</a>{" " + CONTRACT_CHIP if changes_contract(a) else ""} <span>{esc(a.get("gist"))}</span></li>'
                    for a, aid in zip(areas, ids))
    sections = "".join(area_html(i, a, aid, files) for i, (a, aid) in enumerate(zip(areas, ids), 1))
    if housekeeping:
        rows = "".join(f'<li>{esc(h.get("note"))} {files.link(h.get("where"))}</li>' for h in housekeeping)
        one = len(housekeeping) == 1
        count = f'{len(housekeeping)} file{"" if one else "s"} with no behavior of {"its" if one else "their"} own'
        order += (f'<li class="housekeeping"><details><summary><b>Housekeeping</b><svg class="ou-icon" aria-hidden="true"><use href="#ou-chevron"/></svg>'
                  f' <span>{count}</span></summary><ul>{rows}</ul></details></li>')

    configs = {mode: mermaid_config(mode) for mode in PALETTES}
    mermaid = (f'<script type="module">{MERMAID_JS % json.dumps(configs)}</script>'
               if any(a["sketch"]["kind"] == "mermaid" for a in areas) else "")
    tokens = open(os.path.join(design, "tokens.css")).read()
    stamp, toggle, sync = theme_toggle(tokens)
    sprite = open(os.path.join(design, "icons.svg")).read()
    symbols = "".join(re.search(rf'<symbol id="ou-{name}".*?</symbol>', sprite, re.S).group(0) for name in ("external", "chevron"))
    icon = '<svg class="ou-icon" aria-hidden="true"><use href="#ou-external"/></svg>'
    key, url = ticket_key(meta), os.environ.get("TICKET_URL", "")
    ticket = f' · <a href="{html.escape(url.replace("{key}", key))}" title="{key}">Open the ticket {icon}</a>' if key and url else ""

    page = f"""<!doctype html>
<html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Lato:wght@400;700;900&display=swap" rel="stylesheet">
<title>{html.escape(repo)} #{number} walkthrough</title>
<style>{tokens}{CSS}{MARK_CSS}</style></head>
<body>
{stamp}
<svg width="0" height="0" style="position:absolute" aria-hidden="true">{symbols}</svg>
<main class="page">
  <header>
    <div class="top"><span class="repo">{html.escape(repo)} #{number}</span>
      {toggle}</div>
    <h1>{html.escape(meta["title"])}</h1>
    <p class="summary">{esc(data.get('summary'))}</p>
    <p class="meta">{esc(meta['author']['login'])} · built from <code>{head[:7]}</code> · <a href="{html.escape(meta['url'])}">Open the PR {icon}</a>{ticket}</p>
  </header>
  <section class="order"><h2>Reading order</h2><ol>{order}</ol></section>
  {sections}
</main>
{mermaid}
{sync}
</body></html>
"""
    open(out, "w").write(page)
    print(out)


CSS = r'''
.page { max-width: 880px; margin: 0 auto; padding: var(--ou-space-3) var(--ou-gutter) var(--ou-space-8); }
a { color: var(--ou-accent-pressed); text-underline-offset: 2px; transition: color var(--ou-duration-press) var(--ou-ease-standard); }
a:hover { color: var(--ou-accent-hover); }
a:active { color: var(--ou-accent-pressed); }
pre, code { background: transparent; color: inherit; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.875em; overflow-wrap: anywhere; }
a.file { text-decoration: none; }
a.file code { color: var(--ou-accent-pressed); border-bottom: 1px solid var(--ou-border); }
a.file:hover code { border-bottom-color: var(--ou-accent); }
p, li { max-width: var(--ou-measure); }
header .top { display: flex; align-items: center; justify-content: space-between; gap: var(--ou-space-2); }
header .repo { font-weight: var(--ou-weight-medium); font-size: var(--ou-size-body); color: var(--ou-text-secondary); }
h1 { font-size: var(--ou-size-h3); line-height: 1.375; margin: var(--ou-space-1) 0 var(--ou-space-2); }
h2 { font-size: var(--ou-size-h4); line-height: 1.5385; margin: 0 0 var(--ou-space-1); }
.summary { background: var(--ou-accent-wash); border-radius: var(--ou-radius-md); padding: var(--ou-space-2) var(--ou-space-3); margin: 0 0 var(--ou-space-2); max-width: none; }
.meta { font-size: var(--ou-size-body); color: var(--ou-text-secondary); margin: 0; max-width: none; }
section { border: 1px solid var(--ou-border); border-radius: var(--ou-radius-md); padding: var(--ou-space-3); margin-top: var(--ou-space-3); scroll-margin-top: var(--ou-space-2); }
.order ol { margin: 0; padding-left: var(--ou-space-3); }
.order li { margin: var(--ou-space-half) 0; }
.order li > a { font-weight: var(--ou-weight-medium); }
.order li > span, .housekeeping summary span, .gist { color: var(--ou-text-secondary); }
.num { color: var(--ou-accent-pressed); margin-right: var(--ou-space-1); }
.gist { margin: 0 0 var(--ou-space-2); }
.delta { display: grid; gap: var(--ou-space-1); margin: 0 0 var(--ou-space-2); }
.delta > div { display: grid; grid-template-columns: 72px 1fr; gap: var(--ou-space-2); padding: var(--ou-space-1) var(--ou-space-2); border-left: 3px solid var(--ou-text-hint); }
.delta > .after { border-left-color: var(--ou-accent); }
.delta span { font-weight: var(--ou-weight-medium); font-size: var(--ou-size-body); color: var(--ou-text-secondary); padding-top: 2px; }
.delta p { margin: 0; }
.unchanged { color: var(--ou-text-secondary); }
.sketch { margin: 0 0 var(--ou-space-2); border: 1px solid var(--ou-border); border-radius: var(--ou-radius-md); overflow-x: auto; background: var(--ou-surface); color: var(--ou-text); }
.sketch pre { margin: 0; padding: var(--ou-space-2) 0; font-size: var(--ou-size-body); line-height: 1.6; }
.sketch pre > code { display: inline-block; min-width: 100%; vertical-align: top; }
.sketch pre span { display: block; padding: 0 var(--ou-space-2); }
.sketch pre.diagram { padding: var(--ou-space-2); text-align: center; }
.sketch .add { background: color-mix(in srgb, var(--ou-accent) 14%, transparent); }
.sketch .del { background: color-mix(in srgb, var(--ou-error) 14%, transparent); }
.questions { margin: 0 0 var(--ou-space-2); }
.label, .facts dt { font-weight: var(--ou-weight-medium); font-size: var(--ou-size-body); margin: 0 0 var(--ou-space-half); }
.questions ul { margin: 0; padding-left: var(--ou-space-3); }
.questions li { margin: var(--ou-space-1) 0; }
.chip { display: inline-block; font-size: var(--ou-size-caption); font-weight: var(--ou-weight-medium); background: var(--ou-fill); color: var(--ou-text); border-radius: var(--ou-radius-lg); padding: 0 10px; white-space: nowrap; }
.facts { display: grid; grid-template-columns: max-content 1fr; gap: var(--ou-space-1) var(--ou-space-2); margin: 0; padding-top: var(--ou-space-2); border-top: 1px solid var(--ou-border); font-size: var(--ou-size-body); line-height: 1.6; }
.facts dt { margin: 0; color: var(--ou-text-secondary); }
.facts dd { margin: 0; min-width: 0; }
.facts ul { margin: 0; padding: 0; list-style: none; }
.facts li { margin: 0 0 var(--ou-space-half); }
.facts p { margin: 0; }
.chip.contract { background: var(--ou-warning); color: var(--ou-warning-text); }
.chip { vertical-align: 1.5px; }
.facts .chip { vertical-align: 0.5px; }
.role { font-size: var(--ou-size-caption); color: var(--ou-text-hint); }
.also { display: inline; }
.also summary { display: inline; cursor: pointer; color: var(--ou-text-hint); }
.also[open] { display: block; }
.housekeeping summary { cursor: pointer; list-style: none; }
.housekeeping summary::-webkit-details-marker { display: none; }
.housekeeping summary b { font-weight: var(--ou-weight-medium); color: var(--ou-accent-pressed); }
.housekeeping summary:hover b { color: var(--ou-accent-hover); }
.housekeeping summary .ou-icon { width: 0.75em; height: 0.75em; margin: 0 2px 0 4px; color: var(--ou-accent-pressed); vertical-align: -1px; transition: transform var(--ou-duration-press) var(--ou-ease-standard); }
.housekeeping details[open] .ou-icon { transform: rotate(90deg); }
.housekeeping ul { margin: var(--ou-space-1) 0 var(--ou-space-1) var(--ou-space-2); padding: 0; list-style: none; font-size: var(--ou-size-body); }
.housekeeping ul li { margin: var(--ou-space-half) 0; }
.key { display: flex; flex-wrap: wrap; gap: var(--ou-space-half) var(--ou-space-2); margin: 0; padding: var(--ou-space-1) var(--ou-space-2); max-width: none; border-top: 1px solid var(--ou-border); font-size: var(--ou-size-caption); color: var(--ou-text-secondary); }
.key span { display: inline-flex; align-items: center; gap: 6px; }
.key i { box-sizing: border-box; width: 18px; height: 12px; border-radius: 2px; }
.key .arrow { height: 0; border-radius: 0; }
@media (max-width: 600px) {
  section { padding: var(--ou-space-2); }
  .facts { grid-template-columns: 1fr; }
  .facts dd { margin-bottom: var(--ou-space-1); }
  .delta > div { grid-template-columns: 1fr; gap: 0; }
}
'''

MERMAID_JS = r'''
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs";
const configs = %s, root = document.documentElement, nodes = [...document.querySelectorAll("pre.diagram")];
for (const pre of nodes) pre.dataset.source = pre.textContent;
async function draw() {
  mermaid.initialize(configs[root.getAttribute("data-theme") === "dark" ? "dark" : "light"]);
  for (const pre of nodes) { pre.removeAttribute("data-processed"); pre.textContent = pre.dataset.source; }
  await mermaid.run({nodes, suppressErrors: true});
  for (const svg of document.querySelectorAll("pre.diagram svg")) svg.style.minWidth = Math.round(svg.viewBox.baseVal.width * 0.8) + "px";
}
await draw();
new MutationObserver(draw).observe(root, {attributes: true, attributeFilter: ["data-theme"]});
'''

MARK_CSS = "".join(f':root{sel}{{--mk-added:{c["added"]};--mk-removed:{c["removed"]}}}'
                   for sel, c in (("", PALETTES["light"]), ('[data-theme="dark"]', PALETTES["dark"]))) + (
    f".key .box.added{{background:var(--mk-added);border:2px solid {ADDED}}}"
    f".key .box.removed{{background:var(--mk-removed);border:2px dashed {REMOVED}}}"
    f".key .arrow{{border-top:3px solid {ADDED}}}"
    f".key .band.added{{background:{MARKS['added']}}}.key .band.removed{{background:{MARKS['removed']}}}")


if __name__ == "__main__":
    main(sys.argv)
