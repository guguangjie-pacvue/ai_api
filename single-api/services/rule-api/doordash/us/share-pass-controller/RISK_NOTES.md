# share-pass-controller (doordash, us) — 风险标注 / 跳过说明

生成时间：2026-09-14

以下 7 个接口未生成 case、未执行，原因见下：

## 背景

`POST /sharePass/create` 的请求体含 `productLine` 字段，可按平台归因。ES 按
`body.productLine.keyword: doordash` 过滤：

- 近 90 天：0 命中
- 近 180 天：0 命中（全平台该接口合计 87 次调用，均为 amazon(64次)/dsp(23次)，无 doordash）

即 doordash 平台下从未有真实请求创建过 SharePass 实体（不区分 clientId）。

`POST /sharePass/list`、`POST /sharePass/getSharePlatforms` 同样在请求体中携带
`productLine`，按 `body.productLine.keyword: doordash` 过滤，90天/180天均为 **0 命中**。

按任务铁律：
1. `create`/`list`/`getSharePlatforms` 均因 ES 无流量（doordash）跳过（不得生成 case、不得执行）。
2. 不允许"借用其他平台的真实请求体，把 productLine 换成 doordash"来填补空白（已被明确禁止）。

因此 **不存在任何 doordash 平台下真实创建的 SharePass 实体**，也就不存在
client_id=62 (QA 账号) 在 doordash 下拥有的 sharePassId，可用于测试下列 4 个依赖已存在
SharePass 实体的接口。

## 逐接口说明

- **POST /sharePass/check**：请求体不含 `productLine`（用的是 `targetProductLine`），ES
  近180天全平台135条命中（含 clientId=62 自身发起的55条，均为此前其他平台任务留下的真实
  调用，`targetProductLine` 取值仅见 `amazon`/`instacart`/`dsp`，**无 doordash**）。没有
  targetProductLine=doordash 且归属 client_id=62 的真实 sharePassId 可用，若使用其他
  targetProductLine 的 sharePassId 测试则与"doordash 平台"名不副实，故跳过。
- **POST /sharePass/delete**：破坏性操作(物理删除)。ES 近180天全平台仅10条命中且
  body 均未被索引(delete 请求体是字符串数组，ES 未记录明细)，同上没有可合法归属
  doordash 平台且属于 client_id=62 的 sharePassId 可回收，故跳过。
- **POST /sharePass/edit**：状态变更类写操作。ES 近180天全平台仅2条命中，涉及
  sharePassId `14888826-e199-4953-9ced-9c243c6a23db`（该 ID 同时出现在
  getRuleIdsFromSharePass 样本中，targetProductLine=dsp，非 doordash 且非 client_id=62
  拥有），无 doordash 下可合法编辑并回滚的 sharePassId，故跳过。
- **POST /sharePass/getRuleIdsFromSharePass**：请求体不含 `productLine`，ES 近180天
  全平台83条命中，涉及的 sharePassId 全部归属真实客户
  (clientId 如 2942/2938/515/4316/3925/1256/4159/4066/4267/4452 等)，无一 targetProductLine
  为 doordash，也无 client_id=62 拥有的 doordash 相关记录，读取会读到别人客户的规则关联
  信息，超出 QA 账号范围，故跳过。

## 结论

本模块 9 个接口中，仅 `GET /sharePass/creators`、`GET /sharePass/getAccounts` 生成并执行
了 case（这两个不区分平台且无入参，无数据归属风险，已连续验证通过）。
`create`/`getSharePlatforms`/`list` 按 ES 无流量规则跳过（0 命中，90天与180天均确认）。
以上 4 个（check/delete/edit/getRuleIdsFromSharePass）按风险标注跳过。

若后续 doordash 平台产生了真实的 SharePass 创建记录（client_id=62 下的真实数据），或产品侧
明确同意为 doordash 平台单独创建一个专属测试用 SharePass 并落库到 QA 账号名下，可回到本模块
补齐这 4 个接口的 case（可参考 amazon 平台 `single-api/services/rule-api/amazon/us/
share-pass-controller/` 下已验证通过的完整生命周期 case：create→check→
getRuleIdsFromSharePass→edit→delete，届时需替换为 doordash 平台的真实 create 请求体）。
