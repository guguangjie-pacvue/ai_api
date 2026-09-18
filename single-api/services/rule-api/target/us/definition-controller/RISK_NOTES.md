# definition-controller (target) — 风险标记接口

## POST /automationPauseAsins

- **状态**：未生成 case，未执行。
- **ES 流量**：target 平台全平台 90 天/180 天窗口均为 0 次真实调用（已排除 clientId 62/3186 测试账号），单凭该条件已满足"ES 无流量"跳过规则。
- **额外风险**（即使未来出现真实流量，仍建议人工评估后再考虑覆盖）：
  - Swagger 声明请求体为 `RuleChangeRequest`（`ruleId`/`ruleIds`/`isPaused`/`isDelete`/`clientId`/`userId`/`userName`），与 `changeStatus`/`changeOwners` 共用同一个泛型 DTO。
  - 接口名称语义为"批量自动暂停 ASIN"，从字段结构无法判断其实际作用范围是否严格限定为调用方自身 client 的数据，也无法排除是否存在跨 client/批量副作用的可能。
  - 由于零真实调用样本，无法通过真实请求观察其实际影响半径来验证安全边界。
  - 综合以上，即使后续 ES 出现该接口的 target 平台流量，也建议先人工确认其作用范围（是否强制校验 clientId 归属、是否支持真正的批量跨规则操作）后再决定是否纳入自动化用例，而不要直接照搬样本执行。

本次未对该接口做任何写操作。
