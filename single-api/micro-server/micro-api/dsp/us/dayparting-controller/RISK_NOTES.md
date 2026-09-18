# dayparting-controller (micro-api, dsp, us) — 风险标记接口

本模块（含 calendar-center-controller / platform-dict-controller）共 54 个有效接口。本文件记录**判定为高风险、直接跳过（不做任何探测性调用）的写操作接口**，以及 `updateTemplate` 的验证性调用结果。

## 结论继承自 amazon / citrus 已验证的服务级发现（与平台无关，dsp 同样适用）

`single-api/micro-server/micro-api/amazon/us/dayparting-controller/RISK_NOTES.md` 已确认：**该服务（micro-api dayparting-controller）的写接口对测试账号不做跨 client 权限隔离**——写调用会对请求体里指定的任意真实客户数据真实生效，且无回滚接口可核实原状态。这一结论是服务级、与平台无关的，dsp 平台的 dspautous 账号（clientId=2938）同样适用。

## 高风险写操作接口（一律跳过，不做任何探测性调用）

以下 13 个接口无论 ES 流量如何，dsp 平台同样直接跳过，理由与 amazon RISK_NOTES.md 一致（批量/删除/状态变更类写操作，无法安全自建可回滚的测试数据）：

1. `DELETE /dayparting/campaigns`（`deleteCampaignDayparting`）
2. `POST /dayparting/deleteTemplate`（`deleteTemplates`）
3. `POST /dayparting/deleteApply`（`deleteApply`）
4. `POST /dayparting/deleteDetailApply`（`deleteDetailApply`）
5. `POST /dayparting/bulk/pausecampaigns`（`bulkPausedCampaigns`）
6. `POST /dayparting/changeStatus`（`changeCampaignSchdulerStatus`）
7. `POST /dayparting/changeOwner`（`changeOwner`）
8. `POST /dayparting/appoint`（`appointDayparting`）
9. `POST /dayparting/apply-switch`（`switchDayparting`）
10. `POST /dayparting/status-switch`（`switchDaypartingStatus`）
11. `POST /dayparting/setTemplateAndApply`（`setTemplateAndApply`）
12. `POST /bulk/set/dayparting`（`setBulkBolDayParting`）

**新增红线项（citrus 平台发现，同样适用于 dsp）：**

13. `POST /bulk/update/campaigns/bid`（`bulkChangeOriginalBid`）——批量修改真实出价，无回滚接口，一律跳过。

以上 13 个接口，dsp 平台未做任何调用（包括探测性调用），未生成 case。

**新增红线项（本轮 dsp 21接口任务新核实，与 bol/chewy/criteo/target/kroger/walmart 已有发现一致）：**

14. `POST /update/campaign/bid`（`changeOriginalBid`）——请求体含 `bid`/`targetId`/`profileId`，语义是修改单条真实出价，与 `bulk/update/campaigns/bid` 同构，无回滚接口，一律跳过。dsp 平台该接口 ES 近365天流量为 0（全平台90天内共198次真实调用，但均非 productLine=dsp），因此即使流量为0也按"确认写操作"红线跳过，而非按"ES无流量"处理，避免归类含糊。
15. `POST /update/dayPartingChangeTimeZone`（`dayPartingChangeTimeZoneChange`）——Swagger summary 明确写明"根据时区更新bid值点位"，请求体含开始/结束时间+action数组，是根据时区变更改写bid点位数据的写操作。dsp 平台及全平台 ES 90天内流量均为 0，同样按"确认写操作"红线跳过。

以上 15 个接口，dsp 平台未做任何调用（包括探测性调用），未生成 case。

## `POST /dayparting/updateTemplate` — 验证性调用结果（dsp）

按任务要求，仅做**一次**干净的验证性调用：回放 dspautous 账号（clientId=2938，实际操作子账号 userName=dspustest2024/userId=20152）自己名下的真实历史请求体，未做任何字段修改。

- **回放数据来源**：ES `dayparting-schedule-api-*` 中 clientId=2938 近 365 天 `POST /dayparting/updateTemplate` 的最新一条记录（`@timestamp=2026-09-15T01:24:54Z`），`id=27090`，`tempName="test0515-03"`，`productLine=dsp`，`profileId=578107614358724215`（lineItemIds/lineItemTags 中）。
- **调用方式**：请求体与 ES 记录逐字节一致（未替换任何字段），仅补充当前登录 Authorization/productline header。
- **结果**：`HTTP 200`
  ```json
  {
    "code": 200,
    "data": {
      "sucessNums": 2,
      "failNums": -2,
      "totalNums": 0,
      "message": "Total:0,Success:2,Failed:-2",
      "addSuccessTags": [{"id":"1871839658789355522","name":"334","profileId":"578107614358724215"}],
      "addSuccessCampaigns": [
        {"id":"576498614884942144","name":"autoTestCreation_lineItem_20260911092247","profileId":"578107614358724215"},
        {"id":"576506443794904197","name":"Prospecting - Display","profileId":"578107614358724215"}
      ]
    }
  }
  ```
- **模式判定**：`code:200` 且 `sucessNums=2 (>=1)` → **属于"真实生效"模式**，与 **samsclub / citrus 一致**（区别于 amazon 的 500 缺陷模式、instacart 的 `sucessNums:0` 空操作模式）。
- **各平台 updateTemplate 复现结果汇总**：
  | 平台 | 结果 | 模式 |
  |---|---|---|
  | amazon | HTTP 500（任意 body 均 500） | 确认缺陷 |
  | instacart | HTTP 200, sucessNums:0 | 空操作 |
  | samsclub | HTTP 200, sucessNums:1 | 真实生效 |
  | citrus | HTTP 200, sucessNums:1 | 真实生效 |
  | **dsp** | **HTTP 200, sucessNums:2** | **真实生效** |
- **风险披露**：本次回放的字段（lineItemIds/lineItemTags/advertiserIds/action 等）与该模板此前已保存的状态完全一致（未做任何修改），是对已有状态的等幂重放，未引入新数据、未改变模板的实际配置内容。但该调用确认了该模板对应的 line item 关联关系被重新落库（`addSuccessCampaigns`/`addSuccessTags` 返回非空），属于真实写入。
- **结论**：由于 `deleteTemplate` 仍在上方红线名单内，无法安全自建自清理闭环，**本次未生成 `updateTemplate` 的自动化 case**，仅记录此次验证结果，未再做第二次调用。

## `POST /dayparting/templateNames` — 确认后端缺陷（dsp，本轮新发现）

生成 case 执行时发现：使用真实用户历史请求体（含非空 `userIds` 数组）回放会稳定返回 **HTTP 500**，即使字段值与 ES 记录中账号自己的真实历史请求体逐字节一致也复现。为定位根因，做了系统性字段隔离测试（均使用 dspautous 账号自己的 token，未涉及其他客户数据）：

- 仅 `productLine` + `profileIds` + `pageInfo` → **200**
- 依次追加 `clientId` / `advertiserIds=null` / `tempName=null` / `fliterQuery=false` / `datePattern=null` → 均 **200**
- 追加 `userIds=[14495]`（本账号 root_user_id）→ **500**
- `userIds=[]`（空数组）→ **200**；`userIds` 字段整体不传 → **200**
- `userIds` 为非空数组时，无论元素是 int/string、单个/多个、本账号真实用户ID，一律 **500**（已排除数据本身错误的可能，是字段结构触发的服务端异常）

**结论**：`POST /dayparting/templateNames` 在 dsp 平台下，请求体一旦包含非空 `userIds` 数组即触发服务端 500，是**确认的后端缺陷**（区别于正常业务失败）。对照 citrus 平台同一字段结构（`userIds: ["{{root_user_id}}"]`）测试通过（PASS），说明该缺陷是 **dsp 平台特有**，不是通用请求体结构问题。而 ES 真实流量显示 dsp 用户请求 `templateNames` 时绝大多数会带上非空 `userIds`（该字段是模板列表页的"创建人"筛选条件），因此该缺陷在生产环境应有实际影响面。

**处理方式**：未修改 case 的请求体去回避该缺陷（case 仍如实反映真实用户会用到 `userIds` 筛选的两个高频场景），保留为 **FAIL**，作为缺陷证据留痕，供开发排查。详见 `task-2026-09-15-16-29-34/report.json` 中 `POST /dayparting/templateNames` 的两条失败记录。

### 🔴 跨平台对比：`templateNames` 在 bol / chewy / dsp 三个平台各自出现不同触发条件的 500，应作为同一接口的多个健壮性问题分别打包反馈研发，不要笼统合并成一条

| 平台 | 触发字段 | 触发条件 | 不触发条件 | 是否与具体取值相关 | 性质判断 |
|---|---|---|---|---|---|
| **bol** | `userIds` | 传入 `root_user_id`（93）这个**特定值** | 传入账号登录自身的 `user_id`（18589）→ 200 正常 | 是，仅特定 userId 值触发（疑似该 id 在 bol 产品线用户表缺记录，反查空指针） | 特定值触发的空指针类缺陷 |
| **chewy** | `profileIds` | 字段为**非 null**（无论值是什么，含单值/多值/空数组`[]`/虚构不存在的id） | 仅 `profileIds` 整体为 `null` → 200（退化为查全部模板） | 否，与具体值无关，只要非null即触发 | 观测到具有时间窗口性（同一时刻回放 citrus 侧刚 PASS 的历史请求也复现 500，疑似服务侧短时窗口的一次回归/部署问题，非稳定的字段级缺陷） |
| **dsp** | `userIds` | 字段为**非空数组**（无论值是什么，含账号自己的真实 userId、单个/多个） | `userIds=[]` 或字段不传 → 200 | 否，与具体值无关，只要非空数组即触发 | 稳定可复现的字段级缺陷（非时间窗口性，多次重试结果一致） |

三者字段不同（bol/dsp 是 `userIds`，chewy 是 `profileIds`），触发条件也不同（bol 是特定值、chewy 与 dsp 是"非空/非null即触发"但一个精确到 null 判断一个精确到空数组判断），且 chewy 观测到疑似时间窗口性而 dsp/bol 未观测到该现象。**这是 `templateNames` 接口在不同字段、不同条件下暴露的至少 2-3 处独立健壮性问题，不应合并成一条"userIds/profileIds 传值导致500"笼统反馈**，建议分别列出上表三行给研发定位。

## 小结

- 15 个接口因高风险写操作跳过（未做任何调用，含本轮新确认的 `update/campaign/bid`、`update/dayPartingChangeTimeZone`）。
- 1 个接口（`updateTemplate`）仅做 1 次验证性调用，确认为"真实生效"模式，未生成 case。
- 1 个接口（`templateNames`）生成了 2 条 Happy Path case，均因确认的后端缺陷（非空 `userIds` 触发 500）FAIL，详见上节。
- 其余接口按 ES 真实流量正常生成 case 或标注"ES 无流量"，见 dayparting-controller / calendar-center-controller / platform-dict-controller 各自 task 目录下的 cases.json/report.json。
