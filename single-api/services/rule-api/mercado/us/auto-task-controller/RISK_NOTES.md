# auto-task-controller (mercado/us) — 未生成 case 说明

## GET /task/sendManualRuleMessage
ES `rule-api-access-*` 按 `urlReferrer.keyword=/task/sendManualRuleMessage` + `method=GET` 查询（GET 无 productLine 过滤，全平台基线）：近90天、近180天均 0 命中，全索引范围内无任何真实调用记录。按 ABSOLUTE RULE 1（ES 无流量禁止生成 case、禁止执行）未生成 case。

补充：该接口语义为"手动发送规则消息"，属于会产生真实副作用的写操作/管理类接口（对应 ABSOLUTE RULE 3 要求的保守处理）；即使日后 ES 出现流量，也需先确认其真实副作用范围（是否会真的触发通知/消息投递）才能考虑生成 case，本次因零流量未进入该评估阶段。仅在 Excel 标注「ES 无流量」。
