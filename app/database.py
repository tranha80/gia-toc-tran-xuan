import sqlite3
import json
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

DB_PATH = r"d:\Gia pha\gia_toc_tran_xuan.db"
JSON_PATH = r"d:\Gia pha\gia_toc_tran_xuan.json"
EXCEL_PATH = r"d:\Gia pha\Gia_Pha_Tran_Xuan_So_Hoa_Chuan.xlsx"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_members(query=None, gen=None, gender=None):
    conn = get_db()
    c = conn.cursor()
    sql = "SELECT * FROM thanh_vien WHERE 1=1"
    params = []
    if gen and gen != "all":
        sql += " AND the_he = ?"
        params.append(int(gen))
    if gender and gender != "all":
        sql += " AND gioi_tinh = ?"
        params.append(gender)
    if query:
        sql += " AND (ho_ten LIKE ? OR ghi_chu LIKE ? OR sinh LIKE ? OR vai_ve LIKE ?)"
        q_wild = f"%{query}%"
        params.extend([q_wild, q_wild, q_wild, q_wild])
    sql += " ORDER BY the_he ASC, id ASC"
    c.execute(sql, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_member_by_id(member_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM thanh_vien WHERE id = ?", (member_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_next_member_id():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM thanh_vien WHERE id LIKE 'TX-%' ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    max_num = 0
    for r in rows:
        try:
            num = int(r["id"].replace("TX-", ""))
            if num > max_num:
                max_num = num
        except ValueError:
            pass
    return f"TX-{(max_num + 1):03d}"

def create_member(data):
    conn = get_db()
    c = conn.cursor()
    mid = data.get("id") or get_next_member_id()
    c.execute("""
        INSERT INTO thanh_vien (id, ho_ten, gioi_tinh, the_he, vai_ve, sinh, mat_duong, mat_am, huong_tho, que_quan, phan_mo, ghi_chu)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        mid,
        data.get("ho_ten", ""),
        data.get("gioi_tinh", "Nam"),
        int(data.get("the_he", 1)) if data.get("the_he") else None,
        data.get("vai_ve", ""),
        data.get("sinh", ""),
        data.get("mat_duong", ""),
        data.get("mat_am", ""),
        str(data.get("huong_tho", "")),
        data.get("que_quan", ""),
        data.get("phan_mo", ""),
        data.get("ghi_chu", "")
    ))
    conn.commit()
    conn.close()
    sync_to_json_and_excel()
    return get_member_by_id(mid)

def update_member(member_id, data):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        UPDATE thanh_vien SET
            ho_ten = ?,
            gioi_tinh = ?,
            the_he = ?,
            vai_ve = ?,
            sinh = ?,
            mat_duong = ?,
            mat_am = ?,
            huong_tho = ?,
            que_quan = ?,
            phan_mo = ?,
            ghi_chu = ?
        WHERE id = ?
    """, (
        data.get("ho_ten", ""),
        data.get("gioi_tinh", "Nam"),
        int(data.get("the_he", 1)) if data.get("the_he") else None,
        data.get("vai_ve", ""),
        data.get("sinh", ""),
        data.get("mat_duong", ""),
        data.get("mat_am", ""),
        str(data.get("huong_tho", "")),
        data.get("que_quan", ""),
        data.get("phan_mo", ""),
        data.get("ghi_chu", ""),
        member_id
    ))
    conn.commit()
    conn.close()
    sync_to_json_and_excel()
    return get_member_by_id(member_id)

def delete_member(member_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM thanh_vien WHERE id = ?", (member_id,))
    conn.commit()
    conn.close()
    sync_to_json_and_excel()
    return True

def get_anniversaries():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM ngay_gio ORDER BY id ASC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def sync_to_json_and_excel():
    """Tự động đồng bộ CSDL SQLite ra file JSON và file Excel để dữ liệu luôn nhất quán"""
    try:
        members = get_all_members()
        anniversaries = get_anniversaries()

        # 1. Update JSON
        if os.path.exists(JSON_PATH):
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                jdata = json.load(f)
        else:
            jdata = {}
        jdata["thanh_vien"] = members
        jdata["ngay_gio"] = anniversaries
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(jdata, f, ensure_ascii=False, indent=2)

        # 2. Update Excel Sheet 1
        if os.path.exists(EXCEL_PATH):
            wb = openpyxl.load_workbook(EXCEL_PATH)
            if "Danh sách Thành viên" in wb.sheetnames:
                ws = wb["Danh sách Thành viên"]
                # Clear existing rows from row 3
                max_r = ws.max_row
                if max_r > 2:
                    ws.delete_rows(3, max_r - 2)
                thin_border = Border(
                    left=Side(style='thin', color='D9D9D9'),
                    right=Side(style='thin', color='D9D9D9'),
                    top=Side(style='thin', color='D9D9D9'),
                    bottom=Side(style='thin', color='D9D9D9')
                )
                regular_font = Font(name="Arial", size=10)
                for m in members:
                    ws.append([
                        m["id"], m["ho_ten"], m["gioi_tinh"], m["the_he"], m["vai_ve"],
                        m["sinh"], m["mat_duong"], m["mat_am"], m["huong_tho"],
                        m["phan_mo"], m["ghi_chu"]
                    ])
                    r_idx = ws.max_row
                    ws.row_dimensions[r_idx].height = 22
                    for col_idx in range(1, 12):
                        cell = ws.cell(row=r_idx, column=col_idx)
                        cell.font = regular_font
                        cell.border = thin_border
                        if col_idx in [1, 3, 4, 6, 7, 8, 9]:
                            cell.alignment = Alignment(horizontal="center", vertical="center")
                        else:
                            cell.alignment = Alignment(vertical="center")
                wb.save(EXCEL_PATH)
    except Exception as e:
        print(f"[CẢNH BÁO ĐỒNG BỘ]: {e}")
