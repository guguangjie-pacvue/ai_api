# sov-hub 高风险接口跳过记录

记录哪些接口经评估后判定风险过高、主动不生成/不执行 case，避免后续被误认为"漏测"。

## Bulk Operation 模块（2026-09-24，amazon 平台）

该模块 8 个接口中 6 个近90天有真实流量，但全部是批量写/删操作，主动跳过、未执行：

| 接口 | 90天命中(amazon) | 请求体 | 跳过原因 |
|---|---|---|---|
| `DELETE /api/sov/bulk/brand` | 79 | `{brandName, countryCode}` | 按品牌名+国家批量删除该账号下所有匹配 category，命中范围不可控（无法只影响自建的一次性测试数据），账号内已有其它同事的真实测试 category，误删风险高 |
| `DELETE /api/sov/bulk/category` | 80 | 批量 category id 列表 | 批量删除，同上风险；且删除目标需要先精确验证归属，链路上任何一步出错都会误删共享账号里别人的数据 |
| `PUT /api/sov/bulk/category/daypart` | 8 | `ids[] + isDaypart(query)` | 批量修改已存在 category 的 daypart 开关，账号是多人共用测试账号，可能改到别人正在用的 category 配置 |
| `PUT /api/sov/bulk/category/device-types` | 4 | `{ids[], deviceTypes[]}` | 同上，批量覆盖已存在 category 的设备类型配置 |
| `POST /api/sov/bulk/import-sov-template` | 24 | `{brand, category, keywords[], isDaypart, ...}` | 批量新建 category+keywords，会真实消耗账号 quota、产生新监控配置，且不确定是否会与已有品牌/类目冲突 |
| `POST /api/sov/bulk/upload-sov-template` | 74 | `{file: string}` | 文件上传格式未知（大概率 base64 Excel），无法在不了解真实模板格式的情况下构造安全的测试输入，贸然尝试可能触发未知副作用 |

**处理方式**：不生成 cases.json，不调用 run_cases.py。Excel 里这 6 个接口的「场景覆盖」列标注"跳过：批量写/删操作，风险未评估，见 RISK_NOTES.md"，与"ES无流量"（`download-sov-template`、`preview-sov-template` 两个 GET，本身就是0调用）区分开，避免误认为是同一种"未覆盖"。

**后续如需覆盖**：需要先专门为这几个接口设计隔离的一次性测试数据（如新建一个明确带 `AutoTest_` 前缀且不会与任何品牌/国家碰撞的 category），并在真正执行前让人复核一遍参数范围，不能直接照搬 ES 真实日志里的参数重放。

## SOV Insight 模块（2026-09-24，amazon 平台）

`PATCH /api/sov/insight/main-brand` 近90天有 15 次真实调用（amazon），请求体 `{groupId, mainBrand}`，`groupId` 是收藏分组（favorite-group）的 id。但 `favorite-group` 的 GET/POST 两个接口本身就在用户指定的排除名单里（见 `excluded-endpoints.json`），不能调用来创建/查询一个属于本测试账号的合法 groupId，因此没有安全的方式获得一个"确定是自己的、不会误改到别人分组"的 groupId。**跳过，未执行**，Excel 场景覆盖列标注"跳过：需真实groupId，依赖已排除的favorite-group接口"。

**后续如需覆盖**：需要先由产品/其他渠道确认可以对 favorite-group 解禁测试，或者由人工在页面上手动建一个测试专用收藏分组、把其 id 提供给自动化流程使用。
