# dayparting-controller (micro-api, bol, us) — 风险标记接口

本模块共 52 个有效接口。本文件记录：(1) 平台登录别名的探测结论；(2) 沿用 amazon 已验证的服务级结论、无条件跳过的高风险写操作接口（原 13 项红线清单）；(3) **bol 平台新发现的 8 个此前未被纳入红线清单的写操作接口**（Swagger 结构核实为写操作，但 bol 平台 90 天窗口内均为 0 流量，未造成实际风险，一并记录供后续平台参考）；(4) `updateTemplate` 在 bol 账号下的验证结果。

## 🔴 平台登录别名探测结论

- `productline: "bol"` 登录 → HTTP 200，但业务层 `code: 406`，`message: "Please reach to your Pacvue contacts to activate."`；返回的 `platformCheckInfo.availablePlatforms` 列表中**根本没有 "bol"**，只有 `"bolv2"`。
- `productline: "bolv2"` 登录 → `code: 200`，成功拿到 `accessToken`，JWT `userInfo.ClientId=62`、`RootUserId=93`、`availablePlatforms` 含 `"bolv2"`。
- 交叉验证：用 `query_es.py --platform bol` 查询任意接口（如 `/dayparting/updateTemplate`）恒为 0 命中；改用 `--platform bolv2` 能查到真实命中（90天：7次clientId=62本账号历史调用 + 7次其他真实客户）。
- **结论**：登录别名与 ES `productLine.keyword` 真实值统一为 `"bolv2"`。本次交付中目录名固定为 `bol`（与 `services.json.platforms` 列表一致），但 `config.json` 的 `variables.platform`、`auth.headers.productline`、顶层 `headers.productline`、以及所有 ES 查询的 `--platform` 参数一律用 `"bolv2"`。这与 rule-api 侧 bol 平台的已知发现（`bolv2` 别名）完全一致，micro-api 侧首次得到独立验证。

## 🔴 沿用 amazon 平台已验证的服务级结论（不重新探测）

见 `single-api/micro-server/micro-api/amazon/us/dayparting-controller/RISK_NOTES.md`：
该服务的写接口对 superAdmin/自动化测试账号**不做跨 client 权限隔离**——请求体里指定的任意真实客户数据都会真实生效，且无可靠撤销/回滚接口。

**结论对本服务所有平台一视同仁**，因此本次 bol 生成 case 时，对下列 13 个写操作接口
**一律直接跳过，未做任何探测性调用**：

| 接口 | bol(bolv2) 90天ES流量(已排除clientId 62/3186) | 说明 |
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
| `POST /bulk/update/campaigns/bid` | 0 | 批量修改真实出价(citrus平台新发现的第13项，bol侧同样0流量) |

判定与 amazon/instacart/samsclub/citrus 完全一致：无论 ES 流量高低，只要是这 13 个写操作，一律不生成 case、不执行、不做探测性调用。

## 🆕 bol 平台新发现：8 个此前未被识别的写操作接口

在核对 Swagger `operationId`/请求体结构时（此前 amazon/instacart/samsclub/citrus 的调查均未把这些接口列入红线清单），发现以下 8 个接口从**接口语义和请求体结构上**明确是写操作（会修改真实数据），与"批量改出价"(`bulk/update/campaigns/bid`)属于同一风险类别。经查 bol 平台 90 天窗口内（`productLine.keyword=bolv2`）**均为 0 流量**，因此本次未造成实际暴露，但仍需和上表 13 项同等对待——**一律未做任何探测性调用，直接跳过**，并记录在此供后续平台（mercado/ebay/doordash/kroger/dsp 等）排查时参考：

| 接口 | operationId | Swagger 结构依据 | bol 90天流量 |
|---|---|---|---|
| `POST /dayparting/applyTemplate` | `applyTemplate` | 请求体与 `updateTemplate`/`setTemplateAndApply` 同构(模板对象)，响应类型 `ResultVOApplyResponseView`，是"应用模板"的写入口 | 0 |
| `POST /dayparting/LineItemIdApply` | `lineItemTeplateApplyScheduler` | summary明确"lineItem template创建lineitem关联scheduler"；请求体含 `bind: boolean`，创建/解除lineItem与scheduler的绑定关系 | 0 |
| `POST /dayparting/pause/client-templates` | `pauseClientTemplates` | summary"关闭 client 的 template"；参数为 `clientId: array`(query参数，按clientId数组批量操作)，语义是批量暂停指定client名下全部模板，风险面比单模板更大 | 0 |
| `POST /dayparting/changeTimeZone` | `changeTimeZone` | 请求体含 `sourceTimeZone`/`targetTimeZone`/`action`(DayPartingAction数组)，是"改变时区配置"的写操作 | 0 |
| `POST /update/campaign/bid` | `changeOriginalBid` | 请求体含 `bid: number`/`targetId`/`profileId`，响应 `ResultVOVoid`(纯执行型)，与`bulk/update/campaigns/bid`同构，是单条版本的真实改出价接口 | 0 |
| `POST /update/dayPartingChangeTimeZone` | `dayPartingChangeTimeZoneChange` | summary"根据时区更新bid值点位"，请求体含开始/结束时间+action数组，明确是根据时区变更改写bid点位数据 | 0 |
| `POST /transcript/expire` | `dealExpireTranscript` | 仅需 `productLine` 查询参数(无clientId/身份参数隔离)，语义是使某类"transcript"过期失效，属于状态变更写操作 | 0 |
| `POST /dayparting/bulkDeleteApply` | `bulkDeleteApply` | 与已在原13项清单中的 `deleteApply` 同构的批量删除(请求体 `DeleteAppliedAutomationReq`)，amazon侧RISK_NOTES已预先标注"若未来出现流量应按delete类风险重新评估"——bol侧核实后仍为0流量 | 0 |

**结论**：上述 8 个接口应被视为与原 13 项同等风险等级的红线接口，建议后续所有平台（含已完成的 amazon/instacart/samsclub/citrus 和后续平台）统一把红线清单从 13 项扩展为 **21 项**。本次 bol 因这些接口实际 0 流量，不影响 Excel 标注（按"ES无流量"处理），但请求体结构上的写风险已如实记录，避免未来某平台出现流量时被误当作普通查询接口生成 case。

## `POST /dayparting/updateTemplate`（`updateTemplate`）—— 本次验证结果

- bol(bolv2) 90天ES真实流量：14次（`--client-id-exclude ""`不排除时的总数），其中 7 次为本账号(clientId=62)历史自身调用，另 7 次为其他真实客户(clientId=3159/3655/2690)调用；按标准排除规则(排除62/3186噪音)统计"其他真实客户流量"为7次。
- **本次只做了一次干净的验证性调用**（未反复试探多种payload）：
  从 ES 中查到测试账号自己(clientId=62/autoui_acount)过去对自己名下模板 `id=10986`（`auto自动化专用勿删`，该账号在 bolv2 产品线下专用于自动化测试的 fixture 模板）发起过的历史 `updateTemplate` 真实请求体，原样回放（未修改任何字段）：
  ```
  POST /dayparting/updateTemplate
  -> HTTP 200
  {"code":200,"msg":"success",
   "data":{"totalNums":0,"sucessNums":1,"failNums":-1,
           "addSuccessCampaigns":[{"id":"1000000001398800","name":"test1-Auto","profileId":"218944","profileIdName":null}],
           "message":"Total:0,Success:1,Failed:-1"}}
  ```
- **结论：与 amazon(500) 和 instacart(200，但 sucessNums:0 no-op) 均不同，与 samsclub/citrus 一致**——bol 账号下 `updateTemplate` 未复现 amazon 的 500 缺陷，且**实际把该模板应用到了一个真实 campaign**——`sucessNums:1`，`addSuccessCampaigns` 显示确实生效。经核实，campaignId=`1000000001398800`(名为"test1-Auto")、profileId=`218944` 均为**本测试账号(client 62)自身历史流量中反复出现的自有测试campaign**（同一campaignId/profileId组合在本账号 `POST /findDayParting/campaign` 历史调用中出现21次(共27次样本中)，在updateTemplate历史请求体的`lineItemIds`字段中也直接出现），不是其他真实客户的 campaign，因此本次调用未违反"不得影响真实客户数据"的红线，但确认了该接口在 bol 下**并非 no-op**，而是会对返回结果里列出的 campaign 产生真实的 dayparting 应用变更。
- **为何未据此生成自动化 case**：按 Phase 3.5 规则，写操作 case 必须"创建→验证→后置逆操作清理"成对出现；但 `updateTemplate` 的清理动作天然要用 `deleteTemplate`（删除/回滚模板应用），而 `deleteTemplate` 属于上表 13 个红线接口之一、被要求无条件跳过、禁止调用（不允许为了自清理而破例调用）。因此无法在不违反红线的前提下构造一个"自建数据+自清理"的合规写操作 case。
- 综上：`updateTemplate` **已完成唯一一次验证性调用**（证明该接口本身可用、非缺陷，但会对本账号自有 campaign 产生真实的模板应用变更，不是单纯查询），因缺乏合规的自清理路径，**未生成可重复执行的自动化 case**。五个平台（amazon/instacart/samsclub/citrus/bol）中，samsclub、citrus、bol 呈现相同模式(200+真实生效于自有campaign)，amazon 为 500 缺陷，instacart 为 200+no-op，已如实分别记录在各自 RISK_NOTES.md。

## 🆕 `POST /dayparting/templateNames`：`userIds` 字段特定取值触发 HTTP 500

在为该接口生成 case 时发现：请求体的 `userIds` 字段若传入本账号 JWT 的 `RootUserId`（即 config.json 里的 `root_user_id=93`，其他平台如 citrus/samsclub 的多个只读接口都是用这个值填 `userIds`），会导致后端 **HTTP 500**（疑似按 userId 反查用户信息时空指针，93 这个 id 在 bol 产品线下的用户表里可能不存在对应记录或关联缺失）；改用测试账号**登录本身的** `user_id=18589` 填 `userIds` 后请求恢复 **HTTP 200** 正常返回。

- 已验证的对照：
  - `userIds: [93]`（root_user_id）→ `HTTP 500`
  - `userIds: [18589]`（user_id，账号自身登录ID）→ `HTTP 200`，正常返回模板列表
- **处理方式**：最终生成的 2 条 `templateNames` case 统一改用 `{{user_id}}` 而非常规使用的 `{{root_user_id}}`，已在 case `description` 里注明，2/2 PASS。
- **性质判断**：这是一个 bol 平台下 `templateNames` 接口的**功能性异常**（其余接口如 `apply`/`campaign/tree` 用 `root_user_id=93` 均正常，说明并非账号整体缺少 93 这个 userId 的数据，而是 `templateNames` 这一条写路径对 93 处理有缺陷），建议反馈给 micro-api 研发核实。本次未生成额外的"必现500"负向 case（SKILL.md 规定本次任务只做 Happy Path，不生成异常路径 case），仅在此如实记录该发现，供后续修复/复现参考。

## 最终小结（本模块 52 个接口 + calendar-center-controller 1 个 + platform-dict-controller 1 个 = 54 个接口，全部有归属）

| 类别 | 接口数 | 说明 |
|---|---|---|
| 高风险跳过（原13项，bol侧0流量） | 13 | 未生成case，未执行，未做任何探测性调用 |
| 高风险跳过（bol新发现的8项，bol侧0流量） | 8 | Swagger结构确认为写操作，未生成case，未执行，未做任何探测性调用 |
| 已验证但因缺乏合规自清理路径未生成case（`updateTemplate`） | 1 | 唯一一次验证性调用：200+真实生效于自有测试campaign(与samsclub/citrus一致) |
| 有真实ES流量 → 生成Happy Path case | 7 | 共15条case，15/15 PASS（100%），见下方明细 |
| ES无流量（dayparting-controller内） | 23 | 按规则跳过，未生成case，Excel标注"ES无流量" |
| ES无流量（calendar-center-controller，整模块） | 1 | 同上 |
| ES无流量（platform-dict-controller，整模块） | 1 | 同上 |
| **合计** | **54** | 13+8+1+7+23+1+1=54，与endpoints-MicroApi.json全量一致 |

### 7 个有真实流量的接口 case 明细（均已执行，15/15 PASS）

| 接口 | 90天真实流量(bolv2,已排除62/3186) | 场景数/case数 | 产物目录 |
|---|---|---|---|
| `POST /dayparting/apply` | 有(4种applyLevel×profile数组合) | 4 | `task-2026-09-15-21-15-00` |
| `POST /dayparting/applyTargetSum` | 有(单一模式) | 1 | `task-2026-09-15-21-15-00` |
| `POST /dayparting/campaign/tree` | 有(4种组合) | 4 | `task-2026-09-15-21-15-00` |
| `POST /dayparting/campaignTag/tree` | 有(单一模式) | 1 | `task-2026-09-15-21-15-00` |
| `POST /dayparting/checkDeletePermission` | 有(单一模式) | 1 | `task-2026-09-15-21-15-00` |
| `POST /dayparting/detailApply` | 有(2种层级) | 2 | `task-2026-09-15-21-15-00` |
| `POST /dayparting/templateNames` | 有(单/多profile2种，且发现userIds=93会500的问题，已规避) | 2 | `task-2026-09-15-15-37-49` |

`task-2026-09-15-merged/` 目录内的 cases.json/report.json 是以上两个真实task目录（21-15-00 与 15-37-49）的**汇总副本**，仅用于统一跑一次 `update_excel.py` 写入Excel（避免两次调用互相覆盖模块汇总行），不是独立的第三次执行，两个源task目录均完整保留。

### 交付物核对
- `single-api/micro-server/micro-api/bol/us/config.json`：已创建，全部变量均有ES真实流量/真实API调用依据。
- `single-api/micro-server/micro-api/bol/us/dayparting-controller/RISK_NOTES.md`：本文件。
- `single-api/micro-server/micro-api/bol/us/dayparting-controller/task-2026-09-15-21-15-00/`、`task-2026-09-15-15-37-49/`：两次真实执行的cases.json+report.json。
- `single-api/micro-server/micro-api/bol/us/dayparting-controller/task-2026-09-15-merged/`：Excel聚合用的合并副本。
- `single-api/micro-server/micro-api/swagger_modules.xlsx`：`模块汇总`sheet 3行(calendar-center-controller/dayparting-controller/platform-dict-controller) + `MicroApi`sheet 54行场景覆盖列，均已针对 `平台(Platform)=bol` 填写完毕，未触碰其他平台的行。
