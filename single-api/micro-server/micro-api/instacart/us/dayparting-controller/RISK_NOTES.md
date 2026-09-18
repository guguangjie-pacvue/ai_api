# dayparting-controller (micro-api, instacart, us) — 风险标记接口

本模块共 52 个有效接口。其中 19 条 Happy Path case 已生成并执行
（`task-2026-09-15-14-30-00/cases.json`，19/19 PASS，连跑两遍验证幂等/稳定）。

本文件记录：(1) 直接沿用 amazon 平台已验证结论、无条件跳过的高风险写操作接口；
(2) `updateTemplate` 在 instacart 账号下的验证结果（与 amazon 不同）。

## 🔴 沿用 amazon 平台已验证的服务级结论（不重新探测）

见 `single-api/micro-server/micro-api/amazon/us/dayparting-controller/RISK_NOTES.md`：
该服务的写接口对 superAdmin/自动化测试账号**不做跨 client 权限隔离**——请求体里指定的任意真实客户数据都会真实生效，且无可靠撤销/回滚接口。amazon 一侧在排查 `changeOwner` 时已经因为一次探测性调用，意外对 clientId=3555 的真实客户模板执行了 `changeOwner`（详见该文件）。

**结论对本服务所有平台一视同仁**，因此本次 instacart 生成 case 时，对下列 12 个写操作接口
**一律直接跳过，未做任何探测性调用**（连"看看会不会500"这种试探也没有做）：

| 接口 | instacart 90天ES流量(已排除clientId 62/3186) | 说明 |
|---|---|---|
| `DELETE /dayparting/campaigns` | 0 | 删除campaign的dayparting应用关联 |
| `POST /dayparting/deleteTemplate` | 2 | 删除模板 |
| `POST /dayparting/deleteApply` | 1 | 删除apply记录 |
| `POST /dayparting/deleteDetailApply` | 8 | 删除apply明细 |
| `POST /dayparting/bulk/pausecampaigns` | 724 | 批量暂停campaign的dayparting(高频) |
| `POST /dayparting/changeStatus` | 0 | 批量修改campaign的dayparting状态 |
| `POST /dayparting/changeOwner` | 0 | 变更模板所有者(amazon侧曾在此接口发生意外生效事故) |
| `POST /dayparting/appoint` | 0 | 冲突时指定campaign最高优先级 |
| `POST /dayparting/apply-switch` | 0 | 切换apply启用/禁用状态 |
| `POST /dayparting/status-switch` | 0 | 与changeStatus同构 |
| `POST /dayparting/setTemplateAndApply` | 10 | 保存模板配置并应用到campaign(与updateTemplate共用写路径) |
| `POST /bulk/set/dayparting` | 34 | 批量设置dayparting(与updateTemplate同构) |

以上 12 个接口的判定与 amazon 完全一致：无论 ES 流量高低，只要是这 12 个写操作，一律不生成 case、不执行、不做探测性调用。

## `POST /dayparting/updateTemplate`（`updateTemplate`）—— 本次验证结果与 amazon 不同

- instacart 90天ES真实流量：18次（已排除clientId 62/3186噪音）。
- **本次只做了一次干净的验证性调用**（未像 amazon 那样反复试探多种 payload）：
  从 ES 中查到测试账号自己(clientId=62/autoui_acount)过去对自己名下模板 `id=23946`（`auto_temp3`，属于该账号专用的 8 个自动化 fixture 模板 `auto_temp1~8` 之一）发起过的历史 `updateTemplate` 真实请求体，原样回放（未修改任何字段）：
  ```
  POST /dayparting/updateTemplate  (identity 均为账号自身历史真实数据，非他人数据)
  -> HTTP 200, {"code":200,"msg":"success","data":{"totalNums":0,"sucessNums":0,"failNums":0,...}}
  ```
- **结论：与 amazon 平台不同，instacart 账号下 `updateTemplate` 并未复现 amazon 的 500 缺陷**，该接口本身可正常调用成功（`sucessNums:0` 是因为该 fixture 模板当前未绑定任何真实 campaign，属于预期的空应用范围，不是失败）。
- **为何未据此生成自动化 case**：按 Phase 3.5 规则，写操作 case 必须"创建→验证→后置逆操作清理"成对出现；但 `updateTemplate` 的清理动作天然要用 `deleteTemplate`（删除本次新建的模板），而 `deleteTemplate` 属于上表 12 个红线接口之一、被要求无条件跳过、禁止调用（不允许为了自清理而破例调用）。因此无法在不违反红线的前提下构造一个"自建数据+自清理"的合规写操作 case。
- 综上：`updateTemplate` **已完成唯一一次验证性调用（证明其本身可用，非缺陷）**，但因缺乏合规的自清理路径，**未生成可重复执行的自动化 case**，未计入 19 条 Happy Path。此发现（instacart 侧此接口工作正常）已如实记录，供后续如需专门测试该接口时参考（需要另行评估是否可以为 deleteTemplate 开放白名单式的自建数据清理）。

## 小结

- 19 条 Happy Path case（12 个只读/校验类接口，覆盖全部 ≥1% 真实场景，2 次连跑 100% PASS）。
- 12 个接口因高风险（与 amazon 结论一致）跳过，未生成 case，未执行，未做任何探测性调用。
- 1 个接口（`updateTemplate`）已验证可正常工作（与 amazon 不同），但因自清理路径依赖被红线禁止的 `deleteTemplate`，未生成自动化 case。
- 27 个接口（7 个 GET + 20 个 POST）ES 90天内 instacart 平台无真实流量，按"ES无流量"规则跳过，已在 Excel 标注（不在本文件重复列出，完整清单见 Excel `MicroApi` sheet 的 instacart 行）。
