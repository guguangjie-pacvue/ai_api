# data-impact-controller (doordash/us) — 未生成/未执行接口说明

## POST /dataImpact/oos/asinList
该接口请求体含 `productLine` 字段（可按平台归因）。ES `rule-api-access-*` 按 `body.productLine.keyword:doordash` 过滤，近90天、近180天查询均为 0 命中。近180天全平台真实调用共5条，全部为 `productLine=amazon`(4) / `walmart`(1)，无 doordash 真实调用可参考。按 ABSOLUTE RULE（ES 无流量禁止生成 cases.json、禁止执行，且不得借用其他平台真实请求体填充），本次未生成该接口的 case。

## POST /dataImpact/oos/brandList
同上：`productLine` 字段按 doordash 过滤 90天/180天均 0 命中；近180天全平台共37条，全部为 `amazon`(36) / `walmart`(1)，无 doordash 数据。未生成 case。

## POST /dataImpact/price/asinList
同上：`productLine` 字段按 doordash 过滤 90天/180天均 0 命中；近180天全平台共40条，全部为 `amazon`(38) / `walmart`(2)，无 doordash 数据。未生成 case。

---

## 已生成但执行失败的说明（POST /dataImpact/brandOrManufacturers、POST /dataImpact/categories）

这两个接口请求体不含 `productLine`/`clientId` 字段，无法按平台归因，按规则使用全平台真实样本作为基线（与 GET 同等对待），已生成 4 条 Happy Path case 并执行。**执行结果 4 条全部 FAIL**：服务端返回 HTTP 200 但业务 `code:405`，`msg: "Cannot invoke \"com.alibaba.fastjson.JSONObject.getString(String)\" because \"countryInfo\" is null"`。

排查：这是服务端对当前 QA 测试账号（client_id=62, doordash）缺少 `countryInfo` 配置导致的空指针，与请求体内容无关（同样的现象此前在 target 平台执行同一 case 时也复现，见 `single-api/services/rule-api/target/us/data-impact-controller/task-2026-09-11-14-25-07/report.json`）。因不允许猜测/编造参数值来"修复"真实 ES 样本，本次如实保留该 4 条真实场景 case 及其 FAIL 结果，视为已知服务端/测试账号配置缺陷，未做进一步处理。
