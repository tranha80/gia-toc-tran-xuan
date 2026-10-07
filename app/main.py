import os
import sys
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
    sync_to_json_and_excel
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
