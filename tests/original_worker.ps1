param([Parameter(Mandatory=$true)][string]$Source,[Parameter(Mandatory=$true)][string]$Url,[Parameter(Mandatory=$true)][string]$Root)
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$ErrorActionPreference='Stop'
$t=$null;$e=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Resolve-Path -LiteralPath $Source),[ref]$t,[ref]$e)
$command=$ast.Find({param($n) $n -is [Management.Automation.Language.CommandAst] -and $n.GetCommandName() -eq 'Start-Job'},$true)
$expression=$command.CommandElements | Where-Object {$_ -is [Management.Automation.Language.ScriptBlockExpressionAst]} | Select-Object -First 1
$block=[scriptblock]::Create($expression.ScriptBlock.Extent.Text.Trim().TrimStart('{').TrimEnd('}'))
$job=Start-Job -ScriptBlock $block -ArgumentList $Url,$Root
try { $job | Wait-Job | Out-Null; Receive-Job -Job $job -ErrorAction Stop | ConvertTo-Json -Depth 6 } finally { Remove-Job $job -Force }
