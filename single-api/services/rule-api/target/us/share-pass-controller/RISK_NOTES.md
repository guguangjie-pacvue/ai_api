# share-pass-controller (target, us) — 风险标注 / 跳过说明

生成时间：2026-09-11

以下 4 个接口未生成 case、未执行，原因见下：

## 背景

`POST /sharePass/create` 的请求体含 `productLine` 字段，可按平台归因。ES 近 180 天按
`body.productLine.keyword: target` 过滤后为 **0 命中**（全平台该接口合计 88 次调用，均为
amazon/其他平台）——即 target 平台下 client_id=62 (QA 账号) 从未创建过任何 SharePass 实体。

按任务铁律：
1. `create` 本身因 ES 无流量已跳过（不得生成 case、不得执行）。
2. 不允许"借用其他平台的真实请求体在 target 下跑一遍"来填补空白（已被明确禁止）。

因此 **不存在任何 client_id=62 + target 平台下的真实 SharePass ID** 可用于测试下列 4 个
依赖已存在 SharePass 实体的接口。ES 中能查到的 sharePassId 样本全部属于其他真实客户
(clientId 如 3642/2938/2942/515/4316/37/1256 等)，与本次任务的 QA 账号 (client_id=62) 无关。

## 逐接口说明

- **POST /sharePass/check**：请求体不含 `productLine`（用的是 `targetProductLine`，真实
  样本枚举值仅见 `amazon`/`dsp`，无 target），无法归因也无法从 ES 拿到 client_id=62 的真实
  sharePassId。若要执行，只能传入其他真实客户的 sharePassId+clientId 组合，即读取/校验
  别人真实客户的数据，超出 QA 账号范围，故跳过。
- **POST /sharePass/delete**：破坏性操作(物理删除)。同上，没有 client_id=62 下的真实/可
  合法回收的 sharePassId 可用；若使用其他真实客户的 ID 则会对其真实数据造成破坏性影响，
  明确不可接受，故跳过。
- **POST /sharePass/edit**：状态变更类写操作。同上，没有可合法拥有并回滚的 sharePassId，
  若用他人真实客户 ID 会修改其真实数据状态，故跳过。
- **POST /sharePass/getRuleIdsFromSharePass**：请求体不含 `productLine`，同样只能借用其他
  真实客户的 sharePassId 才能拿到非空响应，读取的是别人客户的规则关联信息，超出 QA 账号
  范围，故跳过。

## 结论

本模块 9 个接口中，仅 `GET /sharePass/creators`、`GET /sharePass/getAccounts` 生成并执行
了 case（这两个不区分平台且无入参，无数据归属风险）。`create`/`getSharePlatforms`/`list`
按 ES 无流量规则跳过。以上 4 个接口按风险标注跳过。

若后续 target 平台产生了真实的 SharePass 创建记录（client_id=62 下的真实数据），或产品侧
明确同意为 target 平台单独创建一个专属测试用 SharePass 并落库到 QA 账号名下，可回到本模块
补齐这 4 个接口的 case。
