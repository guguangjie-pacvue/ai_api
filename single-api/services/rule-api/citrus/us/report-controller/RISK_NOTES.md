# report-controller (citrus, us) — 风险标注 / 跳过说明

生成时间：2026-09-14

## ES 无流量跳过（10 个接口，未生成 case，未执行）

以下 10 个 `/report/*` POST 接口请求体实际携带 `body.productLine`
字段（运行时字段，Swagger 未声明，如 `{"productLine":"amazon","schema":"DATAMART_1055",...}`），
可据此做平台归因。分两种方式核实 citrus 流量：

1. `es_helper.py productline-agg`（近180天，未排除 62/3186 测试账号）：每个接口的 productLine
   聚合桶里出现的是 `krogerv3` / `krogerv3dev` / `walmart` / `amazon` / `target` / `chewyv2`
   / `tiktok` / `instacart`，总命中数在 331～1348 之间，**citrus 桶完全不存在**（哪怕 instacart
   这种仅 1 条命中的平台也出现在桶里，citrus 一次都没有）。
2. `query_es.py --platform citrus`（近180天，`body.productLine.keyword: citrus` 精确过滤）对全部
   10 个接口逐一核实，**命中数均为 0**。

| 接口 | citrus 180天命中 |
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

即 citrus 平台下从未有客户/自动化调用过这 10 个 Profitero 品牌/竞品报表接口
（这些接口与客户是否开通了 Profitero 数据源`schema: DATAMART_xxx`绑定，citrus 下无任何
客户开通迹象）。按铁律「ES 无流量禁止生成 cases.json、禁止执行」，以上 10 个接口本次
**未生成 case、未执行**，仅在 Excel 标注「ES 无流量」。

⚠️ 不确定是否为"结构性不可用"：无法从 Swagger/ES 直接证明 citrus 架构上不可能使用
Profitero 报表（例如 citrus 客户理论上也可能开通 Profitero 数据源，只是目前没人开通），
因此本次按「真实无流量」处理，不作为"结构性跳过"下定论——如后续 citrus 有客户开通
Profitero，应重新查 ES 补 case。

## syncBrands / syncTables — 已生成 Happy Path case，但请注意其运维性质

`GET /report/syncBrands`、`GET /report/syncTables` 的 ES 原始样本显示：

- 绝大多数调用的 `queryString` 为 `env=k8s-Production-pacvue-custom-job-<pod名>`
  （生产环境 Kubernetes 定时任务/custom-job Pod），每天固定时间各调用1次（近90天各90次，
  1次/天，无遗漏），不带 clientId/userId，说明这是后端定时同步任务而非用户/前端触发。
- 仅有 1 次 `clientId=62`（QA 测试账号）调用，`timeElapsed` 约 26～32 秒（syncBrands）
  即为本次自动化测试执行 run_cases.py 时留下的记录，说明该接口耗时较长，与"批量同步"
  语义一致。
- Swagger 响应结构为通用 `BaseResponseObject{code,msg,data}`，`data` 类型为 `object`
  但两接口实测返回 `data: null`（无具体数据体，仅 code:200 表示同步已触发/完成）。

**处理方式**：本次判断为「语义上是写/同步动作，但无用户可见实体创建、无需 archive 清理、
天然幂等（本身就是每天被无参数重复调用的定时任务）」，因此未套用 Phase 3.5 的
创建+归档配对模板，而是按 Happy Path 单步调用（call once, assert `code:200`），
并额外连续执行两次验证幂等性（两次均 PASS，见 report.json 与本任务的复跑记录）。

这与同服务 kroger 平台 `report-controller/RISK_NOTES.md` 中对这两个接口采取的"运维类
接口整体跳过"结论不同（kroger 判断为生产运维接口不应在自动化测试中触发，本次判断为
可安全幂等调用）。两种判断都基于同一份 ES 证据（k8s custom-job 调用模式对全平台通用，
与具体平台无关），差异在于对"是否应该在自动化测试里触发生产定时任务"这一风险容忍度的
取舍，留待人工复核统一口径。

## 结论

本模块 13 个接口中：
- 3 个（getProfiteroCountryList / syncBrands / syncTables）生成并执行了 case，全部 PASS。
- 10 个（`/report/*` POST，Profitero 品牌报表相关）因 ES 无流量跳过，未生成 case、未执行。
