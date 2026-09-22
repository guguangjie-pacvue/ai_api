# health-controller (mercado/us) — 未生成 case 说明

## GET /health
ES `rule-api-access-*` 按 `urlReferrer.keyword=/health` + `method=GET` 查询（GET 无 productLine 过滤，全平台基线）：近90天、近180天均 0 命中。该接口在整个 ES 索引范围内（不区分平台）近180天内无任何真实调用记录，属于真实业务零流量（并非仅 mercado 样本少），按 ABSOLUTE RULE 1（ES 无流量禁止生成 case、禁止执行）未生成 case，仅在 Excel 标注「ES 无流量」。
