# template-controller (bol, us) — 写操作风险评估记录

以下 5 个 `Default*` 端点操作的是"系统默认模板/分类库"（全局推荐模板池），**未生成 case、未执行**。
该判断已在 kroger/target/citrus 平台的 RISK_NOTES.md 中通过实测验证过，因为这些默认模板/分类是
**全局共享实体**，不因调用方 productline 不同而改变其归属结构，故判断标准直接复用到 bol，本次仅用
bol 测试账号复核了一遍关键结论（未执行任何破坏性写操作）：

## 已验证的事实（本次用 bol 测试账号复核，结论与 kroger/citrus 一致）

- `POST /template/getDefaultCategory`（bol 账号，client_id=62）返回 7 条默认分类：其中 4 条
  `accessibleClientIds: ["62"]`（test v2 / yyyyyyyyyyyyyy / fltest_bol v2 / fltest_pro_626），
  其余 3 条 `accessibleClientIds: null`（Efficiency / Relevancy / Rule Kickstart）为全局共享。
- `POST /template/getDefaultTemplate`（categoryId=1930933114109800449 "test v2"）返回的默认模板
  记录 `clientId` 为 `null`，说明模板实体本身不是按 client 隔离的——即便所属分类的可见性被
  `accessibleClientIds` 限定到某个 client，模板记录仍是全局共享实体，删除/编辑会影响所有能看到该分类
  的其他客户端。

## 结论：跳过的接口与理由

| 接口 | 结论 |
|---|---|
| `DELETE /template/default/{templateId}` | 候选模板 `clientId=null`，是全平台共享的推荐模板数据，且 Swagger 中无"创建默认模板"接口可先造出一次性记录再删除回滚。物理删除不可逆，跳过。 |
| `DELETE /template/defaultCategory/{categoryId}` | 候选分类均为全局共享或 canDelete 受限，且无创建接口可回滚，跳过。 |
| `POST /template/editDefaultCategory` | 会整体覆盖写入一个全局共享分类的 name/description，误写会立即影响所有能看到该分类的客户端，跳过。 |
| `POST /template/editDefaultTemplate` | 覆盖式写入一条 `clientId=null` 的全局共享模板，一旦字段映射不完全一致会静默改坏全局推荐数据，跳过。 |
| `POST /template/moveDefaultTemplate` | 修改的是全局共享模板（`clientId=null`）的 `categoryId` 归属，非仅 client 62 私有数据，跳过。 |

按红线「无法确认明确限定在 QA client 范围内时，宁可跳过并标记」，以上 5 个接口本次均不生成
cases.json、不执行。

## 已生成并执行的 17 个接口

- 只读查询（8）：`getCategory`、`getDefaultCategory`、`getDefaultTemplate`、`getOwners`、
  `getRecommendation`（复现跨平台共性 SQL 拼接缺陷，断言按正确预期写，实际 FAIL，如实记录）、
  `getTemplate`（bol 账号真实存量 4 种 ruleType：Targeting 73.3%/Harvest Keywords 13.3%/
  SOV Bid 6.7%/Campaign 6.7%，共 4 个 case）、`getTemplateListFromDirectShare`、
  `getTemplateListFromSharePass`（借助 share-pass-controller 的 create/delete 作为 fixture
  bootstrap，仅用于验证本接口，不代表 sharePass/create 本身在 bol 下有真实流量覆盖）。
- 写操作生命周期（3 组，均含 extract_vars 抓新建 ID + 后置清理 + 已连跑 2 次验证幂等，全 PASS）：
  - 模板生命周期：`POST /template` → `editTemplate` → `addFavorite` → `moveTemplate` →
    `DELETE /template/{templateId}`
  - 分类生命周期：`POST /template/category` → `editCategory` → `DELETE /template/category/{categoryId}`
  - 批量创建：`POST /template/bulk` → `DELETE /template/{templateId}`（清理新建的 bulk 模板）
  - 全程只使用本次自建的 `QA_Bol_Test_*` 临时模板/分类，未触碰 bol 账号既有存量数据
    （执行前后均为 15 模板 / 10 分类，一致）。

## 已知缺陷（非本次引入）

`POST /template/getRecommendation` 在 `defaultCategory:false` 且无 `templateId`/`ruleType` 过滤时，
服务端拼接出非法 SQL `... WHERE (rule_template_id IN ())`，返回 `code:405` + SQLSyntaxErrorException。
该缺陷已在 walmart/instacart/target/kroger/chewy/citrus 平台独立复现，本次在 bol 平台复现，确认是
`RuleAutomationMapper` 的跨平台共性缺陷。

## 执行结果

14 个 case，13 PASS / 1 FAIL（getRecommendation 的已知缺陷），已连跑 2 次结果一致（13/14 稳定）。
