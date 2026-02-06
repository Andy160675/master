[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [Parameter(Mandatory=$true)][string]$UncPath,
    [ValidatePattern('^[A-Z]$')][string]$DriveLetter = 'S',
    [switch]$Persistent,
    [switch]$PromptCredential,
    [switch]$Unmount,
    [string]$OutDir = "${PSScriptRoot}\\..\\..\\validation\\evidence_mount",
    [switch]$EmitJson,
    [switch]$Gate
)

$ErrorActionPreference = 'Stop'

function New-StampUtc { (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') }

$stamp = New-StampUtc
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$driveName = "$DriveLetter:"

$credential = $null
if ($PromptCredential) {
    $credential = Get-Credential -Message "Credentials for $UncPath"
}

$ok = $false
$errorText = $null

try {
    if ($Unmount) {
        if ($PSCmdlet.ShouldProcess($driveName, "Remove mapped drive")) {
            # Remove PSDrive mapping if present
            try { Remove-PSDrive -Name $DriveLetter -Force -ErrorAction SilentlyContinue } catch {}
            # Best-effort: remove any net use mapping
            try { cmd.exe /c "net use $driveName /delete /y" | Out-Null } catch {}
        }
        $ok = $true
    } else {
        if ($PSCmdlet.ShouldProcess("$driveName -> $UncPath", "Map evidence share")) {
            # Clear any prior mapping
            try { Remove-PSDrive -Name $DriveLetter -Force -ErrorAction SilentlyContinue } catch {}

            $psDriveParams = @{
                Name       = $DriveLetter
                PSProvider  = 'FileSystem'
                Root       = $UncPath
                Persist    = [bool]$Persistent
                Scope      = 'Global'
                ErrorAction = 'Stop'
            }
            if ($credential) { $psDriveParams.Credential = $credential }

            New-PSDrive @psDriveParams | Out-Null

            # Verify path is reachable
            $ok = Test-Path -LiteralPath "$driveName\\"
            if (-not $ok) { throw "Mapped drive created but path is not reachable: $driveName\\" }
        }
    }
} catch {
    $ok = $false
    $errorText = $_.Exception.Message
}

$record = [ordered]@{
    generated_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    action = if ($Unmount) { 'unmount' } else { 'mount' }
    unc_path = $UncPath
    drive = $driveName
    persistent = [bool]$Persistent
    prompted_credential = [bool]$PromptCredential
    ok = $ok
    error = $errorText
    host = $env:COMPUTERNAME
    user = $env:USERNAME
}

$outJson = Join-Path $OutDir ("evidence_mount_{0}_{1}.json" -f $DriveLetter, $stamp)
$record | ConvertTo-Json -Depth 6 | Out-File -FilePath $outJson -Encoding utf8

# Hash receipt
$receipt = "$outJson.sha256"
$receiptScript = Join-Path $PSScriptRoot 'Write-Sha256-Receipt.ps1'
if (Test-Path -LiteralPath $receiptScript) {
    & $receiptScript -InputFile $outJson -OutputFile $receipt -DisplayPath (Split-Path -Leaf $outJson) | Out-Null
}

if ($EmitJson) {
    $record | ConvertTo-Json -Depth 6
} else {
    Write-Host "Evidence -> $outJson" -ForegroundColor Green
    if ($ok) {
        Write-Host "OK: $driveName -> $UncPath" -ForegroundColor Green
    } else {
        Write-Host "FAIL: $driveName -> $UncPath :: $errorText" -ForegroundColor Red
    }
}

if ($Gate -and -not $ok) { exit 1 }
