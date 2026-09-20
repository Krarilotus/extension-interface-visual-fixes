# Offline regression tests

Install Python dependencies from `requirements-test.txt` and FASM (or set `FASM`
to its executable). The harness runs UCP 3.0.7's actual Lua compiler and assembler
wrappers, with native memory I/O and fixture scanning substituted for the game.
Fetch the pinned framework source before running tests:

```sh
git clone --filter=blob:none --no-checkout https://github.com/UnofficialCrusaderPatch/UnofficialCrusaderPatch3.git .framework-fixture
git -C .framework-fixture checkout 77c6accf14a55fb95434fe6ffd96516e005568b5 -- content/ucp/code/core.lua content/ucp/code/utils.lua
python -m pytest -q
```

Alternatively, set `UCP_FRAMEWORK` to an existing checkout with those exact files.
The harness verifies their hashes after normalizing line endings. This source is
test-only, is not vendored and is not included in the extension package.
Lupa's Lua 5.4 backend matches UCP's Lua family. Tower/cliff instruction fixtures
are assembled once per input; every emulated case still gets fresh game memory.

On Windows, use `python -m pytest -p no:faulthandler -q` to avoid Python reporting
Unicorn's handled native exceptions as crashes. See the CI workflow for the
separate package and actual GUI localization checks.
