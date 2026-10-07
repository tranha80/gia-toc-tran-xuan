# HỆ THỐNG SỐ HÓA GIA TỘC TRẦN XUÂN (CHI 3 CÀNH 1)
**Địa bàn:** Làng Đa Sĩ (Sài Thôn), xã Đông Vinh, TP. Thanh Hóa, tỉnh Thanh Hóa  
**Thời gian số hóa chuẩn hóa:** Tháng 10/2026

---

## 📌 1. Danh Mục Các Tệp Dữ Liệu Số Hóa

| Tên Tệp | Định Dạng | Mô Tả Chức Năng |
|:---|:---:|:---|
| **[index.html](file:///d:/Gia%20pha/index.html)** | Web App (HTML5/CSS3/JS) | Cổng thông tin phả hệ tương tác Offline: cây phả hệ 7 đời, danh sách 54 thành viên, lịch ngày giỗ, quy hoạch lăng mộ, thông báo Telegram, văn bia Hán Nôm. |
| **[telegram_notifier.py](file:///d:/Gia%20pha/telegram_notifier.py)** | Python Script | Bot tự động kiểm tra và gửi tin nhắn Telegram **trước 1 ngày**: ngày giỗ tiên tổ (Âm lịch) & sinh nhật con cháu còn sống (Dương lịch). |
| **[telegram_config.json](file:///d:/Gia%20pha/telegram_config.json)** | Tệp Cấu Hình JSON | Lưu Bot Token và Chat ID nhận tin nhắn của dòng họ. |
| **[Gia_Pha_Tran_Xuan_So_Hoa_Chuan.xlsx](file:///d:/Gia%20pha/Gia_Pha_Tran_Xuan_So_Hoa_Chuan.xlsx)** | Microsoft Excel (.xlsx) | 4 Sheet in ấn chuẩn: Danh sách thành viên; Lịch ngày giỗ; Quy hoạch lăng mộ; Văn bia Viện Hán Nôm. |
| **[gia_toc_tran_xuan.db](file:///d:/Gia%20pha/gia_toc_tran_xuan.db)** | CSDL SQLite (.db) | Cơ sở dữ liệu quan hệ chuẩn 4 bảng (`thanh_vien`, `hon_nhan`, `quan_he_cha_con`, `ngay_gio`). |
| **[gia_toc_tran_xuan.json](file:///d:/Gia%20pha/gia_toc_tran_xuan.json)** | Dữ liệu mở JSON (.json) | Dữ liệu cấu trúc mở phục vụ đồng bộ website [donghotranxuan.akb.vn](https://donghotranxuan.akb.vn/). |

---

## 🏛️ 2. Quy Hoạch & Kế Hoạch Xây Lăng Mộ Gia Tộc

### A. Kế hoạch tài chính & Tiến độ:
- **Tổng dự toán:** **235.000.000 VNĐ** (235 triệu đồng).
- **Tiến độ thi công & nghi lễ:**
  - *Ngày 04/10 (Âm lịch):* Đưa mộ các cụ về lăng gia tộc tập trung.
  - *Ngày 20/10 (Âm lịch):* Cải táng, sang mộ cho Ông Cố (Cụ Trần Xuân Phúc Phang).
- **Trọng trách 7 Nam Đinh trên 18 tuổi:**
  1. **Trần Xuân Hạnh** (1957)
  2. **Trần Xuân Tám** (1972)
  3. **Trần Xuân Hải** (1979)
  4. **Trần Xuân Tùng** (Chung; 1979)
  5. **Trần Xuân Hà** (1981)
  6. **Trần Xuân Huấn** (1983 - Thủ quỹ tiếp nhận)
  7. **Trần Xuân Đức** (1991)
- **Tài khoản tiếp nhận đóng góp:**
  - STK: `19131 97826 9999` (Ngân hàng Techcombank - Chi nhánh Thanh Hóa)
  - Chủ tài khoản: **Trần Xuân Huấn**

### B. Tiêu chuẩn kích thước phong thủy Thước Lỗ Ban (38.8 cm - Âm Phần):
- **Mộ đơn nhỏ:** 81 x 127 cm *(Tài Vượng - Tiến Bảo)*.
- **Mộ đơn vừa:** 89 x 133 cm *(Lục Hợp - Quý Tử)* hoặc 89 x 147 cm *(Thêm Đinh - Nhật Lộc)*.
- **Mộ trung / lớn:** 107 x 167 cm *(Quý Tử - Hưng Vượng)* hoặc 107 x 176 cm *(Phú Quý)*.
- **Mộ đôi cụ ông - cụ bà:** 147 x 167 cm hoặc 167 x 197 cm *(Hưng Vượng - Đăng Khoa)*.

---

## 🤖 3. Hướng Dẫn Kích Hoạt Bot Telegram Báo Giỗ & Sinh Nhật Trước 1 Ngày

### Bước 1: Tạo Bot & Lấy Chat ID
1. Mở ứng dụng Telegram, tìm kiếm **`@BotFather`**, bấm `Start` và gửi lệnh `/newbot`.
2. Đặt tên cho bot (ví dụ: `Gia Toc Tran Xuan Bot`) và username kết thúc bằng `bot`. Bạn sẽ nhận được chuỗi **Bot Token** dạng `123456789:ABCdefGHI...`.
3. Thêm bot vừa tạo vào Nhóm Gia Tộc trên Telegram (hoặc chat riêng với bot).
4. Mời bot **`@getidsbot`** vào nhóm để xem **Chat ID** của nhóm (dạng số âm `-100xxxxxxxxxx` hoặc số dương nếu chat cá nhân).

### Bước 2: Cập nhật tệp cấu hình
Mở tệp `d:\Gia pha\telegram_config.json` và thay đổi:
```json
{
  "bot_token": "ĐIỀN_TOKEN_TỪ_BOTFATHER",
  "chat_id": "ĐIỀN_CHAT_ID_TẠI_ĐÂY",
  "remind_days_before": 1,
  "notify_time": "07:00",
  "enabled": true
}
```

### Bước 3: Chạy kiểm tra hoặc lập lịch tự động
- Chạy thử nghiệm gửi tin ngay:
  ```bash
  python telegram_notifier.py --test
  ```
- Mô phỏng tin nhắn báo ngày giỗ trước 1 ngày:
  ```bash
  python telegram_notifier.py --sample-gio
  ```
- Mô phỏng tin nhắn báo sinh nhật con cháu trước 1 ngày:
  ```bash
  python telegram_notifier.py --sample-sn
  ```
- **Lập lịch Windows Task Scheduler:** Cài đặt chạy lệnh `python d:\Gia pha\telegram_notifier.py` vào lúc 07:00 sáng mỗi ngày.
