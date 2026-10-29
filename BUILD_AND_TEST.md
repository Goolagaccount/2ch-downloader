# Build and test results — attachment support

Version 1.0.2.0, verified 2026-10-29. Based on repository head
`6b193ab95d84330388f04ee2a15d05a8066017f4`.

## What the preserved originals show

The author-supplied pair in commit `5c97ea34394b0f926eee6feed1286988797685d3`
contains a 21,362-byte UTF-16 PS1 and a 46,592-byte EXE. The full original PS1
bytes occur inside that EXE at offset 7700 (text after the BOM at 7702).
Its attachment regex is limited to `/b/src/<thread>/` and listed image/video
extensions. The previously rebuilt version used the same format restriction.

The original embedded worker was run on a controlled PDF-only page containing
`/b/src/212/1.pdf`: `Ok=true`, `Downloaded=0`. The updated worker on the same
fixture returned `Downloaded=1`, with byte-exact PDF contents. This establishes
the restriction of the preserved source/embedded worker; it does not disprove
the author's experience with another historical build. The legacy EXE GUI was
not independently automated for this comparison. Original artifacts remain
unchanged in Git history.

## Current behavior

The thread URL accepts any ordinary board name, not just `/b/`. Attachment
links are read from native `post__file-attr` captions and `post__image-link`
anchors, rather than all links on the page. There is no extension whitelist.
URLs must match the selected board/thread attachment directory and contain a
safe leaf filename. External post links, navigation and thumbnails are not
download declarations. HTTP/HTTPS, final response URI after redirects and
absolute CDN origins are retained.

Files are saved only, never executed or automatically opened. Traversal,
encoded separators, Windows device names, invalid/trailing characters and
reserved service names (`file_links.txt`, `errors.txt`, `.part` suffix) are
rejected. Incomplete responses are not promoted to the final filename.

## Rebuild and test

Windows 10 build 19045; Windows PowerShell **5.1.19041.6456**; PS2EXE
**1.0.18**; Python **3.14.4**, standard library only. From the parent folder:

```powershell
git clone https://github.com/MScholtes/PS2EXE.git build-tools/PS2EXE
git -C build-tools/PS2EXE checkout 05c62615b33864c177f5de8e56e06e4c7f34adbb
powershell -NoProfile -ExecutionPolicy Bypass -File .\2ch-downloader\build.ps1 -Ps2ExeModule .\build-tools\PS2EXE\Module\ps2exe.psd1
powershell -NoProfile -ExecutionPolicy Bypass -File .\2ch-downloader\tests\url_logic.ps1 -Cases .\2ch-downloader\tests\url_cases.json
python .\2ch-downloader\tests\integration.py
Get-FileHash .\2ch-downloader\2ch_downloader.exe -Algorithm SHA256
```

The temporary process-only execution option was explicitly authorized. No
persistent OS, antivirus or security settings were changed. The builder is a
local checkout, not a globally installed module; `build.ps1` checks version
and builder SHA256 before import:
`94613E703FA2EC67A01255E5917A056A9406FD31C557685B7AE76417F706A09A`.
Flags: x64, STA, no console, LCID 1033, version 1.0.2.0. Source encoding:
UTF-16 LE with BOM. This is a repeatable procedure, not a claim of bit-for-bit
deterministic compiler output.

**Current EXE SHA256:** `2E5272E70F281CF319B22EAFCEDECF371A32A2347237E4715A93289CAC874A6B`

## Passed checks

- Actual rebuilt GUI: eight byte-exact attachments each in `/b/` and `/pr/`:
  PDF, TXT, ZIP, DOCX, PNG, WEBM, unknown `.xyz`, and a filename with a space.
  PDF/DOCX/archive fixtures are generated locally; the WEBM fixture is only
  synthetic transport bytes, not a playback test.
- Same-thread file URLs inside ordinary post text were not downloaded.
  External document links, navigation, scripts, other-thread paths and unsafe
  names were not requested, verified by fixture server request counts.
- Three sequential runs in one window: download counts 2, 0, 0; skip counts
  0, 2, 2; one result per run; restored controls and successful own-job removal.
- Real local redirect between hostnames, preserved absolute media origin and
  protocol-relative URL resolution.
- Transient/persistent HTTP 503, empty and truncated responses, HTTP 404,
  existing empty files, stale staging files, invalid output directory and
  closing during a slow request.
- **34 URL cases** in the actual Windows PowerShell/.NET resolver.
- Final EXE `-extract` output matches final source text exactly, after
  normalizing line endings. Original embedded source comparison and the
  PDF-only original/current worker comparison were completed separately.

The GUI test entry point runs the real form event loop, download button,
worker jobs and completion timer, recording results instead of showing modal
result boxes. It is not an independent manual/visual inspection. Test output
and downloaded fixture data stay outside the repository.

## Prior live verification and limits

The previous EXE (SHA256
`903D65482E9E4BAB9D534061A1D4BDBDFA21E9B3E16B3A96E84E28923DB76925`)
was tested on live 2ch.su: five images, 1,807,705 bytes, no failures. Its full
report is preserved at commit `6b193ab95d84330388f04ee2a15d05a8066017f4`.
The new attachment build was tested on controlled fixtures; no fresh live
archive of arbitrary documents was downloaded. Current native attachment
markup was inspected, but older/nonstandard mirror templates can differ.

Existing nonempty final files are skipped without a trusted hash/size check.
Closing during transfer can leave a staging file that the next attempt
overwrites. Authentication, CAPTCHA/anti-bot challenges and video playback
were not tested. No mirror discovery or license was added. No downloaded
third-party files, page text, private paths or chat logs are published.
