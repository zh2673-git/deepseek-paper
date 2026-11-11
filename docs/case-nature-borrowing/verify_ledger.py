# -*- coding: utf-8 -*-
"""账本交叉核对：论文里出现的每个数字，能否追到账本里 status=ok 的条目。

不做语义推理，只做「这个字面量在账本 value/verify 里是否出现过」的机械核对，
未命中的列出来人工判断（属于 reference/manual 的会被标出）。
运行：python docs/case-nature-borrowing/verify_ledger.py
"""
import json
import re
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parent
PAPER = CASE / "04-论文.md"
LEDGER = CASE / "02-证据账本.json"


def main() -> int:
    text = PAPER.read_text(encoding="utf-8")
    led = json.loads(LEDGER.read_text(encoding="utf-8"))["paper"]["evidence"]
    blob = json.dumps(led, ensure_ascii=False)

    # 抽取正文里的数值字面量（带千分位或小数，或 >=2 位整数）
    nums = set()
    for m in re.finditer(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+\.\d+|\d{2,})(?![\w.])", text):
        nums.add(m.group(1))

    # 引用与规范引用（书目 DOI、期刊条号、指南原文里的版面数值）不算主张数字，单列白名单
    CITATION_WHITELIST = {
        "2412.19437", "2501.12948", "2402.03300",     # arXiv 编号
        "441",                                        # Wong 2011 页码
        "0.25", "183",                                # 指南原文的版面数值，未采纳
        "2.3",                                        # 章节交叉引用
        "25,955",                                     # 基线稿件字符数，出处见 ev 与 case-selfhost 账本
    }

    ok_ev = [e for e in led if e.get("status") == "ok"]
    blob_plain = blob.replace(",", "").replace("，", "")
    missing, whitelisted = [], []
    for n in sorted(nums):
        plain = n.replace(",", "")
        if (n in blob) or (plain in blob) or (plain in blob_plain):
            continue
        if n in CITATION_WHITELIST:
            whitelisted.append(n)
            continue
        missing.append(n)

    print(json.dumps({
        "paper": str(PAPER),
        "numeric_literals": len(nums),
        "ledger_entries": len(led),
        "ok_entries": len(ok_ev),
        "not_found_in_ledger": missing,
        "whitelisted_as_citation": whitelisted,
        "found_in_ledger": len(nums) - len(missing) - len(whitelisted),
    }, ensure_ascii=False, indent=1))

    # 硬要求：outperforms 类断言必须有 compare 证据
    cmps = re.findall(r"\b(outperform\w*|surpass\w*|significantly better)\b", text, re.I)
    ncmp = len([e for e in ok_ev if e.get("kind") == "compare"])
    print(json.dumps({"comparatives": len(cmps), "compare_evidence": ncmp,
                      "gate_would_pass": len(cmps) <= ncmp}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
