param(
  [int]$Shard = 0,
  [int]$Shards = 8,
  [string]$Manifest = (Join-Path $PSScriptRoot '..\data\manifests\asx200-companies.json'),
  [string]$Archive = (Join-Path $PSScriptRoot '..\annual-reports'),
  [string]$OutputDir = (Join-Path $PSScriptRoot '..\data\intermediate'),
  [string]$Ticker = '',
  [string]$Pdftotext = 'pdftotext',
  [switch]$IncludeEvidence
)

# Poppler can emit non-fatal font and xref warnings for readable PDFs.
$ErrorActionPreference = 'Continue'

$archivePath = (Resolve-Path $Archive).Path
$outputPath = (Resolve-Path $OutputDir).Path
$pdftotextPath = (Get-Command $Pdftotext -ErrorAction Stop).Source
$years = 2015..2025

# These six lexical families are intentionally non-overlapping.
$termPatterns = [ordered]@{
  regulation  = '(?i)\bregulat(?:ion|ions|ory)\b'
  compliance  = '(?i)\bcomplian(?:ce|ces|t)\b'
  burden      = '(?i)\bburdens?\b'
  requirement = '(?i)\brequirements?\b'
  regulator   = '(?i)\bregulators?\b'
  legislation = '(?i)\blegislat(?:ion|ions|ive|ed)\b'
}

$themePatterns = [ordered]@{
  'Compliance and governance' = '(?i)\b(compliance|governance|ethic|conduct|control framework|internal control|code of conduct|anti[- ]bribery|whistleblow)\w*\b'
  'Regulatory change and uncertainty' = '(?i)\b(regulatory change|regulatory reform|new legislation|proposed legislation|evolving regulation|changing regulation|regulatory environment|policy change|law reform)\b'
  'Reporting, disclosure and assurance' = '(?i)\b(reporting|disclos\w*|audit\w*|assurance|statutory financial|financial statements|annual report|external auditor)\w*\b'
  'Direct cost and resourcing' = '(?i)\b(cost|costs|expense|expenses|fee|fees|resource|resourcing|staffing|burden|investment required|financial impact)\w*\b'
  'Systems, data and process implementation' = '(?i)\b(system\w*|data|process\w*|implement\w*|monitor\w*|technology|platform|workflow|record[- ]keeping)\b'
  'Licensing, approvals and market access' = '(?i)\b(licen[cs]\w*|permit\w*|approval\w*|authori[sz]\w*|accredit\w*|concession\w*|market access)\b'
  'Environmental and climate obligations' = '(?i)\b(environment\w*|climate|emission\w*|carbon|biodiversity|pollution|rehabilitation|sustainab\w*)\b'
  'Financial, tax and prudential rules' = '(?i)\b(tax\w*|prudential|capital adequacy|solvency|liquidity|financial crime|anti[- ]money laundering|aml|ctf|sanction\w*)\b'
  'Safety, quality and workforce obligations' = '(?i)\b(health and safety|workplace|workforce|employee|employment|labour|labor|quality|product safety|occupational|modern slavery)\w*\b'
  'Privacy, cyber and data protection' = '(?i)\b(privacy|cyber\w*|data protection|personal information|data breach|information security|cybersecurity)\w*\b'
}

$frameNames = @(
  'Cost or challenge',
  'Obligation or control',
  'Transition or anticipation',
  'Opportunity or legitimacy',
  'Descriptive or neutral'
)

$directCue = '(?i)\b(regulat\w*|complian\w*|legislat\w*|statut\w*|licen[cs]\w*|permit\w*|approval\w*|obligat\w*|mandat\w*|regulator\w*|prudential|privacy|cyber\w*)\b'
$supportProcessCue = '(?i)\b(report\w*|audit\w*|assur\w*|disclos\w*|control\w*|monitor\w*|polic\w*|system\w*|process\w*|standard\w*)\b'
$supportObligationCue = '(?i)\b(cost\w*|expense\w*|resource\w*|burden\w*|require\w*|obligat\w*|rule\w*|law\w*|act\b|compliance)\b'

function New-ZeroCounts($keys) {
  $counts = [ordered]@{}
  foreach ($key in $keys) { $counts[$key] = 0 }
  return $counts
}

function Get-PrimaryFrame([string]$Passage) {
  if ($Passage -match '(?i)\b(cost|costs|expense|expenses|fee|fees|burden|challenge|difficult|complex|resource pressure|delay)\w*\b') {
    return 'Cost or challenge'
  }
  if ($Passage -match '(?i)\b(proposed|future|upcoming|evolving|changing|transition|reform|new regulation|prepare|prepar\w*|expected)\w*\b') {
    return 'Transition or anticipation'
  }
  if ($Passage -match '(?i)\b(opportunit\w*|trust|trusted|legitimacy|leadership|value creation|competitive advantage)\b') {
    return 'Opportunity or legitimacy'
  }
  if ($Passage -match '(?i)\b(required|requirement|obligation|comply|compliance|control|monitor|policy|procedure|assurance|audit)\w*\b') {
    return 'Obligation or control'
  }
  return 'Descriptive or neutral'
}

function Get-ReportPassages([string]$Text) {
  $passages = New-Object System.Collections.ArrayList
  foreach ($block in [regex]::Split($Text, '\r?\n\s*\r?\n')) {
    $normalized = ($block -replace '\s+', ' ').Trim()
    if ($normalized.Length -lt 35) { continue }

    foreach ($sentence in [regex]::Split($normalized, '(?<=[\.!?;:])\s+')) {
      $remaining = $sentence.Trim()
      while ($remaining.Length -gt 800) {
        $cut = $remaining.LastIndexOf(' ', 800)
        if ($cut -lt 200) { $cut = 800 }
        [void]$passages.Add($remaining.Substring(0, $cut).Trim())
        $remaining = $remaining.Substring($cut).Trim()
      }
      if ($remaining.Length -ge 35) { [void]$passages.Add($remaining) }
    }
  }
  return $passages
}

function Get-CodingContext([string]$Passage) {
  if ($Passage.Length -le 500) { return $Passage }
  $cue = [regex]::Match($Passage, $directCue)
  if (!$cue.Success) { $cue = [regex]::Match($Passage, $supportObligationCue) }
  if (!$cue.Success) { return $Passage.Substring(0, 500) }
  $start = [Math]::Max(0, $cue.Index - 220)
  if (($start + 500) -gt $Passage.Length) { $start = $Passage.Length - 500 }
  return $Passage.Substring($start, 500).Trim()
}

function Read-ReportText([string]$PdfPath, [string]$TextPath) {
  & $pdftotextPath -layout -enc UTF-8 $PdfPath $TextPath 2>$null
  if (!(Test-Path -LiteralPath $TextPath)) { return '' }
  $text = Get-Content -LiteralPath $TextPath -Raw -Encoding UTF8
  if ($null -eq $text) { return '' }
  return $text
}

if (!(Test-Path -LiteralPath $Manifest)) { throw "Missing manifest: $Manifest" }
$parsedCompanies = Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json
$allCompanies = @(foreach ($company in $parsedCompanies) { $company }) | Sort-Object Ticker
$eligibleCompanies = @($allCompanies | Where-Object { !$Ticker -or [string]$_.Ticker -eq $Ticker })
$companies = for ($index = 0; $index -lt $eligibleCompanies.Count; $index++) {
  if (($index % $Shards) -eq $Shard) { $eligibleCompanies[$index] }
}

$temporaryDirectory = Join-Path $env:TEMP ("regulatory-shard-$Shard-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temporaryDirectory -Force | Out-Null
$records = New-Object System.Collections.ArrayList
$processed = 0

try {
  foreach ($company in $companies) {
    foreach ($year in $years) {
      $processed++
      $pdfPath = Join-Path $archivePath (Join-Path $company.DirName "$year - Annual Report.pdf")
      $textPath = Join-Path $temporaryDirectory "$($company.Ticker)-$year.txt"
      $text = Read-ReportText $pdfPath $textPath

      $wordCount = [regex]::Matches($text, "(?i)\b[A-Za-z][A-Za-z0-9'\-]*\b").Count
      $termCounts = New-ZeroCounts $termPatterns.Keys
      $themeCounts = New-ZeroCounts $themePatterns.Keys
      $frameCounts = New-ZeroCounts $frameNames

      foreach ($term in $termPatterns.Keys) {
        $termCounts[$term] = [regex]::Matches($text, $termPatterns[$term]).Count
      }

      $codedPassages = 0
      $evidence = ''
      foreach ($passage in (Get-ReportPassages $text)) {
        $isDirect = $passage -match $directCue
        $isSupported = ($passage -match $supportProcessCue) -and ($passage -match $supportObligationCue)
        if (!($isDirect -or $isSupported)) { continue }

        $context = Get-CodingContext $passage
        $codedPassages++
        foreach ($theme in $themePatterns.Keys) {
          if ($context -match $themePatterns[$theme]) { $themeCounts[$theme]++ }
        }
        $frame = Get-PrimaryFrame $context
        $frameCounts[$frame]++

        if ($IncludeEvidence -and !$evidence) {
          $evidence = $context.Substring(0, [Math]::Min(360, $context.Length))
        }
      }

      [void]$records.Add([pscustomobject]@{
        Ticker = $company.Ticker
        Company = $company.Name
        DirName = $company.DirName
        Year = $year
        Words = $wordCount
        Coded = $codedPassages
        Terms = $termCounts
        Themes = $themeCounts
        Frames = $frameCounts
        Evidence = $evidence
      })

      if (($processed % 11) -eq 0) {
        Write-Output "shard=$Shard extracted=$processed/$($companies.Count * 11)"
      }
    }
  }
}
finally {
  if (Test-Path -LiteralPath $temporaryDirectory) {
    Remove-Item -LiteralPath $temporaryDirectory -Recurse -Force -ErrorAction SilentlyContinue
  }
}

$resultPath = Join-Path $outputPath "balanced-regulatory-shard-$Shard.json"
$records | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding UTF8
Write-Output "written=$resultPath records=$($records.Count)"
