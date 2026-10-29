param([Parameter(Mandatory=$true)][string]$Ps2ExeModule,[switch]$Console)
$ErrorActionPreference='Stop'
if ($PSVersionTable.PSEdition -ne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5) { throw 'Build with Windows PowerShell 5.1.' }
$builder=Join-Path (Split-Path (Resolve-Path -LiteralPath $Ps2ExeModule)) 'ps2exe.ps1'
if ((Get-FileHash -LiteralPath $builder -Algorithm SHA256).Hash -ne '94613E703FA2EC67A01255E5917A056A9406FD31C557685B7AE76417F706A09A') { throw 'Unexpected PS2EXE builder; use the pinned checkout in BUILD_AND_TEST.md.' }
Import-Module $Ps2ExeModule -Force
if ((Get-Module ps2exe).Version -ne [version]'1.0.18') { throw 'PS2EXE 1.0.18 is required.' }
$source = @(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '2ch_downloader_*.ps1')
if ($source.Count -ne 1) { throw 'Expected one downloader source file.' }
$tokens=$null; $parseErrors=$null
[void][Management.Automation.Language.Parser]::ParseFile($source[0].FullName,[ref]$tokens,[ref]$parseErrors)
if ($parseErrors.Count) { throw ($parseErrors | Out-String) }
Invoke-ps2exe -inputFile $source[0].FullName -outputFile (Join-Path $PSScriptRoot '2ch_downloader.exe') -noConsole:(!$Console) -STA -x64 -lcid 1033 -title '2ch downloader' -product '2ch downloader' -version '1.0.1.0'
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot '2ch_downloader.exe'))) { throw 'Build output missing.' }
Get-FileHash -LiteralPath (Join-Path $PSScriptRoot '2ch_downloader.exe') -Algorithm SHA256
