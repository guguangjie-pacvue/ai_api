# auto-task-controller (bol, us) — 未生成/未执行接口说明

生成时间：2026-09-14

本模块仅 1 个接口：`GET /task/sendManualRuleMessage`。本次未生成 case、未执行。

## ES 无流量

- Swagger 未声明任何 parameters。
- GET 请求 productLine 不在 ES 中索引（queryString 为空），按规则应使用全平台流量判断，与
  平台无关。
- `es_helper.py wildcard-agg --prefix /task/ --method GET --days 180` 命中 5 次，
  `es_helper.py samples --path /task/sendManualRuleMessage --method GET --days 180
  --no-exclude-test` 显示这 5 次全部来自 clientId=62（3次）/ clientId=3186（2次），即全部为
  内部测试账号自身产生的流量，排除测试账号后真实客户调用为 **0**。
- 按红线"ES 查不到真实流量的接口（真实客户，排除62/3186后）→ 禁止生成 case、禁止执行"，本
  接口本次未生成 case、未执行。

## 结论

本模块唯一接口 ES 无真实客户流量，未生成 cases.json / report.json，本模块本次交付 0 case。
