---
name: swagger-version-diff
description: 接口版本变更测试。对比基线 Swagger（线上）与目标 Swagger（测试环境新版本），识别新增/删除/修改的接口，生成对应测试 case，在测试环境执行并输出报告。当用户要"测试某个版本的接口变更"、"比对两个版本的接口差异"、"新版本接口测试"时使用本 skill。
---

# swagger-version-diff（接口版本变更测试）

## 定位

| | swagger-api-case | swagger-version-diff |
|---|---|---|
| 输入 | 单个 Swagger URL | 基线 Swagger + 目标 Swagger + git commit |
| 目标 | 单接口全场景覆盖 | **版本变更接口的回归 + 新功能验证** |
| case 位置 | 模块目录下新建 task | **追加到现有模块 cases.json**（git 分支隔离） |
| `change_type` | 固定 `NEW` | `NEW` / `MODIFIED` / `REMOVED` |

---

## 🔴 Git 分支工作流（核心）

版本变更测试与开发分支对应，用 git 做版本控制：

```
main 分支
└── single-api/rule-api/<平台>/us/<模块>/task-xxx/cases.json   ← 线上回归基线

test/CP-47435 分支（对应开发的 ai/delivery/1f18987 分支）
└── single-api/rule-api/<平台>/us/<模块>/task-xxx/cases.json   ← 基线 + delta（直接追加）
```

| 阶段 | 操作 |
|------|------|
| 测试中 | 在 `test/CP-xxxxx` 分支追加 delta case，用 `config.test.json` 跑 |
| 回滚 | 放弃分支，main 完全不受影响 |
| 上线确认 | merge `test/CP-xxxxx` → `main`，基线自动更新 |

**🔴 本 skill 运行前，用户须已切换到对应的测试分支（如 `test/CP-47435`）。**

---

## 🔴 铁律

1. **基线 = 线上 Swagger，目标 = 测试环境 Swagger**：diff 方向固定，不反转
2. **Git commit 优先，swagger diff 做校验**：两者冲突时：
   - Git 有变更 + swagger 有对应变化 → 确认，生成 case
   - Git 有变更 + swagger 无对应变化 → 后端逻辑变更，仍生成 case（测行为不测结构）
   - Swagger 有变化 + git 无来源 → 测试环境混入其他分支，**排除本版本范围**，记录到 `diff.json.excluded_from_scope`
   - 两者完全矛盾 → 以 git commit 为准
3. **swagger diff 只能捕捉 API 签名变更**；行为变更（逻辑、精度、取整、枚举语义）必须从 git commit 推导
3b. 🔴 **源码是接口契约的权威，swagger 只作结构参考**：路径/必填参数/body 类型一律先读 Controller 源码确认（见 Phase 1.5），swagger 路径名 ≠ 实际 mapping、必填参数不全，照 swagger 猜必反复失败。契约表没确认完不许进设计。
3c. 🔴 **影响范围三维穷举（中台接口改动的骨架，见 Phase 0.6）**：每个被改接口都要从三个方向展开——**D1 本模块功能**（接口自身）+ **D2 本平台关联模块**（调用/被调用的上下游链，最易漏）+ **D3 跨平台**（共享代码辐射其它平台）。只测 D1 会漏掉"谁依赖它、它依赖谁"和"改 A 碰坏 B"。设计矩阵与覆盖基准都按三维组织。
4. **delta case 追加到现有 cases.json，不新建文件**：`since` 字段标记版本，git diff 天然记录增量
5. **若无现有 cases.json**（新平台/新模块）：先按 `swagger-api-case` 流程全量生成，再追加 delta
6. **since 字段写 git commit 短码**：如 `"1f18987"`
7. **禁止猜参数**：新增字段无 ES 样本时填 `"[NEEDS_REAL_VALUE]"`

---

## 输入

用户需提供：
1. **基线 Swagger URL**：线上版本，如 `https://api.pacvue.com/rule-api/v3/api-docs`
2. **目标 Swagger URL**：测试环境新版本，如 `https://api-test.pacvue.com/rule-api-dev/swagger-ui/index.html`
3. **git commit**：被测版本，如 `1f18987c806f481e8e52a474`
4. **服务名**：先查 `services.json` 匹配，未命中问用户

自动推断：
- **平台**：从 git commit 改动文件的 package 路径推断
- **测试环境 config**：从 `single-api/<服务>/<平台>/us/config.test.json` 读（同目录下 `config.json`=线上、`config.test.json`=测试，仅文件名区分环境）；不存在则复制 `config.json` 改 `RULEBASEURL` 生成

---

## Phase 0 — 获取两个 Swagger 文档

### 0.1 推断 JSON URL

- `swagger-ui/index.html` → 替换为 `v3/api-docs`
- 已是 JSON URL → 直接使用

### 0.2 下载

```powershell
$client = New-Object System.Net.WebClient
$client.DownloadFile("<baseline_url>", "$env:TEMP\swagger_baseline.json")
$client.DownloadFile("<target_url>",   "$env:TEMP\swagger_target.json")
```

---

## Phase 0.5 — 分析 Git Commit（🔴 在 swagger diff 之前必做）

```powershell
# 若 $env:TEMP\pacvue-services-tmp 不存在则先 clone
git clone --no-checkout --depth=1 --filter=blob:none https://github.com/Pacvue/services.git $env:TEMP\pacvue-services-tmp
Set-Location $env:TEMP\pacvue-services-tmp
git fetch origin "ai/delivery/<commit>" --depth=5
git log FETCH_HEAD --oneline -10
# 找与 production 的分叉点
git diff <merge-base>..FETCH_HEAD --name-status
```

从 commit 分析中提取：
1. **平台**：看改动文件 package（如 `kevel/`, `tiktok/`, `walmart/`）
2. **行为变更**：后端逻辑改动 → 记录到 `diff.json.behavior_changes`，针对性生成验证 case
3. **排除噪音基准**：swagger diff 中 commit 里找不到来源的变更 → 写入 `diff.json.excluded_from_scope`
4. 🔴 **共享代码改动 → 反查其它平台回归面（最易漏、最危险）**：把改动文件分两类——
   - **平台专属**（在某平台 package 内，如 `kevel/`）→ 只影响该平台
   - **共享**（平台包外的公共类/方法，如 `EmailTemplate/`、`manager/HistoryManager`、`enums/`、`Columns`）→ **所有走过该方法的平台都是回归面**
   对每个被改的共享方法，追问「哪些平台调用它、走哪个接口」，把这些**其它平台的接口纳入影响范围**，记录到 `diff.json.cross_platform_risk.shared_code_changes`（含 file/method/shared_by/regression_target）。
   - 判定共享：改动文件路径**不在**任何单一平台 package 下，或方法签名被所有平台复用（switch-case 加分支属于共享方法被改）。
   - 回归精确到「走过该共享方法的接口」，不是「全平台全接口」。纯追加式改动（枚举/列新增）风险低，除非有按 ordinal 序列化。

**🔴 merge-base 要用与 production 的真实分叉点**（`git merge-base FETCH_HEAD origin/production`），不能用中间的 "Merge production" 提交，否则漏掉合并前的改动（本 skill 踩过：错用后 73 文件只看到 4 个）。partial-clone 下先 `--depth=100` 加深两分支再求 merge-base。

---

## Phase 0.6 — 🔴 影响范围三维模型（中台接口改动的骨架）

一个中台接口改动，影响范围必须从**三个方向**穷举，缺一个都会漏测。对 Phase 0.5 找出的每个被改方法/接口，逐维展开：

| 维度 | 含义 | 从源码怎么推导 | 产出 |
|------|------|--------------|------|
| **D1 本模块功能** | 被改接口/方法自身的功能是否正确 | 接口自己的 diff（参数/逻辑/枚举/精度） | 该接口的功能 case（正常+边界） |
| **D2 本平台关联模块（调用/被调用）** | 同平台内**上下游调用链** | ①**被调用**：`git grep <方法名>` 反查谁调它 → 契约变则所有调用点回归 ②**调用**：读被改方法体，看它下游又调了谁 → 下游契约变则联动回归 | 上游调用点接口 + 下游联动接口 + 同平台模块连锁（如 建规则→执行→历史→邮件→报表 一条链） |
| **D3 跨平台** | 共享代码辐射的其它平台 | Phase 0.5 第 4 点：平台包外共享方法 → 走过它的其它平台接口 | 其它平台针对性回归接口 |

**D2 是最易漏的一维**：只测被改接口本身（D1）会漏掉「谁依赖它、它依赖谁」。推导方法固定：
```powershell
# 被调用（上游）：谁调用了被改的方法/接口
git grep -n "<changedMethod>" _target -- "*.java"
# 调用（下游）：被改方法体内部的下游调用（读方法源码，找 xxxManager./xxxController./feign 调用）
git show "_target:<改动文件>" | Select-String "<changedMethod>" -Context 0,30
```

把三维结果汇总进 `diff.json`：D1→`affected_endpoints`，D2→新增 `intra_platform_impact`（callers[] / callees[] / module_chain[]），D3→`cross_platform_risk`。**设计矩阵（Phase 2）必须覆盖三维**，覆盖基准按维度分组统计，一眼看出哪一维欠测。

---

## Phase 1 — Diff 两个 Swagger

### 1.1 运行 diff 脚本

diff.json 存放在平台目录下，按版本命名：

```powershell
node ".claude/skills/swagger-version-diff/scripts/diff_swagger.js" `
  "$env:TEMP\swagger_baseline.json" `
  "$env:TEMP\swagger_target.json" `
  "single-api/<服务>/<平台>/diff-<commit短码>.json"
```

### 1.2 结合 git 分析，输出确认表

```
## 变更摘要（CP-47435 / 1f18987）
| 来源 | 类型 | 接口/行为 | 纳入测试 |
|------|------|----------|---------|
| git+swagger | MODIFIED | POST /definition/getRule（targetLevel 新增 Flight） | ✅ |
| git only | BEHAVIOR | KevelFlightEntity Bid 精度 2 位 | ✅ |
| swagger only | ENUM_ADDED | valueType 新增 CPAResult 等 6 个值 | ❌ 噪音，非本版本 |
```

---

## Phase 1.5 — 读 Controller 源码定契约（🔴 硬规则，不可跳过）

**🔴 源码是接口契约的权威，swagger 只作结构参考。**

swagger 的坑（本 skill 已踩过，换个服务照样踩）：
- **路径名 ≠ 实际 mapping**：swagger operationId 可能叫 `createRule`，实际 `@PostMapping` 是 `/definition`。照 swagger 路径发请求直接 404/405。
- **必填参数不全**：swagger 不体现"不传就 NPE"的隐性必填字段（如 `ruleIds`），靠猜会反复失败。
- **body 类型对不上**：swagger 的 requestBody 可能为空或与真实 DTO 不一致。

对**影响范围内每个待测接口**，进目标分支的源码确认三件事：

```powershell
# 1) 定位 Controller（只读树，不拉 blob，避免 partial-clone 逐个拉 blob 超时）
git ls-tree -r --name-only _target 2>&1 | Select-String "Controller"

# 2) 读该接口的 @PostMapping/@GetMapping + @RequestBody 类型
git show "_target:<Controller 路径>" | Select-String "@PostMapping|@GetMapping|@RequestBody|public "

# 3) 从 swagger components.schemas dump 该 body DTO 的字段（结构参考用）
```

产出**接口契约表**（喂给 Phase 2 设计 + Phase 4 写 case，杜绝猜）：

| 意图 | swagger 路径 | **实际 mapping** | body DTO | 隐性必填 |
|------|-------------|-----------------|----------|---------|
| 创建规则 | /definition/createRule | **POST /definition** | RuleRequest | applyTarget.targetInfo |
| 规则列表 | /getRuleViewList | POST /getRuleViewList | RuleParam | **ruleIds(不传NPE)** |

🔴 **契约表没确认完，不许进 Phase 2 设计**。路径/参数一律以源码为准，swagger 只用来看字段结构。

**数据来源同理**：接口要真实实体 ID 时，先找该服务的 provider/实体查询接口（读源码或 provider swagger），从 provider 自举真实 ID，不猜、不硬造。

---

## Phase 2 — 接口 case 设计（🔴 先设计，后写码）

**🔴 拿到影响范围后不要直接写 case，先出一份对齐 swagger 的设计矩阵**，落成 `single-api/<服务>/<平台>/case-design-<commit>.json`。这是后续执行与覆盖统计的**基准**。

设计矩阵结构（`endpoints[]`，每接口一条）：
```json
{
  "method": "POST", "path": "/definition/createRule", "module": "definition",
  "change_type": "NEW|MODIFIED|REMOVED", "req_ref": "FR-x（需求出处）",
  "cases": [
    { "id": "CR-A1", "scenario": "<测试意图>", "assert": "<断言口径>",
      "status": "PASS|FAIL|BLOCKED|TODO", "blocker": "<被什么卡住>" }
  ]
}
```

规则：
- **影响范围内每个接口都要有条目**，一个不漏（对齐 swagger）。
- case 设计**独立自 requirements.md 的 FR-x**（字段×运算符×动作×边界的组合），不抄开发自测清单。
- 每个 case 先标 `TODO`，随执行推进改 `PASS/FAIL/BLOCKED`，`blocker` 写清被什么卡住（如"无真实 flightId"）。
- **设计 case 数 = 测试意图数**，与能否立刻执行无关——被卡住的也要设计出来并标 `BLOCKED`，这样覆盖基准才能暴露"欠了多少测"。

## Phase 2.5 — 定位现有 cases.json

**🔴 先查再生成，不重复造轮子。**

```
single-api/<服务>/<平台>/us/<模块>/task-<最新时间戳>/cases.json
```

- **找到**：后续 delta case 追加到此文件（在当前 git 分支上修改）
- **找不到**（新平台/新模块）：按设计矩阵逐条实现，能跑的先跑。

---

## Phase 3 — 获取 case 源数据（按平台是否有流量分两条路）

### 3.A 既有平台（有 ES 流量）—— ES 抽样

与 `swagger-api-case` Phase 2 完全一致，使用相同脚本：

```powershell
pwsh ".claude/skills/swagger-api-case/scripts/query_es.ps1" `
  -Index     <es_index.us> `
  -Path      <endpoint_path> `
  -Method    <GET|POST> `
  -PathField <es.path_field> `
  [-Platform <平台>]
```

**MODIFIED 接口重点**：优先挖掘涉及变更字段的调用场景（新枚举值有无、新字段有无）。
**行为变更**：ES 抽样找典型入参，构造能触发变更逻辑的场景（如小百分比 budget 调整）。

### 3.B 新平台（无 ES 流量）—— 从需求规格独立推导

新平台线上零流量，ES 抽不出样本。case 源数据改为：

> **Swagger（接口结构）+ requirements.md（字段/动作/验收口径）+ 测试环境真实实体 ID**

🔴 **测试独立性铁律（保持与开发交叉验证的价值）**：

| commit 自带文档 | 性质 | 测试可否引用 |
|----------------|------|-------------|
| `requirements.md` | 需求规格（双方共识的验收契约） | ✅ 可参考——这是验收标准 |
| `integration-test-instructions.md` | **开发的自测清单** | ❌ **禁止参考**——抄它=继承开发盲区，失去独立性 |
| `*-code-summary.md` / `business-logic-model.md` / 其它实现设计文档 | 开发的实现/设计产物 | ❌ 禁止参考 |

- 测试场景由测试**从 requirements.md 的功能需求（FR-x）独立设计**：字段清单 × 运算符 × 动作的组合、边界值、空值/零值等，自己枚举，不抄开发的测试大纲。
- 断言依据取 requirements.md 里的"预期/口径"（如"未设置 Daily Budget 的 Flight 判不命中"）。
- 真实实体 ID（profileId / campaignId / flightId 等）从测试环境取，无则填 `[NEEDS_REAL_VALUE]` 并列入待补清单。
- 拉取 requirements.md：`git show _target:"aidlc-docs/inception/requirements/requirements.md"`（仅此一份，不拉测试/实现文档）。

---

## Phase 4 — 生成 delta case 并追加

### 4.1 NEW 接口

```json
{
  "name": "POST /definition/xxx - <场景>",
  "description": "版本变更(1f18987)：新增接口。<场景说明>。500条样本占比xx%。",
  "change_type": "NEW",
  "since": "1f18987",
  "last_modified": "1f18987",
  "generated_by": "swagger-version-diff"
}
```

### 4.2 MODIFIED 接口

每个变更点必须生成两类 case：

```json
[
  {
    "name": "POST /definition/getRule - targetLevel=Flight（新枚举值）",
    "description": "版本变更(1f18987)：targetLevel 新增 Flight。变更点: targetLevel enum added。500条样本占比xx%。",
    "change_type": "MODIFIED",
    "since": "1f18987"
  },
  {
    "name": "POST /definition/getRule - 兼容性验证（不传 Flight）",
    "description": "版本变更(1f18987)：验证旧版入参（不含 Flight）在新版本仍正常。兼容性回归。",
    "change_type": "MODIFIED",
    "since": "1f18987"
  }
]
```

### 4.3 行为变更（git only）

针对 `behavior_changes` 里每条变更构造验证场景：

```json
{
  "name": "Kevel Flight Bid 精度验证 - 小百分比调整",
  "description": "版本变更(1f18987)：Bid 取整 FLOOR→HALF_UP，验证 5% 增幅不被抹平、下发值保留 2 位小数。",
  "change_type": "MODIFIED",
  "since": "1f18987"
}
```

### 4.4 REMOVED 接口

```json
{
  "name": "GET /xxx - 验证接口已下线",
  "change_type": "REMOVED",
  "since": "1f18987",
  "steps": [{ "expected_response": { "status_code": 404 } }]
}
```

### 4.5 追加到 cases.json

delta case 直接追加到 Phase 2 定位的 cases.json 末尾（JSON 数组 push），在当前 git 分支上保存。

---

## Phase 5 — 执行

### 5.1 去除 BOM

```bash
python ".claude/skills/swagger-api-case/scripts/fix_bom.py" \
  single-api/<服务>/<平台>/us/<模块>/task-<timestamp>/cases.json \
  single-api/<服务>/<平台>/us/config.test.json
```

### 5.2 执行（用 config.test.json）

```bash
python "C:/AI engineering/rule-modules-web-master/rule-modules-web-master/.claude/skills/api-case-generate/api-case-run/scripts/run-cases.py" \
  --cases  single-api/<服务>/<平台>/us/<模块>/task-<timestamp>/cases.json \
  --config single-api/<服务>/<平台>/us/config.test.json \
  --out    single-api/<服务>/<平台>/us/<模块>/task-<timestamp>/report-<commit短码>.json
```

🔴 **config 用 `config.test.json`，cases 和 report 均在 `us` 目录下**：cases.json 是环境无关的（所有 URL 都是 `{{RULEBASEURL}}`），切 config 文件即切环境，目录结构本身不体现环境（同目录 `config.json`=线上、`config.test.json`=测试）。

### 5.3 分析结果

```bash
python ".claude/skills/swagger-api-case/scripts/summarize_report.py" \
  single-api/<服务>/<平台>/us/<模块>/task-<timestamp>/report-<commit短码>.json
```

按 `change_type` 和 `since` 分组输出：

```
## 执行结果（版本 1f18987）
| 类型 | PASS | FAIL |
|------|------|------|
| 回归（since != 1f18987） | 12 | 0 |
| 新增验证（since = 1f18987） | 4 | 1 |

FAIL：MODIFIED POST /definition/getRule 兼容性 case → Breaking Change！
```

🔴 **MODIFIED 接口兼容性 case FAIL = Breaking Change**，明确标记并提示用户。

### 5.4 回写设计矩阵状态

每次执行后，把 report 结果回写 `case-design-<commit>.json` 里对应 case 的 `status`（PASS/FAIL）与 `blocker`，保持设计矩阵与实际执行同步。

---

## Phase 6 — 覆盖基准（🔴 对齐 swagger 的直观视图，每次执行后必做）

以设计矩阵为准、合并 report 实际结果，渲染成一行一接口的 Excel 覆盖表：

```bash
python ".claude/skills/swagger-version-diff/scripts/coverage_baseline.py" \
  --design single-api/<服务>/<平台>/case-design-<commit>.json \
  --report single-api/<服务>/<平台>/us/<模块>/task-<timestamp>/report-<commit短码>.json \
  [--report ...可多次，合并多模块结果] \
  --out    single-api/<服务>/<平台>/coverage-<commit>.xlsx
```

产出一行一接口，列：`Method | Path | 模块 | 变更类型 | 设计case数 | 已执行 | 通过 | 失败 | 阻塞 | 覆盖率 | 状态 | 卡点/失败原因`。状态色：全通过=绿、有失败=红、全阻塞=灰、部分=黄。

- **设计 case 数 vs 已执行 vs 阻塞** 三者并列，一眼看出"欠了多少测、卡在哪"。
- 卡点原因逐接口列出，是推进测试的 TODO 清单。

---

## 交付物

| 文件 | 说明 |
|------|------|
| `single-api/<服务>/<平台>/diff-<commit>.json` | 版本 diff 记录（git + swagger 双来源） |
| `single-api/<服务>/<平台>/case-design-<commit>.json` | 🔴 接口 case 设计矩阵（对齐 swagger，覆盖统计基准） |
| `single-api/<服务>/<平台>/us/<模块>/task-xxx/cases.json` | 追加了 delta case（git 分支上） |
| `single-api/<服务>/<平台>/us/<模块>/task-xxx/report-<commit>.json` | 执行报告（report 按 commit 命名，同一 task 可多次执行） |
| `single-api/<服务>/<平台>/coverage-<commit>.xlsx` | 🔴 覆盖基准（一行一接口：设计/执行/通过/失败/阻塞/卡点） |

目录结构与环境无关，`us` 表示数据来源（ES 抽样自 US 环境），执行环境由 config.json 决定：
- 打线上：`--config single-api/<服务>/<平台>/us/config.json`
- 打测试：`--config single-api/<服务>/<平台>/us/config.test.json`

merge 到 main 后：cases.json 携带完整历史（含本版本 delta），下个版本继续追加。
