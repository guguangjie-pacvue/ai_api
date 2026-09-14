# config-controller (doordash/us) — 未生成/未执行接口说明

## GET /config/getAddOn
ES `rule-api-access-*` 近90天及近180天查询均为 0 命中（全平台口径，非仅 doordash 无流量）。按 ABSOLUTE RULE（ES 无流量禁止生成 cases.json、禁止执行），本次未生成该接口的 case。

## POST /config/openAddOn
双重原因跳过：
1. **ES 无流量**：按 `body.productLine.keyword:doordash` 过滤，近90天、近180天查询均为 0 命中；该接口近180天全平台仅有 5 条真实调用，且全部为 `productLine=amazon`，无 doordash 真实调用可参考。
2. **写操作风险未清晰限定在 QA 账号范围内且不可逆**：该接口为客户端开通 Commerce Add-On 的写操作（`AddOnRequest{productLine, clientId, region}`），语义上是给目标 clientId 开通付费/权限性 Add-On；config-controller 模块内无对应的关闭/回滚接口（无 close/revoke AddOn 接口），一旦对测试账号 `{{client_id}}`(62) 执行会造成不可逆的权限状态变更，且该账号是多个测试任务共享的 QA 账号，可能影响其他并行测试。

按任务要求「若无法安全关闭/回滚，则不执行」，本次仅记录跳过原因，不生成 cases.json、不执行 run_cases.py。

（与 target 平台同模块结论一致：ES 显示该接口历史上仅有 amazon 平台真实调用，doordash 从未真实调用过，双重原因均满足跳过条件。）
