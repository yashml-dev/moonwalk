param(
    [string]$OutputZip = "MOONWALK.zip"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$zipPath = Join-Path $root $OutputZip
$temp = Join-Path $env:TEMP ("MoonwalkPackage_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $temp | Out-Null
try {
    $excludeDirs = @(".venv", ".git", "__pycache__", ".pytest_cache", "temp", "tmp")
    Get-ChildItem -LiteralPath $root -Force | Where-Object {
        $_.Name -ne (Split-Path $zipPath -Leaf) -and $excludeDirs -notcontains $_.Name
    } | ForEach-Object {
        if ($_.PSIsContainer -and $excludeDirs -contains $_.Name) { return }
        Copy-Item -LiteralPath $_.FullName -Destination $temp -Recurse -Force
    }
    if (-not (Test-Path (Join-Path $temp "best.pt"))) { throw "best.pt is missing; refusing to create an incomplete package." }
    if (Test-Path $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
    Compress-Archive -Path (Join-Path $temp "*") -DestinationPath $zipPath -CompressionLevel Optimal
    Write-Host "Created: $zipPath"
} finally {
    if (Test-Path $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}
