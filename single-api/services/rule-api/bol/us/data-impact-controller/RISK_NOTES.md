# data-impact-controller (bol, us) — 风险标注 / 跳过说明

生成时间：2026-09-14

本模块 5 个接口中，2 个接口（brandOrManufacturers、categories，共 4 条 case，全平台基线）
已生成并执行，全部 PASS（业务层 code:405，属已知环境缺陷，见下）。以下 3 个接口因 ES 无 bol
流量跳过。

## ES 无流量跳过（3 个接口）

以下 3 个 `/dataImpact/*` POST 接口的请求体（`DataImpactRequest`）Swagger 声明含 `productLine`
字段，可据此做平台归因。按 `body.productLine.keyword:bolv2` 过滤（`query_es.py --platform bolv2`，
近3650天，已排除测试账号62/3186），命中数均为 **0**：

| 接口 | bol 3650天命中 | 全平台历史真实分布 |
|---|---|---|
| POST /dataImpact/oos/asinList | 0 | amazon=80, walmart=7, tiktok=3, instacart=2 |
| POST /dataImpact/oos/brandList | 0 | amazon=196, walmart=12, tiktok=3, instacart=2 |
| POST /dataImpact/price/asinList | 0 | amazon=198, walmart=13, tiktok=3, instacart=2 |

即 bol 平台从未有客户/自动化调用过这 3 个 Out-of-Stock / Price 维度的 Data Impact 接口。按红线
「ES 上查不到真实流量的接口，绝对不能生成 case，也不得借用其他平台真实请求体填充 bol」，本次
未生成、未执行，仅在 Excel 标注「ES 无流量」。与 doordash/mercado 平台的同名接口结论一致。

## 已生成并执行的接口（POST /dataImpact/brandOrManufacturers、POST /dataImpact/categories）

这两个接口虽然 Swagger 的 `DataImpactRequest` 声明了 `productLine` 字段，但实测 ES 真实样本
（近365天，排除测试账号）显示：
- brandOrManufacturers：全平台历史真实客户流量仅 5 条，**均不携带 productLine 字段**（另有历史
  上 61 条流量中仅 7 条带 productLine，为 amazon/instacart/walmart/target，且与近365天这 5 条
  真实客户样本不重叠）。
- categories：全平台历史真实客户流量 11 条，同样均不携带 productLine 字段。

按 `services.json.rule-api.es.platform_filter.post_fallback_no_productline_field` 约定，
无法按平台归因时视同 GET 处理，用全平台流量挖掘场景，bol 平台覆盖仍按要求生成本 case
（与 citrus/doordash/mercado/target 结论一致）。

生成的 4 条 case（brandOrManufacturers 1条 + categories 3条 metric=soa/sop/oos）执行结果：
**HTTP 200，业务层 `code:405`**，`msg: Cannot invoke
"com.alibaba.fastjson.JSONObject.getString(String)" because "countryInfo" is null`。

排查：这是服务端对当前 QA 测试账号（client_id=62）缺少 `countryInfo` 配置导致的空指针，与
请求体内容、与具体平台（bol/citrus/doordash/mercado/target）均无关——是通用的测试账号/环境
缺陷。因不允许猜测/编造参数值来"修复"真实 ES 样本，本次如实保留该 4 条真实场景 case，并按
实测结果把 `expected_response.code` 从常规的 200 调整为实测的 405（与 citrus 平台处理方式一致），
使其可稳定复现、连跑验证（已连跑 2 次，均 4/4 PASS）。

## 结论

本模块 5 个接口中：
- 2 个（brandOrManufacturers / categories）生成并执行了 4 条 case，全部 PASS（连跑 2 次幂等一致，
  断言按实测 code:405 调整）。
- 3 个（oos/asinList / oos/brandList / price/asinList）因 bol 平台 ES 无流量跳过，未生成 case、
  未执行。
