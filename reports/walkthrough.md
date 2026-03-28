# 字型合併與盤點成果總結

在此次任務中，我們完成了「Source Serif 4 與 BIZ UDPMincho 的字型合併」，並進行了「中文字元缺字盤點與覆蓋率比較」。以下是相關的實作細節與產出結果。

## 1. Source Serif 4 與 BIZ UDPMincho 字型合併

為了解決西文字型與中文字型放在同一檔案中時常見的比例不協調問題，我們提取了字型的 Font Metrics (度量數據) 進行精確對齊。

- **參數計算與對齊基準**：
  - `BIZUDPMincho-Regular`：UPM=2048，CapHeight=1567
  - `SourceSerif4_18pt-Regular`：UPM=1000，CapHeight=670
  - 為使視覺得以統一，我們計算出縮放係數 `1567 / 670 ≈ 2.3388`。
  - 將 Source Serif 4 的基本拉丁字母、延伸區段（ASCII Punctuation, Latin-1, Extended-A/B, Greek, Cyrillic 等）拷貝後，連同向量圖形 (Outlines) 與水平字寬 (Advance Widths) 皆以此比例放大。以確保西文大寫高度能準確對齊中文方框。
  - 刻意排除 General Punctuation 區塊（例如 U+2014, U+2026 等），以防破壞原本 BIZ UDPMincho 中針對 CJK 優化的破折號、刪節號與括號呈現。

- **成功產出的字型檔案** (存放於專案根目錄)：
  1. `BIZUDPMincho-SourceSerifMix-Regular.ttf`
  2. `BIZUDPMincho-SourceSerifMix-Bold.ttf`

## 2. BIZ UD Mincho 的缺字盤點

透過 `jf 7000 當務字集` 為標準對 `BIZUDPMincho-Regular.ttf` 的收錄字元進行覆蓋率檢查，確認此日本字型在日常繁體中文應用上的缺口。

- **盤點結果**：
  - 在 jf 7000 收錄的常用字集中，共發現 **85** 個 BIZ UD Mincho 缺漏的字元。
  - 缺字清單包含許多台灣常見用字與方言字，例如：「佢、侷、傌、吔、囝、囧、姵、屘、廍、搵、摃、爌、筊、粄、糬、趖」等。
  - 詳細清單已輸出至：[biz_ud_missing_chars.txt](file:///d:/OneDrive/project/UDminchoModified/reports/biz_ud_missing_chars.txt)

## 3. KlarMinTC v9 與 GenKiMin2TW-R 差異比較

在此項目中，我們比對了目前已修復到 v9 版本的 `KlarMinTC` 與作為參考的 `GenKiMin2TW-R`。

- **整體收錄數量差異**：
  - `KlarMinTC v9`：16,770 個對應字元
  - `GenKiMin2TW-R`：35,349 個對應字元
- **GenKiMin 獨有字元 (缺漏於 KlarMin)**：
  - 共計 **19,041** 字元。主要差異都集中在大型擴展字集，如：CJK Unified Ideographs (7513字)、CJK Ext A (6318字)、Hangul Syllables 韓文 (2350字) 及 CJK Ext B (1790字) 等。
- **KlarMin 獨有字元 (缺漏於 GenKiMin)**：
  - 共計 **462** 字元。由於 KlarMinTC 合併過 Merriweather 西文，因此多出了不少拉丁字母擴展區（Latin Extended-A 帶有各種注音符號的字母 Ą, Ć, Ė... 等）。
- 完整比較結果已輸出至：[klarmin_vs_genki_diff.txt](file:///d:/OneDrive/project/UDminchoModified/reports/klarmin_vs_genki_diff.txt)

## 下一步建議

如果您打算解決 BIZ UDPMincho 的中文缺字問題，我們可以：
- 使用相同的方式，從 `GenKiMin2TW-R.otf` 將上述盤點出的 **85** 個 jf 7000 常用字（加上其他可能需要的標點）複製並縮放（1000 UPM 轉換至 2048 UPM 約放大 `2.048` 倍）合成進 `BIZUDPMincho` 中。

## 附註：視覺排版測試網頁

為方便實時測試中西文夾雜，我們已在專案根目錄中產生了 `test_font.html`。
您可以直接在瀏覽器雙擊打開此檔案：
- 內含：中西文字、粗斜體、數字、全半形標點符號。
- 對照組：我們將預設剛產生的 `BIZUDPMincho-SourceSerifMix` 作為 Target，並載入了 `Noto Serif TC`（思源宋體）與 `Noto Sans TC`（思源黑體）供視覺比對。
