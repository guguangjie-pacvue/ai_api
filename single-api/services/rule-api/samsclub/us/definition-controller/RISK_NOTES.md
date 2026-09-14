# definition-controller (samsclub, us) — 未生成/未执行接口说明

生成时间：2026-09-14

本模块 51 个接口中，38 个已生成 case 并在 samsclub 测试账号（client_id=62, header
productline=samsclub）上执行验证（含 2 个已复核确认的真实后端缺陷回归用例：
`commerceRuleReport` By Rule Name 分组 405、`adtomicRules/settings` 数据库表缺失 405）。
以下 13 个接口未生成 case、未执行，原因如下（与 target/kroger/chewy 平台的判断标准一致，
结构性问题不因平台不同而变化，直接复用结论）。

## 一、TikTok 平台专属接口（5 个，与平台无关的结构性跳过）

路径本身即声明专属于 tiktok 产品线，samsclub 平台无对应功能概念：

| 接口 |
|---|
| POST /bulk-create/tiktok/roas-explorer |
| POST /bulk-create/tiktok/smart-budget-boost |
| POST /query-rule-ids/tiktok/roas-explorer |
| POST /query-rule-ids/tiktok/smart-budget-boost |
| POST /tiktok/roas-explorer/reminder |

## 二、Adtomic 专属子系统接口（4 个，结构性跳过）

- **POST /createAdtomicRule**、**POST /definition/editAdtomicRule**、**POST /definition/delete/{adtomicRuleId}**：
  Adtomic 是独立子系统，操作对象是 adtomicRuleId，samsclub 平台账号下无此类实体，且无安全的创建接口可先造出
  一次性记录再删除回滚。
- **GET /definition/adtomic/{adtomicRuleId}**：同上，无可用真实 adtomicRuleId。

## 三、无法安全构造映射数据（2 个）

- **POST /downloadMapping**、**POST /downloadMapping/{id}**：Adtomic 映射下载功能，samsclub 账号下无对应映射
  数据可供下载验证，且无创建接口可先造数据。

## 四、不安全的批量/客户级操作（2 个，无论 ES 流量如何都跳过）

- **POST /automationPauseAsins**：批量暂停 ASIN 的操作，请求体为通用 `RuleChangeRequest`
  (ruleId/ruleIds/isPaused/isDelete/clientId/userId/userName)，从字段结构无法判断其实际作用范围是否
  严格限定为调用方自身 client 的数据，也无法排除跨 client/批量副作用的可能，跳过（判断依据与
  target/kroger/chewy 平台 RISK_NOTES.md 一致，不因平台不同而变化）。
- **POST /terminatedClientRule**：按名称语义是"终止某个客户的规则"，属于客户级别的批量终止操作，无法确认
  其安全边界是否限定在 QA 账号范围内，跳过。

## 结论

以上 13 个接口本次均未生成 cases.json、未执行：5 个 TikTok 专属 + 4 个 Adtomic 专属(结构性，与账号
无关) + 2 个无可用映射数据 + 2 个高风险批量/客户级操作。

其余 38 个接口（含 5 种真实 ruleType 分布[Keyword 61.1%/Harvest Keywords 16.7%/Item 11.1%/
Bid Multiplier 5.6%/Campaign 5.6%，按近365天36条真实创建样本折算，近90天仅3条样本过少已改用
365天窗口并如实说明]的规则创建场景、完整规则生命周期链、bulkCreateRule、
addAppliedObjBySeparateRule、getRuleViewList 单/多 ruleId 查询、6 种 calculateNextExecutionTime
频率场景等全部写操作）均已在 samsclub 测试账号上生成 case 并执行验证，写操作 case 均已验证连跑 2 次
结果一致（幂等，前后两次报告完全相同：39 PASS / 2 FAIL[已知缺陷]），执行完成后账号下规则数量已确认
归零（`definition/getRule` 全 mode 下 `totalCount:0`），未在测试账号留下任何残留数据。

## 执行过程说明：一次瞬时的"规则名已存在"冲突（已排查，非用例设计问题）

首次完整执行 41 个 case 时，`POST /getRuleViewList` 多 ruleId 批量查询 case 的前两个"创建临时规则"
步骤返回 `code:500, msg:"The rule name already exists"`。排查确认：这是此前两次因会话额度限制被中断的
`run_cases.py` 执行遗留的同名规则（`TC_Samsclub_MultiView_A_Cleanup`/`_B_Cleanup`）造成的瞬时冲突——
中断发生在这些历史执行进程内部尚未跑到后置清理步骤之前。已手动查出并清理这 2 条残留规则（确认
`definition/getRule` 三种 mode 下 `totalCount` 均归零），随后完整重跑两次，均为 39 PASS / 2 FAIL
（结果完全一致），交付的 `report.json` 为清理残留后的完整重跑结果。

## samsclub 账号与其他平台账号的关键差异

samsclub 测试账号（client_id=62）在本次处理前，`definition/getRule` 全部 mode（Auto/Manual/
AutoCommerce）下 `totalCount` 均为 0，即该账号在 samsclub 平台下**没有任何历史存量规则**。因此本次
涉及"读取真实存量规则"的接口（`GET /definition/{ruleId}`、`GET /definition/checkCustom/{ruleId}`、
`GET /definition/getRuleTargetInfo`、`POST /definition/getRuleTargetInfoByRuleIds`、
`POST /getRuleViewList`(单/多 ruleId)、`POST /definition/checkRuleName`(带 id 排除自身)）
全部改为在"规则完整生命周期"及"多 ruleId 批量查询"两个自包含 case 内，对本次自建的临时规则
做验证，验证完成后立即清理，不依赖也不产生任何持久化的存量数据。

`POST /definition`(创建) 的 ruleType 真实分布近 90 天样本量过少（仅 3 条，全部为 Harvest Keywords），
改用近 365 天窗口（36 条真实样本）以获得更具代表性的分布：Keyword 61.1%/Harvest Keywords 16.7%/
Item 11.1%/Bid Multiplier 5.6%/Campaign 5.6%，5 种均 ≥1%，全部覆盖生成对应 case。
