#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Root = Resolve-Path (Join-Path $Here "..")
$Cli  = Join-Path $Root "cli/teof_cli.py"
$Eval = Join-Path $Root "trunk/ogs/evaluator.py"
$Out  = $env:TEOF_OUT_DIR; if ([string]::IsNullOrEmpty($Out)) { $Out = Join-Path $Root "artifacts/ocers_out" }
if (-not (Test-Path $Cli))  { Write-Error "CLI not found at $Cli" }
if (-not (Test-Path $Eval)) { Write-Error "Evaluator not found at $Eval" }
$py = (Get-Command python3 -ErrorAction SilentlyContinue) ?? (Get-Command python -ErrorAction SilentlyContinue)
if (-not $py) { Write-Error "python3/python not found on PATH" }
$venvPath = Join-Path $Root ".venv"
if (-not (Test-Path $venvPath)) { & $py.Source -m venv $venvPath }
. (Join-Path $venvPath "Scripts/Activate.ps1")
& python -m pip install -U pip | Out-Null
New-Item -ItemType Directory -Force -Path $Out | Out-Null
& python $Cli
& python (Join-Path $Here "append_anchor.py")
