# config-controller (target/us) — 未生成/未执行接口说明

## GET /config/getAddOn
ES `rule-api-access-*` 近90天及近365天查询均为 0 命中（全平台口径，非仅 target 无流量）。按 ABSOLUTE RULE（ES 无流量禁止生成 cases.json、禁止执行），本次未生成该接口的 case。

## POST /config/openAddOn
双重原因跳过：
1. **ES 无流量**：按 `body.productLine.keyword:target` 过滤，近90天、近180天查询均为 0 命中；该接口近180天全平台仅有 5 条真实调用，且全部为 `productLine=amazon`，无 target 真实调用可参考。
2. **写操作风险未清晰限定在 QA 账号范围内且不可逆**：该接口为客户端开通 Commerce Add-On 的写操作（`AddOnRequest{productLine, clientId, region}`），语义上是给目标 clientId 开通付费/权限性 Add-On；config-controller 模块内无对应的关闭/回滚接口（无 close/revoke AddOn 接口），一旦对测试账号 `{{client_id}}`(62) 执行会造成不可逆的权限状态变更，且该账号是多个测试任务共享的 QA 账号，可能影响其他并行测试。

按任务要求「若无法安全关闭/回滚，则不执行」，本次仅记录跳过原因，不生成 cases.json、不执行 run_cases.py。

（对照：此前 amazon/walmart 两个平台目录下的 config-controller 曾经把 amazon 平台的真实请求体直接替换 productLine 字段套用到 walmart 场景并执行，这在当前任务中已被用户明确禁止重复，target 平台本次严格避免了这一做法。）
