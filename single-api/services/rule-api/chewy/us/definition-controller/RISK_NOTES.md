# definition-controller (chewy, us) — 未生成/未执行接口说明

生成时间：2026-09-14

本模块 51 个接口中，38 个已生成 case 并在 chewy 测试账号（client_id=62, header
productline=chewyv2）上执行验证（含 2 个已复核确认的真实后端缺陷回归用例：
`commerceRuleReport` By Rule Name 分组 405、`adtomicRules/settings` 数据库表缺失 405）。
以下 13 个接口未生成 case、未执行，原因如下。

## 一、TikTok 平台专属接口（5 个，与平台无关的结构性跳过）

路径本身即声明专属于 tiktok 产品线，chewy 平台无对应功能概念：

| 接口 |
|---|
| POST /bulk-create/tiktok/roas-explorer |
| POST /bulk-create/tiktok/smart-budget-boost |
| POST /query-rule-ids/tiktok/roas-explorer |
| POST /query-rule-ids/tiktok/smart-budget-boost |
| POST /tiktok/roas-explorer/reminder |

## 二、Adtomic 专属子系统接口（4 个，结构性跳过）

- **POST /createAdtomicRule**、**POST /definition/editAdtomicRule**、**POST /definition/delete/{adtomicRuleId}**：
  Adtomic 是独立子系统，操作对象是 adtomicRuleId，chewy 平台账号下无此类实体，且无安全的创建接口可先造出
  一次性记录再删除回滚。
- **GET /definition/adtomic/{adtomicRuleId}**：同上，无可用真实 adtomicRuleId。

说明：本模块中 `POST /definition/getAdtomicRules` 本次针对 chewy 账号实测**已可正常返回**
（code:200，空列表），与此前 kroger 平台复现 405（元素映射 null key）的结论不同，故本次已改为
正常生成 case 执行验证（详见 cases.json），不再归入本类跳过范围——这是按账号重新验证后的更新
结论，属于账号数据差异导致，非平台功能差异。

## 三、无法安全构造映射数据（2 个）

- **POST /downloadMapping**、**POST /downloadMapping/{id}**：Adtomic 映射下载功能，chewy 账号下无对应映射
  数据可供下载验证，且无创建接口可先造数据。

## 四、不安全的批量/客户级操作（2 个，无论 ES 流量如何都跳过）

- **POST /automationPauseAsins**：批量暂停 ASIN 的操作，请求体为通用 `RuleChangeRequest`
  (ruleId/ruleIds/isPaused/isDelete/clientId/userId/userName)，从字段结构无法判断其实际作用范围是否
  严格限定为调用方自身 client 的数据，也无法排除跨 client/批量副作用的可能，跳过（判断依据与
  target/kroger 平台 RISK_NOTES.md 一致，不因平台不同而变化）。
- **POST /terminatedClientRule**：按名称语义是"终止某个客户的规则"，属于客户级别的批量终止操作，无法确认
  其安全边界是否限定在 QA 账号范围内，跳过。

## 结论

以上 13 个接口本次均未生成 cases.json、未执行：5 个 TikTok 专属 + 4 个 Adtomic 专属(结构性，与账号
无关) + 2 个无可用映射数据 + 2 个高风险批量/客户级操作（getAdtomicRules 已改为正常覆盖，计入
38 个已覆盖接口，故不在此 13 个之列）。

其余 38 个接口（含 3 种真实 ruleType 分布[Product 76.3%/Bid Multiplier 14.4%/Campaign 9.3%]的规则
创建场景、完整规则生命周期链、bulkCreateRule、addAppliedObjBySeparateRule、getRuleViewList 单/多
ruleId 查询、6 种 calculateNextExecutionTime 频率场景等全部写操作）均已在 chewy 测试账号上生成
case 并执行验证，写操作 case 均已验证连跑 2 次结果一致（幂等，前后两次报告完全相同：37 PASS / 2
FAIL[已知缺陷]），执行完成后账号下规则数量已确认归零（`definition/getRule` 全 mode 下
`totalCount:0`），未在测试账号留下任何残留数据。

## chewy 账号与 kroger 账号的关键差异

chewy 测试账号（client_id=62）在本次处理前，`definition/getRule` 全部 mode（Auto/Manual/
AutoCommerce）下 `totalCount` 均为 0，即该账号在 chewy 平台下**没有任何历史存量规则**（kroger
平台账号则有 3 条真实历史规则可复用做只读验证）。因此本次涉及"读取真实存量规则"的接口
（`GET /definition/{ruleId}`、`GET /definition/checkCustom/{ruleId}`、
`GET /definition/getRuleTargetInfo`、`POST /definition/getRuleTargetInfoByRuleIds`、
`POST /getRuleViewList`(单/多 ruleId)、`POST /definition/checkRuleName`(带 id 排除自身)）
全部改为在"规则完整生命周期"及"多 ruleId 批量查询"两个自包含 case 内，对本次自建的临时规则
做验证，验证完成后立即清理，不依赖也不产生任何持久化的存量数据。
