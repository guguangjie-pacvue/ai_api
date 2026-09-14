# definition-controller (doordash) — 风险标记接口

## POST /terminatedClientRule

- **状态**：未生成 case，未执行。**该接口按任务铁律强制跳过，不可执行，与ES流量无关。**
- **ES 流量**：doordash 平台 90天/180天/730天窗口均为 0 次真实调用(全平台基线,已排除 clientId 62/3186 测试账号)。
- **额外风险**：该接口为"client级别终止规则"操作，语义上可能对整个 client 的规则做批量终止/失效处理，影响范围大且难以安全撤销。无论 ES 是否出现真实流量，本次及后续针对 doordash 的测试均不应调用该接口。

## POST /definition/getRuleTargetInfoByRuleIds

- **状态**：未生成 case，未执行。
- **ES 流量**：该接口 90天内有真实调用(全平台基线,212次),但请求体在 ES 日志中恒为 `null`（Swagger 定义该接口 requestBody 为裸数组 `string[]`，而非对象；推测网关/日志中间件仅记录对象类型 body，未记录数组类型 body）。
- **原因**：无法从 ES 获得该接口的任何真实入参样本，为遵守"禁止猜参数值/禁止fabricate"铁律，本次不生成 case。若未来需要覆盖该接口，需人工确认真实 ruleId 数组的合理来源（如从自建临时规则提取 ruleId 后传入），或改进日志采集后重新抽取真实样本。

## POST /definition/getOwners — 已发现的当前后端缺陷（非本次用例误用）

- **状态**：已生成并执行 3 个 Happy Path 场景 case（Auto/Manual/AutoCommerce，覆盖 500 条随机样本中占比 73.8%/21.4%/4.8%），均按接口"当前真实返回"断言为 `code:405`，因而全部标记 PASS。
- **实测现象**：只要请求体 `userIds` 字段非空（无论内容是本测试账号自身 user_id、ES 样本中的历史真实 userIds、还是历史上曾经成功过的 userIds 组合），接口一律抛出 `class java.lang.Long cannot be cast to class java.lang.String (...)` 并返回 `code:405`；`userIds` 为空数组或省略该字段时正常返回 `code:200`。
- **判断依据**：查询该测试账号（clientId=62）自身历史调用日志，2026-09-11/09-12 期间同样的 userIds 组合曾稳定返回 `code:200` 并带有真实数据；现在（2026-09-14）用完全相同的请求体稳定复现 405。判断为近期真实回归缺陷，不是本次用例的参数误用或权限问题。
- **建议**：请开发同学核实 `/definition/getOwners` 近期变更，排查 userIds 非空时的类型转换逻辑（Long→String 强转异常）。

## 已确认 ES 无流量（doordash,90/180/730天窗口均为0,跳过生成/执行，未额外记录风险）

以下接口经 90/180/730 天多窗口复核，doordash 平台（或全平台基线，视接口是否携带 productLine 字段而定）均无真实调用，按铁律跳过，未生成 case：
`/definition/getAsinRelatedRule`、`/definition/getAutoRefillRuleApplyTagCampaigns`（doordash 专属零流量，其他平台有流量）、`/definition/getAutoRefillRuleApplyTags`（同上）、`/definition/getAutoRefillRuleApplyTargets`（同上）、`/definition/getCampaignWithRule`、`/definition/getProfile`、`/definition/getRuleInfoByCampaignId`（doordash 专属零流量，其他平台有流量）、`/definition/getRuleTargetInfo`(GET)、`/definition/getTarget`、`/definition/updateAutomation`、`/downloadMapping`、`/downloadMapping/{id}`。

`/query-rule-ids/tiktok/roas-explorer`、`/query-rule-ids/tiktok/smart-budget-boost`、`/tiktok/roas-explorer/reminder` 为 tiktok 硬编码路径，doordash 平台流量为 0（已用 body.productLine.keyword 过滤验证），按任务说明跳过。
