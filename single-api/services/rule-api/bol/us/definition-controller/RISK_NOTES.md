# definition-controller (bol, us) — 未生成/未执行接口说明

生成时间：2026-09-14

本模块 51 个接口中，**16 个**已生成 case 并在 bol 测试账号（client_id=62，header
productline=bolv2）上执行验证，共 **16 条 case、连跑 2 次全部 PASS（16/16, 100%）**。
以下 **35 个**接口未生成 case、未执行，原因分四类：14 个结构性跳过（与平台无关，沿用
kroger/citrus 已有判断）、21 个 ES 无 bol 真实流量、2 个"有真实流量但为数据安全暂缓"。

---

## 一、结构性跳过（14 个，沿用 kroger/citrus 判断，与平台无关）

判断依据见 `single-api/services/rule-api/kroger/us/definition-controller/RISK_NOTES.md`
与 `single-api/services/rule-api/citrus/us/definition-controller/RISK_NOTES.md`：TikTok 专属
路径（5）、Adtomic 专属子系统（5：createAdtomicRule/editAdtomicRule/delete/{id}/
GET adtomic/{id}/getAdtomicRules）、无法安全构造映射数据（2：downloadMapping 系列）、不安全的
批量/客户级操作（2：automationPauseAsins/terminatedClientRule）。本次未重新独立核查，
按任务说明"结构性判断可直接复用"处理。

| 接口 |
|---|
| POST /bulk-create/tiktok/roas-explorer |
| POST /bulk-create/tiktok/smart-budget-boost |
| POST /query-rule-ids/tiktok/roas-explorer |
| POST /query-rule-ids/tiktok/smart-budget-boost |
| POST /tiktok/roas-explorer/reminder |
| POST /createAdtomicRule |
| POST /definition/editAdtomicRule |
| POST /definition/delete/{adtomicRuleId} |
| GET /definition/adtomic/{adtomicRuleId} |
| POST /definition/getAdtomicRules |
| POST /downloadMapping |
| POST /downloadMapping/{id} |
| POST /automationPauseAsins |
| POST /terminatedClientRule |

## 二、ES 查无 bol 真实流量（21 个，逐接口独立核查，排除 clientId 62/3186）

### 2.1 POST 接口 body 含 productLine 字段，但无 bolv2 桶（14 个）

用 `es_helper.py productline-agg` 逐接口查询近 90 天 `body.productLine.keyword` 分桶，
以下接口存在其它平台（amazon/target/walmart/citrus/instacart/kroger/chewy/kevel 等）
真实流量桶，但**桶列表中不存在 bolv2**（说明 bol 客户从未真实调用过），故判定 bol 平台
下 ES 无真实流量：

| 接口 | 备注 |
|---|---|
| POST /definition/getRule | 有 amazon/target/walmart/citrus/doordash/krogerv3/chewyv2/kevel，无 bolv2（本次仅作为写操作 case 的内部辅助查询步骤被调用，见下方"特别说明"，不作为独立覆盖接口） |
| POST /getRuleViewList | 仅 kevel(6) 有真实流量 |
| POST /definition/calculateNextExecutionTime | 有 amazon/chewyv2/walmart/dsp/target/instacart/krogerv3/doordash/criteo/openai/tiktok，无 bolv2 |
| POST /definition/checkRuleName | 有 amazon/target/walmart，无 bolv2 |
| POST /definition/getProfile | 有 instacart/amazon/kevel，无 bolv2 |
| POST /definition/getTarget | 有 kevel/instacart/amazon，无 bolv2 |
| POST /definition/getRuleInfoByCampaignId | 有 amazon/instacart/krogerv3/chewyv2，无 bolv2 |
| POST /definition/getAutoRefillRuleApplyTags | 有 amazon/instacart，无 bolv2 |
| POST /definition/getAutoRefillRuleApplyTargets | 有 amazon/instacart，无 bolv2 |
| POST /definition/getAutoRefillRuleApplyTagCampaigns | 有 amazon/instacart，无 bolv2 |
| POST /definition/checkAutoRefillRule | 有 amazon/instacart/krogerv3/chewyv2，无 bolv2 |
| POST /definition/editRule | 有 amazon/walmart/target/chewyv2/instacart/dsp/doordash/samsclub/citrus/criteo/krogerv3/tiktok/ebay/kevel/ttd/openai/homedepot，无 bolv2 |
| POST /definition/addAppliedObj | 有 walmart/instacart/target/doordash/krogerv3/chewyv2/samsclub，无 bolv2 |
| POST /definition/updateAutomation | 仅 instacart(9) 有真实流量 |

### 2.2 NO_PRODUCTLINE_FIELD / GET 端点，按 fallback 规则用全平台流量判断，但排除 62/3186 后为 0（7 个）

以下端点 body 不带 productLine 字段（或为 GET），按 SKILL.md fallback 应使用全平台流量判断；
但排除 clientId 62/3186 后，近 180 天全平台真实调用数为 0（唯一命中均为 62/3186 测试噪声），
判定为 ES 无真实流量：

| 接口 | 核查方式 | 结果 |
|---|---|---|
| POST /definition/export/commerceRuleReport | query_es 180d 排除62/3186 | 0 hits（未排除时 18 hits，全部 62/3186） |
| POST /definition/getCampaignWithRule | query_es 180d 排除62/3186 | 0 hits（未排除时 18 hits，全部 62/3186） |
| POST /definition/getAsinRelatedRule | query_es 180d 排除62/3186 | 0 hits（未排除时 18 hits，全部 62/3186） |
| POST /definition/adtomicRules/settings | query_es 180d 排除62/3186 | 0 hits（未排除时 15 hits，全部 62/3186） |
| GET /definition/checkCustom/{ruleId} | wildcard-agg 定位 5 个真实路径后逐一 samples 反查 clientId | 16 hits 全部为 62(4条路径)/3186(1条路径)，0 真实客户 |
| GET /definition/adtomicRules/settings/{profileId} | wildcard-agg 定位 4 个真实路径后逐一 samples 反查 clientId | 18 hits 全部为 62(3条路径)/3186(1条路径)，0 真实客户 |
| GET /definition/getRuleTargetInfo | query_es 180d 排除62/3186 | 0 hits（未排除时 39 hits，全部 62/3186） |

## 三、有真实流量但为数据安全暂缓测试（2 个，与 kroger/citrus 判断不同，bol 独有）

以下 2 个接口 ES 确认有真实客户流量（非结构性跳过、非 ES 无流量），但经实测评估后判断
不适合在本次任务中生成可安全清理的 case，暂缓：

- **POST /definition/updateAppliedObj**（fallback 全平台 90 天 2720 次真实调用，占比高）：
  Swagger 定义其请求体是与 `/definition`（创建规则）几乎相同的完整 RuleParam 结构（含
  applyTarget/automation/frequency 等全部字段），而非窄范围的"仅更新应用对象"局部 PATCH。
  实测 GET 已存在真实规则详情后发现，响应体字段命名与请求体字段命名不完全一致（如
  `automationId` vs 请求体的规则级字段），且无法确认该接口是全量覆盖(overwrite)语义还是
  部分合并(merge)语义。若为全量覆盖语义，随意拼装的请求体可能将 real_rule_id_* 四个跨
  case 复用的持久真实规则（automation 配置等字段）覆盖损坏，且这些规则在后续（含其它场景）
  测试中仍需保持原始可用状态，风险不可控，故未生成 case。

- **POST /definition/addAppliedObjBySeparateRule**（fallback 全平台 90 天 119 次真实调用）：
  实测调用该接口（body: `[{clientId, productLine, ids:[real_rule_id_targeting], ruleTarget:
  {targetLevel, userId, clientId, targetInfo}}]`）返回 `{"Total":1,"Success":1,"Failed":0}`，
  确认此接口会以现有规则为源、创建一条"独立新规则"。但尝试用 `/definition/getRule`
  （ownerIds=18589 + managedProfileIds=218944 + mode=Auto 等多种过滤组合）反查该新建规则以
  提取 ruleId 进行归档清理，**均返回 0 条结果**（对照组：用完全相同的过滤条件确实能查到
  `/definition`、`/bulkCreateRule` 创建的规则，说明该接口新建的规则不遵循相同的
  owner/profile 归属规则，具体归属机制未知）。由于**无法安全定位并清理**新建的实体，
  为避免遗留脏数据，未生成可执行 case。

  🔴 **需要人工介入**：本次核查过程中已实际调用该接口 2 次（第 1 次因缺少 `ruleTarget.userId`
  /`ruleTarget.clientId` 字段返回 `Success:0`，未产生新规则；第 2 次补全字段后返回
  `Success:1`，**确认产生了 1 条真实的新规则**，源规则为 `real_rule_id_targeting`
  =2098300196200034306，应用目标为 targetId=1000000000001777/profileId=218944/
  targetLevel=Campaign）。该新规则**未能通过 API 定位和归档**，可能需要工程side通过数据库
  直接排查 client_id=62 下由 `addAppliedObjBySeparateRule` 产生、`sourceRuleId`
  或类似字段指向 2098300196200034306 的规则记录并手工清理。已确认此操作**未影响**
  `real_rule_id_targeting` 本身（其 applyTarget 事后核查未变化）。

## 四、内部辅助调用说明（不计入接口覆盖，不单独声称通过）

`POST /definition`（3 个场景）与 `POST /bulkCreateRule` 的 case 内部，为了提取新建规则的
ruleId 以便后置归档清理，调用了 `POST /definition/getRule` 作为中间步骤（该调用本身在本次
执行中全部返回 200 且成功提取到目标数据）。但由于 `/definition/getRule` 本身在 bol 平台下
经 ES 核查无真实客户流量（见二.1），**本报告不将 `/definition/getRule` 计入"已覆盖接口"**，
其在 report.json 中的 PASS 记录仅代表该辅助调用在本次执行环境下工作正常，不代表该接口本身
已按 bol 平台真实流量完成独立场景覆盖。

## 五、已生成并执行的 16 个接口 / 16 条 case 清单

| 接口 | case 数 | 说明 |
|---|---|---|
| POST /definition | 3 | Targeting(50%)/Campaign(33.3%)/SOV Bid(16.7%)，180天bol真实流量6条，含创建+归档清理，连跑2次幂等 |
| POST /bulkCreateRule | 1 | fallback全平台流量，含创建+归档清理，连跑2次幂等 |
| POST /definition/changeStatus | 1 | 复用real_rule_id_targeting，pause+resume成对逆操作，连跑2次幂等 |
| POST /definition/changeOwners | 1 | 复用real_rule_id_campaign，owner设为自身(幂等无副作用)，连跑2次幂等 |
| POST /definition/getRuleTargetInfoByRuleIds | 1 | 纯读 |
| POST /definition/getOwners | 1 | 纯读，已复核确认真实后端缺陷(Long/String cast 405)，作为回归用例保留 |
| POST /definition/getApplyRule | 1 | 纯读 |
| POST /definition/commerceRuleReport | 1 | 纯读 |
| POST /definition/export | 1 | 纯读，二进制xlsx响应，用$binary断言 |
| GET /definition/{ruleId} | 1 | 纯读 |
| GET /definition/commerceRuleClient | 1 | 纯读 |
| GET /definition/getAutoRefillRuleProfileIds | 1 | 纯读 |
| GET /definition/hasClickHitMode | 1 | 纯读 |
| GET /definition/transferableOwnerList | 1 | 纯读 |

写操作 case（POST /definition ×3、POST /bulkCreateRule、POST /definition/changeStatus、
POST /definition/changeOwners，共 6 条）均已验证**连跑 2 次全部 PASS**（幂等），且执行前后
`real_rule_id_targeting`/`real_rule_id_campaign`/`real_rule_id_sov_bid`/
`real_rule_id_harvest_keywords` 四个跨任务共用的真实存量规则的 `isPaused`/`userId`/
`ruleName` 均已核实与初始状态一致，未受影响；4 个临时创建的 `TC_Bol_*` 测试规则均已确认
归档（isPaused=true）且不再出现在规则列表查询结果中。

## 结论

51 个接口：16 个生成 case 并执行（16 条 case，2 次连跑 16/16 全 PASS）+ 14 个结构性跳过 +
21 个 ES 无 bol 真实流量跳过 + 2 个有真实流量但因数据安全风险暂缓（其中
addAppliedObjBySeparateRule 核查过程产生 1 条未能清理的真实残留规则，见上方"需要人工介入"）。

## 六、【任务发起方复核追加】残留规则问题的根因排查（2026-09-14 补充）

对"需要人工介入"的残留规则问题做了进一步排查，结论：**风险比原报告更低，且已定位根本原因**。

排查过程：尝试用 `GET /definition/{ruleId}` 直接查看 `real_rule_id_targeting`(2098300196200034306)
的完整字段，发现其 **`isDeleted: true`**。进一步核查发现 **config.json 里全部 4 个
`real_rule_id_*` 共用夹具（targeting/campaign/sov_bid/harvest_keywords）都是 `isDeleted: true`**：

| 变量 | ruleId | ruleName | isDeleted | isPaused |
|---|---|---|---|---|
| real_rule_id_targeting | 2098300196200034306 | autoTest_TargetingRule_20260911143845 | **true** | false |
| real_rule_id_campaign | 2098300191716323330 | autoTest_CampaignRule_20260911143844 | **true** | false |
| real_rule_id_sov_bid | 2098300141296594946 | autoTest_SOV Bid Rule_20260911143832 | **true** | false |
| real_rule_id_harvest_keywords | 2098300200348200961 | autoTest_HarvestKeywords_20260911143846 | **true** | false |

这 4 条规则本身是账号 62 在 bolv2 下由**某个与本任务无关的历史自动化流程**（命名模式
`autoTest_<Type>_<时间戳>`，在 09-08/09-10(×2)/09-11 各批量创建过一轮 4 种 ruleType）留下的
存量数据，在本任务开始前就已经处于软删除（`isDeleted:true`）状态——这不是本任务或
changeStatus/changeOwners 测试造成的（这两个接口的请求体都只传 `isPaused`，不涉及
`isDelete` 字段）。

**这解释了为什么 `POST /definition/getRule` 列表搜索怎么过滤都查不到它**：`isDeleted:true`
的规则被列表搜索正常排除在外（这是预期的软删除行为，不是接口 bug），但 `GET /definition/{ruleId}`
按 ID 直查、`POST /definition/changeStatus`、`POST /definition/changeOwners` 这些按 ID 操作的
接口不受 `isDeleted` 过滤，所以对应 case 依然能拿到 200 并断言通过——**功能上没有问题，
但这 4 个"real_rule_id_*"严格来说是软删除状态的规则，不是"活跃"规则**，描述里"该规则初始
isPaused=false"是准确的，但遗漏了它们本就是 isDeleted=true 这个背景信息。

**对残留规则(addAppliedObjBySeparateRule 克隆产生)的重新评估**：该接口是以
`real_rule_id_targeting`（isDeleted=true 的源规则）为源做克隆，新生成的规则大概率**继承了
同样的不可见/非活跃状态**（这与"用任何 owner/profile/mode 组合的 getRule 搜索都查不到它"这一
观察完全吻合——如果新规则是正常活跃状态，考虑到本模块内其它 `POST /definition`/
`POST /bulkCreateRule` 创建的规则都能用同样的 getRule 搜索模式立即查到，唯独这条查不到，
更合理的解释是它跟随源规则继承了某种非活跃/软删除标记，而非"数据错误地对外可见"）。
即：**该残留规则大概率和其源规则一样，本就不会出现在任何规则列表类 UI/接口中**，实际数据
污染风险显著低于最初报告的表述，但仍建议工程侧在数据库层面确认并按需清理
`client_id=62` 下 `sourceRuleId`（或类似字段）指向 2098300196200034306 的记录。

**遗留建议**：`config.json` 中的 4 个 `real_rule_id_*` 变量目前指向的都是软删除规则，仍可用于
"按ID直查/changeStatus/changeOwners"类需要真实 ruleId 的只读或状态切换测试（已验证不影响
断言结果），但**不适合**作为"该规则应能被 getRule 列表搜索到"这类场景的夹具。后续如需要一个
"活跃、可被 getRule 列表搜索到"的规则夹具，需要另外创建并保持不删除。
