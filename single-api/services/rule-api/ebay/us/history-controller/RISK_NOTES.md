# history-controller（ebay）— 未生成/未执行接口说明

本任务范围内共 26 个接口，14 个生成并执行了 case（见 `task-2026-09-14-14-22-18/`，29 cases 全部 PASS，连跑 2 次均 29/29），
以下 12 个接口按各自原因不生成 case、不执行，记录判断依据。

ebay 平台整体 ES 流量极薄（body.productLine.keyword:ebay 的可归因流量在 730 天内约仅 29 次），本次对每个"0 流量"结论
均执行了 90d→180d→730d 三级核实，对 10 个 `{ruleExecutionLogId}`/`{ruleId}`/`{tableName}` 路径参数接口额外使用
`es_helper.py wildcard-agg` 按解析后真实路径核实，避免 `urlReferrer` 字面量精确匹配导致的假阴性。

## 1. 运维/管理类高风险操作（无论 ES 流量如何，强制不执行）

### POST /history/archiveOldLogsTask
- Swagger：无 requestBody（空 POST），响应 `{code, msg, data:integer}`（归档条数）。
- 风险判断：批量归档全平台旧执行日志的运维/定时任务接口，无 clientId/profileId/dateRange 等范围限定参数，一旦调用影响全平台历史数据。
- ES 流量：近90天、近730天（全平台，排除 clientId 62/3186）均为 **0 次调用**。
- 结论：不生成 case，不执行（与 target/doordash/mercado 平台处理一致）。

### GET /history/deleteHistoryData/{tableName}
- Swagger：path 参数 `tableName: string`（必填，自由字符串），无 requestBody，响应 `{code, msg, data}`。
- 风险判断：按原始表名物理删除历史数据，无客户/时间范围限定，属于无界爆炸半径的破坏性管理操作。
- ES 流量：`urlReferrer` 实际记录解析后的真实表名，近90天全平台（排除测试账号）实际有 **6581 次调用**（其中
  6491 次 `rule_snapshot_detail`、90 次 `out_of_budget_campaign_message`），近730天 16458 次，说明是后台脚本化维护
  任务而非用户交互触发。
- 结论：不生成 case，不执行，即使真实调用频率很高也不例外（任务明确要求，与其余平台处理一致）。

## 2. 写操作因缺少"账号自有真实数据"而不安全执行

### POST /setIgnored
### POST /setRemarks
- ES 流量：该接口 body 无 productLine 字段，视同 GET 用全平台流量判断，近90天分别为 1064 次、7 次，接口本身真实
  存在、Happy Path 场景清晰（setIgnored: operation=add 97.4%/remove 2.6%；setRemarks: 单一结构，7条样本 clientId
  均为 4267/4622 等真实生产客户）。
- 关键问题：这两个接口是**写操作**（修改 `ruleExecutionLogId` 对应记录的 ignore 状态/备注），任务要求写操作必须
  限定在 QA 账号自己的数据范围内。经核实：使用 ebay 测试账号（client_id=62）token 实际调用 `/getHistoryList`
  （宽日期范围 2020-01-01~2026-09-14）与 `/getPendingList`（无过滤），两者均返回 `data.list: []`、`totalCount: 0`，
  即该账号在 ebay 下**没有任何真实规则执行记录**，因此没有一个真正属于本账号的 `ruleExecutionLogId` 可用。
- ES 抽样得到的 setIgnored/setRemarks 请求全部来自 clientId 3935/3076/4267/4622 等真实生产客户，若借用这些 ID 调用
  写接口，一旦服务端未按 clientId 严格校验记录归属，可能真实修改其他客户生产数据——与"绝不能污染非测试账号数据"
  的原则冲突，风险不可接受。
- 结论：不生成 case，不执行。待 ebay 测试账号下产生真实规则执行记录后可重新评估。
  （对比：本次同样受"账号无真实数据"影响的**只读**接口，如 getAdGroups/getCampaigns/getDetail/getProfiles 等，因为
  只是查询、不修改数据，实测对 foreign 执行日志返回 `code:200`（`data:null/[]`），无副作用风险，因此正常生成并
  执行，path 参数统一使用真实抽样值 `{{real_execution_log_id}}`。）

## 3. ES 无流量（真实业务性零调用，已按 90d/180d/730d 三次核实，全平台口径）

以下接口 body 不含 productLine 字段，因此按"视同 GET"规则使用全平台流量判断，近90天、近180天、近730天
（排除测试账号 clientId 62/3186）均为 **0 次调用**：

| 接口 | 90d | 180d | 730d |
|---|---|---|---|
| POST /changeSuggestionStatus | 0 | 0 | 0 |
| POST /getAdtomicSuggestions | 0 | 0 | 0 |
| POST /getAutoRuleDetailLog | 0 | 0 | 0 |
| POST /getAutoRuleDetailLogFilter | 0 | 0 | 0 |
| POST /getAutoRuleLogList | 0 | 0 | 0 |

结论：以上 5 个接口不生成 case，不执行。

### POST /getProducts/{ruleExecutionLogId}
### POST /history/getLastPauseAsins/{ruleId}
- 经 `wildcard-agg` 按解析后真实路径核实（避免路径模板字面量误判）：两接口 180d 与 730d 命中数完全相同
  （均为 12 次），说明全部流量集中在近期一个窗口内。逐条核实 clientId，**全部为 62/3186（测试账号）**，
  时间戳集中在 2026-09-10（其他平台会话调试本模块时产生的测试流量，非真实客户调用）。
- 结论：无真实客户流量，以上 2 个接口不生成 case，不执行。

## 4. ES 无流量（ebay 平台专属零调用）

### POST /history/getRuleAlertDetail
- 该接口 requestBody **含 `productLine` 字段**（已用 `productline-agg` 核实：730天全平台命中952次，
  分布为 amazon 930/instacart 6/walmart 1，无 ebay 桶），因此按任务要求需按 ebay 专属流量判断，不能视同 GET
  用全平台流量。
- 结论：ebay 平台下该接口无真实流量，不生成 case，不执行。

## 方法论说明

- 对 10 个 `{ruleExecutionLogId}`/`{ruleId}`/`{tableName}` 路径参数接口（getAdGroups/getCampaigns/getCampaignTags/
  getDetail/getLineItems/getProducts/history-export/pending-export/history-getLastPauseAsins/deleteHistoryData）
  均使用 `es_helper.py wildcard-agg` 按解析后真实路径核实流量，避免 `urlReferrer` 字面量精确匹配导致的假阴性。
  其中 getLineItems（33条真实样本）、history/export（5条）、pending/export（6条）样本量较小，case description 中
  已如实注明"样本量较小/很小，场景覆盖可能不全"。
- **real_execution_log_id 数据质量问题（本次新发现，已规避）**：最初选取全平台样本中命中数最高的执行日志 ID
  `36330975` 作为 `{{real_execution_log_id}}` 首次执行 case 时，`POST /getCampaigns/{id}`（无过滤场景）与
  `POST /history/export/{id}`（Budget Usage 场景）稳定失败（连续2次），报 `500 Internal Server Error`，根因是
  rule-api 在处理这两个接口时会调用平台专属的实体名称解析服务
  `http://ebay-provider/rule/entity/getCampaignNames` 为该执行日志下的真实 campaign 做名称回填，而该
  执行日志 `36330975` 关联的 campaign 实体在 ebay-provider 侧解析异常（可能是该执行日志本身不属于 ebay
  平台的历史遗留数据，ID 格式与 ebay-provider 期望的 schema 不匹配）。其余接口（getCampaignTags/getDetail/
  getAdGroups/getLineItems/getProfiles/queryRuleSnapshots）用同一 ID 均正常返回 `code:200`，说明并非该
  ID 全局不可用，而是这两个接口特有的下游名称回填逻辑触发了该 ID 的数据缺陷。逐一实测同一 500 样本池内其余
  6 个候选 ID（`39988549`/`36967865`/`39988546`/`36967864`/`36967863`/`39634784`）在 `getCampaigns` 上
  均返回干净的 `code:200`，最终改用 `39988549` 作为 `{{real_execution_log_id}}`（同样验证 getCampaignTags/
  getDetail/getAdGroups/getLineItems/getProfiles/export 类接口均正常返回 `code:200`/合法 xlsx 二进制），
  全部 29 cases 改用该 ID 后连跑 2 次均 29/29 PASS。
- history/export、pending/export 的 `exportHeaders`（导出列）字段在 ES 中高度分散，属于用户自定义列选择的变体、
  非独立业务路径，两接口均只覆盖占比最高的 2 种代表性报表维度（与 doordash/mercado 平台处理口径一致），其余
  维度不逐一生成 case。
