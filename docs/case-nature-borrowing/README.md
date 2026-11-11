# 案例二：把期刊的作者指南借进风格门禁

这是本仓库的**第二篇案例论文**，也是本技能的第二次端到端实测。
第一篇（`docs/case-selfhost/`）用本技能写本技能，验证的是「流水线能不能把一份项目记录写成技术报告」；
这一篇验证的是一个更窄也更难的问题：**当语料本身缺某一类信息时，门禁怎么办。**

## 一句话结论

从 20 篇语料归纳出来的门禁，**结构上**不可能要求语料里不存在的东西（取证摘录 45,524 字节里
error bar / ± / `n = N` / seed / s.d. / CI 的出现次数全是 0）；补这个盲区的唯一低成本来源是
一份**成文**的期刊规范，但它 42 条硬要求里只有 4 条能被机械判定，而借来的每一条都带代价。

## 成品

| 文件 | 内容 |
|---|---|
| `04-论文.md` | 正文（M 类方法论文，42,171 字符，`paper_lint` **G1–G14 全绿**） |
| `04-论文.html` | 单文件 HTML 交付版（图片 base64 内联、目录锚点、可 `Ctrl+P` 存 PDF） |
| `04-论文.docx` | A4 / 1.5 倍行距 / 页码 / 中文 eastAsia 字体的 Word 版 |
| `lint-report.json` | `verdict: PASS`，`failed: []` |
| `06-评分.md` | 人工评分 S1–S10 = 20/20，附「扣分风险评估」五条 |
| `01-素材卡.md` | 五条挖掘线逐线记录 + 体裁判定 + 四条关键取舍 |
| `02-证据账本.json` | 18 条证据（15 `measure` + 2 `compare`），全部 `status: ok` |
| `03-大纲.md` | M 类骨架逐项对照 + 有意偏离 3 条 + **不借清单** |
| `data/*.json` | 表与图的输入数据 + 实测结果（正文数字的唯一来源） |
| `figures/`、`tables/` | `paper_figure` / `paper_table` 生成物 |
| `reproduce.py` | 八个探针的生成、打分、确定性重复、载荷与同步核对 |
| `make_artifacts.py` | 图表重生成入口 |
| `measure_cost.py` | 成本测量（刻意不报 tokens，理由见脚本头） |

## 复现

```bash
# 1. 重跑八个探针 + 语料计数 + 载荷 + 同步核对（写 data/measurements.json）
python docs/case-nature-borrowing/reproduce.py

# 2. 重出图表（写 figures/ tables/，并把 markdown 表打到 stdout）
python docs/case-nature-borrowing/make_artifacts.py

# 3. 跑门禁
echo '{"args":{"path":"docs/case-nature-borrowing/04-论文.md","genre":"M","ledger":"docs/case-nature-borrowing/02-证据账本.json"}}' \
  | python tools/paper_lint.py

# 4. 出交付形态
echo '{"args":{"path":"docs/case-nature-borrowing/04-论文.md","out_html":"docs/case-nature-borrowing/04-论文.html","out_docx":"docs/case-nature-borrowing/04-论文.docx"}}' \
  | python tools/paper_render.py
```

## 关键数字（全部可复核）

| 指标 | 值 | 复核方式 |
|---|---|---|
| 语料里统计口径的出现次数 | 0（error bar / ± / n= / seed / s.d. / CI 各 0） | `data/measurements.json → corpus` |
| Nature 硬要求 → 采纳 | 42 → 4（8 组：A5 B6 C4 D5 E5 F5 G6 H6） | `→ nature_extract` |
| G13 与作者预期一致 | 7/8 | `→ gate_summary.g13_correct` |
| G14 与作者预期一致 | 8/8 | `→ gate_summary.g14_correct` |
| 唯一不一致 | P7：`CI` 被当成置信区间 → 假阳性 | `→ gate_summary.false_positives_g13` |
| 带账本时的总门禁数 | 14 / 13 / 12（P1、P6、P7 = 13；P3 = 12） | `→ probes[*].gates_passed_with_ledger` |
| 确定性 | 5 次重复逐条一致，s.d. = 0 | `→ determinism` |
| 借用提交的载荷 | +6,848 字节（+3.544%），105 加 / 8 删 | `→ payload_git.delta` |
| 与当前 HEAD 的载荷差 | +6,848 字节（+3.544%），文件数不变 | `→ payload_git.delta_head` |
| 源仓库 ↔ 部署副本 | 28 对 28，无差异 | `→ sync.identical` |
| 本案例自身门禁 | 14/14 PASS | `lint-report.json` |

> 两个字节口径不可混用：git blob 字节（LF 归一）用于提交对比，工作区字节（Windows CRLF）用于
> 「运行时加载多少」。论文 §3 与表 4 caption 双处声明了这件事。

## 这一篇暴露的、第一篇没暴露的问题

| # | 问题 | 为什么第一篇看不见 | 处置 |
|---|---|---|---|
| 1 | 两条新门禁是**计数式**而非绑定式：一处声明豁免所有误差棒（P5 实测通过） | 第一篇的 G12 也是计数式，但那已经作为已知缺陷申报，未意识到新门禁会**重犯同一个错** | 如实申报（§5.2），修法写明（绑到账本条目），本轮不改因为会动第一篇的基线 |
| 2 | G14 只读图注，表注漏检（P6 实测） | 第一篇只有图没有表 | 申报为「已知缺陷 + 已知修法」（§5.1 第二条） |
| 3 | `CI` 假阳性：`paper_lint` 里 `\bCI\b` 大小写不敏感匹配 | 第一篇的稿件里没有 CI 这个词 | 申报在 §4.2 / §5.2，摘要也写了 |
| 4 | `paper_figure` 的 `figure.dpi` 仍是 200，与 savefig 的 300 不一致 | 第一篇没测过渲染参数 | 申报在 §2.4 末 / §5.2 / §6 局限 |

## 这一篇的方法论产出（可复用到下一类改动）

1. **先测天花板再借规则**：在借外部规范之前，先数清自家语料在目标维度上是 0 还是非 0。
   0 意味着「再怎么读同一批语料也补不上」，这是结构性缺口，不是勤奋问题。
2. **准入测试要比规范本身更严**：42 条里 38 条被拒，拒的理由必须分三类（版面 / 不可机检的判断 / 与既有风格冲突），
   否则后来者会以为漏抄了。
3. **每条借来的规则都要配套探针**：正例（该红时红）、修复例（补上就绿）、盲区例（门禁看不见的地方）、
   假阳性例（不该红却红了）。四类各至少一条，缺哪类就说明哪类没测。
4. **「不响」不等于「通过」**：零统计的稿件也能全绿，所以必须有一条探针专门报告这个事实（P0 + §4.4 第一条）。
5. **代价要写进表里**：借来的每一条规则在落地表里都带一列 Cost，代价是定性的就写定性，能量化的量化（字节 / 行数 / 门禁计数分开放）。
