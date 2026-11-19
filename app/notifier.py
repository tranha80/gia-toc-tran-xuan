import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta, timezone
import re
import urllib.request
import urllib.parse

VN_TZ = timezone(timedelta(hours=7))

def get_vn_now():
    """Lấy thời gian hiện tại chuẩn theo múi giờ Việt Nam (UTC+7) bất kể máy chủ đặt ở đâu"""
    return datetime.now(VN_TZ).replace(tzinfo=None)

try:
    from lunardate import LunarDate
except ImportError:
    LunarDate = None

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_FILE = os.path.join(BASE_DIR, "telegram_config.json")
DATABASE_FILE = os.path.join(BASE_DIR, "gia_toc_tran_xuan.json")

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
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        "remind_days_before": 1,
        "notify_time": "06:00",
        "enabled": True,
        "last_notified_date": "",
        "last_checked_date": ""
    }
    if not os.path.exists(CONFIG_FILE):
        return default_config
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
            merged = {**default_config, **cfg}
            if not merged.get("bot_token") and default_config["bot_token"]:
                merged["bot_token"] = default_config["bot_token"]
            if not merged.get("chat_id") and default_config["chat_id"]:
                merged["chat_id"] = default_config["chat_id"]
            return merged
    except Exception:
        return default_config

def save_config(cfg):
    try:
        existing = load_config()
        merged = {**existing, **cfg}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def send_telegram_message(bot_token, chat_id, message_html):
    if not bot_token or not chat_id:
        return False, "Chưa điền Bot Token hoặc Chat ID."
    api_base = os.getenv("TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/")
    url = f"{api_base}/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    data = json.dumps(payload).encode('utf-8')
    last_err = ""
    for attempt in range(3):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                return True, "Gửi thành công!"
        except Exception as e:
            last_err = str(e)
            if attempt < 2:
                time.sleep(2)
    return False, last_err

def _load_members_list():
    try:
        from app.database import get_all_members
        members = get_all_members()
        if members:
            return members
    except Exception:
        pass
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
                clan_data = json.load(f)
            return clan_data.get("thanh_vien", [])
        except Exception:
            pass
    return []

def _is_ex_spouse_woman(m):
    if (m.get("gioi_tinh") or "") != "Nữ":
        return False
    hn = (m.get("tinh_trang_hn") or "").lower()
    vai = (m.get("vai_ve") or "").lower()
    note = (m.get("ghi_chu") or "").lower()
    return "ly hôn" in hn or "ly hôn" in vai or "dâu cũ" in vai or "đã ly hôn" in note

def get_events_for_date(target_date, members):
    d_duong, m_duong, y_duong = target_date.day, target_date.month, target_date.year
    d_am, m_am, y_am, can_chi_am = get_lunar_date(target_date)

    death_events = []
    birthday_events = []

    for m in members:
        if _is_ex_spouse_woman(m):
            continue
        is_deceased = bool(m.get("mat_duong") or m.get("mat_am") or "Đã Mất" in m.get("ghi_chu", "") or "chi mộ" in m.get("phan_mo", ""))

        if is_deceased:
            mat_am_str = m.get("mat_am", "")
            match_am = False
            if mat_am_str:
                nums = re.findall(r'\d+', mat_am_str)
                if len(nums) >= 2:
                    try:
                        p_day = int(nums[0])
                        p_mon = int(nums[1])
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
    lines.append("🏛️ <i>Tra cứu phả hệ online tại: https://giatoctranxuandongvinhthanhhoa.onrender.com/</i>")
    return "\n".join(lines)

_notify_lock = threading.Lock()

def trigger_notification_check(target_date=None, force=False, manual=False):
    with _notify_lock:
        cfg = load_config()
        days_before = cfg.get("remind_days_before", 1)

        now = get_vn_now() if target_date is None else target_date
        today_str = now.strftime("%Y-%m-%d")
        tomorrow = now + timedelta(days=days_before)

        # Chống spam khi web tự động F5 lúc 06:00 sáng hoặc /api/ping gọi định kỳ
        if not force and not manual:
            if cfg.get("last_notified_date") == today_str or cfg.get("last_checked_date") == today_str:
                return False, "Hôm nay đã kiểm tra thông báo tự động rồi."

        members = _load_members_list()
        if not members:
            return False, "Không tìm thấy CSDL."

        ev_data = get_events_for_date(tomorrow, members)
        msg = format_telegram_message(ev_data, days_before)

        if not msg:
            if force:
                msg = (
                    f"🌿 <b>GIA TỘC TRẦN XUÂN - TEST HỆ THỐNG</b> 🌿\n\n"
                    f"Ngày mai ({tomorrow.strftime('%d/%m/%Y')}) không có ngày giỗ hoặc sinh nhật nào.\n"
                    f"Kết nối Telegram hoạt động tốt!\n"
                    f"🏛️ https://giatoctranxuandongvinhthanhhoa.onrender.com/"
                )
            else:
                cfg["last_checked_date"] = today_str
                save_config(cfg)
                return True, f"Ngày mai ({tomorrow.strftime('%d/%m/%Y')}) không có sự kiện giỗ hoặc sinh nhật."

        bot_token = cfg.get("bot_token")
        chat_id = cfg.get("chat_id")
        ok, res = send_telegram_message(bot_token, chat_id, msg)
        if ok:
            cfg["last_notified_date"] = today_str
            cfg["last_checked_date"] = today_str
            save_config(cfg)
        return ok, res

# ==============================================================================
# 4. BACKGROUND SCHEDULER DAEMON (CHẠY THEO MÚI GIỜ VIỆT NAM UTC+7)
# ==============================================================================
_scheduler_thread = None
_scheduler_running = False

def _scheduler_loop():
    global _scheduler_running
    print("[TELEGRAM SCHEDULER] Tiến trình quét ngầm thông báo 06:00 sáng (UTC+7) đã khởi động!")
    while _scheduler_running:
        try:
            cfg = load_config()
            if cfg.get("enabled", True):
                notify_time_str = cfg.get("notify_time", "06:00")
                now = get_vn_now()
                current_hm = now.strftime("%H:%M")
                today_str = now.strftime("%Y-%m-%d")

                if notify_time_str <= current_hm <= "10:00" and cfg.get("last_notified_date") != today_str and cfg.get("last_checked_date") != today_str:
                    print(f"[TELEGRAM SCHEDULER] Khung giờ báo sáng ({current_hm} VN), đang kiểm tra sự kiện ngày giỗ & sinh nhật...")
                    ok, res = trigger_notification_check(force=False, manual=False)
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
    """Lấy danh sách các sự kiện giỗ & sinh nhật trong 30 ngày tới (theo giờ Việt Nam UTC+7)"""
    members = _load_members_list()
    if not members:
        return []

    results = []
    base_date = get_vn_now()
    for offset in range(0, 31):
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
