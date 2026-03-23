# 🚀 Web 工具開發百科：GEMS 知識庫 (2024版)

## 📌 技術選型
- **框架**: Streamlit (Python 網頁框架)
- **部署**: GitHub + Streamlit Cloud
- **數據**: Excel (openpyxl)

## 🛠️ 避坑金律 (必看)
1. **數據標準化**: 永遠在讀取 Excel 後使用 `df.columns = [str(c).strip().capitalize() for c in df.columns]` 以防大小寫報錯。
2. **狀態持久化**: 使用 `st.session_state` 儲存分數、進度與當前題目，避免頁面刷新後資料遺失。
3. **發音重複觸發**: 為 JavaScript 發音組件加上 `time.time()` 隨機 ID，否則重複點擊會因快取而失效。
4. **互動體驗**: 顯示正確答案後，應由使用者主動點擊「下一題」按鈕，而非使用自動計時器跳轉。

## 📋 部署 SOP
1. 準備 `app.py` 與 `requirements.txt`。
2. 上傳 GitHub 後，前往 Streamlit Cloud 進行 Deploy。
3. 手機端「加入主畫面」實現類 App 體驗。
