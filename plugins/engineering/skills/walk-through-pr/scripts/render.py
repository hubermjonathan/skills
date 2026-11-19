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
WORD_CAPS = {"summary": 50, "gist": 15, "change": 20, "note": 15, "test": 12, "why": 20, "what_changes": 45}
ADDED, REMOVED = "#00a87e", "#e05666"
PALETTES = {
    "light": {"bg": "#ffffff", "text": "#121212", "line": "#505050", "node": "#f7f7f7", "border": "#8a8a8a",
              "added": "#def3ec", "removed": "#ffd7df", "changed": "#fdf2cc", "cluster": "#fafafa"},
    "dark": {"bg": "#121215", "text": "#f7f7f7", "line": "#ababab", "node": "#282a2e", "border": "#8a8a8a",
             "added": "#0e382f", "removed": "#462329", "changed": "#3f3416", "cluster": "#1e2024"},
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
            "noteBkgColor": c["bg"], "noteBorderColor": c["border"], "noteTextColor": c["text"],
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
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|__fixtures__)/|\.(test|spec)\.[jt]sx?$|Tests?\.(java|kt)$|_test\.(go|py)$|(^|/)test_[^/]*\.py$")
EXTERNAL = 'target="_blank" rel="noopener"'
ICON = '<svg class="ou-icon ou-icon--sm" aria-hidden="true"><use href="#ou-external"/></svg>'
VIEWED = '<label class="viewed"><input type="checkbox"> Viewed</label>'


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


def fold(name, closed=False):
    return (f'<button type="button" class="fold" aria-expanded="{"false" if closed else "true"}" aria-label="{html.escape(name)}">'
            '<svg class="ou-icon" aria-hidden="true"><use href="#ou-chevron"/></svg></button>')


def block(head, body, key, name, closed=False, bid="", caller=False):
    attrs = ' id="%s"' % bid if bid else ""
    if not body:
        return f'<div class="fblock"{attrs}><div class="fh">{head}</div></div>'
    closed = closed or bool(TEST_PATH.search(split_where(name)[0]))
    return (f'<div class="fblock{" caller" if caller else ""}{" closed" if closed else ""}"{attrs} data-key="{key}">'
            f'<div class="fh">{fold(name, closed)}{head}{VIEWED}</div>{body}</div>')


def short_id(*parts):
    return "t" + hashlib.sha256("|".join(parts).encode()).hexdigest()[:8]


def slug(name, taken):
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "area"
    sid, n = base, 2
    while sid in taken:
        sid, n = f"{base}-{n}", n + 1
    taken.add(sid)
    return sid


TICKET = r"[A-Z][A-Z0-9]{1,9}-\d+"
TICKETS = rf"[(\[]\s*{TICKET}(?:\s*(?:[,/&]|and)\s*{TICKET})*\s*[)\]]|#{TICKET}\b"


def title_parts(meta):
    title = meta.get("title", "")
    keys = re.findall(TICKET, " ".join(re.findall(TICKETS, title)))
    keys = keys or [k.upper() for k in re.findall(rf"\b{TICKET}\b", meta.get("headRefName", ""), re.I)[:1]]
    rest = re.sub(TICKETS, "", title)
    for k in keys:
        rest = re.sub(rf"\b{k}\b", "", rest, flags=re.I)
    rest = " ".join(rest.split()) or title
    m = re.match(r"([\w.-]+(?:\([^)]*\))?!?):\s+(.+)", rest)
    kind, rest = m.groups() if m else ("", rest)
    return kind, (rest[0].upper() + rest[1:] if re.match(r"[a-z]+\b", rest) else rest), list(dict.fromkeys(keys))


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


def check(data, files, diff, owners):
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
        if words(h.get("note")) > WORD_CAPS["note"]:
            warnings.append(f"housekeeping: the note on {h.get('where')} runs past {WORD_CAPS['note']} words")
    if words(data.get("summary")) > WORD_CAPS["summary"]:
        warnings.append(f"summary runs past {WORD_CAPS['summary']} words")
    teams = {t.get("owner"): t for t in data.get("teams") or []}
    for owner in sorted(set(teams) - set(owners)):
        warnings.append(f"teams: {owner} owns no file in owners.tsv, so its row doesn't show")
    for owner in sorted(set(owners) - set(teams)):
        warnings.append(f"teams: {owner} is in owners.tsv but has no row in teams")
    for owner, t in teams.items():
        for field in ("why", "what_changes"):
            if words(t.get(field)) > WORD_CAPS[field]:
                warnings.append(f"teams: the {field} for {owner} runs past {WORD_CAPS[field]} words")
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

    def head_link(self, path):
        return (f'<a href="{html.escape(self.files.href(path))}" title="{html.escape(path)}" {EXTERNAL}>'
                f'<code>{html.escape(self.files.label(path))}</code>{ICON}</a>')

    def block(self, path, marks, expand, tid, bid="", closed=False):
        fd = self.diff.get(path)
        head = self.head_link(path)
        wrap = lambda body: block(head, body, short_id(tid, json.dumps(fd)), path, closed, bid)
        if not fd or fd["binary"] or not fd["hunks"]:
            note = "Binary file" if fd and fd["binary"] else "No line changes"
            return set(), wrap(f'<p class="nodiff">{note}. Open it on GitHub to see it.</p>')
        lines = [l for h in fd["hunks"] for l in h["lines"]]
        head += f' <span class="stat">+{sum(l["kind"] == "+" for l in lines)} −{sum(l["kind"] == "-" for l in lines)}</span>'
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
        return placed, wrap(f'<div class="fwrap"><table class="diff" id="{tid}" data-pr="{gh}" data-lang="{lang(path)}">{"".join(body)}</table></div>')

    def callers(self, path, hits, tid):
        src, notes, ranges = self.read("base", path), collections.defaultdict(list), []
        for k, n, note in hits:
            notes[n].append((k, note))
        for n in sorted(notes):
            lo, hi = max(1, n - SNIPPET), min(len(src), n + SNIPPET)
            if ranges and lo <= ranges[-1][1] + 1:
                ranges[-1][1] = max(ranges[-1][1], hi)
            else:
                ranges.append([lo, hi])
        rows = []
        for lo, hi in ranges:
            if rows:
                rows.append('<tr class="skip"><td colspan="3">⋯</td></tr>')
            for n in range(lo, hi + 1):
                rows += [f'<tr class="lbl" id="{k}"><td colspan="3">{esc(note)}</td></tr>' for k, note in notes.get(n, [])]
                rows.append(self.row({"kind": " ", "old": None, "new": n, "text": src[n - 1]}, tid, " focus" if n in notes else " dim", n == ranges[0][0]))
        table = (f'<div class="fwrap"><table class="diff" id="{tid}" data-blob="{html.escape(self.files.href(path))}" '
                 f'data-lang="{lang(path)}">{"".join(rows)}</table></div>')
        return block(self.head_link(path), table, tid, path, caller=True)


def change_html(c, target, targets, files):
    lines = split_where(c.get("where"))[1]
    also = c.get("also") or []
    more = (f' <details class="also"><summary>and {len(also)} more</summary>'
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
        got, fb = code.block(path, marks, True, short_id(aid, path), fid)
        placed.update(got)
        blocks.append(fb)
    tests = a["tests"]
    if tests["files"]:
        blocks.append('<p class="label">Tests</p>' + "".join(code.block(p, [], True, short_id(aid, p))[1] for p in tests["files"]))
    reach = a["reach"]
    if reach:
        blocks.append('<p class="label">Callers outside this PR</p>')
    by_path = {}
    for j, r in enumerate(reach):
        by_path.setdefault(split_where(str(r.get("where")))[0], []).append((f"{aid}-x{j}", r))
    for path, hits in by_path.items():
        lines = {k: split_where(str(r.get("where")))[1] for k, r in hits} if code.read("base", path) else {}
        shown = [(k, span(lines[k])[0], r.get("note")) for k, r in hits if lines.get(k)]
        if shown:
            blocks.append(code.callers(path, shown, short_id(aid, "caller", *(str(r.get("where")) for _, r in hits))))
        blocks += [block(f'<span>{esc(r.get("note"))}</span> {files.link(str(r.get("where")))}', "", k, path, bid=k)
                   for k, r in hits if not lines.get(k)]
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
        listed = lambda label, items, none: (f'<p><strong>{label}</strong></p><ul class="tests">{"".join(f"<li>{esc(t)}</li>" for t in items)}</ul>'
                                             if items else f'<p><strong>{label}:</strong> {none}.</p>')
        facts.append(("Tests", listed("Tested", covered, "nothing in this PR") + listed("Not tested", gaps, "no gaps found")))
    facts_html = "".join(f"<dt>{dt}</dt><dd>{dd}</dd>" for dt, dd in facts)
    key = short_id(aid, *(json.dumps(code.diff.get(p)) for p in sorted(area_paths(a))))
    return f"""
<section class="area" id="{aid}" data-key="{key}">
  <div class="ah">{fold(a["name"])}<h2><span class="num">{i}</span> {esc(a.get('name'))}</h2>{VIEWED}</div>
  <div class="prose">
    <p class="gist">{esc(a.get('gist'))}</p>
    {delta}
    {sketch_html(s) if s else ""}
    <dl class="facts">{facts_html}</dl>
  </div>
  <div class="code">{"".join(blocks)}</div>
</section>"""


def area_paths(a):
    return ({split_where(c.get("where"))[0] for c in a["changes"]} | {p for c in a["changes"] for p in c.get("also") or []}
            | set(a["tests"]["files"]))


def teams_html(data, owners, areas, ids, housekeeping):
    notes = {t.get("owner"): t for t in data.get("teams") or []}
    skippable = {split_where(h.get("where"))[0] for h in housekeeping}
    rows = []
    for owner, paths in sorted(owners.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        links = [f'<a href="#{aid}" title="{html.escape(a["name"])}">{i}</a>'
                 for i, (a, aid) in enumerate(zip(areas, ids), 1) if paths & area_paths(a)]
        links += ['<a href="#housekeeping">housekeeping</a>'] if paths & skippable else []
        n = notes.get(owner, {})
        what = f'<p class="what">{esc(n["what_changes"])}</p>' if n.get("what_changes") else ""
        rows.append(f'<li><p class="who"><strong title="{html.escape(owner)}">{html.escape(owner.lstrip("@").rsplit("/", 1)[-1])}</strong>'
                    f'<span>{len(paths)} file{"" if len(paths) == 1 else "s"} · {", ".join(links)}</span></p>'
                    f'<div><p>{esc(n.get("why"))}</p>{what}</div></li>')
    return f'<section class="teams"><h2>Why each team is here</h2><ul>{"".join(rows)}</ul></section>' if rows else ""


def housekeeping_html(housekeeping, code):
    files = code.files
    items, blocks = [], []
    for k, h in enumerate(housekeeping):
        path = split_where(h.get("where"))[0]
        items.append(f'<li>{esc(h.get("note"))} {files.link(path, href=f"#hk-{k}")}</li>')
        blocks.append(code.block(path, [], False, short_id("housekeeping", path), f"hk-{k}", True)[1])
    key = short_id("housekeeping", *(json.dumps(code.diff.get(split_where(h.get("where"))[0])) for h in housekeeping))
    return f"""
<section class="area" id="housekeeping" data-key="{key}">
  <div class="ah">{fold("Housekeeping")}<h2>Housekeeping</h2>{VIEWED}</div>
  <div class="prose"><p class="gist">Files with no behavior of their own.</p><ul class="hk">{"".join(items)}</ul></div>
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
    owners = collections.defaultdict(set)
    for owner, path in (l.rstrip("\n").split("\t") for l in open(f"{gather}/owners.tsv") if not l.startswith("#")):
        owners[owner].add(path)

    warnings = []
    for a in data.get("areas") or []:
        normalize(a, set(changed), warnings)
    errors, more, missing = check(data, files_tsv, diff, owners)
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
    symbols = "".join(re.search(rf'<symbol id="{i}".*?</symbol>', sprite, re.S).group(0) for i in ("ou-external", "ou-chevron"))
    kind, title, keys = title_parts(meta)
    url = os.environ.get("TICKET_URL", "")
    ticket = "".join(f' · <a href="{html.escape(url.replace("{key}", k))}" title="Open the ticket" {EXTERNAL}>{k} {ICON}</a>' if url
                     else f" · {k}" for k in keys)
    kind = f" · <code>{html.escape(kind)}</code>" if kind else ""

    page = f"""<!doctype html>
<html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Lato:wght@400;700;900&display=swap" rel="stylesheet">
<title>{html.escape(repo)} #{number} walkthrough</title>
<style>{tokens}{CSS}{MARK_CSS}</style></head>
<body>
{stamp}
<svg width="0" height="0" style="position:absolute" aria-hidden="true">{symbols}</svg>
<main class="page" data-store="{html.escape(repo)}#{number}">
  <header>
    <div class="top"><h1>{html.escape(title)}</h1>{toggle}</div>
    <p class="meta">{html.escape(repo)} #{number}{kind} · {esc(meta['author']['login'])} · built from <code>{head[:7]}</code> · <a href="{html.escape(meta['url'])}" {EXTERNAL}>Open the PR {ICON}</a>{ticket}</p>
    <p class="summary">{esc(data.get('summary'))}</p>
    <p class="cta"><a class="pill" href="{html.escape(meta['url'])}/files" {EXTERNAL}>Approve on GitHub {ICON}</a></p>
  </header>
  {teams_html(data, owners, areas, ids, housekeeping)}
  {overview_html}
  <section class="order"><h2>Reading order</h2><ol>{order}</ol>
    <p class="hint">The code for each area sits beside it. Click a line to comment on it. Mark a file or an area viewed to fold it away.</p></section>
  {sections}
</main>
<div id="line-actions" class="actions" hidden><button type="button" class="pill" data-act="here">Comment here</button><a class="pill" data-act="gh" {EXTERNAL}>Comment on GitHub {ICON}</a></div>
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
h1 { font-size: var(--ou-size-h3); line-height: 1.375; margin: var(--ou-space-1) 0 0; min-width: 0; }
h2 { font-size: var(--ou-size-h4); line-height: 1.5385; margin: 0 0 var(--ou-space-1); }
section:not(.area) > h2 { font-size: var(--ou-size-h6); line-height: 1.3333; margin-bottom: var(--ou-space-2); }
.meta { font-size: var(--ou-size-body); color: var(--ou-text-secondary); margin: var(--ou-space-1) 0 0; max-width: none; }
.meta :is(code, a) { white-space: nowrap; }
.summary { background: var(--ou-accent-wash); border-radius: var(--ou-radius-md); padding: var(--ou-space-2) var(--ou-space-3); margin: var(--ou-space-3) 0 var(--ou-space-2); }
.cta { margin: 0 0 var(--ou-space-5); }
section { border: 1px solid var(--ou-border); border-radius: var(--ou-radius-md); padding: var(--ou-space-3); margin-top: var(--ou-space-3); scroll-margin-top: var(--ou-space-2); }
.teams ul { margin: 0; padding: 0; list-style: none; }
.teams li { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 4fr); gap: var(--ou-space-1) var(--ou-space-3); max-width: none; margin: 0; }
.teams li + li { margin-top: var(--ou-space-2); padding-top: var(--ou-space-2); border-top: 1px solid var(--ou-border); }
.teams p { margin: 0; }
.who span { display: block; font-size: var(--ou-size-caption); color: var(--ou-text-secondary); }
.teams li > div { max-width: var(--ou-measure); }
.teams .what { margin-top: var(--ou-space-1); max-width: none; font-size: var(--ou-size-body); line-height: 1.6; }
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
.chip { display: inline-block; font-size: var(--ou-size-caption); font-weight: var(--ou-weight-medium); background: var(--ou-fill); color: var(--ou-text); border-radius: var(--ou-radius-lg); padding: 0 10px; margin-right: var(--ou-space-half); white-space: nowrap; vertical-align: 1.5px; }
.chip.contract { background: var(--ou-warning); color: var(--ou-warning-text); }
.facts { display: grid; grid-template-columns: max-content 1fr; gap: var(--ou-space-1) var(--ou-space-2); margin: 0; padding-top: var(--ou-space-2); border-top: 1px solid var(--ou-border); font-size: var(--ou-size-body); line-height: 1.6; }
.facts dt { font-weight: var(--ou-weight-medium); margin: 0; color: var(--ou-text-secondary); }
.facts dd { margin: 0; min-width: 0; }
.facts ul { margin: 0; padding: 0; list-style: none; }
.facts li { margin: 0 0 var(--ou-space-half); }
.facts p { margin: 0; }
.facts .tests { list-style: disc; padding-left: 1.25em; }
.facts .tests + p { margin-top: var(--ou-space-1); }
.facts .chip { vertical-align: 0.5px; }
.changes > li { margin: 0 0 var(--ou-space-1); }
.changes ul { margin: var(--ou-space-half) 0 0; padding-left: var(--ou-space-3); list-style: disc; }
.also { display: inline; }
.also summary { display: inline; cursor: pointer; color: var(--ou-text-secondary); }
.also[open] { display: block; }
.hint { font-size: var(--ou-size-body); margin: var(--ou-space-2) 0 0; }
.hk { margin: 0; padding: 0; list-style: none; font-size: var(--ou-size-body); }
.hk li { margin: 0 0 var(--ou-space-half); }
.area { display: grid; grid-template-columns: minmax(0, 5fr) minmax(0, 7fr); gap: var(--ou-space-1) var(--ou-space-3); align-items: start; }
.ah { grid-column: 1 / -1; display: flex; align-items: center; gap: var(--ou-space-1); }
[data-key] > :is(.fh, .ah) { cursor: pointer; }
.ah h2 { margin: 0; }
.fold { display: inline-flex; padding: 2px; margin: 0 -2px; background: none; border: 0; border-radius: var(--ou-radius-sm); color: var(--ou-text-secondary); cursor: pointer; }
.fold .ou-icon { transform: rotate(90deg); transition: transform var(--ou-duration-press) var(--ou-ease-standard); }
.closed > * > .fold .ou-icon { transform: none; }
.viewed { display: inline-flex; align-items: center; gap: 6px; padding: 6px; margin: -6px -6px -6px auto; font-size: var(--ou-size-caption); font-family: var(--ou-font-body); color: var(--ou-text-secondary); white-space: nowrap; cursor: pointer; }
.viewed input { appearance: none; flex: none; width: 20px; height: 20px; margin: 0; border: 2px solid var(--ou-text-hint); border-radius: var(--ou-radius-sm); background: var(--ou-surface) center / 18px no-repeat; cursor: pointer; transition: background-color 150ms var(--ou-ease-standard), border-color 150ms var(--ou-ease-standard); }
.viewed:hover input { border-color: var(--ou-text-secondary); }
.viewed input:checked { border-color: var(--ou-accent); background-color: var(--ou-accent); background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23fff'%3E%3Cpath d='m9.54988 17.575c-.13333 0-.25833-.021-.375-.063-.11667-.0413-.225-.112-.325-.212l-4.3-4.3c-.18333-.1833-.271-.421-.263-.713.00867-.2913.10466-.5287.288-.712.18333-.1833.41667-.275.7-.275s.51667.0917.7.275l3.575 3.575 8.47502-8.47501c.1833-.18333.421-.275.713-.275.2913 0 .5286.09167.712.275.1833.18334.275.42067.275.712 0 .292-.0917.52967-.275.713l-9.2 9.20001c-.1.1-.2084.1707-.32502.212-.11667.042-.24167.063-.375.063z'/%3E%3C/svg%3E"); }
.viewed:hover input:checked { border-color: var(--ou-accent-hover); background-color: var(--ou-accent-hover); }
.viewed input:checked:active { border-color: var(--ou-accent-pressed); background-color: var(--ou-accent-pressed); }
.area.closed > :not(.ah), .fblock.closed > :not(.fh) { display: none; }
.area > .code { position: sticky; top: var(--ou-space-2); max-height: calc(100vh - 2 * var(--ou-space-2)); overflow: auto; min-width: 0; scrollbar-width: none; }
.area > .code::-webkit-scrollbar { display: none; }
.fblock { border: 1px solid var(--ou-border); border-radius: var(--ou-radius-md); margin: 0 0 var(--ou-space-2); overflow: clip; background: var(--ou-surface); }
.fblock :is(tr, td) { scroll-margin-top: 3rem; }
.fh { position: sticky; top: 0; z-index: 1; display: flex; flex-wrap: wrap; align-items: center; gap: 2px var(--ou-space-1); padding: 6px 12px; background: var(--ou-surface-sunken); border-bottom: 1px solid var(--ou-border); font-size: var(--ou-size-body); }
.fblock.closed > .fh { border-bottom: 0; }
.fh > a { text-decoration: none; font-weight: var(--ou-weight-medium); }
.stat { color: var(--ou-text-secondary); font-size: var(--ou-size-caption); }
.nodiff { margin: 0; padding: var(--ou-space-1) 12px; color: var(--ou-text-secondary); font-size: var(--ou-size-body); max-width: none; }
.label { font-weight: var(--ou-weight-medium); font-size: var(--ou-size-body); color: var(--ou-text-secondary); margin: var(--ou-space-3) 0 var(--ou-space-1); }
.fwrap { overflow-x: auto; }
table.diff { border-collapse: collapse; width: 100%; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: var(--ou-size-caption); line-height: 1.6; }
.diff td { padding: 0; vertical-align: top; transition: background-color var(--ou-duration-press) var(--ou-ease-standard); }
tr.l td { cursor: pointer; }
td.o, td.n { width: 1%; padding: 0 8px; text-align: right; white-space: nowrap; color: var(--ou-text-secondary); user-select: none; }
tr.l:hover td { background-image: linear-gradient(color-mix(in srgb, var(--ou-accent) 10%, transparent) 0 0); }
tr.l:hover td.o, tr.l:hover td.n { color: var(--ou-accent-pressed); }
td.c { position: relative; white-space: pre-wrap; padding: 0 16px 0 20px; tab-size: 4; }
tr.add td { background: color-mix(in srgb, var(--ou-accent) 12%, transparent); }
tr.del td { background: color-mix(in srgb, var(--ou-error) 12%, transparent); }
tr.add td.c::before, tr.del td.c::before { position: absolute; left: 6px; }
tr.add td.c::before { content: "+"; color: var(--ou-accent-pressed); }
tr.del td.c::before { content: "-"; color: var(--ou-error); }
tr.dim td { opacity: 0.45; }
tr.focus td.o { box-shadow: inset 3px 0 0 var(--ou-accent); }
tr.lbl td { padding: 6px 12px; white-space: normal; font-family: var(--ou-font-body); font-size: var(--ou-size-body); font-weight: var(--ou-weight-medium); background: var(--ou-accent-wash); border-top: 1px solid var(--ou-border); }
tr.gap td { padding: 2px 12px; background: var(--ou-surface-sunken); }
tr.skip td { padding: 0 12px; background: var(--ou-surface-sunken); color: var(--ou-text-hint); }
tr.gap button { font: inherit; font-family: var(--ou-font-body); font-size: var(--ou-size-caption); color: var(--ou-accent-pressed); background: none; border: 0; cursor: pointer; }
tr.gap button:hover { color: var(--ou-accent-hover); }
tr.picked td { background-color: var(--ou-accent-wash); }
tr.flash td, .fblock.flash { background-color: color-mix(in srgb, var(--ou-warning) 24%, transparent); }
.actions { position: fixed; z-index: 30; display: flex; gap: var(--ou-space-1); padding: var(--ou-space-1); background: var(--ou-surface); border: 1px solid var(--ou-border); border-radius: var(--ou-radius-sm); box-shadow: var(--ou-shadow-2); }
:root[data-theme="dark"] .actions { box-shadow: none; }
.pill { display: inline-flex; align-items: center; gap: var(--ou-space-half); height: 32px; padding: 0 var(--ou-space-2); border: 1px solid var(--ou-accent); border-radius: var(--ou-radius-pill); background: var(--ou-accent); color: var(--ou-text-on-accent); font: inherit; font-family: var(--ou-font-body); font-size: var(--ou-size-body); font-weight: var(--ou-weight-medium); white-space: nowrap; text-decoration: none; cursor: pointer; transition: background-color var(--ou-duration-press) var(--ou-ease-standard), border-color var(--ou-duration-press) var(--ou-ease-standard); }
.pill:hover { background: var(--ou-accent-hover); border-color: var(--ou-accent-hover); color: var(--ou-text-on-accent); }
.pill:active { background: var(--ou-accent-pressed); border-color: var(--ou-accent-pressed); }
.can-comment .actions [data-act=gh] { background: var(--ou-surface); border-color: var(--ou-accent-pressed); color: var(--ou-accent-pressed); }
.can-comment .actions [data-act=gh]:hover { background: var(--ou-accent-wash); }
.can-comment .actions [data-act=gh]:active { background: color-mix(in srgb, var(--ou-accent) 24%, var(--ou-surface)); }
.actions[hidden] { display: none; }
.actions [data-act=here] { display: none; }
.can-comment .actions [data-act=here] { display: inline-flex; }
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
  .ah { margin-bottom: var(--ou-space-1); }
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
  .teams li { grid-template-columns: 1fr; }
  .summary { padding: var(--ou-space-2); }
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
const sources = {}, STORE = "walkthrough " + document.querySelector("main").dataset.store;
const folds = new Map([...document.querySelectorAll("[data-key]")].map(el => [el.dataset.key, el]));
let picked = null, comments = null, misses = 0, saved = {};
try { saved = JSON.parse(localStorage.getItem(STORE)) || {}; } catch {}
for (const key of Object.keys(saved)) if (!folds.has(key)) delete saved[key];

const box = el => el.querySelector(":scope > :is(.fh, .ah) .viewed input");
const isOpen = el => !el.classList.contains("closed");

function show(el, open, viewed) {
  el.classList.toggle("closed", !open);
  el.querySelector(":scope > :is(.fh, .ah) .fold").setAttribute("aria-expanded", open);
  box(el).checked = viewed;
  saved[el.dataset.key] = {open, viewed};
  try { localStorage.setItem(STORE, JSON.stringify(saved)); } catch {}
}
for (const [key, el] of folds) if (saved[key]) show(el, saved[key].open, saved[key].viewed);

function reveal(target) {
  for (let el = target.closest("[data-key]"); el; el = el.parentElement.closest("[data-key]")) {
    if (!isOpen(el) || box(el).checked) show(el, true, false);
  }
}

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

function openBar(cell, keyboard, x) {
  const tr = cell.parentElement, table = tr.closest("table"), {n, o} = tr.dataset;
  closeBar();
  picked = tr;
  tr.classList.add("picked");
  github.href = table.dataset.pr ? table.dataset.pr + (n ? "R" + n : "L" + o) : table.dataset.blob + "#L" + n;
  bar.hidden = false;
  const r = cell.getBoundingClientRect(), fits = r.bottom + 4 + bar.offsetHeight <= innerHeight;
  bar.style.left = Math.max(0, Math.min(x ?? r.left, innerWidth - bar.offsetWidth - 8)) + "px";
  bar.style.top = (fits ? r.bottom + 4 : r.top - 4 - bar.offsetHeight) + "px";
  if (keyboard) (root.classList.contains("can-comment") ? here : github).focus();
}

function zoom(sketch) {
  const on = !sketch.classList.contains("zoom");
  document.querySelector(".sketch.zoom")?.classList.remove("zoom");
  sketch.classList.toggle("zoom", on);
}

function jump(target) {
  const pane = target.closest(".code");
  if (pane && getComputedStyle(pane).position === "sticky" && pane.scrollHeight > pane.clientHeight) {
    const lift = pane.getBoundingClientRect().top - parseFloat(getComputedStyle(pane).top);
    if (lift < 0) scrollBy({top: lift, behavior: smooth});
    const head = target.matches(".fblock") ? null : target.closest(".fblock")?.querySelector(":scope > .fh");
    pane.scrollTo({top: pane.scrollTop + target.getBoundingClientRect().top - pane.getBoundingClientRect().top - 12 - (head?.offsetHeight || 0), behavior: smooth});
  } else {
    target.scrollIntoView({block: "center", behavior: smooth});
  }
  if (!target.hasAttribute("tabindex")) target.tabIndex = -1;
  target.focus({preventScroll: true});
  target.classList.add("flash");
  setTimeout(() => target.classList.remove("flash"), 1200);
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
  const dragged = !t.closest("button, td.o, td.n") && !getSelection().isCollapsed && getSelection().containsNode(t, true);
  const cell = !dragged && t.closest("tr.l td");
  if (cell) return cell.parentElement === picked ? closeBar() : openBar(cell, false, event.clientX);
  closeBar();
  const gap = t.closest("tr.gap button");
  if (gap) return expand(gap.closest("tr.gap"));
  const link = t.closest('a[href^="#"]'), target = link && document.getElementById(decodeURIComponent(link.hash.slice(1)));
  if (target) reveal(target);
  if (target && link.matches(".jump")) {
    jump(target);
    return event.preventDefault();
  }
  const head = !dragged && !t.closest("a, label") && t.closest("[data-key] > :is(.fh, .ah)");
  if (head) {
    const el = head.parentElement;
    return show(el, !isOpen(el), box(el).checked);
  }
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
document.addEventListener("change", event => {
  const input = event.target.closest(".viewed input");
  if (!input) return;
  const item = input.closest("[data-key]"), area = item.parentElement.closest(".area[data-key]");
  show(item, !input.checked, input.checked);
  if (!area || item.matches(".caller")) return;
  const files = [...area.querySelectorAll(".fblock[data-key]:not(.caller)")];
  if (input.checked && files.every(f => box(f).checked)) show(area, false, true);
  else if (!input.checked && box(area).checked) show(area, isOpen(area), false);
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
