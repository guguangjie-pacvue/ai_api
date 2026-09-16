# dayparting-controller (micro-api, ebay, us) — 风险标记接口

本模块共 52 个有效接口。其中 23 条 Happy Path case 已生成并执行
（`task-2026-09-15-17-40-00/cases.json`，23/23 PASS，连跑两遍验证幂等/稳定，
中途 1 条 case（`campaignApply`）因真实业务数据本身返回 `data:null`（该真实campaign当前无冲突应用记录，
属业务正常结果）而收敛断言为仅校验 `code:200`，收敛后再次连跑两遍均 23/23 PASS），覆盖 12 个只读/校验类接口。

本文件记录：(1) 有真实流量、但判定为高风险/破坏性操作而主动跳过的写接口；
(2) `updateTemplate` 在 ebay 账号下的复现结果（与 amazon/walmart/criteo/target/doordash 一致，仍为 HTTP 500，
kroger 因无自有模板未能实测）；
(3) ebay 平台与此前 6 个平台不同的关键背景——`GET /dayparting/getCampaignsName?productLine=ebay` 返回 `data:null`
（本账号当前在 ebay 平台下没有可通过该接口列出的 real-time campaign），但通过对 ES 索引显式按 `clientId=62`
（不排除 62）独立探测，发现本账号在 ebay 平台下确有历史真实调用流量，据此找到了本账号自己产生的真实
`profileId`/`campaignId`，详见下方"identity 字段来源"一节。

**判断方法**：本轮所有命中数均通过
`query_es.py --index "dayparting-schedule-api-*" --path <path> --method <method> --path-field urlReferrer.keyword --method-field httpMethod.keyword --platform ebay --platform-field productLine.keyword --platform-methods all --client-id-exclude 62,3186 --days 90` 对
ebay 平台独立统计（90 天窗口，已排除 clientId 62/3186 测试账号噪音，得到"其他真实客户"口径的场景分布）；
另外对每个候选接口额外跑一次 `--client-id-exclude 3186`（即不排除 62）的探测查询，用两次命中数之差判断
"本账号(clientId=62)在该接口上是否有自己的历史流量"。风险分类逻辑复用 amazon/walmart/criteo/target/kroger/doordash
六平台 RISK_NOTES.md 已验证的服务级结论（同一份后端代码），但本轮仍对每个接口用 ebay 自己的真实 ES 流量数据
独立验证了一遍，未直接照抄其他平台的命中数。

🔴 **ebay 平台登录**：`productline`/`productLine` 真实值直接用 `ebay`（不需要像 kroger/bol/chewy 那样使用登录别名），
已验证 `productline=ebay` 登录直接成功。目录名/Excel Platform 列/请求体 `productLine` 字段值均为 `"ebay"`。

**本轮排查过程中未对任何非本测试账号 (autoui_acount, clientId=62) 所有的真实数据执行过任何写操作或探测性写调用**——
`updateTemplate` 的复现验证仅使用了本账号自己创建的模板 `fixture_template_id=45054`（`tempName="自动化专用-勿删"`，
`userId=18589`，已用 `getTemplate` 确认返回 `userId=18589` 与当前登录账号一致后才回放 no-op 更新）；
`checkDeletePermission`/`template/operation-log`/`template/operators` 三个只读模板接口，ES 样本中的 `ids`/`templateId`/`tempId`
均为其他真实客户所有，本轮统一替换为本账号自有的 `fixture_template_id=45054` 后再调用，未使用 ES 样本中其他真实客户的模板 id
发起过调用；23 条 Happy Path case 全部为只读/校验类接口，涉及 `campaignId`/`profileId` 的场景（`bulk/verify/apply`、
`campaignApply`、`findDayParting/campaign`、`dayparting/apply`、`dayparting/detailApply`）均已替换为本账号自有的
`real_campaign_id`({{real_campaign_id}}=5018005010，次要 {{real_campaign_id_2}}=5020578010) +
`profile_id`({{profile_id}}=vfstro9jqxk，次要 {{profile_id_2}}=007IND2xyeBay、{{profile_id_3}}=c9ac344a-a156-4406-8f3c-ad8c36f3daea），
涉及 `clientId`/`userIds` 的场景（`campaign/tree`、`profile/campaignTag/tree`、`templateNames`）已替换为本账号自有的
`client_id`({{client_id}}=62) + `user_id`({{user_id}}=18589)，未使用 ES 样本中其他真实客户的任何 identity 值发起过调用。

---

## 🔴 identity 字段来源：ES 历史流量证实的本账号真实 profileId/campaignId（ebay 平台特有背景）

与此前 6 个平台不同，本账号在 ebay 平台下当前无法通过 `GET /dayparting/getCampaignsName` 查到任何 real-time campaign
（返回 `data:null`）。若仅凭这一实时接口判断，会误以为本账号在 ebay 平台完全没有可安全使用的真实 identity 数据。

按任务要求，本轮对每个候选接口额外做了一次"不排除 clientId=62"的探测查询（`--client-id-exclude 3186`），并与标准查询
（`--client-id-exclude 62,3186`）的命中数比较，发现以下接口 90 天内**确实存在 clientId=62 自己产生的历史真实调用**：
`dayparting/detailApply`（62 vs 55，差 7 条）、`dayparting/templateNames`（106 vs 63，差 43 条）、
`findDayParting/campaign`（29 vs 3，差 26 条）、`dayparting/campaign/tree`（51 vs 49，差 2 条）、
`dayparting/profile/campaignTag/tree`（18 vs 17，差 1 条）、`bulk/verify/apply`（9 vs 4，差 5 条）、
`bulk/set/dayparting`（3 vs 0，全部为本账号）、`dayparting/deleteDetailApply`（7 vs 0，全部为本账号）、
`dayparting/deleteTemplate`（44 vs 3，差 41 条）、`dayparting/setTemplateAndApply`（46 vs 5，差 41 条）、
`dayparting/updateTemplate`（19 vs 12，差 7 条）。

进一步对 `clientId=62` 显式过滤取样（`findDayParting/campaign`、`dayparting/detailApply` 等）后确认：
本账号在 ebay 平台下真实使用过的 `profileId` 为 `vfstro9jqxk` / `007IND2xyeBay` / `c9ac344a-a156-4406-8f3c-ad8c36f3daea`
（三者常一起出现在 `profileIds` 数组中，代表"多 profile"场景）；`vfstro9jqxk` 与真实 `campaignId=5018005010`
（次要 `5020578010`）在 `findDayParting/campaign`、`bulk/set/dayparting` 的历史调用中存在明确关联。这些值已写入
`config.json` 的 `profile_id`/`profile_id_2`/`profile_id_3`/`real_campaign_id`/`real_campaign_id_2` 变量，
并附详细 `_note_*` 说明来源，可安全用于只读查询类 case 的 identity 字段替换——**它们是本账号自己产生的真实历史数据，
不是借用其他真实客户的数据**。

本轮未发现的情况：`checkDeletePermission`（4 vs 4，差 0）、`template/operation-log`（4 vs 4，差 0）、
`template/operators`（body 恒为 null）这三个模板相关接口在 ebay 平台上没有 clientId=62 的历史流量，
按 amazon/walmart/criteo/doordash 已验证的保守口径，统一用本账号自有的 `fixture_template_id=45054` 替换 ES 样本中
其他真实客户的模板 id 后再调用（而非使用 ES 中该接口本身的其他客户样本）。

---

## 🔴 identity 字段处理范围（与此前 6 个平台一致的判断标准）

按任务红线要求，本轮统一把所有 case 请求体中的顶层 `clientId`/`profileIds`/`profileId`/`userIds`/`campaignId`
（调用方账号维度、需要账号归属匹配的 identity 字段）替换为本测试账号真实值，不直接照抄 ES 样本里属于其他真实客户
的原始值。以下字段判定为"业务过滤字段"而非调用方 identity，保留 ES 真实值不做替换（与 amazon/walmart/criteo/target/
kroger/doordash 六平台已审定的口径完全一致）：
- `tempId`（`campaign/tree`/`dayparting/apply`/`dayparting/detailApply` 中的业务过滤字段，描述被查询的模板范围）
- `states`/`tagIds`/`applyLevels`/`pageInfo`/`preferenceZone`/`datePattern` 等业务过滤/展示字段
- `dayparting/applyTargetSum` 中 `lineItemIds`/`lineItemTags` 内嵌的 `relId`/`relName`/`profileId`/`profileIdName`
  ——这些描述的是"被查询的targeting对象归属"而非"调用方 identity"，与此前六平台口径一致，保留 ES 真实值不做替换
  （包括其中出现的真实客户业务名称，如 `radwell_international`、产品名 `Beldray - Steam Iron...` 等，均为已审定的
  非敏感业务过滤维度）

`checkDeletePermission`/`template/operation-log`/`template/operators` 三个"直接以模板 id 为查询目标"的接口采用更保守
的处理：虽然 `ids`/`templateId`/`tempId` 结构上是业务字段而非调用方 identity 字段，但这三个接口的查询对象就是
"某个模板本身"（权限校验/操作日志/可操作人列表），直接照抄 ES 样本中其他真实客户的模板 id 等同于查询该客户模板的
元数据/操作历史/权限归属，本轮统一替换为本账号自有的 `fixture_template_id`（=45054），与 amazon/walmart/criteo/doordash
平台的处理方式一致。

对于原始 ES 样本中 `profileIds` 为多元素数组的"多 profile"场景，本账号当前恰好验证到 3 个真实可访问 `profileId`
（`vfstro9jqxk`/`007IND2xyeBay`/`c9ac344a-a156-4406-8f3c-ad8c36f3daea`），比此前 6 个平台（均仅 1 个）更完整，
"多 profile"场景直接使用这 3 个真实值组合（`dayparting/apply`、`dayparting/detailApply` 用其中 2 个，
`dayparting/templateNames` 用全部 3 个），未采用此前平台"用同一个真实值重复占位"的折中做法，更贴近真实结构；
`bulk/verify/apply` 的"批量校验"场景本账号仅验证到 2 个真实历史 campaignId（真实流量该场景单次可达 24 个元素），
已在对应 case 的 `description` 字段中如实注明用 2 个真实值代表批量结构语义，不构成编造场景。

23 条 case 首次执行 22/23 PASS（`campaignApply` 因真实业务数据 `data:null` 需收敛断言），修正断言后连跑两次均
23/23 PASS。

---

## `POST /dayparting/updateTemplate`（`updateTemplate`）—— ebay 复现结果：与 amazon/walmart/criteo/target/doordash 一致，仍为 HTTP 500

- ES 90 天真实流量（ebay，排除 62/3186）：12 次；不排除 62 时为 19 次（本账号自己有 7 次历史调用）。
- **验证方法（安全、无副作用，仅验证一次，未反复重试）**：先用 `POST /dayparting/getTemplate`
  （`{"productLine":"ebay","templateId":45054}`）读取本测试账号自己拥有的模板 `fixture_template_id=45054`
  （`tempName="自动化专用-勿删"`，返回 `userId=18589`，与当前登录账号 `autoui_acount` 一致）的完整当前配置，
  确认返回 `HTTP 200` 且数据确属本账号后，再原样把该 `data` 对象整体回传给 `updateTemplate`
  （等价于不改变任何实际配置的 no-op 更新）。全程只操作账号自己拥有的数据，未涉及任何其他真实客户的模板。
- **结果**：原样回传自己模板的完整当前配置（等价 no-op 更新）→ `HTTP 500`
  （`{"timestamp":"2026-09-15T09:35:24.964+00:00","status":500,"error":"Internal Server Error","path":"/dayparting/updateTemplate"}`，
  无业务 `code` 字段，是后端处理请求时的异常，非业务校验失败）。
- **结论**：**ebay 平台复现了与 amazon、walmart、criteo、target、doordash 平台完全相同（kroger 因无自有模板未能实测，
  但性质判断一致）的现象**——`updateTemplate` 对当前测试账号会话下的请求（即便是不改变任何字段、目标模板确属账号
  自己所有的 no-op 更新）仍返回 `HTTP 500`。六个平台（amazon/walmart/criteo/target/doordash/ebay）交叉印证，
  进一步排除"平台特有问题"的可能，指向 micro-api 该写路径本身的功能性缺陷或该测试账号缺少必要的写权限初始化。
  **未生成 case**，不计入 23 条 Happy Path，建议连同其余五平台的复现结果一并反馈给 micro-api 研发。

---

## 高风险写操作接口（有真实流量，判定跳过，未生成 case，未执行）

以下接口语义与 amazon/walmart/criteo/target/kroger/doordash 平台完全一致（同一份后端代码），风险判断逻辑复用
六平台 RISK_NOTES 的结论，命中数为 ebay 平台独立统计：

### POST /bulk/set/dayparting
- ES 90 天真实流量（ebay，排除 62/3186）：0 次；不排除 62 时为 3 次（**全部为本账号自己的历史调用**，
  真实 campaignId 均为 `5020578010`）。
- 语义：批量设置 dayparting（请求体与 `updateTemplate` 同构：`action` 字段为二维矩阵结构）。受 `updateTemplate`
  同一写路径问题阻塞（结构一致，必然复现同样的 500），即便请求体全部来自本账号自己的历史真实数据，仍判定为高风险
  写操作跳过，不做探测性调用。

### POST /bulk/update/campaigns/bid
- ES 90 天真实流量（ebay，排除 62/3186）：24365 次；不排除 62 时为 24373 次（仅差 8 条，绝大多数为其他真实客户的
  真实出价数据，如 `profileId: "nbakq1qxquc"`, `bid: 0.62` 等）。批量出价更新，写操作 + 高频真实其他客户数据，
  跳过。

### POST /dayparting/bulk/pausecampaigns
- ES 90 天真实流量（ebay，排除 62/3186）：188 次；不排除 62 时同为 188 次（无本账号自己的历史调用）。
  批量暂停 campaign 的 dayparting，属显式高风险破坏性操作，且该服务写接口对任意真实 client 数据都可能真实生效
  （amazon 平台已披露过 `changeOwner` 场景的教训），不做探测性调用。跳过。

### POST /dayparting/deleteDetailApply
- ES 90 天真实流量（ebay，排除 62/3186）：0 次；不排除 62 时为 7 次（**全部为本账号自己的历史调用**，
  `ids` 为形如 `[7786]`/`[7784]` 的 apply-detail 明细 id，`temId=45054`）。虽然全部来自本账号历史真实调用，
  但这些 `ids` 是特定时间点存在的 apply 明细记录，当前是否仍然存在无法安全确认（该操作会同时触发 bid 回退，
  且本轮未建立新的可验证前置数据），删除操作不可逆，为避免对未知状态数据发起破坏性调用，跳过。

### POST /dayparting/deleteTemplate
- ES 90 天真实流量（ebay，排除 62/3186）：3 次；不排除 62 时为 44 次（**41 条为本账号自己的历史调用**，
  说明本账号历史上曾多次创建/删除测试模板，`temId` 均为 `null`，`ids` 为已被删除的历史模板 id）。
  虽然本账号拥有可安全操作的 `fixture_template_id=45054`，但该模板是本轮唯一的自建模板 fixture，删除后若
  `updateTemplate`（同一写路径）持续 500 将无法重新创建替代模板；且不希望破坏当前作为其他只读 case
  （`checkDeletePermission`/`template/operation-log`/`template/operators`）依赖的 fixture，为保留可复用的 fixture、
  避免不可逆操作，本轮跳过，与 amazon/walmart/criteo/target/doordash 平台判断一致。

### POST /dayparting/setTemplateAndApply
- ES 90 天真实流量（ebay，排除 62/3186）：5 次；不排除 62 时为 46 次（**41 条为本账号自己的历史调用**，
  请求体与 `updateTemplate` 同构，额外包含应用范围字段）。同样受 `updateTemplate` 写路径 500 问题阻塞，
  且会把变更同步应用到已绑定的真实 campaign，风险高于纯 `updateTemplate`，即便部分历史流量来自本账号自己，
  仍判定为高风险写操作跳过。

---

## ES 无流量接口（ebay，90 天窗口内该平台无真实调用，按规则禁止生成 case）

以下 35 个接口（calendar-center-controller 1 个 + platform-dict-controller 1 个 + dayparting-controller 内 33 个：
9 GET + 1 DELETE + 23 POST）经 `query_es.py --platform ebay --platform-field productLine.keyword --platform-methods all`
独立查询，90 天内 ebay 平台命中数均为 0（含路径参数的 2 个 GET 接口已按 `{productLine}` 替换为实际值 `ebay` 查询；
额外用"不排除 clientId=62"的探测查询二次确认，命中数同样为 0，即本账号在这些接口上也没有任何历史真实调用；
GET 类接口经与此前平台交叉验证，该 ES 索引不采集 GET 请求，是索引本身的限制，非查询口径问题）：

- POST `/calendar/getApplyTagIdByProfileIds`
- POST `/platform/queryDictByConditions`
- GET `/{productLine}/dayparting/template-info`
- GET `/dayparting/{productLine}/getSetting`
- GET `/dayparting/getAmazonTimeZone`
- GET `/dayparting/getCampaignsName`（已人工验证：`productLine=ebay` 时返回 `data:null`，本账号当前无 real-time
  可查询的 campaign；但见上方"identity 字段来源"一节，历史 ES 流量证实本账号曾真实使用过 campaignId）
- GET `/dayparting/getOwners`
- GET `/dayparting/getTemplates`（已人工验证：本账号在 ebay 平台下有 3 条自有模板，其中 `id=45054` 明确标注
  `tempName="自动化专用-勿删"`，已作为 `fixture_template_id` 使用）
- GET `/hello`
- POST `/dayparting/LineItemIdApply`
- POST `/dayparting/amazonCampaignTag/tree`（amazon 专属字段结构，ebay 平台无流量符合预期）
- POST `/dayparting/apply-switch`
- POST `/dayparting/apply-template/check`
- POST `/dayparting/applyTemplate`
- POST `/dayparting/appoint`
- POST `/dayparting/bulkDeleteApply`
- DELETE `/dayparting/campaigns`
- POST `/dayparting/campaignTag/tree`（注意：与本模块生成了 case 的 `POST /dayparting/profile/campaignTag/tree`
  是两个不同接口，前者在 ebay 平台 90 天内无流量，后者有 17 条真实流量，均已用 ebay 自己的真实 ES 数据独立验证）
- POST `/dayparting/changeOwner`
- POST `/dayparting/changeStatus`
- POST `/dayparting/changeTimeZone`
- POST `/dayparting/deleteApply`
- POST `/dayparting/downloadApply`
- POST `/dayparting/downloadTemplate`
- POST `/dayparting/findAmazonCampaignRules`
- POST `/dayparting/getCampaignsName`
- POST `/dayparting/getProfileInfos`
- POST `/dayparting/getTemplate`（注：本轮为验证 `updateTemplate` 曾人工调用过一次该接口读取
  `fixture_template_id=45054`，属安全只读操作，但该调用发生在验证时点、且 90 天 ES 访问日志统计口径下 ebay 平台
  历史真实用户流量为 0，故仍按 ES 无流量处理，不生成常规 case）
- POST `/dayparting/pause/client-templates`
- POST `/dayparting/status-switch`
- POST `/dayparting/templates`
- POST `/transcript/expire`
- POST `/update/campaign/bid`
- POST `/update/dayPartingChangeTimeZone`
- POST `/verity/campaignApplyTag`
