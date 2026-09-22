# share-pass-controller (citrus, us) — 未生成/未执行接口说明

生成时间：2026-09-14

本模块 9 个接口中，仅 `GET /sharePass/creators`、`GET /sharePass/getAccounts` 生成并执行了 case（无入参、
不区分平台、无数据归属风险，见 `task-2026-09-14-09-22-31/`）。其余 7 个接口本次均未生成 cases.json、未执行，
原因分两类：

## 一、ES 无流量跳过（4 个接口，body 确实携带 productLine 字段，citrus 分桶为 0）

以下 4 个接口的真实请求体（虽然 `create`/`list` 未在 Swagger `SharePassCreateReq`/`SharePassListReq` 中声明，
但抽取 ES 真实样本后发现请求体运行时实际携带 `productLine`；`getRuleIdsFromSharePass`/`getSharePlatforms` 则在
Swagger `SharePassParams`/`SharePlatformReq` 中已声明该字段）均可按 `body.productLine.keyword` 做平台归因。
近 90~180 天全量命中数与平台分桶如下，citrus 均为 0：

| 接口 | 命中总数 | 平台分桶(doc_count) |
|---|---|---|
| POST /sharePass/create | 167 (180d) | amazon 119 / dsp 29 / instacart 5 / target 4 / doordash 3 / krogerv3 3 / tiktok 3 / walmart 1 |
| POST /sharePass/getRuleIdsFromSharePass | 128 (180d) | amazon 4 / instacart 2 / dsp 1 |
| POST /sharePass/getSharePlatforms | 321 (180d) | amazon 301 / dsp 11 / walmart 7 / instacart 2 |
| POST /sharePass/list | 449 (180d，90d 内 216) | amazon / dsp / walmart / tiktok / instacart / target（citrus 未出现） |

即 citrus 平台下 client_id=62 (QA 账号) 及其他所有 citrus 客户均从未产生过任何 SharePass 创建/查规则ID/查可分享
平台/查列表的真实调用。按铁律「ES 上查不到真实流量的接口绝对不能生成 case」，以上 4 个接口本次未生成 case、未
执行，仅在报告中标注「ES 无流量」，不臆造请求体。

## 二、结构性/安全性跳过（3 个接口：check / delete / edit）

这 3 个接口的请求体（`SharePassParams`、无 schema 的 `string[]`、`SharePassEditReq`）均**不含**
`productLine` 字段，`body.productLine.keyword` 聚合返回 `NO_PRODUCTLINE_FIELD`（总命中数 >0 但分桶为空），
按 `es.platform_filter.post_fallback_no_productline_field` 规则本应"视同 GET，使用全平台流量兜底"，即从
ES 流量归属角度这 3 个接口并不构成"无流量跳过"。但进一步核查发现三者均存在无法回避的安全阻塞：

- **POST /sharePass/check**（另核对 `targetProductLine` 字段分桶：amazon 104 / dsp 27 / instacart 2 /
  walmart 2，同样无 citrus）：请求体的核心参数是一个真实存在的 `sharePassId`（外加 `targetProductLine`），
  该 ID 只能来自 `/sharePass/create` 的返回值。由于 `create` 在 citrus 下是真实零流量（见上），本次未生成
  create case，因此没有任何"citrus 平台下由本次测试自己创建"的合法 sharePassId 可用。
- **POST /sharePass/delete**：物理删除操作，同样需要真实 `sharePassId`（Swagger 声明为 `string[]`）。
  ES 近 180 天命中 32 条，全部 `body` 字段未被访问日志记录（仅有 `clientId`/`@timestamp`，无法读出具体
  ID），且这些记录的 `clientId=62` 时间戳集中在 2026-09-10~2026-09-14（与本仓库其他并行平台 agent 当前
  正在跑的 create→check→edit→delete 生命周期用例时间高度吻合），判断属于其他平台并行任务自建自删的临时
  实体，并非 citrus 所有，也并非本次测试创建，不可挪用（红线：只能操作本测试自己创建的对象）。
- **POST /sharePass/edit**：状态编辑操作，同样需要真实 `sharePassId`。近 180 天命中 11 条，样本中的
  `sharePassId` 分别属于 `clientId=62/2938/3186`：其中 `clientId=62` 的几条同样与其他平台并行任务的
  创建时间戳吻合（同上，非 citrus 所有），`clientId=2938`/`3186` 明确是其他真实/其他测试客户的数据，
  修改会影响非本测试范围的对象。

**根因**：check/delete/edit 三者都依赖一个"由本次 citrus 测试自己创建的真实 sharePassId"才能安全执行
（对照 amazon 平台的处理方式：amazon 下 `create` 有真实流量，因此可以用 `{{fixture_template_id}}` 真实创建
一个 SharePass，再串联 check → getRuleIdsFromSharePass → edit → delete 在同一个 case 内完成"创建+验证+清理"
的完整生命周期，全程只操作自己新建的实体）。但 citrus 下 `create` 是真实零流量，按铁律不能为了给 check/edit/
delete 制造测试对象而凭空调用 create（这既违反"ES 无流量禁止生成/执行"，也违反"不得为了覆盖率编造请求"）。
因此 check/delete/edit 在 citrus 下没有安全的主操作输入来源，本次未生成 case、未执行。

## 结论

本模块 9 个接口：2 个（creators/getAccounts）已生成 case 并执行验证（连跑 2 次，均 2/2 PASS，无状态、天然
幂等）；4 个（create/getRuleIdsFromSharePass/getSharePlatforms/list）因 citrus 平台 ES 真实零流量跳过；
3 个（check/delete/edit）因缺少可安全操作的真实 `sharePassId`（根因是 create 零流量，且 ES 现有 sharePassId
样本均属于其他客户或其他平台并行任务自建自删的临时实体，禁止挪用）跳过。执行前后 citrus 测试账号
(client_id=62) 下未新增、未删除、未修改任何 SharePass 相关数据。

若后续 citrus 平台产生了真实的 SharePass 创建记录（client_id=62 下的真实数据），可回到本模块补齐
check/create/delete/edit/getRuleIdsFromSharePass/getSharePlatforms/list 的 case。
