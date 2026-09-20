# Capture the next crash

Interface and Visual Fixes writes startup diagnostics automatically through UCP's
normal logger. Keep the default INFO logging level (or more detailed). There is
no extra diagnostic switch and no logging on each frame, tile or simulation tick.

After a crash, **copy `ucp3.log` and `ucp3-error-log.log` from the game folder before
starting the game again**: UCP replaces them at startup. Include the applied UCP
configuration, exact executable name, crash time and a save/reproduction if available.
The log already identifies extension versions and enabled settings. This module
adds native binding/code/cache addresses and which feature installation completed.

These are startup details, not the faulting registers or a history of texture
changes. For those, enable a full Windows crash dump before the next session.

## Optional Windows crash dump

Use Windows' existing [LocalDumps facility](https://learn.microsoft.com/en-us/windows/win32/wer/collecting-user-mode-dumps).
The extension does not install an exception handler or change Windows settings.

In Registry Editor, first check this **application-specific** key:

`HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\Stronghold_Crusader_Extreme.exe`

If it already exists, export it before changing its values so you can restore it.
For regular Crusader, use the actual executable name, normally
`Stronghold Crusader.exe`, instead. In an administrator Command Prompt, run:

```bat
reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\Stronghold_Crusader_Extreme.exe" /v DumpType /t REG_DWORD /d 2 /f
reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\Stronghold_Crusader_Extreme.exe" /v DumpCount /t REG_DWORD /d 3 /f
```

After the next unhandled crash, look in `%LOCALAPPDATA%\CrashDumps` (unless an
existing `DumpFolder` overrides it). Keep the matching `.dmp` together with that
session's logs. Full dumps can be large and contain loaded artwork; share privately.
After testing, restore the exported settings or delete only the application key
you created. Do not remove the global `LocalDumps` key.

This writes a dump when the process crashes, not continuously during play.
An attached debugger, custom crash handler or system policy may prevent capture;
if no dump appears, report that alongside the logs. A Lua startup error dialog
is not itself an unhandled native crash and need not produce a dump.

## Reading the diagnostic context

Use the exact same session's log and full dump. `native binding` lines locate
the resolved native code and data globals; they are not hardcoded addresses.
`native code entry` lines identify injected wrappers. The `render epoch`, tower
cache and cliff cache lines locate existing live state without adding a second
copy or a recording hook.

Each cliff cache entry contains five 32-bit fields: last checked epoch, active
source byte count, capacity in source bytes, heap buffer pointer and validity
flags. There are 32 entries with a 20-byte stride. The heap allocation holds
twice the capacity; the source copy starts at `buffer` and the projection at
`buffer + bytes`. Flags 1/2 mean valid source/projection. In the dump, compare the
faulting source register/address with this state and the `PrimaryImage`,
`SecondaryImage`, `ImageHeaders`, `ImageSizes`, `ImageOffsets` and `ImageData`
bindings. Effective strip height is header height minus seven; each source row
has 30 RGB565 pixels (60 bytes). Inspect actual metadata, including oversized strips.

Startup diagnostics alone cannot establish which texture or mod caused a crash.
The reported intermittent blitter crash remains under investigation in
[issue34](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/34).
