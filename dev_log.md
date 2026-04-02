# UDminchoModified 開發與現況日誌 (Dev Log)

> 本文件為系統自動盤點產出，為未來的開發者與 Agent 梳理目錄結構及最新開發脈絡。

## 專案概述 (Project Overview)

本專案致力於開發適合螢幕閱讀與電子書排版的繁體中文「宋體 / 明體」字型。專案經歷了兩個主要的開發路線：

1. **KlarMinTC 路線 (v1 - v9，目前已達穩定版)**：
   以 TRWUDMincho / KlarMinTC 為基底，融合 GenKiMin2TW (源泉圓體/明體) 的中式標點、以及 Merriweather 的西文標點及斜體。已完成行高修復與過大標點校正，產出 `v9-symbolfix` 最新版本。
2. **BIZ UDPMincho 路線 (最新的開發主軸)**：
   為了尋找更好的字腔空間與中西文協調感，目前轉向以日本 Morisawa 公司開源的 `BIZ UDPMincho` (UD明朝) 作為漢字基底，並混排 `Source Serif 4` 作為西文配套。處理了兩者之間極大的度量與比例落差。

---

## 最新開發進度 (2026-04-02 更新)

- **資料夾規範化**：根目錄已完成清理，僅保留成品 `.ttf` 與說明文件。其餘腳本、報告、備份已分類歸檔。
- **CJK 審閱台 (Iansui/芫荽 範圍擴展)**：
  - 審閱範圍從單純的 01-03 擴展至 **01-06 (包含符號、日文、粵語常用字)**。
  - 核心審閱清單已增加至 **8,160 字**，涵蓋注音、方音符號、KK/DJ 音標、漢語拼音等排版必備字元。
  - 審閱台新增 **「💾 存檔」與「📂 讀檔」** 功能，支援跨電腦進度轉發與「覆蓋/合併」模式。
  - **總覽頁功能優化**：在「總覽對照表」新增與側邊欄同步的篩選按鈕列 (Chip Row)，支援所有篩選模式。
  - **UI 強化與標籤一致化**：
    - 新增 BIZ 收錄狀態標籤（已有/未收錄）。
    - 統一檢字頁面標籤為 `BIZUDMincho` 與 `KlarMinTC`，優化對照呈現。
    - 優化決策流程（捨棄/修改/合併/清除）。

---

## 目錄結構與現況庫存 (Directory Structure)

- **`/` (Root)** - **最新成品與專案說明區域**
  - `BIZUDPMincho-SourceSerifMix-Regular.ttf` & `-Bold.ttf`: 【測試中】目前 BIZ UDP 路線的混排測試版。
  - `KlarMinTC-Regular-GenKiMerriMix-PunctFix-v9-symbolfix.ttf`: 【已完成】KlarMin 路線的最新穩定字型。
  - `README.md`: 給使用者看的快速導引。
  - `dev_log.md`: 本檔案，記錄開發脈絡與資料夾原則。
  - `CLAUDE.md`: AI 助手的工作守則與專案指南。
  
- **`/tools/`** - **工具腳本與 Web Reviewer**
  - `cjk_review_app.html`: 核心審閱工具，支援 8,000+ 字的高效總覽與決策。
  - `export_essential_rtf_cjk.py`: 從 RTF 提取字元並生成審閱數據檔。
  - `merge_approved_cjk.py`: 讀取審閱結果 JSON 並執行真正的字體合併。
  - `merge_sourceserif.py` & `merge_bizud_tw_glyphs.py`: 核心建置腳本。

- **`/reports/`** - **分析報告與測試頁面**
  - `missing_chars.json` & `missing_chars_data.js`: 審閱台的數據來源。
  - `font_review_report.html`: 三大字型比對報告（已從 root 移至此處）。
  - `test_font.html`: 排版測試頁。

- **`/referenceFont/`** - **基底字型庫**
  - `BIZUD*`, `GenKiMin*`, `GenYoMin*`, `Merriweather`, `Source_Serif_4`。

- **`/essentialFontTW/`** - **字集原始資料**
  - `01~06*.rtf` 當務字集原始檔、精選 XLSX。

- **`/archive/`** - **歷程備份**
  - 舊版字型、SFD 專案檔、臨時測試文件。

---

## 發展狀態與待辦建議 (Future Roadmap)

1. **執行全面審閱**：
   使用 `tools/cjk_review_app.html` 針對 8,160 字進行「合併/捨棄」判斷，特別注意標點符號與 Bopomofo 的視覺表現。
2. **應用決策**：
   審閱完成後，執行 `tools/merge_approved_cjk.py`產出最終版 BIZ UDPMincho (Trad. Chinese Fix)。
3. **字體度量微調**：
   針對 BIZ 與 Source Serif 4 的基線 (Baseline) 與字高比例進行最終確認，確保長篇閱讀的舒適度。
