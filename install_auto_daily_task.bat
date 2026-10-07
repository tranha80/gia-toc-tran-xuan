@echo off
chcp 65001 >nul
title Cài Đặt Tự Động Gửi Thông Báo Gia Tộc Trần Xuân
echo ============================================================
echo   GIA TỘC TRẦN XUÂN - CÀI ĐẶT TỰ ĐỘNG THÔNG BÁO TELEGRAM
echo ============================================================
echo.
echo Đang đăng ký tác vụ tự động vào Windows Task Scheduler...
echo Thời gian gửi tự động: 07:00 sáng mỗi ngày.
echo.

schtasks /create /tn "GiaTocTranXuanNotify" /tr "\"C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe\" \"d:\Gia pha\telegram_notifier.py\"" /sc daily /st 07:00 /f

if %ERRORLEVEL% equ 0 (
    echo.
    echo ============================================================
    echo [THÀNH CÔNG] Đã đăng ký tác vụ tự động thành công!
    echo Từ nay mỗi ngày vào lúc 07:00 sáng, Windows sẽ tự động chạy
    echo kiểm tra và gửi tin nhắn Telegram báo Ngày Giỗ & Sinh Nhật
    echo trước 1 ngày mà KHÔNG CẦN BẠN PHẢI MỞ GIAO DIỆN HAY CHẠY PYTHON!
    echo ============================================================
) else (
    echo.
    echo [LƯU Ý] Nếu gặp lỗi quyền hạn, vui lòng bấm chuột phải vào file này
    echo và chọn 'Run as administrator' (Chạy dưới quyền quản trị viên).
)

echo.
pause
