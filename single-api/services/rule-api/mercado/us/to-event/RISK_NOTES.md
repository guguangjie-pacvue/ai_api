# to-event (mercado/us) — 未生成 case 说明

## POST /event/clearCacheTypes
ES `rule-api-access-*` 按 `urlReferrer.keyword=/event/clearCacheTypes` + `method=POST` 查询：近90天、近180天、全平台（不加 productLine 过滤）均 **0 命中**，全索引范围内无任何真实调用记录。同时该接口语义为缓存清理管理操作（对应 ABSOLUTE RULE 3 要求的保守处理），即便日后出现流量也需先评估其清理范围/副作用再决定是否生成 case。本次因零流量按 ABSOLUTE RULE 1 未生成 case、未执行。

## POST /event/getRuleCountByCampaignIds
该接口请求体含真实 `productLine` 字段（非测试流量确认存在，且带 `productLine` 时确为真实平台值，如 amazon/tiktok）。用 `body.productLine.keyword:mercado` 过滤：近180天 0 命中；用 `es_helper.py productline-agg`（不排除测试账号）核对全量分布：`total=47`，桶分布 amazon(15)/tiktok(2)，同样**无 mercado 桶**，确认包括测试账号在内都从未以 mercado 身份调用过该接口。未生成 case。

## POST /event/getRuleCountByUserIds
同上核实：`body.productLine.keyword:mercado` 过滤近180天 0 命中；`productline-agg` 全量分布 `total=10029`：amazon(9600)/walmart(143)/instacart(104)/criteo(101)/target(79)/tiktok(2)，**无 mercado 桶**。确认真实业务零流量。未生成 case。

以上3个接口按 ABSOLUTE RULE 1（ES 无流量禁止生成、禁止执行，不得借用其他平台真实请求体填充 mercado）跳过，仅在 Excel 标注「ES 无流量」。

---

## 已生成并执行的接口（POST /event/getRuleDefinition、POST /event/getRuleTypes）

这两个接口请求体经核实不含 `productLine` 字段，按规则使用全平台真实样本作为基线，与此前 target/doordash 结论一致。已生成2条 Happy Path case 并执行，**2条全部 PASS**（详见 `task-2026-09-14-11-26-52/report.json`）。
