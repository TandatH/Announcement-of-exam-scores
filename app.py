"""
================================================================================
  ỨNG DỤNG TRA CỨU ĐIỂM THI - app.py
  Tra cứu bằng: Ngày sinh + Số báo danh
  Đã nâng cấp: Hiển thị từng môn + Thời gian theo giờ Việt Nam + Fix PDF
================================================================================
"""

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import re
import io
import qrcode
import requests
import pytz
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
# CSS — Giữ nguyên giao diện Luxury Dark gốc
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
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 2.4rem !important;
        color: #e8c96d !important;
    }

    .total-box {
        background: linear-gradient(135deg, rgba(184,146,42,0.15), rgba(184,146,42,0.06)) !important;
        border: 2px solid rgba(232,201,109,0.45) !important;
        box-shadow: 0 0 35px rgba(232,201,109,0.25) !important;
        border-radius: 14px;
        padding: 20px; text-align: center; margin-top: 24px;
    }
    .total-value {
        font-size: 4.2rem !important;
        line-height: 1 !important;
        text-shadow: 0 0 30px rgba(232,201,109,0.7) !important;
    }

    .timestamp-line {
        color: rgba(255,255,255,0.18); font-size: 0.70rem;
        text-align: center; margin-top: 14px; letter-spacing: 0.05em;
    }

    .app-footer {
        text-align: center; padding: 28px 0 14px;
        color: rgba(255,255,255,0.15); font-size: 0.72rem; letter-spacing: 0.08em;
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

# ============================================================
# IP & GEOLOCATION
# ============================================================
def get_client_ip() -> str:
    try:
        headers = st.context.headers
        for h in ["CF-Connecting-IP", "X-Forwarded-For", "X-Real-Ip", "Forwarded"]:
            val = headers.get(h, "")
            if val:
                ip = val.split(",")[0].strip()
                if ip:
                    return ip
    except:
        pass
    return "unknown"

@st.cache_data(ttl=3600)
def get_ip_location(ip: str) -> dict:
    if ip in ["unknown", "127.0.0.1", "::1", "localhost"] or any(ip.startswith(x) for x in ["192.168.", "10.", "172.16."]):
        return {"country": "Unknown", "city": "Local Network", "region": "", "isp": "Unknown"}
    try:
        response = requests.get(f"https://freeipapi.com/api/json/{ip}", timeout=6)
        if response.status_code == 200:
            data = response.json()
            return {
                "country": data.get("countryName", "Unknown"),
                "city": data.get("cityName", "Unknown"),
                "region": data.get("regionName", ""),
                "isp": data.get("isp", "Unknown")
            }
    except:
        pass
    return {"country": "Unknown", "city": "Unknown", "region": "", "isp": "Unknown"}

# ============================================================
# GOOGLE SHEETS
# ============================================================
@st.cache_resource(ttl=300)
def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.readonly"]
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
        return pd.DataFrame(ws.get_all_records())
    except Exception as e:
        st.error(f"❌ Lỗi đọc dữ liệu: {e}")
        return pd.DataFrame()

# ============================================================
# ACCESS LOGS
# ============================================================
def _create_access_log_sheet(spreadsheet):
    try:
        ws = spreadsheet.add_worksheet(title=SHEET_ACCESS_LOGS, rows=10000, cols=10)
        ws.append_row(["IP", "Thời gian", "SBD_Tra_Cuu", "Trạng thái", "Quốc gia", "Thành phố", "Vùng", "ISP", "Latitude", "Longitude"])
    except Exception:
        pass

def append_access_log(ip: str, sbd: str, status: str):
    loc = get_ip_location(ip)
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    timestamp_vn = datetime.now(vn_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    spreadsheet = get_spreadsheet()
    if spreadsheet is None:
        return
    try:
        ws = spreadsheet.worksheet(SHEET_ACCESS_LOGS)
        row = [
            ip, timestamp_vn, sbd, status,
            loc.get("country", ""), loc.get("city", ""), loc.get("region", ""),
            loc.get("isp", ""), "", ""
        ]
        ws.append_row(row)
    except gspread.exceptions.WorksheetNotFound:
        _create_access_log_sheet(spreadsheet)
        try:
            append_access_log(ip, sbd, status)
        except:
            pass
    except Exception:
        pass

# ============================================================
# BẢO MẬT & TRA CỨU
# ============================================================
def check_security(ip: str, sbd_dang_tra: str) -> dict:
    logs_df = load_access_logs()
    if logs_df.empty or "IP" not in logs_df.columns:
        return {"allowed": True, "reason": ""}

    ip_logs = logs_df[logs_df["IP"] == ip].copy()

    # Kiểm tra số lần sai trong LOCKOUT_MINUTES phút
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

    # Kiểm tra giới hạn số thí sinh khác nhau
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

def validate_sbd(sbd: str) -> bool:
    return bool(re.fullmatch(r"\d{6}", sbd.strip()))

def lookup_score(ngay_sinh: str, sbd: str) -> dict:
    df = load_score_data()
    if df.empty:
        return {"found": False, "data": None}

    sbd_input = str(sbd).strip()
    df["_sbd"] = df["Số báo danh"].astype(str).str.strip().str.zfill(6)

    def normalize_dob(val):
        if pd.isna(val) or str(val).strip() == "":
            return None
        for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]:
            try:
                return pd.to_datetime(val, format=fmt, errors='coerce').strftime("%d/%m/%Y")
            except:
                continue
        try:
            return pd.to_datetime(val, dayfirst=True, errors='coerce').strftime("%d/%m/%Y")
        except:
            return None

    df["_ngay_sinh"] = df["Ngày sinh"].apply(normalize_dob)

    try:
        input_date = pd.to_datetime(ngay_sinh, dayfirst=True, errors='coerce').strftime("%d/%m/%Y")
    except:
        return {"found": False, "data": None}

    matched = df[(df["_sbd"] == sbd_input) & (df["_ngay_sinh"] == input_date)]
    if matched.empty:
        return {"found": False, "data": None}

    row = matched.iloc[0]
    return {
        "found": True,
        "data": {
            "Họ và Tên": str(row.get("Họ và Tên", "Không có tên")).strip(),
            "Ngày sinh": str(row.get("Ngày sinh", "")).strip(),
            "Số báo danh": str(row.get("Số báo danh", "")).strip(),
            "Công nghệ": row.get("Công nghệ", 0),
            "GD ĐP": row.get("GD ĐP", 0),
        }
    }

# ============================================================
# QR CODE & PDF (ĐÃ FIX)
# ============================================================
def generate_qr(data):
    try:
        cn = float(data.get("Công nghệ", 0))
        gd = float(data.get("GD ĐP", 0))
        total = cn + gd
    except:
        total = 0.0
    qr_data = f"SBD:{data.get('Số báo danh', '')}|TOTAL:{total}"
    qr = qrcode.make(qr_data)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    return buf

def generate_pdf(data):
    try:
        cn = float(data.get("Công nghệ", 0))
        gd = float(data.get("GD ĐP", 0))
        total = cn + gd
    except:
        cn = gd = total = 0.0

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
    content.append(Paragraph(f"Công nghệ: {cn}", styles["Normal"]))
    content.append(Spacer(1, 8))
    content.append(Paragraph(f"GD ĐP: {gd}", styles["Normal"]))
    content.append(Spacer(1, 15))
    content.append(Paragraph(f"<b>TỔNG ĐIỂM: {total} / 20.0</b>", styles["Heading2"]))
    doc.build(content)
    buffer.seek(0)
    return buffer

# ============================================================
# HIỂN THỊ KẾT QUẢ (NÂNG CẤP)
# ============================================================
def display_score_result(data: dict):
    try:
        cn = float(data.get("Công nghệ", 0))
        gd = float(data.get("GD ĐP", 0))
        total = cn + gd
    except:
        cn = gd = total = 0.0

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

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.metric(label="Công nghệ", value=f"{cn:.1f}")
    with col2:
        st.metric(label="GD ĐP", value=f"{gd:.1f}")

    st.markdown(f"""
    <div class="total-box">
        <div class="total-label">🏆 TỔNG ĐIỂM</div>
        <div class="total-value">{total:.1f}</div>
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
    st.markdown('<span class="emblem-icon">🎓</span>', unsafe_allow_html=True)
    st.markdown('<h1 class="title-main">Tra Cứu Điểm Thi</h1>', unsafe_allow_html=True)
    st.markdown('<p class="title-sub">Hệ thống tra cứu kết quả kỳ thi</p>', unsafe_allow_html=True)

    st.markdown('<div class="lookup-card">', unsafe_allow_html=True)
    st.markdown('<p class="card-hint">Nhập thông tin bên dưới để xem điểm của bạn</p>', unsafe_allow_html=True)

    with st.form(key="lookup_form", clear_on_submit=False):
        ngay_sinh_input = st.text_input("📅 Ngày sinh", placeholder="VD: 15/08/2007", help="Định dạng: DD/MM/YYYY")
        sbd_input = st.text_input("🔢 Số báo danh", placeholder="VD: 000002", max_chars=6, help="Đúng 6 chữ số")
        submitted = st.form_submit_button("🔍  Xem kết quả")

    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        if not ngay_sinh_input.strip() or not sbd_input.strip() or not validate_sbd(sbd_input):
            st.warning("⚠️ Vui lòng nhập đầy đủ và đúng định dạng")
            return

        sbd_clean = sbd_input.strip()
        ngay_sinh_clean = ngay_sinh_input.strip()

        with st.spinner("Đang tra cứu..."):
            result = lookup_score(ngay_sinh_clean, sbd_clean)

        if result["found"]:
            append_access_log(client_ip, sbd_clean, "Thành công")
            st.success("✅ Tìm thấy kết quả thi!")
            display_score_result(result["data"])
            data = result["data"]

            # Thông tin truy cập (Admin)
            loc = get_ip_location(client_ip)
            with st.expander("📍 Thông tin truy cập (Admin only)", expanded=False):
                st.write(f"**IP:** {client_ip}")
                st.write(f"**Quốc gia:** {loc.get('country')}")
                st.write(f"**Thành phố:** {loc.get('city')}")
                st.write(f"**ISP:** {loc.get('isp')}")

            st.markdown("### 🔐 Mã xác thực")
            st.image(generate_qr(data), use_column_width=True)

            pdf = generate_pdf(data)
            sbd_safe = data.get("Số báo danh", "unknown").strip()
            st.download_button(
                label="📄 Tải bảng điểm PDF",
                data=pdf,
                file_name=f"bang_diem_{sbd_safe}.pdf",
                mime="application/pdf"
            )
        else:
            append_access_log(client_ip, sbd_clean, "Thất bại - Không tìm thấy")
            st.error("❌ Không tìm thấy thông tin. Vui lòng kiểm tra lại Ngày sinh và Số báo danh.")

def render_footer():
    st.markdown("""
    <div class="app-footer">
        🔒 Hệ thống được bảo vệ &nbsp;·&nbsp; Mọi truy cập đều được ghi lại
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__" or True:
    main()
    render_footer()
