param([switch]$Docker)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$validationArgs = @('scripts/validate.py')
if ($Docker) { $validationArgs += '--docker' }
& examples/notes/.venv/Scripts/python.exe @validationArgs
if ($LASTEXITCODE -ne 0) { throw 'Postflight failed' }
