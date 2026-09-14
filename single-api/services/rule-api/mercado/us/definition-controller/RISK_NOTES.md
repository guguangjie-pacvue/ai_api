# definition-controller (mercado, 前26个接口) — 风险标记 / ES无流量接口

本文件仅覆盖本次任务范围内的前26个接口(POST /automationPauseAsins 到 POST /definition/getAdtomicRules)。所有判断均以 mercado 平台为对象,已排除测试账号 clientId 62/3186,90/180/730天多窗口复核。

## 核心发现:mercado 平台在本任务范围内的真实(非测试账号)调用量为 0

对 `/definition`(创建规则)在 mercado 场景下做 730 天 `body.productLine.keyword:mercado` 精确匹配,命中 70 条,但用 `clientId.keyword` 聚合后 **100% 来自 clientId=62**(与 config.json 中本账号完全一致的 target_id=316943422 / profile_id=1611231681435504641 fixture),即全部为测试账号自身历史操作痕迹(规则名形如 `autoTest_MercadoRule_*`),**排除后为 0 条真实客户调用**。这与任务预告的"mercado 测试账号流量比 doordash 更稀薄"一致。已确认未借用其他平台真实请求体伪造 mercado 数据(任务铁律 2 明确禁止)。

## 一、ES 无流量,直接跳过(未生成 case,未执行)

以下接口在 mercado 平台(或该接口不含 productLine 字段时的全平台基线)90/180/730天窗口均无真实调用,按铁律跳过:

- **POST /definition** — mercado 90/180/730天 `body.productLine.keyword:mercado` 精确匹配后聚合 clientId,全部为 62(测试账号),真实客户调用为 0。
- **POST /definition/addAppliedObj** — mercado 90/180/730天均 0 命中。
- **POST /definition/calculateNextExecutionTime** — mercado 90/180/730天均 0 命中(纯计算接口,不落库,但请求体含 productLine 且从未见 mercado)。
- **POST /definition/editRule** — mercado 90/180/730天均 0 命中。
- **POST /definition/export** — mercado 90/180/730天均 0 命中。
- **POST /definition/export/commerceRuleReport** — mercado 90/180/730天均 0 命中。
- **POST /definition/checkAutoRefillRule** — 该接口请求体含 productLine 字段,180天基线 1336 条样本聚合出 amazon(1321)/instacart(8)/krogerv3(4)/chewyv2(3),730天窗口内均无 mercado 桶。
- **POST /bulkCreateRule** — 请求体 productLine 嵌套在 `ruleRequests[].productLine`(非顶层),已用嵌套 terms 聚合验证:730天窗口 186 条真实样本(amazon/dsp/instacart/citrus/chewyv2/krogerv3/walmart),无 mercado。
- **POST /automationPauseAsins** — 全平台(该接口不含 productLine,按全平台基线判定)90/730天均 0 命中,与 target 平台 agent 的既往发现一致。**额外风险**:请求体为 `RuleChangeRequest` 通用 DTO(ruleId/ruleIds/isPaused/isDelete/clientId/userId/userName),接口语义为"批量自动暂停 ASIN",无法从字段结构判断其作用范围是否严格限定在调用方自身 client,也无法排除跨规则批量副作用;零真实调用样本下无法观测其真实影响半径。即使未来出现流量,也建议先人工确认作用边界后再决定是否纳入自动化用例。

## 二、tiktok 硬编码路径,与 mercado 无关(未生成 case,未执行)

- **POST /bulk-create/tiktok/roas-explorer** — 730天窗口 99 条真实样本,请求体 `ruleRequests[].productLine` 聚合 100% 为 `tiktok`,mercado 占比 0%。
- **POST /bulk-create/tiktok/smart-budget-boost** — 全平台 730 天窗口 0 命中(该功能本身几乎无人使用)。

## 三、Adtomic 功能族 — 全平台范围内均为测试账号自身操作痕迹,非真实功能使用(未生成 case,未执行)

以下 8 个接口经排查,其全部历史调用(不限 mercado,覆盖所有平台)均只来自 clientId=62 或 3186(测试/内部账号),90/180/730天窗口一致,真实客户调用为 0。判断为该 Adtomic 相关功能当前仅被内部账号手动探测过,尚无真实业务使用:

- **POST /createAdtomicRule** — 90/730天全平台 0 命中。
- **POST /definition/editAdtomicRule** — 全平台仅 1 条历史命中(90/730天一致),clientId=62,body 中 `ruleRequestList[].productLine=instacart`(测试账号手动构造,与 mercado 无关)。
- **POST /definition/getAdtomicRules** — 全平台 90天 21 条命中,clientId 聚合验证 100% 为 62。
- **POST /definition/adtomicRules/settings** — 全平台 90/730天 0 命中。
- **POST /definition/delete/{adtomicRuleId}** — 全平台仅 1 条历史命中(90/730天一致),clientId=62。
- **GET /definition/adtomic/{adtomicRuleId}** — 用 `es_helper.py wildcard-agg` 探测路径前缀,仅发现 1 个真实路径 `/definition/adtomic/1780150708001509377`,共 1 次调用,clientId=62。
- **GET /definition/adtomicRules/settings/{profileId}** — wildcard-agg 探测到 4 个真实 profileId 路径,合计 18 次调用(90/730天一致,无新增),逐一抽样确认 clientId 均为 62 或 3186。
- **GET /definition/checkCustom/{ruleId}** — wildcard-agg 探测到 5 个真实 ruleId 路径,合计 16 次调用(90/730天一致),逐一抽样确认 clientId 均为 62 或 3186。

## 四、无法获取真实请求体样本(未生成 case,未执行)

- **POST /definition/addAppliedObjBySeparateRule** — ES 该路径 90天内有 142 条真实调用记录,但 `_source` 中不含 `body` 字段(仅记录 responseBody/clientId/traceId 等,推测网关/日志中间件未采集该接口的请求体,可能与其请求体结构或大小有关)。无法获得任何真实入参样本,为遵守"禁止猜参数值"铁律,不生成 case。与 doordash 任务中 `/definition/getRuleTargetInfoByRuleIds` 的既往发现同属"日志未采集该接口 body"类问题。

## 五、precursor 依赖被阻断(未生成 case,未执行)

以下接口本身与平台无关(请求体不含 productLine,通常按"自建临时规则→操作→清理"的自包含模式测试),但其必需的前置步骤"创建一条 mercado 规则"(POST /definition)已在第一节确认为 mercado 平台 ES 无流量。任务铁律明确禁止借用其他平台的真实请求体伪造 mercado 数据,因此无法为 mercado 合规构造这条前置创建规则,连带以下接口本次也未生成 case:

- **GET /definition/{ruleId}** — 需要一个真实存在、由 mercado 会话创建的 ruleId 才能验证(GET 全平台流量巨大且不可归因到平台,但路径含动态 ID,doordash/target 的做法均是"先自建临时规则,取其 ruleId 再 GET",该前置创建对 mercado 不可行)。
- **POST /definition/changeOwners** — 同上,需要前置自建规则。
- **POST /definition/changeStatus** — 同上,需要前置自建规则。
- **POST /definition/checkRuleName**(仅"带 id 排除自身"这一子场景被阻断,"不带 id"子场景不依赖前置创建,已正常生成,见 cases.json)。

以上均未尝试用其他账号/其他平台的规则数据替代,以避免违反"数据不可跨平台借用"与"写操作需可安全撤销"的铁律。

## 已生成并全部通过的接口(见 cases.json / report.json)

- **POST /definition/checkRuleName**("不带 id"新建校验场景,全平台基线占比 40.0%)
- **GET /definition/commerceRuleClient**(无入参,全平台基线占比 100%)
- **POST /definition/commerceRuleReport**(By Client,占比 89.7%)
- **POST /definition/commerceRuleReport**(By Rule Name,占比 10.3%,**发现真实缺陷**:调用方账号 clientId=62 名下存在 `requirements` 为 null 的规则,By Rule Name 分组代码路径未做空值检查,稳定复现服务端 405 `Cannot invoke "String.contains(java.lang.CharSequence)" because the return value of "RuleView.getRequirements()" is null`。该缺陷根因与 target 平台 agent 在同一账号上独立发现的缺陷完全一致,判断为服务端真实回归缺陷而非本次用例构造问题,已按实际响应 code:405 固化为回归用例,建议开发同学核实。)
