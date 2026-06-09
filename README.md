# Lord and Maiden — Wiki Data Project

Reverse-engineering the game **Lord and Maiden** (Unity/IL2CPP, dev `fyf`) to
extract its stats, formulas, build/queue tables, etc. — so the community has a
real reference for a game with little public info.

## Key finding: nothing is encrypted
The game uses **YooAsset** (plain `UnityFS` bundles) + **HybridCLR** (game C#
ships as plain .NET DLLs). No asset decryption is needed — the work is
*extraction + decompilation*. See [`notes/01-recon-and-encryption.md`](notes/01-recon-and-encryption.md).

- **Formulas / logic** → decompiled C# (`Assembly-CSharp`).
- **Stats / tables** → ~104 plain-XML configs at `Assets/Resources_AB/Xml/*.xml`
  (loaded as `TextAsset`s from bundles).

## Layout
```
notes/        findings, methodology, encryption analysis
tools/        extraction & parsing scripts
extracted/    raw outputs — DLLs, bundle assets, raw XML   (gitignored)
decompiled/   decompiled C# from the hot-update DLLs        (gitignored)
data/         curated, human-readable stats/formulas (the wiki source)
```

## Reproduce
1. Decompile hot-update DLLs: `ilspycmd` (ILSpy) on the `*.rawfile`s in
   `StreamingAssets/yoo/DefaultPackage/` (they're .NET assemblies). Output in `decompiled/`.
2. Extract XML configs from the bundles: `python tools/extract_xml_configs.py`.
3. Parse/curate into `data/`.

Requires: Python 3 + `UnityPy`, and `dotnet tool install -g ilspycmd`.

> Educational/community reference. Game assets and code are property of the developer.
