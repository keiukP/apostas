param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("continuo", "servidor")]
    [string]$Modo
)

$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
if (-not $env:ODDS_API_KEY) {
    $env:ODDS_API_KEY = [Environment]::GetEnvironmentVariable("ODDS_API_KEY", "User")
}
$py = "C:\Users\3200\AppData\Local\Programs\Python\Python313\python.exe"
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot "data") | Out-Null
$log = Join-Path $PSScriptRoot "data\autopilot_$Modo.log"

while ($true) {
    if ($Modo -eq "continuo") {
        if (-not $env:ODDS_API_KEY) {
            Add-Content -Path $log -Value "[$(Get-Date -Format s)] ODDS_API_KEY em falta; nova verificação em 5 min"
            Start-Sleep -Seconds 300
            continue
        }
        $argumentos = @("-u", "main.py", "--continuo", "--preparar-amanha", "--intervalo", "1440")
    }
    else {
        $argumentos = @("-u", "servidor.py")
    }

    Add-Content -Path $log -Value "[$(Get-Date -Format s)] inicio $Modo"
    & $py @argumentos 2>&1 | ForEach-Object { Add-Content -Path $log -Value $_ }
    Add-Content -Path $log -Value "[$(Get-Date -Format s)] terminou; a reiniciar em 60 s"
    Start-Sleep -Seconds 60
}
