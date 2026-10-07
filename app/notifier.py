import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
import urllib.request
import urllib.parse

try:
    from lunardate import LunarDate
except ImportError:
    LunarDate = None

CONFIG_FILE = r"d:\Gia pha\telegram_config.json"
DATABASE_FILE = r"d:\Gia pha\gia_toc_tran_xuan.json"

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

def load_config():
    default_config = {
        "bot_token": "",
        "chat_id": "",
        "remind_days_before": 1,
        "notify_time": "07:00",
        "enabled": True,
        "last_notified_date": ""
    }
    if not os.path.exists(CONFIG_FILE):
        return default_config
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
            return {**default_config, **cfg}
    except Exception:
        return default_config

def save_config(cfg):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def send_telegram_message(bot_token, chat_id, message_html):
    if not bot_token or not chat_id:
        return False, "Chưa điền Bot Token hoặc Chat ID."
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
            return True, "Gửi thành công!"
    except Exception as e:
        return False, str(e)

def get_events_for_date(target_date, members):
    d_duong, m_duong, y_duong = target_date.day, target_date.month, target_date.year
    d_am, m_am, y_am, can_chi_am = get_lunar_date(target_date)

    death_events = []
    birthday_events = []

    for m in members:
        is_deceased = bool(m.get("mat_duong") or m.get("mat_am") or "Đã Mất" in m.get("ghi_chu", "") or "chi mộ" in m.get("phan_mo", ""))

        if is_deceased:
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

    return {
        "target_date_solar": target_date.strftime("%d/%m/%Y"),
        "target_date_lunar": f"Ngày {d_am:02d} tháng {m_am:02d} ({can_chi_am})",
        "death_events": death_events,
        "birthday_events": birthday_events
    }

def format_telegram_message(ev_data, days_before=1):
    death_events = ev_data["death_events"]
    birthday_events = ev_data["birthday_events"]

    if not death_events and not birthday_events:
        return None

    lines = [
        "🌿 <b>THÔNG BÁO TỪ GIA TỘC TRẦN XUÂN (CHI 3 CÀNH 1)</b> 🌿",
        "<i>Kính gửi con cháu dòng họ tại Đông Vinh, TP. Thanh Hóa và khắp mọi miền.</i>",
        "",
        f"⏰ <b>BÁO TRƯỚC {days_before} NGÀY: SỰ KIỆN NGÀY MAI ({ev_data['target_date_solar']})</b>",
        f"📅 <i>Âm lịch: {ev_data['target_date_lunar']}</i>",
        "────────────────────────"
    ]

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

    lines.append("────────────────────────")
    lines.append("🏛️ <i>Tra cứu phả hệ online tại: https://donghotranxuan.akb.vn/</i>")
    return "\n".join(lines)

def trigger_notification_check(target_date=None, force=False):
    cfg = load_config()
    days_before = cfg.get("remind_days_before", 1)

    now = datetime.now() if target_date is None else target_date
    tomorrow = now + timedelta(days=days_before)

    if not os.path.exists(DATABASE_FILE):
        return False, "Không tìm thấy CSDL."

    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        clan_data = json.load(f)

    members = clan_data.get("thanh_vien", [])
    ev_data = get_events_for_date(tomorrow, members)
    msg = format_telegram_message(ev_data, days_before)

    if not msg:
        if force:
            msg = f"🌿 <b>GIA TỘC TRẦN XUÂN - TEST HỆ THỐNG</b> 🌿\n\nNgày mai ({tomorrow.strftime('%d/%m/%Y')}) không có ngày giỗ hoặc sinh nhật nào.\nKết nối Telegram hoạt động tốt!"
        else:
            return True, "Không có sự kiện ngày mai."

    bot_token = cfg.get("bot_token")
    chat_id = cfg.get("chat_id")
    ok, res = send_telegram_message(bot_token, chat_id, msg)
    if ok:
        cfg["last_notified_date"] = now.strftime("%Y-%m-%d")
        save_config(cfg)
    return ok, res

# ==============================================================================
# 4. BACKGROUND SCHEDULER DAEMON (TỰ ĐỘNG CHẠY NGẦM KHÔNG CẦN CHẠY TAY)
# ==============================================================================
_scheduler_thread = None
_scheduler_running = False

def _scheduler_loop():
    global _scheduler_running
    print("[TELEGRAM SCHEDULER] Tiến trình quét ngầm thông báo đã khởi động!")
    while _scheduler_running:
        try:
            cfg = load_config()
            if cfg.get("enabled", True):
                notify_time_str = cfg.get("notify_time", "07:00")
                now = datetime.now()
                current_hm = now.strftime("%H:%M")
                today_str = now.strftime("%Y-%m-%d")

                if current_hm == notify_time_str and cfg.get("last_notified_date") != today_str:
                    print(f"[TELEGRAM SCHEDULER] Đến giờ gửi tự động ({current_hm}), đang kiểm tra sự kiện...")
                    ok, res = trigger_notification_check()
                    print(f"[TELEGRAM SCHEDULER] Kết quả gửi: {ok} - {res}")
        except Exception as e:
            print(f"[TELEGRAM SCHEDULER LỖI]: {e}")
        time.sleep(30)

def start_scheduler():
    global _scheduler_thread, _scheduler_running
    if _scheduler_thread is None or not _scheduler_thread.is_alive():
        _scheduler_running = True
        _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
        _scheduler_thread.start()

def get_upcoming_month_events():
    """Lấy danh sách các sự kiện giỗ & sinh nhật trong 30 ngày tới"""
    if not os.path.exists(DATABASE_FILE):
        return []
    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        clan_data = json.load(f)
    members = clan_data.get("thanh_vien", [])

    results = []
    base_date = datetime.now()
    for offset in range(1, 31):
        target = base_date + timedelta(days=offset)
        evs = get_events_for_date(target, members)
        for de in evs["death_events"]:
            results.append({
                "type": "death",
                "solar_date": evs["target_date_solar"],
                "lunar_date": evs["target_date_lunar"],
                "days_left": offset,
                "ho_ten": de["ho_ten"],
                "vai_ve": de["vai_ve"],
                "chi_tiet": f"Ngày giỗ Âm lịch: {de.get('mat_am')}"
            })
        for be in evs["birthday_events"]:
            results.append({
                "type": "birthday",
                "solar_date": evs["target_date_solar"],
                "lunar_date": evs["target_date_lunar"],
                "days_left": offset,
                "ho_ten": be["ho_ten"],
                "vai_ve": be["vai_ve"],
                "chi_tiet": f"Sinh nhật {be.get('sinh')} (Tròn {be.get('tuoi_mung')} tuổi)"
            })
    return results
