# to-event (doordash/us) — 未生成/未执行接口说明

## POST /event/clearCacheTypes
双重原因跳过：
1. **ES 无流量**：ES `rule-api-access-*` 近90天、近180天查询（不限平台）均为 0 命中，全服务范围内该接口近半年无任何真实调用记录，不存在真实入参样本。
2. **管理/维护类操作，风险未清晰限定**：接口名语义为清除缓存类型（clearCacheTypes），属于运维/管理性质的写操作，即便有流量也需按任务要求审慎评估副作用与可回滚性；本次因无真实样本，直接跳过，未凭空构造。

未生成该接口的 case，未执行。

## POST /event/getRuleCountByCampaignIds
该接口请求体含 `productLine` 字段（可按平台归因，但部分历史请求未携带该字段）。按 `body.productLine.keyword:doordash` 过滤，近90天、近180天查询均为 0 命中。近90天全平台真实调用共24条，均为 `amazon` 或未携带 `productLine` 字段，无 doordash 真实调用可参考。按 ABSOLUTE RULE（ES 无流量禁止生成、禁止执行，不得借用其他平台请求体），本次未生成该接口的 case。

## POST /event/getRuleCountByUserIds
同上：按 `body.productLine.keyword:doordash` 过滤，近90天、近180天查询均为 0 命中；近90天全平台500条抽样分布为 `amazon`(487)/`instacart`(5)/`walmart`(5)/`criteo`(2)/`target`(1)，doordash 占比为0。未生成 case。

---

已生成并执行通过的接口：`POST /event/getRuleDefinition`（请求体不含 productLine，全平台基线，100% 单 ruleId 场景）、`POST /event/getRuleTypes`（无入参，全平台基线，100% 空 body 场景），详见同目录 `task-2026-09-14-09-13-28/cases.json` 与 `report.json`（2/2 PASS）。
