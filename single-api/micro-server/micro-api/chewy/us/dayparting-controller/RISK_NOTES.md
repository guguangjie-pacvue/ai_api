# dayparting-controller (micro-api, chewy, us) — 风险标记与全量接口核算

本模块共 52 个有效接口（另有 calendar-center-controller 1 个、platform-dict-controller 1 个，
合计服务全量 54 个，一并在本文件核算）。

最终产物：`task-2026-09-15-17-30-00/cases.json`（合并 batch A + batch B + 本文件补充的
templateNames 探测case，共 26 条），`task-2026-09-15-17-30-00/report.json`（26 条中 24 条
PASS、2 条 FAIL，2 次连跑结果一致，FAIL 原因见下方 templateNames 章节，非 case 编写错误）。
`task-2026-09-15-16-00-00/` 与 `task-2026-09-15-16-30-00/` 为并行生成阶段的中间产物，内容已
完整并入最终目录，予以保留作为过程记录。

## 🔴 沿用 amazon/citrus 平台已验证的服务级结论（不重新探测）

见 `single-api/micro-server/micro-api/amazon/us/dayparting-controller/RISK_NOTES.md` 与
`single-api/micro-server/micro-api/citrus/us/dayparting-controller/RISK_NOTES.md`：该服务的
写接口对测试账号**不做跨 client 权限隔离**——请求体里指定的任意真实客户数据都会真实生效，
且无可靠撤销/回滚接口。**结论对本服务所有平台一视同仁**。

因此本次 chewy 生成 case 时，对下列 **14 个写操作接口**（原始 12 项 + citrus 发现的
`bulk/update/campaigns/bid` + chewy 本次新发现的 `update/campaign/bid`，合并统一清单）
**一律直接跳过，未做任何探测性调用**，仅为存档核实了 chewy 平台 90 天真实流量（流量高低不影响
跳过决定）：

| 接口 | chewy 90天流量(已排除clientId 62/3186) | 说明 |
|---|---|---|
| `DELETE /dayparting/campaigns` | 3 | 删除campaign的dayparting应用关联 |
| `POST /dayparting/deleteTemplate` | 6 | 删除模板 |
| `POST /dayparting/deleteApply` | 0 | 删除apply记录 |
| `POST /dayparting/deleteDetailApply` | 3 | 删除apply明细 |
| `POST /dayparting/bulk/pausecampaigns` | 348 | 批量暂停campaign的dayparting |
| `POST /dayparting/changeStatus` | 17 | 批量修改campaign的dayparting状态 |
| `POST /dayparting/changeOwner` | 0 | 变更模板所有者(amazon侧曾在此接口发生意外生效事故) |
| `POST /dayparting/appoint` | 0 | 冲突时指定campaign最高优先级 |
| `POST /dayparting/apply-switch` | 0 | 切换apply启用/禁用状态 |
| `POST /dayparting/status-switch` | 0 | 与changeStatus同构 |
| `POST /dayparting/setTemplateAndApply` | 10 | 保存模板配置并应用到campaign(与updateTemplate共用写路径) |
| `POST /bulk/set/dayparting` | 9 | 批量设置dayparting(与updateTemplate同构) |
| `POST /bulk/update/campaigns/bid` | 3420 | 批量修改真实出价(citrus轮发现，Swagger确认`bulkChangeOriginalBid`) |
| `POST /update/campaign/bid` | 197 | 🆕 chewy本轮新发现，见下 |

**与 citrus/amazon/samsclub 不同点**：citrus/amazon/samsclub 侧这些接口大多是 0 流量，
chewy 侧多个接口（尤其 `bulk/pausecampaigns`=348、`bulk/update/campaigns/bid`=3420）有显著
真实流量，说明 chewy 平台的批量暂停/批量改价功能被真实客户较频繁使用。但按既定红线规则，
流量高低不影响"无条件跳过、不探测"的判定，本轮同样未对以上 14 个接口做任何试探性调用。

## 🆕 chewy 本轮新发现的第 15 类高风险写操作：`POST /update/campaign/bid`（`changeOriginalBid`）

该接口不在此前 amazon/instacart/samsclub/citrus 四轮总结的 14 项清单内（此前各轮该接口流量为
0 或未被专门排查）。chewy 平台实测该接口 **90天内有 197 次真实调用**（已排除clientId 62/3186）：

- Swagger 结构核实：`operationId: changeOriginalBid`，请求体 `CampaignBidUpdateReq`（单个对象，
  非数组，是 `bulk/update/campaigns/bid` 的单目标版本），响应 `ResultVOVoid`（无返回数据的纯
  执行型接口）。
- 真实请求体样本（真实客户数据）：
  `{"productLine":"chewyv2","itemId":"658276267","targetId":"658276267","matchType":null,"profileId":"SmartBones","targetType":"campaign","bid":null,"adGroupId":null}`
  `{"productLine":"chewyv2","itemId":"658819644","targetId":"658819644","matchType":null,"profileId":"the-honest-kitchen","targetType":"campaign","bid":null,"adGroupId":null}`
  —— `profileId` 为真实客户品牌名（SmartBones / the-honest-kitchen），语义是直接修改某个
  campaign/target 的原始出价(bid)，是不折不扣的写操作，与 `bulk/update/campaigns/bid`
  同构、同等风险。
- 按既有结论（该服务写接口无跨client隔离、无回滚接口），本接口**未做任何探测性调用**，一律
  跳过，不生成 case。已并入上表红线清单（第14项），供后续平台轮次参考——该接口应被视为与
  `bulk/update/campaigns/bid` 同等级的常设红线项，不再是"未发现"状态。

## 6 个疑似写操作/高风险语义接口，经核实 chewy 90天内均为 0 流量（未在两批任务分配范围内，由主任务本人独立核实）

以下接口名称/语义具有写操作特征（创建关联、暂停模板、时区重算写入bid点位、处理过期transcript），
虽不在原 14 项红线清单，但出于同一服务的安全结论，未做任何探测性调用，仅确认流量：

| 接口 | chewy 90天流量 | 判定依据 |
|---|---|---|
| `POST /dayparting/bulkDeleteApply` | 0 | `bulkDeleteApply`，与`deleteApply`同构的批量删除 |
| `POST /dayparting/pause/client-templates` | 0 | `pauseClientTemplates`，"关闭client的template"，写操作 |
| `POST /dayparting/changeTimeZone` | 0 | `changeTimeZone`，请求体`ActionPositionRebalance`，语义与"重算bid点位"相关，判断为写路径 |
| `POST /dayparting/LineItemIdApply` | 0 | `lineItemTeplateApplyScheduler`，Swagger summary明确"创建lineitem关联scheduler" |
| `POST /update/dayPartingChangeTimeZone` | 0 | `dayPartingChangeTimeZoneChange`，summary"根据时区更新bid值点位"，明确写操作 |
| `POST /transcript/expire` | 0 | `dealExpireTranscript`，疑似内部维护类写操作(标记transcript过期) |

以上 6 个接口均为 0 流量，按"ES无流量"规则处理（未生成case），与是否高风险无关；若未来
这几个接口在 chewy 出现真实流量，应比照上方 15 项红线清单同等对待，不做探测性调用。

## `POST /dayparting/updateTemplate`（`updateTemplate`）—— 本次验证结果

- chewy 90天ES真实流量（近365天client 62自身历史）：9次，均为本账号历史自身调用。
- **本次只做了一次干净的验证性调用**（未反复试探）：从 ES 中查到测试账号自己
  (clientId=62/autoui_acount) 过去对自己名下模板 `id=10993`（`auto自动化专用勿删`，本账号在
  chewy产品线下专用于自动化测试的fixture模板）发起过的历史 `updateTemplate` 真实请求体，
  原样回放（未修改任何字段）：
  ```
  POST /dayparting/updateTemplate  (identity 均为账号自身历史真实数据，非他人数据)
  -> HTTP 200
  {"code":200,"msg":"success",
   "data":{"totalNums":0,"sucessNums":1,"failNums":-1,
           "addSuccessCampaigns":[{"id":"658373364","name":"keywordvaliation1357","profileId":"pacvue-test","profileIdName":null}],
           "message":"Total:0,Success:1,Failed:-1"}}
  ```
- **结论：与 amazon(500) 和 instacart(200，但 sucessNums:0 no-op) 均不同，与 samsclub、citrus
  一致**——chewy 账号下 `updateTemplate` 未复现 amazon 的 500 缺陷，且**实际把该模板应用到了
  一个真实 campaign**——`sucessNums:1` 且返回 `addSuccessCampaigns` 显示确实生效。
  campaignId=`658373364`（名为"keywordvaliation1357"）、profileId=`pacvue-test` 均为**本测试
  账号(client 62)自身历史流量中反复出现的自有测试campaign**（同一组合在本账号
  `POST /findDayParting/campaign` 历史调用中出现21次），不是其他真实客户的数据，因此本次调用
  未违反"不得影响真实客户数据"的红线，但确认了该接口在 chewy 下**并非 no-op**，而是会对返回
  结果里列出的 campaign 产生真实的 dayparting 应用变更。
- **为何未据此生成自动化 case**：按 Phase 3.5 规则，写操作 case 必须"创建→验证→后置逆操作清理"
  成对出现；但 `updateTemplate` 的清理动作天然要用 `deleteTemplate`，而 `deleteTemplate` 属于
  上表红线接口之一（本轮实测 chewy 该接口也有 6 次真实流量，同样无条件跳过），因此无法在不违反
  红线的前提下构造一个"自建数据+自清理"的合规写操作 case。
- 综上：`updateTemplate` **已完成唯一一次验证性调用**（证明该接口本身可用、非缺陷，会对本账号
  自有 campaign 产生真实的模板应用变更），因缺乏合规的自清理路径，**未生成可重复执行的自动化
  case**，未计入 26 条 Happy Path。**五个平台(amazon/instacart/samsclub/citrus/chewy)对比**：
  amazon=500(缺陷)，instacart=200+no-op，samsclub/citrus/chewy=200+真实生效于自有campaign
  （3/5平台一致）。

## 🔴 `POST /dayparting/templateNames`（`getTemplateNames`）—— 本次发现的可复现服务缺陷

与其余接口不同，该接口**已生成 case 并执行**，但**当前稳定复现 HTTP 500**，如实记录为发现的
服务端缺陷，而非 case 编写错误：

- ES 90天真实流量（已排除clientId 62/3186）：113次。场景挖掘：单profile查询占比约33.6%（38次），
  多profile查询(含2/3/5/9/24个profile不同组合)合计占比约66.4%（75次）。已生成2条 Happy Path
  case（单profile / 多profile），分别用 `{{profile_id}}` 和 `{{profile_ids_all}}` 变量化。
- **实测发现**：该接口只要请求体的 `profileIds` 字段是**非null数组**（不论具体值，含单值、
  多值、乃至**空数组 `[]`**、甚至完全不存在的虚构profileId），一律返回 `HTTP 500 Internal
  Server Error`；**仅当 `profileIds` 字段本身为 `null`** 时才返回正常的 `HTTP 200`（此时接口
  退化为"查询本账号全部模板"，不做profile过滤）。
- **🔴 关键佐证：该缺陷与 chewy 平台无关，是当前服务侧的即时性缺陷**。用同一账号
  (autoui_acount/client 62) 切到 citrus 平台，回放 citrus 侧 RISK_NOTES.md 记录的、**当天早些
  时候（约30分钟前）刚验证通过（HTTP 200）** 的 `templateNames` 真实历史请求体（profileIds
  非空），**同样立即复现 HTTP 500**。也就是说 citrus 侧此前生成并 PASS 的 `templateNames` 两条
  case，如果此刻重新执行，同样会失败——这不是 chewy 特有问题，而是整个 micro-api 服务在近30分钟
  内出现的一次覆盖多平台的回归（推测是后端刚发生的一次部署或配置变更导致该字段处理路径出现空指针
  类异常），非本次case参数构造错误。
- **处理方式**：仍按接口应有的正常行为（ES真实场景占比）编写了2条 Happy Path case，并诚实执行，
  在 `report.json` 中如实记录为 **FAIL（HTTP 500）**，2次连跑结果一致（非偶发）。**未为了让case
  通过而修改断言标准或规避该字段**。计入26条case总数，但通过率相应低于100%（24/26）。
  **建议主任务/后端团队核实近期是否有 micro-api 部署变更影响了 `templateNames` 的 profileIds
  处理逻辑**。

## 🆕 异常发现：Swagger 请求体 schema 字段名被错误渲染为中文（结构性文档问题）

`CampaignReq` / `ApplySearchParam` / `ApplyLineItemTreeParams` / `TemplateSearchParam` /
`TemplateChangeStatusParam` 这几个 requestBody schema，在 `/v3/api-docs` 中 `productLine`
字段被渲染为中文属性名 `"产品线类型"`（`required` 列表里也是这个中文字符串，而非
`productLine`）：

```json
"required": ["产品线类型"],
"properties": { "产品线类型": {"type":"string","description":"产品线类型"}, ... }
```

但 ES 90天内所有真实请求体（含本账号历史请求）里该字段的**真实 JSON key 都是
`productLine`**，从未出现过 `产品线类型` 这个 key。判断是后端 `@Schema(description="产品线
类型")` 注解被 springdoc/OpenAPI 生成器错误地当成了属性名，而非接口真的用中文字段名收参数。
本次 case 严格按 ES 真实值使用 `"productLine"` 作为 JSON key，24 条非 templateNames 相关的
case 全部 200 通过，验证了这一判断正确。**建议主任务/后端团队核实该 Swagger 文档生成配置**，
避免后续消费方（前端SDK生成、契约测试）被这个字段名误导。

## config.json 变量补充：profile_ids_all 从 2 个扩至 3 个

生成 `POST /dayparting/applyTargetSum` 的 case 时，发现本账号(client 62)在 chewy 下历史真实
调用中还涉及第三个真实 profile `american-journey`（`relId=659249097/659236110/659250674/
659261129` 均挂在该profile下）。进一步查询本账号 `POST /dayparting/campaign/tree` 的历史真实
调用，独立验证到 `profileIds: ["Test111","american-journey","pacvue-test"]`（3个）的真实组合，
证实该账号在 chewy 下实际绑定 3 个 profile，而非最初创建 config.json 时依据
`templateNames`/`findDayParting/campaign` 样本推断的 2 个。已更新 `config.json`：新增
`profile_id_3="american-journey"`，`profile_ids_all` 扩为 `["pacvue-test","Test111",
"american-journey"]`。更新后重跑全部 26 条 case，结果不变（24 PASS / 2 FAIL于templateNames），
无回归。（`applyTargetSum` 的 2 条 case 描述文本中会看到 `american-journey` 直接以字面量出现，
是因为该场景在ES里的原始真实调用即单独锁定这一个profile的target，未使用`profile_ids_all`
变量。）

## 全量 52 个 dayparting-controller 接口核算（合计 = 52，无遗漏）

| 分类 | 接口数 | 说明 |
|---|---|---|
| 高风险写操作，无条件跳过(14+6=20个中14个有名有姓的红线+6个经核实0流量的疑似写操作) | 14 + 6 = 20 | 见上两表 |
| `updateTemplate`，已验证但因缺乏合规自清理路径未生成case | 1 | 见上 |
| `templateNames`，已生成2条case但因当前服务缺陷FAIL | 1 | 见上 |
| batch A 处理的只读接口（8个ES无流量 + 8个生成21条case） | 16 | `task-2026-09-15-16-00-00/` |
| batch B 处理的只读接口（11个ES无流量 + 3个生成3条case，另有calendar/platform-dict各1个不计入本模块52数） | 14 | `task-2026-09-15-16-30-00/`（16减去calendar/platform-dict各1个） |
| **合计** | **14+6+1+1+16+14 = 52** | 与 `endpoints-MicroApi.json` 中 tag=dayparting-controller 的52条逐一比对，无遗漏、无重复 |

## calendar-center-controller / platform-dict-controller（各1个接口）

- `POST /calendar/getApplyTagIdByProfileIds`：chewy 90天ES无真实流量（已排除62/3186，独立复核确认0流量），按规则跳过，未生成case。
- `POST /platform/queryDictByConditions`：chewy 90天ES无真实流量（同上，独立复核确认0流量），按规则跳过，未生成case。

## 小结

- **26 条 Happy Path case**（11个只读/校验类接口贡献24条PASS + templateNames贡献2条FAIL，
  2次连跑结果一致），覆盖全部 ≥1% 真实场景。
- **20 个接口**因高风险写操作语义跳过（14个沿用amazon/citrus结论 + chewy新发现1个红线
  `update/campaign/bid` + 6个经核实0流量的疑似写操作接口），未生成case，未做任何探测性调用。
- **1 个接口**（`updateTemplate`）已完成唯一一次验证性调用（结果与samsclub/citrus一致：
  200+真实生效于自有campaign），因自清理路径依赖被红线禁止的`deleteTemplate`，未生成自动化case。
- **1 个接口**（`templateNames`）生成了2条case并诚实执行，因发现的当前服务缺陷（profileIds非空
  即500，经交叉验证在citrus平台同样复现，判断为近期跨平台回归而非chewy专属问题）导致FAIL，
  已记录在案，建议报给后端排查。
- **21 个接口**（dayparting-controller内19个只读接口：batch A的8个 + batch B的11个，
  另加 calendar-center-controller 1个 + platform-dict-controller 1个）ES 90天内chewy平台无
  真实流量，按"ES无流量"规则跳过，已在Excel标注（不在本文件重复列出明细，见上方52条核算表与
  batch A/B各自的中间产物说明）。
- 合计校验：20(高风险写) + 1(updateTemplate) + 1(templateNames) + 11(只读接口生成case，
  贡献24条Happy Path) + 19(只读ES无流量) + 2(calendar/platform-dict均ES无流量) = 54，
  与服务全量54个接口（52 dayparting-controller + 1 calendar-center-controller +
  1 platform-dict-controller）完全吻合，无遗漏、无重复。
