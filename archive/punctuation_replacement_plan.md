# BIZ UD Mincho 繁中全形標點替換計畫書

## 1. 背景與目標

BIZ UD Mincho 為日文明朝體，其全形標點符號依循日文排版慣例：句讀點（、。）置於字面框右上方，括號類偏右或偏上。繁體中文排版要求全形標點置中於字面框。本計畫將源樣明體月版 R（GenYoMin TW R，以下簡稱 GYM-R）的繁中標點字形，逐一覆蓋至 BIZ UD Mincho（以下簡稱 BIZ），產出符合繁中排版習慣的衍生字體。

---

## 2. 前置驗證（Pre-flight Checks）

執行任何替換前，必須先確認以下數值。使用 Python fonttools 執行：

```python
from fontTools.ttLib import TTFont

for path in ["BIZUDMincho-Regular.ttf", "GenYoMinTW-R.ttf"]:
    font = TTFont(path)
    head = font["head"]
    os2 = font["OS/2"]
    hhea = font["hhea"]
    print(f"=== {path} ===")
    print(f"  UPM:            {head.unitsPerEm}")
    print(f"  head yMin/yMax: {head.yMin} / {head.yMax}")
    print(f"  OS/2 sTypoAscender/Descender: {os2.sTypoAscender} / {os2.sTypoDescender}")
    print(f"  OS/2 usWinAscent/Descent:     {os2.usWinAscent} / {os2.usWinDescent}")
    print(f"  hhea ascent/descent:           {hhea.ascent} / {hhea.descent}")
    font.close()
```

**必須確認項目：**

| 項目 | 預期值 | 若不符 |
|------|--------|--------|
| 兩者 UPM 相同 | 均為 1000 | 若不同，需對 GYM-R 字形做等比縮放（scale = BIZ_UPM / GYM_UPM） |
| Vertical metrics 差異 | 記錄但不阻擋 | 標點替換不影響全域 metrics，但需留意字形是否超出 BIZ 的 yMin/yMax |

---

## 3. 需替換的全形標點 Unicode 完整清單

### 3.1 CJK 符號與標點（U+3000–U+303F）

| Unicode | 字元 | 名稱 | 替換優先級 | 說明 |
|---------|------|------|-----------|------|
| U+3001 | 、 | Ideographic Comma（頓號） | **必要** | 日文置右上，繁中置中 |
| U+3002 | 。 | Ideographic Full Stop（句號） | **必要** | 日文置右上，繁中置中 |
| U+3008 | 〈 | Left Angle Bracket（單書名號左） | **必要** | 括號類形狀與位置可能不同 |
| U+3009 | 〉 | Right Angle Bracket（單書名號右） | **必要** | |
| U+300A | 《 | Left Double Angle Bracket（書名號左） | **必要** | |
| U+300B | 》 | Right Double Angle Bracket（書名號右） | **必要** | |
| U+300C | 「 | Left Corner Bracket（單引號左） | **必要** | 日文為主要引號，繁中亦常用 |
| U+300D | 」 | Right Corner Bracket（單引號右） | **必要** | |
| U+300E | 『 | Left White Corner Bracket（雙引號左） | **必要** | |
| U+300F | 』 | Right White Corner Bracket（雙引號右） | **必要** | |
| U+3010 | 【 | Left Black Lenticular Bracket | **必要** | |
| U+3011 | 】 | Right Black Lenticular Bracket | **必要** | |
| U+3014 | 〔 | Left Tortoise Shell Bracket | 建議 | 較少用但仍需一致 |
| U+3015 | 〕 | Right Tortoise Shell Bracket | 建議 | |
| U+3016 | 〖 | Left White Lenticular Bracket | 建議 | |
| U+3017 | 〗 | Right White Lenticular Bracket | 建議 | |
| U+301D | 〝 | Reversed Double Prime Quotation Mark | 選用 | 部分繁中排版使用 |
| U+301E | 〞 | Double Prime Quotation Mark | 選用 | |

### 3.2 全形 ASCII 符號（U+FF00–U+FF60）

| Unicode | 字元 | 名稱 | 替換優先級 | 說明 |
|---------|------|------|-----------|------|
| U+FF01 | ！ | Fullwidth Exclamation Mark | **必要** | |
| U+FF08 | （ | Fullwidth Left Parenthesis | **必要** | |
| U+FF09 | ） | Fullwidth Right Parenthesis | **必要** | |
| U+FF0C | ， | Fullwidth Comma（逗號） | **必要** | 繁中最高頻標點之一 |
| U+FF0E | ． | Fullwidth Full Stop | 建議 | |
| U+FF1A | ： | Fullwidth Colon | **必要** | |
| U+FF1B | ； | Fullwidth Semicolon | **必要** | |
| U+FF1F | ？ | Fullwidth Question Mark | **必要** | |
| U+FF3B | ［ | Fullwidth Left Square Bracket | 建議 | |
| U+FF3D | ］ | Fullwidth Right Square Bracket | 建議 | |
| U+FF5B | ｛ | Fullwidth Left Curly Bracket | 選用 | |
| U+FF5D | ｝ | Fullwidth Right Curly Bracket | 選用 | |
| U+FF5E | ～ | Fullwidth Tilde（全形波浪號） | 建議 | 繁中常用 |

### 3.3 一般標點（Latin/General Punctuation 區段中繁中排版常用者）

| Unicode | 字元 | 名稱 | 替換優先級 | 說明 |
|---------|------|------|-----------|------|
| U+2014 | — | Em Dash（破折號） | **必要** | 繁中使用連續兩個 U+2014 |
| U+2015 | ― | Horizontal Bar | 建議 | 部分系統以此替代 U+2014 |
| U+2018 | ' | Left Single Quotation Mark | 視需求 | 繁中主流用「」，但西式引號仍出現 |
| U+2019 | ' | Right Single Quotation Mark | 視需求 | |
| U+201C | " | Left Double Quotation Mark | 視需求 | |
| U+201D | " | Right Double Quotation Mark | 視需求 | |
| U+2026 | … | Horizontal Ellipsis（刪節號） | **必要** | 繁中置中，日文可能偏下 |
| U+00B7 | · | Middle Dot（間隔號） | **必要** | 繁中人名間隔使用，需置中 |
| U+2027 | ‧ | Hyphenation Point | 建議 | 部分繁中系統用此作間隔號 |
| U+30FB | ・ | Katakana Middle Dot | 建議 | 日文中黑點，繁中有時混用 |

### 3.4 補充：可能需要檢查的字元

| Unicode | 字元 | 名稱 | 說明 |
|---------|------|------|------|
| U+3000 | 　 | Ideographic Space | 全形空格，通常無可見字形但寬度需一致 |
| U+3003 | 〃 | Ditto Mark | |
| U+3005 | 々 | Ideographic Iteration Mark | 日文漢字疊字號，繁中少用但可能出現 |
| U+303B | 〻 | Vertical Ideographic Iteration Mark | 直排用 |
| U+FE30–U+FE4F | ︰︱︳等 | CJK Compatibility Forms（直排標點） | 若需支援直排，整個區段都需檢查 |

---

## 4. 執行計畫

### Phase 1：環境準備

```bash
# 安裝依賴
pip install fonttools brotli

# 確認字體檔案
ls -la BIZUDMincho-Regular.ttf GenYoMinTW-R.ttf
```

### Phase 2：前置驗證（執行第 2 節的腳本）

執行 UPM 與 vertical metrics 驗證腳本，記錄結果。若 UPM 不一致，在 Phase 4 加入縮放步驟。

### Phase 3：字形存在性檢查

在執行替換前，確認 GYM-R 中確實包含目標字形，且 BIZ 中也有對應字形（否則為新增而非替換）。

```python
from fontTools.ttLib import TTFont

TARGET_CODEPOINTS = [
    # 3.1 CJK Symbols and Punctuation
    0x3001, 0x3002,
    0x3008, 0x3009, 0x300A, 0x300B, 0x300C, 0x300D,
    0x300E, 0x300F, 0x3010, 0x3011,
    0x3014, 0x3015, 0x3016, 0x3017,
    0x301D, 0x301E,
    # 3.2 Fullwidth Forms
    0xFF01, 0xFF08, 0xFF09, 0xFF0C, 0xFF0E,
    0xFF1A, 0xFF1B, 0xFF1F,
    0xFF3B, 0xFF3D, 0xFF5B, 0xFF5D, 0xFF5E,
    # 3.3 General Punctuation
    0x2014, 0x2015,
    0x2018, 0x2019, 0x201C, 0x201D,
    0x2026, 0x00B7, 0x2027, 0x30FB,
]

biz = TTFont("BIZUDMincho-Regular.ttf")
gym = TTFont("GenYoMinTW-R.ttf")

biz_cmap = biz.getBestCmap()
gym_cmap = gym.getBestCmap()

print(f"{'Unicode':<10} {'Char':<4} {'BIZ glyph':<20} {'GYM glyph':<20} {'Status'}")
print("-" * 80)
for cp in TARGET_CODEPOINTS:
    char = chr(cp)
    biz_glyph = biz_cmap.get(cp, None)
    gym_glyph = gym_cmap.get(cp, None)
    if gym_glyph and biz_glyph:
        status = "OK - 可替換"
    elif gym_glyph and not biz_glyph:
        status = "NEW - GYM有/BIZ無，需新增"
    elif not gym_glyph:
        status = "SKIP - GYM無此字形"
    else:
        status = "CHECK"
    print(f"U+{cp:04X}    {char:<4} {str(biz_glyph):<20} {str(gym_glyph):<20} {status}")

biz.close()
gym.close()
```

### Phase 4：字形替換（核心步驟）

```python
from fontTools.ttLib import TTFont
from fontTools.pens.t2Pen import T2Pen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.pointPen import SegmentToPointPen
import copy

def replace_glyphs(biz_path, gym_path, output_path, codepoints):
    """
    將 GYM-R 的指定標點字形（含輪廓與寬度）覆蓋至 BIZ UD Mincho。
    """
    biz = TTFont(biz_path)
    gym = TTFont(gym_path)

    biz_upm = biz["head"].unitsPerEm
    gym_upm = gym["head"].unitsPerEm
    scale = biz_upm / gym_upm  # 若 UPM 相同則為 1.0

    biz_cmap = biz.getBestCmap()
    gym_cmap = gym.getBestCmap()

    biz_glyf = biz.get("glyf")  # TrueType outlines
    gym_glyf = gym.get("glyf")

    # 判斷字體輪廓格式
    is_truetype_biz = "glyf" in biz
    is_truetype_gym = "glyf" in gym

    replaced = []
    skipped = []

    for cp in codepoints:
        gym_gname = gym_cmap.get(cp)
        biz_gname = biz_cmap.get(cp)

        if not gym_gname:
            skipped.append((cp, "GYM 無此字形"))
            continue
        if not biz_gname:
            skipped.append((cp, "BIZ 無此字形（需另行新增）"))
            continue

        # --- 替換字形輪廓 ---
        if is_truetype_biz and is_truetype_gym:
            # 兩者皆為 TrueType：直接複製 glyf 表中的字形
            gym_glyph = gym_glyf[gym_gname]
            biz_glyf[biz_gname] = copy.deepcopy(gym_glyph)

            # 若需縮放 (UPM 不同)
            if scale != 1.0:
                g = biz_glyf[biz_gname]
                if g.isComposite():
                    # 複合字形：調整 component offset
                    for comp in g.components:
                        comp.x = int(comp.x * scale)
                        comp.y = int(comp.y * scale)
                else:
                    # 簡單字形：調整座標
                    if g.numberOfContours > 0:
                        coords = g.coordinates
                        g.coordinates = [(int(x * scale), int(y * scale)) for x, y in coords]
        else:
            # CFF/CFF2 輪廓：需使用 Pen 介面轉錄
            # （較複雜，此處提供框架，實際需根據字體格式調整）
            skipped.append((cp, "輪廓格式不同，需手動處理"))
            continue

        # --- 替換寬度 (hmtx) ---
        gym_width, gym_lsb = gym["hmtx"][gym_gname]
        if scale != 1.0:
            gym_width = int(gym_width * scale)
            gym_lsb = int(gym_lsb * scale)
        biz["hmtx"][biz_gname] = (gym_width, gym_lsb)

        # --- 若有 vmtx（直排寬度），一併替換 ---
        if "vmtx" in biz and "vmtx" in gym:
            gym_vwidth, gym_tsb = gym["vmtx"][gym_gname]
            if scale != 1.0:
                gym_vwidth = int(gym_vwidth * scale)
                gym_tsb = int(gym_tsb * scale)
            biz["vmtx"][biz_gname] = (gym_vwidth, gym_tsb)

        replaced.append(cp)

    # 儲存
    biz.save(output_path)
    biz.close()
    gym.close()

    return replaced, skipped


# --- 執行 ---
CODEPOINTS_MUST = [
    0x3001, 0x3002,
    0x3008, 0x3009, 0x300A, 0x300B, 0x300C, 0x300D,
    0x300E, 0x300F, 0x3010, 0x3011,
    0xFF01, 0xFF08, 0xFF09, 0xFF0C, 0xFF0E,
    0xFF1A, 0xFF1B, 0xFF1F,
    0x2014, 0x2026, 0x00B7,
]

CODEPOINTS_RECOMMENDED = [
    0x3014, 0x3015, 0x3016, 0x3017,
    0x2015, 0x2027, 0x30FB,
    0xFF3B, 0xFF3D, 0xFF5B, 0xFF5D, 0xFF5E,
]

CODEPOINTS_OPTIONAL = [
    0x301D, 0x301E,
    0x2018, 0x2019, 0x201C, 0x201D,
]

# 分批執行，先替換必要項目
all_targets = CODEPOINTS_MUST + CODEPOINTS_RECOMMENDED + CODEPOINTS_OPTIONAL

replaced, skipped = replace_glyphs(
    biz_path="BIZUDMincho-Regular.ttf",
    gym_path="GenYoMinTW-R.ttf",
    output_path="BIZUDMincho-TWPunct.ttf",
    codepoints=all_targets,
)

print(f"\n替換完成：{len(replaced)} 個字形")
print(f"跳過：{len(skipped)} 個字形")
for cp, reason in skipped:
    print(f"  U+{cp:04X} {chr(cp)} - {reason}")
```

### Phase 5：驗證替換結果

```python
from fontTools.ttLib import TTFont

def verify_replacement(original_path, modified_path, codepoints):
    """比對替換前後的字形寬度與輪廓，確認替換確實生效。"""
    orig = TTFont(original_path)
    mod = TTFont(modified_path)

    orig_cmap = orig.getBestCmap()
    mod_cmap = mod.getBestCmap()

    print(f"{'Unicode':<10} {'Char':<4} {'原始寬度':<10} {'替換後寬度':<10} {'變更'}")
    print("-" * 50)
    for cp in codepoints:
        gname_orig = orig_cmap.get(cp)
        gname_mod = mod_cmap.get(cp)
        if gname_orig and gname_mod:
            w_orig = orig["hmtx"][gname_orig][0]
            w_mod = mod["hmtx"][gname_mod][0]
            changed = "✓ 已變更" if w_orig != w_mod else "— 相同"
            print(f"U+{cp:04X}    {chr(cp):<4} {w_orig:<10} {w_mod:<10} {changed}")

    orig.close()
    mod.close()

verify_replacement("BIZUDMincho-Regular.ttf", "BIZUDMincho-TWPunct.ttf", all_targets)
```

### Phase 6：視覺驗證

產出測試 HTML，以瀏覽器渲染替換後的字體，逐一檢視標點是否正確置中。

```python
test_html = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<style>
@font-face {
    font-family: 'BIZ-TW';
    src: url('BIZUDMincho-TWPunct.ttf');
}
@font-face {
    font-family: 'BIZ-Original';
    src: url('BIZUDMincho-Regular.ttf');
}
body { font-size: 24px; line-height: 2; }
.tw { font-family: 'BIZ-TW'; }
.jp { font-family: 'BIZ-Original'; color: #999; }
td { padding: 4px 12px; border: 1px solid #ccc; }
</style>
</head>
<body>
<h2>繁中標點替換驗證</h2>
<table>
<tr><th>Unicode</th><th>字元</th><th>替換後 (BIZ-TW)</th><th>原始 (BIZ-JP)</th><th>GYM-R 參照</th></tr>
"""

PUNCT_CHARS = [
    (0x3001, "、", "頓號"), (0x3002, "。", "句號"),
    (0xFF0C, "，", "逗號"), (0xFF01, "！", "驚嘆號"),
    (0xFF1F, "？", "問號"), (0xFF1A, "：", "冒號"),
    (0xFF1B, "；", "分號"), (0x2014, "—", "破折號"),
    (0x2026, "…", "刪節號"), (0x00B7, "·", "間隔號"),
    (0xFF08, "（", "左括號"), (0xFF09, "）", "右括號"),
    (0x300C, "「", "左引號"), (0x300D, "」", "右引號"),
    (0x300E, "『", "左雙引號"), (0x300F, "』", "右雙引號"),
    (0x300A, "《", "左書名號"), (0x300B, "》", "右書名號"),
    (0x3010, "【", "左隅括號"), (0x3011, "】", "右隅括號"),
]

for cp, char, name in PUNCT_CHARS:
    test_str = f"測{char}試"
    test_html += f'<tr><td>U+{cp:04X}</td><td>{name}</td>'
    test_html += f'<td class="tw">{test_str}</td>'
    test_html += f'<td class="jp">{test_str}</td>'
    test_html += f'<td style="font-family:GenYoMinTW-R">{test_str}</td></tr>\n'

test_html += "</table></body></html>"

with open("punct_verify.html", "w", encoding="utf-8") as f:
    f.write(test_html)

print("已產出 punct_verify.html，請以瀏覽器開啟驗證。")
```

---

## 5. CJK 直排標點補充區段（U+FE30–U+FE4F）

若字體需支援直排（vertical layout），以下 CJK Compatibility Forms 區段也必須一併處理：

| Unicode | 字元 | 名稱 |
|---------|------|------|
| U+FE30 | ︰ | Presentation Form for Vertical Two Dot Leader |
| U+FE31 | ︱ | Presentation Form for Vertical Em Dash |
| U+FE32 | ︲ | Presentation Form for Vertical En Dash |
| U+FE33 | ︳ | Presentation Form for Vertical Low Line |
| U+FE35 | ︵ | Presentation Form for Vertical Left Parenthesis |
| U+FE36 | ︶ | Presentation Form for Vertical Right Parenthesis |
| U+FE37 | ︷ | Presentation Form for Vertical Left Curly Bracket |
| U+FE38 | ︸ | Presentation Form for Vertical Right Curly Bracket |
| U+FE39 | ︹ | Presentation Form for Vertical Left Tortoise Shell Bracket |
| U+FE3A | ︺ | Presentation Form for Vertical Right Tortoise Shell Bracket |
| U+FE3B | ︻ | Presentation Form for Vertical Left Black Lenticular Bracket |
| U+FE3C | ︼ | Presentation Form for Vertical Right Black Lenticular Bracket |
| U+FE3D | ︽ | Presentation Form for Vertical Left Double Angle Bracket |
| U+FE3E | ︾ | Presentation Form for Vertical Right Double Angle Bracket |
| U+FE3F | ︿ | Presentation Form for Vertical Left Angle Bracket |
| U+FE40 | ﹀ | Presentation Form for Vertical Right Angle Bracket |
| U+FE41 | ﹁ | Presentation Form for Vertical Left Corner Bracket |
| U+FE42 | ﹂ | Presentation Form for Vertical Right Corner Bracket |
| U+FE43 | ﹃ | Presentation Form for Vertical Left White Corner Bracket |
| U+FE44 | ﹄ | Presentation Form for Vertical Right White Corner Bracket |
| U+FE4F | ﹏ | Wavy Low Line |

將這些 codepoints 加入 Phase 3/4 的清單即可一併處理。

---

## 6. 注意事項與風險

**字形名稱映射：** BIZ 與 GYM-R 的 glyph name 可能不同（如 `uni3001` vs `comma.ideo`）。Phase 4 的腳本透過 cmap 查表取得對應 glyph name，不依賴名稱直接對應，因此不受此影響。

**輪廓格式：** BIZ UD Mincho（Google Fonts 版）為 TrueType 輪廓（glyf 表）；源樣明體系列可能為 CFF 輪廓（CFF/CFF2 表）。若兩者輪廓格式不同，無法直接複製 glyf 資料，需透過 Pen 介面轉錄或事先將 GYM-R 轉為 TrueType。**這是最可能的阻塞點，務必在 Phase 2 確認。**

```python
# 檢查輪廓格式
for path in ["BIZUDMincho-Regular.ttf", "GenYoMinTW-R.ttf"]:
    font = TTFont(path)
    if "glyf" in font:
        print(f"{path}: TrueType outlines (glyf)")
    elif "CFF " in font:
        print(f"{path}: CFF outlines")
    elif "CFF2" in font:
        print(f"{path}: CFF2 outlines")
    font.close()
```

若格式不同的處理方案：

1. **方案 A（推薦）：** 使用 `fontTools.pens.cu2quPen` 將 CFF 曲線（cubic Bézier）轉為 TrueType 曲線（quadratic Bézier），再寫入 glyf 表。
2. **方案 B：** 預先將 GYM-R 整體轉為 TrueType 格式（`fontTools.ttLib` 搭配 `cu2qu`），再從轉換後的檔案提取字形。

**GSUB/GPOS 特徵：** 若 BIZ 原有針對標點的 OpenType 特徵（如 `halt`、`vhal`、`palt`、`vpal`），替換字形後這些特徵的位移值可能不再正確。需在 Phase 5 額外檢查這些 feature 是否影響替換後的標點定位。

**授權：** BIZ UD Mincho 採 OFL 1.1 授權；源樣明體月版同樣為 OFL。兩者均允許修改與衍生，但衍生字體不得使用原始保留名稱（Reserved Font Name）。確認兩份 OFL 的 RFN 條款後再命名。

---

## 7. 執行摘要（Agent Checklist）

- [ ] Phase 1: 確認兩個字體檔案存在且可讀取
- [ ] Phase 2: 執行 UPM / metrics / 輪廓格式驗證，記錄結果
- [ ] Phase 2b: 若輪廓格式不同，先執行 CFF → TrueType 轉換
- [ ] Phase 3: 執行字形存在性檢查，產出可替換清單
- [ ] Phase 4: 執行字形替換（先必要 → 建議 → 選用）
- [ ] Phase 5: 執行數值驗證（寬度比對）
- [ ] Phase 6: 產出視覺驗證 HTML，人工確認標點置中
- [ ] 檢查 GSUB/GPOS 特徵是否需要調整
- [ ] 確認 OFL 授權與命名合規
