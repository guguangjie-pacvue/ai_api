# history-controller (kroger, us) — 未生成/未执行接口说明

生成时间：2026-09-11

本模块 26 个接口中，8 个通用查询类接口（`getHistoryList`/`getPendingList`/`getPendingRuleNum`/
`getProfiles`/`history/getRuleAlertCount`/`history/getRuleAlertDetail`/`history/getRuleDeadDetail`/
`queryRuleSnapshots`）已用 kroger 测试账号（client_id=62, header productline=krogerv3）验证并生成
case。以下 18 个接口未生成 case、未执行，原因分三类：

## 一、运维类高风险接口（2 个，无论 ES 流量如何都跳过）

- **POST /history/archiveOldLogsTask**：无 requestBody，无范围限定参数，批量归档全平台旧执行日志的
  运维/定时任务接口，blast radius 不限定于单个客户。
- **GET /history/deleteHistoryData/{tableName}**：按原始表名物理删除历史数据，无客户/时间范围限定，
  近 90 天全平台真实调用 6480+ 次但 `tableName` 全部为 `rule_snapshot_detail`，显示这是后台定时任务
  触发而非用户交互功能。

判断依据与 target 平台 RISK_NOTES.md 中记录的一致，不因平台不同而变化，直接复用结论。

## 二、需要真实 ruleExecutionLogId / ruleId，但 kroger 账号当前无任何真实数据（9 个）

实测确认：kroger 测试账号（client_id=62）当前在 `getHistoryList`/`getPendingList` 下返回的执行历史
和待处理列表均为 **空**（`totalCount:0`），即该账号在 kroger 平台下从未产生过任何规则执行记录。
以下接口都需要一个真实存在、属于 QA 账号的 `ruleExecutionLogId`（或 `ruleId`）作为路径参数，用于查询
某条具体执行记录的子资源：

| 接口 |
|---|
| POST /getAdGroups/{ruleExecutionLogId} |
| POST /getCampaigns/{ruleExecutionLogId} |
| POST /getCampaignTags/{ruleExecutionLogId} |
| POST /getDetail/{ruleExecutionLogId} |
| POST /getLineItems/{ruleExecutionLogId} |
| POST /getProducts/{ruleExecutionLogId} |
| POST /history/export/{ruleExecutionLogId} |
| POST /pending/export/{ruleExecutionLogId} |
| POST /history/getLastPauseAsins/{ruleId} |

ES 中能查到的 `ruleExecutionLogId`/`ruleId` 样本均属于其他真实客户，与本次任务的 QA 账号
(client_id=62) 无关；借用这些 ID 会读取他人真实客户的执行日志详情，超出 QA 账号范围，明确不可接受
（与 share-pass-controller 模块中 delete/edit 接口的跳过逻辑一致）。definition-controller 模块处理
完成后 kroger 账号会有自建规则，但目前尚无对应的真实执行记录（规则执行是异步定时任务，非创建后立即
产生），故本次未能覆盖，留待后续有真实执行数据后补充。

同理，以下 3 个写操作接口也需要真实 `ruleExecutionLogId`/建议记录 ID 才能定位到具体记录做状态变更，
在 kroger 账号无真实执行历史的前提下，若使用他人真实客户的 ID 会修改其真实数据状态，风险不可接受：

| 接口 |
|---|
| POST /changeSuggestionStatus |
| POST /setIgnored |
| POST /setRemarks |

## 三、Amazon 专属 / Adtomic 专属子系统接口（4 个）

实测验证（非凭空判断）：

- **POST /getAutoRuleDetailLog**、**POST /getAutoRuleDetailLogFilter**：请求体为
  `AmazonSpecialRuleRequest`，即使补齐 `newLog` 字段后仍要求真实 `ruleId`（`getRuleId()` 非空），
  这是 Amazon 平台专属的"特殊规则"遗留功能（DTO 命名已表明），kroger 平台无对应数据概念，且无真实
  ID 可用。
- **POST /getAutoRuleLogList**：请求体为 `RuleRequest`，同样要求真实 `id`（`getId()` 非空），无可用
  真实 ID。
- **POST /getAdtomicSuggestions**：请求体要求非空 `profileInfoList`（Adtomic 子系统专属字段），与
  definition-controller 模块中统一跳过的 Adtomic 专属端点（`createAdtomicRule` 等）同属一个子系统，
  按已有惯例跳过。

## 结论

以上 18 个接口本次均未生成 cases.json、未执行。2 个运维类接口按风险跳过；9+3=12 个需要真实
ruleExecutionLogId/ruleId 但账号当前无数据的接口，留待后续有真实执行数据后补充；4 个 Amazon/Adtomic
专属接口因功能不适用于 kroger 平台而跳过。
