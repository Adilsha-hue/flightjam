$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
Write-Host 'FlightJam project demo: http://127.0.0.1:8765/sim/index.html'
Write-Host 'Open the URL and choose a section in the project navigation. Ctrl+C stops the server.'
python -m http.server 8765 --bind 127.0.0.1
