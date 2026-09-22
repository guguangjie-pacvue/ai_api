# report-controller (chewy, us) — 风险标注 / 跳过说明

生成时间：2026-09-14

## ES 无流量跳过（10 个接口）

以下 10 个 `/report/*` POST 接口（Profitero 品牌/竞品报表相关）按 `body.productLine.keyword: chewyv2`
过滤，近 90 天命中数均为 **0**：

| 接口 |
|---|
| POST /report/BrandEventList |
| POST /report/CompetitorBrandSummary |
| POST /report/ExecutionRecordSummary |
| POST /report/getAllBrands |
| POST /report/getAllProfiteroRules |
| POST /report/getAllProfiteroRulesApplies |
| POST /report/getAsins |
| POST /report/getDailyRuleData |
| POST /report/getSignals |
| POST /report/MyBrandCountSummary |

即 chewy 平台从未有客户配置过 Profitero 品牌报表数据源。按铁律「ES 无流量禁止生成 cases.json、
禁止执行」，以上 10 个接口本次未生成 case、未执行，仅在 Excel 标注「ES 无流量」。

## 风险跳过（2 个接口）

- **GET /report/syncBrands**
- **GET /report/syncTables**

两接口均无 Swagger 声明参数，ES 近 90 天样本显示其 `queryString` 均为
`env=k8s-Production-pacvue-custom-job-<pod名>`（实测抽样确认，与 kroger/target 平台此前的判断
完全一致），即调用方是 Kubernetes 生产环境的**内部定时任务/custom-job Pod**，而非用户交互触发的
前端请求：

1. 接口语义是触发 Profitero 品牌/表数据的全局同步任务，作用范围不限定于单个 client/productLine，
   而是刷新后端共享的数据仓库同步状态。
2. 调用方本就是生产环境的定时 Pod，说明这是运维/后台调度接口，不是被前端页面正常触发的用户功能。
3. 无法确认在测试环境重复触发是否会与生产环态的同步调度产生冲突（如触发重复同步、误刷新生产数据表）。

按任务要求，即使 ES 显示有真实流量，此类运维/管理类接口也应跳过，不生成 case、不执行。

## 结论

本模块 13 个接口中，仅 `GET /profitero/getProfiteroCountryList`（无入参、不区分平台、纯参考数据
查询）生成并执行了 case。其余 12 个接口：10 个因 ES 无流量跳过，2 个（syncBrands/syncTables）
因运维类风险跳过，均未生成 cases.json、未执行。
