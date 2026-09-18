# report-controller (bol, us) — 风险标注 / 跳过说明

生成时间：2026-09-14

## ES 无流量跳过（10 个接口，未生成 case，未执行）

以下 10 个 `/report/*` POST 接口（Profitero 品牌/竞品报表相关）的请求体虽未在 Swagger 中声明
`productLine` 字段，但抽取 ES 真实样本后发现请求体实际都携带 `productLine`（运行时存在但文档
未登记的字段），可据此做平台归因。按 `body.productLine.keyword: bolv2` 过滤（`query_es.py
--platform bolv2`，近3650天，已排除测试账号62/3186），命中数均为 **0**：

| 接口 | bol 3650天命中 |
|---|---|
| POST /report/BrandEventList | 0 |
| POST /report/CompetitorBrandSummary | 0 |
| POST /report/ExecutionRecordSummary | 0 |
| POST /report/getAllBrands | 0 |
| POST /report/getAllProfiteroRules | 0 |
| POST /report/getAllProfiteroRulesApplies | 0 |
| POST /report/getAsins | 0 |
| POST /report/getDailyRuleData | 0 |
| POST /report/getSignals | 0 |
| POST /report/MyBrandCountSummary | 0 |

即 bol 平台下从未有客户/自动化调用过这 10 个 Profitero 品牌/竞品报表接口（与客户是否开通
Profitero 数据源 `schema: DATAMART_xxx` 绑定，bol 下无任何客户开通迹象）。按红线「ES 无流量
禁止生成 cases.json、禁止执行」，以上 10 个接口本次**未生成 case、未执行**，仅在 Excel 标注
「ES 无流量」。与 kroger/citrus 平台的同名接口结论一致。

## GET /report/syncBrands、GET /report/syncTables — 已生成 Happy Path case

两接口均无 Swagger 声明参数，ES 近90天全平台样本（各90条）显示绝大多数调用的 `queryString` 为
`env=k8s-Production-pacvue-custom-job-<pod名>`（生产环境 Kubernetes 定时任务/custom-job Pod，
每天固定时间各调用1次），不带 clientId/userId，说明这是后端定时同步任务而非用户/前端触发。

**按任务发起人明确裁定的跨平台口径「保留生成 Happy Path case」**（与 citrus 平台一致，不同于
kroger 平台此前"运维接口整体跳过"的旧结论），本次未套用 Phase 3.5 的创建+归档配对模板（语义上
是幂等的读/触发同步动作，无用户可见实体创建、无需 archive 清理），而是按 Happy Path 单步调用
（call once, assert `code:200`），并额外连续执行两次验证幂等性——**两次均 PASS**。

## 已生成的接口

GET /profitero/getProfiteroCountryList：无入参、不区分平台、纯参考数据查询，ES 近90天全平台
186次调用均为无参默认调用，唯一模式占比100%，生成并执行 case，PASS。

## 结论

本模块 13 个接口中：
- 3 个（getProfiteroCountryList / syncBrands / syncTables）生成并执行了 case，全部 PASS，
  连跑 2 次幂等一致。
- 10 个（`/report/*` POST，Profitero 品牌报表相关）因 bol 平台 ES 无流量跳过，未生成 case、
  未执行。
