FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要目录
RUN mkdir -p /app/data /app/temp_media /app/data/backups

# 安装cron任务
RUN echo "0 * * * * find /app/temp_media -type f -mmin +1440 -delete >> /var/log/cron.log 2>&1" >> /etc/crontab
RUN echo "0 3 * * * cp /app/data/analysis_records.db /app/data/backups/db_$(date +\%Y\%m\%d).sqlite3 && find /app/data/backups -type f -mtime +7 -delete >> /var/log/cron.log 2>&1" >> /etc/crontab

# 启动服务
CMD ["sh", "-c", "cron && uvicorn main:app --host 0.0.0.0 --port 8000"]
