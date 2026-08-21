# 待续：Account / BulkCampaign 接口覆盖补充清单

> 背景：`swagger-api-case` 技能对 `PacvueMainApi` 的 `Account`、`BulkCampaign` 两个模块生成 case 时，
> 部分接口因零 ES 流量或涉及真实账号/权限写操作，暂时按方案 B 跳过（未生成 case）。
> 本文件记录截至目前的缺口，供下次继续。

## Account 模块（当前覆盖 16/27，剩 11 个）

已完成（本轮新增）：`CheckName`（username=lmtesting111）、`SetRorA`（userId=39931, RandA=Staff）

**2026-08-21 更新**：用户确认 lmtesting111（userId=39931）为可随便操作的测试账号。已针对 `PasswordForm`、`SetUserProfile` 生成 case（`task-2026-08-21-09-40-00/cases.json`），**仅生成未执行**：
- `PasswordForm`：结构清楚，用占位密码 `Test@123456`，执行前需再次确认——一旦执行会真的改密码，且无法反查原密码还原。
- `SetUserProfile`：ES 近90天249条真实调用，用现有测试 Profile（2755545444012419）+ UserIds 加入 39931。但从样本看该接口疑似"整体覆盖式"设置 UserIds（非增量追加），执行前必须先确认：(1) 接口是覆盖还是追加语义 (2) 该测试 Profile 当前真实的 UserIds 列表，避免误删其他已有权限。
- `AddDataNew`/`Delete`/`EditDataNew` 仍未解决：`EditDataNew` 除 `userId` 外 Swagger 完全没定义其他字段、ES 也 0 条真实样本，跟测试账号无关，需单独找开发确认接口入参。

**2026-08-21 补充**：核实了 `Delete`/`SetUserForm`/`SetUserMultiProfile`/`DeleteAmazon` 四个接口的 ES 真实调用情况：
- `Delete`、`SetUserForm`、`SetUserMultiProfile`：近90天 ES 均**0条**真实调用记录，Excel 已标注"ES无真实调用记录"。卡点仍是缺测试账号/字段枚举值不明，与调用量无关。
- `DeleteAmazon`：近90天 ES **110条**真实调用，结构唯一（仅 advertiserId 单参数）。已生成 case（`task-2026-08-21-15-00-00/cases.json`），**仅生成未执行**：为避免解绑真实用户账号，改用测试账号已验证的 `amazon_advertiser_id` 构造，而非 ES 样本里的真实客户 advertiserId。执行前需确认：解绑后是否影响其他依赖该账号的测试 case，以及能否重新绑定回来。

### 类型 1：Swagger 未定义参数 + ES 零流量（3个）——需要人工提供接口文档或前端调用示例
- `POST /api/Account/V3/AddDataNew`
- `POST /api/Account/V3/AmazonList`
- `POST /api/Account/V3/GetGoogleAccount`

（Excel 场景覆盖列已加说明备注，见 `single-api/swagger_modules.xlsx` PacvueMainApi sheet 对应行）

### 类型 2：结构已知，但缺真实枚举值（2个）
- `POST /api/Account/V3/SetUserForm`：body 含 `UserId`/`UserRole`/`Mail`/`Profiles`/`DspRoleCheck`/`UserGroups`/`IsSetTagPermission`/`TagPermissionTagIds`，缺 `UserRole`、`DspRoleCheck` 等字段的合法枚举值
- `POST /api/Account/V3/SetUserMultiProfile`：body 含 `ProfileIds`/`AmazonAdvertiserId`/`UserIds`/`AdminId`/`optype`，`optype` 含义未知（猜测 1=绑定/2=解绑），需要真实值或找开发确认

### 类型 3：结构 + 真实值都有，但涉及真实账号写操作，需确认是否执行（2个）
- `POST /api/Account/V3/DeleteAmazon`：ES 近90天有 **110条**真实样本，参数为 query `advertiserId`（真实值形如 `amzn1.account.XXXXX`），风险：删除真实 Amazon 账号绑定
- `POST /api/Account/V3/SetUserProfile`：ES 近90天有 **251条**真实样本，body 为 `ProfileId`/`AmazonAdvertiserId`/`UserIds`/`AdminId`，风险：改动测试账号下真实用户的 Profile 权限分配

### 类型 4：需要先有"专用测试用户"才能安全测（3个，依赖类型1的 AddDataNew 先解决）
- `POST /api/Account/V3/Delete`：query `userId`，删除用户账号
- `POST /api/Account/V3/EditDataNew`：query `userId`，编辑用户信息，同时 body 结构也未知（Swagger 里也没写）
- `POST /api/Account/V3/PasswordForm`：body `userid`/`newpwd`/`repeatpwd`，修改用户密码——即使标记"仅生成不执行"也需谨慎考虑是否构造真实密码字符串

### 类型 5：低风险，具备生成条件，只是还没做（1个）
- `GET /api/Account/V3/GetRorA`：无参数，大概率读取当前登录用户自身的角色标志，不依赖额外真实值，是这批里最容易先测的

---

## BulkCampaign 模块（当前覆盖 34/38 按接口覆盖率算 / 27/38 按独立场景算，剩 11 个未生成独立 case）

### 已被间接调用、但没有独立场景描述（7个）——已在其他 case 里作为"预检步骤"跑过
这几个是 `Confirm*ChangeXxx` 类 case 的前置检查步骤，接口本身已被执行过，只是没有自己的场景条目：
- `POST /api/BulkCampaign/TestExecute`（在 ConfirmCampaignChangeName 里被调用）
- `POST /api/BulkCampaign/TestBudgetExecute`（在 ConfirmCampaignChangeBudget 里被调用）
- `POST /api/BulkCampaign/TestAdgroupNameExecute`（在 ConfirmAdgroupChangeName 里被调用）
- `POST /api/BulkCampaign/TestCampaignStateExecute`（在 ConfirmCampaignChangeState 里被调用）
- `POST /api/BulkCampaign/TestTargetStateExecute`（在 ConfirmChangeTarget 里被调用）
- `POST /api/BulkCampaign/TestTargetCreateExecute`（在 ConfirmCreateTarget 里被调用）
- `POST /api/BulkCampaign/TestCreateNegativeTargetExecuted`（在 ConfirmCreateTarget 里被调用）

如果要给这 7 个补独立场景，需要单独设计"仅预检、不确认执行"的 case（即只调 Test*Execute 本身，不接后续 Confirm 步骤）。

### 真正零覆盖，ES 近90天/365天窗口内完全没有调用记录（4个）
- `POST /api/BulkCampaign/ExportAdgroupNameFailLog`
- `GET /api/BulkCampaign/GetCampaignChangeLog/{kindType}`
- `POST /api/BulkCampaign/VerifyCampaignChangeBudget`
- `POST /api/BulkCampaign/VerifyCampaignChangeName`

这 4 个需要按 Swagger 结构纯手工构造（无真实样本可参考），且从命名看 `Verify*` 应该是 `Confirm*` 系列的另一种前置校验，可能和 `Test*Execute` 类似，建议生成时一并核对是否也是某个 Confirm case 里遗漏的步骤。

---

## 建议下次开始顺序
1. `GetRorA`（零风险，直接可测）
2. `BulkCampaign` 的 4 个真零覆盖接口（结构未知但风险较低，多是查询/校验类）
3. 跟用户确认 `Account` 类型2的枚举值（`UserRole`/`optype` 等）
4. 跟用户确认是否要执行类型3的 `DeleteAmazon`/`SetUserProfile`（需要明确可牺牲的测试对象）
5. 类型4（`AddDataNew` 等）需要先拿到接口文档或前端调用示例，可能需要问开发
