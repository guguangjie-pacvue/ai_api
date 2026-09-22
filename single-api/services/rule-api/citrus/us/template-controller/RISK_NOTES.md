# template-controller (citrus, us) — 写操作风险评估记录

生成时间：2026-09-14

以下 5 个端点操作的是"系统默认模板/分类库"（全局推荐模板池），**未生成 case、未执行**。
该判断已在 target/kroger/chewy 平台的 RISK_NOTES.md 中通过实测验证过，因为这些默认模板/分类是
**全局共享实体**，不因调用方 productline 不同而改变其归属结构，故判断标准可直接复用到 citrus：

## 已验证的事实（本次用 citrus 测试账号复核，结论与 target/kroger/chewy 一致）

- `POST /template/getDefaultCategory`（citrus 账号，client_id=62, header productline=citrus）返回
  1 条默认分类：`Rule Kickstart`（id=1912046024318316545）：`accessibleClientIds: null`、
  `canDelete: false` → 全局共享分类，明确不可删除。
- `POST /template/getDefaultTemplate` 返回的全部默认模板记录 `clientId` 均为 `null`，说明模板实体
  本身不是按 client 隔离的——是全局共享实体，删除/编辑会影响所有能看到该分类的其他客户端。
- **额外 ES 流量交叉验证**（全平台口径，因该模块 POST 接口 body 无 productLine 字段无法按 citrus
  单独过滤，采用全平台流量作为下限证据）：
  - `POST /template/editDefaultCategory`：近 90 天全平台 0 次调用，近 180 天全平台 0 次调用，近 365
    天全平台仅 1 次调用——几乎无人使用。
  - `POST /template/editDefaultTemplate`：近 90 天全平台 0 次调用，近 180 天全平台 0 次调用，近 365
    天全平台仅 2 次调用——几乎无人使用。
  - `POST /template/moveDefaultTemplate`：近 90/180/365 天全平台均 0 次调用——**ES 无流量**（该接口
    单独即满足"ES 上查不到真实流量"的红线，本身就该跳过，不生成 case）。
  - `DELETE /template/default/{templateId}`：近 90 天全平台 2 次调用（真实路径参数替换流量，接口
    确实存在使用）。
  - `DELETE /template/defaultCategory/{categoryId}`：近 90 天全平台 3 次调用（真实路径参数替换流量，
    接口确实存在使用）。

## 结论：跳过的接口与理由

| 接口 | 结论 |
|---|---|
| `DELETE /template/default/{templateId}` | 候选模板 `clientId=null`，是全平台共享的推荐模板数据，且 Swagger 中无"创建默认模板"接口可先造出一次性记录再删除回滚。物理删除不可逆，跳过（ES 上确有 2 次真实调用，属"有真实流量但为安全 structural skip"，非"ES 无流量"跳过）。 |
| `DELETE /template/defaultCategory/{categoryId}` | 唯一候选分类 `Rule Kickstart` 明确 `canDelete:false`，且无创建接口可回滚，跳过（ES 上确有 3 次真实调用，同上，为安全 structural skip）。 |
| `POST /template/editDefaultCategory` | 会整体覆盖写入一个全局共享分类的 name/description，误写会立即影响所有能看到该分类的客户端；且近 90/180 天 ES 全平台流量为 0，近 365 天仅 1 次，跳过（安全 structural skip + 流量极稀疏双重理由）。 |
| `POST /template/editDefaultTemplate` | 覆盖式写入一条 `clientId=null` 的全局共享模板，一旦字段映射不完全一致会静默改坏全局推荐数据；且近 90/180 天 ES 全平台流量为 0，近 365 天仅 2 次，跳过（安全 structural skip + 流量极稀疏双重理由）。 |
| `POST /template/moveDefaultTemplate` | 修改的是全局共享模板（`clientId=null`）的 `categoryId` 归属，非仅 client 62 私有数据；且近 90/180/365 天 ES 全平台流量均为 0，属"ES 无流量"，按红线本身即不能生成 case、不能执行，跳过。 |

按任务要求「ES 上查不到真实流量的接口不能生成 case；无法确认明确限定在 QA client 范围内的写操作
宁可跳过并标记」，以上 5 个接口本次均不生成 cases.json、不执行。其余 17 个接口（含只读查询、模板
生命周期创建/编辑/收藏/移动/删除、分类生命周期创建/编辑/删除、bulk 批量创建）均已在 citrus 测试
账号(client_id=62)上生成 case 并执行验证，写操作 case 均已验证连跑 2 次结果完全一致（11 PASS + 1
已知跨平台真实缺陷 FAIL，两次一致，幂等）。执行前后测试账号下的真实存量数据（4 个真实分类：
QA_Citrus_Fixture_Category / Rule Kickstart / latata / campaign_rule1；12 条真实模板，含
QA_Citrus_Fixture_Template）逐条核对，未受任何影响；`addFavorite` 端点的 `defaultTemplate:true`
（收藏全局默认模板）场景同样出于"操作全局共享实体"的一致理由未覆盖，仅覆盖 `defaultTemplate:false`
（收藏自建模板）场景。
