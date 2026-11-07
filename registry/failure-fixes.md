# failure-fixes — deepseek-paper

> 每条必须带 case_id（对应 evals/cases.jsonl）。

| case_id | 现象 | 根因 | 改法 | 是否生效 |
|---|---|---|---|---|
| c2 | 单次单 benchmark 就写「显著优于所有基线」 | 主张强度未与证据强度绑定 | 03 §3.1 动词表 + 04 §4.5 强度分级；`outperforms` 类入 G12 账本交叉 | 已生效（lint G12 可拦） |
| c4 | 把 PLAN.md 当结果、把 commit 当「更好」的证据 | 未区分计划/实施/测量 | 04 §4.1 输入分级表；evidence_scan 把全部条目置 todo | 已生效 |
| c3 | 项目顺利时编造消融与失败 | 把「像论文」理解成「必须有难点」 | 五条挖掘线穷尽后允许降级主张（写设计选择与成本账），不虚构 | 已生效（写入 SKILL 纪律 1） |
| c6 | 手写表里数字与正文不一致 | 数字两处手抄 | 05 §5.5 强制走 templates/05-图表数据.json → paper_table 生成 | 已生效 |
| c7 | 工具能跑但结果全绿（假阳性） | lint 缺负例校验 | 用 .scratch 坏稿回归，G1–G11 全 FAIL，确认可拦 | 已生效 |
| c8 | 4 列表 `Draft \| Gates \| Verdict \| Defect` 里，`Gates failed` 列的最高值被加粗，等于把最差档标成最好 | `paper_table` 硬编码 `data_start = start + 2`，假定必有「类别列 + benchmark 列」，标签列少一列时数据列整体左移一列；mixed-direction 列（越低越好）也无从声明 | 加 `data_start` 显式覆盖（默认行为不变），并在 templates/05 写明何时必须给；同时把「同表内不混放相反方向的指标」写成 caption 纪律 | 已生效（本篇表 2 拆掉 `Gates failed` 列后重测） |
| c9 | 故障注入脚本「改了但没改」：锚点文本随论文演化失效，`str.replace` 静默无变化，测量结论仍报旧值 | 脚本无断言 | 注入处加 `must_change()`，文本未变即 `SystemExit`；测量结果落 `data/measurements.json` 再从该文件抄数字 | 已生效（本篇 4 个变体均复跑确认） |
| c10 | `paper_table` 生成的 markdown 首行已是 `**Table: <caption>**`，再手动加 `**Table 2: ` 前缀会得到 `Table 2: Table: …` | 工具输出与正文编号职责混淆 | 正文装表时先剥掉工具首行的 `Table: ` 前缀再补编号 | 已生效 |
