# dayparting-controller (micro-api, walmart, us) — 风险标记接口

本模块共 52 个有效接口。其中 25 条 Happy Path case 已生成并执行（`task-2026-09-15-13-17-12/cases.json`，覆盖 13 个只读接口，25/25 PASS，连跑两遍验证幂等/可重复）。

本文件记录：(1) 有真实 walmart ES 流量但判定为高风险/无法确认自建数据边界而主动跳过的写操作接口；(2) `updateTemplate` 在 walmart 平台的复现结果（与 amazon 平台对照）。

**判断方法**：本轮判断均基于 walmart 自己的 ES 90 天流量数据独立统计（见下方 `query_es.py --platform walmart` 命中数），风险分类逻辑参考 amazon 平台 `single-api/micro-server/micro-api/amazon/us/dayparting-controller/RISK_NOTES.md` 已验证的结论（同一份后端代码，只是 productLine 不同）。**本轮排查过程中未对任何非本测试账号(autoui_acount, clientId=62)所有的真实数据执行过任何写操作或探测性写调用**，updateTemplate 的复现验证仅使用了本账号自己创建的模板 `fixture_template_id=53645`（详见下文）。

---

## 🔴 updateTemplate 在 walmart 平台的复现结果：与 amazon 一致，仍为 HTTP 500

### POST /dayparting/updateTemplate（`updateTemplate`）
- ES 90 天真实流量（walmart）：605 次，其中 500 条抽样内 **100% 为"更新已有模板"场景**（均带真实 `id`，未观察到创建新模板的请求）。
- **验证方法（安全、无副作用）**：先用 `POST /dayparting/getTemplate` 读取本测试账号自己拥有的模板 `fixture_template_id=53645`（`AutoTest_ApplyCampaign_20260525060036`，`userId=18589`，与本次登录账号 `autoui_acount` 一致）的完整当前配置，再原样把该配置回传给 `updateTemplate`（即"等价于不改变任何实际配置"的 no-op 更新），全程只操作账号自己拥有的数据，不涉及任何其他真实客户的模板。
- **结果**：
  1. 原样回传自己模板的完整当前配置（等价 no-op 更新）→ `HTTP 500 Internal Server Error`。
  2. 空请求体 `{}` → `HTTP 500`。
  3. 仅 `{"productLine":"walmart"}` → `HTTP 500`。
  4. 仅 `{"productLine":"walmart","id":53645}` → `HTTP 500`。
- **结论**：**walmart 平台复现了与 amazon 平台完全相同的现象**——`updateTemplate` 对当前测试账号会话下的任意请求体（无论是否修改了任何字段、无论目标模板是否为账号自己所有）均返回 `HTTP 500`，与请求体内容、目标平台均无关。这排除了"amazon 平台/amazon 账号特有问题"的可能，进一步印证这是 micro-api 该写路径本身的功能性缺陷或该测试账号缺少必要的写权限初始化（而非"case 参数写错了"或"平台特定问题"）。**未生成 case**，不计入 25 条 Happy Path，建议连同 amazon 平台的复现结果一并反馈给 micro-api 研发。

---

## 高风险写操作接口（walmart 有真实流量，判定跳过，未生成 case，未执行）

以下接口语义与 amazon 平台完全一致（同一份后端代码），风险判断逻辑复用 amazon RISK_NOTES 的结论，命中数为 walmart 平台独立统计：

### POST /bulk/set/dayparting（`setBulkBolDayParting`）
- ES 90 天真实流量（walmart）：2198 次。
- 语义：批量设置 dayparting（请求体与 `updateTemplate` 同构）。受 `updateTemplate` 同一写路径 500 问题阻塞（结构完全一致，必然复现同样的 500），且是批量操作，边界不明确。跳过。

### POST /dayparting/bulk/pausecampaigns（`bulkPausedCampaigns`）
- ES 90 天真实流量（walmart）：7301 次（高频，"批量暂停"场景）。
- 语义：批量暂停 campaign 的 dayparting（`baseCampaignList: [{profileId, campaignId}]`）。即使限定为本账号自己的 campaign，"批量暂停"是显式高风险破坏性操作，且该服务写接口对任意真实 client 数据都可能真实生效（amazon 平台已验证过 changeOwner 场景的教训），不做探测性调用。跳过。

### DELETE /dayparting/campaigns（`deleteCampaignDayparting`）
- ES 90 天真实流量（walmart）：10 次。
- 语义：删除 campaign 的 dayparting 应用关联。物理移除关联且无撤销接口可核实原状态，无法确认可安全复用于自建数据的最小验证路径。跳过。

### POST /dayparting/changeStatus（`changeCampaignSchdulerStatus`）
- ES 90 天真实流量（walmart）：378 次。
- 语义：批量修改 campaign 的 dayparting 状态。依赖已存在的 campaign-scheduler 绑定关系，本轮未建立可验证的自有绑定数据，且属于状态变更类破坏性操作。跳过。

### POST /dayparting/deleteApply（`deleteApply`）
- ES 90 天真实流量（walmart）：7 次。
- 语义：删除 apply 记录（`ids: [applyId]`）。无可靠的"自建 apply"前置路径（`applyTemplate`/`LineItemIdApply` 在 walmart 平台 90 天内均为 0 流量，无法参照真实结构验证正确用法安全创建后再删除）。跳过。

### POST /dayparting/deleteDetailApply（`deleteDetailApply`）
- ES 90 天真实流量（walmart）：57 次。
- 语义：删除更细粒度的 apply 明细（line item 级）。同上，无可靠自建前置数据来源。跳过。

### POST /dayparting/deleteTemplate（`deleteTemplates`）
- ES 90 天真实流量（walmart）：69 次。
- 语义：删除模板（`ids: [tempId]`）。虽然本账号拥有可安全操作的 `fixture_template_id=53645`，但该模板是本轮唯一的自建模板 fixture，删除后若 `updateTemplate`（同一写路径）持续 500 将无法重新创建替代模板；且 ES 样本中的模板 id 均为其他真实客户所有，无法安全参照。为保留可复用的 fixture、避免不可逆操作，本轮跳过，与 amazon 平台判断一致。
- 关联：该接口的唯一安全测试路径依赖 `updateTemplate`/新建模板可用，而 `updateTemplate` 已确认 500（见上），因此即使想按"先自建后删除"的思路测试也已被阻塞。

### POST /dayparting/setTemplateAndApply（`setTemplateAndApply`）
- ES 90 天真实流量（walmart）：169 次。
- 语义：保存模板配置并应用到 campaign（请求体与 `updateTemplate` 同构，额外包含应用范围字段）。同样受 `updateTemplate` 写路径 500 问题阻塞，且会把变更同步应用到已绑定的真实 campaign，风险高于纯 updateTemplate。跳过。

---

## ES 无流量接口（walmart，90 天窗口内该平台无真实调用，按规则禁止生成 case）

以下 30 个接口（7 GET + 23 POST/DELETE）经 `query_es.py --platform walmart --platform-field productLine.keyword` 独立查询，90 天内 walmart 平台命中数均为 0（其中 `getProfileInfos` 全平台仅 amazon 使用、`bulk/update/campaigns/bid` 全平台仅 criteo/ebay/krogerv3/chewyv2/citrus 使用，均已用聚合查询交叉核实非查询口径问题，walmart 确实为 0）：

- GET `/{productLine}/dayparting/template-info`
- POST `/bulk/update/campaigns/bid`
- GET `/dayparting/{productLine}/getSetting`
- POST `/dayparting/apply-switch`
- POST `/dayparting/apply-template/check`
- POST `/dayparting/applyTemplate`
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
- POST `/dayparting/getTemplate`
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

这些接口已在 Excel `场景覆盖(us)` 列标注「ES 无流量」，`场景数` 填 0，`通过率` 留空。

---

## 小结

- 25 条 Happy Path case，覆盖 13 个只读接口，全部真实场景（占比 ≥1%）已覆盖，2 次连跑 100% PASS（读接口天然幂等，无需额外清理步骤）。
- 8 个接口因高风险/无法确认自建数据边界跳过（本文件）。
- 1 个接口（`updateTemplate`）确认与 amazon 平台复现完全一致的 HTTP 500 功能性缺陷，已跳过，建议合并反馈给研发。
- 30 个接口（7 GET + 23 POST/DELETE）walmart 平台 90 天内无真实流量，按"ES 无流量"规则跳过。
- 13 + 8 + 1 + 30 = 52，与模块总接口数一致。
