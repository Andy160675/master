[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ServerIp,
    [string]$Name = "example.com",
    [string]$Type = "A",
    [string]$OutDir = "${PSScriptRoot}\\..\\..\\validation\\sovereign_dns",
    [switch]$Gate
)

$ErrorActionPreference = 'Stop'

function New-StampUtc { (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') }

$stamp = New-StampUtc
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$report = [ordered]@{
    generated_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    server_ip = $ServerIp
    query = @{ name = $Name; type = $Type }
    ok = $false
    answer = $null
    error = $null
}

try {
    $res = Resolve-DnsName -Server $ServerIp -Name $Name -Type $Type -ErrorAction Stop
    $report.ok = $true
    $report.answer = @($res | Select-Object Name, Type, TTL, Section, IPAddress, NameHost, QueryType)
} catch {
    $report.ok = $false
    $report.error = $_.Exception.Message
    if ($Gate) { throw }
}

$outPath = Join-Path $OutDir ("dns_client_test_{0}.json" -f $stamp)
$report | ConvertTo-Json -Depth 6 | Out-File -FilePath $outPath -Encoding utf8

$receiptScript = Join-Path $PSScriptRoot 'Write-Sha256-Receipt.ps1'
if (Test-Path -LiteralPath $receiptScript) {
    & $receiptScript -InputFile $outPath -OutputFile "$outPath.sha256" -DisplayPath (Split-Path -Leaf $outPath) | Out-Null
}

Write-Host "DNS client test -> $outPath" -ForegroundColor Green
if (-not $report.ok -and $Gate) { exit 1 }
exit 0
