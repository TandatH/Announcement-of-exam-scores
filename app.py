"""
================================================================================
  ỨNG DỤNG TRA CỨU ĐIỂM THI - app.py
  Tra cứu bằng: Ngày sinh + Số báo danh (không cần nhập tên)
================================================================================
"""
import pytz
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import re
import unicodedata
import io
import qrcode
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
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
st.markdown("""
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

    /* Top bar */
    .top-bar {
        width: 100%; height: 3px;
        background: linear-gradient(90deg, transparent, #b8922a, #e8c96d, #b8922a, transparent);
        margin-bottom: 40px; border-radius: 2px;
    }

    /* Emblem */
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

    /* Title */
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

    /* Divider */
    .gold-divider {
        display: flex; align-items: center; gap: 12px; margin: 24px 0;
    }
    .gold-line {
        flex: 1; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(184,146,42,0.45), transparent);
    }
    .gold-diamond {
        width: 6px; height: 6px; background: #b8922a;
        transform: rotate(45deg); flex-shrink: 0;
    }

    /* Card */
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

    /* Labels */
    .stTextInput label {
        color: rgba(232,213,163,0.72) !important;
        font-size: 0.76rem !important; font-weight: 500 !important;
        letter-spacing: 0.16em !important; text-transform: uppercase !important;
        margin-bottom: 6px !important;
    }

    /* Input — sáng, chữ tối, tương phản cao */
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

    /* Button */
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

    /* Alerts */
    .stAlert { border-radius: 10px !important; }

    /* Result */
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
    .result-header::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(184,146,42,0.7), transparent);
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

    /* Metrics */
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.07) !important;
        border-radius: 12px !important; padding: 14px 10px !important;
        text-align: center !important; transition: all 0.2s !important;
    }
    [data-testid="metric-container"]:hover {
        border-color: rgba(184,146,42,0.32) !important;
        background: rgba(184,146,42,0.05) !important;
    }
    [data-testid="metric-container"] label {
        color: rgba(232,213,163,0.5) !important;
        font-size: 0.72rem !important; font-weight: 500 !important;
        letter-spacing: 0.1em !important; text-transform: uppercase !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #e8c96d !important; font-size: 1.75rem !important;
        font-weight: 700 !important;
        font-family: 'Cormorant Garamond', serif !important;
    }

    /* Total */
    .total-box {
        background: linear-gradient(135deg, rgba(184,146,42,0.10), rgba(184,146,42,0.04));
        border: 1px solid rgba(184,146,42,0.38); border-radius: 14px;
        padding: 20px; text-align: center; margin-top: 14px; position: relative;
    }
    .total-box::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(232,201,109,0.75), transparent);
    }
    .total-label { color: rgba(232,213,163,0.5); font-size: 0.70rem; letter-spacing: 0.18em; text-transform: uppercase; margin-bottom: 6px; }
    .total-value {
        font-family: 'Cormorant Garamond', Georgia, serif;
        font-size: 3rem; font-weight: 700; color: #e8c96d; line-height: 1;
        text-shadow: 0 0 28px rgba(232,201,109,0.45);
    }
    .total-max { color: rgba(232,213,163,0.28); font-size: 0.78rem; margin-top: 4px; }

    .timestamp-line {
        color: rgba(255,255,255,0.18); font-size: 0.70rem;
        text-align: center; margin-top: 14px; letter-spacing: 0.05em;
    }

    /* Spinner */
    .stSpinner > div { border-top-color: #b8922a !important; }

    /* Expander */
    .streamlit-expanderHeader {
        color: rgba(232,213,163,0.45) !important;
        font-size: 0.80rem !important; background: transparent !important;
    }

    /* Footer */
    .app-footer {
        text-align: center; padding: 28px 0 14px;
        color: rgba(255,255,255,0.15); font-size: 0.72rem; letter-spacing: 0.08em;
    }

    @media (max-width: 640px) {
        .title-main { font-size: 1.9rem; }
        .lookup-card { padding: 26px 18px; }
    }
    /* Cải thiện metric điểm môn */
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

    /* Làm tổng điểm nổi bật hơn */
    .total-box {
        background: linear-gradient(135deg, rgba(184,146,42,0.15), rgba(184,146,42,0.06)) !important;
        border: 2px solid rgba(232,201,109,0.45) !important;
        box-shadow: 0 0 35px rgba(232,201,109,0.25) !important;
    }
    .total-value {
        font-size: 4.2rem !important;
        line-height: 1 !important;
        text-shadow: 0 0 30px rgba(232,201,109,0.7) !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# HẰNG SỐ
# ============================================================
SHEET_DIEM_THI    = "Diem_Thi"
SHEET_ACCESS_LOGS = "Access_Logs"
MAX_FAIL_ATTEMPTS = 5
LOCKOUT_MINUTES   = 30
MAX_UNIQUE_SBD    = 3

def normalize_date(date_str):
    try:
        return pd.to_datetime(date_str, dayfirst=True).date()
    except:
        return None

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
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame()
        return pd.DataFrame(records)
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"❌ Không tìm thấy tab '{SHEET_DIEM_THI}'.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi đọc dữ liệu: {e}")
        return pd.DataFrame()


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
    except Exception as e:
        return pd.DataFrame(columns=["IP", "Thời gian", "SBD_Tra_Cuu", "Trạng thái"])


def _create_access_log_sheet(spreadsheet):
    try:
        ws = spreadsheet.add_worksheet(title=SHEET_ACCESS_LOGS, rows=10000, cols=4)
        ws.append_row(["IP", "Thời gian", "SBD_Tra_Cuu", "Trạng thái"])
    except Exception:
        pass


def append_access_log(ip: str, sbd: str, status: str):
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
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


def lookup_score(ngay_sinh: str, sbd: str) -> dict:
    df = load_score_data()
    if df.empty:
        st.error("❌ Không tải được dữ liệu điểm thi từ Google Sheets.")
        return {"found": False, "data": None}

    sbd_input = str(sbd).strip()

    # Clean SBD
    df["_sbd"] = df["Số báo danh"].astype(str).str.strip().str.zfill(6)  # đảm bảo 6 chữ số

    # Clean Ngày sinh - cách chắc chắn nhất
    def normalize_dob(date_val):
        if pd.isna(date_val) or str(date_val).strip() == "":
            return None
        try:
            # Thử nhiều format phổ biến
            for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y"]:
                try:
                    return pd.to_datetime(date_val, format=fmt, errors='coerce').strftime("%d/%m/%Y")
                except:
                    continue
            # Nếu không được thì fallback dayfirst
            return pd.to_datetime(date_val, dayfirst=True, errors='coerce').strftime("%d/%m/%Y")
        except:
            return None

    df["_ngay_sinh"] = df["Ngày sinh"].apply(normalize_dob)

    # Normalize input ngày sinh
    try:
        input_date = pd.to_datetime(ngay_sinh, dayfirst=True, errors='coerce').strftime("%d/%m/%Y")
        if pd.isna(input_date):  # nếu input sai format
            st.error("❌ Ngày sinh nhập không đúng định dạng (DD/MM/YYYY)")
            return {"found": False, "data": None}
    except:
        st.error("❌ Ngày sinh nhập không đúng định dạng.")
        return {"found": False, "data": None}

    # Match (không phân biệt hoa thường, bỏ khoảng trắng thừa)
    matched = df[
        (df["_sbd"] == sbd_input) &
        (df["_ngay_sinh"] == input_date)
    ].copy()

    if matched.empty:
        # Debug tạm thời (chỉ hiện khi không tìm thấy)
        with st.expander("🔍 Debug thông tin tra cứu (chỉ admin thấy)", expanded=False):
            st.write("**SBD input:**", sbd_input)
            st.write("**Ngày sinh input (normalized):**", input_date)
            st.write("**Danh sách SBD trong dữ liệu:**", df["_sbd"].unique().tolist())
            st.write("**Danh sách ngày sinh normalized:**", df["_ngay_sinh"].dropna().unique().tolist())
            st.dataframe(df[["Họ và Tên", "Ngày sinh", "_ngay_sinh", "Số báo danh", "_sbd"]].head(10))
        
        return {"found": False, "data": None}

    row = matched.iloc[0]

    return {
        "found": True,
        "data": {
            "Họ và Tên": str(row.get("Họ và Tên", "")).strip(),
            "Ngày sinh": str(row.get("Ngày sinh", "")).strip(),
            "Số báo danh": str(row.get("Số báo danh", "")).strip(),
            "Công nghệ": row.get("Công nghệ", "N/A"),
            "GD ĐP": row.get("GD ĐP", "N/A"),
            # Không cần đưa 'Tổng điểm' vào đây nữa
        }
    }
def generate_qr(data):
    def parse(val):
        try:
            return float(val) / 100
        except:
            return 0.0

    diem_cn = parse(data.get("Công nghệ"))
    diem_gd = parse(data.get("GD ĐP"))
    tong_diem = diem_cn + diem_gd

    qr_data = (
        f"SBD:{data.get('Số báo danh', '')}|"
        f"DOB:{data.get('Ngày sinh', '')}|"
        f"CN:{diem_cn:.2f}|"
        f"GDĐP:"{diem_gd:.2f}|"
        f"TOTAL:{tong_diem:.2f}"
    )

    qr = qrcode.make(qr_data)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    return buf
    return buf
def generate_pdf(data):
    try:
        diem_cn = float(data.get("Công nghệ", 0))
        diem_gd = float(data.get("GD ĐP", 0))
        tong_diem = diem_cn + diem_gd
    except:
        tong_diem = 0.0

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("BẢNG ĐIỂM THÍ SINH", styles["Title"]))
    content.append(Spacer(1, 20))

    content.append(Paragraph(f"Họ và Tên: {data.get('Họ và Tên', '')}", styles["Normal"]))
    content.append(Spacer(1, 8))
    content.append(Paragraph(f"Ngày sinh: {data.get('Ngày sinh', '')}", styles["Normal"]))
    content.append(Spacer(1, 8))
    content.append(Paragraph(f"Số báo danh: {data.get('Số báo danh', '')}", styles["Normal"]))
    content.append(Spacer(1, 12))
    content.append(Paragraph(f"Công nghệ: {data.get('Công nghệ', 'N/A')}", styles["Normal"]))
    content.append(Spacer(1, 8))
    content.append(Paragraph(f"GD ĐP: {data.get('GD ĐP', 'N/A')}", styles["Normal"]))
    content.append(Spacer(1, 12))
    content.append(Paragraph(f"Tổng điểm: {tong_diem} / 20.0", styles["Normal"]))

    doc.build(content)
    buffer.seek(0)
    return buffer
# ============================================================
# HIỂN THỊ KẾT QUẢ
# ============================================================
# ============================================================
# HIỂN THỊ KẾT QUẢ - ĐÃ TÁCH RIÊNG CÔNG NGHỆ & GD ĐP
# ============================================================
def display_score_result(data: dict):
    # Tính điểm an toàn — môn nào trống thì None, không ép về 0
    def parse_diem(val):
      if val is None or str(val).strip() == '':
          return None
      try:
          return float(val) / 100   # ✅ chia lại 100
      except:
          return None
    diem_cn = parse_diem(data.get("Công nghệ"))
    diem_gd = parse_diem(data.get("GD ĐP"))

    # Tổng điểm chỉ tính các môn đã có điểm
    co_diem = [d for d in [diem_cn, diem_gd] if d is not None]
    tong_diem = sum(co_diem) if co_diem else None
    tong_str = f"{tong_diem:.2f}" if tong_diem is not None else "—"

    # Thời gian theo giờ Việt Nam
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    now_vn = datetime.now(vn_tz).strftime("%H:%M:%S — %d/%m/%Y")

    st.markdown('<div class="result-wrapper">', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="result-header">
        <div style="font-size:1.8rem; margin-bottom:10px;">🎓</div>
        <div class="result-name">{data.get("Họ và Tên", "Thí sinh")}</div>
        <div class="result-info">
            📅 {data.get("Ngày sinh", "")} &nbsp;·&nbsp; 🔢 SBD: <strong style="color:#e8c96d">{data.get("Số báo danh", "")}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="result-body">', unsafe_allow_html=True)
    st.markdown('<p class="score-label">KẾT QUẢ CÁC MÔN THI</p>', unsafe_allow_html=True)

    # === HIỂN THỊ TỪNG MÔN — môn chưa có điểm hiện "Chưa có" ===
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.metric(
            label="📘 CÔNG NGHỆ",
            value=f"{diem_cn:.2f}" if diem_cn is not None else "Chưa có",
            delta=None
        )

    with col2:
        st.metric(
            label="📖 GIÁO DỤC ĐỊA PHƯƠNG",
            value=f"{diem_gd:.2f}" if diem_gd is not None else "Chưa có",
            delta=None
        )

    # Tổng điểm nổi bật
    st.markdown(f"""
    <div class="total-box">
        <div class="total-label">🏆 TỔNG ĐIỂM</div>
        <div class="total-value">{tong_str}</div>
        <div class="total-max">/ 20.0 điểm</div>
    </div>
    <div class="timestamp-line">
        ✓ Tra cứu thành công · {now_vn}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)


# ============================================================
# MAIN
# ============================================================
def main():
    client_ip = get_client_ip()

    st.markdown('<div class="top-bar"></div>', unsafe_allow_html=True)

    st.markdown("""
    <span class="emblem-icon">🎓</span>
    <h1 class="title-main">Tra Cứu Điểm Thi</h1>
    <p class="title-sub">Hệ thống tra cứu kết quả kỳ thi</p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="gold-divider">
        <div class="gold-line"></div>
        <div class="gold-diamond"></div>
        <div class="gold-line"></div>
    </div>
    """, unsafe_allow_html=True)

    pre_check = check_security(client_ip, sbd_dang_tra="__pre_check__")
    if not pre_check["allowed"] and "nhập sai quá nhiều" in pre_check["reason"]:
        st.error(pre_check["reason"])
        return

    st.markdown('<div class="lookup-card">', unsafe_allow_html=True)
    st.markdown('<p class="card-hint">Nhập thông tin bên dưới để xem điểm của bạn</p>', unsafe_allow_html=True)

    with st.form(key="lookup_form", clear_on_submit=False):
        ngay_sinh_input = st.text_input(
            "📅 Ngày sinh",
            placeholder="VD: 15/08/2007",
            help="Định dạng: DD/MM/YYYY"
        )
        sbd_input = st.text_input(
            "🔢 Số báo danh",
            placeholder="VD: 012345",
            max_chars=6,
            help="Đúng 6 chữ số"
        )
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🔍  Xem kết quả")

    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("ℹ️ Hướng dẫn tra cứu"):
        st.markdown("""
**Bạn cần nhập đúng 2 thông tin:**
- 📅 **Ngày sinh**: Định dạng `DD/MM/YYYY` — ví dụ `15/08/2007`
- 🔢 **Số báo danh**: Đúng 6 chữ số — ví dụ `012345`

> ⚠️ Hệ thống giới hạn số lần tra cứu để bảo mật thông tin thí sinh.
        """)

    if submitted:
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

        sbd_clean       = sbd_input.strip()
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
            st.success("✅ Tìm thấy kết quả thi!")
            display_score_result(result["data"])
            data = result["data"]

            # ========================
            # QR CODE
            # ========================
            st.markdown("### 🔐 Mã xác thực")
            qr_img = generate_qr(data)
            st.image(qr_img)

            # ========================
            # PDF DOWNLOAD
            # ========================
            pdf = generate_pdf(data)

            st.download_button(
                label="📄 Tải bảng điểm PDF",
                data=pdf,
                file_name=f"bang_diem_{data['Số báo danh']}.pdf",
                mime="application/pdf"
            )
        else:
            append_access_log(client_ip, sbd_clean, "Thất bại - Không tìm thấy")
            st.error("❌ Không tìm thấy thông tin. Vui lòng kiểm tra lại Ngày sinh và Số báo danh.")

            logs_df = load_access_logs()
            if not logs_df.empty and "IP" in logs_df.columns:
                cutoff = datetime.now() - timedelta(minutes=LOCKOUT_MINUTES)
                recent_fails = logs_df[
                    (logs_df["IP"] == client_ip) &
                    (logs_df["Thời gian"] >= cutoff) &
                    (logs_df["Trạng thái"].astype(str).str.contains("Thất bại", na=False))
                ]
                remaining = MAX_FAIL_ATTEMPTS - len(recent_fails)
                if 0 < remaining <= 2:
                    st.warning(f"⚠️ Bạn còn **{remaining}** lần thử trước khi bị tạm khóa {LOCKOUT_MINUTES} phút.")


def render_footer():
    st.markdown("""
    <div class="app-footer">
        🔒 Hệ thống được bảo vệ &nbsp;·&nbsp; Mọi truy cập đều được ghi lại
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__" or True:
    main()
    render_footer()
