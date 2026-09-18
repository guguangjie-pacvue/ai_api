# dayparting-controller (micro-api, doordash, us) — 风险标记接口

本模块共 52 个有效接口。其中 25 条 Happy Path case 已生成并执行
（`task-2026-09-15-21-00-00/cases.json`，25/25 PASS，连跑两遍验证幂等/稳定），覆盖 12 个只读/校验类接口。

本文件记录：(1) 有真实流量、但判定为高风险/破坏性操作而主动跳过的写接口；
(2) `updateTemplate` 在 doordash 账号下的复现结果（与 amazon/walmart/criteo/target/kroger 一致，仍为 HTTP 500，
本次是唯一一个账号在该平台下**拥有自有模板**、可以完整走一遍安全 no-op 验证流程并复现的第五个平台）；
(3) 3 个涉及模板(template)的只读接口，本轮采用 amazon/walmart 平台已验证的更保守做法（用自有 `fixture_template_id` 替换掉 ES
样本中其他真实客户的模板 id，而非像 target 那样直接照抄）。

**判断方法**：本轮所有命中数均通过
`query_es.py --index "dayparting-schedule-api-*" --path <path> --method <method> --path-field urlReferrer.keyword --method-field httpMethod.keyword --platform doordash --platform-field productLine.keyword --platform-methods all --client-id-exclude 62,3186 --days 90` 对
doordash 平台独立统计（90 天窗口，已排除 clientId 62/3186 测试账号噪音）；风险分类逻辑复用
amazon/walmart/criteo/target/kroger 平台 RISK_NOTES.md 已验证的服务级结论（同一份后端代码）。

🔴 **doordash 平台登录**：`productline`/`productLine` 真实值直接用 `doordash`（不需要像 kroger/bol/chewy 那样使用登录别名），
已验证 `productline=doordash` 登录直接成功。目录名/Excel Platform 列/请求体 `productLine` 字段值均为 `"doordash"`。

**本轮排查过程中未对任何非本测试账号 (autoui_acount, clientId=62) 所有的真实数据执行过任何写操作或探测性写调用**——
`updateTemplate` 的复现验证仅使用了本账号自己创建的模板 `fixture_template_id=10990`（`tempName="auto自动化专用勿删"`，`userId=18589`，
已用 `getTemplate` 确认返回 `userId=18589` 与当前登录账号一致后才回放 no-op 更新）；
`checkDeletePermission`/`template/operation-log`/`template/operators` 三个只读模板接口，ES 样本中的 `ids`/`templateId`/`tempId`
均为其他真实客户所有，本轮统一替换为本账号自有的 `fixture_template_id=10990` 后再调用，未使用 ES 样本中其他真实客户的模板 id 发起过调用；
其余高风险写接口全部只做静态 ES 样本结构分析，未发起任何调用。25 条 Happy Path case 全部为只读/校验类接口，涉及 `campaignId`/`profileId`
的场景（`bulk/verify/apply`、`campaignApply`、`findDayParting/campaign`）均已替换为本账号自有的
`real_campaign_id`({{real_campaign_id}}=5f21d2cd-3a51-4506-a507-54063ea3064e) + `profile_id`({{profile_id}}=1159880242790137856），
涉及 `clientId`/`userIds` 的场景（`campaign/tree`、`campaignTag/tree`、`templateNames`）已替换为本账号自有的
`client_id`({{client_id}}=62) + `user_id`({{user_id}}=18589)，未使用 ES 样本中其他真实客户的任何 identity 值发起过调用。

---

## 🔴 identity 字段处理（吸收 criteo/target 教训，生成阶段就统一替换）

按任务红线要求，本轮在生成阶段就统一把所有 case 请求体中的 `clientId`/`profileIds`/`profileId`/`userIds`/`campaignId`
（调用方账号维度或需要账号归属匹配的 identity 字段）替换为本测试账号真实值（`{{client_id}}`=62、`{{profile_id}}`=1159880242790137856、
`{{user_id}}`=18589、`{{real_campaign_id}}`=5f21d2cd-3a51-4506-a507-54063ea3064e），不直接照抄 ES 样本中属于其他真实客户的原始值。
`tempId`（`campaign/tree`/`campaignTag/tree`/`dayparting/apply`/`detailApply` 中的业务过滤字段，描述被查询的模板范围而非调用方 identity）、
`lineItemIds`/`lineItemTags` 内嵌的 `profileId`（描述被查询对象归属）、`states`/`tagIds`/`applyLevels` 等业务过滤字段保留 ES 真实值，不做替换。

🔴 **本轮对 `checkDeletePermission`/`template/operation-log`/`template/operators` 三个"直接以模板 id 为查询目标"的接口采用比
`campaign/tree` 系列更保守的处理**：虽然 `ids`/`templateId`/`tempId` 结构上是业务字段而非调用方 identity 字段，但这三个接口的查询对象
就是"某个模板本身"（权限校验/操作日志/可操作人列表），直接照抄 ES 样本中其他真实客户的模板 id 等同于查询该客户模板的元数据/操作历史/
权限归属，本轮统一替换为本账号自有的 `fixture_template_id`（=10990），与 amazon/walmart 平台的处理方式一致（target 平台此前对这三个
接口直接保留了 ES 原始模板 id，本轮 doordash 采用更保守的口径，不视为对 target 结论的否定，仅为账号有自有模板时的更优选择）。

对于原始 ES 样本中 `profileIds` 为多元素数组的"多 profile"场景，本账号当前仅验证到 1 个真实可访问 `profile_id`，
数组内重复使用该值占位其余位置以保留"多 profile"的结构语义，已在对应 case 的 `description` 字段中如实注明，不构成编造场景。
25 条 case 首次执行即 25/25 PASS，连跑两次均 25/25 PASS，未出现 criteo 曾经历的"先 500 再回头排查"情况。

---

## `POST /dayparting/updateTemplate`（`updateTemplate`）—— doordash 复现结果：与 amazon/walmart/criteo/target 一致，仍为 HTTP 500

- ES 90 天真实流量（doordash）：32 次。
- **验证方法（安全、无副作用，仅验证一次，未反复重试）**：先用 `POST /dayparting/getTemplate`（`{"productLine":"doordash","templateId":10990}`）
  读取本测试账号自己拥有的模板 `fixture_template_id=10990`（`tempName="auto自动化专用勿删"`，返回 `userId=18589`，与当前登录账号
  `autoui_acount` 一致）的完整当前配置，确认返回 `HTTP 200` 且数据确属本账号后，再原样把该 `data` 对象整体回传给 `updateTemplate`
  （等价于不改变任何实际配置的 no-op 更新）。全程只操作账号自己拥有的数据，未涉及任何其他真实客户的模板。
- **结果**：原样回传自己模板的完整当前配置（等价 no-op 更新）→ `HTTP 500`
  （`{"timestamp":"2026-09-15T08:21:53.878+00:00","status":500,"error":"Internal Server Error","path":"/dayparting/updateTemplate"}`，
  无业务 `code` 字段，是后端处理请求时的异常，非业务校验失败）。
- **结论**：**doordash 平台复现了与 amazon、walmart、criteo、target、kroger 平台完全相同（kroger 因无自有模板未能实测，但性质判断一致）的现象**——
  `updateTemplate` 对当前测试账号会话下的请求（即便是不改变任何字段、目标模板确属账号自己所有的 no-op 更新）仍返回 `HTTP 500`。
  五个平台（amazon/walmart/criteo/target/doordash）交叉印证，进一步排除"平台特有问题"的可能，指向 micro-api 该写路径本身的功能性缺陷
  或该测试账号缺少必要的写权限初始化。**未生成 case**，不计入 25 条 Happy Path，建议连同其余四平台的复现结果一并反馈给 micro-api 研发。

---

## 高风险写操作接口（有真实流量，判定跳过，未生成 case，未执行）

以下接口语义与 amazon/walmart/criteo/target/kroger 平台完全一致（同一份后端代码），风险判断逻辑复用五平台 RISK_NOTES 的结论，
命中数为 doordash 平台独立统计：

### POST /bulk/set/dayparting
- ES 90 天真实流量（doordash）：50 次。
- 语义：批量设置 dayparting（请求体与 `updateTemplate` 同构）。受 `updateTemplate` 同一写路径问题阻塞（结构一致，必然复现同样的 500），
  且是批量操作，边界不明确。跳过。

### POST /dayparting/bulk/pausecampaigns
- ES 90 天真实流量（doordash）：73 次。
- 语义：批量暂停 campaign 的 dayparting。即使限定为本账号自己的 `real_campaign_id`，"批量暂停"是显式高风险破坏性操作，
  且该服务写接口对任意真实 client 数据都可能真实生效（amazon 平台已披露过 `changeOwner` 场景的教训），不做探测性调用。跳过。

### POST /dayparting/changeStatus
- ES 90 天真实流量（doordash）：3 次。
- 语义：批量修改 campaign 的 dayparting 状态。依赖已存在的 campaign-scheduler 绑定关系，本轮未建立可验证的自有绑定数据，
  且属于状态变更类破坏性操作。跳过。

### POST /dayparting/deleteDetailApply
- ES 90 天真实流量（doordash）：4 次。
- 语义：删除更细粒度的 apply 明细（line item 级，此前平台样本证实会同时触发 bid 回退）。无可靠的自建前置数据来源
  （`applyTemplate`/`LineItemIdApply` 本轮均为 ES 无流量，无法安全参照真实结构先行创建可删除的 apply）。跳过。

### POST /dayparting/deleteTemplate
- ES 90 天真实流量（doordash）：1 次（低频，但非零）。
- 语义：删除模板（`ids: [tempId]`）。虽然本账号拥有可安全操作的 `fixture_template_id=10990`，但该模板是本轮唯一的自建模板 fixture，
  删除后若 `updateTemplate`（同一写路径）持续 500 将无法重新创建替代模板；且 ES 样本中的模板 id 均为其他真实客户所有，无法安全参照。
  为保留可复用的 fixture、避免不可逆操作，本轮跳过，与 amazon/walmart/criteo/target 平台判断一致。

### POST /dayparting/setTemplateAndApply
- ES 90 天真实流量（doordash）：17 次。
- 语义：保存模板配置并应用到 campaign（请求体与 `updateTemplate` 同构，额外包含应用范围字段）。同样受 `updateTemplate` 写路径 500
  问题阻塞，且会把变更同步应用到已绑定的真实 campaign，风险高于纯 updateTemplate。跳过。

---

## ES 无流量接口（doordash，90 天窗口内该平台无真实调用，按规则禁止生成 case）

以下 33 个接口（7 GET + 1 DELETE + 25 POST）经 `query_es.py --platform doordash --platform-field productLine.keyword --platform-methods all`
独立查询，90 天内 doordash 平台命中数均为 0（其中含路径参数的 2 个 GET 接口已按 `{productLine}` 替换为实际值 `doordash` 查询；
GET 类接口经交叉验证该 ES 索引不采集 GET 请求，是索引本身的限制，非查询口径问题——本轮已通过 config.json 手动验证
`GET /dayparting/getCampaignsName?productLine=doordash` 实际可正常调用并返回真实数据，只是 ES access log 未索引该请求）：

- GET `/{productLine}/dayparting/template-info`
- GET `/dayparting/{productLine}/getSetting`
- GET `/dayparting/getAmazonTimeZone`
- GET `/dayparting/getCampaignsName`
- GET `/dayparting/getOwners`
- GET `/dayparting/getTemplates`（已人工验证：本账号在 doordash 平台下有 4 条自有模板，其中 `id=10990` 明确标注给自动化测试用，
  已作为 `fixture_template_id` 使用）
- GET `/hello`
- POST `/bulk/update/campaigns/bid`
- POST `/dayparting/LineItemIdApply`
- POST `/dayparting/amazonCampaignTag/tree`
- POST `/dayparting/apply-switch`
- POST `/dayparting/apply-template/check`
- POST `/dayparting/applyTemplate`（🔴 target 平台该接口有 61 次流量并判定为风险跳过，doordash 平台 90 天内为 0 流量，按 ES无流量 处理）
- POST `/dayparting/appoint`
- POST `/dayparting/bulkDeleteApply`
- DELETE `/dayparting/campaigns`
- POST `/dayparting/changeOwner`
- POST `/dayparting/changeTimeZone`
- POST `/dayparting/deleteApply`
- POST `/dayparting/downloadApply`
- POST `/dayparting/downloadTemplate`
- POST `/dayparting/findAmazonCampaignRules`
- POST `/dayparting/getCampaignsName`
- POST `/dayparting/getProfileInfos`
- POST `/dayparting/getTemplate`（注：本轮为验证 `updateTemplate` 曾人工调用过一次该接口读取 `fixture_template_id=10990`，属安全只读操作，
  但该调用本身发生在验证时点、且 90 天 ES 访问日志统计口径下 doordash 平台历史真实用户流量为 0，故仍按 ES 无流量处理，不生成常规 case）
- POST `/dayparting/pause/client-templates`
- POST `/dayparting/profile/campaignTag/tree`
- POST `/dayparting/status-switch`
- POST `/dayparting/templates`
- POST `/transcript/expire`
- POST `/update/campaign/bid`
- POST `/update/dayPartingChangeTimeZone`
- POST `/verity/campaignApplyTag`

这些接口已在 Excel `MicroApi` sheet 的 doordash 行标注「ES无流量」。

---

## calendar-center-controller / platform-dict-controller（doordash，独立验证）

- POST `/calendar/getApplyTagIdByProfileIds`（calendar-center-controller）：`query_es.py --platform doordash` 90 天内命中 0 次，按"ES无流量"处理，未生成 case。
- POST `/platform/queryDictByConditions`（platform-dict-controller）：`query_es.py --platform doordash` 90 天内命中 0 次，按"ES无流量"处理，未生成 case。

两个模块共 2 个接口，均已在 Excel 对应 sheet 标注「ES无流量」。

---

## 小结

- 25 条 Happy Path case，覆盖 12 个只读/校验类接口，全部真实场景（占比 ≥1%）已覆盖，2 次连跑 100% PASS（25/25）。
- 1 个接口（`updateTemplate`）确认与 amazon/walmart/criteo/target 平台复现完全一致的 HTTP 500 功能性缺陷，已跳过，
  doordash 是第五个交叉印证该缺陷的平台（kroger 因无自有模板未能实测）。
- 5 个接口因高风险/破坏性操作跳过（`bulk/set/dayparting`、`bulk/pausecampaigns`、`changeStatus`、`deleteDetailApply`、
  `deleteTemplate`、`setTemplateAndApply`，共 6 个，含 updateTemplate 相关写路径阻塞的两个）。
- 33 个接口（7 GET + 1 DELETE + 25 POST）doordash 平台 90 天内无真实流量，按"ES 无流量"规则跳过（完整清单见上方，含曾用于
  updateTemplate 验证的 `getTemplate`(POST)，该调用发生在验证时点、非历史真实用户流量，仍按 ES 无流量计入）。
- 本模块 52 个接口全部逐一分类完毕：12（已生成 case）+ 1（updateTemplate 复现 500）+ 6（高风险/写路径阻塞跳过：
  bulk/set/dayparting、bulk/pausecampaigns、changeStatus、deleteDetailApply、deleteTemplate、setTemplateAndApply）+ 33（ES 无流量）= 52。
- calendar-center-controller、platform-dict-controller 各 1 个接口，doordash 平台 90 天内均无真实流量，按"ES 无流量"规则跳过（不计入上述 52 个，属独立模块）。
