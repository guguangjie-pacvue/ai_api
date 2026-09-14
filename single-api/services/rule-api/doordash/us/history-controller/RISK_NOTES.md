# history-controller（doordash）— 未生成/未执行接口说明

本任务范围内共 26 个接口，14 个生成并执行了 case（见 `task-2026-09-14-09-26-52/`，23 cases 全部 PASS），
以下 12 个接口按各自原因不生成 case、不执行，记录判断依据。

## 1. 运维/管理类高风险操作（无论 ES 流量如何，强制不执行）

### POST /history/archiveOldLogsTask
- Swagger：无 requestBody（空 POST），响应 `{code, msg, data:integer}`（归档条数）。
- 风险判断：批量归档全平台旧执行日志的运维/定时任务接口，无 clientId/profileId/dateRange 等范围限定参数，一旦调用影响全平台历史数据。
- ES 流量：近90天、近180天（全平台，排除 clientId 62/3186）均为 **0 次调用**。
- 结论：不生成 case，不执行（与 target 平台处理一致）。

### GET /history/deleteHistoryData/{tableName}
- Swagger：path 参数 `tableName: string`（必填，自由字符串），无 requestBody，响应 `{code, msg, data}`。
- 风险判断：按原始表名物理删除历史数据，无客户/时间范围限定，属于无界爆炸半径的破坏性管理操作。
- ES 流量：近90天全平台（排除测试账号）实际有 **6570 次调用**（`urlReferrer` 实际记录的是解析后的真实表名，如
  `/history/deleteHistoryData/rule_snapshot_detail`，而非路径模板字面量），近180天 13140 次，抽样 tableName
  均为 `rule_snapshot_detail`，说明是后台脚本化维护任务而非用户交互触发。
- 结论：不生成 case，不执行，即使真实调用频率很高也不例外（任务明确要求）。

## 2. 写操作因缺少"账号自有真实数据"而不安全执行（本次新增判断，与 target 平台情况不同）

### POST /setIgnored
### POST /setRemarks
- ES 流量：全平台近90天分别为 1058 次、7 次（该接口 body 无 productLine 字段，视同 GET 用全平台流量判断），
  接口本身真实存在、Happy Path 场景清晰（setIgnored: operation=add 98%+/remove 2%-；setRemarks: 100%单一结构）。
- 关键问题：这两个接口是**写操作**（修改 `ruleExecutionLogId` 对应记录的 ignore 状态/备注），任务要求写操作
  "必须能配对安全的可验证回滚，且严格限定在 QA 账号自己的数据范围内"。经核实，doordash 测试账号
  (`client_id=62`) 通过 `/getHistoryList`、`/getPendingList`、`/getPendingRuleNum` 查询（多种日期范围/无
  ownerIds 过滤）均返回**空结果**，即该账号在 doordash 下**没有任何真实规则执行记录**，因此没有一个真正属于
  本账号的 `ruleExecutionLogId` 可用。
- 若使用从 ES 抽样得到的、属于其他真实生产客户的 `ruleExecutionLogId` 去调用 `setIgnored`/`setRemarks`，
  由于这是写操作，一旦服务端未按 clientId 严格校验记录归属，可能真实修改其他客户生产数据的 ignore 状态/备注
  字段——这与"绝不能污染非测试账号数据"的原则冲突，风险不可接受。
- 结论：不生成 case，不执行。待 doordash 测试账号下产生真实规则执行记录后可重新评估。
  （对比：本次同样受"账号无真实数据"影响的**只读**接口，如 getAdGroups/getCampaigns/getProfiles 等，因为只是
  查询、不修改数据，借用 ES 真实抽样 ID 至多返回 `code:200 + data:null/[]`，无副作用风险，因此正常生成并执行。）

## 3. ES 无流量（真实业务性零调用，已按 90d/180d 两次核实）

以下接口该接口 body **不含 productLine 字段**，因此按"视同 GET"规则使用全平台流量判断，全平台近90天和近180天
（排除测试账号 clientId 62/3186）均为 **0 次调用**：

| 接口 | 90d | 180d |
|---|---|---|
| POST /changeSuggestionStatus | 0 | 0 |
| POST /getAdtomicSuggestions | 0 | 0 |
| POST /getAutoRuleDetailLog | 0 | 0 |
| POST /getAutoRuleDetailLogFilter | 0 | 0 |
| POST /getAutoRuleLogList | 0 | 0 |
| POST /getProducts/{ruleExecutionLogId} | 0 | 0 |
| POST /history/getLastPauseAsins/{ruleId} | 0 | 0 |

结论：以上 7 个接口不生成 case，不执行。

## 4. ES 无流量（doordash 平台专属零调用）

### POST /history/getRuleAlertDetail
- 该接口 requestBody **含 `productLine` 字段**（已核实 swagger schema），因此按任务要求需按 doordash 专属流量
  判断，不能视同 GET 用全平台流量。
- 全平台近90天流量为 285 次（说明接口本身在其他平台被使用），但按 `body.productLine.keyword:doordash` 过滤后，
  近90天、近180天均为 **0 次调用**。
- 结论：doordash 平台下该接口无真实流量，不生成 case，不执行。

## 方法论说明（本次相对 target 平台的修正）

在核实 ES 查询方法时发现：对于 `{ruleExecutionLogId}`/`{ruleId}`/`{tableName}` 等路径参数接口，`urlReferrer`
字段在 ES 中记录的是**解析后的真实路径值**（如 `/getCampaigns/43301077`），而非路径模板字面量
（如 `/getCampaigns/{ruleExecutionLogId}`）。此前按字面量做 `term` 精确匹配会对这类接口误判为"ES 无流量"。
本次改用 `wildcard` 匹配（如 `/getCampaigns/*`）重新核实后，发现 **getAdGroups / getCampaigns / getCampaignTags /
getDetail / getLineItems / history/export / pending/export** 等 7 个路径参数接口实际存在真实流量（此前在
target 平台的生成中被漏判为零流量、未覆盖），本次已按修正后的方法正确生成并执行 case。
