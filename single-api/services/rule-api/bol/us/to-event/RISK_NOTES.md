# to-event (bol, us) — 未生成/未执行接口说明

生成时间：2026-09-14

本模块 5 个接口中，2 个（`getRuleDefinition`、`getRuleTypes`）已生成 case 并执行通过（详见
task-2026-09-14-11-30-00/cases.json + report.json，3 条 case 全部 PASS，其中 `getRuleDefinition`
覆盖单ruleId查询与批量ruleIds查询两个场景）。以下 3 个接口未生成 case、未执行，原因均为 ES 无
真实流量。

## ES 无流量接口（3 个）

| 接口 | 排除测试账号后的真实流量 | 说明 |
|---|---|---|
| POST /event/getRuleCountByCampaignIds | 0（该接口body携带productLine字段，productline-agg显示近90天全平台仅 amazon 15次/tiktok 2次，无bol；用 `--platform bolv2` 精确过滤 [180天,含测试账号] 命中0次） | bol 平台在真实分平台流量中完全缺席 |
| POST /event/getRuleCountByUserIds | 0（同上，productline-agg显示近90天全平台仅 amazon/walmart/instacart/criteo/target/tiktok 六个平台有真实流量，无bol；用 `--platform bolv2` 精确过滤 [180天,含测试账号] 命中0次） | 同上 |
| POST /event/clearCacheTypes | 0（该接口ES无productLine字段，属于全平台基线接口；近180天全平台原始总命中仅5次，samples排除clientId 62/3186后为0，即5次全部来自内部测试账号自身产生的流量，无真实客户调用记录） | 全平台维度上都无真实客户流量，非仅bol平台问题 |

## 结论

以上 3 个接口本次均未生成 cases.json、未执行。其中前 2 个是可按平台归因的接口，bol 在真实
分平台流量中完全缺席；`clearCacheTypes` 是全平台无客户真实流量（仅测试账号流量）。其余 2 个
接口已生成 3 条 case，全部 PASS。
