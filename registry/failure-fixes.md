# failure-fixes — deepseek-paper

> 每条必须带 case_id（对应 evals/cases.jsonl）。

| case_id | 现象 | 根因 | 改法 | 是否生效 |
|---|---|---|---|---|
| c2 | 单次单 benchmark 就写「显著优于所有基线」 | 主张强度未与证据强度绑定 | 03 §3.1 动词表 + 04 §4.5 强度分级；`outperforms` 类入 G12 账本交叉 | 已生效（lint G12 可拦） |
| c4 | 把 PLAN.md 当结果、把 commit 当「更好」的证据 | 未区分计划/实施/测量 | 04 §4.1 输入分级表；evidence_scan 把全部条目置 todo | 已生效 |
| c3 | 项目顺利时编造消融与失败 | 把「像论文」理解成「必须有难点」 | 五条挖掘线穷尽后允许降级主张（写设计选择与成本账），不虚构 | 已生效（写入 SKILL 纪律 1） |
| c6 | 手写表里数字与正文不一致 | 数字两处手抄 | 05 §5.5 强制走 templates/05-图表数据.json → paper_table 生成 | 已生效 |
| c7 | 工具能跑但结果全绿（假阳性） | lint 缺负例校验 | 用 .scratch 坏稿回归，G1–G11 全 FAIL，确认可拦 | 已生效 |
