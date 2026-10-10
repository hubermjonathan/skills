#!/usr/bin/env python3
import collections
import glob
import json
import os
import re
import sys
import time

USAGE = """usage:
  skill-audit.py extract [--days N] [--since YYYY-MM-DD] [--out events.tsv]
  skill-audit.py check <expectations.json> <events.tsv> [--window N] [--skip-cwd REGEX]"""


def transcript_files():
    dirs = os.environ.get("TRANSCRIPT_DIRS")
    if not dirs:
        sys.exit("TRANSCRIPT_DIRS is not set. Set it to the session stores, colon-separated. The find-transcript skill lists them.")
    for root in dirs.split(":"):
        yield from glob.glob(f"{root}/**/*.jsonl", recursive=True)


def skill_from_path(text):
    m = re.search(r"([A-Za-z0-9_.-]+)/SKILL\.md", text)
    return m.group(1) if m else None


def events(path):
    session = os.path.basename(path).removesuffix(".jsonl")
    agent, cwd = "", ""
    for line in open(path, errors="replace"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        ts = d.get("timestamp", "")
        agent = d.get("entrypoint") or agent
        cwd = d.get("cwd") or cwd
        listing = d.get("attachment") or {}
        if listing.get("type") == "skill_listing":
            for name in listing.get("names") or []:
                yield session, agent, cwd, ts, "listed", name, ""
            continue
        payload = d.get("payload") or {}
        if payload.get("type") == "function_call":
            agent = agent or "codex"
            args = payload.get("arguments", "")
            yield session, agent, cwd, ts, "tool", payload.get("name", ""), args[:300]
            if skill_from_path(args):
                yield session, agent, cwd, ts, "skill", skill_from_path(args), "read"
            continue
        content = (d.get("message") or {}).get("content")
        typed = re.search(r"<command-name>/([^<]+)</command-name>", content) if d.get("type") == "user" and isinstance(content, str) else None
        if typed:
            yield session, agent, cwd, ts, "skill", typed.group(1), "slash"
        if not isinstance(content, list):
            continue
        for b in content:
            if b.get("type") != "tool_use":
                continue
            inp = json.dumps(b.get("input"), ensure_ascii=False)
            if b.get("name") == "Skill":
                yield session, agent, cwd, ts, "skill", (b.get("input") or {}).get("skill", ""), "tool"
                continue
            yield session, agent, cwd, ts, "tool", b.get("name", ""), inp[:300]
            if b.get("name") == "Read" and skill_from_path(inp):
                yield session, agent, cwd, ts, "skill", skill_from_path(inp), "read"


def extract(argv):
    days = float(argv[argv.index("--days") + 1]) if "--days" in argv else 30
    out = argv[argv.index("--out") + 1] if "--out" in argv else "events.tsv"
    since = argv[argv.index("--since") + 1] if "--since" in argv else ""
    cutoff = time.time() - days * 86400
    if since and "--days" not in argv:
        cutoff = time.mktime(time.strptime(since, "%Y-%m-%d"))
    rows = 0
    with open(out, "w") as f:
        f.write("session\tagent\tcwd\tts\tkind\tname\tdetail\n")
        for path in transcript_files():
            if os.path.getmtime(path) < cutoff:
                continue
            for e in events(path):
                if e[3] < since:
                    continue
                f.write("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in e) + "\n")
                rows += 1
    print(f"{rows} events -> {out}")


def same(name, want):
    return name == want or (":" not in want and name.split(":")[-1] == want)


def check(argv):
    rules = json.load(open(argv[0]))
    window = int(argv[argv.index("--window") + 1]) if "--window" in argv else 40
    skip_cwd = argv[argv.index("--skip-cwd") + 1] if "--skip-cwd" in argv else r"^(/private)?/(tmp|var/folders)/"
    skipped = set()
    by_session = collections.defaultdict(list)
    listed = collections.defaultdict(list)
    for line in list(open(argv[1]))[1:]:
        session, agent, cwd, ts, kind, name, detail = line.rstrip("\n").split("\t", 6)
        if skip_cwd and re.search(skip_cwd, cwd + "/"):
            skipped.add(session)
        if kind == "listed":
            listed[session].append((len(by_session[session]), name))
            continue
        by_session[session].append((kind, name, detail, ts))

    for session in skipped:
        by_session.pop(session, None)
    print(f"{len(by_session)} sessions, {len(skipped)} skipped by --skip-cwd\n")

    loaded = collections.Counter()
    for evs in by_session.values():
        for s in {n for k, n, _, _ in evs if k == "skill"}:
            loaded[s] += 1
    print("## Sessions that loaded each skill")
    for s, n in loaded.most_common():
        print(f"- {s}: {n}")

    print("\n## Expectations")
    for rule in rules:
        expect = rule["expect"]
        hits, misses, missing = 0, [], 0
        for session, evs in by_session.items():
            for i, (kind, name, detail, ts) in enumerate(evs):
                if "after" in rule:
                    fired = kind == "skill" and same(name, rule["after"])
                else:
                    fired = kind == "tool" and re.search(rule.get("tool", "."), name) and re.search(rule.get("match", "."), detail)
                if not fired:
                    continue
                if session in listed and not any(pos <= i and same(n, expect) for pos, n in listed[session]):
                    missing += 1
                    if "after" in rule:
                        break
                    continue
                nearby = evs[i:i + window] if "after" in rule else evs[:i + 1]
                if any(k == "skill" and same(n, expect) for k, n, _, _ in nearby):
                    hits += 1
                else:
                    misses.append(f"{session} {ts}")
                if "after" in rule:
                    break
        total = hits + len(misses)
        label = f"after `{rule['after']}`" if "after" in rule else f"`{rule.get('tool', '.')}` matching `{rule.get('match', '.')}`"
        rate = f"{hits}/{total} ({hits * 100 // total}%)" if total else "never happened"
        print(f"- {label} -> `{expect}`: {rate}" + (f", plus {missing} where `{expect}` was not installed" if missing else ""))
        for m in misses[:5]:
            print(f"  - miss: {m}")


def main(argv):
    if len(argv) < 2 or argv[1] not in ("extract", "check"):
        sys.exit(USAGE)
    if argv[1] == "extract":
        extract(argv[2:])
    elif len(argv) < 4:
        sys.exit(USAGE)
    else:
        check(argv[2:])


if __name__ == "__main__":
    main(sys.argv)
