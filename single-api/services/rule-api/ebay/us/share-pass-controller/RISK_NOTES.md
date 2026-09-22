# share-pass-controller (ebay, us) — 风险标注 / 跳过说明

生成时间：2026-09-14

以下 7 个接口未生成 case、未执行，原因见下：

## 背景

ebay 平台整体 ES 流量极稀薄（730 天窗口内全平台合计仅约 29 次命中），share-pass-controller
模块下按 ebay 过滤后进一步验证如下：

### 平台可归因接口（body 含 productLine）—— ES 无流量

`POST /sharePass/create`、`POST /sharePass/getSharePlatforms`、`POST /sharePass/list` 请求体
含 `productLine` 字段，按 `body.productLine.keyword: ebay` 过滤：

| 接口 | 90天命中 | 180天命中 |
|------|---------|----------|
| create | 0 | 0 |
| getSharePlatforms | 0 | 0 |
| list | 0 | 0 |

三个接口在 90 天和 180 天窗口下均为 **0 命中** —— 即 ebay 平台下从未有真实用户创建/查询过
SharePass 实体。按任务铁律：ES 业务性零结果，禁止生成 case、禁止执行，也不允许借用其他
平台的真实请求体在 ebay 下运行。

### 依赖已存在 SharePass 实体的接口 —— 无 QA 账号(clientId=62)可用数据

`POST /sharePass/check`、`POST /sharePass/delete`、`POST /sharePass/edit`、
`POST /sharePass/getRuleIdsFromSharePass` 请求体不含 `productLine`（用 `targetProductLine`
或直接不携带平台字段），无法按 ebay 过滤，只能用全平台样本核实数据归属：

| 接口 | 90天命中(全平台) | clientId=62 命中 | targetProductLine 枚举值 |
|------|------|------|------|
| check | 62 | 0 | amazon / dsp (无 ebay) |
| delete | 6 | 0 | 请求体均为空(null，参数走 path/query，未见 clientId) |
| edit | 2 | 0 | 无 productLine 字段，样本仅 clientId 无关信息 |
| getRuleIdsFromSharePass | 35 | 0 | amazon / dsp / 无 (无 ebay) |

全部样本核对后，**没有任何一条记录属于 clientId=62（QA 账号）**，真实 sharePassId 全部属于
其他真实客户（如 2942/2938/515/3642/4159/1256/3925 等）。由于 `create` 在 ebay 下已确认
ES 无流量，QA 账号也从未在其他平台下产生可安全复用的 sharePassId 归属证据，故不存在合法、
无风险的 sharePassId 可用于以下操作：

- **POST /sharePass/check**：只能借用真实客户的 sharePassId+clientId 才能拿到有效响应，
  超出 QA 账号范围，故跳过。
- **POST /sharePass/delete**：破坏性操作（物理删除）。无 clientId=62 下可合法回收的
  sharePassId，若用他人真实客户 ID 会造成不可接受的破坏性影响，故跳过。
- **POST /sharePass/edit**：状态变更类写操作。同上，无可合法拥有并回滚的 sharePassId，
  故跳过。
- **POST /sharePass/getRuleIdsFromSharePass**：只能借用他人真实客户 sharePassId 才能拿到
  非空响应，读取的是别人客户的规则关联信息，超出 QA 账号范围，故跳过。

## 结论

本模块 9 个接口中，仅 `GET /sharePass/creators`、`GET /sharePass/getAccounts` 生成并执行了
case（这两个不区分平台且无入参，无数据归属风险，2/2 PASS）。`create`/`getSharePlatforms`/
`list` 按 ES 无流量规则跳过（90天与180天均 0 命中）。`check`/`delete`/`edit`/
`getRuleIdsFromSharePass` 按数据归属风险跳过（无 clientId=62 真实样本）。

若后续 ebay 平台产生了真实的 SharePass 创建记录（clientId=62 下的真实数据），或产品侧明确
同意为 ebay 平台单独创建一个专属测试用 SharePass 并落库到 QA 账号名下，可回到本模块补齐这
7 个接口的 case。
