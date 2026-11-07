# deepseek-paper

**把项目记录写成 DeepSeek 官方技术报告风格的论文。** 一条六道工序的生产线：先建证据账本，再挖研究点，再按 DeepSeek 的骨架/措辞/图表规范成稿，最后用硬门禁机检。

> 一句话原则：**证据先于主张，骨架先于措辞。** 不写「感觉像论文」的文章，只写每个数字都能被账本追到的技术报告。

## 它解决什么问题

拿 LLM 写论文，失败模式高度固定：

| 失败模式 | 具体表现 | 本技能的处置 |
|---|---|---|
| 套话开场 | `In this paper, we propose a novel framework that achieves state-of-the-art results.` | G10 禁用词零容忍（`novel` / 裸 SOTA / `to the best of our knowledge`） |
| 主张强于证据 | 单次单 benchmark 就写「显著优于所有基线」 | G12 比较级断言必须对到账本 `compare` 证据 |
| 无数字 | 「训练很快、成本很低」 | G3 强制 GPU hours + 数据量；G1 摘要 ≥2 处「分数 on benchmark」 |
| 手抄数字 | 表里和正文的数字对不上 | 图表一律由 `paper_table` / `paper_figure` 生成，不许手写 |
| 无失败申报 | 通篇只夸 | G9 至少 1 处失败/负面结果 + 成本口径澄清；M 类设 `Unsuccessful Attempts` 专节 |
| 体裁判错 | 技术报告里插独立 Related Work 章 | G7 三种体裁都不许单独设 Related Work |

## 六道工序（顺序不可跳）

| # | 工序 | 产出 | 判不过的信号 |
|---|---|---|---|
| 1 | 定体裁 | 体裁判定（T/M/A/S）+ 骨架清单 | 要报全账却选 M；设了独立 Related Work 却选 T |
| 2 | 建证据账本 | `evidence-ledger.json`（`evidence_scan` 出骨架，人补 claim/value/scope） | 正文有数字但账本 `status=todo` |
| 3 | 挖研究点 | 5 条挖掘线各轮一遍，每条写成 `<机制名>: <收益>` | 挖出 3 个以上「主研究点」（还在堆料） |
| 4 | 搭骨架 + 写 | 按 `references/02` 逐章填必写件 | 某章无证据 → 回工序 2 |
| 5 | 出图表 | `paper_table` / `paper_figure` 生成 | 图/表未被正文引用 |
| 6 | 机检 + 移交 | `paper_lint` G1–G12 全绿 + 评分 ≥14/20 | 有 FAIL 门禁 |

工序 3 的五条挖掘线（异常 / 取舍 / 复用 / 失败 / 成本）是本技能的判断核心：**一条线最多出一个主研究点**，写不成 `<机制名>: <收益>` 双段式小节名的，还不是研究点。

## 四种体裁

| 体裁 | 母版 | 用于 |
|---|---|---|
| T | DeepSeek-V3 | 技术报告：模型/系统全账（Architecture → Infrastructures → Pre-Training → Post-Training） |
| M | DeepSeek-R1 | 方法论文：一个机制讲透，第 2 章按实验演进组织，必备 `Unsuccessful Attempts` |
| A | DeepSeek-Coder | 应用/领域论文 |
| S | DeepSeek-Math | 短报告 |

20 篇 DeepSeek 论文的骨架/措辞/图表取证（含原文引文与出处）在 `registry/ds-corpus-evidence.md`。

## 为什么是这条流水线（设计依据）

本技能按「技能编译器」流程造出，两项设计依据单独落盘，可审计：

- `registry/skill-contract.md` —— 技能契约：本质 / 成熟度（A 为主判 + B 为风格层）/ 主算子（流水线，以及为什么不用角色制）/ 档位 / 六单元失败信号 / 理论→规则→校验信号 / 冲突裁决优先级 / 边界 / 六条自检。
- `registry/profession-map.md` —— 行业还原图：角色谱系（谁对什么质量负责）、工件链（谁交什么给谁 + 翻译损耗最大的一处）、裁决权、5 条真实反例、未验证假设清单。

一句话：它选择流水线而不是「作者—审稿人—编辑」角色制，是因为这类工作最怕**体裁随证据量反向选择**；而单 agent 扮审稿人不会打回自己的稿。

## 工具

四个工具统一 `stdin` 收 `{"args": {...}}`、`stdout` 回 `{"ok": true, "result": {...}}`：

```
evidence_scan   扫项目 → 账本骨架（全部 todo，等人判定）
paper_table     表数据 JSON → booktabs LaTeX + Markdown（best 加粗 / second 下划线 / 同档容差）
paper_figure    图数据 JSON → PNG/SVG/PDF（三线网格 + 单一强调色）
paper_lint      明文 → G1–G12 门禁报告 + 排版指纹
```

图表数据格式见 `templates/05-图表数据.json`。**表里的数字禁止手抄**——先落 JSON，再生成。

```bash
echo '{"args":{"path":"04-论文.md","genre":"M","ledger":"02-证据账本.json"}}' | python tools/paper_lint.py
```

`paper_figure` 需要 `matplotlib`；`paper_table` / `paper_lint` / `evidence_scan` 仅用标准库。

## 安装

把本仓库放进 agent 的 skills 目录：

```bash
git clone https://github.com/zh2673-git/deepseek-paper.git <agent-root>/skills/deepseek-paper
```

支持 skill 目录扫描的宿主（rsi-agent 等）下一轮即可见；也可直接把 `SKILL.md` 交给任意 LLM 当写作协议用。

## 输出约定

```
outputs/<论文名>/
  01-素材卡.md
  02-证据账本.json
  03-大纲.md
  04-论文.md
  04-论文-zh.md    # 可选：中文阅读版（非投稿版）
  figures/
  tables/
  lint-report.json
```

## 目录

```
SKILL.md                     技能主协议（六道工序 + 硬纪律 + 验收）
references/01-语料与体裁.md   20 篇谱系 + 体裁判定
references/02-章节骨架.md     每章必写件 + M 类改装 + 结论三段式
references/03-措辞指纹.md     动词表 / 句式 / 禁用清单
references/04-证据与主张.md   账本字段 / 挖掘线 / 主张强度分级
references/05-图表规范.md     三线表 / caption 三件套 / 视觉惯例
references/06-质检与反例.md   G1–G12 门禁 + S1–S10 评分 + 反例
templates/                   素材卡 / 账本 / 摘要填空 / 贡献与结论填空 / 图表数据
tools/                       四个工具
evals/                       案例集 + rubric + 评测结果
registry/                    技能契约 / 行业还原图 / DeepSeek 语料取证 / 范例 / 失败修复台账
docs/case-selfhost/          自举案例：用本技能写本技能（英文版 + 中文阅读版 + 复现脚本）
```

## 验收标准

- `paper_lint` G1–G12 全绿，或余项在 `lint-report.json` 写明理由并经用户确认；
- `references/06-质检与反例.md` 评分项 ≥14/20（机检全绿 ≠ 可交，仍需人工打分）；
- 正文每个数字能追到账本 `status: ok` 的条目，`outperforms` 类断言 100% 有 `compare` 证据；
- 摘要 / 贡献组 / 结论三段式三处数字一致；
- 图表由工具生成且每张被正文引用；
- 至少 1 条失败尝试带机制解释。

## 版本

`0.1.0` — 六道工序、G1–G12 门禁、4 个工具、4 种体裁、11 个评测案例（10 已判定 / 1 待 judge）、失败修复台账 11 条、技能契约与行业还原图各 1 份、自举案例 1 篇（含中文阅读版）。

## 验证状态

**partial（部分验证）**。自检（11 案例 / pass_rate 1.00）、同行（自举实跑一次）、门禁正负例回归均已做；**缺外部信号**——风格相似度尚无真实投稿/盲评反馈，故不得表述为「风格已验证」。

## License

MIT
