# history-controller — 风险接口说明（未生成 case、未执行）

按任务要求，以下 2 个接口判定为运维/管理类高风险操作，blast radius 不限定于单个客户/单个实体，
即使 ES 显示有真实流量也**不生成 cases.json、不执行**，仅在此记录接口契约与判断依据。

## POST /history/archiveOldLogsTask

- **Swagger**：无 requestBody（空 POST），响应 `{code, msg, data:integer}`（`data` 为归档条数）。
- **风险判断**：接口名和参数结构（无任何范围限定参数，如 clientId/profileId/dateRange 等）表明这是一个
  批量归档全平台旧执行日志的运维/定时任务接口，一旦调用会影响全平台历史数据，不限于当前 QA 测试账号
  (client_id=62)。
- **ES 流量**：近90天、近180天（全平台，排除 clientId 62/3186）均为 **0 次调用**，也没有证据表明该接口
  是被前端正常触发的，更像是仅由内部定时任务/管理后台调用。
- **结论**：不生成 case，不执行。

## GET /history/deleteHistoryData/{tableName}

- **Swagger**：path 参数 `tableName: string`（必填），无 requestBody，响应 `{code, msg, data}`。
- **风险判断**：接口按**原始表名**物理删除历史数据，`tableName` 作为自由字符串直接传给后端，没有任何
  客户/时间范围限定参数，一旦误传或权限校验缺失，可能清空整张表，属于无界爆炸半径的破坏性管理操作。
- **ES 流量**：近90天全平台（排除 clientId 62/3186）实际有 **6480 次调用**，抽样 `tableName` 值全部为
  `rule_snapshot_detail`（说明生产环境确实在被脚本化/定时调用，但这恰恰说明这是一个后台维护任务而非
  用户交互触发的功能，更应避免测试环境重复触发）。
- **结论**：不生成 case，不执行，即使真实调用频率很高也不例外（任务明确要求这两个接口无论 ES 流量如何
  都不执行）。
