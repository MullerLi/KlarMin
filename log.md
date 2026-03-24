# Project Log

## Project Purpose

This project builds a modified KlarMin-based Traditional Chinese font by merging glyphs from multiple reference fonts and then cleaning up the project directory so future work stays manageable.

Current release goal:

- Keep one latest release font in the project root.
- Keep source/reference fonts in `referenceFont`.
- Keep build scripts in `tools`.
- Keep logs, audits, and candidate lists in `reports`.
- Keep old generated fonts and `.sfd` backups in `archive`.

## Current Latest Font

Latest release font kept in the root:

- `KlarMinTC-Regular-GenKiMerriMix-ItalicAlt-v3.ttf`

This is the font a future agent should treat as the current canonical output unless the user explicitly says otherwise.

## Reference Fonts

Primary references used in this conversation:

- `referenceFont/GenKiMin2TW-R.otf`
- `referenceFont/Merriweather-Regular.ttf`
- `referenceFont/Merriweather-Italic.ttf`
- `referenceFont/TRWUDMincho-R.ttf`
- `referenceFont/GenYoMin2-R.ttc`

Base font:

- `archive/fonts/KlarMinTC-Regular.ttf`

Note:

- The original base font was moved to `archive/fonts` during cleanup to keep the root simple.

## What Was Done In This Conversation

### 1. Symbol and punctuation merge

Starting point:

- Base font: `KlarMinTC-Regular.ttf`

Merge strategy:

- Use `GenKiMin2TW-R.otf` to replace CJK punctuation, bopomofo, and symbol-related blocks.
- Use `Merriweather-Regular.ttf` to replace non-CJK western punctuation and symbols.

Important implementation detail:

- `GenKiMin2TW-R.otf` uses `unitsPerEm = 1000`.
- KlarMin uses `unitsPerEm = 2048`.
- Copying GenKi glyphs without scaling makes fullwidth punctuation look too small.
- Result: GenKi-derived glyphs must be post-scaled by `2048 / 1000 = 2.048`.

### 2. Italic alternates inside the same font

We added Merriweather italic forms as alternate glyphs, not as direct replacements.

Implementation approach:

- Import italic alternates from `Merriweather-Italic.ttf`.
- Add an OpenType `ss20` feature so supporting software can switch western letters, digits, and western punctuation to italic alternates.

This work produced the `ItalicAlt` variants.

### 3. Coverage audit

We audited missing characters against the reference fonts.

Key findings before the last repair:

- No important printable characters were missing from `Merriweather-Regular.ttf` or `TRWUDMincho-R.ttf`.
- One useful printable character was missing from `Merriweather-Italic.ttf`: `U+2009 THIN SPACE`.
- High-priority missing printable characters mainly came from `GenKiMin2TW-R.otf` / `GenYoMin2-R.ttc`:
  - Vietnamese and Latin Extended letters
  - A few modifier letters and combining marks
  - A small set of symbols such as `U+22EF`
  - Some dingbat circled digits
- Large remaining gaps were mostly optional low-priority blocks:
  - CJK Unified Ideographs
  - CJK Ext A
  - Hangul
  - CJK Compatibility Ideographs

### 4. High-priority character repair

We then added the high-priority missing printable characters:

- `135` GenKi-derived characters
- `1` Merriweather-Italic-derived character (`U+2009 THIN SPACE`)

After this repair, the coverage audit reported:

- No remaining high-priority candidate characters missing from the current reference set.

### 5. Folder cleanup

The root directory was intentionally cleaned so it does not become a dump of old outputs and scripts.

Cleanup result:

- Root keeps the latest release font.
- Old generated fonts were moved to `archive/fonts`.
- `.sfd` backups were moved to `archive/sfd`.
- Build scripts were moved to `tools`.
- Audit reports, logs, and candidate lists were moved to `reports`.

## Folder Layout Rules

These rules should be preserved unless the user asks for a different structure.

### Root

Keep only:

- The latest release font
- `referenceFont/`
- Long-term project notes like `log.md` and `README.md`
- User-provided assets such as sample text or screenshots

Avoid leaving these in the root after builds:

- Old `.ttf` outputs
- `.sfd` backups
- `.log` files
- temporary candidate lists
- build scripts

### tools

Put reusable build and repair scripts here.

Current important scripts:

- `tools/merge_klarmin_symbols.py`
- `tools/postprocess_genki_scale.py`
- `tools/add_merriweather_italic_alts.py`
- `tools/add_priority_missing_chars_ff.py`
- `tools/add_priority_missing_chars.py`
- `tools/audit_font_coverage.py`

### reports

Put generated text outputs here:

- audit results
- merge logs
- candidate codepoint lists
- text reports used for inspection

### archive/fonts

Put old generated `.ttf` files here, including:

- intermediate builds
- previous release candidates
- base font backups no longer intended to stay in root

### archive/sfd

Put all `.sfd` backups here.

## Recommended Rebuild Workflow

If a future agent needs to rebuild the latest font, use this mental model:

1. Start from the merged KlarMin pipeline, not from scratch guessing.
2. Use FontForge for cross-font glyph copying.
3. Use fontTools for post-scaling and GSUB feature work.
4. After generating files, re-clean the root so only the latest release font remains there.

Useful commands from the project root:

```powershell
python tools\add_priority_missing_chars.py
python tools\audit_font_coverage.py --target KlarMinTC-Regular-GenKiMerriMix-ItalicAlt-v3.ttf --report reports\font_coverage_audit-v3.txt
```

Important note:

- `tools/add_priority_missing_chars.py` will generate intermediate files in the root while running.
- After a rebuild, move new logs to `reports`, move intermediate `.ttf` to `archive/fonts`, and move new `.sfd` to `archive/sfd`.
- Keep the newest final release font in the root.

## Font Design And Implementation Knowhow

### UPM mismatch is critical

This project already hit a real issue here.

- `GenKiMin2TW-R.otf` is `1000 UPM`.
- KlarMin is `2048 UPM`.
- If glyphs are copied directly, especially fullwidth punctuation, they look too small next to Han characters.

Rule:

- Any newly copied GenKi glyphs must be scaled after merge.

### FontForge is safer for cross-font glyph transfer

For this project, pure fontTools is not the best first tool for copying glyphs between OTF and TTF.

Why:

- FontForge handles cross-font copy/paste more directly.
- It is better for creating missing Unicode slots and outputting a working font.

Rule:

- Use FontForge for glyph transfer.
- Use fontTools for audits, postprocessing, and OpenType feature injection.

### Copying glyphs is not the same as copying layout behavior

Copying outlines and widths does not automatically import all GSUB/GPOS behavior.

Implications:

- For punctuation and many standalone symbols, this is usually acceptable.
- For combining marks or advanced script behavior, shape presence does not guarantee ideal layout behavior.

### Italic alternates are provided through `ss20`

The current italic strategy is:

- Keep the normal western glyphs as default.
- Add italic alternates.
- Expose them through OpenType feature `ss20`.

Implication:

- Software must support stylistic sets to show those alternates.

### Audit before large merge decisions

Before adding huge character sets, always audit first.

Reason:

- Large CJK or Hangul merges can significantly expand the font.
- Not every missing codepoint is worth adding.

Rule:

- Prioritize printable, high-value additions first.
- Treat massive rare CJK/Hangul imports as a separate product decision.

## Current Known State

As of the end of this conversation:

- High-priority printable gaps from the current reference fonts are resolved.
- Remaining missing characters are mostly optional large ranges from GenKi / GenYo:
  - CJK Unified Ideographs
  - CJK Ext A
  - Hangul
  - CJK Compatibility Ideographs

This means future work is now more about scope choice than bug fixing.

## Suggested Future Goals

These are the most natural next steps.

### 1. Decide whether to expand rare Han coverage

Open question:

- Should the project remain focused on core Traditional Chinese + western typography quality?
- Or should it absorb large rare CJK coverage from GenKi / GenYo?

This is the next biggest product decision.

### 2. Decide whether to add Hangul

The current font does not pull in the large Hangul ranges from GenKi / GenYo.

That may be correct.

Only do this if the user explicitly wants Korean support in the same font.

### 3. Improve release naming

The current release filename works, but it is long.

A future agent may want to add a shorter alias such as:

- `KlarMinTC-Regular-Latest.ttf`

If doing so, keep the long version too unless the user asks otherwise.

### 4. Automate post-build cleanup

Right now, the build scripts work, but cleanup is still a manual convention.

A future agent could make the build pipeline automatically:

- move intermediate files into archive folders
- move logs into reports
- keep only the newest final release font in the root

## Fast Start For Future Agents

If you are a future agent entering this project, do this first:

1. Read this file.
2. Treat `KlarMinTC-Regular-GenKiMerriMix-ItalicAlt-v3.ttf` as the current canonical font.
3. Check `reports/font_coverage_audit-v3.txt` before deciding what to add next.
4. Use the scripts in `tools/` rather than rebuilding logic from memory.
5. Keep the root clean when you are done.

