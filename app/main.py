import os
import sys
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.database import (
    get_all_members,
    get_member_by_id,
    create_member,
    update_member,
    delete_member,
    get_anniversaries,
    sync_to_json_and_excel,
    get_db,
    EXCEL_PATH
)
from app.notifier import (
    start_scheduler,
    load_config,
    save_config,
    trigger_notification_check,
    get_upcoming_month_events
)

# Admin PIN bảo mật
ADMIN_PIN = "5101980"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi động tiến trình chạy ngầm gửi tin nhắn Telegram đúng giờ
    start_scheduler()
    sync_to_json_and_excel()
    yield

app = FastAPI(
    title="Gia Tộc Trần Xuân - Quản Lý Phả Hệ",
    description="Backend API và Giao Diện Quản Trị Phả Hệ Dòng Họ Trần Xuân",
    version="2.0.0",
    lifespan=lifespan
)

# Models
class MemberSchema(BaseModel):
    id: Optional[str] = None
    ho_ten: str
    gioi_tinh: Optional[str] = "Nam"
    the_he: Optional[int] = 1
    vai_ve: Optional[str] = ""
    sinh: Optional[str] = ""
    mat_duong: Optional[str] = ""
    mat_am: Optional[str] = ""
    huong_tho: Optional[str] = ""
    que_quan: Optional[str] = ""
    phan_mo: Optional[str] = ""
    ghi_chu: Optional[str] = ""
    cha_id: Optional[str] = ""
    me_id: Optional[str] = ""
    vo_chong_id: Optional[str] = ""
    tinh_trang_hn: Optional[str] = ""

class TelegramConfigSchema(BaseModel):
    bot_token: str
    chat_id: str
    remind_days_before: Optional[int] = 1
    notify_time: Optional[str] = "07:00"
    enabled: Optional[bool] = True

class AdminLoginSchema(BaseModel):
    pin: str

# APIs
@app.get("/api/members")
def api_get_members(q: Optional[str] = None, gen: Optional[str] = None, gender: Optional[str] = None):
    return get_all_members(query=q, gen=gen, gender=gender)

@app.get("/api/members/{member_id}")
def api_get_member(member_id: str):
    m = get_member_by_id(member_id)
    if not m:
        raise HTTPException(status_code=404, detail="Không tìm thấy thành viên")
    return m

@app.post("/api/members")
def api_create_member(data: MemberSchema):
    new_m = create_member(data.model_dump())
    return {"success": True, "member": new_m}

@app.put("/api/members/{member_id}")
def api_update_member(member_id: str, data: MemberSchema):
    m = get_member_by_id(member_id)
    if not m:
        raise HTTPException(status_code=404, detail="Không tìm thấy thành viên")
    updated = update_member(member_id, data.model_dump())
    return {"success": True, "member": updated}

@app.delete("/api/members/{member_id}")
def api_delete_member(member_id: str):
    m = get_member_by_id(member_id)
    if not m:
        raise HTTPException(status_code=404, detail="Không tìm thấy thành viên")
    delete_member(member_id)
    return {"success": True, "message": f"Đã xóa thành viên {member_id}"}

@app.get("/api/anniversaries")
def api_get_anniversaries():
    return get_anniversaries()

@app.get("/api/upcoming-events")
def api_get_upcoming_events():
    return get_upcoming_month_events()

@app.get("/api/telegram/config")
def api_get_telegram_config():
    return load_config()

@app.post("/api/telegram/config")
def api_save_telegram_config(cfg: TelegramConfigSchema):
    saved = save_config(cfg.model_dump())
    return {"success": saved}

@app.post("/api/telegram/test")
def api_test_telegram():
    ok, res = trigger_notification_check(force=True)
    return {"success": ok, "message": res}

@app.post("/api/telegram/trigger-today")
def api_trigger_telegram_today():
    ok, res = trigger_notification_check(force=False)
    return {"success": ok, "message": res}

@app.post("/api/admin/login")
def api_admin_login(data: AdminLoginSchema):
    if data.pin == ADMIN_PIN:
        return {"success": True, "token": "admin_authenticated_session"}
    return {"success": False, "message": "Mã PIN quản trị viên không chính xác!"}

# Mount static files and frontend
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Gia Tộc Trần Xuân Backend đang hoạt động!</h1>"

# PWA & Offline Support
@app.get("/manifest.json")
def serve_manifest():
    mf = os.path.join(static_dir, "manifest.json")
    if os.path.exists(mf):
        return FileResponse(mf, media_type="application/manifest+json")
    raise HTTPException(status_code=404, detail="Manifest not found")

@app.get("/sw.js")
def serve_service_worker():
    sw = os.path.join(static_dir, "sw.js")
    if os.path.exists(sw):
        return FileResponse(sw, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="Service worker not found")

# Backup & Restore APIs
@app.get("/api/backup")
def api_backup_database():
    members = get_all_members()
    anniversaries = get_anniversaries()
    return {
        "version": "2.0.0",
        "exported_at": datetime.now().isoformat(),
        "total_members": len(members),
        "members": members,
        "anniversaries": anniversaries
    }

@app.post("/api/restore")
def api_restore_database(data: Dict[str, Any]):
    members = data.get("members") or data.get("thanh_vien")
    if not members or not isinstance(members, list):
        raise HTTPException(status_code=400, detail="Dữ liệu sao lưu không hợp lệ!")
    
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM thanh_vien")
    for m in members:
        c.execute("""
            INSERT OR REPLACE INTO thanh_vien (
                id, ho_ten, gioi_tinh, the_he, vai_ve, sinh, mat_duong, mat_am, 
                huong_tho, que_quan, phan_mo, ghi_chu, cha_id, me_id, vo_chong_id, tinh_trang_hn
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            m.get("id"), m.get("ho_ten", ""), m.get("gioi_tinh", "Nam"), m.get("the_he", 1),
            m.get("vai_ve", ""), m.get("sinh", ""), m.get("mat_duong", ""), m.get("mat_am", ""),
            str(m.get("huong_tho", "")), m.get("que_quan", ""), m.get("phan_mo", ""),
            m.get("ghi_chu", ""), m.get("cha_id", ""), m.get("me_id", ""),
            m.get("vo_chong_id", ""), m.get("tinh_trang_hn", "")
        ))
    conn.commit()
    conn.close()
    sync_to_json_and_excel()
    return {"success": True, "count": len(members)}

@app.get("/api/export/excel")
def api_export_excel():
    sync_to_json_and_excel()
    if os.path.exists(EXCEL_PATH):
        return FileResponse(
            EXCEL_PATH, 
            filename="Gia_Pha_Tran_Xuan_So_Hoa.xlsx", 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    raise HTTPException(status_code=404, detail="Không tìm thấy tệp Excel")

@app.get("/api/media/{filename}")
def api_get_media(filename: str):
    safe_name = os.path.basename(filename)
    root_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(root_dir, safe_name)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Không tìm thấy tệp hình ảnh")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
