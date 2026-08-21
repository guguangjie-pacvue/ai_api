<#
cleanup_rules.ps1 - delete test rules by ruleName prefix (write-case self cleanup)

Safe: only deletes rules whose ruleName starts with the given prefix.
Never deletes by index/range, so it can't touch other people's rules.
Use as pre/post cleanup for createRule cases to stay idempotent.

Usage:
  pwsh cleanup_rules.ps1 -Config <config.test.json> -Prefix "vdiff-1f18987-" [-ProfileId 6274332]
#>
param(
  [Parameter(Mandatory=$true)][string]$Config,
  [Parameter(Mandatory=$true)][string]$Prefix,
  [string]$ProfileId
)

$cfg = Get-Content $Config -Raw | ConvertFrom-Json
$base = $cfg.base_urls.RULEBASEURL
$pl   = $cfg.variables.platform
if (-not $ProfileId) { $ProfileId = $cfg.variables.profile_id }

$loginBody = @{ userName = $cfg.auth.body.userName; password = $cfg.auth.body.password } | ConvertTo-Json
$lhdr = @{ "Content-Type"="application/json"; "productline"=$pl }
$lr = Invoke-RestMethod -Uri $cfg.auth.login_url -Method POST -Body $loginBody -Headers $lhdr
$token = "Bearer " + $lr.data.accessToken
$authHdr = @{ "Content-Type"="application/json"; "productline"=$pl; "Authorization"=$token }

$q = @{ productLine=$pl; profileId=$ProfileId; pageInfo=@{pageNo=1;pageSize=200} } | ConvertTo-Json
$rules = Invoke-RestMethod -Uri ($base+"definition/getRule") -Method POST -Body $q -Headers $authHdr
$targets = $rules.data.list | Where-Object { $_.ruleName -like "$Prefix*" }

if (-not $targets) { Write-Host "[cleanup] no rules matching '$Prefix*', skip"; exit 0 }

$ids = @($targets | ForEach-Object { [long]$_.id })
$names = ($targets | ForEach-Object { $_.ruleName }) -join ', '
Write-Host ("[cleanup] deleting {0} rule(s): {1}" -f $ids.Count, $names)

$del = @{ ruleIds = $ids; isDelete = $true } | ConvertTo-Json
$r = Invoke-RestMethod -Uri ($base+"definition/changeStatus") -Method POST -Body $del -Headers $authHdr
Write-Host ("[cleanup] changeStatus(delete) -> code:{0}" -f $r.code)

$chk = Invoke-RestMethod -Uri ($base+"definition/getRule") -Method POST -Body $q -Headers $authHdr
$left = $chk.data.list | Where-Object { $_.ruleName -like "$Prefix*" }
if ($left) { Write-Host ("[cleanup] WARNING: {0} left" -f $left.Count); exit 1 } else { Write-Host "[cleanup] OK, all cleared" }
