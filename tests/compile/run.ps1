# Compile gate (local, Windows) — every specs\*.symboleo must report errors:0.
#
# Jar mode only: set $env:CODEGEN_JAR to the codegen-cli fat jar (see ..\..\CLAUDE.md).
# CI uses the portable run.sh in remote mode instead.
#
#   $env:CODEGEN_JAR = "C:\...\symboleoac-codegen-cli-1.0.0-all.jar"
#   .\tests\compile\run.ps1                 # defaults to the specs\ dir
#
# Exit: 0 = all clean; 1 = a spec has errors; 2 = misconfigured.
param([string]$SpecsDir = "specs")
$ErrorActionPreference = "Stop"

if (-not $env:CODEGEN_JAR) {
  Write-Host "Set `$env:CODEGEN_JAR to the codegen-cli fat jar (see CLAUDE.md)." -ForegroundColor Red
  exit 2
}
$specs = Get-ChildItem -Path $SpecsDir -Filter *.symboleo -ErrorAction SilentlyContinue
if (-not $specs) { Write-Host "no specs found in '$SpecsDir'" -ForegroundColor Red; exit 1 }
Write-Host ("compile gate - {0} spec(s), jar: {1}" -f $specs.Count, $env:CODEGEN_JAR)

$fail = 0
foreach ($f in $specs) {
  $out = Get-Content $f.FullName -Raw | java -jar $env:CODEGEN_JAR
  $j = $out | ConvertFrom-Json
  $e = $j.summary.errors
  if ($e -eq 0) {
    "OK    {0,-30} errors:0 warnings:{1}" -f $f.Name, $j.summary.warnings
  } else {
    "FAIL  {0,-30} errors:{1}" -f $f.Name, $e
    foreach ($i in $j.issues) { "  $($i.severity) L$($i.line):$($i.column) $($i.message)" }
    $fail = 1
  }
}
if ($fail -eq 0) { Write-Host "all specs compile clean." -ForegroundColor Green }
else { Write-Host "compile gate FAILED." -ForegroundColor Red }
exit $fail
