# data-impact-controller (mercado/us) — 未生成/已知缺陷说明

## POST /dataImpact/oos/asinList
该接口请求体含真实 `productLine` 字段（可按平台归因，非 test 流量确认存在该字段）。近180天全平台真实样本（已排除测试账号）共5条，全部为 `productLine=amazon`(4)/`walmart`(1)，**0条 mercado**。按 ABSOLUTE RULE 1（ES 无流量禁止生成、禁止执行，且不得借用其他平台真实请求体填充 mercado）未生成该接口的 case。

## POST /dataImpact/oos/brandList
同上：近180天全平台真实样本共37条，全部为 `amazon`(36)/`walmart`(1)，0条 mercado。未生成 case。

## POST /dataImpact/price/asinList
同上：近180天全平台真实样本共40条，全部为 `amazon`(38)/`walmart`(2)，0条 mercado。未生成 case。

---

## 已生成并执行的接口（POST /dataImpact/brandOrManufacturers、POST /dataImpact/categories）

这两个接口请求体经核实**不含** `productLine`/`clientId` 字段（近180天全平台真实非测试流量样本抽查确认），无法按平台归因，按规则使用全平台真实样本作为基线（与 GET 同等对待）——与此前 target/doordash 平台执行时结论一致，样本内容也相同（同一份全局 ES 数据，无平台维度可切分）。已生成 4 条 Happy Path case 并执行。

**执行结果：4 条全部 FAIL**（HTTP 200，业务 `code:405`）：
```
msg: Cannot invoke "com.alibaba.fastjson.JSONObject.getString(String)" because "countryInfo" is null
```

排查：这是服务端对当前 QA 测试账号（client_id=62, productline=mercado）缺少 `countryInfo` 配置导致的空指针，与请求体内容无关——同一现象在 target（`single-api/services/rule-api/target/us/data-impact-controller/task-2026-09-11-14-25-07/report.json`）和 doordash（`single-api/services/rule-api/doordash/us/data-impact-controller/task-2026-09-14-09-13-28/report.json`）执行同一 case 时均复现，确认是与平台无关的通用服务端/测试账号环境缺陷。因不允许猜测/编造参数值来"修复"真实 ES 样本，本次如实保留该4条真实场景 case 及其 FAIL 结果（`single-api/services/rule-api/mercado/us/data-impact-controller/task-2026-09-14-11-26-52/report.json`），视为已知环境缺陷，未做进一步处理。
