# config-controller (bol, us) — 风险标注 / 跳过说明

生成时间：2026-09-14

本模块 10 个接口中，7 个接口（actionMetrics 拆成 3 个真实场景，共 9 条 case）已生成并在 bol
测试账号（client_id=62, header productline=bolv2）上执行验证，全部 PASS，且连跑 2 次结果一致。
以下 3 个接口未生成 case，原因如下。

## GET /config/getAddOn

ES `rule-api-access-*` 近3650天（约10年，全平台口径，非仅 bol 无流量）查询为 **0 命中**：
`query_es.py --path /config/getAddOn --method GET --days 3650 --count-only` 返回 `0 hits`。
按红线（ES 无流量禁止生成 cases.json、禁止执行），本次未生成该接口的 case。
与 citrus/target/doordash 等平台的 config-controller 结论一致：该接口全平台历史上从未被真实调用过，
属结构性/全局跳过，与 bol 平台本身无关。

## POST /config/openAddOn

双重原因跳过：

1. **ES 无 bol 流量**：`es_helper.py productline-agg`（近3650天，未排除测试账号）显示该接口
   全平台历史仅有 **12 条真实调用**（`amazon`=8, `walmart`=2，另有 2 条落在其他桶或超出显示范围），
   **完全没有 bol/bolv2 记录**。按红线「ES 上查不到真实流量的接口，绝对不能生成 case」，bol 平台
   本次不生成。
2. **写操作风险未清晰限定在 QA 账号范围内且不可逆**：该接口是给目标 clientId 开通 Commerce
   Add-On 的写操作（`AddOnRequest{productLine, clientId, region}`），config-controller 模块内无
   对应的关闭/回滚接口，一旦对测试账号 `{{client_id}}`(62) 执行会造成不可逆的权限状态变更，且该
   账号是多个测试任务共享的 QA 账号。

未使用其他平台（如 amazon）的真实请求体替换 productLine 字段套用到 bol 场景——严格避免这种做法。

## POST /config/RuleActionMetrics

**该接口按 queryString 归因，bol 无真实流量** —— 已按任务要求专门核实 queryString 字段（而非
`body.productLine`，因为该接口 productLine 实际是 `in: query` 参数，Swagger 已确认：
`parameters: [{name: productLine, in: query, required: true}]`）：

- `es_helper.py productline-agg` 检查 `body.productLine.keyword` 字段返回
  `NO_PRODUCTLINE_FIELD`（body 里确实没有该字段）。若仅看这一个信号，会误判为"无法按平台归因，
  应按 GET 兜底用全平台流量"。
- 但实测发现该接口的 `productLine` 参数确实通过 **queryString** 传递（自建脚本
  `match_phrase: queryString` 查询验证）。按 `queryString.keyword` 聚合（近3650天，已排除测试
  账号62/3186）真实调用共 **65 条**：`amazon=51`、`dsp=14`，**没有 bol**。
- 因此该接口对 bol 而言是**真实业务性零流量**（不是"无法归因所以按全平台兜底"），按红线，
  本次不生成 case。

**结论（对应任务特别口径要求 #1）**：POST /config/RuleActionMetrics 的 queryString 平台归属
判断结果为——该接口**可以**按平台归因（走 queryString 而非 body），归因结果显示历史上仅
amazon(51)/dsp(14) 两个平台调用过，bol 从未调用过，故本次跳过。与 citrus 平台此前的判断方法完全
一致（citrus 同样发现 queryString 可归因但 citrus 也无流量）。

## 结论

本模块 10 个接口中，7 个接口生成并执行了 case（actionMetrics 贡献 3 个场景，emails /
getCommercePermission / requirementMetrics / RuleActionMetrics(GET) / ruleTypes /
supportedTimeZones 各 1 个场景，共 9 条 case），全部 PASS，连跑 2 次幂等一致。其余 3 个接口
（getAddOn / openAddOn / RuleActionMetrics POST）因 ES 无流量（getAddOn 为全平台历史 0 流量，
openAddOn 与 RuleActionMetrics POST 为 bol 平台历史 0 流量）未生成、未执行。
