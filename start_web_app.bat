@echo off
chcp 65001 >nul
title Gia Tộc Trần Xuân - Cổng Phả Hệ & Web App Quản Lý
echo ============================================================
echo   GIA TỘC TRẦN XUÂN (CHI 3 CÀNH 1 - ĐÔNG VINH, TP. THANH HÓA)
echo   KHỞI ĐỘNG MÁY CHỦ WEB APP & CƠ SỞ DỮ LIỆU
echo ============================================================
echo.
echo Đang khởi động Backend FastAPI & Trình quét ngầm Telegram...
cd /d "d:\Gia pha"

start "" http://127.0.0.1:8000/

"C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
