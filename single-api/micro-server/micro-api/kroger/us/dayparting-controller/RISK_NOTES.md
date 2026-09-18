# dayparting-controller (micro-api, kroger, us) — 风险标记接口

本模块共 52 个有效接口。其中 24 条 Happy Path case 已生成并执行
（`task-2026-09-15-15-35-05/cases.json`，24/24 PASS，连跑两遍验证幂等/稳定），覆盖 9 个只读/校验类接口。

本文件记录：(1) 有真实流量、但判定为高风险/无法确认自建数据边界而主动跳过的写操作接口；
(2) `updateTemplate` 在 kroger 账号下**无法安全验证**的原因（本账号在 kroger 平台下没有任何自有模板，与 amazon/walmart/criteo/target 不同）；
(3) 3 个涉及模板(template)的只读接口因同样原因（无自有模板 fixture）跳过。

**判断方法**：本轮所有命中数均通过
`query_es.py --index "dayparting-schedule-api-*" --path <path> --method <method> --path-field urlReferrer.keyword --method-field httpMethod.keyword --platform krogerv3 --platform-field productLine.keyword --platform-methods all`
对 kroger 平台独立统计（90 天窗口，已排除 clientId 62/3186 测试账号噪音）；风险分类逻辑复用
amazon/walmart/criteo/target 平台 RISK_NOTES.md 已验证的服务级结论（同一份后端代码）。

🔴 **kroger 平台登录别名**：`productLine`/`productline` 真实值必须用 `krogerv3`（不是 `kroger`），已验证 `productline=kroger` 登录返回 406
"Please reach to your Pacvue contacts to activate."。目录名/Excel Platform 列/`--swagger-title` 参数仍用业务名 `kroger`。所有 case 请求体中的
`productLine` 字段值均为 `"krogerv3"`，`query_es.py --platform` 参数也传 `krogerv3`。

**本轮排查过程中未对任何非本测试账号 (autoui_acount, clientId=62) 所有的真实数据执行过任何写操作或探测性写调用**——
本轮 24 条 case 全部为只读/校验类接口，涉及 `campaignId`/`profileId` 的场景（`bulk/verify/apply`、`campaignApply`、`findDayParting/campaign`）
均已替换为本账号自有的 `real_campaign_id`({{real_campaign_id}}=100000000169) + `profile_id`({{profile_id}}=100000000001)，
涉及 `clientId`/`userIds` 的场景（`campaign/tree`、`campaignTag/tree`、`templateNames`）已替换为本账号自有的
`client_id`({{client_id}}=62) + `user_id`({{user_id}}=18589)，未使用 ES 样本中其他真实客户的任何 identity 值发起过调用。

---

## 🔴 identity 字段处理（吸收 criteo/target 教训，生成阶段就统一替换）

按任务红线要求，本轮在生成阶段就统一把所有 case 请求体中的 `clientId`/`profileIds`/`profileId`/`userIds`/`campaignId`
（调用方账号维度或需要账号归属匹配的 identity 字段）替换为本测试账号真实值（`{{client_id}}`=62、`{{profile_id}}`=100000000001、
`{{user_id}}`=18589、`{{real_campaign_id}}`=100000000169），不直接照抄 ES 样本中属于其他真实客户的原始值。`tempId`/`applyIds`
（业务过滤字段，描述被查询对象而非调用方 identity）、`lineItemIds`/`lineItemTags` 内嵌的 `profileId`（描述被查询对象归属）、
`states`/`tagIds` 等业务字段保留 ES 真实值，不做替换。24 条 case 首次执行即 24/24 PASS，连跑两次均 24/24 PASS，未出现
criteo 曾经历的"先 500 再回头排查"情况。

对于原始 ES 样本中 `profileIds`/`userIds` 为多元素数组的"多 profile/多 user"场景，本账号当前仅验证到 1 个真实可访问 `profile_id`，
数组内重复使用该值占位第二个（及以上）位置以保留"多 profile"的结构语义，已在对应 case 的 `description` 字段中如实注明，不构成编造场景。

---

## 🔴 无自有模板导致跳过的接口（kroger 平台特有情况）

`GET /dayparting/getTemplates?productLine=krogerv3` 返回空列表 —— 本测试账号在 kroger 平台下**没有任何已有模板**
（不同于 amazon/walmart/criteo/target，这四个平台均验证到本账号至少拥有 1 个自建模板，如 target 的 `fixture_template_id=45063`）。
以下接口的安全验证方法（复用 ES 真实值调用同结构、且必须是本账号自有的 `tempId`）在 kroger 上不具备可行的自有 fixture，
按红线"无法确认自建数据边界的接口跳过"处理：

### POST /dayparting/updateTemplate（🔴 无法复现 amazon/walmart/criteo/target 的 no-op 验证）
- ES 90 天真实流量（kroger）：26 次（有真实流量，非"ES无流量"，但跳过原因是缺少可安全验证的自有 fixture）。
- amazon/walmart/criteo/target 四平台均通过"读取本账号自有模板 → 原样回传做 no-op 更新"验证出 HTTP 500 的复现结果；
  该验证方法的前提是账号在该平台下拥有至少 1 个自有模板。kroger 账号在该平台下模板数为 0，无法执行同样的安全验证路径。
  未尝试用 ES 样本中其他真实客户的 `templateId` 发起调用（会构成对非本账号数据的写操作探测，属红线禁止行为）。
- **结论**：本平台无自有模板可安全验证，跳过。未生成 case，不计入 24 条 Happy Path。建议合并 amazon/walmart/criteo/target
  四平台已确认的 HTTP 500 复现结果一并反馈给 micro-api 研发，无需在 kroger 上重复验证同一个已知功能性缺陷。

### POST /dayparting/checkDeletePermission
- ES 90 天真实流量（kroger）：9 次。
- 语义：按 `profileIds` + `ids`(模板id列表) 校验当前用户是否具有删除模板权限。amazon/walmart/criteo/target 四平台均将
  `ids` 字段替换为本账号自有的 `fixture_template_id` 后验证（而非直接使用 ES 样本中其他真实客户的模板 id）。
  kroger 无自有模板 id 可替换，为避免查询其他真实客户的模板权限数据，跳过。

### POST /dayparting/template/operation-log
- ES 90 天真实流量（kroger）：3 次。
- 语义：按 `templateId` 查询该模板的操作日志。同上，amazon/walmart/criteo/target 均使用自有 `fixture_template_id`
  发起验证，kroger 无自有模板 id，跳过（避免读取其他真实客户模板的操作历史）。

### POST /dayparting/template/operators
- ES 90 天真实流量（kroger）：3 次。
- 语义：按 query string 参数 `productLine`+`tempId` 查询模板可操作人列表（请求体为空）。同上，amazon/walmart/criteo/target
  均使用自有 `fixture_template_id` 发起验证，kroger 无自有模板 id，跳过。

---

## 高风险写操作接口（有真实流量，判定跳过，未生成 case，未执行）

以下接口语义与 amazon/walmart/criteo/target 平台完全一致（同一份后端代码），风险判断逻辑复用四平台 RISK_NOTES 的结论，
命中数为 kroger 平台独立统计：

### POST /bulk/set/dayparting
- ES 90 天真实流量（kroger）：14 次。
- 语义：批量设置 dayparting（请求体与 `updateTemplate` 同构）。受 `updateTemplate` 同一写路径问题阻塞，且是批量操作，边界不明确。跳过。

### POST /bulk/update/campaigns/bid（🔴 本轮新发现：kroger 平台流量远高于其他四平台）
- ES 90 天真实流量（kroger）：4,663 次（amazon/walmart/criteo/target 四平台该接口 90 天内均为 0 流量，kroger 是首次出现真实调用，且量级很大）。
- 语义：批量修改 campaign 出价（bid）。属于任务红线明确列出的高风险破坏性写操作（批量修改真实客户出价，无法确认自建数据边界），
  即便流量很高也不做探测性调用。仅做只读 ES 样本结构分析，未发起任何调用。跳过。

### POST /dayparting/bulk/pausecampaigns
- ES 90 天真实流量（kroger）：79 次。
- 语义：批量暂停 campaign 的 dayparting。显式高风险破坏性操作，且该服务写接口对任意真实 client 数据都可能真实生效
  （amazon 平台已披露过 `changeOwner` 场景的教训），不做探测性调用。跳过。

### POST /dayparting/changeStatus
- ES 90 天真实流量（kroger）：3 次。
- 语义：批量修改 campaign 的 dayparting 状态。依赖已存在的 campaign-scheduler 绑定关系，本轮未建立可验证的自有绑定数据，
  且属于状态变更类破坏性操作。跳过。

### POST /dayparting/deleteApply
- ES 90 天真实流量（kroger）：2 次（低频，但非零）。
- 语义：删除 apply 记录（`ids: [applyId]`）。无可靠的"自建 apply"前置路径。跳过。

### POST /dayparting/deleteDetailApply
- ES 90 天真实流量（kroger）：1 次。
- 语义：删除更细粒度的 apply 明细（line item 级）。同上，无可靠自建前置数据来源。跳过。

### POST /dayparting/deleteTemplate
- ES 90 天真实流量（kroger）：9 次。
- 语义：删除模板（`ids: [tempId]`）。kroger 本轮无任何自有模板（含此前尝试的 fixture），ES 样本中的模板 id 均为其他真实客户所有，
  无法安全参照。跳过，与 amazon/walmart/criteo/target 平台判断一致。

### POST /dayparting/setTemplateAndApply
- ES 90 天真实流量（kroger）：30 次。
- 语义：保存模板配置并应用到 campaign（请求体与 `updateTemplate` 同构，额外包含应用范围字段）。同样受 `updateTemplate`
  写路径问题阻塞，且会把变更同步应用到已绑定的真实 campaign，风险高于纯 updateTemplate。跳过。

---

## ES 无流量接口（kroger，90 天窗口内该平台无真实调用，按规则禁止生成 case）

以下 31 个接口（8 GET + 23 POST/DELETE）经 `query_es.py --platform krogerv3 --platform-field productLine.keyword --platform-methods all`
独立查询，90 天内 kroger 平台命中数均为 0（其中含路径参数的 2 个 GET 接口已按 `{productLine}` 替换为实际值 `krogerv3` 查询；
GET 类接口经交叉验证该 ES 索引本身不采集 GET 请求，是索引本身的限制，非查询口径问题——本轮已通过 config.json 手动验证
`GET /dayparting/getCampaignsName?productLine=krogerv3` 实际可正常调用并返回真实数据，只是 ES access log 未索引该请求）：

- GET `/{productLine}/dayparting/template-info`
- GET `/dayparting/{productLine}/getSetting`
- POST `/dayparting/amazonCampaignTag/tree`
- POST `/dayparting/apply-switch`
- POST `/dayparting/apply-template/check`
- POST `/dayparting/applyTemplate`（🔴 target 平台该接口有 61 次流量并判定为风险跳过，kroger 平台 90 天内为 0 流量，按 ES无流量 处理）
- POST `/dayparting/appoint`
- POST `/dayparting/bulkDeleteApply`
- DELETE `/dayparting/campaigns`
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
- POST `/dayparting/getTemplate`
- GET `/dayparting/getTemplates`（已人工验证返回空列表，本账号无模板，见上文说明）
- POST `/dayparting/LineItemIdApply`
- POST `/dayparting/pause/client-templates`
- POST `/dayparting/profile/campaignTag/tree`
- POST `/dayparting/status-switch`
- POST `/dayparting/templates`
- GET `/hello`
- POST `/transcript/expire`
- POST `/update/campaign/bid`
- POST `/update/dayPartingChangeTimeZone`
- POST `/verity/campaignApplyTag`

这些接口已在 Excel `MicroApi` sheet 的 kroger 行标注「ES无流量」。

---

## calendar-center-controller / platform-dict-controller（kroger，独立验证）

- POST `/calendar/getApplyTagIdByProfileIds`（calendar-center-controller）：`query_es.py --platform krogerv3` 90 天内命中 0 次，按"ES无流量"处理，未生成 case。
- POST `/platform/queryDictByConditions`（platform-dict-controller）：`query_es.py --platform krogerv3` 90 天内命中 0 次，按"ES无流量"处理，未生成 case。

两个模块共 2 个接口，均已在 Excel 对应 sheet 标注「ES无流量」。

---

## 小结

- 24 条 Happy Path case，覆盖 9 个只读/校验类接口，全部真实场景（占比 ≥1%）已覆盖，2 次连跑 100% PASS（24/24）。
- 8 个接口因高风险/破坏性操作跳过（`bulk/set/dayparting`、`bulk/update/campaigns/bid`、`bulk/pausecampaigns`、`changeStatus`、
  `deleteApply`、`deleteDetailApply`、`deleteTemplate`、`setTemplateAndApply`）。
- 4 个接口因"kroger 账号无自有模板 fixture"无法安全验证跳过（`updateTemplate`、`checkDeletePermission`、`template/operation-log`、`template/operators`）。
- 31 个接口（dayparting-controller 内）kroger 平台 90 天内无真实流量，按"ES 无流量"规则跳过（完整清单见上方）。
- 本模块 52 个接口全部逐一分类完毕：9（已生成 case）+ 8（高风险跳过）+ 4（因无自有模板跳过）+ 31（ES 无流量）= 52。
- calendar-center-controller、platform-dict-controller 各 1 个接口，kroger 平台 90 天内均无真实流量，按"ES 无流量"规则跳过（不计入上述 52 个，属独立模块）。
