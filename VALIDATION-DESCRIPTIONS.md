# Store and installed descriptions, version 0.1.1

Issue [21](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/21).
Version0.1.0 had no `locale/description-<language>.md` files. Its README and PR
gallery were not description inputs, so the published catalog contained an empty
description list and the installed viewer had nothing to read.

Version0.1.1 includes a short description in all nine supported languages, with
seven feature bullets and only two cropped native screenshots. The crops show
tower foundations/door heights and connected cliff textures. Their coordinates
and original image hashes are recorded in `docs/store/crops.json`; no pixels are
retouched. Absolute HTTPS URLs pin the screenshots to an immutable commit, so
the same Markdown works in both viewers. Images use the existing renderer's
`max-width:100%` behavior and need network access.

A patch version is necessary: the Store builder reuses the complete contents
of an already-published name/version, including its old package and description
list. The new version therefore produces both a new signed package and fresh
online description entries. Build/check tooling now derives the archive name
from the definition instead of hardcoding0.1.0.

Validation:

- 935 tests pass, including nine concise-description/image-path checks and a
  check against accidentally reusing the empty-description release version.
- The built archive includes all nine Markdown files (28 runtime/content files
  total). Existing option localization resolves in all nine GUI languages.
- A task-local harness executes the actual GUI `createIO`,
  `resolveContentDescription` and `SaferMarkdown` code. Filesystem/network
  adapters supply isolated fixtures. Installed and Store selection return the
  expected nonempty text in every language; regional and English fallback pass;
  the renderer emits exactly two images with the existing width constraint.
- The two native screenshot crops were visually inspected. Screenshot URLs are
  checked against the published immutable assets before release acceptance.
- A live browser check was attempted but Computer Use stopped because it could
  not determine the current Windows browser URL reliably. No live GUI rendering
  acceptance is claimed from that attempt. The desktop slot was released.

Game Lua, options and option-label catalogs are unchanged from0.1.0. This release
adds description content, with no new game hook, input path or frame-time cost.
The Store follow-up must verify the published0.1.1 package, all nine description
URLs plus English default, and both image URLs—not just the merge or recipe.
