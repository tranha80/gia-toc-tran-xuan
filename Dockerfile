FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY app/ ./app/
COPY static/ ./static/
COPY gia_toc_tran_xuan.db ./gia_toc_tran_xuan.db
COPY gia_toc_tran_xuan.json ./gia_toc_tran_xuan.json
COPY Gia_Pha_Tran_Xuan_So_Hoa_Chuan.xlsx ./Gia_Pha_Tran_Xuan_So_Hoa_Chuan.xlsx
COPY telegram_config.json ./telegram_config.json

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
