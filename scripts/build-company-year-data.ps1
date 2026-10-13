param(
  [string]$ShardDirectory = (Join-Path $PSScriptRoot '..\data\intermediate'),
  [string]$MetadataCsv = (Join-Path $PSScriptRoot '..\data\processed\company-year-analysis.csv'),
  [string]$OutputCsv = (Join-Path $PSScriptRoot '..\data\processed\company-year-analysis.csv')
)

$ErrorActionPreference = 'Stop'
$termKeys = @('regulation', 'compliance', 'burden', 'requirement', 'regulator', 'legislation')

$metadata = @{}
foreach ($row in (Import-Csv -LiteralPath $MetadataCsv)) {
  if (!$metadata.ContainsKey($row.Ticker)) {
    $metadata[$row.Ticker] = [pscustomobject]@{
      Name = $row.Name
      Sector = $row.Sector
      Subsector = $row.Subsector
      IsASX50 = $row.IsASX50
    }
  }
}

$records = New-Object System.Collections.ArrayList
foreach ($file in (Get-ChildItem -LiteralPath $ShardDirectory -Filter 'balanced-regulatory-shard-*.json' | Sort-Object Name)) {
  $shardRows = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
  foreach ($row in $shardRows) {
    $meta = $metadata[[string]$row.Ticker]
    if ($null -eq $meta) { throw "Missing metadata for ticker $($row.Ticker)" }
    $occurrences = 0
    foreach ($term in $termKeys) { $occurrences += [int64]$row.Terms.PSObject.Properties[$term].Value }
    $incidence = if ([int64]$row.Words -gt 0) { 100000 * $occurrences / [int64]$row.Words } else { 0 }
    [void]$records.Add([pscustomobject]@{
      Year = [int]$row.Year
      Ticker = [string]$row.Ticker
      Name = [string]$meta.Name
      Sector = [string]$meta.Sector
      Subsector = [string]$meta.Subsector
      IsASX50 = [string]$meta.IsASX50
      SixTermIncidencePer100k = $incidence
      ExtractedWords = [int64]$row.Words
      CodedPassages = [int64]$row.Coded
    })
  }
}

if ($records.Count -ne 1045) { throw "Expected 1,045 company-year records; found $($records.Count)" }
$records | Sort-Object Ticker, Year | Export-Csv -LiteralPath $OutputCsv -NoTypeInformation -Encoding UTF8
Write-Output "written=$OutputCsv rows=$($records.Count)"
