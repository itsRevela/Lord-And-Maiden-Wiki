# Lord and Maiden — Recon & "Encryption" Analysis

**Game:** Lord and Maiden (dev: `fyf`) — Steam, Windows.
**Path:** `C:\Program Files (x86)\Steam\steamapps\common\LAM\Lord and Maiden_Data`
**Engine:** Unity, **IL2CPP** (`GameAssembly.dll` + `il2cpp_data/Metadata/global-metadata.dat`).
**Asset system:** **YooAsset** (`StreamingAssets/yoo/DefaultPackage/`, manifest format `OOY` v1.5.2).
**Hot-update:** **HybridCLR** — game C# ships as plain .NET DLLs stored as YooAsset `*.rawfile`.

## TL;DR — there is NO asset encryption
**Nothing here is encrypted:**

| Thing | State |
|---|---|
| 1278 `*.bundle` files | **Plain `UnityFS`** (verified 1278/1278 start with `UnityFS\0`). Readable by UnityPy/AssetStudio directly. |
| YooAsset manifest (`*.bytes`) | Standard `OOY` v1.5.2 binary, plaintext asset paths. |
| `*.rawfile` (7 files) | **Plain .NET assemblies** (`MZ`/`PE`). HybridCLR hot-update + AOT-ref DLLs. Decompile directly. |
| XML config / stats | Plain-text XML `TextAsset`s inside bundles. |

There IS a `home.MemoryEncrypt` namespace in the game code, but that's **runtime in-memory value protection (anti-cheat)** for live values — it does not encrypt anything on disk.

## The 7 `*.rawfile` DLLs (copied to `extracted/dlls/`, decompiled to `decompiled/`)
| short | size | identity |
|---|---|---|
| `eb46ed1b3cbb` | 2.97 MB | **Assembly-CSharp — the game logic** (Formula, Battle, Build, Hero, Troop, …) |
| `d0968bf93e90` | 2.45 MB | `mscorlib` (BCL) |
| `5263bd29cb11` | 0.57 MB | `System` |
| `16deaab43b38` | 0.56 MB | `UnityEngine.CoreModule` |
| `b05e748f50fa` | 0.38 MB | Steamworks.NET |
| `ea5d17f5c198` | 0.34 MB | UniTask |
| `eec5ad6bf783` | 0.12 MB | `System.Core` |

## Where the game data lives
- **Calculations / formulas / logic:** `decompiled/eb46ed1b3cbb.cs` (Assembly-CSharp). Classes: `Formula`, `FormulaQuickAdd`, `FormulateQueue`, `Battle*`, `BuildBase`, `BuildNeed`, `BuildRemainTime`, `FightBuildTimeInfo`, `Hero`, `Troop`, etc. Config POCOs use a custom `[XMLExtension("field")]` attribute mapping to XML.
- **Stats / tables (the numbers):** ~104 config files at `Assets/Resources_AB/Xml/*.xml` (+ a few `.txt`/`.asset`), loaded as `TextAsset` from bundles via `LoadXmlData(name)` → `XmlDocument.LoadXml(text)`. Examples: `Formula.xml`, `HeroInfo.xml`, `HeroTalent.xml`, `BuildBaseInfo.xml`, `BuildNeed.xml`, `BuildUnLockInfo.xml`, `NewSkillInfo.xml`, `Buff.xml`, `Assess.xml`, `CityLvUnlock.xml`, plus `Language_*.xml` localization tables.

## Extraction plan
1. **DLLs → C#:** done (`decompiled/`). Mine `eb46…` for damage/power/queue/build-time formulas.
2. **XML configs → `data/xml/`:** extract the `Resources_AB/Xml` `TextAsset`s from the bundles (UnityPy). These are the stat tables.
3. Cross-reference schema (decompiled POCO classes + `[XMLExtension]`) with the XML to produce clean, documented tables + formulas for the wiki.

## Tooling
- `tools/` — extraction/parse scripts.
- Decompiler: `ilspycmd` (ILSpy 10.1) via `dotnet tool`.
- `UnityPy` for reading bundles (no decryption needed).
