# template-controller (target, us) — 写操作风险评估记录

以下 5 个 `Default*` 端点操作的是"系统默认模板/分类库"（全局推荐模板池，`userName="Pacvue Default"`），**未生成 case、未执行**。判断依据：直接用 target 测试账号（client_id=62, productline=target）实测调用 `POST /template/getDefaultCategory`、`POST /template/getDefaultTemplate` 验证结构与归属。

## 已验证的事实

- `getDefaultCategory` 返回 3 个默认分类：
  - `Rule Kickstart`（id=2028440916079656962）：`accessibleClientIds: null`、`canDelete: false` → 全平台/全客户共享，不可删除。
  - `fltest`（id=1993232309946986498）：`accessibleClientIds: ["62"]`、`canDelete: false` → 分类可见性被限定到 client 62，但仍不可删除。
  - `fltest2`（id=1998333816908328962）：`accessibleClientIds: ["62"]`、`canDelete: true`、`countNum: 0` → 唯一一个"看起来"可安全删除的默认分类，但这是账号里已存在的历史数据（非本次自动化创建），无法确认是否为其他同事的测试遗留数据，且没有对应的"创建默认分类"接口可以先造一次性数据再删除做回滚。
- `getDefaultTemplate` 返回的全部 6 条默认模板记录 `clientId` 均为 `null`（非 `62`），说明模板实体本身不是按 client 隔离的——即便其所属分类的可见性被 `accessibleClientIds` 限定到某个 client，模板记录仍是全局共享实体。

## 结论：跳过的接口与理由

| 接口 | 结论 |
|---|---|
| `DELETE /template/default/{templateId}` | 全部候选模板 `clientId=null`，是全平台共享的推荐模板数据，且 Swagger 中无"创建默认模板"接口可先造出一次性记录再删除回滚。物理删除不可逆，跳过。 |
| `DELETE /template/defaultCategory/{categoryId}` | 3 个默认分类中 2 个明确不可删除；唯一 `canDelete:true` 的 `fltest2` 是账号历史遗留数据、非本次创建，无法确认删除后果范围，且无创建接口可回滚，跳过。 |
| `POST /template/editDefaultCategory` | 会整体覆盖写入一个全局共享分类的 name/description，误写会立即影响所有能看到该分类的客户端，跳过。 |
| `POST /template/editDefaultTemplate` | 覆盖式写入一条 `clientId=null` 的全局共享模板（TemplateRequest 含大量嵌套 automation 字段），一旦字段映射不完全一致会静默改坏全局推荐数据，跳过。 |
| `POST /template/moveDefaultTemplate` | 修改的是全局共享模板（`clientId=null`）的 `categoryId` 归属，非仅 client 62 私有数据，跳过。 |

按任务要求"无法确认明确限定在 QA client 范围内时，宁可跳过并标记"，以上 5 个接口本次均不生成 cases.json、不执行。若需要覆盖，需要研发确认是否存在专门给自动化测试用的隔离默认模板库/分类，或提供"创建默认模板/分类"接口以支持安全回滚。
