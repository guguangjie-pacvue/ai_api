# feature-usage-controller (mercado/us) — 未生成 case 说明

两个接口的请求体均使用 `platform` 字段（而非 `productLine`）标识平台，已用 `es_helper.py productline-agg` 确认字段名后，改用直接抽样比对 `platform` 取值分布（query_es.py 的内建 `--platform` 过滤走的是 `body.productLine.keyword`，对本模块无效，故手工核对样本 body 中的 `platform` 值）。

## POST /featureHealth/monthlyReport
近180天全平台真实样本（已排除测试账号 clientId 62/3186）共44条，`platform` 取值分布：instacart / amazon / walmart 三者瓜分，**0条 mercado**。属真实业务零流量（mercado 从未调用该接口），未生成 case。

## POST /featureHealth/topNClients
近180天全平台真实样本共8条，`platform` 取值：amazon(4)/walmart(3)，**0条 mercado**。同样属真实业务零流量，未生成 case。

两接口均按 ABSOLUTE RULE 1（ES 无流量禁止生成 case、禁止执行，且不得借用其他平台真实请求体填充 mercado）跳过，仅在 Excel 标注「ES 无流量」。
