# -*- coding: utf-8 -*-
"""成本测量：本案例（docs/case-nature-borrowing 的构建过程）可精确复核的量。

刻意不做的事：**不把字符数换算成 tokens**。
理由与 case-selfhost 的 ev-010 相同——中英混排的 bytes→tokens 比例未标定，
而 stream 里的 input_tokens 是每轮累积上下文（同一段文本被重复计费），
两者相除得不到稳定系数。宁可少报一个数，也不报一个别人复核不出来的数。

能精确复核的量：
  - 0 GPU hours（全程无梯度训练，只有推理）
  - 物化进上下文的消息数 / 字符数（会话文件逐条累加）
  - 工具调用次数与分布（同文件里的 tool_calls）
  - 本论文与部署载荷的字节数（见 measurements.json）
运行：python docs/case-nature-borrowing/measure_cost.py
"""
import collections
import json
from pathlib import Path

RSI = Path("D:/ZH/vibe code/skills/tool/rsi-agent")
SESSION = RSI / "runtime/plugins/memory/data/sessions/main.json"
OUT = Path(__file__).resolve().parent / "data/cost.json"


def main() -> int:
    msgs = json.loads(SESSION.read_text(encoding="utf-8"))
    chars = sum(len(str(m.get("content") or "")) for m in msgs)
    roles = collections.Counter(m.get("role", "?") for m in msgs)
    tools = collections.Counter()
    calls = 0
    for m in msgs:
        for tc in (m.get("tool_calls") or []):
            calls += 1
            tools[tc.get("name") or (tc.get("function") or {}).get("name") or "?"] += 1

    rec = {
        "session_file": "runtime/plugins/memory/data/sessions/main.json",
        "messages": len(msgs),
        "roles": dict(roles),
        "context_chars": chars,
        "tool_calls": calls,
        "tool_distribution": dict(sorted(tools.items(), key=lambda kv: -kv[1])),
        "gpu_hours": 0,
        "tokens_reported": None,
        "tokens_not_reported_because": (
            "字符→token 的比值未标定；stream 的 input_tokens 是每轮累积上下文，"
            "与同一段文本重复相乘，得不到可复核的单一系数。同一纪律见 case-selfhost 的 ev-010"
            "（该条因口径不稳被 dropped）。本文只报第一案例已实测的 2.04M tokens 作为参照。"
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
