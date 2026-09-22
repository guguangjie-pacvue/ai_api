# history-controller (chewy, us) — 未生成/未执行接口说明

生成时间：2026-09-14

本模块 26 个接口中，10 个通用查询类接口（`getHistoryList`/`getPendingList`/`getPendingRuleNum`/
`getProfiles`/`history/getRuleAlertCount`/`history/getRuleAlertDetail`/`history/getRuleDeadDetail`/
`queryRuleSnapshots`/`getAutoRuleDetailLog`/`getAutoRuleDetailLogFilter`）已用 chewy 测试账号
（client_id=62, header productline=chewyv2）验证并生成 case。以下 16 个接口未生成 case、未执行，
原因分三类。

## 一、运维类高风险接口（2 个，无论 ES 流量如何都跳过）

- **POST /history/archiveOldLogsTask**：无 requestBody，无范围限定参数，批量归档全平台旧执行日志的
  运维/定时任务接口，blast radius 不限定于单个客户。
- **GET /history/deleteHistoryData/{tableName}**：按原始表名物理删除历史数据，无客户/时间范围限定。

判断依据与 target/kroger 平台 RISK_NOTES.md 中记录的一致，不因平台不同而变化，直接复用结论。

## 二、需要真实 ruleExecutionLogId / ruleId，但 chewy 账号当前无任何真实数据（12 个）

实测确认：chewy 测试账号（client_id=62）当前在 `getHistoryList`/`getPendingList` 下返回的执行历史
和待处理列表均为**空**（`totalCount:0`），即该账号在 chewy 平台下从未产生过任何规则执行记录。
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
接受。definition-controller 模块处理完成后 chewy 账号会有自建规则，但规则执行是异步定时任务，非
创建后立即产生，故本次未能覆盖，留待后续有真实执行数据后补充。

`POST /getAutoRuleLogList` 实测确认属于同一类：请求体为 `RuleRequest`，即使补齐 `pageInfo` 后仍
报错 `Cannot invoke "java.lang.Long.toString()" because the return value of
"RuleRequest.getId()" is null`，即必须携带非空真实 `id`（真实 ruleId），故归入本类，同样无可用真实
ID，跳过。

## 三、Amazon 专属 / Adtomic 专属子系统接口（2 个）

- **POST /getAdtomicSuggestions**：请求体要求非空 `profileInfoList`（Adtomic 子系统专属字段），实测
  传入 chewy 真实 profileId 后报错 `For input string: "FurHaven"`（后端将品牌名字段误当数字解析，
  属 Adtomic 子系统与非 Adtomic 账号数据不兼容的已知问题），与 definition-controller 模块中统一跳过
  的 Adtomic 专属端点同属一个子系统，按已有惯例跳过。
- 说明：本模块中另外两个曾在其他平台被归为"Amazon专属"的接口——`POST /getAutoRuleDetailLog` 和
  `POST /getAutoRuleDetailLogFilter`——本次针对 chewy 账号重新实测后确认**只需携带 `pageInfo`/`newLog`
  即可正常返回 code:200**（不要求真实 ruleId），因此本次已改为正常生成 case 并执行验证，不再归入
  跳过类别（与此前 kroger 平台的判断不同，属于按账号重新验证后的更新结论，非平台差异导致的功能不同）。

## 结论

以上 16 个接口本次均未生成 cases.json、未执行：2 个运维类接口按风险跳过；12 个需要真实
ruleExecutionLogId/ruleId 但账号当前无数据的接口，留待后续有真实执行数据后补充；2 个 Adtomic
专属接口因功能不适用于 chewy 平台账号数据而跳过。
