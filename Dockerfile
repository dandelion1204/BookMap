# 使用官方 Python 基底
FROM python:3.11-slim

# 設定容器內的工作目錄
WORKDIR /app

# 先把 requirements.txt 複製進容器
COPY requirements.txt .

# 安裝 Python 套件
RUN pip install --no-cache-dir -r requirements.txt

# 再把其他程式全部複製進容器
COPY . .

# ... 在 COPY . . 之後，CMD 之前加入
# 宣告此容器預期運行的埠口
EXPOSE 8000

# 啟動 Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
