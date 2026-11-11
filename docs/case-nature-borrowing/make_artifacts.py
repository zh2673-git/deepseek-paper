# -*- coding: utf-8 -*-
"""用本技能的两个渲染工具产出论文的图表（禁止手抄数字）。

运行：python docs/case-nature-borrowing/make_artifacts.py
产出：figures/fig1-agreement.png、tables/*.tex，并把 markdown 表写进 stdout 供粘贴。
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "docs/case-nature-borrowing"
DATA = CASE / "data"
TABLES = CASE / "tables"
FIGS = CASE / "figures"


def table(name: str) -> str:
    p = subprocess.run([sys.executable, str(ROOT / "tools/paper_table.py")],
                       input=json.dumps({"args": {"data": str(DATA / f"{name}.json"),
                                                  "out": str(TABLES / f"{name}.tex")}}),
                       capture_output=True, text=True, encoding="utf-8")
    r = json.loads(p.stdout)
    if not r.get("ok"):
        raise SystemExit(f"{name}: {r}")
    return r["result"]["markdown"]


def figure(name: str) -> dict:
    p = subprocess.run([sys.executable, str(ROOT / "tools/paper_figure.py")],
                       input=json.dumps({"args": {"data": str(DATA / f"{name}.json"),
                                                  "out": str(FIGS / f"{name}.png")}}),
                       capture_output=True, text=True, encoding="utf-8")
    r = json.loads(p.stdout)
    if not r.get("ok"):
        raise SystemExit(f"{name}: {r}")
    return r["result"]


def main() -> int:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    out = {}
    for t in ("tab-nature-groups", "tab-probes", "tab-rules", "tab-payload"):
        out[t] = table(t)
    fi = figure("fig1-agreement")
    print(json.dumps({"figure": fi, "tables": list(out)}, ensure_ascii=False, indent=1))
    print("\n--- markdown tables (paste into 04-论文.md) ---")
    for name, md in out.items():
        print(f"\n### {name}\n{md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
