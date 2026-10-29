param([Parameter(Mandatory=$true)][string]$Url,[Parameter(Mandatory=$true)][string]$Root)
$ErrorActionPreference='Stop'
$source=Get-ChildItem -LiteralPath (Split-Path $PSScriptRoot) -Filter '2ch_downloader_*.ps1'
$t=$null;$e=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($source.FullName,[ref]$t,[ref]$e)
$assignment=$ast.Find({param($node) $node -is [Management.Automation.Language.AssignmentStatementAst] -and $node.Left.Extent.Text -eq '$downloadWorker'},$true)
$block=[scriptblock]::Create($assignment.Right.Expression.ScriptBlock.Extent.Text.Trim().TrimStart('{').TrimEnd('}'))
$job=Start-Job -ScriptBlock $block -ArgumentList $Url,$Root
try { $job | Wait-Job | Out-Null; Receive-Job -Job $job -ErrorAction Stop | ConvertTo-Json -Depth 6 } finally { Remove-Job $job -Force }
