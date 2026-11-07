# -*- coding: utf-8 -*-
"""复现自举案例的故障注入测量：生成 4 个单缺陷变体并逐一跑 paper_lint。

在仓库根目录运行：
    python docs/case-selfhost/reproduce.py

输出：docs/case-selfhost/data/measurements.json（论文表 2 / 表 4 的数字来源）。
每条注入都断言「确实改动了文本」，否则抛错——静默不生效会让测量结论变成假的。
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # 仓库根
CASE = ROOT / "docs/case-selfhost"
PAPER = CASE / "04-论文.md"
LEDGER = CASE / "02-证据账本.json"
VAR = CASE / "variants"
LINT = ROOT / "tools/paper_lint.py"

# 朴素对照稿：无工序、无账本、措辞合规但数字虚构
NAIVE = """# PaperPipe: A Framework for Academic Writing

## Abstract

In this paper, we propose a novel framework that achieves state-of-the-art results for
academic writing. Our framework is very effective and much better than existing baselines.
The author believes it will be widely adopted.

## 1 Introduction

Writing papers is important. Many people struggle with it. It is well known that prompting helps.

## 2 Related Work

There are many works on writing assistants. Chen et al. proposed a summarization tool.

## 3 Method

Our method has three modules: template, prompt, and check. The details are presented in Figure 1.

## 4 Experiments

Table 1 shows the results. Our method is much better than baselines.

Table 1: Comparison among PaperPipe and baselines.

| Model | Score |
|---|---|
| Baseline-A | 71.2 |
| PaperPipe | 88.4 |

## 5 Conclusion

We proposed a novel framework for academic writing. It works very well.
"""


def run_lint(path: Path, genre: str = "M", ledger: Path | None = None) -> dict:
    args = {"path": str(path), "genre": genre}
    if ledger:
        args["ledger"] = str(ledger)
    p = subprocess.run([sys.executable, str(LINT)], input=json.dumps({"args": args}),
                       capture_output=True, text=True, encoding="utf-8")
    if not p.stdout.strip():
        raise SystemExit(f"paper_lint 无输出：{p.stderr}")
    return json.loads(p.stdout)["result"]


def must_change(before: str, after: str, name: str) -> str:
    if before == after:
        raise SystemExit(f"注入未生效：{name} —— 锚点文本已不存在，请先更新变体定义")
    return after


def main() -> int:
    text = PAPER.read_text(encoding="utf-8")
    VAR.mkdir(parents=True, exist_ok=True)

    # N2：摘要里所有「N on GateLint」的分数去掉
    head, sep, tail = text.partition("## 1 Introduction")
    edits = {"N2-no-numbers": must_change(
        head, re.sub(r"\d+(?:\.\d+)?\s+on GateLint", "no score on GateLint", head), "N2") + sep + tail}

    # N3：删掉正文对 Figure 1 的引用句（图仍在 → G11 应报 orphan）
    n3 = text.replace(
        "Figure 1 presents the same measurement as a bar chart, which makes the isolation property\n"
        "visible at a glance: the distance between the compliant draft and a caught fault is exactly one\n"
        "gate, while the distance to the naive control is ten. As illustrated, the gates behave as\n"
        "independent detectors rather than as a single aggregate score, and the one bar that does not\n"
        "drop is the one defect the checker cannot see.",
        "The per-draft gate counts are reported above and we do not repeat them here.")
    edits["N3-orphan-figure"] = must_change(text, n3, "N3")

    # N5：图 caption 缩成一句（→ G8 应报短 caption）
    n5 = re.sub(r"^\*\*Figure 1:.*?\*\*$",
                "**Figure 1: Gate counts across six drafts.**", text, count=1, flags=re.M)
    edits["N5-short-caption"] = must_change(text, n5, "N5")

    # N4：插入无账本支撑的比较级断言（→ 期望 G12 拦下，实测未拦）
    n4 = text.replace(
        "As illustrated, the gates behave as\nindependent detectors rather than as a single aggregate score,",
        "As illustrated, our gates clearly outperform every checklist-based reviewer we have tried,")
    edits["N4-unbacked-claim"] = must_change(text, n4, "N4")

    naive_path = VAR / "naive-control.md"
    naive_path.write_text(NAIVE, encoding="utf-8")

    rows = [("Compliant", run_lint(PAPER, ledger=LEDGER), "none")]
    for name, body in edits.items():
        p = VAR / f"{name}.md"
        p.write_text(body, encoding="utf-8")
        rows.append((name, run_lint(p, ledger=LEDGER), name))
    rows.append(("Naive control", run_lint(naive_path, "T"), "unwritten provenance"))

    out = []
    for name, r, defect in rows:
        npass = sum(1 for g in r["gates"] if g["pass"])
        out.append({"draft": name, "passed": npass, "failed": 12 - npass,
                    "verdict": r["verdict"], "failed_gates": r["failed"], "defect": defect})
    dest = CASE / "data/measurements.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
