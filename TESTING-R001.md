# R001 review build

This is an unsigned review build for SHC1.41 and UCP3.0.7, containing R001 plus
its R007 integration base. It is not a release or the owner's combined build.
Use an isolated test installation; keep other feature builds separate.

1. Verify interface-visual-fixes-0.1.0.zip against SHA256SUMS.txt.
2. Extract its contents into ucp/modules/interface-visual-fixes-0.1.0 in the
   isolated installation using the project's developer/test loader workflow.
3. Open that installation in UCP GUI and enable the module. Both options default
   off. Enable **Show Load in skirmish lobby**, apply the configuration and restart.
4. In Crusader, choose a custom skirmish. With only the human present, inspect
   the Load icon right of the master portrait and before the Start hand. Click
   it to open the original dialog; Back returns; reopen and load a valid SP save.
5. Repeat with an AI opponent. With the option disabled and the game restarted,
   the original behavior must return. MP retains its original position/rules.

The archive contains all nine GUI locale catalogs. LOCALIZATION.json records
the title/category/description produced by the actual pinned GUI resolver for
each language without English fallback. This automated check does not establish
native layout quality or independent translation approval in every language.

Native SP placement/click/back/save checks have passed. See VALIDATION-R001.md
and PR12 for remaining acceptance, including native MP, other resolutions,
disabled behavior, empty/invalid saves and translated tooltip layout.
