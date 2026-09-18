# feature-usage-controller (bol/us) — 未生成 case 说明

两个接口的请求体均使用 `platform` 字段（而非 `productLine`）标识平台，`query_es.py` 的内建
`--platform` 过滤走的是 `body.productLine.keyword`，对本模块无效，故手工抽样比对 `body.platform`
的真实取值分布（`es_helper.py samples --no-exclude-test`，覆盖全部 clientId 含测试账号）。

## POST /featureHealth/monthlyReport

近 180 天全平台真实样本共 60 条，`platform` 取值分布：amazon 22 / instacart 18 / walmart 18 /
tiktok 2，**0 条 bol**。额外用 365 天窗口、500 条样本对 `bol`/`Bol` 做大小写不敏感的关键字扫描，
仍无一条命中。属真实业务零流量（bol 从未调用该接口），未生成 case、未执行。

## POST /featureHealth/topNClients

近 180 天全平台真实样本共 25 条，`platform`+`eventType` 组合分布：amazon+Data Impact 8 /
walmart+Data Impact 4 / instacart+Profitero 3 / instacart+Data Impact 3 / walmart+Profitero 3 /
amazon+Profitero 3 / amazon+(空) 1，**0 条 bol**。同样用 365 天/500 条样本做关键字扫描确认无
bol 记录。属真实业务零流量，未生成 case、未执行。

两接口均按红线 1（ES 无流量禁止生成 case、禁止执行，且不得借用其他平台真实请求体填充 bol）跳过，
仅在报告中标注「ES 无流量」，不臆造请求体。本结论与 mercado 平台 feature-usage-controller 的既有
判断方法一致。
