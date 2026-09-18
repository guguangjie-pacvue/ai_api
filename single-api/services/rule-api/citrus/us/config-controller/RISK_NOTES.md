# config-controller (citrus/us) — 未生成/未执行接口说明

本模块 10 个接口中，7 个已生成 case 并在 citrus 测试账号（client_id=62, header
productline=citrus）上执行验证。以下 3 个接口未生成 case，原因如下。

## GET /config/getAddOn

ES `rule-api-access-*` 近180天查询为 **0 命中（全平台口径，非仅 citrus 无流量）**：
`query_es.py --path /config/getAddOn --method GET --days 180 --count-only` 返回 `0 hits`。
按 ABSOLUTE RULE（ES 无流量禁止生成 cases.json、禁止执行），本次未生成该接口的 case。
（与此前 target/doordash 平台的 config-controller 结论一致：该接口全平台历史上从未被真实调用过。）

## POST /config/openAddOn

双重原因跳过：

1. **ES 无 citrus 流量**：`body.productLine.keyword` 聚合（近3650天/全部历史）显示该接口全平台仅有
   **5 条真实调用**（已排除测试账号 62/3186），且全部为 `productLine=amazon`，无 citrus 真实调用可参考。
   按红线「ES 上查不到真实流量的接口，绝对不能生成 case」，citrus 平台本次不生成。
2. **写操作风险未清晰限定在 QA 账号范围内且不可逆**：该接口为客户端开通 Commerce Add-On 的写操作
   （`AddOnRequest{productLine, clientId, region}`），语义上是给目标 clientId 开通付费/权限性 Add-On；
   config-controller 模块内无对应的关闭/回滚接口（无 close/revoke AddOn 接口），一旦对测试账号
   `{{client_id}}`(62) 执行会造成不可逆的权限状态变更，且该账号是多个测试任务共享的 QA 账号，可能影响
   其他并行测试。

按任务要求「若无法安全关闭/回滚，则不执行」，本次仅记录跳过原因，不生成 cases.json、不执行
run_cases.py。**未使用其他平台（如 amazon）的真实请求体替换 productLine 字段套用到 citrus 场景**——
这种做法（此前部分平台目录曾经这样做）在当前任务中被明确禁止，本次严格避免。

## POST /config/RuleActionMetrics

**该接口实际可按平台归因，但 citrus 无真实流量** —— 这一点与 `services.json.rule-api.es.platform_filter`
中记录的 `post_fallback_no_productline_field` 假设不同，特此记录以供核实：

- `es_helper.py productline-agg` 检查 `body.productLine.keyword` 字段返回 `NO_PRODUCTLINE_FIELD`
  （body 里确实没有该字段），若仅看这一个信号，会误判为「无法按平台归因，应按 GET 兜底用全平台流量」。
- 但实测发现该接口的 `productLine` 参数其实是通过 **queryString**（不是 body）传递的：
  `POST /config/RuleActionMetrics?productLine=xxx`（与 Swagger 声明的
  `parameters: [{name: productLine, in: query, required: true}]` 一致）。按 `queryString.keyword`
  聚合（近3650天，已排除测试账号62/3186）真实调用共 65 条：`amazon=51`、`dsp=14`，**没有 citrus**。
- 因此该接口对 citrus 而言是**真实业务性零流量**（不是"无法归因所以按全平台兜底"），按红线
  「ES 上查不到真实流量的接口，绝对不能生成 case」，本次不生成 case。

（建议后续更新 `services.json.rule-api.es.platform_filter.post_fallback_no_productline_field` 的判定逻辑，
补充 queryString 兜底检查，避免其他平台/接口重复此误判。）
