# Kevel 测试数据与真实接口契约（1f18987 / CP-47435）

> 通过读源码 + provider 实测得到，纠正之前盲猜的路径/参数。

## 🔴 纠正：真实接口路径（swagger 路径名 ≠ 实际 mapping）

| 意图 | 之前误用 | **实际** | body |
|------|---------|---------|------|
| 创建规则 | `/definition/createRule`（不存在） | **`POST /definition`** | `RuleRequest` |
| 编辑规则 | — | `POST /definition/editRule` | `RuleRequest` |
| 启停/删规则 | — | `POST /definition/changeStatus` | `RuleChangeRequest` |
| Apply-to 候选 | `getTarget` | `POST /definition/getTarget` → `ruleManager.getTarget(req, clientId, productLine)` | `RuleParam` |

- `getTarget` 按 **clientId(当前 token=62) + productLine** 过滤，返回 0 —— rule 侧候选查询与 provider 数据是两条路，rule 侧当前查不到。
- **不必依赖 getTarget**：真实 campaign/flight ID 可从 provider 直接取，直接塞进 createRule 的 `applyTarget.targetInfo`。

## Provider 实体接口（数据源，已验证可用）

| 接口 | 说明 |
|------|------|
| `GET https://api-test.pacvue.com/kevel-dev/user/profiles` | 4 个 profile |
| `POST kevel-dev/user/getCampaigns` `{profileId}` | 96 campaign |
| `POST kevel-dev/user/getAdGroups` `{profileId}` | 111 flight（55 Enabled） |

## 真实测试数据（profile 6274332 Waitrose）

| 用途 | 值 |
|------|-----|
| Enabled Flight（有 budget） | adGroupId=863338711, campaignId=659202073, bid=1.0, dailyCap=190 |
| Enabled Flight（有 budget，小值） | adGroupId=863288736, campaignId=659204672, bid=12.0, dailyCap=1.0 |
| Enabled Flight（**无 dailyCap**，测 R-2 不命中） | adGroupId=863280894, campaignId=659202120, bid=566.0, dailyCap=null |
| Enabled Campaign | campaignId=659202073 |

## createRule（POST /definition）body 骨架

```json
{
  "ruleType": "KevelFlight",
  "ruleName": "vdiff-1f18987-<场景>",
  "productLine": "kevel",
  "mode": "Auto",
  "frequency": "daily",
  "applyTarget": {
    "targetLevel": "Flight",
    "profileId": [6274332],
    "targetInfo": [ { "profileId": "6274332", "targetId": "863338711" } ]
  },
  "automation": [
    {
      "requirements": [[ { "field": "Bid", "operand": "Greater", "value": "0.5", "valueType": "Custom" } ]],
      "action": { "action": "Pause" }
    }
  ]
}
```

- `requirements`: `array<array>`（外层 OR、内层 AND 的条件组），元素是 `Filter`
- `action.action` 枚举含 `Pause/Enable/...`；Bid/Budget 动作用 `value`/`percentage`/`cap`/`floor`
- ⚠️ 待确认：`ruleType` 精确串（`KevelFlight` vs `Flight`）、`mode`/`frequency` 取值、Bid 的 `valueType` —— 首次 createRule 会以调试确认

## 🔴 状态变更风险

createRule 会创建规则，Pause/Bid/Budget 动作**可能真的改动 Waitrose 真实 Flight**。执行写操作 case 必须：
1. 建完立即 `changeStatus` 归档/删除（Phase 3.5 自清理）
2. 动作类优先选影响可逆或 Preview 类，避免真实改动生产实体
