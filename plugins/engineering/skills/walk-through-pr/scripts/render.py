#!/usr/bin/env python3
import collections
import hashlib
import html
import json
import os
import re
import sys
import urllib.parse

ROLES = {"behavior", "contract", "config", "docs"}
SKETCH_KINDS = {"mermaid", "tree-diff"}
WORD_CAPS = {"summary": 50, "gist": 15, "change": 20, "note": 15, "test": 12}
ADDED, REMOVED = "#00a87e", "#e05666"
PALETTES = {
    "light": {"bg": "#ffffff", "text": "#121212", "line": "#505050", "node": "#f7f7f7", "border": "#8a8a8a",
              "added": "#def3ec", "removed": "#ffd7df", "changed": "#fdf2cc", "note": "#fdf2cc", "cluster": "#fafafa"},
    "dark": {"bg": "#121215", "text": "#f7f7f7", "line": "#ababab", "node": "#282a2e", "border": "#8a8a8a",
             "added": "#0e382f", "removed": "#462329", "changed": "#3f3416", "note": "#3f3416", "cluster": "#1e2024"},
}
MARKS = {"added": "rgba(0, 168, 126, 0.18)", "removed": "rgba(224, 86, 102, 0.18)", "changed": "rgba(244, 190, 25, 0.22)"}


def mermaid_config(mode):
    c = PALETTES[mode]
    shapes = "rect,.node.{0} polygon,.node.{0} circle,.node.{0} path"
    return {
        "startOnLoad": False,
        "deterministicIds": True,
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
        "themeCSS": (f".node.added {shapes.format('added')}{{fill:{c['added']} !important;stroke:{ADDED} !important;stroke-width:2px !important}}"
                     f".node.removed {shapes.format('removed')}{{fill:{c['removed']} !important;stroke:{REMOVED} !important;stroke-dasharray:5 3 !important}}"
                     f".node.changed {shapes.format('changed')}{{fill:{c['changed']} !important;stroke:{c['text']} !important;stroke-width:2px !important}}"
                     ".node.removed .nodeLabel{text-decoration:line-through}"
                     f".flowchart-link.edge-thickness-thick{{stroke:{ADDED} !important}}"
                     f'rect.rect[fill="{MARKS["added"]}"]{{stroke:{ADDED};stroke-width:2px}}'
                     f'rect.rect[fill="{MARKS["removed"]}"]{{stroke:{REMOVED};stroke-width:2px;stroke-dasharray:5 3}}'
                     f'rect.rect[fill="{MARKS["changed"]}"]{{stroke:{c["text"]};stroke-width:2px}}'),
    }


MARKED = re.compile(r":::(added|removed|changed)|^\s*rect (added|removed|changed)\s*$|==>", re.M)
KEY = [(r":::added", "box added", "Added"), (r":::removed", "box removed", "Removed"), (r":::changed", "box changed", "Changed"),
       (r"==>", "arrow", "Added arrow"), (r"(?m)^\s*rect added\s*$", "band added", "Added calls"),
       (r"(?m)^\s*rect removed\s*$", "band removed", "Removed calls"), (r"(?m)^\s*rect changed\s*$", "band changed", "Changed calls")]
HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")
DIFF_KINDS = {"+": "add", "-": "del", " ": "ctx"}
CONTEXT_STEP, SNIPPET, MAX_SOURCE = 20, 5, 1_000_000
HLJS = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__)/|\.(test|spec)\.[jt]sx?$|Tests?\.(java|kt)$|_test\.(go|py)$|(^|/)test_[^/]*\.py$")
EXTERNAL = 'target="_blank" rel="noopener"'
ICON = '<svg class="ou-icon ou-icon--sm" aria-hidden="true"><use href="#ou-external"/></svg>'


def esc(text):
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(str(text or "")))


def lang(path):
    return html.escape(path.rsplit(".", 1)[-1].lower())


def inert_json(value):
    return json.dumps(value).replace("<", "\\u003c")


def split_where(where):
    m = re.fullmatch(r"(.+?):(\d+(?:-\d+)?)", str(where or ""))
    return (m.group(1), m.group(2)) if m else (str(where or ""), "")


def span(lines):
    start, _, end = lines.partition("-")
    return int(start), int(end or start)


def short_id(*parts):
    return "t" + hashlib.sha256("|".join(parts).encode()).hexdigest()[:8]


def slug(name, taken):
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "area"
    sid, n = base, 2
    while sid in taken:
        sid, n = f"{base}-{n}", n + 1
    taken.add(sid)
    return sid


def ticket_key(meta):
    m = (re.search(r"\(([A-Z][A-Z0-9]{1,9}-\d+)\)", meta.get("title", ""))
         or re.search(r"\b([A-Z][A-Z0-9]{1,9}-\d+)\b", meta.get("headRefName", ""), re.I))
    return m.group(1).upper() if m else ""


class Files:
    def __init__(self, repo, number, base, changed, paths):
        self.repo, self.number, self.base, self.changed = repo, number, base, changed
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

    def href(self, where):
        path, lines = split_where(where)
        if path in self.changed:
            return f"https://github.com/{self.repo}/pull/{self.number}/files#diff-{hashlib.sha256(path.encode()).hexdigest()}"
        return f"https://github.com/{self.repo}/blob/{self.base}/{urllib.parse.quote(path)}" + (f"#L{span(lines)[0]}" if lines else "")

    def label(self, where):
        path, lines = split_where(where)
        return self.labels.get(path, path.rsplit("/", 1)[-1]) + (f":{lines}" if lines else "")

    def link(self, where, label=None, href=None):
        path = split_where(where)[0]
        attrs = 'class="file jump"' if href else f'class="file" {EXTERNAL}'
        return (f'<a {attrs} href="{html.escape(href or self.href(where))}" title="{html.escape(path)}">'
                f'<code>{html.escape(label or self.label(where))}</code></a>')


def words(text):
    return len(str(text or "").split())


def normalize(a, changed, warnings):
    name = a.get("name")
    tests = a.setdefault("tests", {})
    tests.setdefault("files", [])
    rows = []
    for c in a.get("changes") or []:
        path = split_where(c.get("where"))[0]
        if TEST_PATH.search(path):
            warnings.append(f"{name}: {path} is a test, so it moves from changes to tests.files")
            tests["files"].append(path)
        else:
            rows.append(c)
    a["changes"] = rows
    tests["files"] = list(dict.fromkeys(split_where(w)[0] for w in tests["files"]))
    inside = [r for r in a.get("reach") or [] if split_where(r.get("where"))[0] in changed]
    for r in inside:
        warnings.append(f"{name}: {r.get('where')} is in this PR, so it isn't a caller outside it, and doesn't show")
    a["reach"] = [r for r in a.get("reach") or [] if r not in inside]


def is_main(a):
    return bool(a.get("behavior") or a.get("sketch"))


def check_sketch(label, sketch, errors, warnings):
    if sketch is None:
        return
    if sketch.get("kind") not in SKETCH_KINDS or not sketch.get("source"):
        errors.append(f"{label}: sketch needs kind (one of {sorted(SKETCH_KINDS)}) and source")
    elif re.search(r"</?(?!br\b)[A-Za-z]", sketch["source"]):
        errors.append(f"{label}: the sketch has an HTML tag other than <br/>, so remove it, or put a space after a <")
    elif not (MARKED.search(sketch["source"]) if sketch["kind"] == "mermaid" else
              sketch["kind"] == "tree-diff" and re.search(r"(?m)^[+-]", sketch["source"])):
        warnings.append(f"{label}: the sketch marks nothing as added, removed, or changed")


def parse_diff(text, changed):
    files, path, hunk = {}, None, None
    for line in text.split("\n"):
        line = line.removesuffix("\r")
        if line.startswith("diff --git "):
            path = max((p for p in changed if line.endswith(" b/" + p)), key=len, default=line.split(" b/", 1)[-1])
            hunk = None
            files[path] = {"hunks": [], "binary": False}
        elif path is None or line.startswith("\\"):
            continue
        elif line.startswith("Binary files "):
            files[path]["binary"] = True
        elif m := HUNK.match(line):
            old, new = int(m.group(1)), int(m.group(2))
            hunk = {"old": old, "new": new, "lines": []}
            files[path]["hunks"].append(hunk)
        elif hunk is not None and line[:1] in ("+", "-", " "):
            kind = line[0]
            hunk["lines"].append({"kind": kind, "old": None if kind == "+" else old, "new": None if kind == "-" else new, "pos": new, "text": line[1:]})
            old += kind != "+"
            new += kind != "-"
        if hunk is not None:
            hunk["end_old"], hunk["end_new"] = old, new
    return files


def in_span(line, s):
    return s[0] <= (line["pos"] or line["old"]) <= s[1]


def unsafe(path):
    return path.startswith("/") or ".." in path.split("/")


def check(data, files, diff):
    errors, warnings = [], []
    changed = set(files)
    areas = data.get("areas") or []
    if not areas:
        errors.append("no areas")
    check_sketch("overview", data.get("overview"), errors, warnings)
    mains = sum(map(is_main, areas))
    if mains > 1 and not data.get("overview"):
        warnings.append(f"the PR has {mains} main areas, so it needs an overview sketch")
    elif mains <= 1 and data.get("overview"):
        warnings.append("the PR has one main area, whose sketch already shows it, so overview is null")
    last_main = max((i for i, a in enumerate(areas) if is_main(a)), default=-1)
    seen = set()
    for i, a in enumerate(areas, 1):
        name = a.get("name") or f"area {i}"
        if not a.get("name"):
            errors.append(f"area {i}: no name")
        check_sketch(name, a.get("sketch"), errors, warnings)
        if i - 1 < last_main and not is_main(a):
            warnings.append(f"{name}: has no behavior or sketch, so it's a supporting area, and it comes before a main area")
        for c in a["changes"]:
            if c.get("role", "behavior") not in ROLES:
                errors.append(f"{name}: {c.get('where')} has role {c.get('role')!r}, not one of {sorted(ROLES)}")
            path, lines = split_where(c.get("where"))
            seen.update([path] + list(c.get("also") or []))
            if words(c.get("change")) > WORD_CAPS["change"]:
                warnings.append(f"{name}: the change at {c.get('where')} runs past {WORD_CAPS['change']} words")
            if ";" in re.sub(r"`[^`]*`", "", str(c.get("change") or "")):
                warnings.append(f"{name}: the change at {c.get('where')} joins clauses with a semicolon, so split it into rows")
            hunks = diff.get(path, {}).get("hunks")
            if hunks and not lines:
                warnings.append(f"{name}: the change at {path} names no lines, so the code pane can't mark it")
            elif hunks and not any(in_span(l, span(lines)) for h in hunks for l in h["lines"]):
                warnings.append(f"{name}: the change at {c.get('where')} points at lines outside the diff, so the code pane marks nothing")
        seen.update(a["tests"]["files"])
        if words(a.get("gist")) > WORD_CAPS["gist"]:
            warnings.append(f"{name}: gist runs past {WORD_CAPS['gist']} words")
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
    reach = {split_where(r.get("where"))[0] for a in areas for r in a["reach"]}
    for path in sorted(p for p in seen | reach if unsafe(p)):
        errors.append(f"{path} isn't a path inside the repo")
    for path in sorted(seen - changed):
        warnings.append(f"{path} is listed but isn't in files.tsv")
    for path, (_, added, removed) in files.items():
        if (added, removed) != ("0", "0") and not diff.get(path, {}).get("hunks") and not diff.get(path, {}).get("binary"):
            warnings.append(f"{path} has line changes in files.tsv but none in pr.diff, so the code pane can't show them")
    missing = [p for p in sorted(changed) if p not in seen]
    for p in missing:
        warnings.append(f"{p} from files.tsv is in no area and not in housekeeping, so it shows under housekeeping")
    return errors, warnings, missing


CHIPS = {"contract": "Contract", "config": "Config", "docs": "Docs"}


def chip(role):
    return f'<span class="chip {role}">{CHIPS[role]}</span>' if role in CHIPS else ""


def changes_contract(a):
    return any(c.get("role") == "contract" for c in a["changes"])


def diagram(kind, source):
    if kind == "mermaid":
        source = re.sub(r"(?m)^(\s*rect) (added|removed|changed)\s*$", lambda m: f"{m.group(1)} {MARKS[m.group(2)]}", source)
        source = source.replace("\\n", "<br/>")
        return f'<pre class="diagram">{html.escape(source)}</pre>'
    cls = {"+": "add", "-": "del"}
    lines = "".join(f'<span class="{cls.get(l[:1], "ctx")}">{html.escape(l) or " "}</span>' for l in source.split("\n"))
    return f"<pre><code>{lines}</code></pre>"


def key_html(source):
    items = "".join(f'<span><i class="{cls}"></i>{label}</span>' for pattern, cls, label in KEY if re.search(pattern, source))
    return f'<p class="key">{items}</p>' if items else ""


def sketch_html(s):
    key = key_html(s["source"]) if s["kind"] == "mermaid" else ""
    return (f'<div class="sketch" tabindex="0" role="button" aria-label="Zoom the sketch">'
            f'{diagram(s["kind"], s["source"])}{key}</div>')


class Code:
    def __init__(self, gather, diff, files):
        self.gather, self.diff, self.files = gather, diff, files
        self.heads, self.sources, self.ids = {}, {}, {}

    def read(self, into, path):
        try:
            text = open(os.path.join(self.gather, into, path), errors="replace", newline="").read()
        except OSError:
            return None
        return [l.removesuffix("\r") for l in text.removesuffix("\n").split("\n")] if text else []

    def head(self, path):
        if path not in self.heads:
            lines = self.read("head", path)
            self.heads[path] = lines if lines is not None and sum(map(len, lines)) <= MAX_SOURCE else None
        return self.heads[path]

    def gap(self, path, a, b, delta, up):
        if b < a or not self.head(path):
            return ""
        if path not in self.ids:
            self.ids[path] = f"src{len(self.ids)}"
            self.sources[self.ids[path]] = self.head(path)
        return (f'<tr class="gap" data-src="{self.ids[path]}" data-a="{a}" data-b="{b}" data-d="{delta}" data-up="{int(up)}">'
                f'<td colspan="3"><button type="button"></button></td></tr>')

    def row(self, l, tid, cls="", first=False):
        o, n = l["old"] or "", l["new"] or ""
        rid = f"{tid}n{n}" if n else f"{tid}o{o}"
        return (f'<tr class="l {DIFF_KINDS[l["kind"]]}{cls}" id="{rid}" data-o="{o}" data-n="{n}"><td class="o">{o}</td>'
                f'<td class="n"{" tabindex=0" if first else ""}>{n}</td><td class="c">{html.escape(l["text"])}</td></tr>')

    def table(self, path, marks, expand, tid):
        fd = self.diff.get(path)
        head = (f'<div class="fh"><a href="{html.escape(self.files.href(path))}" title="{html.escape(path)}" {EXTERNAL}>'
                f'<code>{html.escape(self.files.label(path))}</code>{ICON}</a>')
        if not fd or fd["binary"] or not fd["hunks"]:
            note = "Binary file" if fd and fd["binary"] else "No line changes"
            return set(), f'{head}</div><p class="nodiff">{note}. Open it on GitHub to see it.</p>'
        lines = [l for h in fd["hunks"] for l in h["lines"]]
        head += f' <span class="stat">+{sum(l["kind"] == "+" for l in lines)} −{sum(l["kind"] == "-" for l in lines)}</span></div>'
        gap = self.gap if expand else lambda *_: ""
        placed, body, prev = set(), [], (1, 1)
        for h in fd["hunks"]:
            body.append(gap(path, prev[1], h["new"] - 1, h["old"] - h["new"], True))
            for l in h["lines"]:
                hits = [m for m in marks if in_span(l, m[1])]
                for k, _, label in hits:
                    if k not in placed:
                        placed.add(k)
                        body.append(f'<tr class="lbl" id="{k}"><td colspan="3">{label}</td></tr>')
                body.append(self.row(l, tid, " focus" if hits else " dim" if marks else "", l is lines[0]))
            prev = (h["end_old"], h["end_new"])
        body.append(gap(path, prev[1], len(self.head(path) or []), prev[0] - prev[1], False))
        gh = html.escape(self.files.href(path))
        return placed, f'{head}<div class="fwrap"><table class="diff" id="{tid}" data-pr="{gh}" data-lang="{lang(path)}">{"".join(body)}</table></div>'

    def snippet(self, where, tid):
        path, lines = split_where(where)
        src = self.read("base", path)
        if not src or not lines:
            return ""
        at = span(lines)[0]
        first = max(1, at - SNIPPET)
        rows = "".join(self.row({"kind": " ", "old": None, "new": n, "text": src[n - 1]}, tid, " focus" if n == at else "", n == first)
                       for n in range(first, min(len(src), at + SNIPPET) + 1))
        return (f'<div class="fwrap"><table class="diff" id="{tid}" data-blob="{html.escape(self.files.href(path))}" '
                f'data-lang="{lang(path)}">{rows}</table></div>')


def change_html(c, target, targets, files):
    lines = split_where(c.get("where"))[1]
    also = c.get("also") or []
    more = (f'<details class="also"><summary>and {len(also)} more</summary>'
            f'{" ".join(files.link(p, href="#" + targets[p]) for p in also)}</details>' if also else "")
    return (f'<li>{chip(c.get("role"))} {esc(c.get("change"))}'
            f'{" " + files.link(c.get("where"), "L" + lines, "#" + target) if lines else ""}{more}</li>')


def area_html(i, a, aid, code):
    files = code.files
    b, s, main = a.get("behavior"), a.get("sketch"), is_main(a)
    delta = ("" if not main else '<p class="unchanged">Behavior doesn\'t change.</p>' if not b else
             f'<div class="delta"><div class="before"><span>Before</span><p>{esc(b.get("before"))}</p></div>'
             f'<div class="after"><span>After</span><p>{esc(b.get("after"))}</p></div></div>')
    by_file = collections.OrderedDict()
    for j, c in enumerate(a["changes"]):
        by_file.setdefault(split_where(c.get("where"))[0], []).append((j, c))
    also = [p for c in a["changes"] for p in c.get("also") or [] if p not in by_file]
    blocks, targets, placed = [], {}, set()
    for k, path in enumerate(list(by_file) + list(dict.fromkeys(also))):
        fid = targets[path] = f"{aid}-f{k}"
        marks = [(f"{aid}-c{j}", span(split_where(c["where"])[1]), f'{chip(c.get("role"))} {esc(c.get("change"))}')
                 for j, c in by_file.get(path, []) if split_where(c["where"])[1]]
        got, table = code.table(path, marks, True, short_id(aid, path))
        placed.update(got)
        blocks.append(f'<div class="fblock" id="{fid}">{table}</div>')
    tests = a["tests"]
    if tests["files"]:
        blocks.append('<p class="label">Tests</p>' + "".join(
            f'<div class="fblock">{code.table(p, [], True, short_id(aid, p))[1]}</div>' for p in tests["files"]))
    reach = a["reach"]
    if reach:
        blocks.append('<p class="label">Callers outside this PR</p>' + "".join(
            f'<div class="fblock" id="{aid}-x{j}"><div class="fh">{esc(r.get("note"))} {files.link(r.get("where"))}</div>'
            f'{code.snippet(r.get("where"), short_id(aid, "caller", str(r.get("where"))))}</div>'
            for j, r in enumerate(reach)))
    rows = "".join(f'<li>{files.link(path, href="#" + targets[path])}<ul>'
                   f'{"".join(change_html(c, f"{aid}-c{j}" if f"{aid}-c{j}" in placed else targets[path], targets, files) for j, c in cs)}</ul></li>'
                   for path, cs in by_file.items())
    facts = [("Changes", f'<ul class="changes">{rows}</ul>' if rows else "<p>Only tests change in this area.</p>")]
    if main or reach:
        facts.append(("Callers outside this PR", "<ul>" + "".join(f'<li>{esc(r.get("note"))} {files.link(r.get("where"), href=f"#{aid}-x{j}")}</li>'
                                                                  for j, r in enumerate(reach)) + "</ul>"
                      if reach else "<p>Nothing outside this PR calls the changed code.</p>"))
    covered, gaps = tests.get("covered") or [], tests.get("missing") or []
    if main or covered or gaps:
        facts.append(("Tests", f'<p><strong>Tested:</strong> {"; ".join(esc(t) for t in covered) if covered else "nothing in this PR"}.</p>'
                               f'<p><strong>Not tested:</strong> {"; ".join(esc(t) for t in gaps) if gaps else "no gaps found"}.</p>'))
    facts_html = "".join(f"<dt>{dt}</dt><dd>{dd}</dd>" for dt, dd in facts)
    return f"""
<section class="area" id="{aid}">
  <div class="prose">
    <h2><span class="num">{i}</span> {esc(a.get('name'))}</h2>
    <p class="gist">{esc(a.get('gist'))}</p>
    {delta}
    {sketch_html(s) if s else ""}
    <dl class="facts">{facts_html}</dl>
  </div>
  <div class="code">{"".join(blocks)}</div>
</section>"""


def housekeeping_html(housekeeping, code):
    files = code.files
    items, blocks = [], []
    for k, h in enumerate(housekeeping):
        path = split_where(h.get("where"))[0]
        items.append(f'<li>{esc(h.get("note"))} {files.link(path, href=f"#hk-{k}")}</li>')
        blocks.append(f'<details class="fblock" id="hk-{k}"><summary>{html.escape(files.label(path))}</summary>'
                      f'{code.table(path, [], False, short_id("housekeeping", path))[1]}</details>')
    return f"""
<section class="area" id="housekeeping">
  <div class="prose"><h2>Housekeeping</h2><p class="gist">Files with no behavior of their own.</p><ul class="hk">{"".join(items)}</ul></div>
  <div class="code">{"".join(blocks)}</div>
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
    files_tsv = {r[3]: r[:3] for r in (l.rstrip("\n").split("\t") for l in open(f"{gather}/files.tsv")) if len(r) == 4}
    changed = list(files_tsv)
    diff = parse_diff(open(f"{gather}/pr.diff", errors="replace", newline="").read(), changed)

    warnings = []
    for a in data.get("areas") or []:
        normalize(a, set(changed), warnings)
    errors, more, missing = check(data, files_tsv, diff)
    for w in warnings + more:
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
        referenced.update(split_where(x.get("where"))[0] for x in a["changes"] + a["reach"])
        referenced.update(p for c in a["changes"] for p in c.get("also") or [])
    files = Files(repo, number, meta.get("baseOid") or meta["baseRefName"], set(changed), referenced)
    code = Code(gather, diff, files)

    taken = set()
    ids = [slug("a " + a["name"], taken) for a in areas]
    order = "".join(f'<li><a href="#{aid}">{esc(a["name"])}</a>{" " + chip("contract") if changes_contract(a) else ""} <span>{esc(a.get("gist"))}</span></li>'
                    for a, aid in zip(areas, ids))
    sections = "".join(area_html(i, a, aid, code) for i, (a, aid) in enumerate(zip(areas, ids), 1))
    if housekeeping:
        one = len(housekeeping) == 1
        count = f'{len(housekeeping)} file{"" if one else "s"} with no behavior of {"its" if one else "their"} own'
        order += f'<li class="housekeeping"><a href="#housekeeping">Housekeeping</a> <span>{count}</span></li>'
        sections += housekeeping_html(housekeeping, code)
    sources = "".join(f'<script type="application/json" id="{sid}">{inert_json(lines)}</script>' for sid, lines in code.sources.items())

    overview = data.get("overview")
    overview_html = f'<section class="overview"><h2>Where the changes land</h2>{sketch_html(overview)}</section>' if overview else ""
    configs = {mode: mermaid_config(mode) for mode in PALETTES}
    sketches = [overview] + [a.get("sketch") for a in areas]
    mermaid = (f'<script type="module">{MERMAID_JS % json.dumps(configs)}</script>'
               if any(s and s["kind"] == "mermaid" for s in sketches) else "")
    tokens = open(os.path.join(design, "tokens.css")).read()
    stamp, toggle, sync = theme_toggle(tokens)
    sprite = open(os.path.join(design, "icons.svg")).read()
    symbol = re.search(r'<symbol id="ou-external".*?</symbol>', sprite, re.S).group(0)
    key, url = ticket_key(meta), os.environ.get("TICKET_URL", "")
    ticket = f' · <a href="{html.escape(url.replace("{key}", key))}" title="{key}" {EXTERNAL}>Open the ticket {ICON}</a>' if key and url else ""

    page = f"""<!doctype html>
<html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Lato:wght@400;700;900&display=swap" rel="stylesheet">
<title>{html.escape(repo)} #{number} walkthrough</title>
<style>{tokens}{CSS}{MARK_CSS}</style></head>
<body>
{stamp}
<svg width="0" height="0" style="position:absolute" aria-hidden="true">{symbol}</svg>
<main class="page">
  <header>
    <div class="top"><h1>{html.escape(meta["title"])}</h1>{toggle}</div>
    <p class="summary">{esc(data.get('summary'))}</p>
    <p class="meta">{html.escape(repo)} #{number} · {esc(meta['author']['login'])} · built from <code>{head[:7]}</code> · <a href="{html.escape(meta['url'])}" {EXTERNAL}>Open the PR {ICON}</a>{ticket}</p>
  </header>
  {overview_html}
  <section class="order"><h2>Reading order</h2><ol>{order}</ol>
    <p class="hint">The code for each area sits beside it. Click a line number to comment on that line.</p></section>
  {sections}
</main>
<div id="line-actions" class="actions" hidden><button type="button" data-act="here">Comment here</button><a data-act="gh" {EXTERNAL}>Comment on GitHub {ICON}</a></div>
{sources}
<script src="{HLJS}"></script>
<script type="module">{PAGE_JS}</script>
{mermaid}
{sync}
</body></html>
"""
    open(out, "w").write(page)
    print(out)


CSS = r'''
:root { color-scheme: light; }
:root[data-theme="dark"] { color-scheme: dark; }
body { overflow-wrap: anywhere; }
.page { max-width: 1600px; margin: 0 auto; padding: var(--ou-space-3) var(--ou-gutter) var(--ou-space-8); }
a { color: var(--ou-accent-pressed); text-underline-offset: 2px; transition: color var(--ou-duration-press) var(--ou-ease-standard); }
a:hover { color: var(--ou-accent-hover); }
a .ou-icon { margin-left: 4px; vertical-align: -1px; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.875em; }
a.file { text-decoration: none; }
a.file code { color: var(--ou-accent-pressed); border-bottom: 1px solid var(--ou-border); }
a.file:hover code { border-bottom-color: var(--ou-accent); }
p, li { max-width: var(--ou-measure); }
header .top { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--ou-space-2); }
h1 { font-size: var(--ou-size-h3); line-height: 1.375; margin: var(--ou-space-1) 0 var(--ou-space-2); min-width: 0; }
h2 { font-size: var(--ou-size-h4); line-height: 1.5385; margin: 0 0 var(--ou-space-1); }
.summary { background: var(--ou-accent-wash); border-radius: var(--ou-radius-md); padding: var(--ou-space-2) var(--ou-space-3); margin: 0 0 var(--ou-space-2); max-width: none; }
.meta { font-size: var(--ou-size-body); color: var(--ou-text-secondary); margin: 0; max-width: none; }
section { border: 1px solid var(--ou-border); border-radius: var(--ou-radius-md); padding: var(--ou-space-3); margin-top: var(--ou-space-3); scroll-margin-top: var(--ou-space-2); }
.order ol { margin: 0; padding-left: var(--ou-space-3); }
.order li { margin: var(--ou-space-half) 0; }
.order li > a { font-weight: var(--ou-weight-medium); }
.order li > span, .gist, .hint { color: var(--ou-text-secondary); }
.num { color: var(--ou-accent-pressed); margin-right: var(--ou-space-half); }
.gist { margin: 0 0 var(--ou-space-2); }
.delta { display: grid; gap: var(--ou-space-1); margin: 0 0 var(--ou-space-2); }
.delta > div { display: grid; grid-template-columns: 72px 1fr; gap: var(--ou-space-2); padding: var(--ou-space-1) var(--ou-space-2); border-left: 3px solid var(--ou-text-hint); }
.delta > .after { border-left-color: var(--ou-accent); }
.delta span { font-weight: var(--ou-weight-medium); font-size: var(--ou-size-body); color: var(--ou-text-secondary); padding-top: 2px; }
.delta p { margin: 0; }
.unchanged { color: var(--ou-text-secondary); }
.sketch { margin: 0 0 var(--ou-space-2); border: 1px solid var(--ou-border); border-radius: var(--ou-radius-md); overflow-x: auto; background: var(--ou-surface); color: var(--ou-text); cursor: zoom-in; }
.sketch pre { margin: 0; padding: var(--ou-space-2) 0; font-size: var(--ou-size-body); line-height: 1.6; }
.sketch pre > code { display: inline-block; min-width: 100%; vertical-align: top; }
.sketch pre span { display: block; padding: 0 var(--ou-space-2); }
.sketch pre.diagram { padding: var(--ou-space-2); text-align: center; }
.sketch .add { background: color-mix(in srgb, var(--ou-accent) 14%, transparent); }
.sketch .del { background: color-mix(in srgb, var(--ou-error) 14%, transparent); }
.overview .sketch { margin: 0; }
.chip { display: inline-block; font-size: var(--ou-size-caption); font-weight: var(--ou-weight-medium); background: var(--ou-fill); color: var(--ou-text); border-radius: var(--ou-radius-lg); padding: 0 10px; white-space: nowrap; vertical-align: 1.5px; }
.chip.contract { background: var(--ou-warning); color: var(--ou-warning-text); }
.facts { display: grid; grid-template-columns: max-content 1fr; gap: var(--ou-space-1) var(--ou-space-2); margin: 0; padding-top: var(--ou-space-2); border-top: 1px solid var(--ou-border); font-size: var(--ou-size-body); line-height: 1.6; }
.facts dt { font-weight: var(--ou-weight-medium); margin: 0; color: var(--ou-text-secondary); }
.facts dd { margin: 0; min-width: 0; }
.facts ul { margin: 0; padding: 0; list-style: none; }
.facts li { margin: 0 0 var(--ou-space-half); }
.facts p { margin: 0; }
.facts .chip { vertical-align: 0.5px; }
.changes > li { margin: 0 0 var(--ou-space-1); }
.changes ul { margin: var(--ou-space-half) 0 0; padding-left: var(--ou-space-3); list-style: disc; }
.also { display: inline; }
.also summary { display: inline; cursor: pointer; color: var(--ou-text-secondary); }
.also[open] { display: block; }
.hint { font-size: var(--ou-size-body); margin: var(--ou-space-2) 0 0; }
.hk { margin: 0; padding: 0; list-style: none; font-size: var(--ou-size-body); }
.hk li { margin: 0 0 var(--ou-space-half); }
.area { display: grid; grid-template-columns: minmax(0, 5fr) minmax(0, 7fr); gap: var(--ou-space-3); align-items: start; }
.area > .code { position: sticky; top: var(--ou-space-2); max-height: calc(100vh - 2 * var(--ou-space-2)); overflow: auto; min-width: 0; }
.fblock { border: 1px solid var(--ou-border); border-radius: var(--ou-radius-md); margin: 0 0 var(--ou-space-2); overflow: hidden; background: var(--ou-surface); }
.fh, details.fblock > summary { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px var(--ou-space-1); padding: 6px 12px; background: var(--ou-surface-sunken); border-bottom: 1px solid var(--ou-border); font-size: var(--ou-size-body); }
details.fblock > summary { cursor: pointer; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
details.fblock > summary:focus-visible { outline-offset: -2px; }
details.fblock:not([open]) > summary { border-bottom: 0; }
.fh > a { text-decoration: none; font-weight: var(--ou-weight-medium); }
.stat { color: var(--ou-text-secondary); font-size: var(--ou-size-caption); }
.nodiff { margin: 0; padding: var(--ou-space-1) 12px; color: var(--ou-text-secondary); font-size: var(--ou-size-body); max-width: none; }
.label { font-weight: var(--ou-weight-medium); font-size: var(--ou-size-body); color: var(--ou-text-secondary); margin: var(--ou-space-3) 0 var(--ou-space-1); }
.fwrap { overflow-x: auto; }
table.diff { border-collapse: collapse; width: 100%; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: var(--ou-size-caption); line-height: 1.6; }
.diff td { padding: 0; vertical-align: top; transition: background-color var(--ou-duration-press) var(--ou-ease-standard); }
td.o, td.n { width: 1%; padding: 0 8px; text-align: right; white-space: nowrap; color: var(--ou-text-secondary); cursor: pointer; user-select: none; }
td.o:hover, td.n:hover { color: var(--ou-accent-pressed); }
td.c { position: relative; white-space: pre-wrap; padding: 0 16px 0 20px; tab-size: 4; }
tr.add td { background: color-mix(in srgb, var(--ou-accent) 12%, transparent); }
tr.del td { background: color-mix(in srgb, var(--ou-error) 12%, transparent); }
tr.add td.c::before, tr.del td.c::before { position: absolute; left: 6px; }
tr.add td.c::before { content: "+"; color: var(--ou-accent-pressed); }
tr.del td.c::before { content: "-"; color: var(--ou-error); }
tr.dim td { opacity: 0.45; }
tr.focus td.o { box-shadow: inset 3px 0 0 var(--ou-accent); }
tr.lbl td { padding: 6px 12px; white-space: normal; font-family: var(--ou-font-body); font-size: var(--ou-size-body); background: var(--ou-accent-wash); border-top: 1px solid var(--ou-border); }
tr.gap td { padding: 2px 12px; background: var(--ou-surface-sunken); }
tr.gap button, .actions button, .actions a { font: inherit; font-family: var(--ou-font-body); font-size: var(--ou-size-caption); color: var(--ou-accent-pressed); background: none; border: 0; cursor: pointer; text-decoration: none; }
tr.gap button:hover, .actions button:hover, .actions a:hover { color: var(--ou-accent-hover); }
tr.picked td { background-color: var(--ou-accent-wash); }
tr.flash td, .fblock.flash { background-color: color-mix(in srgb, var(--ou-warning) 24%, transparent); }
.actions { position: fixed; z-index: 30; display: flex; gap: var(--ou-space-1); padding: 4px 8px; background: var(--ou-surface); border: 1px solid var(--ou-border); box-shadow: var(--ou-shadow-2); }
.actions[hidden] { display: none; }
.actions [data-act=here] { display: none; }
.can-comment .actions [data-act=here] { display: inline; }
.sketch.zoom { position: fixed; inset: var(--ou-space-3); z-index: 40; margin: 0; overflow: auto; cursor: zoom-out; box-shadow: 0 0 0 100vmax var(--ou-overlay-strong); }
.sketch.zoom pre.diagram svg { max-width: none !important; min-width: 0 !important; width: 100%; height: auto; }
.hljs-keyword, .hljs-selector-tag, .hljs-doctag { color: var(--sx-keyword); }
.hljs-string, .hljs-regexp, .hljs-template-string { color: var(--sx-string); }
.hljs-comment, .hljs-quote, .hljs-meta { color: var(--sx-comment); }
.hljs-number, .hljs-literal, .hljs-attr, .hljs-attribute, .hljs-variable, .hljs-template-variable, .hljs-symbol, .hljs-selector-class, .hljs-selector-id { color: var(--sx-number); }
.hljs-title, .hljs-type, .hljs-built_in, .hljs-section, .hljs-name, .hljs-tag { color: var(--sx-title); }
:root { --sx-keyword: #cf222e; --sx-string: #0a3069; --sx-comment: #6e7781; --sx-number: #0550ae; --sx-title: #953800; }
:root[data-theme="dark"] { --sx-keyword: #ff7b72; --sx-string: #a5d6ff; --sx-comment: #8b949e; --sx-number: #79c0ff; --sx-title: #ffa657; }
@media (max-width: 1100px) {
  .area { display: block; }
  .area > .code { position: static; max-height: none; overflow: visible; margin-top: var(--ou-space-3); }
}
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
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { transition: none !important; }
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
let queue = document.fonts.ready.then(draw);
new MutationObserver(() => queue = queue.then(draw, draw)).observe(root, {attributes: true, attributeFilter: ["data-theme"]});
'''

PAGE_JS = r'''
const root = document.documentElement, STEP = %d;
const smooth = matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
const bar = document.getElementById("line-actions"), github = bar.querySelector("[data-act=gh]"), here = bar.querySelector("[data-act=here]");
const sources = {};
let picked = null, comments = null, misses = 0;

function language(table) {
  const lang = table.dataset.lang;
  return window.hljs && hljs.getLanguage(lang) ? lang : null;
}

function split(html) {
  const lines = [""], open = [];
  for (const part of html.split(/(<span[^>]*>|<\/span>|\n)/)) {
    if (part === "\n") {
      lines[lines.length - 1] += "</span>".repeat(open.length);
      lines.push(open.join(""));
      continue;
    }
    if (part.startsWith("<span")) open.push(part);
    else if (part === "</span>") open.pop();
    lines[lines.length - 1] += part;
  }
  return lines;
}

function paint(table) {
  const lang = language(table);
  if (!lang) return;
  table.dataset.hl = "1";
  const rows = [...table.querySelectorAll("tr.l")];
  for (const [side, keep] of [[r => r.dataset.n, () => true], [r => r.dataset.o, r => !r.dataset.n]]) {
    const run = rows.filter(side);
    const html = split(hljs.highlight(run.map(r => r.cells[2].textContent).join("\n"), {language: lang, ignoreIllegals: true}).value);
    run.forEach((r, i) => { if (keep(r)) r.cells[2].innerHTML = html[i]; });
  }
}

const painter = new IntersectionObserver(entries => {
  for (const entry of entries) {
    if (!entry.isIntersecting) continue;
    painter.unobserve(entry.target);
    paint(entry.target);
  }
}, {rootMargin: "600px"});
document.querySelectorAll("table.diff").forEach(t => painter.observe(t));

function label(gap) {
  const left = gap.dataset.b - gap.dataset.a + 1;
  gap.querySelector("button").textContent = left <= STEP ? `Show ${left} hidden line${left === 1 ? "" : "s"}` : `Show ${STEP} of ${left} hidden lines`;
}
document.querySelectorAll("tr.gap").forEach(label);

function expand(gap) {
  const table = gap.closest("table"), lines = sources[gap.dataset.src] ??= JSON.parse(document.getElementById(gap.dataset.src).textContent);
  const delta = +gap.dataset.d, up = gap.dataset.up === "1", dim = table.querySelector("tr.dim") ? " dim" : "";
  let a = +gap.dataset.a, b = +gap.dataset.b;
  const count = Math.min(STEP, b - a + 1), from = up ? b - count + 1 : a, rows = [];
  for (let n = from; n < from + count; n++) {
    const tr = document.createElement("tr");
    tr.className = "l ctx" + dim;
    tr.id = `${table.id}n${n}`;
    tr.dataset.o = n + delta;
    tr.dataset.n = n;
    tr.innerHTML = `<td class="o">${n + delta}</td><td class="n">${n}</td><td class="c"></td>`;
    tr.cells[2].textContent = lines[n - 1] ?? "";
    rows.push(tr);
  }
  if (up) { gap.after(...rows); b = from - 1; } else { gap.before(...rows); a = from + count; }
  if (a > b) gap.remove();
  else { gap.dataset.a = a; gap.dataset.b = b; label(gap); }
  if (table.dataset.hl) paint(table);
}

function closeBar(refocus) {
  if (bar.hidden) return;
  const cell = picked?.cells[1];
  bar.hidden = true;
  picked?.classList.remove("picked");
  picked = null;
  if (refocus) cell?.focus();
}

function openBar(cell, keyboard) {
  const tr = cell.parentElement, table = tr.closest("table"), {n, o} = tr.dataset;
  closeBar();
  picked = tr;
  tr.classList.add("picked");
  github.href = table.dataset.pr ? table.dataset.pr + (n ? "R" + n : "L" + o) : table.dataset.blob + "#L" + n;
  bar.hidden = false;
  const r = cell.getBoundingClientRect(), fits = r.bottom + 4 + bar.offsetHeight <= innerHeight;
  bar.style.left = r.left + "px";
  bar.style.top = (fits ? r.bottom + 4 : r.top - 4 - bar.offsetHeight) + "px";
  if (keyboard) (root.classList.contains("can-comment") ? here : github).focus();
}

function zoom(sketch) {
  const on = !sketch.classList.contains("zoom");
  document.querySelector(".sketch.zoom")?.classList.remove("zoom");
  sketch.classList.toggle("zoom", on);
}

function jump(link) {
  const target = document.getElementById(decodeURIComponent(link.hash.slice(1)));
  if (!target) return false;
  target.closest("details")?.setAttribute("open", "");
  const box = target.closest(".code");
  if (box && getComputedStyle(box).position === "sticky" && box.scrollHeight > box.clientHeight) {
    box.scrollTo({top: box.scrollTop + target.getBoundingClientRect().top - box.getBoundingClientRect().top - 12, behavior: smooth});
  } else {
    target.scrollIntoView({block: "center", behavior: smooth});
  }
  if (!target.hasAttribute("tabindex")) target.tabIndex = -1;
  target.focus({preventScroll: true});
  target.classList.add("flash");
  setTimeout(() => target.classList.remove("flash"), 1200);
  return true;
}

document.addEventListener("click", async event => {
  const t = event.target, zoomed = document.querySelector(".sketch.zoom");
  if (zoomed && !zoomed.contains(t)) {
    zoomed.classList.remove("zoom");
    return event.preventDefault();
  }
  if (t.closest("[data-act=here]")) {
    const tr = picked;
    closeBar();
    if (comments && tr) await comments.openComposer({element: tr}).catch(e => {
      if (e?.code === "unavailable" && ++misses > 1) root.classList.remove("can-comment");
    });
    return;
  }
  if (bar.contains(t)) return closeBar();
  const cell = t.closest("tr.l td.o, tr.l td.n");
  if (cell) return cell.parentElement === picked ? closeBar() : openBar(cell, false);
  closeBar();
  const gap = t.closest("tr.gap button");
  if (gap) return expand(gap.closest("tr.gap"));
  const link = t.closest("a.jump");
  if (link && jump(link)) return event.preventDefault();
  const sketch = t.closest(".sketch");
  if (sketch && !t.closest("a")) zoom(sketch);
});

document.addEventListener("keydown", event => {
  const t = event.target, cell = t.closest?.("tr.l td.n"), sketch = t.closest?.(".sketch");
  const press = event.key === "Enter" || event.key === " ";
  if (cell && (event.key === "ArrowDown" || event.key === "ArrowUp")) {
    let tr = cell.parentElement;
    do tr = event.key === "ArrowDown" ? tr.nextElementSibling : tr.previousElementSibling; while (tr && !tr.matches("tr.l"));
    if (!tr) return;
    event.preventDefault();
    cell.tabIndex = -1;
    tr.cells[1].tabIndex = 0;
    tr.cells[1].focus();
  } else if (cell && press) {
    event.preventDefault();
    openBar(cell, true);
  } else if (sketch && press) {
    event.preventDefault();
    zoom(sketch);
  } else if (event.key === "Escape") {
    closeBar(bar.contains(document.activeElement));
    document.querySelector(".sketch.zoom")?.classList.remove("zoom");
  }
});
document.addEventListener("scroll", () => closeBar(), true);
window.claude?.use?.("comments").then(c => {
  comments = c;
  if (c) root.classList.add("can-comment");
}).catch(() => {});
''' % CONTEXT_STEP

MARK_CSS = "".join(f':root{sel}{{--mk-added:{c["added"]};--mk-removed:{c["removed"]};--mk-changed:{c["changed"]}}}'
                   for sel, c in (("", PALETTES["light"]), ('[data-theme="dark"]', PALETTES["dark"]))) + (
    f".key .box.added{{background:var(--mk-added);border:2px solid {ADDED}}}"
    f".key .box.removed{{background:var(--mk-removed);border:2px dashed {REMOVED}}}"
    ".key .box.changed{background:var(--mk-changed);border:2px solid var(--ou-text)}"
    f".key .arrow{{border-top:3px solid {ADDED}}}"
    f".key .band.added{{background:{MARKS['added']};border:2px solid {ADDED}}}"
    f".key .band.removed{{background:{MARKS['removed']};border:2px dashed {REMOVED}}}"
    f".key .band.changed{{background:{MARKS['changed']};border:2px solid var(--ou-text)}}")


if __name__ == "__main__":
    main(sys.argv)
