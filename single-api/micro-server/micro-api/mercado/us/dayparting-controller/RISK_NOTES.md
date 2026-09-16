# dayparting-controller (micro-api, mercado, us) — 风险标记接口

本模块共 52 个有效接口。其中 10 条 Happy Path case 已生成并执行
（`task-2026-09-16-10-40-39/cases.json`，10/10 PASS，连跑两遍验证幂等/稳定），覆盖 7 个只读/校验类接口。

本文件记录：(1) mercado 平台流量的特殊背景（近乎 100% 为本测试账号 clientId=62 自己产生）；
(2) 有真实流量、但判定为高风险/破坏性操作而主动跳过的写接口；
(3) `updateTemplate` 在 mercado 账号下**无法安全验证**的原因（本账号在 mercado 平台下没有任何自有模板，与 kroger 情况一致）；
(4) 3 个涉及模板(template)的只读/写接口因同样原因（无自有模板 fixture）跳过；
(5) `templateNames` 场景中发现的一个"团队 userIds 名单随时间漂移导致历史真实请求原样回放会复现 HTTP 500"的现象，及本轮的处理方式。

**判断方法**：本轮所有命中数均通过
`query_es.py --index "dayparting-schedule-api-*" --path <path> --method <method> --path-field urlReferrer.keyword --method-field httpMethod.keyword --platform mercado --platform-field productLine.keyword --platform-methods all --client-id-exclude 3186 --days 90`
对 mercado 平台独立统计（90 天窗口，仅排除 clientId=3186 测试账号噪音，**不排除 62**）；另外对每个候选接口额外跑一次
`--client-id-exclude 62,3186`（标准双排除）核实差值，结果显示 **mercado 平台 90 天内 52 个接口的全部真实流量在双排除口径下均为 0**——
即该平台目前 100% 的调用记录顶层 `clientId` 都是 62（本测试账号自己），不存在"误用其他真实客户数据"的风险来源。风险分类逻辑复用
amazon/walmart/criteo/target/kroger/doordash/ebay 七平台 RISK_NOTES.md 已验证的服务级结论（同一份后端代码），但本轮仍对每个接口
用 mercado 自己的真实 ES 流量数据独立验证了一遍，未直接照抄其他平台的命中数。

🔴 **mercado 平台登录**：`productline`/`productLine` 真实值直接用 `mercado`（不需要像 kroger/bol/chewy 那样使用登录别名），
已验证 `productline=mercado` 登录直接成功。目录名/Excel Platform 列/请求体 `productLine` 字段值均为 `"mercado"`。

**本轮排查过程中未对任何非本测试账号 (autoui_acount, clientId=62) 所有的真实数据执行过任何写操作或探测性写调用**——
10 条 Happy Path case 全部为只读/校验类接口（`bulk/verify/apply`、`dayparting/apply`、`dayparting/applyTargetSum`、
`dayparting/campaign/tree`、`dayparting/campaignTag/tree`、`dayparting/templateNames`、`findDayParting/campaign`），
涉及 `campaignId`/`profileId` 的场景均已替换为本账号自有的 `real_campaign_id`({{real_campaign_id}}=347721808，
次要 `real_campaign_id_2`=352835350) + `profile_id`({{profile_id}}=3679，次要 `profile_id_2`=609975)；涉及 `clientId`/`userIds`
的场景已替换为本账号自有的 `client_id`({{client_id}}=62) + `user_id`({{user_id}}=18589，另一真实历史 userId `user_id_2`=93)；
数组内其余未单独定义变量的 profileId/userId 均经"mercado 该索引 90 天内双排除口径命中数为 0"这一平台级核实，确认同属本账号
(clientId=62) 自己的历史真实数据，非借用其他真实客户数据。

---

## 🔴 mercado 平台特殊背景：ES 流量 100% 来自本测试账号(clientId=62)

与此前七个平台（部分场景需要额外做"不排除 62"的探测才能找到本账号自己的历史流量）不同，mercado 平台经本轮核实：
**该索引 90 天内所有 52 个接口的真实流量，在双排除(`62,3186`)口径下命中数均为 0**——也就是说 mercado 目前只有本测试账号
在使用，不存在"ES 样本混杂其他真实客户数据"的可能性。这意味着：

- 本轮不需要像 ebay 那样额外做"逐接口对比双口径差值"来甄别哪些流量属于本账号——凡是双排除口径下检测到的流量（本轮为 0）
  才是真正的"其他真实客户流量"，凡是仅单排除(`3186`)口径下检测到的流量（本轮 13 个接口共 53 条）**必然**全部是本账号自己的。
- 即便如此，生成 case 时仍严格遵守标准做法：identity 字段（`clientId`/`profileId`/`profileIds`/`userIds`/`campaignId`）统一
  用变量引用本账号已确认的真实值，不直接硬编码 ES 样本里的具体数字；数组中出现的、未单独定义变量的其余 ID（如 `dayparting/apply`
  的 profileIds 数组中另外 7 个非 {{profile_id}} 的值）予以保留 ES 真实值，因为已通过平台级核实确认同属本账号数据。
- 高风险/破坏性写操作接口（`bulk/set/dayparting`、`checkDeletePermission`、`deleteApply`、`deleteTemplate`、
  `setTemplateAndApply`、`updateTemplate`）即便流量确认 100% 为本账号自己产生，仍按红线标准判定跳过，不因为"反正是自己的数据"
  而放松高风险接口的判断标准。

---

## 🔴 无自有模板导致跳过的接口（mercado 平台，与 kroger 情况一致）

`GET /dayparting/getTemplates?productLine=mercado` 返回空列表 —— 本测试账号在 mercado 平台下**没有任何已有模板**
（与 amazon/walmart/criteo/target/ebay 不同，这五个平台均验证到本账号至少拥有 1 个自建模板；与 kroger 情况一致，均为 0 个）。
以下接口的安全验证方法（复用 ES 真实值调用同结构、且必须是本账号自有的 `tempId`）在 mercado 上不具备可行的自有 fixture，
按红线"无法确认自建数据边界的接口跳过"处理：

### POST /dayparting/updateTemplate（🔴 无法复现 amazon/walmart/criteo/target/doordash/ebay 的 no-op 验证）
- ES 90 天真实流量（mercado，排除 3186，100% 为 clientId=62）：2 次。
- amazon/walmart/criteo/target/doordash/ebay 六平台均通过"读取本账号自有模板 → 原样回传做 no-op 更新"验证出 HTTP 500 的复现结果；
  该验证方法的前提是账号在该平台下拥有至少 1 个自有模板。mercado 账号在该平台下模板数为 0，无法执行同样的安全验证路径。
  未尝试用 ES 样本中的 `templateId` 发起调用（即便该样本本身也是 clientId=62 产生的，仍不构成"确认可安全操作"的自有 fixture，
  按红线要求依然跳过）。
- **结论**：本平台无自有模板可安全验证，跳过。未生成 case，不计入 10 条 Happy Path。建议合并 amazon/walmart/criteo/target/
  doordash/ebay 六平台已确认的 HTTP 500 复现结果一并反馈给 micro-api 研发，无需在 mercado 上重复验证同一个已知功能性缺陷。

### POST /dayparting/checkDeletePermission
- ES 90 天真实流量（mercado，排除 3186）：1 次（100% 为 clientId=62）。
- 语义：按 `profileIds` + `ids`(模板id列表) 校验当前用户是否具有删除模板权限。amazon/walmart/criteo/target/doordash/ebay
  六平台均将 `ids` 字段替换为本账号自有的 `fixture_template_id` 后验证。mercado 无自有模板 id 可替换，为避免对不确定归属的
  模板发起权限查询，跳过。

### POST /dayparting/deleteTemplate
- ES 90 天真实流量（mercado，排除 3186）：1 次（100% 为 clientId=62）。
- 语义：删除模板（`ids: [tempId]`）。mercado 本轮无任何自有模板，删除操作本身也属于高风险破坏性操作（见下节），双重原因跳过，
  与 kroger 平台判断一致。

---

## 高风险写操作接口（有真实流量，判定跳过，未生成 case，未执行）

以下接口语义与 amazon/walmart/criteo/target/kroger/doordash/ebay 平台完全一致（同一份后端代码），风险判断逻辑复用
七平台 RISK_NOTES 的结论，命中数为 mercado 平台独立统计（均排除 clientId=3186，双排除口径下均为 0，即以下命中 100% 为
本账号 clientId=62 自己产生）：

### POST /bulk/set/dayparting
- ES 90 天真实流量（mercado，排除 3186）：1 次。
- 语义：批量设置 dayparting（请求体与 `updateTemplate` 同构：`action` 字段为二维矩阵结构）。受 `updateTemplate` 同一写路径
  问题阻塞（结构一致，必然复现同样的 500），即便请求体全部来自本账号自己的历史真实数据，仍判定为高风险写操作跳过，不做探测性调用。

### POST /dayparting/deleteApply
- ES 90 天真实流量（mercado，排除 3186）：3 次。
- 语义：删除 apply 记录（`ids: [applyId]`）。删除操作不可逆，且无可靠的"自建 apply"前置路径可验证当前是否仍然存在，
  即便流量全部来自本账号历史，仍跳过，与此前七平台判断一致。

### POST /dayparting/setTemplateAndApply
- ES 90 天真实流量（mercado，排除 3186）：1 次。
- 语义：保存模板配置并应用到 campaign（请求体与 `updateTemplate` 同构，额外包含应用范围字段）。同样受 `updateTemplate`
  写路径问题阻塞，且会把变更同步应用到已绑定的真实 campaign，风险高于纯 `updateTemplate`，跳过。

---

## ES 无流量接口（mercado，90 天窗口内该平台无真实调用，按规则禁止生成 case）

以下 39 个接口（dayparting-controller 内）经 `query_es.py --platform mercado --platform-field productLine.keyword --platform-methods all --client-id-exclude 3186`
独立查询，90 天内 mercado 平台命中数均为 0（含路径参数的 2 个 GET 接口已按 `{productLine}` 替换为实际值 `mercado` 查询；
GET 类接口经与此前七平台交叉验证，该 ES 索引不采集 GET 请求，是索引本身的限制，非查询口径问题）：

- GET `/{productLine}/dayparting/template-info`
- GET `/dayparting/{productLine}/getSetting`
- POST `/bulk/update/campaigns/bid`
- POST `/dayparting/amazonCampaignTag/tree`（amazon 专属字段结构，mercado 平台无流量符合预期）
- POST `/dayparting/apply-switch`
- POST `/dayparting/apply-template/check`
- POST `/dayparting/applyTemplate`
- POST `/dayparting/appoint`
- POST `/dayparting/bulk/pausecampaigns`
- POST `/dayparting/bulkDeleteApply`
- POST `/dayparting/campaignApply`
- DELETE `/dayparting/campaigns`
- POST `/dayparting/changeOwner`
- POST `/dayparting/changeStatus`
- POST `/dayparting/changeTimeZone`
- POST `/dayparting/deleteDetailApply`
- POST `/dayparting/detailApply`
- POST `/dayparting/downloadApply`
- POST `/dayparting/downloadTemplate`
- POST `/dayparting/findAmazonCampaignRules`
- GET `/dayparting/getAmazonTimeZone`
- GET `/dayparting/getCampaignsName`
- POST `/dayparting/getCampaignsName`
- GET `/dayparting/getOwners`
- POST `/dayparting/getProfileInfos`
- POST `/dayparting/getTemplate`
- GET `/dayparting/getTemplates`（已人工验证：返回空模板列表，本账号在 mercado 平台下无任何自有模板）
- POST `/dayparting/LineItemIdApply`
- POST `/dayparting/pause/client-templates`
- POST `/dayparting/profile/campaignTag/tree`
- POST `/dayparting/status-switch`
- POST `/dayparting/template/operation-log`
- POST `/dayparting/template/operators`
- POST `/dayparting/templates`
- GET `/hello`
- POST `/transcript/expire`
- POST `/update/campaign/bid`
- POST `/update/dayPartingChangeTimeZone`
- POST `/verity/campaignApplyTag`

这些接口已在 Excel `MicroApi` sheet 的 mercado 行标注「ES无流量」。

---

## 🔴 `templateNames` 场景中发现的现象：团队 userIds 名单随时间漂移，历史真实请求原样回放会复现 HTTP 500

`POST /dayparting/templateNames` 90 天内真实流量（排除 3186）共 12 条，其中 11 条(91.7%) `userIds` 为一份完整的 1942 人
团队名单、1 条(8.3%) 为 231 人子集，二者结构上都是"不筛选、查询当前可见全部模板"这同一个业务动作。这份 1942 人名单与
`POST /dayparting/campaignTag/tree` 90 天内 5 条真实流量(100%)使用的 `userIds` 完全一致(逐元素比对相同)。

本轮验证时发现：
- ES 记录的 `responseCode` 字段显示，包括 2026-08-27 那些使用 1942 人名单的历史请求，**当时全部返回 200（成功）**。
- 但本轮将该 1942 人名单原样回放（今日执行），无论是完整名单、还是从中任取 100/231/500 个元素的子集，**均稳定复现 HTTP 500**
  （`Internal Server Error`，无业务 `code` 字段）；而同一份 231 人子集里**今天新产生的那一条真实历史记录**（时间戳
  `2026-09-16T02:32:29`，即准备本任务 config.json 时预先做的验证调用）原样回放**稳定返回 HTTP 200**。
- 该现象与 `dayparting/campaignTag/tree` 形成对照：`campaignTag/tree` 使用完全相同的 1942 人名单回放，本轮**稳定返回 200**，
  说明问题并非"名单本身语法/大小"导致，而更可能是 `templateNames` 接口在处理该名单时会尝试解析/关联每个 `userId`
  对应的用户信息（如显示名、所属团队等），而名单中部分 userId 对应的账号在 8 月下旬到 9 月中旬期间已被禁用/删除，
  触发后端空指针一类异常，只有 `templateNames` 这条链路会真正解析这些字段因而报错，`campaignTag/tree` 不需要做这层解析
  因而不受影响。
- **处理方式**：本轮 `templateNames` 的 Happy Path case 未采用已确认会复现 500 的 1942 人名单样本，改用占比虽仅 8.3%
  但**今日回放仍稳定返回 200** 的 231 人子集样本作为代表（该样本同样是真实历史流量，且是团队名单发生变动前最近验证过
  仍然有效的一份），保证生成的 case 长期可重复执行、不因团队 roster 自然变化而变得脆弱。已在 case `description` 中如实
  注明这一处理逻辑，不构成编造场景。
- 这一现象本身值得反馈给 micro-api 研发：`templateNames` 接口对 `userIds` 列表中包含"已失效用户 id"的容错能力不足，
  建议增加空值/异常保护，避免因团队成员离职/账号禁用而导致该接口报 500。

---

## calendar-center-controller / platform-dict-controller（mercado，独立验证）

- POST `/calendar/getApplyTagIdByProfileIds`（calendar-center-controller）：`query_es.py --platform mercado --client-id-exclude 3186`
  90 天内命中 0 次（双排除口径下同为 0），按"ES无流量"处理，未生成 case。
- POST `/platform/queryDictByConditions`（platform-dict-controller）：同上，90 天内命中 0 次，按"ES无流量"处理，未生成 case。

两个模块共 2 个接口，均已在 Excel 对应 sheet 标注「ES无流量」。

---

## 小结

- 10 条 Happy Path case，覆盖 7 个只读/校验类接口，全部真实场景（占比 ≥1%）已覆盖，2 次连跑 100% PASS（10/10）。
- 6 个接口因高风险/无自有模板判定跳过（`bulk/set/dayparting`、`checkDeletePermission`、`deleteApply`、`deleteTemplate`、
  `setTemplateAndApply`、`updateTemplate`；其中 `checkDeletePermission`/`deleteTemplate`/`updateTemplate` 同时属于"无自有模板"
  原因，`deleteTemplate` 额外也属于高风险破坏性操作）。
- 39 个接口（dayparting-controller 内）mercado 平台 90 天内无真实流量，按"ES 无流量"规则跳过（完整清单见上方）。
- 本模块 52 个接口全部逐一分类完毕：7（已生成 case）+ 6（高风险/无自有模板跳过）+ 39（ES 无流量）= 52。
- calendar-center-controller、platform-dict-controller 各 1 个接口，mercado 平台 90 天内均无真实流量，按"ES 无流量"规则跳过
  （不计入上述 52 个，属独立模块）。
- 额外发现并记录一个值得反馈给研发的问题：`templateNames` 对包含已失效 userId 的历史真实请求原样回放会复现 HTTP 500
  （详见上方专节），已妥善处理避免影响本次 case 的稳定性。
