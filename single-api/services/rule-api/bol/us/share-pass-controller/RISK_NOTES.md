# share-pass-controller (bol, us) — 风险标注 / 跳过说明

生成时间：2026-09-14

## 一、ES 无流量跳过（4 个接口）

以下 4 个接口的请求体确实携带 `productLine` 字段（`check`/`getRuleIdsFromSharePass`/`getSharePlatforms`
在 Swagger 中已声明该字段；`create`/`list` 虽未在 Swagger 中声明，但抽取 ES 真实样本后发现请求体运行时
实际携带 `productLine`），均可按 `body.productLine.keyword` 做平台归因。近 180 天全量命中数与平台分桶
如下，`bolv2` 均为 0：

| 接口 | 命中总数 | 平台分桶(doc_count) |
|---|---|---|
| POST /sharePass/create | 176 | amazon 119 / dsp 29 / instacart 5 / target 4 / chewyv2 3 / citrus 3 / doordash 3 / krogerv3 3 / mercado 3 / tiktok 3 / walmart 1 |
| POST /sharePass/list | 447 | amazon 381 / dsp 46 / walmart 8 / tiktok 7 / instacart 2 / target 1 |
| POST /sharePass/getRuleIdsFromSharePass | 128 | amazon 4 / instacart 2 / dsp 1 |
| POST /sharePass/getSharePlatforms | 320 | amazon 301 / dsp 11 / walmart 6 / instacart 2 |

即 bol 平台下 client_id=62（QA 账号）及其他所有 bol 客户均从未产生过任何 SharePass 创建/查列表/查规则ID/
查可分享平台的真实调用。按铁律「ES 上查不到真实流量的接口绝对不能生成 case」，以上 4 个接口本次未生成
case、未执行，仅标注「ES 无流量」，不臆造请求体。

## 二、结构性/安全性跳过（3 个接口：check / delete / edit）

这 3 个接口的请求体均**不含** `productLine` 字段（`productline-agg` 返回 `NO_PRODUCTLINE_FIELD`），
按 fallback 规则本应视同 GET 用全平台流量兜底，但进一步核查发现均存在无法回避的安全阻塞：

- **POST /sharePass/check**：核心参数是真实 `sharePassId`（外加 `targetProductLine`），只能来自
  `/sharePass/create` 的返回值。抽样近 180 天全平台样本（135 条）发现 `clientId=62` 的记录
  `targetProductLine` 均为 `instacart`/`amazon`，时间戳集中在 2026-09-04~2026-09-10，与本仓库其他
  并行平台 agent 的 create→check→edit→delete 生命周期用例时间吻合，判断属于其他平台并行任务自建自删
  的临时实体，非 bol 所有、也非本次测试创建，不可挪用。且 `/sharePass/create` 本身在 bol 下是真实零
  流量（见上表），没有"由本次 bol 测试自己创建"的合法 sharePassId 可用于 check 自身独立成 case
  （区别于 template-controller 模块中把 create/delete 仅作为 getTemplateListFromSharePass 的 fixture
  bootstrap 使用，那里不代表 check/edit/delete 本身有真实 bol 流量支撑）。
- **POST /sharePass/delete**：物理删除操作，同样需要真实 `sharePassId`。近 90 天样本（40 条）同样
  未见 bol/bolv2 归属数据，且不可借用其他真实客户或其他平台并行任务的 ID。
- **POST /sharePass/edit**：状态编辑操作，同样需要真实 `sharePassId`。近 180 天样本（11 条）分别属于
  `clientId=62/2938/3186`，其中 `clientId=2938`/`3186` 明确是其他真实/其他测试客户的数据，`clientId=62`
  的记录同样与其他平台并行任务时间戳吻合，非本次 bol 测试所有。

**根因**：check/delete/edit 三者都依赖一个"由本次 bol 测试自己创建的真实 sharePassId"才能安全执行，
但 `create` 本身在 bol 下真实零流量，按铁律不能为了给 check/edit/delete 制造测试对象而凭空调用
create（这既违反"ES 无流量禁止生成/执行"，也违反"不得为了覆盖率编造请求"）。因此这 3 个接口本次
未生成 case、未执行，判断标准与 kroger/citrus 的 RISK_NOTES.md 一致。

## 结论

本模块 9 个接口：2 个（`GET /sharePass/creators`、`GET /sharePass/getAccounts`）已生成 case 并执行
验证（连跑 2 次，均 2/2 PASS，无入参、不区分平台、无数据归属风险，天然幂等）；4 个（create/list/
getRuleIdsFromSharePass/getSharePlatforms）因 bol 平台 ES 真实零流量跳过；3 个（check/delete/edit）
因缺少可安全操作的真实 `sharePassId`（根因是 create 零流量，且 ES 现有 sharePassId 样本均属于其他
客户或其他平台并行任务自建自删的临时实体，禁止挪用）跳过。执行前后 bol 测试账号（client_id=62）下
未新增、未删除、未修改任何 SharePass 相关数据（本模块内）。

若后续 bol 平台产生了真实的 SharePass 创建记录（client_id=62 下的真实数据），可回到本模块补齐
check/create/delete/edit/getRuleIdsFromSharePass/getSharePlatforms/list 的 case。
