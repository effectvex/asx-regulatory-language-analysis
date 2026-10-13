param(
  [int]$Shard=0,
  [int]$Shards=8,
  [string]$Manifest=(Join-Path $PSScriptRoot '..\data\manifests\asx200-companies.json'),
  [string]$Archive=(Join-Path $PSScriptRoot '..\annual-reports'),
  [string]$OutputDir=(Join-Path $PSScriptRoot '..\data\intermediate'),
  [string]$Ticker='',
  [string]$Pdftotext='pdftotext'
)
# Poppler can emit non-fatal font/xref warnings on otherwise readable PDFs.
# Keep the shard alive so a warning in one report does not discard the batch.
$ErrorActionPreference='Continue'
$archive=(Resolve-Path $Archive).Path;$output=(Resolve-Path $OutputDir).Path;$years=2015..2025
$pdftotext=(Get-Command $Pdftotext -ErrorAction Stop).Source
$terms=[ordered]@{regulation='(?i)\bregulat(?:ion|ions|ory|or|ors)\b';compliance='(?i)\bcomplian(?:ce|ces|t)\b';burden='(?i)\bburdens?\b';requirement='(?i)\brequirements?\b';regulator='(?i)\bregulators?\b';legislation='(?i)\blegislat(?:ion|ions|ive|ed)\b'}
$themePatterns=[ordered]@{
  'Compliance and governance'='(?i)\b(compliance|governance|ethic|conduct|control framework|internal control|code of conduct|anti[- ]bribery|whistleblow)\w*\b'
  'Regulatory change and uncertainty'='(?i)\b(regulatory change|regulatory reform|new legislation|proposed legislation|evolving regulation|changing regulation|regulatory environment|policy change|law reform)\b'
  'Reporting, disclosure and assurance'='(?i)\b(reporting|disclos\w*|audit\w*|assurance|statutory financial|financial statements|annual report|external auditor)\w*\b'
  'Direct cost and resourcing'='(?i)\b(cost|costs|expense|expenses|fee|fees|resource|resourcing|staffing|burden|investment required|financial impact)\w*\b'
  'Systems, data and process implementation'='(?i)\b(system\w*|data|process\w*|implement\w*|monitor\w*|technology|platform|workflow|record[- ]keeping)\b'
  'Licensing, approvals and market access'='(?i)\b(licen[cs]\w*|permit\w*|approval\w*|authori[sz]\w*|accredit\w*|concession\w*|market access)\b'
  'Environmental and climate obligations'='(?i)\b(environment\w*|climate|emission\w*|carbon|biodiversity|pollution|rehabilitation|sustainab\w*)\b'
  'Financial, tax and prudential rules'='(?i)\b(tax\w*|prudential|capital adequacy|solvency|liquidity|financial crime|anti[- ]money laundering|aml|ctf|sanction\w*)\b'
  'Safety, quality and workforce obligations'='(?i)\b(health and safety|workplace|workforce|employee|employment|labour|labor|quality|product safety|occupational|modern slavery)\w*\b'
  'Privacy, cyber and data protection'='(?i)\b(privacy|cyber\w*|data protection|personal information|data breach|information security|cybersecurity)\w*\b'
}
$frames=@('Cost or challenge','Obligation or control','Transition or anticipation','Opportunity or legitimacy','Descriptive or neutral')
if(!(Test-Path -LiteralPath $Manifest)){throw "Missing manifest $Manifest"}
$allCompanies=Get-Content -LiteralPath $Manifest -Raw|ConvertFrom-Json
$sortedCompanies=@($allCompanies|Where-Object { !$Ticker -or [string]$_.Ticker -eq $Ticker }|Sort-Object Ticker)
$companies=New-Object System.Collections.ArrayList
for($ci=0;$ci -lt $sortedCompanies.Count;$ci++){if(($ci % $Shards) -eq $Shard){[void]$companies.Add($sortedCompanies[$ci])}}
$tmpDir=Join-Path $env:TEMP ("balanced-shard-$Shard-"+[guid]::NewGuid().ToString('N'));New-Item -ItemType Directory -Path $tmpDir -Force|Out-Null
$records=New-Object System.Collections.ArrayList;$n=0
try {
 foreach($c in $companies){foreach($y in $years){$n++;$pdf=Join-Path $archive (Join-Path $c.DirName ("$y - Annual Report.pdf"));$txt=Join-Path $tmpDir ("$($c.Ticker)-$y.txt");& $pdftotext -layout -enc UTF-8 $pdf $txt 2>$null;$text=if(Test-Path -LiteralPath $txt){Get-Content -LiteralPath $txt -Raw -Encoding UTF8}else{''};if($null -eq $text){$text=''}
  $words=[regex]::Matches($text,'(?i)\b[A-Za-z][A-Za-z0-9''\-]*\b').Count;$tc=[ordered]@{};$thc=[ordered]@{};$fc=[ordered]@{};foreach($k in $terms.Keys){$tc[$k]=[regex]::Matches($text,$terms[$k]).Count};foreach($k in $themePatterns.Keys){$thc[$k]=0};foreach($k in $frames){$fc[$k]=0};$coded=0;$evidence=''
  foreach($p0 in [regex]::Split($text,'(?<=[\.!\?;:])\s+|\r?\n{2,}')){$p=($p0 -replace '\s+',' ').Trim();if($p.Length -lt 35){continue};$direct=$p -match '(?i)\b(regulat\w*|complian\w*|legislat\w*|statut\w*|licen[cs]\w*|permit\w*|approval\w*|obligat\w*|mandat\w*|regulator\w*|prudential|privacy|cyber\w*)\b';$support=($p -match '(?i)\b(report\w*|audit\w*|assur\w*|disclos\w*|control\w*|monitor\w*|polic\w*|system\w*|process\w*|standard\w*)\b') -and ($p -match '(?i)\b(cost\w*|expense\w*|resource\w*|burden\w*|require\w*|obligat\w*|rule\w*|law\w*|act\b|compliance)\b');if(!($direct -or $support)){continue};$coded++;foreach($k in $themePatterns.Keys){if($p -match $themePatterns[$k]){$thc[$k]++}};$frame='Descriptive or neutral';if($p -match '(?i)\b(cost|costs|expense|expenses|fee|fees|burden|challenge|difficult|complex|resource pressure|delay|risk)\w*\b'){$frame='Cost or challenge'}elseif($p -match '(?i)\b(proposed|future|upcoming|evolving|changing|transition|reform|new regulation|prepare|prepar\w*|expected)\w*\b'){$frame='Transition or anticipation'}elseif($p -match '(?i)\b(opportunit\w*|trust|trusted|legitimacy|leadership|value creation|competitive advantage)\b'){$frame='Opportunity or legitimacy'}elseif($p -match '(?i)\b(required|requirement|obligation|comply|compliance|control|monitor|policy|procedure|assurance|audit)\w*\b'){$frame='Obligation or control'};$fc[$frame]++;if(!$evidence){$evidence=$p.Substring(0,[Math]::Min(360,$p.Length))}}
  [void]$records.Add([pscustomobject]@{Ticker=$c.Ticker;Company=$c.Name;DirName=$c.DirName;Year=$y;Words=$words;Coded=$coded;Terms=$tc;Themes=$thc;Frames=$fc;Evidence=$evidence})
  if(($n%11)-eq 0){Write-Output "shard=$Shard extracted=$n/$($companies.Count*11)"}
 }}} finally {if(Test-Path -LiteralPath $tmpDir){Remove-Item -LiteralPath $tmpDir -Recurse -Force -ErrorAction SilentlyContinue}}
$out=Join-Path $output ("balanced-regulatory-shard-$Shard.json");$records|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $out -Encoding UTF8;Write-Output "written=$out records=$($records.Count)"
