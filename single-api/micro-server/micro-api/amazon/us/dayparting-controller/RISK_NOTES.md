# dayparting-controller (micro-api, amazon, us) — 风险标记接口

本模块共 52 个有效接口（已排除 deprecated 的 `/syncbid/byTempId`、`/dayparting/bulk/bulkAchiveCampaigns`、`/dayparting/relationUpdate`）。
其中 29 条 Happy Path case 已生成并执行（`task-2026-09-15-11-59-17/cases.json`，29/29 PASS，跑了两遍验证幂等）。
本文件记录**有真实 ES 流量、但判定为高风险/无法确认自建数据边界而主动跳过**的写操作接口，以及一个必须公开披露的探测事故。

## 🔴 重要发现：该服务的写接口对 superAdmin 测试账号不做跨 client 权限隔离

在排查 `changeOwner` 接口结构时，为验证"最小请求体是否会 500"，误用了 ES 真实样本（非本次生成的 case，只是探测调用）：

```json
{"productLine":"amazon","destUserId":27252,"destName":"saiqa.shoaib","tempIds":[464673],"clinetId":3555}
```

该调用返回 `200`（成功），而这条数据来自 **clientId=3555 的真实客户**（非本测试账号 client 3186）。也就是说：
**这个服务的写接口不会因为请求体里的实体（模板/campaign）不属于当前登录 client 而拒绝，超级管理员账号可以直接对任意真实客户的数据生效写操作**（这与它的部分只读接口相反——只读接口在 identity 字段(advertiserIds/userIds)与当前 client 不匹配时会触发后端 500，见下文"数据归属"说明，但这只是空指针保护缺失导致的报错，不是权限拦截）。

**影响评估**：`destUserId`/`destName` 与该 `tempIds` 在同一条历史真实日志中一起出现，大概率是把该模板的所有者重新设置为其"当时已经是"的所有者（等价于无害的 no-op 重放），但无法 100% 排除该模板所有者在此之后被人工改过、从而被本次探测调用覆盖回旧值的可能。**这不是本次交付的任何一条 case 产生的（29 条最终 case 全部是只读查询），而是本次调查过程中的一次探测性请求造成的副作用**，特此如实披露。

**由此得出的结论**：鉴于该服务写接口对任意真实 client 数据都会真实生效且无回滚接口可核实，下方所有"有真实流量"的写操作接口，**一律不再做任何探测性调用**，直接按跳过处理，仅通过 Swagger 结构 + ES 样本做静态分析。

---

## 高风险写操作接口（有真实流量，判定跳过，未生成 case，未执行）

### DELETE /dayparting/campaigns（`deleteCampaignDayparting`）
- ES 90 天真实流量：148 次（amazon，已排除测试账号）。
- 语义：删除 campaign 的 dayparting 应用关联。请求体 `baseCampaignList: [{profileId, campaignId}]` 直接来自 ES 样本均为其他真实客户的 profile/campaign。
- 风险：物理移除他人 campaign 的 dayparting 关联且无法验证是否为测试账号自建关联，无撤销接口可确认原状态。跳过。

### POST /dayparting/deleteTemplate（`deleteTemplates`）
- ES 90 天真实流量：384 次。
- 语义：删除模板（`ids: [tempId]`）。ES 样本全部为其他真实客户的模板 id。
- 原计划：本测试账号先通过 `updateTemplate` 自建一个模板，再用它的 id 测试 delete（闭环自清理）。
- **实测受阻**：`updateTemplate` 接口对本测试账号会话下的**任意合法请求体**（空 body、单字段 body、完整未改动的真实 ES 样本、替换为本账号可访问的 advertiserId 后的 body）均返回 `HTTP 500 Internal Server Error`，且该 500 与请求体内容无关（详见下方 updateTemplate 条目）。因此无法安全建立"自建模板"这一前置数据，deleteTemplate 也就失去了唯一可行的安全测试路径。跳过。

### POST /dayparting/deleteApply（`deleteApply`）
- ES 90 天真实流量：106 次。
- 语义：删除 apply 记录（`ids: [applyId]`）。ES 样本均为其他真实客户数据。
- 无可靠的"自建 apply"前置路径（`applyTemplate`/`LineItemIdApply` 在 amazon 平台 90 天内均为 0 流量，无法参照真实结构验证正确用法；`setTemplateAndApply` 本身也在风险清单内，见下）。跳过。

### POST /dayparting/deleteDetailApply（`deleteDetailApply`）
- ES 90 天真实流量：363 次。
- 语义：删除更细粒度的 apply 明细（line item 级）。同上，无可靠自建前置数据来源（`LineItemIdApply` 0 流量）。跳过。

### POST /dayparting/bulk/pausecampaigns（`bulkPausedCampaigns`）
- ES 90 天真实流量：20354 次（高频，用户在前端"批量暂停"场景常用）。
- 语义：批量暂停 campaign 的 dayparting（`baseCampaignList: [{profileId, campaignId}]`）。
- 风险：即使把 `baseCampaignList` 限定为本账号自己的 `real_campaign_id`，"批量暂停"属于用户显式列出的红线示例接口，且鉴于上方披露的"写接口对任意真实数据都会真实生效"的结论，为避免对本账号下真实业务范围以外的数据产生不可控影响，本轮不做探测性调用验证其边界，直接跳过。

### POST /dayparting/changeStatus（`changeCampaignSchdulerStatus`）
- ES 90 天真实流量：18726 次（高频）。
- 语义：批量修改 campaign 的 dayparting 状态（`commonCampaignList` + `status`）。与 `bulk/pausecampaigns` 同类风险（批量、状态変更），且依赖已存在的 campaign-scheduler 绑定关系，本轮未建立可验证的自有绑定数据。跳过。

### POST /dayparting/changeOwner（`changeOwner`）
- ES 90 天真实流量：14 次（低频）。
- 语义：变更模板所有者（`tempIds` + `destUserId`）。**本接口在探测阶段已发生上述"意外生效"事故**，进一步确认其对任意真实 client 数据都会真实生效。跳过，不再做任何调用。

### POST /dayparting/appoint（`appointDayparting`）
- ES 90 天真实流量：461 次。
- 语义："冲突情况下，指定campaign最高优先级"——需要目标 campaign 已存在多个模板应用产生冲突的前置状态才能触发真实业务分支，无法用最小化自建数据安全复现该冲突场景，且直接对 ES 样本里的真实 campaign 执行会变更其他客户 campaign 的优先级配置。跳过。

### POST /dayparting/apply-switch（`switchDayparting`）
- ES 90 天真实流量：66 次。
- 语义：切换某个 apply 的启用/禁用状态（`applyTargets: [{relId, profileId, applyLevel, templateId}]`）。ES 样本 relId/templateId 均为其他真实客户数据，无自建 apply 前置路径（见 deleteApply 条目）。跳过。

### POST /dayparting/status-switch（`switchDaypartingStatus`）
- ES 90 天真实流量：仅 1 次（90 天窗口内近乎从未被调用的低频功能）。
- 语义：与 `changeStatus` 同构（`commonCampaignList` + `status`），样本量过低也不足以支撑归纳"真实场景"，且同样依赖已存在的真实 campaign-scheduler 绑定。跳过。

### POST /dayparting/setTemplateAndApply（`setTemplateAndApply`）
- ES 90 天真实流量：1064 次。
- 语义：保存模板配置并应用到 campaign（请求体与 `updateTemplate` 同构，额外包含 `apply`/`allApplyCampaigns`/`lineItemIds` 等应用范围字段）。
- 因与 `updateTemplate` 共用底层写路径，同样受"任意 payload 下 500"问题阻塞（见下），且该接口会把模板变更同步应用到已绑定的真实 campaign，风险高于纯 updateTemplate。跳过。

### POST /bulk/set/dayparting（`setBulkBolDayParting`）
- ES 90 天真实流量：7184 次。
- 语义：批量设置 dayparting（请求体与 `updateTemplate` 同构）。同上，受写路径 500 问题阻塞，且是"批量"操作，边界不明确。跳过。

### POST /dayparting/updateTemplate（`updateTemplate`）
- ES 90 天真实流量：5258 次，其中 **100% 为"更新已有模板"场景**（500 条样本内未观察到 `id` 为空的创建请求）。
- **已验证的功能性问题**：
  1. 直接回放未修改的真实 ES 样本（含真实 `id`）→ `HTTP 500`。
  2. 去掉 `id` 尝试"创建新模板"（结构上 `id` 非必填）→ 仍 `HTTP 500`。
  3. 仅替换 `advertiserIds` 为本账号真实值、其余不变 → 仍 `HTTP 500`。
  4. 空请求体 `{}`、仅 `{"productLine":"amazon"}`、仅单个字段 `{"transcriptAutoMin": null}` → 均 `HTTP 500`（与请求体内容无关，说明并非某个字段值不合法导致，而是该写路径本身对当前测试账号会话不可用或存在后端缺陷）。
  5. 作为对照，同一账号在 `rule-api` 的 `template-controller` 写接口可以正常创建成功（10/10 PASS），排除了"账号整体不能做任何写操作"的可能，问题定位到 micro-api 的 `updateTemplate` 这条具体写路径。
- **结论**：这既不是"case 参数写错了"，也不是可以通过换用测试账号自建数据来规避的"高风险跳过"，而是一个需要研发介入排查的功能性缺陷/环境限制（该账号在 micro-api 侧可能缺少必要的写权限初始化，或该接口本身有未处理的空指针分支）。**未生成 case，未计入 29 条 Happy Path**，建议反馈给 micro-api 研发核实该测试账号的写权限配置。

### 已是 ES 无流量、顺带同属高风险类别的接口（无需额外风险跳过，已按无流量处理）
- `POST /dayparting/bulkDeleteApply`（0 流量）：与 `deleteApply` 同构的批量删除，若未来出现流量也应按上述 delete 类风险重新评估。
- `POST /dayparting/applyTemplate`（0 流量）：疑似"应用模板到 campaign"的创建入口，若未来出现流量，可考虑作为 `deleteApply`/`deleteDetailApply` 的自建前置步骤来源，但需先人工确认其字段语义。
- `POST /dayparting/LineItemIdApply`（0 流量）：line item 级别的创建入口，同上。

---

## 小结

- 29 条 Happy Path case（15 个只读/校验类接口，覆盖全部真实场景，2 次连跑 100% PASS）。
- 13 个接口因高风险/无法确认自建数据边界跳过（本文件）。
- 1 个接口（`updateTemplate`）因确认的功能性/环境问题跳过，建议报给研发。
- 24 个接口（7 个 GET + 17 个 POST）ES 90 天内 amazon 平台无真实流量，按"ES 无流量"规则跳过，已在 Excel 标注（不在本文件重复列出）。
