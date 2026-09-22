# share-pass-controller (kroger, us) — 风险标注 / 跳过说明

生成时间：2026-09-11

## ES 无流量跳过（5 个接口）

以下 5 个接口在实际请求体中确实携带 `productLine` 字段（`check`/`getRuleIdsFromSharePass`/`getSharePlatforms` 在
Swagger 中已声明该字段；`create`/`list` 虽未在 Swagger 中声明，但抽取 ES 真实样本后发现请求体实际携带
`productLine`，属于运行时存在但文档未登记的字段，Swagger 结构权威性用于校验类型/必填性，不影响此处按真实字段
做平台归因）。按 `body.productLine.keyword: krogerv3`（以及兜底 `kroger`）过滤，近 90 天命中数：

| 接口 | krogerv3 命中 | kroger(字面量) 命中 |
|---|---|---|
| POST /sharePass/check | 0 | 0 |
| POST /sharePass/create | 0 | 0 |
| POST /sharePass/getRuleIdsFromSharePass | 0 | 0 |
| POST /sharePass/getSharePlatforms | 0 | 0 |
| POST /sharePass/list | 0 | 0 |

即 kroger 平台下 client_id=62 (QA 账号) 及其他所有 kroger 客户均从未产生过任何 SharePass 相关的真实调用。
按铁律「ES 无流量禁止生成 cases.json、禁止执行」，以上 5 个接口本次未生成 case、未执行，仅在 Excel 标注「ES 无流量」。

## 风险跳过（2 个接口）

- **POST /sharePass/delete**：Swagger 声明请求体为 `string[]`（sharePassId 列表），但 ES 近 90 天真实样本
  （6 条，全平台）的 `body` 字段均为空（`null`），说明该接口的真实入参不经过标准 JSON body 记录路径，无法获取
  任何真实 sharePassId 样本。同时该接口是物理删除操作，且因 `create` 本身在 kroger 下无真实流量、也没有
  client_id=62 名下任何真实存在的 kroger sharePass 实体可安全操作——若要执行只能借用其他真实客户
  (如 ES 中出现的 clientId=37/2938/858/515 等)的 sharePassId，这会删除他人真实客户的数据，明确超出 QA
  账号范围，不可接受。跳过。
- **POST /sharePass/edit**：请求体不含 `productLine`（无法平台归因），且 ES 近 90 天全平台仅 2 条真实调用，
  均属于 clientId=2938 的同一个 sharePassId（`14888826-e199-4953-9ced-9c243c6a23db`），状态在 Active/Inactive
  之间切换。没有 client_id=62 名下的真实 sharePassId 可用；若使用该真实样本 ID 会修改其他真实客户的数据状态，
  跳过。

## 结论

本模块 9 个接口中，仅 `GET /sharePass/creators`、`GET /sharePass/getAccounts` 生成并执行了 case（无入参、
不区分平台、无数据归属风险）。其余 7 个接口：5 个因 ES 无流量跳过，2 个（delete/edit）因写操作风险
（无法限定在 QA client 范围内且不可逆/无回滚）跳过，均未生成 cases.json、未执行。

若后续 kroger 平台产生了真实的 SharePass 创建记录（client_id=62 下的真实数据），可回到本模块补齐相关接口的 case。
