# dayparting-controller (micro-api, tiktok, us) — 风险标记与结论

本文件记录 tiktok 平台（含 calendar-center-controller / platform-dict-controller）共 54 个有效接口的风险跳过、ES 流量结论与新发现的后端缺陷。

## 结论继承自 amazon / citrus / dsp 已验证的服务级发现（与平台无关，tiktok 同样适用）

`single-api/micro-server/micro-api/amazon/us/dayparting-controller/RISK_NOTES.md` 已确认：**该服务（micro-api dayparting-controller）的写接口对测试账号不做跨 client 权限隔离**——写调用会对请求体里指定的任意真实客户数据真实生效，且无回滚接口可核实原状态。这一结论是服务级、与平台无关的，tiktok 平台的 autoui_acount 账号（clientId=62，与 citrus/samsclub 等平台共用同一测试账号）同样适用。

## 高风险写操作接口（15 项，一律跳过，未做任何探测性调用）

与 amazon/citrus/dsp 等平台一致，以下 15 个接口无论 ES 流量如何，tiktok 平台同样直接跳过：

1. `DELETE /dayparting/campaigns`
2. `POST /dayparting/deleteTemplate`
3. `POST /dayparting/deleteApply`
4. `POST /dayparting/deleteDetailApply`
5. `POST /dayparting/bulk/pausecampaigns`
6. `POST /dayparting/changeStatus`
7. `POST /dayparting/changeOwner`
8. `POST /dayparting/appoint`
9. `POST /dayparting/apply-switch`
10. `POST /dayparting/status-switch`
11. `POST /dayparting/setTemplateAndApply`
12. `POST /bulk/set/dayparting`
13. `POST /bulk/update/campaigns/bid`
14. `POST /update/campaign/bid`
15. `POST /update/dayPartingChangeTimeZone`

以上 15 个接口，tiktok 平台未做任何调用，未生成 case。

## `POST /dayparting/updateTemplate` — 本次未做验证性调用（与其他平台不同）

按任务要求本应"回放该测试账号自己名下的真实历史 body"做一次干净验证，但实测：

- 本账号（clientId=62）近 365 天内对 tiktok 产品线的 `updateTemplate` 调用为 **0 次**。
- ES 全平台真实客户（排除测试账号）近 365 天内对 tiktok 产品线的 `updateTemplate` 调用同样为 **0 次**。

即：tiktok 平台在本服务上根本不存在任何 `updateTemplate` 真实历史请求体可供回放，不存在"自己名下真实历史 body"这一素材。为避免编造请求体、避免对未知结构做无依据的探测调用，**本次未对 tiktok 执行任何 `updateTemplate` 调用**（包括验证性调用），按红线 1「ES 无流量禁止生成、禁止执行」处理，Excel 场景覆盖列填「ES 无流量」。因此 tiktok 无法归入 amazon(500)/instacart(空操作)/samsclub/citrus/dsp(真实生效) 四种已知模式中的任何一种——目前状态是"从未被使用过"。

## `POST /dayparting/templateNames` — 新发现：tiktok 平台专属、更严重的确认后端缺陷

本次生成 case 前按任务要求做分层验证：

1. **空/无 userIds、无 profileIds 的最简请求体验证接口本身可用**：`{}` → `HTTP 200`（返回空列表）；`{"pageInfo":{...}}`（不含 `productLine` 字段）→ `HTTP 200`。
2. 加入 `"productLine":"tiktok"` 单个字段 → **`HTTP 500`**，且与其余字段完全无关：
   - `{"productLine":"tiktok"}` 单字段 → 500（复测 2 次结果一致，稳定复现）
   - 完整真实结构（含 `profileIds`/`userIds` 等全部字段，`profileIds`/`userIds` 均为空数组）+ `productLine:"tiktok"` → 仍 500
   - 完整真实结构 + 真实非空 `profileIds`/`userIds` + `productLine:"tiktok"` → 仍 500
3. **横向对照**：用完全相同的调用方式，把 `productLine` 依次替换为其余 12 个平台（amazon/walmart/samsclub/instacart/bol/chewy/kroger/criteo/target/doordash/ebay/dsp/mercado）→ **全部 `HTTP 200`** 正常返回数据，排除"请求体结构本身有问题"的可能，问题精确定位到 `productLine` 字段值等于字面量 `"tiktok"` 这一个条件。
4. **ES 交叉验证**：真实客户（`clientId=4618`，非测试账号）近 90 天内对该接口有 2 次真实 tiktok 调用，请求体结构与本账号历史调用体一致，同样携带 `"productLine":"tiktok"` 字段——说明该缺陷当前正在生产环境对真实 tiktok 客户必现，不是本次测试引入或环境特有问题。

**性质判断**：这是与 bol（`userIds` 特定值触发）/chewy（`profileIds` 非 null 触发）/dsp（`userIds` 非空数组触发）三个平台已知的"字段取值级"500 缺陷**不同且更严重**的一类问题——tiktok 只需要 `productLine` 字段等于 `"tiktok"` 这一个条件即可稳定 100% 触发，与其余任何字段是否存在、是否为空、取什么值完全无关。

### 跨平台 `templateNames` 500 缺陷对比更新

| 平台 | 触发字段 | 触发条件 | 性质判断 |
|---|---|---|---|
| bol | `userIds` | 传入特定值（93） | 特定值触发的空指针类缺陷 |
| chewy | `profileIds` | 字段非 null（任意值） | 疑似时间窗口性的回归问题 |
| dsp | `userIds` | 非空数组（任意值） | 稳定可复现的字段级缺陷 |
| **tiktok** | **`productLine`** | **值等于 `"tiktok"` 本身，与其余字段完全无关** | **稳定可复现，触发条件最简单、影响面最广（凡是 tiktok 客户调用该接口即必现）** |

**处理方式**：按 dsp 先例，未修改请求体规避该缺陷，生成 1 条 Happy Path case（ES 90 天真实流量仅 2 次，结构完全一致，占比 100%），`expected_response` 按正常预期编写，执行结果如实保留 **FAIL**（HTTP 500），作为缺陷证据留痕，详见 `task-2026-09-16-02-40-08/report.json`。

## ES 流量结论：GET 端点（7 个，全部 ES 无流量）

与 `services.json.micro-api.es.platform_filter._note` 记录的已知现象一致（该索引近 180 天 GET 请求实测为 0 条），tiktok 平台下逐一核实（365 天窗口）以下 7 个 GET 接口均为 **0 条真实流量**，按 ES 无流量处理，未生成 case：

1. `GET /{productLine}/dayparting/template-info`（已代入真实路径 `/tiktok/dayparting/template-info` 核实，同时对照 amazon/walmart/citrus/dsp 同路径也均为 0，确认是服务级 GET 流量现象非路径拼错）
2. `GET /dayparting/{productLine}/getSetting`（已代入 `/dayparting/tiktok/getSetting` 核实）
3. `GET /dayparting/getAmazonTimeZone`
4. `GET /dayparting/getCampaignsName`
5. `GET /dayparting/getOwners`
6. `GET /dayparting/getTemplates`
7. `GET /hello`

## ES 流量结论：POST 端点（27 个，全部 ES 无流量）

逐一核实（`--platform tiktok --platform-field productLine.keyword --platform-methods all`，365 天窗口，排除测试账号 62/3186）以下 27 个 POST 接口均为 **0 条真实流量**，按 ES 无流量处理，未生成 case（已用 `/dayparting/getProfileInfos`、`/dayparting/campaign/tree` 的 amazon 流量做过查询机制正确性的抽样对照，确认查询本身有效，tiktok 确系真实低流量而非查询错误）：

1. `POST /bulk/verify/apply`
2. `POST /dayparting/amazonCampaignTag/tree`
3. `POST /dayparting/apply`
4. `POST /dayparting/apply-template/check`
5. `POST /dayparting/applyTargetSum`
6. `POST /dayparting/applyTemplate`
7. `POST /dayparting/bulkDeleteApply`
8. `POST /dayparting/campaign/tree`
9. `POST /dayparting/campaignApply`
10. `POST /dayparting/campaignTag/tree`
11. `POST /dayparting/changeTimeZone`
12. `POST /dayparting/checkDeletePermission`
13. `POST /dayparting/detailApply`
14. `POST /dayparting/downloadApply`
15. `POST /dayparting/downloadTemplate`
16. `POST /dayparting/findAmazonCampaignRules`
17. `POST /dayparting/getCampaignsName`
18. `POST /dayparting/getProfileInfos`
19. `POST /dayparting/getTemplate`
20. `POST /dayparting/LineItemIdApply`
21. `POST /dayparting/pause/client-templates`
22. `POST /dayparting/profile/campaignTag/tree`
23. `POST /dayparting/template/operation-log`
24. `POST /dayparting/template/operators`
25. `POST /dayparting/templates`
26. `POST /transcript/expire`
27. `POST /verity/campaignApplyTag`

## calendar-center-controller（1 个接口，ES 无流量）

`POST /calendar/getApplyTagIdByProfileIds`：ES 真实客户流量（排除测试账号）近 365 天为 **0 次**。虽然本账号（clientId=62）用自己的真实 `profile_ids_all` 现场验证调用可正常返回 `HTTP 200`（`data:[]`，用于确认 config 变量安全可用，非 case 素材），但按红线 1「ES 无流量禁止生成 case」，该接口未生成 case，Excel 场景覆盖列填「ES 无流量」，未创建 task 目录。

## platform-dict-controller（1 个接口，ES 无流量）

`POST /platform/queryDictByConditions`：ES 真实流量（tiktok，365 天窗口）为 **0 次**。未生成 case，未创建 task 目录，Excel 场景覆盖列填「ES 无流量」。

## 小结

- **2 条 Happy Path case**（dayparting-controller，`task-2026-09-16-02-40-08/`）：
  - `POST /findDayParting/campaign`：PASS（真实数据验证通过）
  - `POST /dayparting/templateNames`：FAIL（tiktok 平台专属确认后端缺陷，HTTP 500，留痕）
  - 连跑 2 次，结果一致（1 PASS + 1 FAIL），无幂等性问题（均为只读接口）。
- **15 个接口**因高风险写操作跳过，未做任何调用。
- **1 个接口**（`updateTemplate`）因 tiktok 平台真实历史流量为 0（含本账号自身），无可回放素材，按 ES 无流量处理，未做任何调用（含验证性调用）。
- **34 个接口**（7 GET + 27 POST）ES 无流量，未生成 case。
- **1 个接口**（`calendar/getApplyTagIdByProfileIds`）ES 无流量，仅做过安全性验证调用（未计入 case）。
- **1 个接口**（`platform/queryDictByConditions`）ES 无流量。
- 合计 2 + 15 + 1 + 34 + 1 + 1 = 54，与 `endpoints-MicroApi.json` 总数一致。

tiktok 平台在本服务上的真实使用率显著低于 amazon/citrus/dsp 等平台（仅 2 个接口有真实流量痕迹），这是当前生产环境的真实情况，未做任何数据编造以凑数。
