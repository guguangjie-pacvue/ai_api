# dayparting-controller (micro-api, citrus, us) — 风险标记接口

本模块共 52 个有效接口。其中 18 条 Happy Path case 已生成并执行
（`task-2026-09-15-14-40-00/cases.json`，18/18 PASS，连跑两遍验证幂等/稳定）。

本文件记录：(1) 直接沿用 amazon 平台已验证结论、无条件跳过的高风险写操作接口；
(2) `updateTemplate` 在 citrus 账号下的验证结果（与 amazon 不同、与 samsclub 相同、与 instacart 不同）；
(3) citrus 特有的一个新发现——`bulk/update/campaigns/bid`（该接口在 amazon/samsclub 90天窗口内均为 0 流量，未被纳入原始红线清单，但 citrus 平台下有真实流量，经核实同样是不可安全测试的写操作，一并跳过）。

## 🔴 沿用 amazon 平台已验证的服务级结论（不重新探测）

见 `single-api/micro-server/micro-api/amazon/us/dayparting-controller/RISK_NOTES.md`：
该服务的写接口对 superAdmin/自动化测试账号**不做跨 client 权限隔离**——请求体里指定的任意真实客户数据都会真实生效，且无可靠撤销/回滚接口。amazon 一侧在排查 `changeOwner` 时已经因为一次探测性调用，意外对 clientId=3555 的真实客户模板执行了 `changeOwner`（详见该文件）。

**结论对本服务所有平台一视同仁**，因此本次 citrus 生成 case 时，对下列 12 个写操作接口
**一律直接跳过，未做任何探测性调用**：

| 接口 | citrus 90天ES流量(已排除clientId 62/3186) | 说明 |
|---|---|---|
| `DELETE /dayparting/campaigns` | 0 | 删除campaign的dayparting应用关联 |
| `POST /dayparting/deleteTemplate` | 0 | 删除模板 |
| `POST /dayparting/deleteApply` | 0 | 删除apply记录 |
| `POST /dayparting/deleteDetailApply` | 0 | 删除apply明细 |
| `POST /dayparting/bulk/pausecampaigns` | 0 | 批量暂停campaign的dayparting |
| `POST /dayparting/changeStatus` | 0 | 批量修改campaign的dayparting状态 |
| `POST /dayparting/changeOwner` | 0 | 变更模板所有者(amazon侧曾在此接口发生意外生效事故) |
| `POST /dayparting/appoint` | 0 | 冲突时指定campaign最高优先级 |
| `POST /dayparting/apply-switch` | 0 | 切换apply启用/禁用状态 |
| `POST /dayparting/status-switch` | 0 | 与changeStatus同构 |
| `POST /dayparting/setTemplateAndApply` | 0 | 保存模板配置并应用到campaign(与updateTemplate共用写路径) |
| `POST /bulk/set/dayparting` | 0 | 批量设置dayparting(与updateTemplate同构) |

以上 12 个接口在 citrus 平台 90 天窗口内（已排除 clientId 62/3186）实测均为 **0 流量**。判定与 amazon/instacart/samsclub 完全一致：无论 ES 流量高低，只要是这 12 个写操作，一律不生成 case、不执行、不做探测性调用。

## 🆕 citrus 特有新发现：`POST /bulk/update/campaigns/bid`（`bulkChangeOriginalBid`）

该接口不在原始 12 项红线清单内（amazon/samsclub 侧该接口 90 天内均为 0 流量，因此未被纳入红线调查范围）。但 citrus 平台实测该接口 **90 天内有 92 次真实调用**（已排除 clientId 62/3186），且本测试账号自身(client 62)历史上也有 4 次真实调用记录。

- Swagger 结构核实：`operationId: bulkChangeOriginalBid`，请求体为 `CampaignBidUpdateReq[]` 数组，响应类型 `ResultVOVoid`（无返回数据的纯执行型接口）。
- 真实请求体样本（本账号历史调用）：`[{"productLine":"citrus","itemId":"a1c2047b-...","targetId":"a1c2047b-...","matchType":null,"profileId":"0acae067-...","targetType":"","bid":1.5,"adGroupId":null}]` —— 语义是**直接修改某个 target 的原始出价(bid)**，是不折不扣的写操作。
- 按照上方"该服务写接口无跨client隔离、无回滚接口"的既有结论，本接口同样**未做任何探测性调用**，一律跳过，不生成 case。
- 记录此发现供后续如需扩展红线清单时参考：该接口应被视为与上方 12 项同等风险等级的第 13 个写操作红线接口，只是此前因 amazon/samsclub 均无真实流量而未被发现。

## `POST /dayparting/updateTemplate`（`updateTemplate`）—— 本次验证结果

- citrus 90天ES真实流量：7次（已排除clientId 62/3186噪音，均为本账号历史自身调用；未观察到其他真实客户对citrus的updateTemplate调用落入抽样窗口）。
- **本次只做了一次干净的验证性调用**（未像 amazon 那样反复试探多种 payload）：
  从 ES 中查到测试账号自己(clientId=62/autoui_acount)过去对自己名下模板 `id=45061`（`auto自动化专用勿删`，该账号在 citrus 产品线下专用于自动化测试的 fixture 模板，与 instacart/samsclub 侧同名 fixture 用法一致）发起过的历史 `updateTemplate` 真实请求体，原样回放（未修改任何字段）：
  ```
  POST /dayparting/updateTemplate  (identity 均为账号自身历史真实数据，非他人数据)
  -> HTTP 200
  {"code":200,"msg":"success",
   "data":{"totalNums":0,"sucessNums":1,"failNums":-1,
           "addSuccessCampaigns":[{"id":"fd943b03-40a8-4b96-be2c-804908f0b7c2","name":"AutoCitrusCampaign_20250518","profileId":"0acae067-00b9-411f-a614-09ca7bc3a12b","profileIdName":null}],
           "message":"Total:0,Success:1,Failed:-1"}}
  ```
- **结论：与 amazon(500) 和 instacart(200，但 sucessNums:0 no-op) 均不同，与 samsclub 一致**——citrus 账号下 `updateTemplate` 不仅未复现 amazon 的 500 缺陷，还**实际把该模板应用到了一个真实 campaign**——`sucessNums:1` 且返回 `addSuccessCampaigns` 显示确实生效。经核实，campaignId=`fd943b03-40a8-4b96-be2c-804908f0b7c2`(名为"AutoCitrusCampaign_20250518"，命名自带Auto前缀)、profileId=`0acae067-00b9-411f-a614-09ca7bc3a12b` 均为**本测试账号(client 62)自身历史流量中反复出现的自有测试campaign**（同一campaignId/profileId组合在本账号 `POST /findDayParting/campaign` 历史调用中出现21次，在updateTemplate历史请求体的`lineItemIds`字段中也直接出现），不是其他真实客户的 campaign，因此本次调用未违反"不得影响真实客户数据"的红线，但确认了该接口在 citrus 下**并非 no-op**，而是会对返回结果里列出的 campaign 产生真实的 dayparting 应用变更。
- **为何未据此生成自动化 case**：按 Phase 3.5 规则，写操作 case 必须"创建→验证→后置逆操作清理"成对出现；但 `updateTemplate` 的清理动作天然要用 `deleteTemplate`（删除/回滚模板应用），而 `deleteTemplate` 属于上表 12 个红线接口之一、被要求无条件跳过、禁止调用（不允许为了自清理而破例调用）。因此无法在不违反红线的前提下构造一个"自建数据+自清理"的合规写操作 case。
- 综上：`updateTemplate` **已完成唯一一次验证性调用**（证明该接口本身可用、非缺陷，但会对本账号自有 campaign 产生真实的模板应用变更，不是单纯查询），因缺乏合规的自清理路径，**未生成可重复执行的自动化 case**，未计入 18 条 Happy Path。四个平台（amazon/instacart/samsclub/citrus）中，samsclub 与 citrus 呈现相同模式(200+真实生效于自有campaign)，amazon 为 500 缺陷，instacart 为 200+no-op，已如实分别记录在各自 RISK_NOTES.md。

## 小结

- 18 条 Happy Path case（11 个只读/校验类接口，覆盖全部 ≥1% 真实场景，2 次连跑 100% PASS）。
- 12 个接口因高风险（沿用 amazon 结论，citrus 侧实测同样 0 流量）跳过，未生成 case，未执行，未做任何探测性调用。
- 1 个接口（`bulk/update/campaigns/bid`）为 citrus 特有新发现的第13个高风险写操作接口（amazon/samsclub均0流量未被发现，citrus有92次真实流量），经Swagger结构核实为bid直接修改操作，同样未做任何探测性调用，直接跳过。
- 1 个接口（`updateTemplate`）已完成唯一一次验证性调用（结果与samsclub一致：200+真实生效于自有campaign），但因自清理路径依赖被红线禁止的 `deleteTemplate`，未生成自动化 case。
- 27 个接口 ES 90天内citrus平台无真实流量，按"ES无流量"规则跳过，已在Excel标注（不在本文件重复列出）。（11+12+1+1+27=52，本模块全部52个接口分类完毕）
- calendar-center-controller（1个接口）与 platform-dict-controller（1个接口）在 citrus 平台 90天内均为 ES 无流量，按规则跳过，未生成 case。
