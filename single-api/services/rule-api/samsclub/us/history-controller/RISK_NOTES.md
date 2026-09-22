# history-controller (samsclub, us) — 未生成/未执行接口说明

生成时间：2026-09-14

本模块 26 个接口中，10 个通用查询类接口（`getHistoryList`/`getPendingList`/`getPendingRuleNum`/
`getProfiles`/`history/getRuleAlertCount`/`history/getRuleAlertDetail`/`history/getRuleDeadDetail`/
`queryRuleSnapshots`/`getAutoRuleDetailLog`/`getAutoRuleDetailLogFilter`）已用 samsclub 测试账号
（client_id=62, header productline=samsclub）验证并生成 case。以下 16 个接口未生成 case、未执行，
原因分三类（与 target/kroger/chewy 平台观察一致）。

## 一、运维类高风险接口（2 个，无论 ES 流量如何都跳过）

- **POST /history/archiveOldLogsTask**：无 requestBody，无范围限定参数，批量归档全平台旧执行日志的
  运维/定时任务接口，blast radius 不限定于单个客户。ES 近 90 天全平台命中 0 次（本身即为极少触发的
  运维任务）。
- **GET /history/deleteHistoryData/{tableName}**：按原始表名物理删除历史数据，无客户/时间范围限定，
  实测 ES 近 90 天全平台真实调用 6480 次但 `tableName` 全部为 `rule_snapshot_detail`，显示这是后台
  定时任务触发而非用户交互功能。

判断依据与 target/kroger/chewy 平台 RISK_NOTES.md 中记录的一致，不因平台不同而变化，直接复用结论。

## 二、需要真实 ruleExecutionLogId / ruleId，但 samsclub 账号当前无任何真实数据（13 个）

实测确认：samsclub 测试账号（client_id=62）当前在 `getHistoryList`/`getPendingList` 下返回的执行历史
和待处理列表均为**空**（`totalCount:0`），即该账号在 samsclub 平台下从未产生过任何规则执行记录。
以下接口都需要一个真实存在、属于 QA 账号的 `ruleExecutionLogId`（或 `ruleId`）作为路径参数：

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
| POST /changeSuggestionStatus |
| POST /setIgnored |
| POST /setRemarks |

ES 中能查到的 `ruleExecutionLogId`/`ruleId` 样本均属于其他真实客户，与本次任务的 QA 账号
(client_id=62) 无关；借用这些 ID 会读取/修改他人真实客户的执行日志详情，超出 QA 账号范围，明确不可
接受。definition-controller 模块处理完成后 samsclub 账号会有自建规则，但规则执行是异步定时任务，非
创建后立即产生，故本次未能覆盖，留待后续有真实执行数据后补充。

`POST /getAutoRuleLogList` 实测确认属于同一类：请求体为 `RuleRequest`，携带 `pageInfo` 后仍报错
`Cannot invoke "java.lang.Long.toString()" because the return value of "RuleRequest.getId()" is null`，
即必须携带非空真实 `id`（真实 ruleId），故归入本类，同样无可用真实 ID，跳过。

## 三、Amazon 专属 / Adtomic 专属子系统接口（1 个）

- **POST /getAdtomicSuggestions**：请求体要求非空的 Adtomic 专属字段，实测传入 samsclub 测试账号
  profileId 后仍报错 `Cannot invoke "java.util.List.stream()" because "profileInfoList" is null`，
  与 definition-controller 模块中统一跳过的 Adtomic 专属端点同属一个子系统，按已有惯例跳过。
- 说明：本模块中另外两个曾在 kroger 平台被归为"Amazon专属"的接口——`POST /getAutoRuleDetailLog` 和
  `POST /getAutoRuleDetailLogFilter`——本次针对 samsclub 账号重新实测后确认**只需携带
  `pageInfo`/`newLog` 即可正常返回 code:200**（不要求真实 ruleId），因此本次已改为正常生成 case
  并执行验证，不再归入跳过类别（与 chewy 平台的复核结论一致，属于按账号重新验证后的更新结论，非平台
  差异导致的功能不同）。

## 结论

以上 16 个接口本次均未生成 cases.json、未执行。2 个运维类接口按风险跳过；13 个需要真实
ruleExecutionLogId/ruleId 但账号当前无数据的接口，留待后续有真实执行数据后补充；1 个 Adtomic 专属
接口因功能不适用于 samsclub 平台而跳过。
