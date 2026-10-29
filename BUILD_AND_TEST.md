# Build and test results

Verified on 2026-10-29. Based on published mirror-support commit
`e4be7b055bd4b69b8843c23c8e39c7f50ab76b6b`.
The original author-supplied source and EXE remain in Git history.

## Rebuild

Tools used: Windows 10 build 19045, Windows PowerShell **5.1.19041.6456**,
PS2EXE **1.0.18**, Python **3.14.4** (tests use only its standard library),
Git **2.53.0.windows.3**.

From a parent directory containing this repository:

```powershell
git clone https://github.com/MScholtes/PS2EXE.git build-tools/PS2EXE
git -C build-tools/PS2EXE checkout 05c62615b33864c177f5de8e56e06e4c7f34adbb
powershell -NoProfile -ExecutionPolicy Bypass -File .\2ch-downloader\build.ps1 -Ps2ExeModule .\build-tools\PS2EXE\Module\ps2exe.psd1
powershell -NoProfile -ExecutionPolicy Bypass -File .\2ch-downloader\tests\url_logic.ps1 -Cases .\2ch-downloader\tests\url_cases.json
python .\2ch-downloader\tests\integration.py
Get-FileHash .\2ch-downloader\2ch_downloader.exe -Algorithm SHA256
```

The process-only execution-policy option was explicitly authorized for this
build and testing. No persistent policy or antivirus settings were changed.
The builder is a local checkout, not a globally installed module. The build
script checks its version and SHA256 before importing it:
`94613E703FA2EC67A01255E5917A056A9406FD31C557685B7AE76417F706A09A`.

Build flags: x64, STA, no console, LCID 1033, assembly version 1.0.1.0.
The source is UTF-16 LE with BOM. This is a repeatable build procedure;
PS2EXE/compiler output is not claimed to be bit-for-bit deterministic.

Published EXE SHA256:

`903D65482E9E4BAB9D534061A1D4BDBDFA21E9B3E16B3A96E84E28923DB76925`

## Results — passed

| Check | Observed result |
| --- | --- |
| Actual Windows PowerShell/.NET URL resolver | All 27 cases passed: mirror domains, HTTP/HTTPS, absolute and protocol-relative URLs, relative paths, query encoding, dangerous schemes/paths/names and unsupported extensions. No network used for these cases. |
| Embedded source | EXE `-extract` output matches the final source text exactly after normalizing line endings. |
| Clean GUI download | Exactly two expected fixture payloads; `Ok=true`, no error log, controls restored. |
| Three runs in the same GUI | Download counts 2, 0, 0; skip counts 0, 2, 2; exactly one result per run. |
| Query and fragment | Thread URL remains valid with both. |
| Real HTTP redirect | Redirect from 127.0.0.1 to localhost; relative links use final origin, absolute media retain their original origin, protocol-relative links resolve correctly. |
| Temporary HTTP 503 | Exactly three requests, success on the third. |
| Persistent HTTP 503 | Three attempts; failure returned, no final or staging file. |
| Empty / truncated response | Three attempts; failure returned, no final or staging file. |
| Existing empty file / stale staging file | Complete expected bytes replace them. |
| HTTP 404 page | Error result, restored controls. |
| Misleading extension / documents | `.jpg.exe`, PDF and DOCX are excluded. |
| Output path is a file | Rejected before network work. |
| Job lifecycle | Own `Remove-Job` calls succeed after completion; active handle cleared. Closing during a slow request successfully stops/removes the own job and exits. |

`tests/integration.py` runs the actual rebuilt GUI EXE, its form event loop,
download-button handler, background jobs and completion timer. Test mode records
results instead of showing modal result boxes, then closes the window. It only
accepts HTTP loopback fixture URLs. A separate source-worker smoke check was
also executed successfully under Windows PowerShell 5.1 (`tests/worker.ps1`).
This is runtime integration testing, not an independent visual/manual inspection.
It does not enumerate the user's scheduled jobs.

The local integration suite downloads only neutral synthetic data from its HTTP server. The PNG
is a one-pixel test image; `.webm` bytes are an explicitly synthetic transport
fixture, not a playback test. Test data and results live in temporary folders
outside the repository. No real imageboard content or private logs are included.

## Live verification — 2026-10-29, 08:44–08:45 UTC

The exact published EXE from commit
`6082a6f4097e21b3484a9490775993657c470d06` was verified by Git blob
`740dc48c2baf2deeba971f2430ea2dc93774eb7e` and the SHA256 above, then
tested against `https://2ch.su/b/res/337795941.html`.

- Page returned HTTP 200; five supported image links were present.
- The actual EXE form event loop and download-button handler returned
  `Ok=true`, `Downloaded=5`, `Skipped=0`, `Failed=0`; exit code 0.
- Controls were restored, the own job was successfully removed and the active
  job handle was cleared.
- All five linked filenames existed, were nonempty and had valid PNG/JPEG
  signatures. Total downloaded size: **1,807,705 bytes**; individual sizes:
  151,432; 384,824; 10,588; 6,423; 1,254,438 bytes.
- Images were opened successfully for local inspection. Images, page text and
  machine-specific paths were not uploaded to the repository.

This was an automated GUI integration run, not manual inspection of a modal
dialog. The published loopback test entry point received one local HTTP
redirect to this explicitly authorized live URL; the EXE itself fetched the
real HTTPS page and media. The binary, page responses and network settings
were not modified. No CAPTCHA, anti-bot, antivirus or network barrier was
bypassed. No code fix or rebuild was needed.

## Scope and remaining limits

The completion/error, retry, staging-file and job cleanup fixes preserve the
existing `/b/` and image/video scope. There is no automatic mirror discovery
and no document support. Existing nonempty final files are skipped without a
trusted hash/size check; an old partial file saved under its final name cannot
be recognized reliably. Closing during a transfer can leave a `.part` file;
the next attempt overwrites it. Authentication, anti-bot challenges and playback
of downloaded videos were not tested. No license was added.
