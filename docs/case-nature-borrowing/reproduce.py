# -*- coding: utf-8 -*-
"""为「从 Nature 借来的四条」做实测：G13/G14 的召回、精确率、dpi、色板、载荷。

运行：python docs/case-nature-borrowing/reproduce.py
输出：docs/case-nature-borrowing/data/measurements.json（论文所有数字的唯一来源）

纪律：每处注入都断言「文本确实变了」（must_change）。静默失效会让测量结论变假——
这是 case-selfhost 的 c9 踩过的坑，本脚本沿用同一防护。
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "docs/case-nature-borrowing"
BASE = ROOT / "docs/case-selfhost/04-论文.md"      # 复用已全绿的自举论文做基线
LEDGER = ROOT / "docs/case-selfhost/02-证据账本.json"
LINT = ROOT / "tools/paper_lint.py"
FIG = ROOT / "tools/paper_figure.py"
DATA = CASE / "data"


def run_lint(text: str, genre: str = "M", name: str = "_probe", ledger: Path | None = None) -> dict:
    tmp = DATA / f"{name}.md"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(text, encoding="utf-8")
    args = {"path": str(tmp), "genre": genre}
    if ledger:
        args["ledger"] = str(ledger)
    p = subprocess.run([sys.executable, str(LINT)],
                       input=json.dumps({"args": args}),
                       capture_output=True, text=True, encoding="utf-8")
    tmp.unlink(missing_ok=True)
    return json.loads(p.stdout)["result"]


def run_figure(payload: dict, out: Path) -> dict:
    p = subprocess.run([sys.executable, str(FIG)],
                       input=json.dumps({"args": {"data": payload, "out": str(out)}}),
                       capture_output=True, text=True, encoding="utf-8")
    return json.loads(p.stdout)


def must_change(before: str, after: str, name: str) -> str:
    if before == after:
        raise SystemExit(f"注入未生效：{name} —— 锚点文本已不存在，请更新探针定义")
    return after


def sub1(text: str, old: str, new: str, name: str) -> str:
    if old not in text:
        raise SystemExit(f"锚点不存在：{name}")
    return must_change(text, text.replace(old, new, 1), name)


def gates(r: dict, ids=("G13", "G14")) -> dict:
    return {g["id"]: g["pass"] for g in r["gates"] if g["id"] in ids}


def main() -> int:
    base = BASE.read_text(encoding="utf-8")
    probes = []

    def add(name, text, expect_g13, expect_g14, intent):
        r = run_lint(text, name=name)
        rl = run_lint(text, name=name + "-ledger", ledger=LEDGER)
        g = gates(r)
        probes.append({
            "probe": name, "intent": intent,
            "g13_pass": g["G13"], "g14_pass": g["G14"],
            "g13_expected_pass": expect_g13, "g14_expected_pass": expect_g14,
            "g13_ok": g["G13"] == expect_g13, "g14_ok": g["G14"] == expect_g14,
            "failed": r["failed"], "chars": len(text),
            "gates_passed_with_ledger": sum(1 for x in rl["gates"] if x["pass"]),
            "gates_total": len(rl["gates"]),
            "failed_with_ledger": rl["failed"],
        })
        return r

    # ── 基线 ────────────────────────────────────────────────────────────
    add("P0-baseline", base, True, True, "compliant draft, no statistics at all")

    # ── P1：带 ± 但不给口径 → G13 应红 ────────────────────────────────
    p1 = sub1(base, "we reach 12\non GateLint", "we reach 12 \u00b1 0.8\non GateLint", "P1")
    add("P1-errorbar-nodecl", p1, False, True, "error bar introduced, no definition anywhere")

    # ── P2：P1 + 口径声明 → G13 应转绿 ────────────────────────────────
    p2 = sub1(p1, "Note that the aforementioned costs include only",
              "Error bars denote one standard deviation over n = 5 repeated runs. "
              "Note that the aforementioned costs include only", "P2")
    add("P2-errorbar-decl", p2, True, True, "same error bar, now defined with s.d. and n")

    # ── P3：图注带 ± 但不给 n → G14 应红 ──────────────────────────────
    cap_old = re.search(r"^\*\*Figure 1:.*?\*\*$", base, re.M | re.S).group(0)
    p3 = sub1(base, cap_old,
              "**Figure 1: Gate counts across six drafts scored by the same checker.** "
              "Bars show the number of the twelve hard gates satisfied, with \u00b1 0.8 "
              "denoting the spread over repeated scorings. The compliant draft reaches twelve "
              "and the naive control reaches two.**", "P3")
    add("P3-caption-non", p3, False, False, "figure caption gains an error bar but no n")

    # ── P4：P3 + 图注给 n → G14 应转绿 ────────────────────────────────
    p4 = sub1(p3, "denoting the spread over repeated scorings",
              "denoting one standard deviation over n = 5 repeated scorings", "P4")
    add("P4-caption-withn", p4, True, True, "same caption, n = 5 supplied inside the caption")

    # ── P5：一处声明 + 两处远处误差棒 → G13 是否逐处绑定？──────────────
    p5 = sub1(base, "we reach 12\non GateLint", "we reach 12 \u00b1 0.8\non GateLint", "P5a")
    p5 = sub1(p5, "written without any stage of the pipeline reaches 2 on GateLint",
              "written without any stage of the pipeline reaches 2 \u00b1 0.3 on GateLint",
              "P5b")
    p5 = sub1(p5, "Note that the aforementioned costs include only",
              "The first spread is one standard deviation over n = 5 runs; the second is "
              "unreported. Note that the aforementioned costs include only", "P5c")
    add("P5-two-bars-one-decl", p5, True, True,
        "two error bars, only the first is defined; is the second also excused?")

    # ── P6：表 caption 带 ± 不给 n → G14 只查图注？────────────────────
    tab_old = "**Table 1: Payload composition of the pipeline."
    p6 = sub1(base, tab_old,
              "**Table 1: Payload composition of the pipeline, with \u00b1 0.4 on the share column.",
              "P6")
    add("P6-tablecap-non", p6, False, True,
        "table caption gains an error bar and no n; G14 reads figure captions only")

    # ── P7：'CI' 当普通词（CI pipeline）→ G13 是否误报 ────────────────
    p7 = sub1(base, "## 3 Implementation",
              "We also keep a CI pipeline that runs the checker on every push.\n\n## 3 Implementation",
              "P7")
    add("P7-CI-as-word", p7, True, True,
        "'CI' used as an ordinary abbreviation (continuous integration), no statistics present")

    # ── 语料侧：20 篇 DeepSeek 取证里统计口径出现次数 ─────────────────
    corpus = (ROOT / "registry/ds-corpus-evidence.md").read_text(encoding="utf-8")
    ref05 = (ROOT / "references/05-图表规范.md").read_text(encoding="utf-8")
    i56 = ref05.find("## 5.6")
    corpus_stats = {
        "corpus_file": "registry/ds-corpus-evidence.md",
        "corpus_bytes": len(corpus.encode("utf-8")),
        "corpus_error_bar": len(re.findall(r"error bar", corpus, re.I)),
        "corpus_plus_minus": corpus.count("\u00b1"),
        "corpus_n_equals": len(re.findall(r"\bn\s*=\s*\d+", corpus)),
        "corpus_seed": len(re.findall(r"seed", corpus, re.I)),
        "corpus_sd_or_ci": len(re.findall(r"standard deviation|confidence interval|s\.e\.m\.", corpus, re.I)),
        "ref05_5_1_to_5_5_stat_terms": len(re.findall(r"error bar|\bn\s*=\s*\d+", ref05[:i56], re.I)),
        "ref05_5_6_stat_terms": len(re.findall(r"error bar|\bn\s*=\s*\d+", ref05[i56:], re.I)),
        "ref05_bytes": len(ref05.encode("utf-8")),
    }

    # ── Nature 摘录侧：42 条硬要求，采纳 4 条 ──────────────────────────
    nat = Path("D:/ZH/vibe code/skills/tool/rsi-agent/outputs/nature-figure-spec-extract.md")
    nat_stats = {"file": str(nat), "available": nat.is_file()}
    if nat.is_file():
        t = nat.read_text(encoding="utf-8")
        rows = re.findall(r"^\| ([A-H])(\d+) \|", t, re.M)
        groups = {}
        for g, _ in rows:
            groups[g] = groups.get(g, 0) + 1
        nat_stats.update({"requirements": len(rows), "by_group": groups,
                          "bytes": len(t.encode("utf-8"))})

    # ── 渲染侧：dpi 与色板 ────────────────────────────────────────────
    DATA.mkdir(parents=True, exist_ok=True)
    figdata = json.loads((ROOT / "docs/case-selfhost/data/fig1-gates.json").read_text(encoding="utf-8"))
    figdata = figdata.get("figure", figdata)
    render = {}
    for pal in ("deepseek", "colorblind"):
        d = json.loads(json.dumps(figdata))
        d.setdefault("style", {})["palette"] = pal
        out = DATA / f"_probe-{pal}.png"
        r = run_figure(d, out)
        if not r.get("ok"):
            render[pal] = {"ok": False, "error": r.get("error")}
            continue
        from PIL import Image  # matplotlib 依赖已带 Pillow
        with Image.open(out) as im:
            render[pal] = {"ok": True, "size_px": list(im.size), "dpi": [round(v, 4) for v in im.info.get("dpi", ())]}
        out.unlink(missing_ok=True)
    # 默认（不给 palette）应等同 deepseek
    d = json.loads(json.dumps(figdata))
    d.pop("style", None)
    out = DATA / "_probe-default.png"
    r = run_figure(d, out)
    if r.get("ok"):
        from PIL import Image
        with Image.open(out) as im:
            render["default"] = {"ok": True, "size_px": list(im.size), "dpi": [round(v, 4) for v in im.info.get("dpi", ())]}
        out.unlink(missing_ok=True)

    # 色板常量直接读源码（比截图比色更可靠）
    src = (ROOT / "tools/paper_figure.py").read_text(encoding="utf-8")
    def grab(name):
        m = re.search(name + r"\s*=\s*\[(.*?)\]", src, re.S)
        return [x.strip().strip('"').strip("'") for x in m.group(1).split(",") if x.strip()] if m else []
    wong_impl = grab("WONG")
    nature_wong = ["#000000", "#e69f00", "#56b4e9", "#009e73",
                   "#f0e442", "#0072b2", "#d55e00", "#cc79a7"]
    palette = {
        "wong_in_tool": wong_impl,
        "wong_in_nature_guide": nature_wong,
        "identical_ci": [a.lower() for a in wong_impl] == [b.lower() for b in nature_wong],
        "deepseek_palette": grab("PALETTE"),
        "default_dpi_line": (re.search(r"args\.get\(\"dpi\",\s*(\d+)\)", src) or [None, None])[1],
        "rcparam_figure_dpi": (re.search(r"\"figure\.dpi\":\s*(\d+)", src) or [None, None])[1],
        "red_green_pairs_in_deepseek": _rg_pairs(grab("PALETTE")),
        "red_green_pairs_in_wong": _rg_pairs(wong_impl),
    }

    # ── 载荷：两个口径（部署副本 = 运行时实际加载的那部分；整仓库 = 含 docs/README）──
    DEPLOY_EXCLUDE = {".gitignore", "LICENSE", "README.md", "docs"}
    deploy, whole = [], []
    for p in ROOT.rglob("*"):
        if not p.is_file() or ".git" in p.parts or p.suffix in (".pyc", ".pyo", ".bak"):
            continue
        if "__pycache__" in p.parts or ".scratch" in p.parts:
            continue
        rel = p.relative_to(ROOT)
        whole.append(p)
        if rel.parts[0] not in DEPLOY_EXCLUDE:
            deploy.append(p)

    def area_breakdown(paths):
        by = {}
        for p in paths:
            rel = p.relative_to(ROOT)
            area = rel.parts[0] if len(rel.parts) > 1 else "(top-level files)"
            by.setdefault(area, {"files": 0, "bytes": 0})
            by[area]["files"] += 1
            by[area]["bytes"] += p.stat().st_size
        return dict(sorted(by.items(), key=lambda kv: -kv[1]["bytes"]))

    payload = {
        "deploy": {"files": len(deploy), "bytes": sum(p.stat().st_size for p in deploy),
                   "by_area": area_breakdown(deploy)},
        "whole_repo": {"files": len(whole), "bytes": sum(p.stat().st_size for p in whole),
                       "by_area": area_breakdown(whole)},
    }
    payload["deploy"]["sum_check"] = sum(v["bytes"] for v in payload["deploy"]["by_area"].values())
    payload["whole_repo"]["sum_check"] = sum(v["bytes"] for v in payload["whole_repo"]["by_area"].values())

    # ── 提交级载荷（口径：git blob 字节，LF；工作区因 CRLF 会略大，两者不可混用）──
    EXCL = {".gitignore", "LICENSE", "README.md", "docs"}

    def git_dep(rev: str):
        out = subprocess.run(["git", "ls-tree", "-r", "-l", "-z", rev], cwd=str(ROOT),
                             capture_output=True, text=True).stdout
        files = []
        for rec in out.split("\0"):
            if not rec.strip():
                continue
            meta, path = rec.split("\t", 1)
            size = int(meta.split()[3])
            if path.split("/")[0] in EXCL:
                continue
            files.append((path, size))
        return {"rev": rev, "files": len(files), "bytes": sum(s for _, s in files),
                "paths": [p for p, _ in files], "sizes": dict(files)}

    payload_git = {}
    for label, rev in (("before_nature_commit", "792ec91^"),
                       ("at_nature_commit", "792ec91"),
                       ("head", "HEAD")):
        try:
            payload_git[label] = git_dep(rev)
        except Exception as exc:                                    # noqa: BLE001
            payload_git[label] = {"rev": rev, "error": str(exc)}
    b, a = payload_git["before_nature_commit"], payload_git["at_nature_commit"]
    if "bytes" in b and "bytes" in a:
        payload_git["delta"] = {
            "files": a["files"] - b["files"],
            "bytes": a["bytes"] - b["bytes"],
            "pct": round((a["bytes"] - b["bytes"]) / b["bytes"] * 100, 3),
            "files_touched": [p for p in a["paths"] if p in b["paths"] and a["sizes"][p] != b["sizes"][p]],
        }
    h = payload_git["head"]
    if "bytes" in b and "bytes" in h:
        # 与当前 HEAD 比：文件集合完全相同，只有内容变化，是本案例最干净的载荷差
        payload_git["delta_head"] = {
            "files": h["files"] - b["files"],
            "bytes": h["bytes"] - b["bytes"],
            "pct": round((h["bytes"] - b["bytes"]) / b["bytes"] * 100, 3),
            "only_in_head": sorted(set(h["paths"]) - set(b["paths"])),
            "only_in_before": sorted(set(b["paths"]) - set(h["paths"])),
        }

    # ── 语料触发测试：把 20 篇取证里真实的 caption 段拼成一份稿，G13/G14 会响吗 ──
    corpus_trigger = {"note": "G13/G14 是前瞻性门禁：它们只在稿件报告了误差/重复时才生效"}
    for label, path in (("ds_corpus_evidence", ROOT / "registry/ds-corpus-evidence.md"),
                        ("selfhost_paper", BASE)):
        t = path.read_text(encoding="utf-8")
        r = run_lint(t, name=f"_trig-{label}")
        corpus_trigger[label] = {"file": path.name, "g13_pass": gates(r)["G13"],
                                 "g14_pass": gates(r)["G14"],
                                 "has_error_semantics": bool(re.search(r"\u00b1|error bar", t, re.I))}

    # ── 确定性：同一套探针跑 5 遍，门禁结论是否逐字相同（G13/G14 要报 n）──
    rep = []
    for k in range(5):
        r = run_lint(base, name=f"_rep{k}")
        rep.append({"failed": r["failed"], "gates": {g["id"]: g["pass"] for g in r["gates"]},
                    "chars": len(base)})
    counts = [sum(1 for v in x["gates"].values() if v) for x in rep]
    mean = sum(counts) / len(counts)
    sd = (sum((c - mean) ** 2 for c in counts) / (len(counts) - 1)) ** 0.5
    identical = all(x["gates"] == rep[0]["gates"] for x in rep)
    determinism = {
        "runs": len(rep), "gates_total": len(rep[0]["gates"]),
        "counts": counts, "mean": round(mean, 4), "sd": round(sd, 6),
        "identical_verdicts": identical,
        "note": "同一份稿件在同一版本上重复评分；s.d. = 0 表示门禁是确定性的，不是采样估计",
    }

    # ── 源仓库 ↔ 部署副本一致性（部署副本才是运行时加载的那份）─────────
    import hashlib
    DEPLOY = Path("D:/ZH/vibe code/skills/tool/rsi-agent/skills/deepseek-paper")

    def _walk(root: Path):
        out = {}
        for p in root.rglob("*"):
            if not p.is_file() or ".git" in p.parts:
                continue
            rel = p.relative_to(root).as_posix()
            if rel.split("/")[0] in DEPLOY_EXCLUDE or p.suffix in (".pyc", ".pyo", ".bak"):
                continue
            if "__pycache__" in p.parts or ".scratch" in p.parts:
                continue
            raw = p.read_bytes().lstrip(b"\xef\xbb\xbf").replace(b"\r\n", b"\n")
            out[rel] = hashlib.md5(raw).hexdigest()
        return out
    src_h, dst_h = _walk(ROOT), _walk(DEPLOY) if DEPLOY.is_dir() else {}
    sync = {
        "deploy_dir": str(DEPLOY), "available": DEPLOY.is_dir(),
        "files_source": len(src_h), "files_deploy": len(dst_h),
        "only_in_source": sorted(set(src_h) - set(dst_h)),
        "only_in_deploy": sorted(set(dst_h) - set(src_h)),
        "content_differs": sorted(r for r in set(src_h) & set(dst_h) if src_h[r] != dst_h[r]),
    }
    sync["identical"] = (sync["available"] and not sync["only_in_source"]
                         and not sync["only_in_deploy"] and not sync["content_differs"])

    out = {
        "probes": probes,
        "gate_summary": {
            "total_probes": len(probes),
            "g13_correct": sum(1 for p in probes if p["g13_ok"]),
            "g14_correct": sum(1 for p in probes if p["g14_ok"]),
            "both_correct": sum(1 for p in probes if p["g13_ok"] and p["g14_ok"]),
            "false_negatives_g13": [p["probe"] for p in probes
                                    if p["g13_expected_pass"] is False and p["g13_pass"]],
            "false_positives_g13": [p["probe"] for p in probes
                                    if p["g13_expected_pass"] is True and not p["g13_pass"]],
            "false_negatives_g14": [p["probe"] for p in probes
                                    if p["g14_expected_pass"] is False and p["g14_pass"]],
            "false_positives_g14": [p["probe"] for p in probes
                                    if p["g14_expected_pass"] is True and not p["g14_pass"]],
        },
        "corpus": corpus_stats,
        "nature_extract": nat_stats,
        "render": render,
        "palette": palette,
        "payload": payload,
        "payload_git": payload_git,
        "corpus_trigger": corpus_trigger,
        "determinism": determinism,
        "sync": sync,
    }
    dest = DATA / "measurements.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def _rg_pairs(colors: list[str]) -> int:
    """数色板里同时存在的「偏红」与「偏绿」色对（Nature 明令避免）。"""
    def kind(h):
        h = h.lstrip("#")
        if len(h) != 6:
            return None
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        if r > 120 and r > g + 50 and r > b + 40:
            return "red"
        if g > 100 and g > r + 40 and g > b + 30:
            return "green"
        return None
    ks = [kind(c) for c in colors]
    return ks.count("red") * ks.count("green")


if __name__ == "__main__":
    raise SystemExit(main())
