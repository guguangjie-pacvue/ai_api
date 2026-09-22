# definition-controller (citrus, us) — 14 个未生成/未执行接口说明

生成时间：2026-09-14

本文档只覆盖 definition-controller 51 个接口中的 14 个"结构性/高风险"子集（其余 37 个
"正常"接口由另一 agent 负责，产物在本目录同级的其它 `task-*/` 子目录下，本文件不涉及、不覆盖）。

这 14 个接口在 kroger 平台被判定为跳过（见
`single-api/services/rule-api/kroger/us/definition-controller/RISK_NOTES.md`）。本次**未直接
沿用 kroger 的结论**，而是针对 citrus 重新独立核查：读 Swagger 请求体结构、查 ES 真实流量
（citrus + 全平台）、用 citrus 测试账号真实 token/profileId 做只读探测（不调用任何写接口）。
结论：**14 个全部维持跳过**，但其中 Adtomic/mapping 相关接口的"跳过理由"与 kroger 并不完全相同
——citrus 的实测行为与 kroger 有明显差异（citrus 不报错、返回真实数据），只是深入核查后确认
仍然没有真正可安全测试的数据，具体见下文。

---

## 一、TikTok 平台专属接口（5 个，结构性事实，无需查 ES）

路径本身在 URL 中硬编码 `tiktok`，与调用方 `productline` header 是 citrus 还是别的平台无关
——这是接口路径命名的结构性事实，不随平台变化，也不需要 ES 流量佐证：

| 接口 |
|---|
| POST /bulk-create/tiktok/roas-explorer |
| POST /bulk-create/tiktok/smart-budget-boost |
| POST /query-rule-ids/tiktok/roas-explorer |
| POST /query-rule-ids/tiktok/smart-budget-boost |
| POST /tiktok/roas-explorer/reminder |

## 二、Adtomic 专属子系统接口（5 个：createAdtomicRule / editAdtomicRule / delete / adtomic GET / getAdtomicRules）

**独立核查方法**：
1. ES `query_es.py` 精确路径查询：`/createAdtomicRule`、`/definition/editAdtomicRule`、
   `/definition/getAdtomicRules`（POST，citrus 过滤 + 全平台不过滤两种口径），近 180 天：
   **citrus: 0 hits；全平台: 0 hits**（三个接口均为 0，见下方原始命令输出）。
2. ES `es_helper.py wildcard-agg` 探测 ID 替换后的真实路径（`/definition/delete/{adtomicRuleId}`
   POST、`/definition/adtomic/{adtomicRuleId}` GET）：各命中 1 条（`total=1`），但用
   `samples --no-exclude-test` 反查发现两条命中均为 **clientId=62**（研发/QA 内部测试账号，
   时间戳 `2026-09-10`，与本次任务时间窗高度吻合，判定为其他模块测试探测产生的噪声，非真实
   客户流量），排除后仍为 0 真实流量。
3. **活体探测（只读，未调用任何写接口）**：用 citrus 测试账号真实登录 token +
   `productline: citrus` + 真实 `profile_id=0acae067-00b9-411f-a614-09ca7bc3a12b` 调用
   `POST /definition/getAdtomicRules`（body：`{"productLine":"citrus","pageInfo":{"pageIndex":1,
   "pageSize":50},"adtomicProfileIds":["0acae067-..."]}`）：
   - **结果与 kroger 不同**：kroger 稳定返回 405 NPE；citrus 返回 **HTTP 200**，`code:200`，
     真实分页数据，`totalCount:7`，返回 7 条该 profile 下的真实规则（如
     `lj_lead1_user2_tag`、`Debug for AT-1429`、`autotest_rule_opt_manual` 等）。
   - **但深入检查这 7 条记录的 Adtomic 关联字段**：`adtomicRuleType`、`ruleAdtomicId`、
     `ruleAdtomicName`、`adtomicProfileId` **全部为 `null`**（7/7）。说明这个接口对 citrus
     账号并不报错，但它返回的只是该 profile 下的**普通规则**（ruleType=Campaign/Keyword，
     经标准 `/definition` 创建），**没有任何一条是真正通过 Adtomic 子系统创建/关联的规则**
     ——即 citrus 测试账号下不存在真实 `adtomicRuleId`，与 kroger"无此类实体"的结论一致，
     只是 citrus 后端实现对空结果的处理方式不同（不抛 NPE，而是优雅返回普通规则列表）。

**结论（按接口）**：
- **POST /definition/getAdtomicRules**：活体探测虽然成功（HTTP 200 有真实数据），但 ES 近
  180 天**全平台 0 次真实调用**（citrus 和其它平台均无）。按任务铁律"ES 上查不到真实流量的
  接口绝对不能生成 case，也不能执行"，即使活体探测证明接口本身可用，**仍必须跳过**（这是
  规则要求的，不是接口不可用）。
- **POST /createAdtomicRule、POST /definition/editAdtomicRule**：ES 0 真实流量（全平台），
  且未执行（写操作，Phase 3.5 要求先有真实 pre-existing adtomicRuleId 才能安全测 edit/delete，
  当前不存在；创建一条全新 Adtomic 规则纯属为了造数据而造数据，违反"禁止为了生成 case 而
  捏造规则/映射"的红线，故不调用）。
- **POST /definition/delete/{adtomicRuleId}**、**GET /definition/adtomic/{adtomicRuleId}**：
  ES 唯一命中均为 clientId=62 测试噪声，非真实业务流量；且 citrus 测试账号下经
  getAdtomicRules 核实**不存在任何真实 adtomicRuleId**（7 条候选规则 ruleAdtomicId 全 null），
  没有可用的真实 ID 可供测试，也不允许伪造 ID，跳过。

## 三、无法安全构造映射数据（2 个：downloadMapping / downloadMapping/{id}）

**独立核查方法**：
1. ES 精确查询 `/downloadMapping`（POST，citrus 过滤 + 全平台）：**0 hits**。
2. ES `wildcard-agg` 探测 `/downloadMapping/{id}`：命中 1 条真实路径
   `/downloadMapping/2097972824280858626`，`samples --no-exclude-test` 反查同样是
   **clientId=62** 测试噪声（同一时间窗），非真实客户流量。
3. **活体探测（只读）**：用 citrus 真实存量规则 `real_rule_id=2098299714324836354`
   （config.json 中记录的真实 citrus 规则，ruleType=Campaign，非 Adtomic 创建）分别调用
   `POST /downloadMapping`（body `{"id":2098299714324836354}`）和
   `POST /downloadMapping/2098299714324836354`：
   - 两次均返回 **HTTP 200**，`Content-Type: application/vnd...spreadsheetml.sheet`
     （真实 xlsx 文件，非报错）。
   - 解压 xlsx 检查 `xl/worksheets/sheet1.xml`：`<dimension ref="A1"/>`，`sheetData` 里只有
     一个空行（`<row r="1" .../>`，无单元格数据），即**返回的是一份空白模板，没有任何真实
     映射数据行**。这与该规则并非 Adtomic 创建、其 `ruleAdtomicId` 为 null 的事实完全吻合
     ——不存在真实的 mapping 数据可供验证。

**结论**：downloadMapping 系列接口对 citrus 不报错（与 kroger 表现不同，kroger 场景未见此
探测细节，但同样无数据），但 ES 无真实流量 + 活体探测证实无真实映射数据可测，跳过。

## 四、不安全的批量/客户级操作（2 个：automationPauseAsins、terminatedClientRule）

**独立核查方法**：
1. ES 精确查询两接口（POST，citrus 过滤 + 全平台）：**均 0 hits**（citrus 和全平台近 180 天
   均无真实调用）。
2. **重新读取 Swagger 请求体结构**（未直接采信 kroger 文档描述，自行从
   `/tmp/swagger_cache/swagger_rule-api.json` 的 `components.schemas.RuleChangeRequest`
   核实）：两接口请求体共用同一 schema `RuleChangeRequest`：
   ```json
   {
     "ruleId": "integer(int64)",
     "ruleIds": "array<integer(int64)>",
     "isPaused": "boolean",
     "isDelete": "boolean",
     "clientId": "integer(int64)",
     "userId": "integer(int64)",
     "userName": "string"
   }
   ```
   独立核查确认：**`ruleId`/`ruleIds` 均非 required 字段**（Swagger 无 `required` 数组），
   `clientId` 是与 `ruleId(s)` 并列的独立字段，**schema 层面没有任何约束表明后端一定会用
   `ruleId(s)` 精确限定作用范围**——无法排除后端实现里 `clientId` 单独生效、对该 client 下
   全部规则做批量暂停/终止的可能性（`terminatedClientRule` 的接口命名本身就是"终止某客户
   规则"，语义上就是客户级操作，而非规则级操作）。这一风险判断是基于**接口本身的请求体
   结构**，与调用者是 kroger 还是 citrus 无关（两平台共用同一份 `RuleChangeRequest` schema），
   citrus 独立复核后同样成立。

**结论**：ES 无真实流量 + 请求体结构无法证明作用范围安全限定，跳过（不做活体探测，因为
一旦请求体解读有误、真实调用可能造成 client 级批量副作用，任务要求"高风险批量/客户级操作
无论 ES 流量如何都跳过"）。

---

## 附：ES 原始查询命令与结果摘要

```
query_es.py --path /definition/getAdtomicRules --method POST --platform citrus --days 180 -> 0 hits
query_es.py --path /definition/getAdtomicRules --method POST --days 180 (全平台)          -> 0 hits
query_es.py --path /createAdtomicRule          --method POST --platform citrus --days 180 -> 0 hits
query_es.py --path /createAdtomicRule          --method POST --days 180 (全平台)          -> 0 hits
query_es.py --path /definition/editAdtomicRule --method POST --platform citrus --days 180 -> 0 hits
query_es.py --path /definition/editAdtomicRule --method POST --days 180 (全平台)          -> 0 hits
query_es.py --path /downloadMapping            --method POST --platform citrus --days 180 -> 0 hits
query_es.py --path /downloadMapping            --method POST --days 180 (全平台)          -> 0 hits
query_es.py --path /automationPauseAsins       --method POST --platform citrus --days 180 -> 0 hits
query_es.py --path /automationPauseAsins       --method POST --days 180 (全平台)          -> 0 hits
query_es.py --path /terminatedClientRule       --method POST --platform citrus --days 180 -> 0 hits
query_es.py --path /terminatedClientRule       --method POST --days 180 (全平台)          -> 0 hits

es_helper.py wildcard-agg --prefix /definition/delete/  --method POST --days 180 -> total=1 (clientId=62 噪声)
es_helper.py wildcard-agg --prefix /definition/adtomic/ --method GET  --days 180 -> total=1 (clientId=62 噪声)
es_helper.py wildcard-agg --prefix /downloadMapping/    --method POST --days 180 -> total=1 (clientId=62 噪声)
```

活体探测（只读，未调用任何写操作/未产生任何数据变更）：
- `POST /definition/getAdtomicRules`（真实 citrus token + profile_id）→ HTTP 200，返回 7 条
  真实规则，全部 `ruleAdtomicId=null`（无真实 Adtomic 关联）。
- `POST /downloadMapping` 与 `POST /downloadMapping/{real_rule_id}`（真实 citrus 存量非-Adtomic
  规则 id=2098299714324836354）→ HTTP 200，返回空白 xlsx（单空行，无数据）。

---

## 结论

以上 14 个接口本次在 citrus 平台经独立核查（Swagger 结构重读 + ES 全量/citrus 过滤查询 +
只读活体探测）后，**结论与 kroger 一致：全部跳过、未生成 cases.json、未执行**。其中
Adtomic/mapping 相关接口的**实测行为与 kroger 不同**（citrus 不报错、能返回真实数据/文件），
但深入检查确认返回内容里均无真正的 Adtomic 关联数据（`ruleAdtomicId` 全为 null、mapping
文件为空白模板），且这些接口 ES 近 180 天全平台真实调用为 0（不含 clientId=62/3186 测试噪声），
按任务铁律不允许生成/执行 case。批量/客户级操作（automationPauseAsins、terminatedClientRule）
的跳过理由经独立重读 `RuleChangeRequest` schema 确认为接口本身结构性风险，与平台无关，
citrus 与 kroger 结论一致。
