# definition-controller (kroger, us) — 未生成/未执行接口说明

生成时间：2026-09-11

本模块 51 个接口中，37 个已生成 case 并在 kroger 测试账号（client_id=62, header
productline=krogerv3）上执行验证（含 2 个已复核确认的真实后端缺陷回归用例：
`commerceRuleReport` By Rule Name 分组 405、`adtomicRules/settings` 数据库表缺失 405）。
以下 14 个接口未生成 case、未执行，原因如下。

## 一、TikTok 平台专属接口（5 个，与平台无关的结构性跳过）

路径本身即声明专属于 tiktok 产品线，kroger 平台无对应功能概念：

| 接口 |
|---|
| POST /bulk-create/tiktok/roas-explorer |
| POST /bulk-create/tiktok/smart-budget-boost |
| POST /query-rule-ids/tiktok/roas-explorer |
| POST /query-rule-ids/tiktok/smart-budget-boost |
| POST /tiktok/roas-explorer/reminder |

## 二、Adtomic 专属子系统接口（4 个，实测验证不适用）

- **POST /createAdtomicRule**、**POST /definition/editAdtomicRule**、**POST /definition/delete/{adtomicRuleId}**：
  Adtomic 是独立子系统，操作对象是 adtomicRuleId，kroger 平台账号下无此类实体，且无安全的创建接口可先造出
  一次性记录再删除回滚。
- **GET /definition/adtomic/{adtomicRuleId}**：同上，无可用真实 adtomicRuleId。
- **POST /definition/getAdtomicRules**：实测验证（非凭空跳过）：即使按 Swagger `RuleParam.adtomicProfileIds`
  字段传入真实 kroger profile，仍稳定返回 405 `"element cannot be mapped to a null key"`，属 Adtomic
  子系统在当前环境的已知限制，跳过。

## 三、无法安全构造映射数据（2 个）

- **POST /downloadMapping**、**POST /downloadMapping/{id}**：Adtomic 映射下载功能，kroger 账号下无对应映射
  数据可供下载验证，且无创建接口可先造数据。

## 四、不安全的批量/客户级操作（2 个，无论 ES 流量如何都跳过）

- **POST /automationPauseAsins**：批量暂停 ASIN 的操作，请求体为通用 `RuleChangeRequest`
  (ruleId/ruleIds/isPaused/isDelete/clientId/userId/userName)，从字段结构无法判断其实际作用范围是否
  严格限定为调用方自身 client 的数据，也无法排除跨 client/批量副作用的可能，跳过（判断依据与 target 平台
  RISK_NOTES.md 一致，不因平台不同而变化）。
- **POST /terminatedClientRule**：按名称语义是"终止某个客户的规则"，属于客户级别的批量终止操作，无法确认
  其安全边界是否限定在 QA 账号范围内，跳过。

## 结论

以上 14 个接口本次均未生成 cases.json、未执行：5 个 TikTok 专属 + 4 个 Adtomic 专属(含 1 个实测验证
不可用) + 2 个无可用映射数据 + 2 个高风险批量/客户级操作 + （getAdtomicRules 已计入 Adtomic 分组）。
其余 37 个接口（含 4 种真实 ruleType 分布的规则创建场景、完整规则生命周期链、bulkCreateRule、
addAppliedObjBySeparateRule 等全部写操作）均已在 kroger 测试账号上生成 case 并执行验证，写操作 case
均已验证连跑 2 次结果一致（幂等），且执行前后测试账号下的 3 条历史真实存量规则(autoTest_Adgroup /
autoTest_rule_opt_manual / dfdfd)未受任何影响。
