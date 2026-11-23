$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
git status --short
if ($LASTEXITCODE -ne 0) { throw 'git status failed' }
uv --cache-dir .cache/uv python find
if ($LASTEXITCODE -ne 0) { throw 'Python is unavailable' }
node --version
if ($LASTEXITCODE -ne 0) { throw 'Node is unavailable' }
if (Test-Path tests/test_plugin.py) {
    uv --cache-dir .cache/uv run --no-project python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Baseline failed' }
} else { Write-Output 'Baseline: empty repository; no tests yet.' }
