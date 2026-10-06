# install.ps1 — AI-Fab harness installer (Windows PowerShell 5.1+ / PowerShell 7)
#
# Thin wrapper: all logic lives in scripts/aifab-install.js (shared with install.sh).
# Usage:  .\install.ps1 [--target DIR] [--global] [--dry-run] [--help]
# If script execution is blocked:  powershell -ExecutionPolicy Bypass -File .\install.ps1 --global

$ErrorActionPreference = 'Stop'

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error 'missing dependency: node (https://nodejs.org)'
    exit 3
}

& node (Join-Path $PSScriptRoot 'scripts\aifab-install.js') @args
exit $LASTEXITCODE
