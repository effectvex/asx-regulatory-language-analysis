param(
  [string]$Archive=(Join-Path $PSScriptRoot '..\annual-reports'),
  [string]$Manifest=(Join-Path $PSScriptRoot '..\data\manifests\asx200-companies.json'),
  [string]$OutputDirectory=(Join-Path $PSScriptRoot '..\data\intermediate'),
  [string]$Pdftotext='pdftotext'
)

$ErrorActionPreference='Stop'

foreach($shard in 0..7){
  & (Join-Path $PSScriptRoot 'extract-regulatory-language.ps1') `
    -Shard $shard -Shards 8 -Manifest $Manifest -Archive $Archive `
    -OutputDir $OutputDirectory -Pdftotext $Pdftotext
}

& (Join-Path $PSScriptRoot 'process-dashboard-data.ps1')
& (Join-Path $PSScriptRoot 'generate-html-report.ps1') `
  -ArchiveName $Archive -ShardDirectory $OutputDirectory -PanelName ASX200

Write-Output 'Analysis pipeline complete.'
