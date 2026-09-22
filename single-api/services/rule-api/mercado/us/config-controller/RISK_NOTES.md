# config-controller (mercado/us) — 未生成/未执行接口说明

## GET /config/getAddOn
ES `rule-api-access-*` 近90天及近180天查询（排除测试账号 clientId 62/3186）均为 0 命中（全平台口径，非仅 mercado 无流量）。近180天不排除测试账号的原始命中共11条，全部来自 clientId=62（QA测试账号自身流量），无任何真实客户调用。按 ABSOLUTE RULE（ES 无流量禁止生成 cases.json、禁止执行），本次未生成该接口的 case。

（与 doordash、target 两平台同模块结论一致：该接口全平台历史上无真实客户调用。）

## POST /config/openAddOn
双重原因跳过：
1. **ES 无流量**：按 `body.productLine.keyword:mercado` 过滤，近90天、近180天查询均为 0 命中；该接口近180天全平台（排除测试账号）仅有 5 条真实调用，`productline-agg` 显示仅 amazon(8)、walmart(2) 两个平台的调用记录（含测试账号流量在内共12条），无 mercado 真实调用可参考。
2. **写操作风险未清晰限定在 QA 账号范围内且不可逆**：该接口为客户端开通 Commerce Add-On 的写操作（`AddOnRequest{productLine, clientId, region}`），语义上是给目标 clientId 开通付费/权限性 Add-On；config-controller 模块内无对应的关闭/回滚接口（无 close/revoke AddOn 接口），一旦对测试账号 `{{client_id}}`(62) 执行会造成不可逆的权限状态变更，且该账号是多个测试任务共享的 QA 账号，可能影响其他并行测试。

按任务要求「若无法安全关闭/回滚，则不执行」，本次仅记录跳过原因，不生成 cases.json、不执行 run_cases.py。

（与 doordash、target 两平台同模块结论一致：该接口历史上仅有 amazon/walmart 平台真实调用，mercado 从未真实调用过，双重原因均满足跳过条件。）

## 补充说明：mercado 平台真实流量整体极稀薄
本次任务中确认 mercado 在 config-controller 各接口的真实（排除测试账号）调用量普遍个位数到十位数量级（如 GET /config/actionMetrics 按 productLine=mercado 过滤，近180天仅2条；GET /config/ruleTypes 按 productLine=mercado 过滤，近180天仅6条），与任务前提「mercado QA 测试账号流量比 doordash 稀薄（近180天约58次 vs doordash 525次）」一致。对于这类样本量极小但确实存在真实调用（非0）的接口，本次采用其真实取值（如实标注样本量极小），未套用其他平台的真实请求体数据，也未凭空编造，符合"如实逐接口验证、不强行造case"的要求。
