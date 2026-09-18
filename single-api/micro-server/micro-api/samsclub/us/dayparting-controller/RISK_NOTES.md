# dayparting-controller (micro-api, samsclub, us) — 风险标记接口

本模块共 52 个有效接口。其中 21 条 Happy Path case 已生成并执行
（`task-2026-09-15-13-50-41/cases.json`，21/21 PASS，连跑两遍验证幂等/稳定；
第一遍跑时其中 1 条因瞬时网络错误`Connection reset by peer`失败，重跑后稳定 21/21 PASS，非逻辑性失败）。

本文件记录：(1) 直接沿用 amazon 平台已验证结论、无条件跳过的高风险写操作接口；
(2) `updateTemplate` 在 samsclub 账号下的验证结果（与 amazon 不同、与 instacart 也不同）。

## 🔴 沿用 amazon 平台已验证的服务级结论（不重新探测）

见 `single-api/micro-server/micro-api/amazon/us/dayparting-controller/RISK_NOTES.md`：
该服务的写接口对 superAdmin/自动化测试账号**不做跨 client 权限隔离**——请求体里指定的任意真实客户数据都会真实生效，且无可靠撤销/回滚接口。amazon 一侧在排查 `changeOwner` 时已经因为一次探测性调用，意外对 clientId=3555 的真实客户模板执行了 `changeOwner`（详见该文件）。

**结论对本服务所有平台一视同仁**，因此本次 samsclub 生成 case 时，对下列 12 个写操作接口
**一律直接跳过，未做任何探测性调用**（连"看看会不会500"这种试探也没有做）：

| 接口 | samsclub 90天ES流量(已排除clientId 62/3186) | 说明 |
|---|---|---|
| `DELETE /dayparting/campaigns` | 2 | 删除campaign的dayparting应用关联 |
| `POST /dayparting/deleteTemplate` | 2 | 删除模板 |
| `POST /dayparting/deleteApply` | 0 | 删除apply记录 |
| `POST /dayparting/deleteDetailApply` | 0 | 删除apply明细 |
| `POST /dayparting/bulk/pausecampaigns` | 355 | 批量暂停campaign的dayparting(高频) |
| `POST /dayparting/changeStatus` | 2 | 批量修改campaign的dayparting状态 |
| `POST /dayparting/changeOwner` | 0 | 变更模板所有者(amazon侧曾在此接口发生意外生效事故) |
| `POST /dayparting/appoint` | 0 | 冲突时指定campaign最高优先级 |
| `POST /dayparting/apply-switch` | 0 | 切换apply启用/禁用状态 |
| `POST /dayparting/status-switch` | 0 | 与changeStatus同构 |
| `POST /dayparting/setTemplateAndApply` | 8 | 保存模板配置并应用到campaign(与updateTemplate共用写路径) |
| `POST /bulk/set/dayparting` | 303 | 批量设置dayparting(与updateTemplate同构，高频) |

以上 12 个接口的判定与 amazon/instacart 完全一致：无论 ES 流量高低，只要是这 12 个写操作，一律不生成 case、不执行、不做探测性调用。

## `POST /dayparting/updateTemplate`（`updateTemplate`）—— 本次验证结果

- samsclub 90天ES真实流量：18次（已排除clientId 62/3186噪音）。
- **本次只做了一次干净的验证性调用**（未像 amazon 那样反复试探多种 payload）：
  从 ES 中查到测试账号自己(clientId=62/autoui_acount)过去对自己名下模板 `id=45058`（`auto自动化专用勿删`，该账号在 samsclub 产品线下专用于自动化测试的 fixture 模板，与 instacart 侧同名 fixture 用法一致，ES 显示该账号历史上曾反复对此 id 调用 updateTemplate，共12次记录里有7次都是这个id）发起过的历史 `updateTemplate` 真实请求体，原样回放（未修改任何字段）：
  ```
  POST /dayparting/updateTemplate  (identity 均为账号自身历史真实数据，非他人数据)
  -> HTTP 200
  {"code":200,"msg":"success",
   "data":{"totalNums":0,"sucessNums":1,"failNums":-1,
           "addSuccessCampaigns":[{"id":"223567","name":"sp_auto gbb 0730","profileId":"12362","profileIdName":null}],
           "message":"Total:0,Success:1,Failed:-1"}}
  ```
- **结论：与 amazon(500) 和 instacart(200，但 sucessNums:0 no-op) 均不同**，samsclub 账号下 `updateTemplate` 不仅未复现 amazon 的 500 缺陷，还**实际把该模板应用到了一个真实 campaign（223567）**——`sucessNums:1` 且返回 `addSuccessCampaigns` 显示确实生效。经核实，campaignId=223567、profileId=12362 均为**本测试账号(client 62)自身历史流量中反复出现的自有数据**（同一 profileId/campaignId 组合在 `POST /findDayParting/campaign` 的本账号历史调用中出现过 74 次），不是其他真实客户的 campaign，因此本次调用未违反"不得影响真实客户数据"的红线，但确认了该接口在 samsclub 下**并非 no-op**，而是会对返回结果里列出的 campaign 产生真实的 dayparting 应用变更。
- **为何未据此生成自动化 case**：按 Phase 3.5 规则，写操作 case 必须"创建→验证→后置逆操作清理"成对出现；但 `updateTemplate` 的清理动作天然要用 `deleteTemplate`（删除/回滚模板应用），而 `deleteTemplate` 属于上表 12 个红线接口之一、被要求无条件跳过、禁止调用（不允许为了自清理而破例调用）。因此无法在不违反红线的前提下构造一个"自建数据+自清理"的合规写操作 case。
- 综上：`updateTemplate` **已完成唯一一次验证性调用**（证明该接口本身可用、非缺陷，但会对本账号自有 campaign 产生真实的模板应用变更，不是单纯查询），因缺乏合规的自清理路径，**未生成可重复执行的自动化 case**，未计入 21 条 Happy Path。三个平台（amazon/instacart/samsclub）对该接口呈现三种不同行为，已如实分别记录在各自 RISK_NOTES.md，供后续如需专门测试该接口/评估是否开放 deleteTemplate 白名单式自建数据清理时参考。

## 小结

- 21 条 Happy Path case（12 个只读/校验类接口，覆盖全部 ≥1% 真实场景，2 次连跑 100% PASS）。
- 12 个接口因高风险（与 amazon/instacart 结论一致）跳过，未生成 case，未执行，未做任何探测性调用。
- 1 个接口（`updateTemplate`）已完成唯一一次验证性调用（结果与 amazon、instacart 均不同，详见上文），但因自清理路径依赖被红线禁止的 `deleteTemplate`，未生成自动化 case。
- 18 个接口（7 个 GET + 11 个 POST）ES 90天内 samsclub 平台无真实流量，按"ES无流量"规则跳过，已在 Excel 标注（不在本文件重复列出，完整清单见 Excel `MicroApi` sheet 的 samsclub 行）。
- calendar-center-controller（1个接口）与 platform-dict-controller（1个接口）在 samsclub 平台 90天内均为 ES 无流量，按规则跳过，未生成 case。
