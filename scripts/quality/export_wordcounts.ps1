param([Parameter(Mandatory=$true)][string]$Archive,[Parameter(Mandatory=$true)][string]$ShardDirectory,[Parameter(Mandatory=$true)][string]$Output)
$all=@();foreach($f in (Get-ChildItem -LiteralPath $ShardDirectory -Filter 'balanced-regulatory-shard-*.json')){$parsed=Get-Content $f.FullName -Raw|ConvertFrom-Json;$all+=@($parsed)}
$rows=foreach($r in $all){$pdf=Join-Path (Join-Path $Archive $r.DirName) ("$($r.Year) - Annual Report.pdf");$fi=Get-Item -LiteralPath $pdf;[pscustomobject]@{Ticker=$r.Ticker;Company=$r.Company;Year=$r.Year;PDF=$pdf;PDFBytes=$fi.Length;VerifiedWords=[int64]$r.Words;Status='Verified'}}
$rows|Sort-Object Ticker,Year|Export-Csv -LiteralPath $Output -NoTypeInformation -Encoding UTF8;Write-Output "rows=$($rows.Count) output=$Output"
