# history-controller (citrus, us) — 未生成/未执行接口说明

生成时间：2026-09-14

本模块 26 个接口中，16 个已生成 case 并执行通过（详见 task-2026-09-14-10-00-00/cases.json + report.json，
20 条 case 全部 PASS，写操作 case 已连跑 2 次验证幂等）。以下 10 个接口未生成 case，原因分两类。

## 一、运维类高风险接口（2 个，无论 ES 流量如何都跳过，不生成 case、不执行）

### POST /history/archiveOldLogsTask

- **Swagger**：无 requestBody，响应 `BaseResponseInteger`（`data` 为归档条数的整数），无 summary/description。
- **ES 流量**：近 180 天全平台（排除 clientId 62/3186 测试账号）**真实调用 0 次**；未排除时的 5 次调用
  全部来自 clientId=3186（内部测试账号），非真实客户/前端触发。同时满足"ES 无流量"（真实客户侧）。
- **风险判断**：接口名和参数结构（无 clientId/profileId/dateRange 等任何范围限定参数）表明这是一个批量
  归档全平台旧执行日志的运维/定时任务接口，一旦调用会影响全平台历史数据，不限于当前 QA 测试账号。
- **结论**：不生成 case，不执行。

### GET /history/deleteHistoryData/{tableName}

- **Swagger**：实测拉取 `https://api.pacvue.com/rule-api/v3/api-docs` 确认：仅 1 个必填 path 参数
  `tableName:string`，无 query 参数、无 requestBody，响应 `BaseResponseObject`（无 summary/description，
  未提供任何"仅查询/预览/dry-run"的契约证据）。已按任务要求核实 GET verb 不能自动等同于只读——但 Swagger
  未给出与"删除"字面含义相矛盾的证据。
- **ES 流量**：近 90 天全平台（排除 clientId 62/3186）**真实调用 13140 次**，抽样确认 `tableName` 取值
  为 `rule_snapshot_detail`（98.6%，12960 次）和 `out_of_budget_campaign_message`（1.4%，180 次）两种
  真实值（此前其他平台报告仅记录了前者，本次核实还发现后者）。真实存在，非"ES 无流量"。
- **风险判断**：接口按调用方传入的表名物理操作历史数据，无客户/时间范围限定参数，一旦误传或权限校验缺失，
  可能影响整张表；调用频率极高（近90天13140次，约146次/天）与固定的两个表名组合，符合"后台定时维护任务"
  特征而非用户交互触发的功能，与其它平台（amazon/target/instacart/kroger/criteo）此前的风险判断结论一致。
- **结论**：即使 ES 显示真实流量很高，仍判定为不可在共享生产环境下由测试脚本触发的破坏性运维操作。不生成
  case，不执行。

## 二、ES 无流量接口（8 个，真实客户流量为 0，按铁律不生成 case、不执行）

以下接口在正确排除 clientId 62/3186（内部研发/测试账号）后，真实客户流量为 **0**：

| 接口 | 排除测试账号后的真实流量 | 说明 |
|---|---|---|
| POST /getAdtomicSuggestions | 0（近180天全平台原始14次，100%为clientId=62） | Adtomic建议子系统，无真实客户调用记录 |
| POST /getAutoRuleDetailLog | 0（近180天全平台原始93次，100%为clientId=62） | Amazon专属"特殊规则"日志功能，纠正此前"生成case掩盖0流量"的做法 |
| POST /getAutoRuleDetailLogFilter | 0（近180天全平台原始33次，100%为clientId=62） | 同上 |
| POST /getAutoRuleLogList | 0（近180天全平台原始1373次，几乎全部为clientId=62/3186历史测试调用；仅1条带productLine=kevel也无法排除是测试） | 之前平台(instacart)误判为"该接口ES近90天全平台0调用"仍生成case，本次严格核实是内部测试账号流量后判定为ES无流量 |
| POST /changeSuggestionStatus | 0（近180天全平台原始18次，100%为clientId=62，时间戳与近几日其它平台case执行时间吻合，确认为测试脚本自身产生的流量） | 写操作接口，无任何真实客户触发证据 |
| POST /getProducts/{ruleExecutionLogId} | 0（wildcard-agg按前缀探测，90天/180天排除测试账号后均为0；未排除时的12次全部为clientId=62/3186） | 已用 wildcard-agg 正确处理路径参数，非字面量查询误判 |
| POST /history/getLastPauseAsins/{ruleId} | 0（wildcard-agg按前缀探测，90天/180天排除测试账号后均为0；未排除时的12次全部为clientId=62/3186，其中6次即为共用fixture real_rule_id自身产生的测试流量） | 同上 |
| POST /history/getRuleAlertDetail | citrus专属0（该接口body携带productLine字段，近180天真实分平台流量为 amazon 701次/instacart 6次/walmart 1次，citrus 0次；用 `--platform citrus` 精确term过滤确认命中0） | 与本模块其余"无productLine字段"接口不同，该接口**确实**携带productLine且可按平台归因，citrus在真实分平台流量中完全缺席，按任务给定规则判定为该平台真实的"ES 无流量"，而非套用全平台兜底 |

**重要说明（与此前 target/kroger/instacart 平台报告的差异）**：本次严格执行"clientId 62/3186 排除"规则后发现，
此前部分平台（如 instacart）报告中所称的"该接口ES近90天全平台0调用"，实际上是指排除测试账号后的0调用，
但随后仍使用 Swagger 结构 + 真实 fixture ID 构造了 case 并执行——这在当时的任务要求下是被允许的。本次任务
要求更严格："ES 上查不到真实流量的接口，绝对不能生成 case，也不能执行"，因此这 8 个接口本次均未生成 case，
且额外发现 getAutoRuleLogList（此前 instacart 生成过 case 且 PASS）在严格排除测试账号后同样属于 ES 无流量。

## 结论

以上 10 个接口本次均未生成 cases.json、未执行。2 个运维类接口按风险跳过（不论 ES 流量）；8 个接口按
"ES 无流量"铁律跳过。其余 16 个接口已生成 20 条 case，全部 PASS（含 2 次幂等重跑验证）。
