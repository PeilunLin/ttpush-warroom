# 1. 採用官方輕量級 Python 3.10 作為系統核心地基
FROM python:3.10-slim

# 2. 設定 Linux 系統內部的專案工作資料夾路徑
WORKDIR /app

# 3. 將 Codespaces 雲端上現有的所有核心檔案複製進虛擬電腦中
COPY app.py style.css metrics_history.json ./

# 4. 執行 pip 迴圈指令，無痛安裝戰情室前台與 Pandas 自動化清洗引擎
RUN pip install --no-cache-dir streamlit pandas

# 5. 開放 8501 網頁連接埠，供對外網址順暢串接
EXPOSE 8501

# 6. 設定容器啟動時的指令：關閉 CORS 安全鎖與 XSRF 防護，防止 Codespaces 連線斷裂
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]