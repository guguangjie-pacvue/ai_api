# 写操作类 case 模板（创建 + 后置归档）

> SKILL.md Phase 3.5 引用。铁律（成对操作、archive 不物理删、extract_vars 抓 ID、业务成功信号断言、幂等连跑 2 次）见 SKILL.md 正文，此处仅存可直接套用的 JSON 模板与值探测清单。

## 模板

```json
{
  "name": "POST /api/xxx/CreateXxx - <场景>(含后置清理,可重复)",
  "description": "...第2步后置操作将新建实体归档,保证用例可重复执行。",
  "module": "<模块>",
  "granularity": "API",
  "since": "init", "last_modified": "init",
  "change_type": "NEW", "generated_by": "swagger-api-case",
  "steps": [
    {
      "name": "创建 <实体>",
      "method": "POST", "base_url": "{{BASEURL}}", "path": "/xxx/CreateXxx",
      "request_body": { "...": "..." },
      "extract_vars": { "created_entity_id": "data.result[0].APIResult[0].entityId" },
      "expected_response": { "code": 200, "success": true, "data": { "successCount": { "$gte": 1 } } }
    },
    {
      "name": "后置清理-归档新建实体",
      "method": "POST", "base_url": "{{BASEURL}}", "path": "/xxx/UpdateXxxStatus",
      "request_body": { "Item": [ { "TargetId": "{{created_entity_id}}", "...": "..." } ], "state": "archived" },
      "extract_vars": {},
      "expected_response": { "code": 200, "success": true, "data": { "successCount": { "$gte": 1 } } }
    }
  ]
}
```

## 写操作类值探测（因涉及真实写库，主动排查再定稿）

- **写操作必须落到能接收的真实层级**：从测试账号真实数据里找有效 campaign/adgroup（如 SP 手动-PAT 广告组、SD 广告组），不可用查询类 case 的 profile 直接套。规则托管广告组可能拒绝手动写入。
- **bid 类约束**：Amazon 常见 `bid < 日预算的一半`，先查目标 campaign 的 DailyBudget 再定 bid。
- **枚举/类型值以 ES 真实样本为准**：如 SD 商品定向 clause `type` 真实值为空串 `""`（不是猜的 `T00030`）。无样本不猜。
