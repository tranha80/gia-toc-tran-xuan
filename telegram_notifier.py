"""
HỆ THỐNG TỰ ĐỘNG THÔNG BÁO GIA TỘC TRẦN XUÂN QUA TELEGRAM
- Báo trước 1 ngày: Ngày giỗ các cụ/ông/bà (Âm lịch)
- Báo trước 1 ngày: Ngày sinh nhật con cháu còn sống (Dương lịch)
- Sử dụng chuyển đổi Âm - Dương chuẩn xác
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

try:
    from lunardate import LunarDate
except ImportError:
    LunarDate = None

CAN = ["Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]
CHI = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]

def get_can_chi_year(yy):
    can = CAN[(yy - 4) % 10]
    chi = CHI[(yy - 4) % 12]
    return f"{can} {chi}"

def get_lunar_date(dt):
    if LunarDate:
        ld = LunarDate.from_solar_date(dt.year, dt.month, dt.day)
        return ld.day, ld.month, ld.year, get_can_chi_year(ld.year)
    return dt.day, dt.month, dt.year, get_can_chi_year(dt.year)

# ==============================================================================
# 2. CẤU HÌNH VÀ GỬI TIN NHẮN TELEGRAM
# ==============================================================================
CONFIG_FILE = r"d:\Gia pha\telegram_config.json"
DATABASE_FILE = r"d:\Gia pha\gia_toc_tran_xuan.json"

DEFAULT_CONFIG = {
    "bot_token": "YOUR_BOT_TOKEN_HERE",
    "chat_id": "YOUR_CHAT_ID_HERE",
    "remind_days_before": 1,
    "notify_time": "07:00",
    "enabled": True,
    "huong_dan": "Để lấy bot_token, chat với @BotFather tạo bot. Để lấy chat_id, thêm bot vào nhóm và chat với @userinfobot hoặc @getidsbot."
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CONFIG

def send_telegram_message(bot_token, chat_id, message_html):
    if not bot_token or bot_token == "YOUR_BOT_TOKEN_HERE" or not chat_id or chat_id == "YOUR_CHAT_ID_HERE":
        print("[LƯU Ý] Chưa cấu hình Telegram Bot Token hoặc Chat ID hợp lệ trong file telegram_config.json")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[LỖI GỬI TELEGRAM]: {e}")
        return False

# ==============================================================================
# 3. LOGIC KIỂM TRA SỰ KIỆN TRƯỚC 1 NGÀY (NGÀY GIỖ & SINH NHẬT)
# ==============================================================================
def check_events_and_notify(target_date=None, force_send=False):
    cfg = load_config()
    days_before = cfg.get("remind_days_before", 1)

    now = datetime.now() if target_date is None else target_date
    tomorrow = now + timedelta(days=days_before)

    # Ngày mai theo Dương lịch
    d_duong, m_duong, y_duong = tomorrow.day, tomorrow.month, tomorrow.year

    # Ngày mai theo Âm lịch
    d_am, m_am, y_am, can_chi_am = get_lunar_date(tomorrow)

    print(f"============================================================")
    print(f"KIỂM TRA SỰ KIỆN GIA TỘC TRẦN XUÂN TRƯỚC {days_before} NGÀY")
    print(f"- Hôm nay: {now.strftime('%d/%m/%Y')}")
    print(f"- Ngày cần nhắc ({days_before} ngày tới): {tomorrow.strftime('%d/%m/%Y')} (Dương lịch)")
    print(f"- Tức ngày Âm lịch: Ngày {d_am:02d} tháng {m_am:02d} năm {can_chi_am}")
    print(f"============================================================")

    if not os.path.exists(DATABASE_FILE):
        print(f"Không tìm thấy CSDL gia tộc: {DATABASE_FILE}")
        return

    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        clan_data = json.load(f)

    members = clan_data.get("thanh_vien", [])

    death_events = []
    birthday_events = []

    for m in members:
        is_deceased = bool(m.get("mat_duong") or m.get("mat_am") or "Đã Mất" in m.get("ghi_chu", "") or "chi mộ" in m.get("phan_mo", ""))

        if is_deceased:
            # Kiểm tra ngày giỗ Âm lịch
            mat_am_str = m.get("mat_am", "")
            match_am = False
            if mat_am_str:
                parts = mat_am_str.split()[0].split('/')
                if len(parts) >= 2:
                    try:
                        p_day = int(parts[0])
                        p_mon = int(parts[1])
                        if p_day == d_am and p_mon == m_am:
                            match_am = True
                    except ValueError:
                        pass
            if match_am:
                death_events.append(m)
        else:
            # Kiểm tra sinh nhật Dương lịch của người còn sống
            sinh_str = m.get("sinh", "")
            if sinh_str and len(sinh_str) >= 5 and '/' in sinh_str:
                parts = sinh_str.split()[0].split('/')
                if len(parts) >= 2:
                    try:
                        b_day = int(parts[0])
                        b_mon = int(parts[1])
                        b_year = int(parts[2]) if len(parts) >= 3 else 0
                        if b_day == d_duong and b_mon == m_duong:
                            age = (y_duong - b_year) if b_year > 0 else None
                            m_copy = dict(m)
                            m_copy["tuoi_mung"] = age
                            birthday_events.append(m_copy)
                    except ValueError:
                        pass

    # TẠO NỘI DUNG THÔNG BÁO TELEGRAM
    if not death_events and not birthday_events and not force_send:
        print(f"Không có sự kiện ngày giỗ hoặc sinh nhật nào vào ngày mai ({tomorrow.strftime('%d/%m/%Y')}).")
        return

    lines = []
    lines.append("🌿 <b>THÔNG BÁO TỪ GIA TỘC TRẦN XUÂN (CHI 3 CÀNH 1)</b> 🌿")
    lines.append(f"<i>Kính gửi con cháu dòng họ tại Đông Vinh, TP. Thanh Hóa và khắp mọi miền.</i>")
    lines.append("")
    lines.append(f"⏰ <b>BÁO TRƯỚC 1 NGÀY: SỰ KIỆN NGÀY MAI ({tomorrow.strftime('%d/%m/%Y')})</b>")
    lines.append(f"📅 <i>Âm lịch: Ngày {d_am:02d} tháng {m_am:02d} năm {can_chi_am}</i>")
    lines.append("────────────────────────")

    # 1. Phần Ngày Giỗ (Âm Lịch)
    if death_events:
        lines.append("🕯️ <b>TƯỞNG NHỚ NGÀY GIỖ TIÊN TỔ (CÚNG TIÊN THƯỜNG / CHÍNH KỴ)</b>")
        for idx, de in enumerate(death_events, 1):
            lines.append(f"<b>{idx}. {de['ho_ten']}</b> ({de['vai_ve']})")
            lines.append(f"   • Ngày giỗ Âm lịch: <b>{de.get('mat_am', '')}</b>")
            if de.get('mat_duong'):
                lines.append(f"   • Ngày mất Dương lịch: {de['mat_duong']}")
            if de.get('huong_tho'):
                lines.append(f"   • Hưởng thọ: {de['huong_tho']} tuổi")
            if de.get('phan_mo'):
                lines.append(f"   • Phần mộ: {de['phan_mo']}")
            lines.append("   👉 <i>Kính xin con cháu sửa soạn hương hoa, lễ phẩm kính bái tổ tiên.</i>")
        lines.append("")

    # 2. Phần Sinh Nhật (Dương Lịch)
    if birthday_events:
        lines.append("🎉 <b>CHÚC MỪNG SINH NHẬT CON CHÁU TRONG GIA TỘC</b>")
        for idx, be in enumerate(birthday_events, 1):
            age_str = f" tròn <b>{be['tuoi_mung']} tuổi</b>" if be.get('tuoi_mung') else ""
            lines.append(f"<b>{idx}. {be['ho_ten']}</b> ({be['vai_ve']}){age_str}")
            lines.append(f"   • Ngày sinh: {be.get('sinh', '')}")
            if be.get('ghi_chu'):
                lines.append(f"   • Quan hệ: {be['ghi_chu']}")
            lines.append("   💐 <i>Kính chúc sức khỏe, an khang thịnh vượng, học tập tiến tới và thành đạt!</i>")
        lines.append("")

    if force_send and not death_events and not birthday_events:
        lines.append("ℹ️ <i>Hôm nay là bản tin thử nghiệm kết nối hệ thống Telegram Bot. Hệ thống đã kết nối thành công!</i>")

    lines.append("────────────────────────")
    lines.append("🏛️ <i>Tra cứu phả hệ online tại: https://donghotranxuan.akb.vn/</i>")

    message_html = "\n".join(lines)
    print("\n--- NỘI DUNG TIN NHẮN DỰ KIẾN ---")
    print(message_html.replace('<b>','').replace('</b>','').replace('<i>','').replace('</i>',''))
    print("--------------------------------\n")

    # Gửi tới Telegram
    bot_token = cfg.get("bot_token")
    chat_id = cfg.get("chat_id")
    if bot_token and bot_token != "YOUR_BOT_TOKEN_HERE" and chat_id and chat_id != "YOUR_CHAT_ID_HERE":
        success = send_telegram_message(bot_token, chat_id, message_html)
        if success:
            print("✅ Đã gửi thông báo Telegram thành công!")
        else:
            print("❌ Gửi thông báo Telegram thất bại. Vui lòng kiểm tra lại Bot Token và Chat ID.")
    else:
        print("[HƯỚNG DẪN KÍCH HOẠT TELEGRAM]")
        print("Để nhận thông báo trực tiếp qua Telegram, hãy mở file 'd:\\Gia pha\\telegram_config.json' và điền:")
        print("1. 'bot_token': Lấy từ @BotFather")
        print("2. 'chat_id': Chat ID của bạn hoặc của nhóm gia tộc họ Trần Xuân")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("[CHẾ ĐỘ KIỂM TRA THỬ NGHIỆM TELEGRAM]")
        check_events_and_notify(force_send=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "--sample-gio":
        print("[MÔ PHỎNG: THÔNG BÁO NGÀY GIỖ CỤ PHANG TRƯỚC 1 NGÀY]")
        # Cụ Phang giỗ 01/08 Âm lịch. Tìm ngày nào trong năm có ngày mai là 01/08 Âm lịch
        # Năm 2026: 01/08 Âm lịch rơi vào 11/09/2026 Dương lịch -> check ngày 10/09/2026
        check_events_and_notify(target_date=datetime(2026, 9, 10), force_send=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "--sample-sn":
        print("[MÔ PHỎNG: THÔNG BÁO SINH NHẬT CHÁU ĐỨC ANH TRƯỚC 1 NGÀY]")
        check_events_and_notify(target_date=datetime(2026, 11, 30), force_send=True)
    else:
        check_events_and_notify()
