# sov-hub 用户指定排除接口清单

- 来源：用户提供的 14 张 swagger-ui 截图（2026-09-24）
- 性质：业务/权限层面明确不需要测试的接口（内部运维、内部服务间调用、健康检查、社媒/Itsumo/品牌重定向等模块），与 ES 90天无流量清单是两套独立机制，**不做 ES 流量判断，直接跳过**
- 总接口 **299**　排除 **64**　待覆盖 **235**

## 按模块(Tag)排除清单

| 模块(Tag) | Method | Path | 说明 |
|---|---|---|---|
| Admin | POST | /api/sov/admin/change-owner | 批量替换监控数据 owner（category / monitor_keyword_user 等） |
| BrandRedirect | POST | /api/sov/brand-redirect/addAsinBrand | 新增 ASIN 品牌关联 |
| BrandRedirect | POST | /api/sov/brand-redirect/checkDuplicatedAsins | 校验 ASIN 是否重复/存在 |
| BrandRedirect | POST | /api/sov/brand-redirect/deleteAsinBrand | 删除 ASIN 品牌关联 |
| BrandRedirect | POST | /api/sov/brand-redirect/editAsinBrand | 编辑 ASIN 品牌关联 |
| BrandRedirect | POST | /api/sov/brand-redirect/getAsinInfoForSov | 查询 ASIN 信息（Doris） |
| BrandRedirect | POST | /api/sov/brand-redirect/list | 获取品牌重定向列表 |
| Customized Report | DELETE | /api/report/deleteConfig/{reportId} | 删除报表配置 |
| Customized Report | POST | /api/report/getConfigById | 按 id 查配置 |
| Customized Report | POST | /api/report/getConfigPage | 配置分页 |
| Customized Report | POST | /api/report/getTargetSOV/export | 导出 Target SOV Excel |
| Customized Report | GET | /api/report/getTargetSOV/{reportId} | 查询父级 Target SOV 配置 |
| Customized Report | POST | /api/report/getTargetSOVTab | Target SOV Tab |
| Customized Report | POST | /api/report/getTargetSOVTrend | Target SOV 趋势 |
| Customized Report | GET | /api/report/getTargetTagSOV/{reportId} | 查询 Campaign Tag 级 Target 配置 |
| Customized Report | POST | /api/report/saveConfig | 保存报表 Tag 配置 |
| Customized Report | POST | /api/report/saveTargetSOV | 保存父级 Target SOV（先删后插） |
| Customized Report | POST | /api/report/saveTargetTagSOV | 保存 Campaign Tag 级 Target（按 reportId+tagName upsert） |
| Data Compare | POST | /api/sov/compare/brand-sov | 品牌指标一致性对比（by-device vs page） |
| Data Compare | POST | /api/sov/compare/brand-weekly-sov | 品牌周/月度指标一致性对比（weekly-performance vs page） |
| Data Compare | POST | /api/sov/compare/dashboard-accuracy/run | Dashboard 数据准确性验证 |
| InternalBrand | GET | /api/sov/internal/brand/list | 按 clientId+productLine 查平台级品牌（my/other） |
| InternalCategory | GET | /api/sov/internal/category/detail | 按 categoryBatchId 查各 productLine 维度配置 |
| InternalCategory | POST | /api/sov/internal/category/keyword-count | 批量按 categoryBatchId 统计 keyword 数 |
| InternalCategory | GET | /api/sov/internal/category/retailer-markets | 各平台可用市场（按 monitor_retailer.market 汇总） |
| InternalCategory | GET | /api/sov/internal/category/retailers | 按 productLine 查平台级全量 retailer/store |
| InternalQuota | POST | /api/sov/internal/quota/check | 配额只读预校验 |
| InternalQuota | POST | /api/sov/internal/quota/hub-keyword-used | hub 关键词槽位已用量与总上限 |
| Itsumo Organic Rank | POST | /api/sov/organicRank/asin-detail | ASIN 详情（导出 Excel） |
| Itsumo Organic Rank | POST | /api/sov/organicRank/asins/all | 全部 ASIN 列表（关键词维度 SOV，分页） |
| Itsumo Organic Rank | GET | /api/sov/organicRank/checkUserQuota/{addQuota} | 预校验再添加若干关键词槽位是否足够 |
| Itsumo Organic Rank | POST | /api/sov/organicRank/favorites | 保存收藏 ASIN |
| Itsumo Organic Rank | POST | /api/sov/organicRank/favorites/query | 收藏 ASIN 分页列表 |
| Itsumo Organic Rank | DELETE | /api/sov/organicRank/favorites/{id} | 删除收藏 ASIN |
| Itsumo Organic Rank | POST | /api/sov/organicRank/keyword-detail | 关键词详情（导出 Excel） |
| Itsumo Organic Rank | GET | /api/sov/organicRank/keywords | 监控关键词列表 |
| Itsumo Organic Rank | POST | /api/sov/organicRank/keywords | 添加监控关键词 |
| Itsumo Organic Rank | GET | /api/sov/organicRank/keywords/distinct-count | 去重关键词数 |
| Itsumo Organic Rank | DELETE | /api/sov/organicRank/monitor-keywords | 删除监控关键词 |
| Itsumo Organic Rank | GET | /api/sov/organicRank/quota | 用户 Itsumo 配额 |
| MigrationAmazonCategory | POST | /api/sov/migration-amazon-category/page | 分页查询 Amazon 类目迁移映射 |
| SOV Insight | POST | /api/sov/insight/cannibalization | 自竞争检测 |
| SOV Insight | GET | /api/sov/insight/favorite-group | 获取收藏分组列表（含异常计数） |
| SOV Insight | POST | /api/sov/insight/favorite-group | 添加/更新收藏分组 |
| SOV Insight | POST | /api/sov/insight/high-rank-terms | 高排名词 SOV 低检测 |
| SOV Insight | POST | /api/sov/insight/keyword | 关键词维度洞察 |
| SOV Insight | POST | /api/sov/insight/keyword-asin | 自竞争关键词-ASIN 对 |
| SOV Insight | POST | /api/sov/insight/my-brand-dropped | 我的品牌 SOV 下降检测 |
| SOV Insight | GET | /api/sov/insight/my-brands | 获取我的品牌名列表 |
| SOV Insight | POST | /api/sov/insight/my-brands | 按类目获取我的品牌名列表（最近 30 天 SOV 数据中出现过的） |
| SOV Insight | POST | /api/sov/insight/new-brand-sprout | 新品牌冒头检测 |
| SOV Insight | POST | /api/sov/insight/not-in-top4 | ASIN 不在 Top4 检测 |
| SOV Insight | POST | /api/sov/insight/top-brand-dropped | 竞品品牌下降检测 |
| Snapshot | POST | /api/sov/snapshot/export/async | 快照异步导出 |
| Social Momentum | POST | /api/sov/social-momentum/brand/download | 品牌 SOV 下载（Excel，social 专用） |
| Social Momentum | POST | /api/sov/social-momentum/brand/page | 品牌 SOV 列表（分页，social 专用） |
| Social Momentum | POST | /api/sov/social-momentum/brand/trend | 品牌 SOV 趋势（social 专用） |
| Social Momentum | POST | /api/sov/social-momentum/group | 保存 Group（幂等 upsert，不做 quota 校验） |
| SovHealth | POST | /api/sov/health/asin-brand/record | 新增 asin-brand 更新记录 |
| SovHealth | DELETE | /api/sov/health/asin-brand/record | 删除 asin-brand 更新记录 |
| SovHealth | POST | /api/sov/health/asin-brand/record/page | 分页查询 asin-brand 更新记录 |
| SovHealth | POST | /api/sov/health/asin-brand/sync | 同步 asin-brand 更新记录 |
| SovHealth | GET | /api/sov/health/monitor | 近期监控健康 |
| health-controller | GET | /health |  |
