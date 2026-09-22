# history-controller（mercado）— 未生成/未执行接口说明

本任务范围内共 26 个接口，14 个生成并执行了 case（见 `task-2026-09-14-11-44-23/`，30 cases 全部 PASS，连跑 2 次均 30/30），
以下 12 个接口按各自原因不生成 case、不执行，记录判断依据。

mercado 平台整体 ES 流量明显薄于 doordash（QA 测试账号自身流量约 58 次/180d 量级），本次对每个"0 流量"结论均执行了
90d→180d 两级核实，对 7 个 `{ruleExecutionLogId}`/`{ruleId}`/`{tableName}` 路径参数接口额外使用 `es_helper.py wildcard-agg`
按解析后真实路径核实，避免 `urlReferrer` 字面量精确匹配导致的假阴性。

## 1. 运维/管理类高风险操作（无论 ES 流量如何，强制不执行）

### POST /history/archiveOldLogsTask
- Swagger：无 requestBody（空 POST），响应 `{code, msg, data:integer}`（归档条数）。
- 风险判断：批量归档全平台旧执行日志的运维/定时任务接口，无 clientId/profileId/dateRange 等范围限定参数，一旦调用影响全平台历史数据。
- ES 流量：近90天、近180天（全平台，排除 clientId 62/3186）均为 **0 次调用**。
- 结论：不生成 case，不执行（与 target/doordash 平台处理一致）。

### GET /history/deleteHistoryData/{tableName}
- Swagger：path 参数 `tableName: string`（必填，自由字符串），无 requestBody，响应 `{code, msg, data}`。
- 风险判断：按原始表名物理删除历史数据，无客户/时间范围限定，属于无界爆炸半径的破坏性管理操作。
- ES 流量：`urlReferrer` 实际记录解析后的真实表名（如 `/history/deleteHistoryData/rule_snapshot_detail`），
  近90天全平台（排除测试账号）实际有 **6581 次调用**（其中 6491 次 `rule_snapshot_detail`、90 次
  `out_of_budget_campaign_message`），近180天 13151 次，说明是后台脚本化维护任务而非用户交互触发。
- 结论：不生成 case，不执行，即使真实调用频率很高也不例外（任务明确要求，与 doordash 平台处理一致）。

## 2. 写操作因缺少"账号自有真实数据"而不安全执行

### POST /setIgnored
### POST /setRemarks
- ES 流量：该接口 body 无 productLine 字段，视同 GET 用全平台流量判断，近90天分别为 1064 次、7 次，接口本身真实
  存在、Happy Path 场景清晰（setIgnored: operation=add 97.6%/remove 2.4%；setRemarks: 单一结构，7条样本clientId均为
  4267/4622 等真实生产客户）。
- 关键问题：这两个接口是**写操作**（修改 `ruleExecutionLogId` 对应记录的 ignore 状态/备注），任务要求写操作必须
  限定在 QA 账号自己的数据范围内。经核实：使用 mercado 测试账号 token 实际调用 `/getHistoryList`（宽日期范围
  2020-01-01~2026-09-14）与 `/getPendingList`（无过滤），两者均返回 `data.list: []`、`totalCount: 0`，即该账号在
  mercado 下**没有任何真实规则执行记录**，因此没有一个真正属于本账号的 `ruleExecutionLogId` 可用。
- ES 抽样得到的 setIgnored/setRemarks 请求全部来自 clientId 4267/4563/4622 等真实生产客户，若借用这些 ID 调用写接口，
  一旦服务端未按 clientId 严格校验记录归属，可能真实修改其他客户生产数据——与"绝不能污染非测试账号数据"的原则冲突，
  风险不可接受。
- 结论：不生成 case，不执行。待 mercado 测试账号下产生真实规则执行记录后可重新评估。
  （对比：本次同样受"账号无真实数据"影响的**只读**接口，如 getAdGroups/getCampaigns/getDetail/getProfiles 等，因为
  只是查询、不修改数据，实测对 foreign 执行日志返回 `code:200+data:[]/null`，无副作用风险，因此正常生成并执行，
  path 参数统一使用真实抽样值 `{{real_execution_log_id}}`。）

## 3. ES 无流量（真实业务性零调用，已按 90d/180d 两次核实，全平台口径）

以下接口 body 不含 productLine 字段（或 schema 虽含该字段但 ES 实测未见任何平台取值），因此按"视同 GET"规则使用
全平台流量判断，近90天和近180天（排除测试账号 clientId 62/3186）均为 **0 次调用**：

| 接口 | 90d | 180d |
|---|---|---|
| POST /changeSuggestionStatus | 0 | 0 |
| POST /getAdtomicSuggestions | 0 | 0 |
| POST /getAutoRuleDetailLog | 0 | 0 |
| POST /getAutoRuleDetailLogFilter | 0 | 0 |
| POST /getAutoRuleLogList | 0 | 0 |
| POST /getProducts/{ruleExecutionLogId} | 0 | 0 |
| POST /history/getLastPauseAsins/{ruleId} | 0 | 0 |

其中 getProducts/getLastPauseAsins 经 `wildcard-agg` 按解析后真实路径核实（避免路径模板字面量误判）：
- `/getProducts/*`：90d/180d 均只有 12 次调用，clientId 全部为 62/3186（测试账号），无任何真实客户调用。
- `/history/getLastPauseAsins/*`：90d/180d 均只有 12 次调用，clientId 全部为 62/3186（测试账号），无任何真实客户调用。

结论：以上 7 个接口不生成 case，不执行。

## 4. ES 无流量（mercado 平台专属零调用）

### POST /history/getRuleAlertDetail
- 该接口 requestBody **含 `productLine` 字段**（已核实 swagger schema 及 ES `productline-agg`），因此按任务要求需按
  mercado 专属流量判断，不能视同 GET 用全平台流量。
- 全平台近90天流量为 338 次（amazon 319 次、instacart 6 次、walmart 1 次，说明接口本身在其他平台被使用），但按
  `body.productLine.keyword:mercado` 过滤后，近90天、近180天均为 **0 次调用**。
- 结论：mercado 平台下该接口无真实流量，不生成 case，不执行。

## 方法论说明

- 对 7 个 `{ruleExecutionLogId}`/`{ruleId}`/`{tableName}` 路径参数接口（getAdGroups/getCampaigns/getCampaignTags/
  getDetail/getLineItems/getProducts/history-export/pending-export/history-getLastPauseAsins/deleteHistoryData）
  均使用 `es_helper.py wildcard-agg` 按解析后真实路径核实流量，避免 `urlReferrer` 字面量精确匹配导致的假阴性。
  其中 getLineItems、history/getRuleDeadDetail 近90天仅测试账号流量，但近180天分别发现 36 次、4 次真实(非测试账号)
  调用，样本虽小但为真实业务流量，仍按 Happy Path 生成 case 并在 description 中如实注明"样本较少"。
- history/export、pending/export 的 `exportHeaders`（导出列）字段在 ES 中高度分散，属于用户自定义列选择的变体、
  非独立业务路径，两接口均只覆盖占比最高的 2 种代表性报表维度（与 doordash 平台处理口径一致），其余维度
  （Targeting 等）在 case description 中注明为同类变体、不逐一生成 case。
- getDetail 接口流量充足（近90天 18288 次），为提高场景占比统计的可靠性，将抽样从初始 15 个执行日志（165条）
  扩大到 60 个执行日志（780条），扩大后 7 种 applyStatusList 组合占比均 ≥1%（0.6%的第8种组合已排除），
  按"占比≥1%场景全部覆盖、不合并"规则生成 7 个 Happy Path case。
