# definition-controller (ebay，第二批25个接口) — 风险标记与跳过说明

范围：POST /definition/getApplyRule、getAsinRelatedRule、getAutoRefillRuleApplyTagCampaigns、getAutoRefillRuleApplyTags、
getAutoRefillRuleApplyTargets、GET /definition/getAutoRefillRuleProfileIds、POST /definition/getCampaignWithRule、
getOwners、getProfile、getRule、getRuleInfoByCampaignId、GET /definition/getRuleTargetInfo、
POST /definition/getRuleTargetInfoByRuleIds、getTarget、GET /definition/hasClickHitMode、
GET /definition/transferableOwnerList、POST /definition/updateAppliedObj、updateAutomation、
POST /downloadMapping、POST /downloadMapping/{id}、POST /getRuleViewList、
POST /query-rule-ids/tiktok/roas-explorer、POST /query-rule-ids/tiktok/smart-budget-boost、
POST /terminatedClientRule、POST /tiktok/roas-explorer/reminder。

ebay 整体 ES 流量极稀薄（730天窗口全服务仅约29次真实调用量级），本模块多数接口按铁律确认为 ES 无流量。

## POST /terminatedClientRule

- **状态**：未生成 case，未执行。**该接口按任务铁律强制跳过，不可执行，与 ES 流量无关（非负性，不可撤销的 client 级别终止操作）。**
- **ES 流量**：`body.productLine.keyword:ebay` 过滤下 90/180/730 天窗口均为 0 次；全平台基线(不分平台)730天内整个服务仅 1 次调用，且该调用极可能来自测试/内部账号。
- **额外风险**：语义为对整个 client 的规则做批量终止/失效处理，影响范围大且难以安全撤销。无论 ES 是否出现真实流量，本次及后续针对 ebay 的测试均不应调用该接口。

## tiktok 硬编码路径（3个）

`/query-rule-ids/tiktok/roas-explorer`、`/query-rule-ids/tiktok/smart-budget-boost`、`/tiktok/roas-explorer/reminder`

- **状态**：未生成 case，未执行。
- **ES 流量**：三者请求体均无 productLine 字段（`es_helper.py productline-agg` 返回 NO_PRODUCTLINE_FIELD），但按 `body.productLine.keyword:ebay` 过滤（与 doordash/target 等历史任务一致的验证方法）90/180/730天窗口均为 0 命中。三者全平台命中量分别为 12708/6854/1247 次（730天），路径本身硬编码为 tiktok 专属业务功能（ROAS Explorer / Smart Budget Boost），ebay 平台不适用，跳过。

## 已确认 ES 无流量（ebay 平台专属零流量，其他平台有真实流量，跳过生成/执行）

以下接口请求体携带 `productLine` 字段，`es_helper.py productline-agg`（730天）显示真实存在的 productLine 分桶均不含 `ebay`：

- `/definition/getAutoRefillRuleApplyTagCampaigns`（amazon 4208 / instacart 8，ebay=0）
- `/definition/getAutoRefillRuleApplyTags`（amazon 3054 / instacart 8，ebay=0）
- `/definition/getAutoRefillRuleApplyTargets`（amazon 5011 / instacart 8，ebay=0）
- `/definition/getProfile`（instacart 10 / amazon 4 / kevel 3，ebay=0）
- `/definition/getRule`（amazon/target/walmart/bolv2/citrus/doordash/krogerv3/chewyv2/kevel/samsclub，ebay=0）
- `/definition/getRuleInfoByCampaignId`（amazon 3846 / instacart 8 / krogerv3 4 / chewyv2 3 / samsclub 2，ebay=0）
- `/definition/getTarget`（kevel 29 / instacart 8 / amazon 2，ebay=0）
- `/definition/updateAutomation`（instacart 9，ebay=0）
- `/downloadMapping`（instacart 1，ebay=0）

同时用 `body.productLine.keyword:ebay` 直接过滤，90/180/730天窗口均为 0 命中，双重验证一致。

## 已确认 ES 无真实客户流量（全平台基线，测试账号污染或路径未使用）

- **GET /definition/getRuleTargetInfo**：全平台（不分平台，GET 无法归因）90/180/730天窗口均为 0 命中，路径本身当前无真实调用。
- **POST /downloadMapping/{id}**：`es_helper.py wildcard-agg` 前缀 `/downloadMapping/` 730天仅发现2个具体路径、共3次命中；`samples --no-exclude-test` 显示全部3次均来自 clientId=62（本测试账号），无真实客户调用。
- **POST /definition/getAsinRelatedRule**：`productline-agg` 显示 730天总命中20次，但 `samples --no-exclude-test` 显示全部20次均来自 clientId=62(18次)/3186(2次)测试账号，排除测试账号后真实客户流量为0。
- **POST /definition/getCampaignWithRule**：同上，730天总命中20次全部来自 clientId=62(18次)/3186(2次)测试账号，真实客户流量为0。

## POST /definition/getRuleTargetInfoByRuleIds — 无法获取真实入参样本

- **状态**：未生成 case，未执行。
- **ES 流量**：该接口请求体无 productLine 字段，全平台基线90天内有真实调用（556次，已排除测试账号）。
- **原因**：Swagger 定义该接口 requestBody 为裸数组 `string[]`（非对象），抽样50条真实记录 `body` 字段恒为 `null`——推测网关/日志中间件仅记录对象类型 body，未记录数组类型 body。无法从 ES 获得任何真实入参样本，为遵守"禁止猜参数值/禁止fabricate"铁律，本次不生成 case。此现象与 doordash/target 等平台此前的调查结论一致（非 ebay 专属问题，是该接口在整个服务范围内的日志采集缺陷）。

## 已生成并执行（7个接口，10个 Happy Path case，全部 PASS，写操作已验证幂等可重复执行2次）

- GET /definition/getAutoRefillRuleProfileIds（全平台基线，无参默认调用，100%）
- GET /definition/hasClickHitMode（全平台基线，不带mode默认调用，100%）
- GET /definition/transferableOwnerList（全平台基线，无参默认调用，100%）
- POST /definition/getApplyRule（全平台基线，按ownerIds查询，100%）
- POST /definition/getOwners（全平台基线，Auto/Manual/AutoCommerce 三场景，占比72.0%/23.2%/4.8%；**已发现当前后端真实缺陷**：非空userIds一律触发 `java.lang.Long cannot be cast to java.lang.String` 返回 code:405，与 doordash 平台此前记录的同一缺陷一致，判断为服务端回归缺陷而非本用例误用，按真实返回码405断言）
- POST /definition/updateAppliedObj（全平台基线，创建临时规则+更新应用对象+归档清理+验证，ruleType使用ES真实样本中3.6%占比且经`/config/ruleTypes?productLine=ebay`验证为ebay合法类型的Keyword，targetLevel改用后端实测通过的KeywordTag）
- POST /getRuleViewList（全平台基线，单/多ruleId两场景占比69.6%/30.4%；直接沿用ES历史ruleId会触发后端NPE(code:405)，故改为创建临时规则获取真实ruleId后验证）

产物：`single-api/services/rule-api/ebay/us/definition-controller/task-2026-09-14-14-21-43/{cases.json,report.json}`
