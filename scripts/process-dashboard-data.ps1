param(
  [string]$InputCsv = (Join-Path $PSScriptRoot '..\data\processed\company-year-analysis.csv'),
  [string]$OutputDirectory = (Join-Path $PSScriptRoot '..\data\graph-data')
)

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$rows = Import-Csv $InputCsv | ForEach-Object {
  [pscustomobject]@{
    Year=[int]$_.Year; Ticker=$_.Ticker; Name=$_.Name; Sector=$_.Sector; Subsector=$_.Subsector
    IsASX50=([bool]::Parse($_.IsASX50)); Rate=[double]$_.SixTermIncidencePer100k
    Words=[double]$_.ExtractedWords
  }
}

function Aggregate($items, $groupProperty) {
  $items | Group-Object $groupProperty | ForEach-Object {
    $g=$_.Group; $words=($g|Measure-Object Words -Sum).Sum
    $sixTerms=($g | ForEach-Object { $_.Rate * $_.Words / 100000 } | Measure-Object -Sum).Sum
    [pscustomobject]@{Year=$g[0].Year; Group=$_.Name; Companies=(($g.Ticker|Sort-Object -Unique).Count); Words=$words; SixTermOccurrences=$sixTerms; SixTermIncidencePer100k=if($words){100000*$sixTerms/$words}else{0}}
  }
}

$annual = $rows | Group-Object Year | ForEach-Object {
  $g=$_.Group; $words=($g|Measure-Object Words -Sum).Sum
  $sixTerms=($g | ForEach-Object { $_.Rate * $_.Words / 100000 } | Measure-Object -Sum).Sum
  [pscustomobject]@{Year=[int]$_.Name; Companies=(($g.Ticker|Sort-Object -Unique).Count); Reports=$g.Count; Words=$words; SixTermOccurrences=$sixTerms; SixTermIncidencePer100k=if($words){100000*$sixTerms/$words}else{0}}
} | Sort-Object Year
$annual | Export-Csv (Join-Path $OutputDirectory 'annual-incidence.csv') -NoTypeInformation -Encoding UTF8

$rows | Group-Object Year | ForEach-Object { Aggregate $_.Group Sector } | Sort-Object Year,Group | Export-Csv (Join-Path $OutputDirectory 'sector-incidence.csv') -NoTypeInformation -Encoding UTF8

$company = $rows | Group-Object Ticker | ForEach-Object {
  $g=$_.Group; $words=($g|Measure-Object Words -Sum).Sum
  $sixTerms=($g | ForEach-Object { $_.Rate * $_.Words / 100000 } | Measure-Object -Sum).Sum
  [pscustomobject]@{Ticker=$g[0].Ticker;Name=$g[0].Name;Sector=$g[0].Sector;Subsector=$g[0].Subsector;IsASX50=$g[0].IsASX50;Reports=$g.Count;Words=$words;SixTermOccurrences=$sixTerms;SixTermIncidencePer100k=if($words){100000*$sixTerms/$words}else{0}}
} | Sort-Object SixTermIncidencePer100k -Descending
$company | Export-Csv (Join-Path $OutputDirectory 'company-comparison.csv') -NoTypeInformation -Encoding UTF8

Write-Output "Created graph-ready outputs in $OutputDirectory"
