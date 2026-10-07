@echo off
chcp 65001 >nul
title Gia Tộc Trần Xuân - Khởi Động Web Online Toàn Cầu
echo ============================================================
echo   GIA TỘC TRẦN XUÂN - ĐƯA WEB APP LÊN ONLINE TOÀN CẦU
echo   KẾT NỐI QUA CLOUDFLARE SECURE TUNNEL (HTTPS MIỄN PHÍ)
echo ============================================================
echo.
echo 1. Đang khởi động Backend FastAPI tại http://127.0.0.1:8000 ...
cd /d "d:\Gia pha"

start /b "" "C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 >nul 2>&1

timeout /t 2 /nobreak >nul

echo 2. Đang tạo đường dẫn HTTPS công khai toàn cầu qua Cloudflare...
echo.
echo ============================================================
echo   HỆ THỐNG ĐANG PHÁT ĐƯỜNG DẪN TRỰC TUYẾN...
echo   HÃY CHỜ 3-5 GIÂY ĐỂ XEM ĐƯỜNG LINK HTTPS BÊN DƯỚI.
echo   BẠN CÓ THỂ GỬI ĐƯỜNG LINK NÀY QUA ZALO CHO MỌI NGƯỜI VÀO XEM!
echo   (KHÔNG ĐƯỢC TẮT CỬA SỔ NÀY TRONG KHI ĐANG SỬ DỤNG ONLINE)
echo ============================================================
echo.

"C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:8000

pause
