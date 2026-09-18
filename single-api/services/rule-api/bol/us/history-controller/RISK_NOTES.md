# history-controller (bol, us) — 未生成/未执行接口说明

生成时间：2026-09-14

本模块 26 个接口中，16 个已生成 case 并执行通过（详见 task-2026-09-14-11-30-00/cases.json +
report.json，22 条 case 全部 PASS；写操作 case `setIgnored`/`setRemarks` 已连跑 2 次
[report.json + report_run2_idempotency.json] 全部 PASS，验证幂等）。以下 10 个接口未生成 case，
未执行，原因分两类。

## 一、运维类高风险接口（2 个，无论 ES 流量如何都跳过，不生成 case、不执行）

### POST /history/archiveOldLogsTask

- 无 requestBody，无客户/时间范围限定参数，批量归档全平台旧执行日志的运维/定时任务接口，
  blast radius 不限定于单个客户。
- 判断依据与 kroger/citrus 等平台 RISK_NOTES 一致，不因平台不同而变化，直接复用结论。

### GET /history/deleteHistoryData/{tableName}

- 按原始表名物理删除历史数据，无客户/时间范围限定参数；历史上其它平台报告显示该接口近90天
  全平台真实调用量极高（citrus 报告记录 13140 次，含 `rule_snapshot_detail` 与
  `out_of_budget_campaign_message` 两个固定表名），符合后台定时任务特征而非用户交互功能。
- 即使 ES 显示真实流量很高，仍判定为不可在共享生产环境下由测试脚本触发的破坏性运维操作。

## 二、ES 无流量接口（8 个，真实客户流量为 0，按铁律不生成 case、不执行）

本次针对 bol 平台实测（clientId 排除 62/3186 后）：

| 接口 | 排除测试账号后的真实流量 | 说明 |
|---|---|---|
| POST /history/getRuleAlertDetail | 0（该接口body确实携带productLine字段，productline-agg显示近90天真实分平台流量仅 amazon 319次/instacart 6次/walmart 1次，bol 0次；用 `--platform bolv2` 精确过滤确认命中0） | 该接口与本模块其余"无productLine字段"接口不同，可按平台精确归因，bol在真实分平台流量中完全缺席 |
| POST /changeSuggestionStatus | 0（近180天全平台原始18次，samples排除62/3186后为0，即18次全部来自内部测试账号） | 写操作接口，无任何真实客户触发证据 |
| POST /getAdtomicSuggestions | 0（近180天全平台原始15次，排除测试账号后为0） | Adtomic建议子系统，无真实客户调用记录 |
| POST /getAutoRuleDetailLog | 0（近180天全平台原始97次，排除测试账号后为0） | Amazon专属"特殊规则"日志功能 |
| POST /getAutoRuleDetailLogFilter | 0（近180天全平台原始35次，排除测试账号后为0） | 同上 |
| POST /getAutoRuleLogList | 0（近180天全平台原始1375次，排除测试账号后为0） | 同上，且productline-agg显示唯一带平台标识的1次为kevel，无法证明是真实客户流量 |
| POST /getProducts/{ruleExecutionLogId} | 0（wildcard-agg按前缀探测 /getProducts/* 近180天全平台命中12次，排除测试账号后为0；未排除时12次全部为clientId=62/3186，其中6次即为共用fixture real_execution_log_id=45527218自身产生的测试流量） | 已用 wildcard-agg 正确处理路径参数，非字面量查询误判 |
| POST /history/getLastPauseAsins/{ruleId} | 0（wildcard-agg按前缀探测 /history/getLastPauseAsins/* 近180天全平台命中12次，排除测试账号后为0；未排除时12次全部为clientId=62/3186） | 同上 |

## 结论

以上 10 个接口本次均未生成 cases.json、未执行。2 个运维类接口按风险跳过（不论 ES 流量）；
8 个接口按"ES 无流量"铁律跳过。其余 16 个接口已生成 22 条 case，全部 PASS（含 2 次幂等重跑
验证）。

## 备注：新增 case 里使用的场景判断

- `getHistoryList` 在 bol 全平台基线下呈现 **3** 种真实场景（mode+ruleDefinitionId+ruleName
  下钻 41.4%、仅 ruleName 过滤 57.6%、无过滤 1.0%），均 ≥1%，与此前 citrus 报告的 2 场景划分
  不同（bol 抽样时点下 "无mode但有ruleName" 与 "无mode无ruleName" 两类都命中且各自 ≥1%），
  按当前抽样如实覆盖 3 个场景。
- `history/getRuleAlertCount` 新增 `dismissedRuleIds` 非空场景（1.2%，6/500），与 citrus 报告中
  "该字段出现时也是空数组、不构成独立场景"的结论不同——本次 bol 抽样中该字段确有非空真实规则ID
  取值，按 ≥1% 硬性规则单独成场景，使用 bol 账号自身真实规则 ID 占位（该 ID 真实存在，仅不保证
  一定处于 dismissed 状态，接口本身不校验）。
