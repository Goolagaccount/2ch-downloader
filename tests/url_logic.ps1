param([Parameter(Mandatory=$true)][string]$Cases)
$ErrorActionPreference='Stop'
$source=Get-ChildItem -LiteralPath (Split-Path $PSScriptRoot) -Filter '2ch_downloader_*.ps1'
$t=$null;$e=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($source.FullName,[ref]$t,[ref]$e)
if ($e.Count) { throw ($e | Out-String) }
$definition=$ast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Get-SafeMediaUrl'},$true)
. ([scriptblock]::Create($definition.Extent.Text))
$all=Get-Content -LiteralPath $Cases -Raw | ConvertFrom-Json
foreach($case in $all) {
    $actual=Get-SafeMediaUrl -BaseUri ([uri]$case[0]) -Link $case[1] -ThreadId '123'
    if ($actual -cne $case[2]) { throw ('Unexpected URL result: ' + $case[1] + ' => ' + $actual) }
}
'PASS '+$all.Count+' URL cases in actual Windows PowerShell/.NET resolver; no network requests.'
