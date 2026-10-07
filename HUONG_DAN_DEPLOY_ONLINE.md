# HƯỚNG DẪN DEPLOY WEB APP GIA TỘC TRẦN XUÂN LÊN ONLINE (INTERNET)

Dự án đã được đóng gói hoàn chỉnh gồm **Backend (FastAPI)**, **Frontend (Admin CRUD + Cây Phả Hệ)**, **Cơ sở dữ liệu (SQLite)**, **Tự động gửi Telegram**, cùng các tệp cấu hình triển khai chuẩn quốc tế:
- `Dockerfile` (Chạy trên mọi nền tảng đám mây và máy chủ Linux/Docker)
- `render.yaml` (Cấu hình tự động triển khai miễn phí trên Render.com)
- `requirements.txt` (Danh sách thư viện phụ thuộc)
- `start_online_tunnel.bat` (Công cụ phát trực tuyến tức thì qua Cloudflare Tunnel)

Dưới đây là 2 phương án đưa Web App lên Online tiện lợi nhất:

---

## ⚡ PHƯƠNG ÁN 1: ONLINE TỨC THÌ QUA CLOUDFLARE TUNNEL (KHÔNG CẦN TẠO TÀI KHOẢN, CHẠY NGAY SAU 3 GIÂY)

Phương án này biến máy tính hiện tại thành máy chủ trực tuyến, Cloudflare sẽ cấp một đường link **HTTPS** bảo mật toàn cầu miễn phí 100%.

### Cách thực hiện:
1. Mở thư mục `d:\Gia pha`.
2. Nhấp đúp chuột vào tệp: **`start_online_tunnel.bat`**.
3. Cửa sổ dòng lệnh sẽ tự động khởi động Backend và kết nối Cloudflare.
4. Sau 3 đến 5 giây, màn hình sẽ hiển thị đường link dạng:
   ```text
   https://xxxx-xxxx-xxxx.trycloudflare.com
   ```
5. **Chia sẻ đường link này qua Zalo / Facebook / Tin nhắn** cho con cháu trong gia tộc. Bất kỳ ai ở Hà Nội, TP.HCM hay nước ngoài đều có thể mở trên điện thoại hoặc máy tính để tra cứu cây phả hệ và ngày giỗ ngay lập tức!
> *Lưu ý:* Giữ cửa sổ `start_online_tunnel.bat` mở trong thời gian muốn con cháu truy cập. Khi tắt cửa sổ, phiên online sẽ kết thúc.

---

## 🌐 PHƯƠNG ÁN 2: DEPLOY LÊN ĐÁM MÂY VĨNH VIỄN 24/7 (MIỄN PHÍ TRÊN RENDER.COM)

Phương án này giúp Web App chạy vĩnh viễn trên máy chủ đám mây, **kể cả khi bạn tắt máy tính** thì mọi người vẫn vào được 24/7 tại địa chỉ cố định (ví dụ: `https://gia-toc-tran-xuan.onrender.com`).

### Bước 1: Đẩy mã nguồn lên GitHub (Đã chuẩn bị sẵn Git repo)
1. Mở trang [github.com](https://github.com) và tạo một Repository mới (ví dụ đặt tên: `gia-toc-tran-xuan`, chọn chế độ Private hoặc Public tùy ý).
2. Mở Terminal / PowerShell tại thư mục `d:\Gia pha` và chạy:
   ```powershell
   git remote add origin https://github.com/TÊN_GITHUB_CỦA_BẠN/gia-toc-tran-xuan.git
   git branch -M main
   git push -u origin main
   ```

### Bước 2: Triển khai 1-Click trên Render.com
1. Truy cập [render.com](https://render.com/) và đăng ký/đăng nhập bằng tài khoản GitHub.
2. Bấm nút **New +** $\rightarrow$ chọn **Web Service**.
3. Chọn kho mã nguồn `gia-toc-tran-xuan` vừa đẩy lên.
4. Render sẽ tự động nhận diện cấu hình:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free ($0/tháng)
5. Bấm **Create Web Service**.
6. Sau khoảng 2-3 phút, Render sẽ cấp cho bạn một đường link HTTPS chính thức dạng:
   👉 **`https://gia-toc-tran-xuan.onrender.com`**

---

## 🐳 PHƯƠNG ÁN 3: DEPLOY BẰNG DOCKER (CHO MÁY CHỦ RIÊNG / VPS LINUX)

Nếu bạn có máy chủ riêng (VPS Ubuntu/CentOS):
```bash
# Build Docker image
docker build -t gia-toc-tran-xuan .

# Chạy container port 8000
docker run -d -p 8000:8000 --name giapha gia-toc-tran-xuan
```

---

## 🔐 BẢO MẬT & QUẢN TRỊ KHI ONLINE
- Người ngoài và con cháu truy cập vào chỉ có thể **Xem Cây Phả Hệ, Lịch Ngày Giỗ, Lăng Mộ**.
- Muốn Thêm / Sửa / Xóa thành viên hoặc cài đặt Telegram Bot, người dùng bắt buộc phải bấm **🔐 Đăng Nhập Admin** và nhập đúng **Mã PIN: `123456`**.
- Mọi thao tác thêm sửa xóa sẽ được ghi nhận và lưu trữ tức thời vào CSDL.
