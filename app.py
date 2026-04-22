# -*- coding: utf-8 -*-
"""
================================================================================
  ỨNG DỤNG TRA CỨU ĐIỂM THI - app.py
  Tra cứu bằng: Ngày sinh + Số báo danh (không cần nhập tên)
================================================================================
"""

import io
import re
from datetime import datetime, timedelta

import gspread
import pandas as pd
import pytz
import qrcode
import streamlit as st
from google.oauth2.service_account import Credentials
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
import os

# ============================================================
# CẤU HÌNH TRANG
# ============================================================
st.set_page_config(
    page_title="Tra Cứu Điểm Thi",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CSS — Giao diện Luxury Dark Academy
# ============================================================
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,300&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', 'Be Vietnam Pro', 'Segoe UI', sans-serif !important;
    }

    .stApp {
        background-color: #080b12;
        background-image:
            radial-gradient(ellipse 80% 50% at 50% -10%, rgba(180,140,60,0.20) 0%, transparent 70%),
            radial-gradient(ellipse 50% 40% at 85% 100%, rgba(50,90,180,0.13) 0%, transparent 60%);
        min-height: 100vh;
    }

    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem !important; max-width: 540px !important; }

    .top-bar {
        width: 100%; height: 3px;
        background: linear-gradient(90deg, transparent, #b8922a, #e8c96d, #b8922a, transparent);
        margin-bottom: 40px; border-radius: 2px;
    }

    .emblem-icon {
        font-size: 3rem; display: block; text-align: center;
        filter: drop-shadow(0 0 20px rgba(184,146,42,0.55));
        animation: glow-pulse 3s ease-in-out infinite;
        margin-bottom: 4px;
    }

    @keyframes glow-pulse {
        0%, 100% { filter: drop-shadow(0 0 12px rgba(184,146,42,0.4)); }
        50%       { filter: drop-shadow(0 0 28px rgba(232,201,109,0.9)); }
    }

    .title-main {
        font-family: 'Cormorant Garamond', Georgia, serif !important;
        font-size: 2.5rem; font-weight: 700; color: #e8d5a3;
        text-align: center; letter-spacing: 0.04em; line-height: 1.15;
        margin: 0 0 6px 0;
    }

    .title-sub {
        font-size: 0.78rem; font-weight: 400;
        color: rgba(232,213,163,0.38);
        text-align: center; letter-spacing: 0.22em;
        text-transform: uppercase; margin-bottom: 34px;
    }

    .lookup-card {
        background: linear-gradient(160deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.015) 100%);
        border: 1px solid rgba(184,146,42,0.22);
        border-radius: 20px;
        padding: 38px 34px 32px;
        box-shadow: 0 40px 80px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.05);
        position: relative; overflow: hidden;
    }

    .lookup-card::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(184,146,42,0.65), rgba(232,201,109,0.85), rgba(184,146,42,0.65), transparent);
    }

    .card-hint {
        color: rgba(232,213,163,0.5); font-size: 0.84rem;
        text-align: center; margin-bottom: 26px;
    }

    .stTextInput label {
        color: rgba(232,213,163,0.72) !important;
        font-size: 0.76rem !important; font-weight: 500 !important;
        letter-spacing: 0.16em !important; text-transform: uppercase !important;
        margin-bottom: 6px !important;
    }

    .stTextInput input {
        background: rgba(255,255,255,0.94) !important;
        border: 1.5px solid rgba(184,146,42,0.38) !important;
        border-radius: 10px !important;
        color: #0f1623 !important;
        font-family: 'DM Sans', 'Be Vietnam Pro', sans-serif !important;
        font-size: 1.05rem !important; font-weight: 500 !important;
        padding: 12px 16px !important;
        transition: all 0.25s ease !important;
        caret-color: #b8922a !important;
    }

    .stTextInput input::placeholder {
        color: #8fa0b3 !important;
        font-style: italic !important; font-weight: 300 !important;
    }

    .stTextInput input:focus {
        background: #ffffff !important;
        border-color: #c9a43a !important;
        box-shadow: 0 0 0 3px rgba(184,146,42,0.20), 0 2px 10px rgba(184,146,42,0.10) !important;
        color: #080b12 !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #a07820 0%, #e8c96d 48%, #a07820 100%) !important;
        background-size: 200% auto !important;
        color: #080b12 !important; border: none !important;
        border-radius: 10px !important; padding: 13px 32px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.92rem !important; font-weight: 700 !important;
        letter-spacing: 0.1em !important; text-transform: uppercase !important;
        width: 100% !important; margin-top: 10px !important;
        cursor: pointer !important; transition: all 0.4s ease !important;
        box-shadow: 0 4px 20px rgba(184,146,42,0.38) !important;
    }

    .stButton > button:hover {
        background-position: right center !important;
        box-shadow: 0 6px 28px rgba(184,146,42,0.60) !important;
        transform: translateY(-2px) !important;
    }

    .result-wrapper {
        margin-top: 26px;
        animation: slide-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
    }

    @keyframes slide-up {
        from { opacity: 0; transform: translateY(18px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    .result-header {
        background: linear-gradient(135deg, rgba(184,146,42,0.09), rgba(50,90,180,0.06));
        border: 1px solid rgba(184,146,42,0.28);
        border-radius: 16px 16px 0 0; border-bottom: none;
        padding: 26px 26px 18px; text-align: center;
        position: relative;
    }

    .result-name {
        font-family: 'Cormorant Garamond', Georgia, serif !important;
        font-size: 1.9rem; font-weight: 700; color: #e8d5a3; margin-bottom: 5px;
    }

    .result-info { color: rgba(232,213,163,0.48); font-size: 0.82rem; }

    .result-body {
        background: rgba(255,255,255,0.018);
        border: 1px solid rgba(184,146,42,0.22);
        border-radius: 0 0 16px 16px; border-top: 1px solid rgba(184,146,42,0.10);
        padding: 22px 24px 26px;
    }

    .score-label {
        color: rgba(232,213,163,0.4); font-size: 0.70rem;
        letter-spacing: 0.18em; text-transform: uppercase;
        text-align: center; margin-bottom: 14px;
    }

    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(184,146,42,0.35) !important;
        border-radius: 14px !important;
        padding: 18px 12px !important;
        min-height: 110px;
    }

    [data-testid="metric-container"] label {
        font-size: 0.78rem !important;
        letter-spacing: 0.12em !important;
    }

    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 2.4rem !important;
        color: #e8c96d !important;
    }

    .total-box {
        background: linear-gradient(135deg, rgba(184,146,42,0.15), rgba(184,146,42,0.06)) !important;
        border: 2px solid rgba(232,201,109,0.45) !important;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        margin-top: 14px;
    }

    .total-value {
        font-size: 4.2rem !important;
        line-height: 1 !important;
        text-shadow: 0 0 30px rgba(232,201,109,0.7) !important;
        color: #e8c96d !important;
        font-family: 'Cormorant Garamond', Georgia, serif !important;
        font-weight: 700 !important;
    }

    .total-label { color: rgba(232,213,163,0.5); font-size: 0.70rem; letter-spacing: 0.18em; text-transform: uppercase; margin-bottom: 6px; }
    .total-max { color: rgba(232,213,163,0.28); font-size: 0.78rem; margin-top: 4px; }

    .timestamp-line {
        color: rgba(255,255,255,0.18); font-size: 0.70rem;
        text-align: center; margin-top: 14px; letter-spacing: 0.05em;
    }

    .app-footer {
        text-align: center; padding: 28px 0 14px;
        color: rgba(255,255,255,0.15); font-size: 0.72rem; letter-spacing: 0.08em;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# HẰNG SỐ
# ============================================================
SHEET_DIEM_THI = "TraCuu1"
SHEET_HOC_SINH = "TongHopHocSinh"
SHEET_ACCESS_LOGS = "Access_Logs"
MAX_FAIL_ATTEMPTS = 5
LOCKOUT_MINUTES = 30
MAX_UNIQUE_SBD = 3

# ============================================================
# IP
# ============================================================
def get_client_ip() -> str:
    try:
        headers = st.context.headers
        for h in ["X-Forwarded-For", "X-Real-Ip", "Forwarded"]:
            val = headers.get(h, "")
            if val:
                ip = val.split(",")[0].strip()
                if ip:
                    return ip
    except Exception:
        pass
    return "unknown"

# ============================================================
# THỜI GIAN CÔNG BỐ
# ============================================================
def get_current_mode() -> str:
    vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
    now = datetime.now(vn_tz)

    khoi9_start = vn_tz.localize(datetime(2026, 4, 21, 0, 0, 0))
    khoi9_end = vn_tz.localize(datetime(2026, 4, 23, 23, 59, 59))
    khoi8_start = vn_tz.localize(datetime(2026, 4, 24, 0, 0, 0))
    khoi8_end = vn_tz.localize(datetime(2026, 4, 26, 23, 59, 59))

    if khoi9_start <= now <= khoi9_end:
        return "khoi9"
    if khoi8_start <= now <= khoi8_end:
        return "khoi8"
    return "closed"

# ============================================================
# GOOGLE SHEETS
# ============================================================
@st.cache_resource(ttl=300)
def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds_info = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
    return gspread.authorize(credentials)


def get_spreadsheet():
    try:
        client = get_gspread_client()
        sheet_id = st.secrets["spreadsheet"]["id"]
        return client.open_by_key(sheet_id)
    except Exception as e:
        st.error(f"❌ Không thể kết nối Google Sheets. Lỗi: {e}")
        return None


@st.cache_data(ttl=120)
def load_score_data() -> pd.DataFrame:
    spreadsheet = get_spreadsheet()
    if spreadsheet is None:
        return pd.DataFrame()

    try:
        ws = spreadsheet.worksheet(SHEET_DIEM_THI)
        values = ws.get_all_values()
        if not values or len(values) < 2:
            return pd.DataFrame()
        return pd.DataFrame(values[1:], columns=values[0])
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"❌ Không tìm thấy tab '{SHEET_DIEM_THI}'.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi đọc dữ liệu: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=120)
def load_student_lookup_data() -> pd.DataFrame:
    spreadsheet = get_spreadsheet()
    if spreadsheet is None:
        return pd.DataFrame()

    try:
        ws = spreadsheet.worksheet(SHEET_HOC_SINH)
        records = ws.get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame()
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"❌ Không tìm thấy tab '{SHEET_HOC_SINH}'.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi đọc dữ liệu từ sheet '{SHEET_HOC_SINH}': {e}")
        return pd.DataFrame()

def parse_score_value(val):
    if val is None:
        return None

    text = str(val).strip()
    if not text:
        return None

    text = text.replace(" ", "")

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")

    try:
        return float(text)
    except Exception:
        return None

# ============================================================
# ACCESS LOGS
# ============================================================
def load_access_logs() -> pd.DataFrame:
    spreadsheet = get_spreadsheet()
    if spreadsheet is None:
        return pd.DataFrame()

    try:
        ws = spreadsheet.worksheet(SHEET_ACCESS_LOGS)
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame(columns=["IP", "Thời gian", "SBD_Tra_Cuu", "Trạng thái"])
        df = pd.DataFrame(records)
        df["Thời gian"] = pd.to_datetime(df["Thời gian"], errors="coerce")
        return df
    except gspread.exceptions.WorksheetNotFound:
        _create_access_log_sheet(spreadsheet)
        return pd.DataFrame(columns=["IP", "Thời gian", "SBD_Tra_Cuu", "Trạng thái"])
    except Exception:
        return pd.DataFrame(columns=["IP", "Thời gian", "SBD_Tra_Cuu", "Trạng thái"])


def _create_access_log_sheet(spreadsheet):
    try:
        ws = spreadsheet.add_worksheet(title=SHEET_ACCESS_LOGS, rows=10000, cols=4)
        ws.append_row(["IP", "Thời gian", "SBD_Tra_Cuu", "Trạng thái"])
    except Exception:
        pass


def append_access_log(ip: str, sbd: str, status: str):
    vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
    timestamp_vn = datetime.now(vn_tz).strftime("%Y-%m-%d %H:%M:%S")

    spreadsheet = get_spreadsheet()
    if spreadsheet is None:
        return

    try:
        ws = spreadsheet.worksheet(SHEET_ACCESS_LOGS)
        ws.append_row([ip, timestamp_vn, sbd, status])
    except gspread.exceptions.WorksheetNotFound:
        _create_access_log_sheet(spreadsheet)
        try:
            ws = spreadsheet.worksheet(SHEET_ACCESS_LOGS)
            ws.append_row([ip, timestamp_vn, sbd, status])
        except Exception:
            pass
    except Exception:
        pass

# ============================================================
# BẢO MẬT
# ============================================================
def check_security(ip: str, sbd_dang_tra: str) -> dict:
    logs_df = load_access_logs()
    if logs_df.empty or "IP" not in logs_df.columns:
        return {"allowed": True, "reason": ""}

    ip_logs = logs_df[logs_df["IP"] == ip].copy()

    cutoff_time = datetime.now() - timedelta(minutes=LOCKOUT_MINUTES)
    recent_logs = ip_logs[ip_logs["Thời gian"] >= cutoff_time]

    if "Trạng thái" in recent_logs.columns:
        fail_count = recent_logs[
            recent_logs["Trạng thái"].astype(str).str.contains("Thất bại", na=False)
        ].shape[0]
        if fail_count >= MAX_FAIL_ATTEMPTS:
            return {
                "allowed": False,
                "reason": (
                    f"🔒 Bạn đã nhập sai quá nhiều lần ({fail_count} lần). "
                    f"Vui lòng thử lại sau {LOCKOUT_MINUTES} phút."
                ),
            }

    if "Trạng thái" in ip_logs.columns and "SBD_Tra_Cuu" in ip_logs.columns:
        success_logs = ip_logs[
            ip_logs["Trạng thái"].astype(str).str.contains("Thành công", na=False)
        ]
        unique_sbd = set(success_logs["SBD_Tra_Cuu"].astype(str).unique()) - {sbd_dang_tra}
        if len(unique_sbd) >= MAX_UNIQUE_SBD:
            return {
                "allowed": False,
                "reason": (
                    "🛡️ Thiết bị của bạn đã đạt giới hạn tra cứu. "
                    f"Mỗi thiết bị chỉ được xem tối đa {MAX_UNIQUE_SBD} thí sinh."
                ),
            }

    return {"allowed": True, "reason": ""}

# ============================================================
# TRA CỨU
# ============================================================
def validate_sbd(sbd: str) -> bool:
    return bool(re.fullmatch(r"\d{6}", sbd.strip()))


def normalize_dob_value(date_val):
    if pd.isna(date_val) or str(date_val).strip() == "":
        return None
    try:
        for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y"]:
            parsed = pd.to_datetime(date_val, format=fmt, errors="coerce")
            if pd.notna(parsed):
                return parsed.strftime("%d/%m/%Y")
        parsed = pd.to_datetime(date_val, dayfirst=True, errors="coerce")
        if pd.notna(parsed):
            return parsed.strftime("%d/%m/%Y")
        return None
    except Exception:
        return None


def normalize_name_value(name_val: str) -> str:
    return re.sub(r"\s+", " ", str(name_val or "").strip()).lower()


def lookup_score(ngay_sinh: str, sbd: str) -> dict:
    df = load_score_data()
    if df.empty:
        st.error("❌ Không tải được dữ liệu điểm thi từ Google Sheets.")
        return {"found": False, "data": None}

    required_columns = [
        "Họ và Tên",
        "Ngày sinh",
        "Số báo danh",
        "Điểm tổng kết HK2",
        "Điểm TBM Công nghệ",
    ]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"❌ Sheet '{SHEET_DIEM_THI}' đang thiếu cột: {', '.join(missing_cols)}")
        return {"found": False, "data": None}

    sbd_input = str(sbd).strip().zfill(6)
    df["_sbd"] = df["Số báo danh"].astype(str).str.strip().str.zfill(6)

    df["_ngay_sinh"] = df["Ngày sinh"].apply(normalize_dob_value)

    input_date_parsed = pd.to_datetime(ngay_sinh, dayfirst=True, errors="coerce")
    if pd.isna(input_date_parsed):
        st.error("❌ Ngày sinh nhập không đúng định dạng (DD/MM/YYYY).")
        return {"found": False, "data": None}

    input_date = input_date_parsed.strftime("%d/%m/%Y")

    matched = df[(df["_sbd"] == sbd_input) & (df["_ngay_sinh"] == input_date)].copy()
    if matched.empty:
        return {"found": False, "data": None}

    row = matched.iloc[0]
    return {
        "found": True,
        "data": {
            "Họ và Tên": str(row.get("Họ và Tên", "")).strip(),
            "Ngày sinh": str(row.get("Ngày sinh", "")).strip(),
            "Số báo danh": str(row.get("Số báo danh", "")).strip(),
            "Điểm tổng kết HK2": row.get("Điểm tổng kết HK2", "N/A"),
            "Điểm TBM Công nghệ": row.get("Điểm TBM Công nghệ", "N/A"),
        },
    }


def lookup_sbd_by_name_dob(ho_ten: str, ngay_sinh: str) -> dict:
    df = load_student_lookup_data()
    if df.empty:
        st.error("❌ Không tải được dữ liệu học sinh từ Google Sheets.")
        return {"found": False, "data": None, "message": "Không tải được dữ liệu học sinh."}

    required_columns = ["Họ và Tên", "Ngày sinh", "Số báo danh"]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"❌ Sheet '{SHEET_HOC_SINH}' đang thiếu cột: {', '.join(missing_cols)}")
        return {
            "found": False,
            "data": None,
            "message": f"Sheet '{SHEET_HOC_SINH}' đang thiếu cột bắt buộc.",
        }

    input_name_raw = re.sub(r"\s+", " ", str(ho_ten or "").strip())
    input_name_normalized = normalize_name_value(input_name_raw)
    input_dob_normalized = normalize_dob_value(ngay_sinh)

    if not input_dob_normalized:
        return {
            "found": False,
            "data": None,
            "message": "Ngày sinh nhập không đúng định dạng (DD/MM/YYYY).",
        }

    working_df = df.copy()
    working_df["_ho_ten_raw"] = working_df["Họ và Tên"].astype(str).str.strip()
    working_df["_ho_ten_norm"] = working_df["Họ và Tên"].apply(normalize_name_value)
    working_df["_ngay_sinh_norm"] = working_df["Ngày sinh"].apply(normalize_dob_value)
    working_df["_sbd"] = working_df["Số báo danh"].astype(str).str.strip()

    matched = working_df[
        (working_df["_ho_ten_norm"] == input_name_normalized)
        & (working_df["_ngay_sinh_norm"] == input_dob_normalized)
    ].copy()

    if matched.empty:
        return {
            "found": False,
            "data": None,
            "message": "Không tìm thấy học sinh khớp với Họ và Tên và Ngày sinh đã nhập.",
        }

    matched["_exact_name"] = matched["_ho_ten_raw"] == input_name_raw
    matched["_exact_name_ci"] = matched["_ho_ten_raw"].str.lower() == input_name_raw.lower()
    matched = matched.sort_values(
        by=["_exact_name", "_exact_name_ci", "_ho_ten_raw"],
        ascending=[False, False, True],
    )

    row = matched.iloc[0]
    return {
        "found": True,
        "data": {
            "Họ và Tên": str(row.get("Họ và Tên", "")).strip(),
            "Ngày sinh": str(row.get("Ngày sinh", "")).strip(),
            "Số báo danh": str(row.get("Số báo danh", "")).strip(),
        },
        "message": "",
    }

# ============================================================
# QR / PDF
# ============================================================
def generate_qr(data):
    def parse(val):
        try:
            return float(val) 
        except Exception:
            return 0.0

    diem_hk2 = parse_score_value(data.get("Điểm tổng kết HK2")) or 0.0
    diem_tbm_cn = parse_score_value(data.get("Điểm TBM Công nghệ")) or 0.0
    tong_diem = diem_hk2 + diem_tbm_cn

    qr_data = (
        f"SBD:{data.get('Số báo danh', '')}|"
        f"DOB:{data.get('Ngày sinh', '')}|"
        f"HK2:{diem_hk2:.2f}|"
        f"TBM_CN:{diem_tbm_cn:.2f}|"
        f"TOTAL:{tong_diem:.2f}"
    )

    qr = qrcode.make(qr_data)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    return buf

def register_vietnamese_font():
    possible_fonts = [
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]

    for font_path in possible_fonts:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("VNFont", font_path))
            return "VNFont"

    return "Helvetica"

def generate_pdf(data):
    def parse_score(val):
        if val is None or str(val).strip() == "":
            return 0.0
        try:
            return float(val)
        except Exception:
            return 0.0

    diem_hk2 = parse_score_value(data.get("Điểm tổng kết HK2")) or 0.0
    diem_tbm_cn = parse_score_value(data.get("Điểm TBM Công nghệ")) or 0.0
    tong_diem = diem_hk2 + diem_tbm_cn

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    font_name = register_vietnamese_font()

    styles["Title"].fontName = font_name
    styles["Title"].fontSize = 22

    styles["Normal"].fontName = font_name
    styles["Normal"].fontSize = 15
    styles["Normal"].leading = 22

    content = [
        Paragraph("BẢNG KẾT QUẢ HỌC TẬP", styles["Title"]),
        Spacer(1, 28),

        Paragraph(f"Họ và Tên: {data.get('Họ và Tên', '')}", styles["Normal"]),
        Spacer(1, 12),

        Paragraph(f"Ngày sinh: {data.get('Ngày sinh', '')}", styles["Normal"]),
        Spacer(1, 12),

        Paragraph(f"Số báo danh: {str(data.get('Số báo danh', '')).zfill(6)}", styles["Normal"]),
        Spacer(1, 20),

        Paragraph(f"Điểm tổng kết HK2: {diem_hk2:.2f}", styles["Normal"]),
        Spacer(1, 12),

        Paragraph(f"Điểm TBM Công nghệ: {diem_tbm_cn:.2f}", styles["Normal"]),
        Spacer(1, 12),

        Paragraph(f"Tổng điểm hiển thị: {tong_diem:.2f} / 20.0", styles["Normal"]),
    ]

    doc.build(content)
    buffer.seek(0)
    return buffer
# ============================================================
# HIỂN THỊ KẾT QUẢ
# ============================================================
def display_score_result(data: dict):
    def parse_diem(val):
        if val is None or str(val).strip() == "":
            return None
        try:
            return float(val)
        except Exception:
            return None

    diem_hk2 = parse_score_value(data.get("Điểm tổng kết HK2"))
    diem_tbm_cn = parse_score_value(data.get("Điểm TBM Công nghệ"))

    co_diem = [d for d in [diem_hk2, diem_tbm_cn] if d is not None]
    tong_diem = sum(co_diem) if co_diem else None
    tong_str = f"{tong_diem:.2f}" if tong_diem is not None else "—"

    vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
    now_vn = datetime.now(vn_tz).strftime("%H:%M:%S — %d/%m/%Y")

    st.markdown('<div class="result-wrapper">', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="result-header">
            <div style="font-size:1.8rem; margin-bottom:10px;">🎓</div>
            <div class="result-name">{data.get("Họ và Tên", "Thí sinh")}</div>
            <div class="result-info">
                📅 {data.get("Ngày sinh", "")} &nbsp;·&nbsp; 🔢 SBD:
                <strong style="color:#e8c96d">{data.get("Số báo danh", "")}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="result-body">', unsafe_allow_html=True)
    st.markdown('<p class="score-label">KẾT QUẢ HỌC TẬP</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.metric(
            label="📘 ĐIỂM TỔNG KẾT HK2",
            value=f"{diem_hk2:.2f}" if diem_hk2 is not None else "Chưa có",
        )
    with col2:
        st.metric(
            label="🏅 ĐIỂM TBM CÔNG NGHỆ",
            value=f"{diem_tbm_cn:.2f}" if diem_tbm_cn is not None else "Chưa có",
        )

    st.markdown(
        f"""
        <div class="total-box">
            <div class="total-label">🏆 TỔNG ĐIỂM HIỂN THỊ</div>
            <div class="total-value">{tong_str}</div>
            <div class="total-max">/ 20.0 điểm</div>
        </div>
        <div class="timestamp-line">
            ✓ Tra cứu thành công · {now_vn}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div></div>", unsafe_allow_html=True)


def display_sbd_result(data: dict):
    vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
    now_vn = datetime.now(vn_tz).strftime("%H:%M:%S — %d/%m/%Y")

    st.markdown('<div class="result-wrapper">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="result-header">
            <div style="font-size:1.8rem; margin-bottom:10px;">🎓</div>
            <div class="result-name">{data.get("Họ và Tên", "Học sinh")}</div>
            <div class="result-info">
                📅 {data.get("Ngày sinh", "")} &nbsp;·&nbsp; 🔢 SBD:
                <strong style="color:#e8c96d">{data.get("Số báo danh", "")}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="result-body">
            <p class="score-label">THÔNG TIN TRA CỨU</p>
            <div style="display:grid; gap:12px;">
                <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(184,146,42,0.35); border-radius:14px; padding:16px 18px;">
                    <div style="color:rgba(232,213,163,0.4); font-size:0.70rem; letter-spacing:0.18em; text-transform:uppercase; margin-bottom:6px;">Họ và Tên</div>
                    <div style="color:#f5f1e6; font-size:1.1rem; font-weight:600;">{data.get("Họ và Tên", "")}</div>
                </div>
                <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(184,146,42,0.35); border-radius:14px; padding:16px 18px;">
                    <div style="color:rgba(232,213,163,0.4); font-size:0.70rem; letter-spacing:0.18em; text-transform:uppercase; margin-bottom:6px;">Ngày sinh</div>
                    <div style="color:#f5f1e6; font-size:1.05rem; font-weight:600;">{data.get("Ngày sinh", "")}</div>
                </div>
                <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(184,146,42,0.35); border-radius:14px; padding:16px 18px;">
                    <div style="color:rgba(232,213,163,0.4); font-size:0.70rem; letter-spacing:0.18em; text-transform:uppercase; margin-bottom:6px;">Số báo danh</div>
                    <div style="color:#e8c96d; font-size:1.35rem; font-weight:700;">{data.get("Số báo danh", "")}</div>
                </div>
            </div>
            <div class="timestamp-line">
                ✓ Tra cứu thành công · {now_vn}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_page_header():
    st.markdown('<div class="top-bar"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <span class="emblem-icon">🎓</span>
        <h1 class="title-main">Tra Cứu Điểm Thi</h1>
        <p class="title-sub">Hệ thống tra cứu kết quả học tập</p>
        """,
        unsafe_allow_html=True,
    )


def render_mode_notice(mode: str):
    messages = {
        "khoi9": "ĐANG TRA CỨU ĐIỂM KHỐI 9 (21–23/04)",
        "khoi8": "TRA CỨU SỐ BÁO DANH KHỐI 8 (24–26/04)",
        "closed": "⏳ Hệ thống tra cứu chưa mở hoặc đã kết thúc",
    }

    st.markdown(
        f"""
        <div style="margin:-8px 0 24px; text-align:center; padding:14px 18px; background:rgba(184,146,42,0.10); border:1px solid rgba(184,146,42,0.28); border-radius:14px;">
            <div style="color:#e8d5a3; font-size:0.82rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase;">
                {messages.get(mode, messages["closed"])}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_khoi9_mode(client_ip: str):
    pre_check = check_security(client_ip, sbd_dang_tra="__pre_check__")
    if not pre_check["allowed"] and "nhập sai quá nhiều" in pre_check["reason"]:
        st.error(pre_check["reason"])
        return

    st.markdown('<div class="lookup-card">', unsafe_allow_html=True)
    st.markdown('<p class="card-hint">Nhập thông tin bên dưới để xem kết quả của bạn</p>', unsafe_allow_html=True)

    with st.form("lookup_form", clear_on_submit=False):
        ngay_sinh_input = st.text_input(
            "📅 Ngày sinh",
            placeholder="VD: 15/08/2007",
            help="Định dạng: DD/MM/YYYY",
        )
        sbd_input = st.text_input(
            "🔢 Số báo danh",
            placeholder="VD: 012345",
            max_chars=6,
            help="Đúng 6 chữ số",
        )
        submitted = st.form_submit_button("🔍 Xem kết quả")

    st.markdown("</div>", unsafe_allow_html=True)

    if not submitted:
        return

    errors = []
    if not ngay_sinh_input.strip():
        errors.append("Vui lòng nhập **Ngày sinh**.")
    if not sbd_input.strip():
        errors.append("Vui lòng nhập **Số báo danh**.")
    elif not validate_sbd(sbd_input):
        errors.append("**Số báo danh** phải đúng **6 chữ số** — ví dụ: `012345`.")

    if errors:
        for err in errors:
            st.warning(f"⚠️ {err}")
        return

    sbd_clean = sbd_input.strip()
    ngay_sinh_clean = ngay_sinh_input.strip()

    security_check = check_security(client_ip, sbd_dang_tra=sbd_clean)
    if not security_check["allowed"]:
        st.error(security_check["reason"])
        append_access_log(client_ip, sbd_clean, "Thất bại - Bị chặn bảo mật")
        return

    with st.spinner("Đang tra cứu..."):
        result = lookup_score(ngay_sinh_clean, sbd_clean)

    if result["found"]:
        append_access_log(client_ip, sbd_clean, "Thành công")
        st.success("✅ Tìm thấy kết quả!")
        data = result["data"]
        display_score_result(data)

        try:
            diem_tbm_cn = parse_score_value(data.get("Điểm TBM Công nghệ")) or 0.0
        except Exception:
            diem_tbm_cn = 0.0

        st.info("📢 Thông báo: Đã công bố điểm tổng kết HK2 và điểm TBM Công nghệ.")

        if diem_tbm_cn > 5:
            st.balloons()
            st.success(
                f"🎓 Chúc mừng em! Em đã hoàn thành môn Công nghệ với điểm TBM {diem_tbm_cn:.2f}."
            )
            st.markdown(
                """
### 🌟 Lời chúc mừng

Xin chúc mừng em đã hoàn thành tốt môn **Công nghệ** và chính thức tốt nghiệp môn học này.  
Đây là kết quả xứng đáng cho sự nỗ lực, kiên trì và cố gắng của em trong suốt quá trình học tập.

Chúc em luôn giữ vững niềm tin, tiếp tục phát huy năng lực của mình,  
và bước tới một tương lai **tươi sáng, bản lĩnh và thành công hơn**.
                """
            )

        st.markdown("### 🔐 Mã xác thực")
        st.image(generate_qr(data))

        pdf = generate_pdf(data)
        st.download_button(
            label="📄 Tải bảng điểm PDF",
            data=pdf,
            file_name=f"bang_diem_{data.get('Số báo danh', 'khong_ro')}.pdf",
            mime="application/pdf",
        )
    else:
        append_access_log(client_ip, sbd_clean, "Thất bại - Không tìm thấy")
        st.error("❌ Không tìm thấy thông tin. Vui lòng kiểm tra lại Ngày sinh và Số báo danh.")


def render_khoi8_mode():
    st.markdown('<div class="lookup-card">', unsafe_allow_html=True)
    st.markdown(
        '<p class="card-hint">Nhập Họ và Tên cùng Ngày tháng năm sinh để tra cứu số báo danh</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="text-align:center; padding:18px 12px; background:rgba(255,255,255,0.025); border:1px solid rgba(184,146,42,0.20); border-radius:14px; color:rgba(255,255,255,0.78); line-height:1.7;">
            Hệ thống đang mở giai đoạn tra cứu số báo danh cho khối 8.<br/>
            Form nhập liệu sẽ được bổ sung ở bước chỉnh sửa tiếp theo.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
    

    with st.form("lookup_form_khoi8", clear_on_submit=False):
        ho_ten_input = st.text_input(
            "👤 Họ và tên",
            placeholder="VD: Nguyễn Văn A",
        )
        ngay_sinh_input = st.text_input(
            "📅 Ngày tháng năm sinh",
            placeholder="VD: 15/08/2012",
            help="Định dạng: DD/MM/YYYY",
        )
        submitted = st.form_submit_button("Tra cứu số báo danh")

    st.markdown("</div>", unsafe_allow_html=True)

    if not submitted:
        return

    errors = []
    if not ho_ten_input.strip():
        errors.append("Vui lòng nhập **Họ và tên**.")
    if not ngay_sinh_input.strip():
        errors.append("Vui lòng nhập **Ngày tháng năm sinh**.")

    if errors:
        for err in errors:
            st.warning(f"⚠️ {err}")
        return

    with st.spinner("Đang tra cứu số báo danh..."):
        result = lookup_sbd_by_name_dob(ho_ten_input, ngay_sinh_input)

    if result["found"]:
        st.success("✅ Tìm thấy số báo danh!")
        display_sbd_result(result["data"])
    else:
        st.error(f"❌ {result.get('message', 'Không tìm thấy thông tin học sinh.')}")


def render_closed_mode():
    st.markdown('<div class="lookup-card">', unsafe_allow_html=True)
    st.markdown(
        """
        <p class="card-hint">Hệ thống chỉ mở tra cứu theo từng giai đoạn đã cấu hình</p>
        <div style="text-align:center; padding:18px 12px; background:rgba(184,146,42,0.10); border:1px solid rgba(184,146,42,0.30); border-radius:16px;">
            <div style="font-size:1.2rem; color:#e8c96d; font-weight:700; margin-bottom:10px;">Hệ thống đang đóng hoặc chưa đến thời gian tra cứu</div>
            <div style="color:rgba(255,255,255,0.78); line-height:1.75;">
                Khối 9: từ <strong>21/04/2026 00:00:00</strong> đến <strong>23/04/2026 23:59:59</strong><br/>
                Khối 8: từ <strong>24/04/2026 00:00:00</strong> đến <strong>26/04/2026 23:59:59</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# MAIN
# ============================================================
def main():
    mode = get_current_mode()
    client_ip = get_client_ip()
    render_page_header()
    render_mode_notice(mode)

    if mode == "khoi9":
        render_khoi9_mode(client_ip)
    elif mode == "khoi8":
        render_khoi8_mode()
    else:
        return

def render_footer():
    st.markdown(
        """
        <div class="app-footer">
            🔒 Hệ thống được bảo vệ &nbsp;·&nbsp; Mọi truy cập đều được ghi lại
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__" or True:
    main()
    render_footer()
