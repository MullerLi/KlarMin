# CLAUDE.md - UDminchoModified 專案工作守則

本檔案記錄了 UDminchoModified 專案的開發規範、架構邏輯與常用工具，旨在讓 AI 助手（Claude/Gemini）能快速理解「我們是如何在這裡開發的」。

---

## 🌎 語言與回應規範

- **語言偏好**：請總是用 **繁體中文 (Traditional Chinese, zh-TW)** 與使用者對話並撰寫非程式碼文件。
- **紀錄習慣**：每次完成重大功能更新或資料庫整理後，必須更新 `dev_log.md`。

---

## 📂 專案資料夾結構 (嚴格遵守)

為保持專案整潔，請遵循以下歸檔原則：

- **`/` (Root)**: 僅存放最新成品字型 (`.ttf`)、`README.md`、`dev_log.md` 與 `CLAUDE.md`。
- **`/tools/`**: 所有 Python 自動化腳本、Web 審閱工具 (`cjk_review_app.html`)。
- **`/reports/`**: 分析報告、審閱用數據檔 (`missing_chars.json`, `.js`)、測試網頁。
- **`/referenceFont/`**: 原始開源字型庫 (BIZ, GenYo, Source Serif 4 等)。
- **`/essentialFontTW/`**: 字集定義 RTF 檔案與 XLSX 資料。
- **`/archive/`**: 舊版輸出、SFD 專案檔、臨時測試文件。

---

## 🛠️ 核心工作流與常用指令

本專案的核心工作是「針對 BIZ UDPMincho 的繁中優化」。

### 1. 準備審閱數據 (01-06 RTF 範圍)

從原始字集 RTF 中提取 Unicode 字元並與來源字型比對：

```powershell
python tools/export_essential_rtf_cjk.py
```

*產出路徑：`reports/missing_chars.json`, `reports/missing_chars_data.js`*

### 2. 啟動 Web 審閱台 (交互式決策)

啟動本機伺服器並使用瀏覽器進行逐字審閱或總覽對照：

```powershell
python -m http.server 8080
```

開啟：`http://localhost:8080/tools/cjk_review_app.html`

### 3. 套用合併決策 (字型生成)

讀取審閱結果 JSON 並執行真正的字體合併/替換：

```powershell
python tools/merge_approved_cjk.py
```

### 4. 基礎建置與覆蓋率分析

- 合併 Source Serif 4：`python tools/merge_sourceserif.py`
- 檢查 Coverage：`python tools/audit_font_coverage.py --target [filename] --report reports/[logname]`

---

## 📜 技術規範

- **字體處理**：使用 Python 的 `fontTools` 處理 OpenType 表格與 `fontforge` (Python 模組) 進行外框遷移與縮放。
- **代碼風格**：
  - Python: 遵循 PEP 8，使用顯式的變數命名。
  - Web: 審閱台工具使用 Vanilla JS 與 CSS，注重效能（在大數據網格渲染時須考慮 Pagination）。
- **常用字集**：以「當務字集 01-06」與「芫荽/Iansui」範圍為準（約 8,160 字）。

---

## ⚠️ 千萬不要踩的坑 (Traps)

- **嚴禁亂放檔案**：不可直接在根目錄產生臨時的 `.html` 或 `.txt`。
- **標籤名稱**：目前的優化應明確標註對照為 `BIZUDMincho` → `KlarMinTC`。
- **存讀檔**：在審閱台作業後，應主動提醒使用者使用 `💾 存檔` 功能匯出進度 .json，避免瀏覽器快取遺失。
- **路徑問題**：腳本內盡量使用 `Path(__file__).parent` 定位相對路徑，以防在不同目錄下執行報錯。
