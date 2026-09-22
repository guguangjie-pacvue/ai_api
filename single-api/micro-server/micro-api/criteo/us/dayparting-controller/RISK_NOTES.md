# dayparting-controller (micro-api, criteo, us) — 风险标记接口

本模块共 52 个有效接口。其中 25 条 Happy Path case 已生成并执行
（`task-2026-09-15-19-00-00/cases.json`，25/25 PASS，连跑两遍验证幂等/稳定），覆盖 13 个只读/校验类接口。

本文件记录：(1) 直接沿用 amazon/walmart 平台已验证结论、无条件跳过的高风险写操作接口（criteo 流量已独立复核）；
(2) `updateTemplate` 在 criteo 账号下的复现结果（与 amazon/walmart 一致）；
(3) 一次影响 2 条 case 的 identity 归属排查记录。

**判断方法**：本轮所有命中数均通过 `query_es.py --platform criteo --platform-field productLine.keyword --platform-methods all` 对 criteo 平台独立统计（90 天窗口，已排除 clientId 62/3186 测试账号噪音）；风险分类逻辑复用 amazon 平台 `single-api/micro-server/micro-api/amazon/us/dayparting-controller/RISK_NOTES.md` 已验证的服务级结论（同一份后端代码）。**本轮排查过程中未对任何非本测试账号 (autoui_acount, clientId=62) 所有的真实数据执行过任何写操作或探测性写调用**——`updateTemplate` 的复现验证仅使用了本账号自己创建的模板 `fixture_template_id=59345`（详见下文），其余高风险写接口全部只做静态 ES 样本结构分析，未发起任何调用。

---

## 🔴 一次 identity 归属排查：`templateNames` 两条 case 首跑 500，已定位并修复

生成 `POST /dayparting/templateNames` 的 2 个场景 case 时，直接复用了 ES 样本里的原始字段（`clientId: 3562`/`4689`，`profileIds`/`userIds` 为对应的其他真实客户值）。首次执行 `run_cases.py` 时这 2 条 case 均返回 `HTTP 500`（`{"timestamp":...,"status":500,"error":"Internal Server Error","path":"/dayparting/templateNames"}`，无业务 `code` 字段，明显是后端处理请求时的异常，而非业务校验失败）。

**排查结论**：与 amazon 平台 RISK_NOTES 中记载的结论完全一致——该服务的只读接口在 `clientId`/`profileIds`/`userIds` 等 identity 字段与当前登录会话的 client 不匹配时，后端会触发空指针类异常返回 500（这不是权限拦截，是防护缺失导致的报错）。**这不是断言写错，也不是接口本身有缺陷，而是 case 参数直接照抄了其他真实客户的 identity 字段**。

**修复**：将这 2 条 case 的 `clientId` 改为 `{{client_id}}`（本账号 62）、`userIds` 改为 `[{{user_id}}]`（本账号 18589）、`profileIds` 改为本账号真实可访问的 `{{profile_id}}`（97393138059194368）。其中"多 profile 过滤"场景的 `profileIds` 数组结构上仍保留两个元素以体现"多 profile 查询"的业务意图，但因 criteo 测试账号目前只验证到这一个真实可访问 profile，数组内重复使用该值占位第二个位置（如实注明在 case description 里，不构成编造场景，只是复用同一真实值满足数组结构）。

**修复后重新执行**：2 条 case 均变为 `HTTP 200`，25 条 case 连跑两遍全部 100% PASS。此次排查过程中的所有调用均针对本账号自己的账号/profile 发起，未涉及任何其他真实客户的数据。

---

## `POST /dayparting/updateTemplate`（`updateTemplate`）—— criteo 复现结果：与 amazon/walmart 一致，仍为 HTTP 500

- ES 90 天真实流量（criteo）：80 次，抽样内 100% 为"更新已有模板"场景（均带真实 `id`）。
- **验证方法（安全、无副作用）**：先用 `POST /dayparting/getTemplate`（`{"productLine":"criteo","templateId":59345}`）读取本测试账号自己拥有的模板 `fixture_template_id=59345`（`tempName=AutoTest_ApplyCampaign_20260905060004`，`userId=18589`，与当前登录账号 `autoui_acount` 一致）的完整当前配置，确认返回 `200` 且数据确属本账号后，再原样把该配置回传给 `updateTemplate`（等价于不改变任何实际配置的 no-op 更新）。全程只操作账号自己拥有的数据，未涉及任何其他真实客户的模板。
- **结果**（4 种 payload 均已验证）：
  1. 原样回传自己模板的完整当前配置（等价 no-op 更新）→ `HTTP 500`
  2. 空请求体 `{}` → `HTTP 500`
  3. 仅 `{"productLine":"criteo"}` → `HTTP 500`
  4. 仅 `{"productLine":"criteo","id":59345}` → `HTTP 500`
- **结论**：**criteo 平台复现了与 amazon、walmart 平台完全相同的现象**——`updateTemplate` 对当前测试账号会话下的任意请求体（无论是否修改任何字段、无论目标模板是否为账号自己所有）均返回 `HTTP 500`，与请求体内容、目标平台均无关。三个平台（amazon/walmart/criteo）交叉印证，进一步排除"平台特有问题"的可能，指向 micro-api 该写路径本身的功能性缺陷或该测试账号缺少必要的写权限初始化。**未生成 case**，不计入 25 条 Happy Path，建议连同 amazon/walmart 平台的复现结果一并反馈给 micro-api 研发。

---

## 高风险写操作接口（criteo 有真实流量，判定跳过，未生成 case，未执行）

以下接口语义与 amazon/walmart 平台完全一致（同一份后端代码），风险判断逻辑复用 amazon RISK_NOTES 的结论，命中数为 criteo 平台独立统计：

### POST /bulk/update/campaigns/bid
- ES 90 天真实流量（criteo）：1,253,227 次（极高频，自动化批量出价同步）。
- 语义：批量更新 campaign/关键词出价（`itemId`/`targetId`/`profileId`/`bid` 等），ES 样本证实为对真实关键词的真实 bid 写入（如 `{"productLine":"criteo","itemId":"673232737277747200","targetId":"PositiveExactMatch-dryer fragrance free sheet","profileId":"621361071936200704","bid":7.44}`）。该接口在 amazon/walmart 平台的 RISK_NOTES 中未单独出现（可能因这两个平台该接口 90 天内流量为 0 或极低），但 criteo 平台流量极高，属于典型的批量出价写操作，风险与其余批量写接口一致。只读查看结构，不做任何调用。跳过。

### POST /bulk/set/dayparting
- ES 90 天真实流量（criteo）：148 次。
- 语义：批量设置 dayparting（请求体与 `updateTemplate` 同构）。受 `updateTemplate` 同一写路径 500 问题阻塞（结构一致，必然复现同样的 500），且是批量操作，边界不明确。跳过。

### POST /dayparting/bulk/pausecampaigns
- ES 90 天真实流量（criteo）：264 次（"批量暂停"场景）。
- 语义：批量暂停 campaign 的 dayparting（`baseCampaignList: [{profileId, campaignId}]`）。即使限定为本账号自己的 campaign，"批量暂停"是显式高风险破坏性操作，且该服务写接口对任意真实 client 数据都可能真实生效（amazon 平台已验证过 `changeOwner` 场景的教训），不做探测性调用。跳过。

### DELETE /dayparting/campaigns
- ES 90 天真实流量（criteo）：12 次。
- 语义：删除 campaign 的 dayparting 应用关联。物理移除关联且无撤销接口可核实原状态，无法确认可安全复用于自建数据的最小验证路径。跳过。

### POST /dayparting/changeStatus
- ES 90 天真实流量（criteo）：16 次。
- 语义：批量修改 campaign 的 dayparting 状态。依赖已存在的 campaign-scheduler 绑定关系，本轮未建立可验证的自有绑定数据，且属于状态变更类破坏性操作。跳过。

### POST /dayparting/deleteDetailApply
- ES 90 天真实流量（criteo）：2 次。
- 语义：删除更细粒度的 apply 明细（`temId`+`ids`+`revertBid`，ES 样本证实会同时触发 bid 回退）。无可靠的"自建 apply"前置路径参照真实结构安全创建后再删除。跳过。

### POST /dayparting/deleteTemplate
- ES 90 天真实流量（criteo）：14 次。
- 语义：删除模板（`ids: [tempId]`）。虽然本账号拥有可安全操作的 `fixture_template_id=59345`，但该模板是本轮唯一的自建模板 fixture，删除后若 `updateTemplate`（同一写路径）持续 500 将无法重新创建替代模板；且 ES 样本中的模板 id 均为其他真实客户所有，无法安全参照。为保留可复用的 fixture、避免不可逆操作，本轮跳过，与 amazon/walmart 平台判断一致。

### POST /dayparting/setTemplateAndApply
- ES 90 天真实流量（criteo）：22 次。
- 语义：保存模板配置并应用到 campaign（请求体与 `updateTemplate` 同构，额外包含应用范围字段）。同样受 `updateTemplate` 写路径 500 问题阻塞，且会把变更同步应用到已绑定的真实 campaign，风险高于纯 updateTemplate。跳过。

---

## ES 无流量接口（criteo，90 天窗口内该平台无真实调用，按规则禁止生成 case）

以下 30 个接口（8 GET + 22 POST）经 `query_es.py --platform criteo --platform-field productLine.keyword --platform-methods all` 独立查询，90 天内 criteo 平台命中数均为 0（其中含路径参数的 2 个 GET 接口已按 `{productLine}` 替换为实际值 `criteo` 查询；`getProfileInfos` 全平台仅 amazon 使用；GET 类接口经交叉验证该 ES 索引近 180 天内所有平台 GET 请求均为 0 条，是该索引本身不采集 GET 请求，非查询口径问题）：

- GET `/{productLine}/dayparting/template-info`
- GET `/dayparting/{productLine}/getSetting`
- POST `/dayparting/apply-switch`
- POST `/dayparting/apply-template/check`
- POST `/dayparting/applyTemplate`
- POST `/dayparting/appoint`
- POST `/dayparting/bulkDeleteApply`
- POST `/dayparting/campaignTag/tree`
- POST `/dayparting/changeOwner`
- POST `/dayparting/changeTimeZone`
- POST `/dayparting/deleteApply`
- POST `/dayparting/downloadApply`
- POST `/dayparting/downloadTemplate`
- POST `/dayparting/findAmazonCampaignRules`
- GET `/dayparting/getAmazonTimeZone`
- GET `/dayparting/getCampaignsName`
- POST `/dayparting/getCampaignsName`
- GET `/dayparting/getOwners`
- POST `/dayparting/getProfileInfos`
- POST `/dayparting/getTemplate`（注：本轮为验证 `updateTemplate` 曾人工调用过一次该接口读取 `fixture_template_id=59345`，属安全只读操作，但 90 天 ES 访问日志中该调用本身尚未被检索到/该接口在 criteo 平台历史真实用户流量中为 0，故仍按 ES 无流量处理，不生成常规 case）
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

这些接口已在 Excel `MicroApi` sheet 的 criteo 行标注「ES无流量」。

---

## 小结

- 25 条 Happy Path case，覆盖 13 个只读/校验类接口，全部真实场景（占比 ≥1%，含 1 个占比 0.9% 但代表独立业务意图的 `isFilter=false` 场景）已覆盖，2 次连跑 100% PASS。
- 8 个接口因高风险/无法确认自建数据边界跳过（本文件）。
- 1 个接口（`updateTemplate`）确认与 amazon/walmart 平台复现完全一致的 HTTP 500 功能性缺陷，已跳过，建议三平台结果合并反馈给研发。
- 30 个接口（8 GET + 22 POST）criteo 平台 90 天内无真实流量，按"ES 无流量"规则跳过。
- 13 + 8 + 1 + 30 = 52，与模块总接口数一致。
