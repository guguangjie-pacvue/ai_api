<#
query_es.ps1 — Phase 2.2 ES 日志查询（参数化，内建 GET/POST 平台过滤）

用法：
  pwsh scripts/query_es.ps1 `
    -Index      rule-api-access-* `
    -Path       /config/RuleActionMetrics `
    -Method     POST `
    -PathField  urlReferrer.keyword `
    [-Platform  tiktok] `        # 多平台服务传当前平台；标准服务省略
    [-ClientIdExclude 62,3186] ` # 默认 62,3186
    [-Size 500] [-Days 90] [-CountOnly]

平台过滤规则（🔴 与 SKILL.md 2.1 分治表一致，内建于此避免手写出错）：
  - Method=POST 且传了 -Platform → 加 queryString: productLine=<platform> 过滤（只取该平台流量）
  - Method=GET 或未传 -Platform → 不加平台过滤（GET 的 queryString 为空，加了会误判零流量）

输出：
  - 默认打印命中总数 + 每条的 _source.body（body 为字符串则原样打印，供调用方按 es.body_is_json_string 决定是否二次解析）
  - -CountOnly 只打印命中总数
#>
param(
  [Parameter(Mandatory=$true)][string]$Index,
  [Parameter(Mandatory=$true)][string]$Path,
  [Parameter(Mandatory=$true)][string]$Method,
  [Parameter(Mandatory=$true)][string]$PathField,
  [string]$Platform,
  [int[]]$ClientIdExclude = @(62,3186),
  [int]$Size = 500,
  [int]$Days = 90,
  [switch]$CountOnly
)

$b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("watcher:kY9GErML%luQTorm"))
$headers = @{ "Authorization" = "Basic $b64"; "kbn-xsrf" = "true"; "Content-Type" = "application/json" }

# must 子句：路径 + 方法（+ 多平台服务 POST 的平台过滤）
$must = @(
  @{ term = @{ $PathField = $Path } },
  @{ term = @{ "method.keyword" = $Method } }
)
$methodUpper = $Method.ToUpper()
if ($Platform -and $methodUpper -eq "POST") {
  $must += @{ match_phrase = @{ "queryString" = "productLine=$Platform" } }
  Write-Host "[query_es] POST + platform=$Platform → 加 queryString 过滤" -ForegroundColor Cyan
} elseif ($Platform) {
  Write-Host "[query_es] $methodUpper 不加平台过滤（queryString 为空，仅 POST 可按平台过滤）→ 用全平台流量" -ForegroundColor Yellow
}

$size = if ($CountOnly) { 0 } else { $Size }
$query = @{
  params = @{
    index = $Index
    body  = @{
      query = @{ bool = @{ must = @(
        @{ function_score = @{
          query = @{ bool = @{
            must     = $must
            must_not = @( @{ terms = @{ clientId = $ClientIdExclude } } )
            filter   = @( @{ range = @{ "@timestamp" = @{ gte = "now-${Days}d" } } } )
          }}
          functions  = @( @{ random_score = @{} } )
          boost_mode = "replace"
        }}
      )}}
      size    = $size
      _source = @("body","@timestamp")
      sort    = @("_score")
    }
  }
} | ConvertTo-Json -Depth 20

$result = Invoke-RestMethod -Uri "https://logs.pacvue.com/internal/search/es" -Method POST -Headers $headers -Body $query -TimeoutSec 30
$total = $result.rawResponse.hits.total
Write-Host "[query_es] $methodUpper $Path : $total hits" -ForegroundColor Green
if (-not $CountOnly) {
  $result.rawResponse.hits.hits | ForEach-Object { $_._source.body }
}
