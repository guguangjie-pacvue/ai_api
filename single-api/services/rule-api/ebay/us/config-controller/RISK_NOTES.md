# config-controller (ebay/us) — 未生成/未执行接口说明

## GET /config/getAddOn
ES `rule-api-access-*` 近90天、近180天、近730天查询（排除测试账号 clientId 62/3186）均为 0 命中（全平台口径，非仅 ebay 无流量——该接口全平台历史上无任何真实客户调用）。按 ABSOLUTE RULE（ES 无流量禁止生成 cases.json、禁止执行），本次未生成该接口的 case。

（与 doordash、target、mercado 三平台同模块结论一致。）

## POST /config/openAddOn
双重原因跳过：
1. **ES 无流量**：按 `body.productLine.keyword:ebay` 过滤，近90天、近180天、近730天查询均为 0 命中；该接口近730天全平台（排除测试账号）仅有 12 条真实调用，`productline-agg` 显示仅 amazon(8)、walmart(2) 两个平台的调用记录，无 ebay 真实调用可参考。
2. **写操作风险未清晰限定在 QA 账号范围内且不可逆**：该接口为客户端开通 Commerce Add-On 的写操作（`AddOnRequest{productLine, clientId, region}`），语义上是给目标 clientId 开通付费/权限性 Add-On；config-controller 模块内无对应的关闭/回滚接口（无 close/revoke AddOn 接口），一旦对测试账号 `{{client_id}}`(62) 执行会造成不可逆的权限状态变更，且该账号是多个测试任务共享的 QA 账号，可能影响其他并行测试。

按任务要求「若无法安全关闭/回滚，则不执行」，本次仅记录跳过原因，不生成 cases.json、不执行 run_cases.py。

（与 doordash、target、mercado 三平台同模块结论一致：该接口历史上仅有 amazon/walmart 平台真实调用，ebay 从未真实调用过，双重原因均满足跳过条件。）

## 补充说明：ebay 平台部分接口真实流量的实际情况
与任务前提「ebay 整体 ES 流量极稀薄（730天内全平台仅约29次命中，其中仅2次来自QA测试账号）」不同，本次逐接口验证发现：`GET /config/ruleTypes` 按 productLine=ebay 归因，近730天实际有 117 条真实调用；`GET /config/actionMetrics` 按 productLine=ebay 归因，近730天有 78 条真实调用（ruleType=Keyword 77条、ruleType=Listing 1条）。这两个接口的真实流量比任务前提描述的更充分，因此均已按真实占比生成对应 case，未受"极稀薄"前提限制而强行跳过或强行造 case——具体以逐接口验证结果为准。

`GET /config/requirementMetrics` 按 productLine=ebay 过滤则为 0 命中（且该接口全平台 queryString 近99.8%为空，非 ebay 特有问题），故其 ruleType 场景采用同模块 actionMetrics 的 ebay 实测最高频值 Keyword 推断，未编造、未借用其他平台数据。

`POST /config/RuleActionMetrics` 近730天全平台仅65条真实调用且仅 amazon/dsp 两个平台，无 ebay 真实调用，按平台强制枚举规则依据 Swagger 参数定义构造 ebay 场景（与 target、mercado 处理方式一致）。
