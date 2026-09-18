# template-controller (samsclub, us) — 写操作风险评估记录

生成时间：2026-09-14

以下 5 个 `Default*` 端点操作的是"系统默认模板/分类库"（全局推荐模板池），**未生成 case、未执行**。
该判断已在 target/kroger/chewy 平台的 RISK_NOTES.md 中通过实测验证过，因为这些默认模板/分类是
**全局共享实体**，不因调用方 productline 不同而改变其归属结构，故判断标准可直接复用到 samsclub。
本次已用 samsclub 测试账号（client_id=62）再次实测复核，结论与 target/kroger/chewy 一致：

## 已验证的事实（本次用 samsclub 测试账号复核）

- `POST /template/getDefaultCategory`（samsclub 账号，client_id=62）返回 5 条默认分类
  （Sales/Efficiency/Relevancy/Discovery/SOV），全部 `canDelete: false`。
- `POST /template/getDefaultTemplate` 返回 24 条默认模板记录，`clientId` 均为 `null`，说明模板
  实体本身不是按 client 隔离的——即便所属分类的可见性可能被限定，模板记录仍是全局共享实体，
  删除/编辑会影响所有能看到该分类的其他客户端。

## 结论：跳过的接口与理由

| 接口 | 结论 |
|---|---|
| `DELETE /template/default/{templateId}` | 候选模板 `clientId=null`，是全平台共享的推荐模板数据，且 Swagger 中无"创建默认模板"接口可先造出一次性记录再删除回滚。物理删除不可逆，跳过。 |
| `DELETE /template/defaultCategory/{categoryId}` | 全部候选默认分类均 `canDelete:false`，且无创建接口可回滚，跳过。 |
| `POST /template/editDefaultCategory` | 会整体覆盖写入一个全局共享分类的 name/description，误写会立即影响所有能看到该分类的客户端，跳过。 |
| `POST /template/editDefaultTemplate` | 覆盖式写入一条 `clientId=null` 的全局共享模板，一旦字段映射不完全一致会静默改坏全局推荐数据，跳过。 |
| `POST /template/moveDefaultTemplate` | 修改的是全局共享模板（`clientId=null`）的 `categoryId` 归属，非仅 client 62 私有数据，跳过。 |

按任务要求「无法确认明确限定在 QA client 范围内时，宁可跳过并标记」，以上 5 个接口本次均不生成
cases.json、不执行。其余 17 个接口（含只读查询、模板生命周期创建/编辑/收藏/移动/删除、分类
生命周期创建/编辑/删除、bulk 批量创建）均已在 samsclub 测试账号上生成 case 并执行验证（其中
`POST /template/getRecommendation` 复现了跨平台共性的后端 SQL 拼接缺陷，如实记录为 FAIL，非本次
测试构造错误）。

## 补充：本次为 samsclub 新增的持久化测试夹具

- 分类 `autotest_fixture_category_samsclub_2`（id=2099342566861484033）：为补齐模板"移动到另一分类"
  场景所需的第二个非默认分类而创建，作为长期可复用的测试夹具保留（不删除），已记录到
  `config.json` 的 `fixture_category_id_2`。
- `fixture_category_id` 复用 samsclub 账号下已存在的非默认分类 `woshimachao`（id=1640962112648499201）。
