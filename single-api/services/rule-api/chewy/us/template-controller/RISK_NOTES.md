# template-controller (chewy, us) — 写操作风险评估记录

生成时间：2026-09-14

以下 5 个 `Default*` 端点操作的是"系统默认模板/分类库"（全局推荐模板池），**未生成 case、未执行**。
该判断已在 target/kroger 平台的 RISK_NOTES.md 中通过实测验证过，因为这些默认模板/分类是**全局共享
实体**，不因调用方 productline 不同而改变其归属结构，故判断标准可直接复用到 chewy：

## 已验证的事实（本次用 chewy 测试账号复核，结论与 target/kroger 一致）

- `POST /template/getDefaultCategory`（chewy 账号，client_id=62, header productline=chewyv2）返回
  1 条默认分类：`test v2`（id=1930933291105234945）：`accessibleClientIds: ["62"]`、
  `canDelete: false` → 分类可见性限定到 client 62，但仍标记为不可删除。
- `POST /template/getDefaultTemplate` 返回的默认模板记录 `clientId` 均为 `null`，说明模板实体本身
  不是按 client 隔离的——即便所属分类的可见性被 `accessibleClientIds` 限定到某个 client，模板记录
  仍是全局共享实体，删除/编辑会影响所有能看到该分类的其他客户端。

## 结论：跳过的接口与理由

| 接口 | 结论 |
|---|---|
| `DELETE /template/default/{templateId}` | 候选模板 `clientId=null`，是全平台共享的推荐模板数据，且 Swagger 中无"创建默认模板"接口可先造出一次性记录再删除回滚。物理删除不可逆，跳过。 |
| `DELETE /template/defaultCategory/{categoryId}` | 唯一候选分类 `test v2` 明确 `canDelete:false`，且无创建接口可回滚，跳过。 |
| `POST /template/editDefaultCategory` | 会整体覆盖写入一个全局共享分类的 name/description，误写会立即影响所有能看到该分类的客户端，跳过。 |
| `POST /template/editDefaultTemplate` | 覆盖式写入一条 `clientId=null` 的全局共享模板，一旦字段映射不完全一致会静默改坏全局推荐数据，跳过。 |
| `POST /template/moveDefaultTemplate` | 修改的是全局共享模板（`clientId=null`）的 `categoryId` 归属，非仅 client 62 私有数据，跳过。 |

按任务要求「无法确认明确限定在 QA client 范围内时，宁可跳过并标记」，以上 5 个接口本次均不生成
cases.json、不执行。其余 17 个接口（含只读查询、模板生命周期创建/编辑/收藏/移动/删除、分类
生命周期创建/编辑/删除、bulk 批量创建）均已在 chewy 测试账号上生成 case 并执行验证，写操作 case
均已验证连跑 2 次结果一致（幂等），执行前后测试账号下的真实存量数据（7 条真实模板、4 个真实分类）
未受任何影响。
