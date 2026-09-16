# dayparting-controller (micro-api, target, us) — 风险标记接口

本模块共 52 个有效接口。其中 32 条 Happy Path case 已生成并执行
（`task-2026-09-15-20-00-00/cases.json`，32/32 PASS，连跑两遍验证幂等/稳定），覆盖 13 个只读/校验类接口。

本文件记录：(1) 有真实流量、但判定为高风险/无法确认自建数据边界而主动跳过的写操作接口；
(2) `updateTemplate` 在 target 账号下的复现结果（与 amazon/walmart/criteo 一致）；
(3) 一个本轮新出现、其他三平台流量为 0 的写接口 `applyTemplate`。

**判断方法**：本轮所有命中数均通过
`query_es.py --index "dayparting-schedule-api-*" --path <path> --method <method> --path-field urlReferrer.keyword --method-field httpMethod.keyword --platform target --platform-field productLine.keyword --platform-methods all`
对 target 平台独立统计（90 天窗口，已排除 clientId 62/3186 测试账号噪音）；风险分类逻辑复用
amazon/walmart/criteo 平台 RISK_NOTES.md 已验证的服务级结论（同一份后端代码）。
**本轮排查过程中未对任何非本测试账号 (autoui_acount, clientId=62) 所有的真实数据执行过任何写操作或探测性写调用**——
`updateTemplate` 的复现验证仅使用了本账号自己创建的模板 `fixture_template_id=45063`（`tempName="auto自动化专用勿删"`，`userId=18589`，
已用 `getTemplate` 确认归属后才回放），其余高风险写接口全部只做静态 ES 样本结构分析（含只读读取 `applyTemplate` 的 ES 样本判断其写语义），未发起任何调用。
32 条 Happy Path case 全部为只读/校验类接口，其中涉及 `campaignId`/`profileId` 的场景（`bulk/verify/apply`、`campaignApply`、`findDayParting/campaign`）
均已替换为本账号自有的 `real_campaign_id`({{real_campaign_id}}=430554106983497728) + `profile_id`({{profile_id}}=97393138059194368)，
未使用 ES 样本中其他真实客户的 campaignId/profileId 发起任何调用。

---

## 🔴 identity 字段处理（吸收 criteo 教训，本轮采用更保守策略）

按任务红线要求，本轮**不等到 500 出现才排查**，而是在生成阶段就统一把所有 case 请求体中的 `clientId`/`profileIds`/`profileId`/`userIds`/`advertiserIds`
（调用方账号维度的 identity 字段）替换为本测试账号真实值（`{{client_id}}`=62、`{{profile_id}}`=97393138059194368、`{{user_id}}`=18589），
不直接照抄 ES 样本中属于其他真实客户的原始值。`tempId`/`templateId`/`campaignId`（单值，已替换为本账号 campaign）/`ids`（模板id列表）/
`lineItemIds`/`lineItemTags` 内嵌的 `profileId`（描述被查询对象归属，而非调用方 identity）等业务/目标引用字段保留 ES 真实值，不做替换。
32 条 case 首次执行即 32/32 PASS，未出现 criteo 曾经历的"先 500 再回头排查"情况。

对于原始 ES 样本中 `profileIds`/`userIds` 为多元素数组的"多 profile/多 user"场景，本账号当前仅验证到 1 个真实可访问 `profile_id`
和 1 个真实 `user_id`，数组内重复使用该值占位第二个（及以上）位置以保留"多 profile/多 user"的结构语义，已在对应 case 的
`description` 字段中如实注明，不构成编造场景。

---

## 高风险写操作接口（有真实流量，判定跳过，未生成 case，未执行）

以下接口语义与 amazon/walmart/criteo 平台完全一致（同一份后端代码），风险判断逻辑复用三平台 RISK_NOTES 的结论，命中数为 target 平台独立统计：

### POST /bulk/set/dayparting
- ES 90 天真实流量（target）：719 次。
- 语义：批量设置 dayparting（请求体与 `updateTemplate` 同构）。受 `updateTemplate` 同一写路径 500 问题阻塞（结构一致，必然复现同样的 500），且是批量操作，边界不明确。跳过。

### POST /dayparting/bulk/pausecampaigns
- ES 90 天真实流量（target）：1,249 次（高频，"批量暂停"场景）。
- 语义：批量暂停 campaign 的 dayparting（`baseCampaignList: [{profileId, campaignId}]`）。即使限定为本账号自己的 `real_campaign_id`，"批量暂停"是显式高风险破坏性操作，且该服务写接口对任意真实 client 数据都可能真实生效（amazon 平台已披露过 `changeOwner` 场景的教训），不做探测性调用。跳过。

### DELETE /dayparting/campaigns
- ES 90 天真实流量（target）：10 次。
- 语义：删除 campaign 的 dayparting 应用关联。物理移除关联且无撤销接口可核实原状态，无法确认可安全复用于自建数据的最小验证路径。跳过。

### POST /dayparting/changeStatus
- ES 90 天真实流量（target）：65 次。
- 语义：批量修改 campaign 的 dayparting 状态。依赖已存在的 campaign-scheduler 绑定关系，本轮未建立可验证的自有绑定数据，且属于状态变更类破坏性操作。跳过。

### POST /dayparting/deleteApply
- ES 90 天真实流量（target）：2 次（低频，但非零）。
- 语义：删除 apply 记录（`ids: [applyId]`）。无可靠的"自建 apply"前置路径（`applyTemplate`/`LineItemIdApply` 本身也属于本文件下方的风险/无流量类别，无法安全参照真实结构验证正确用法）。跳过。

### POST /dayparting/deleteDetailApply
- ES 90 天真实流量（target）：4 次。
- 语义：删除更细粒度的 apply 明细（line item 级，ES 样本证实会同时触发 bid 回退）。同上，无可靠自建前置数据来源。跳过。

### POST /dayparting/deleteTemplate
- ES 90 天真实流量（target）：24 次。
- 语义：删除模板（`ids: [tempId]`）。虽然本账号拥有可安全操作的 `fixture_template_id=45063`，但该模板是本轮唯一的自建模板 fixture，删除后若 `updateTemplate`（同一写路径）持续 500 将无法重新创建替代模板；且 ES 样本中的模板 id 均为其他真实客户所有，无法安全参照。为保留可复用的 fixture、避免不可逆操作，本轮跳过，与 amazon/walmart/criteo 平台判断一致。

### POST /dayparting/setTemplateAndApply
- ES 90 天真实流量（target）：111 次。
- 语义：保存模板配置并应用到 campaign（请求体与 `updateTemplate` 同构，额外包含应用范围字段）。同样受 `updateTemplate` 写路径 500 问题阻塞，且会把变更同步应用到已绑定的真实 campaign，风险高于纯 updateTemplate。跳过。

### POST /dayparting/applyTemplate（🔴 本轮新发现：target 平台首次出现流量）
- ES 90 天真实流量（target）：61 次（amazon/walmart/criteo 三平台该接口 90 天内均为 0 流量，此前只能作为"疑似创建入口"静态标注；target 平台是四个平台中首次出现真实调用）。
- Swagger：`requestBody` 为 `TemplateParam`（与 `updateTemplate`/`setTemplateAndApply` 同构），响应体为 `ResultVOApplyResponseView`，`operationId=applyTemplate`。
- ES 样本证实其请求体包含完整的模板配置结构（`action`、`transcriptAutoMin/Max`、`type` 等字段，与 `updateTemplate` 请求体结构高度一致），语义为"将模板配置应用到真实 campaign/line item"，属于会实际改变真实客户 campaign 排期配置的写操作，风险等级与 `setTemplateAndApply` 一致（甚至可能共用同一受阻的写路径）。仅做只读 ES 样本结构分析，未发起任何调用。跳过。

---

## `POST /dayparting/updateTemplate`（`updateTemplate`）—— target 复现结果：与 amazon/walmart/criteo 一致，仍为 HTTP 500

- ES 90 天真实流量（target）：206 次。
- **验证方法（安全、无副作用，仅验证一次，未反复重试）**：先用 `POST /dayparting/getTemplate`（`{"productLine":"target","templateId":45063}`）读取本测试账号自己拥有的模板 `fixture_template_id=45063`（`tempName="auto自动化专用勿删"`，`userId=18589`，与当前登录账号 `autoui_acount` 一致）的完整当前配置，确认返回 `HTTP 200` 且数据确属本账号后，再原样把该 `data` 对象整体回传给 `updateTemplate`（等价于不改变任何实际配置的 no-op 更新）。全程只操作账号自己拥有的数据，未涉及任何其他真实客户的模板。
- **结果**：原样回传自己模板的完整当前配置（等价 no-op 更新）→ `HTTP 500`（`{"timestamp":"2026-09-15T06:49:07.303+00:00","status":500,"error":"Internal Server Error","path":"/dayparting/updateTemplate"}`，无业务 `code` 字段，是后端处理请求时的异常，非业务校验失败）。
- **结论**：**target 平台复现了与 amazon、walmart、criteo 平台完全相同的现象**——`updateTemplate` 对当前测试账号会话下的请求（即便是不改变任何字段、目标模板确属账号自己所有的 no-op 更新）仍返回 `HTTP 500`。四个平台（amazon/walmart/criteo/target）交叉印证，进一步排除"平台特有问题"的可能，指向 micro-api 该写路径本身的功能性缺陷或该测试账号缺少必要的写权限初始化。**未生成 case**，不计入 32 条 Happy Path，建议连同 amazon/walmart/criteo 平台的复现结果一并反馈给 micro-api 研发。

---

## ES 无流量接口（target，90 天窗口内该平台无真实调用，按规则禁止生成 case）

以下 29 个接口（8 GET + 21 POST）经 `query_es.py --platform target --platform-field productLine.keyword --platform-methods all` 独立查询，90 天内 target 平台命中数均为 0
（其中含路径参数的 2 个 GET 接口已按 `{productLine}` 替换为实际值 `target` 查询；GET 类接口经交叉验证该 ES 索引近 180 天内所有平台 GET 请求均为 0 条，是该索引本身不采集 GET 请求，非查询口径问题）：

- GET `/{productLine}/dayparting/template-info`
- GET `/dayparting/{productLine}/getSetting`
- POST `/bulk/update/campaigns/bid`
- POST `/dayparting/apply-switch`
- POST `/dayparting/apply-template/check`
- POST `/dayparting/appoint`
- POST `/dayparting/bulkDeleteApply`
- POST `/dayparting/campaignTag/tree`
- POST `/dayparting/changeOwner`
- POST `/dayparting/changeTimeZone`
- POST `/dayparting/downloadApply`
- POST `/dayparting/downloadTemplate`
- POST `/dayparting/findAmazonCampaignRules`
- GET `/dayparting/getAmazonTimeZone`
- GET `/dayparting/getCampaignsName`
- POST `/dayparting/getCampaignsName`
- GET `/dayparting/getOwners`
- POST `/dayparting/getProfileInfos`
- POST `/dayparting/getTemplate`（注：本轮为验证 `updateTemplate` 曾人工调用过一次该接口读取 `fixture_template_id=45063`，属安全只读操作，但该调用本身发生在验证时点、且 90 天 ES 访问日志统计口径下 target 平台历史真实用户流量为 0，故仍按 ES 无流量处理，不生成常规 case）
- GET `/dayparting/getTemplates`
- POST `/dayparting/LineItemIdApply`
- POST `/dayparting/pause/client-templates`
- POST `/dayparting/status-switch`
- POST `/dayparting/templates`
- GET `/hello`
- POST `/transcript/expire`
- POST `/update/campaign/bid`
- POST `/update/dayPartingChangeTimeZone`
- POST `/verity/campaignApplyTag`

这些接口已在 Excel `MicroApi` sheet 的 target 行标注「ES无流量」。

---

## 小结

- 32 条 Happy Path case，覆盖 13 个只读/校验类接口，全部真实场景（占比 ≥1%）已覆盖，2 次连跑 100% PASS（32/32）。
- 9 个接口因高风险/无法确认自建数据边界跳过（本文件），其中 `applyTemplate` 是 target 平台相比 amazon/walmart/criteo 新出现流量的接口。
- 1 个接口（`updateTemplate`）确认与 amazon/walmart/criteo 平台复现完全一致的 HTTP 500 功能性缺陷，已跳过，建议四平台结果合并反馈给研发。
- 29 个接口（8 GET + 21 POST）target 平台 90 天内无真实流量，按"ES 无流量"规则跳过。
- 13 + 9 + 1 + 29 = 52，与模块总接口数一致。
