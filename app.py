"""
================================================================================
  ỨNG DỤNG TRA CỨU ĐIỂM THI - app.py
  Tác giả: Được tạo bởi Claude (Anthropic)
  Mô tả: Ứng dụng Streamlit tra cứu điểm thi từ Google Sheets
         với cơ chế bảo mật chống dò điểm theo IP.
================================================================================
"""

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import re
import unicodedata
import json
import time

# ============================================================
# CẤU HÌNH TRANG - Phải đặt đầu tiên trước mọi lệnh Streamlit
# ============================================================
st.set_page_config(
    page_title="Tra Cứu Điểm Thi",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CSS TÙNG CHỈNH - Giao diện đẹp, chuyên nghiệp
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

    :root {
        --cream: #f5f0e8;
        --gold: #c9a84c;
        --gold-light: #e8c97a;
        --dark: #1a1410;
        --dark2: #2d2218;
        --dark3: #3d2f20;
        --text-muted: rgba(245,240,232,0.5);
        --border: rgba(201,168,76,0.25);
        --border-hover: rgba(201,168,76,0.6);
    }

    #MainMenu, footer, header { visibility: hidden; }

    .stApp {
        background: var(--dark);
        font-family: 'DM Sans', sans-serif;
        min-height: 100vh;
    }

    /* Nền có texture */
    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        background:
            radial-gradient(ellipse 80% 60% at 20% 0%, rgba(201,168,76,0.08) 0%, transparent 60%),
            radial-gradient(ellipse 60% 40% at 80% 100%, rgba(201,168,76,0.05) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }

    /* Card chính */
    .main-card {
        background: linear-gradient(160deg, rgba(45,34,24,0.95) 0%, rgba(26,20,16,0.98) 100%);
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: 48px 44px 40px;
        margin: 24px 0;
        box-shadow:
            0 0 0 1px rgba(201,168,76,0.05),
            0 40px 80px rgba(0,0,0,0.6),
            inset 0 1px 0 rgba(201,168,76,0.15);
        position: relative;
        overflow: hidden;
    }

    .main-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold), transparent);
    }

    /* Logo / icon trên cùng */
    .hero-icon {
        text-align: center;
        font-size: 2.2rem;
        margin-bottom: 12px;
        filter: drop-shadow(0 0 20px rgba(201,168,76,0.4));
    }

    /* Tiêu đề */
    .hero-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 2.6rem;
        font-weight: 700;
        color: var(--cream);
        text-align: center;
        margin-bottom: 6px;
        letter-spacing: 0.02em;
        line-height: 1.1;
    }

    .hero-title span {
        color: var(--gold);
    }

    .hero-subtitle {
        color: var(--text-muted);
        text-align: center;
        font-size: 0.9rem;
        font-weight: 300;
        letter-spacing: 0.05em;
        margin-bottom: 36px;
    }

    /* Đường kẻ trang trí */
    .gold-divider {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 28px 0;
    }
    .gold-divider::before, .gold-divider::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border));
    }
    .gold-divider::after {
        background: linear-gradient(90deg, var(--border), transparent);
    }
    .gold-divider-dot {
        width: 5px; height: 5px;
        border-radius: 50%;
        background: var(--gold);
        opacity: 0.5;
    }

    /* Label */
    .stTextInput label {
        color: var(--gold-light) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.12em !important;
        text-transform: uppercase !important;
        margin-bottom: 6px !important;
    }

    /* Input */
    .stTextInput input {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid var(--border) !important;
        border-radius: 2px !important;
        color: var(--cream) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.95rem !important;
        padding: 12px 16px !important;
        transition: all 0.25s ease !important;
        letter-spacing: 0.01em !important;
    }

    .stTextInput input::placeholder {
        color: rgba(245,240,232,0.2) !important;
        font-style: italic;
    }

    .stTextInput input:focus {
        border-color: var(--gold) !important;
        background: rgba(201,168,76,0.04) !important;
        box-shadow: 0 0 0 3px rgba(201,168,76,0.08), 0 1px 20px rgba(201,168,76,0.1) !important;
        outline: none !important;
    }

    /* Nút */
    .stButton > button {
        background: linear-gradient(135deg, #c9a84c 0%, #a8823a 50%, #c9a84c 100%) !important;
        background-size: 200% !important;
        color: var(--dark) !important;
        border: none !important;
        border-radius: 2px !important;
        padding: 14px 32px !important;
        font-size: 0.8rem !important;
        font-weight: 700 !important;
        font-family: 'DM Sans', sans-serif !important;
        letter-spacing: 0.15em !important;
        text-transform: uppercase !important;
        width: 100% !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px rgba(201,168,76,0.3) !important;
        margin-top: 8px !important;
    }

    .stButton > button:hover {
        box-shadow: 0 6px 30px rgba(201,168,76,0.5) !important;
        transform: translateY(-1px) !important;
        background-position: right !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Card kết quả */
    .result-card {
        background: linear-gradient(160deg, rgba(45,34,24,0.8), rgba(26,20,16,0.9));
        border: 1px solid rgba(201,168,76,0.3);
        border-radius: 4px;
        padding: 36px;
        margin-top: 28px;
        position: relative;
        overflow: hidden;
    }

    .result-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold), transparent);
    }

    .result-name {
        font-family: 'Cormorant Garamond', serif;
        font-size: 2rem;
        font-weight: 700;
        color: var(--cream);
        text-align: center;
        margin-bottom: 6px;
        letter-spacing: 0.02em;
    }

    .result-meta {
        color: var(--text-muted);
        text-align: center;
        font-size: 0.82rem;
        letter-spacing: 0.04em;
        margin-bottom: 28px;
    }

    /* Metric */
    [data-testid="metric-container"] {
        background: rgba(201,168,76,0.05) !important;
        border: 1px solid rgba(201,168,76,0.2) !important;
        border-radius: 2px !important;
        padding: 20px 12px !important;
        text-align: center !important;
    }

    [data-testid="metric-container"] label {
        color: var(--gold-light) !important;
        font-size: 0.68rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
    }

    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: var(--cream) !important;
        font-family: 'Cormorant Garamond', serif !important;
        font-size: 2.4rem !important;
        font-weight: 700 !important;
    }

    /* Alert */
    .stAlert {
        border-radius: 2px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.88rem !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        color: var(--text-muted) !important;
        font-size: 0.82rem !important;
    }

    /* Divider */
    .custom-divider {
        border: none;
        border-top: 1px solid rgba(201,168,76,0.15);
        margin: 24px 0;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: var(--gold) !important;
    }

    @media (max-width: 640px) {
        .hero-title { font-size: 2rem; }
        .main-card { padding: 32px 20px; }
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# CÁC HẰNG SỐ CẤU HÌNH
# ============================================================
SHEET_DIEM_THI    = "Diem_Thi"       # Tên tab dữ liệu điểm
SHEET_ACCESS_LOGS = "Access_Logs"     # Tên tab ghi log

MAX_FAIL_ATTEMPTS = 5     # Số lần thất bại tối đa trong cửa sổ thời gian
LOCKOUT_MINUTES   = 30    # Khóa sau bao nhiêu phút
MAX_UNIQUE_SBD    = 2     # Số SBD khác nhau tối đa được tra thành công / IP


# ============================================================
# HÀM: LẤY ĐỊA CHỈ IP CỦA NGƯỜI DÙNG
# ============================================================
def get_client_ip() -> str:
    """
    Lấy IP public của người dùng thông qua request headers.
    Ưu tiên X-Forwarded-For (khi chạy sau proxy/Streamlit Cloud),
    sau đó fallback về các header khác.
    Trả về "unknown" nếu không lấy được.
    """
    try:
        # st.context.headers có từ Streamlit >= 1.31
        headers = st.context.headers
        # Danh sách header phổ biến chứa IP thật
        for header_name in ["X-Forwarded-For", "X-Real-Ip", "Forwarded"]:
            val = headers.get(header_name, "")
            if val:
                # X-Forwarded-For có thể là chuỗi "ip1, ip2, ip3" → lấy ip đầu tiên
                ip = val.split(",")[0].strip()
                if ip:
                    return ip
    except Exception:
        pass
    return "unknown"


# ============================================================
# HÀM: KẾT NỐI GOOGLE SHEETS
# ============================================================
@st.cache_resource(ttl=300)  # Cache kết nối 5 phút để tối ưu performance
def get_gspread_client():
    """
    Khởi tạo và trả về Google Sheets client đã xác thực.
    Đọc thông tin service account từ st.secrets (Streamlit Secrets).
    Raises: Exception nếu không tìm thấy secrets hoặc xác thực thất bại.
    """
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    # Đọc credentials từ Streamlit Secrets (cấu hình khi deploy)
    creds_info = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
    return gspread.authorize(credentials)


def get_spreadsheet():
    """
    Mở và trả về đối tượng Spreadsheet theo URL hoặc tên trong secrets.
    Trả về None và hiển thị lỗi nếu không kết nối được.
    """
    try:
        client = get_gspread_client()
        # Lấy Spreadsheet ID/URL từ secrets
        sheet_id = st.secrets["spreadsheet"]["id"]
        return client.open_by_key(sheet_id)
    except Exception as e:
        st.error(f"❌ Không thể kết nối Google Sheets. Lỗi: {e}")
        return None


# ============================================================
# HÀM: ĐỌC DỮ LIỆU ĐIỂM THI
# ============================================================
@st.cache_data(ttl=120)  # Cache dữ liệu điểm 2 phút (tránh đọc Sheets liên tục)
def load_score_data() -> pd.DataFrame:
    """
    Đọc toàn bộ dữ liệu từ tab 'Diem_Thi' và trả về DataFrame.
    Cache 2 phút để giảm số lần gọi API.
    Trả về DataFrame rỗng nếu có lỗi.
    """
    spreadsheet = get_spreadsheet()
    if spreadsheet is None:
        return pd.DataFrame()
    try:
        ws = spreadsheet.worksheet(SHEET_DIEM_THI)
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        return df
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"❌ Không tìm thấy tab '{SHEET_DIEM_THI}' trong Google Sheets.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi đọc dữ liệu điểm thi: {e}")
        return pd.DataFrame()


# ============================================================
# HÀM: ĐỌC VÀ GHI ACCESS LOGS
# ============================================================
def load_access_logs() -> pd.DataFrame:
    """
    Đọc toàn bộ log truy cập từ tab 'Access_Logs'.
    KHÔNG cache vì cần dữ liệu real-time để kiểm tra bảo mật.
    Trả về DataFrame rỗng nếu chưa có dữ liệu hoặc lỗi.
    """
    spreadsheet = get_spreadsheet()
    if spreadsheet is None:
        return pd.DataFrame()
    try:
        ws = spreadsheet.worksheet(SHEET_ACCESS_LOGS)
        records = ws.get_all_records()
        if not records:
            # Tab tồn tại nhưng chưa có dữ liệu
            return pd.DataFrame(columns=["IP", "Thời gian", "SBD_Tra_Cuu", "Trạng thái"])
        df = pd.DataFrame(records)
        # Chuyển cột thời gian sang kiểu datetime để so sánh
        df["Thời gian"] = pd.to_datetime(df["Thời gian"], errors="coerce")
        return df
    except gspread.exceptions.WorksheetNotFound:
        # Tab chưa tồn tại → tạo mới
        _create_access_log_sheet(spreadsheet)
        return pd.DataFrame(columns=["IP", "Thời gian", "SBD_Tra_Cuu", "Trạng thái"])
    except Exception as e:
        # Lỗi không xác định → trả DataFrame rỗng để app không crash
        st.warning(f"⚠️ Không đọc được log truy cập: {e}")
        return pd.DataFrame(columns=["IP", "Thời gian", "SBD_Tra_Cuu", "Trạng thái"])


def _create_access_log_sheet(spreadsheet):
    """
    Tạo tab 'Access_Logs' với header nếu chưa tồn tại.
    Được gọi tự động khi phát hiện tab thiếu.
    """
    try:
        ws = spreadsheet.add_worksheet(title=SHEET_ACCESS_LOGS, rows=10000, cols=4)
        ws.append_row(["IP", "Thời gian", "SBD_Tra_Cuu", "Trạng thái"])
    except Exception:
        pass  # Bỏ qua nếu không tạo được (quyền hạn chế)


def append_access_log(ip: str, sbd: str, status: str):
    """
    Ghi một dòng log mới vào tab 'Access_Logs'.
    
    Args:
        ip     : Địa chỉ IP của người dùng
        sbd    : Số báo danh đã tra cứu
        status : "Thành công" hoặc "Thất bại" hoặc lý do cụ thể
    """
    spreadsheet = get_spreadsheet()
    if spreadsheet is None:
        return  # Không ghi được log → không crash app
    try:
        ws = spreadsheet.worksheet(SHEET_ACCESS_LOGS)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws.append_row([ip, timestamp, sbd, status])
    except gspread.exceptions.WorksheetNotFound:
        _create_access_log_sheet(spreadsheet)
        # Thử lại sau khi tạo tab
        try:
            ws = spreadsheet.worksheet(SHEET_ACCESS_LOGS)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ws.append_row([ip, timestamp, sbd, status])
        except Exception:
            pass
    except Exception:
        pass  # Lỗi ghi log không được làm crash app chính


# ============================================================
# HÀM: KIỂM TRA BẢO MẬT (CHỐNG DÒ ĐIỂM)
# ============================================================
def check_security(ip: str, sbd_dang_tra: str) -> dict:
    """
    Kiểm tra IP hiện tại có vi phạm các quy tắc bảo mật không.
    
    Quy tắc 1 - Chống brute-force:
        Nếu IP có >= MAX_FAIL_ATTEMPTS lần thất bại trong LOCKOUT_MINUTES phút gần nhất
        → bị khóa.
    
    Quy tắc 2 - Giới hạn xem điểm nhiều người:
        Nếu IP đã tra thành công >= MAX_UNIQUE_SBD số báo danh KHÁC với sbd_dang_tra
        → bị chặn.
    
    Returns:
        dict với keys:
            - "allowed" (bool): True nếu được phép tra cứu
            - "reason"  (str) : Thông báo lý do nếu bị chặn
    """
    logs_df = load_access_logs()

    # Nếu không đọc được log → cho phép (tránh chặn oan)
    if logs_df.empty or "IP" not in logs_df.columns:
        return {"allowed": True, "reason": ""}

    # Lọc log của IP này
    ip_logs = logs_df[logs_df["IP"] == ip].copy()

    # ── Quy tắc 1: Chống brute-force ──────────────────────────────────
    cutoff_time = datetime.now() - timedelta(minutes=LOCKOUT_MINUTES)
    recent_logs = ip_logs[ip_logs["Thời gian"] >= cutoff_time]

    if "Trạng thái" in recent_logs.columns:
        # Đếm số lần thất bại gần đây (bao gồm các dòng chứa từ "Thất bại")
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

    # ── Quy tắc 2: Giới hạn số SBD tra thành công ────────────────────
    if "Trạng thái" in ip_logs.columns and "SBD_Tra_Cuu" in ip_logs.columns:
        success_logs = ip_logs[
            ip_logs["Trạng thái"].astype(str).str.contains("Thành công", na=False)
        ]
        # Lấy tập hợp SBD đã tra thành công (loại trừ SBD đang tra hiện tại)
        unique_sbd_success = set(
            success_logs["SBD_Tra_Cuu"].astype(str).unique()
        ) - {sbd_dang_tra}

        if len(unique_sbd_success) >= MAX_UNIQUE_SBD:
            return {
                "allowed": False,
                "reason": (
                    "🛡️ Thiết bị/Mạng của bạn đã đạt giới hạn tra cứu điểm. "
                    f"Để bảo mật, mỗi thiết bị chỉ được xem điểm của tối đa {MAX_UNIQUE_SBD} thí sinh."
                ),
            }

    return {"allowed": True, "reason": ""}


# ============================================================
# HÀM: CHUẨN HÓA CHUỖI (để so sánh không phân biệt hoa/thường, dấu)
# ============================================================
def normalize_text(text: str) -> str:
    """
    Chuẩn hóa chuỗi họ tên:
    1. Xóa khoảng trắng hai đầu và khoảng trắng thừa giữa các từ.
    2. Chuyển về chữ thường.
    3. Chuẩn hóa NFC để đảm bảo encoding đồng nhất (giữ dấu tiếng Việt).
    
    Ví dụ: "  Huỳnh  TẤN  Đạt  " → "huỳnh tấn đạt"
    """
    if not isinstance(text, str):
        text = str(text)
    # Xóa khoảng trắng thừa
    text = " ".join(text.split())
    # Chuyển về chữ thường
    text = text.lower()
    # Chuẩn hóa NFC — bắt buộc để tránh lỗi encoding khác nhau giữa
    # dữ liệu Google Sheets và input người dùng (NFD vs NFC)
    text = unicodedata.normalize("NFC", text)
    return text


def validate_sbd(sbd: str) -> bool:
    """
    Kiểm tra số báo danh có đúng định dạng 6 chữ số không.
    Ví dụ hợp lệ: "012345", "999999"
    Ví dụ không hợp lệ: "12345", "01234A", ""
    """
    return bool(re.fullmatch(r"\d{6}", sbd.strip()))


# ============================================================
# HÀM: TRA CỨU ĐIỂM
# ============================================================
def lookup_score(ho_ten: str, ngay_sinh: str, sbd: str) -> dict:
    """
    Tra cứu điểm thi dựa trên 3 thông tin: họ tên, ngày sinh, số báo danh.
    
    Logic:
    1. Chuẩn hóa ho_ten để so sánh không phân biệt hoa/thường.
    2. So sánh ngày sinh dưới dạng chuỗi (format YYYY-MM-DD hoặc DD/MM/YYYY).
    3. So sánh SBD chính xác (exact match).
    4. Cả 3 phải khớp → trả về thông tin điểm.
    
    Returns:
        dict với keys:
            - "found" (bool): True nếu tìm thấy
            - "data"  (dict): Thông tin điểm nếu found=True
    """
    df = load_score_data()

    if df.empty:
        return {"found": False, "data": None}

    # Kiểm tra các cột bắt buộc tồn tại
    required_cols = ["Họ và Tên", "Ngày sinh", "Số báo danh"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"❌ Thiếu cột '{col}' trong Google Sheets.")
            return {"found": False, "data": None}

    # Chuẩn hóa cột họ tên trong DataFrame để so sánh
    df["_ho_ten_norm"] = df["Họ và Tên"].astype(str).apply(normalize_text)
    ho_ten_norm = normalize_text(ho_ten)

    # Chuẩn hóa SBD (trim khoảng trắng, đảm bảo là chuỗi)
    df["_sbd_norm"] = df["Số báo danh"].astype(str).str.strip()
    sbd_norm = sbd.strip()

    # Chuẩn hóa ngày sinh: thử nhiều format phổ biến
    df["_ngay_sinh_norm"] = df["Ngày sinh"].astype(str).str.strip()
    
    # Chuẩn hóa ngày sinh người dùng nhập
    ngay_sinh_norm = ngay_sinh.strip()

    # Tìm dòng khớp cả 3 điều kiện
    mask = (
        (df["_ho_ten_norm"] == ho_ten_norm) &
        (df["_sbd_norm"] == sbd_norm) &
        (df["_ngay_sinh_norm"] == ngay_sinh_norm)
    )
    matched = df[mask]

    if matched.empty:
        return {"found": False, "data": None}

    # Lấy dòng đầu tiên khớp (không nên có 2 học sinh giống hệt nhau)
    row = matched.iloc[0]
    return {
        "found": True,
        "data": {
            "Họ và Tên":   row.get("Họ và Tên", ""),
            "Ngày sinh":   row.get("Ngày sinh", ""),
            "Số báo danh": row.get("Số báo danh", ""),
            "Toán":        row.get("Toán", "N/A"),
            "Ngữ Văn":     row.get("Ngữ Văn", "N/A"),
            "Tiếng Anh":   row.get("Tiếng Anh", "N/A"),
            "Tổng điểm":   row.get("Tổng điểm", "N/A"),
        }
    }


# ============================================================
# HÀM: HIỂN THỊ KẾT QUẢ ĐIỂM ĐẸP
# ============================================================
def display_score_result(data: dict):
    """
    Hiển thị bảng điểm với giao diện đẹp sử dụng st.metric và HTML.
    
    Args:
        data: dict chứa thông tin điểm của học sinh
    """
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    
    # Tên học sinh và thông tin cơ bản
    st.markdown(
        f'<div class="result-name">{data["Họ và Tên"]}</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="result-meta">📅 Ngày sinh: {data["Ngày sinh"]} &nbsp;|&nbsp; '
        f'🔢 Số báo danh: <strong>{data["Số báo danh"]}</strong></div>',
        unsafe_allow_html=True
    )

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:rgba(255,255,255,0.7); text-align:center; '
        'font-size:0.9rem; margin-bottom:16px;">📊 Kết quả các môn thi</p>',
        unsafe_allow_html=True
    )

    # Hiển thị điểm từng môn
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="📐 Toán", value=str(data["Toán"]))
    with col2:
        st.metric(label="📖 Ngữ Văn", value=str(data["Ngữ Văn"]))
    with col3:
        st.metric(label="🌐 Tiếng Anh", value=str(data["Tiếng Anh"]))

    # Tổng điểm nổi bật
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="text-align:center; background: rgba(201,168,76,0.06);
             border: 1px solid rgba(201,168,76,0.25); border-radius:2px; padding:24px; margin-top:12px;
             position:relative; overflow:hidden;">
            <div style="position:absolute;top:0;left:0;right:0;height:1px;
                 background:linear-gradient(90deg,transparent,rgba(201,168,76,0.5),transparent)"></div>
            <div style="color:rgba(201,168,76,0.7); font-size:0.68rem; letter-spacing:0.15em;
                 text-transform:uppercase; margin-bottom:8px; font-family:'DM Sans',sans-serif;">
                Tổng điểm
            </div>
            <div style="color:#e8c97a; font-size:3.5rem; font-weight:700; line-height:1;
                 font-family:'Cormorant Garamond',serif;">
                {data["Tổng điểm"]}
            </div>
            <div style="color:rgba(245,240,232,0.25); font-size:0.78rem; margin-top:6px;
                 font-family:'DM Sans',sans-serif; letter-spacing:0.05em;">
                / 30.0 điểm
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<p style="color:rgba(255,255,255,0.4); text-align:center; '
        'font-size:0.75rem; margin-top:16px;">✅ Tra cứu thành công lúc '
        + datetime.now().strftime("%H:%M:%S %d/%m/%Y") + "</p>",
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# GIAO DIỆN CHÍNH
# ============================================================
def main():
    """
    Hàm main: Vẽ toàn bộ giao diện và xử lý logic tra cứu điểm.
    """
    # Lấy IP người dùng ngay khi load trang
    client_ip = get_client_ip()

    # ── Header ────────────────────────────────────────────────
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<div class="hero-icon">🎓</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-title">Tra Cứu <span>Điểm Thi</span></div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="hero-subtitle">NHẬP ĐẦY ĐỦ THÔNG TIN ĐỂ XEM KẾT QUẢ</div>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="gold-divider"><div class="gold-divider-dot"></div><div class="gold-divider-dot"></div><div class="gold-divider-dot"></div></div>', unsafe_allow_html=True)

    # ── Hướng dẫn ──────────────────────────────────────────────
    with st.expander("ℹ️ Hướng dẫn tra cứu", expanded=False):
        st.markdown("""
        **Để tra cứu điểm, bạn cần nhập đúng:**
        - ✏️ **Họ và Tên**: Đúng như đã đăng ký (không phân biệt hoa/thường)
        - 📅 **Ngày sinh**: Đúng theo định dạng `DD/MM/YYYY` (ví dụ: `15/08/2007`)
        - 🔢 **Số báo danh**: Đúng 6 chữ số (ví dụ: `012345`)
        
        > ⚠️ Hệ thống giới hạn tra cứu để bảo mật thông tin thi sinh.
        """)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Kiểm tra brute-force sơ bộ trước khi hiện form ──────
    # (Kiểm tra với SBD rỗng để chỉ check lock-out)
    pre_check = check_security(client_ip, sbd_dang_tra="__pre_check__")
    if not pre_check["allowed"] and "nhập sai quá nhiều" in pre_check["reason"]:
        st.error(pre_check["reason"])
        st.markdown("</div>", unsafe_allow_html=True)  # Đóng main-card
        return

    # ── Form tra cứu ──────────────────────────────────────────
    with st.form(key="lookup_form", clear_on_submit=False):
        ho_ten_input = st.text_input(
            "👤 Họ và Tên",
            placeholder="Ví dụ: Nguyễn Văn An",
            help="Nhập đúng họ tên đã đăng ký dự thi"
        )
        ngay_sinh_input = st.text_input(
            "📅 Ngày sinh",
            placeholder="Ví dụ: 15/08/2007",
            help="Định dạng: ngày/tháng/năm (DD/MM/YYYY)"
        )
        sbd_input = st.text_input(
            "🔢 Số báo danh",
            placeholder="Ví dụ: 012345",
            max_chars=6,
            help="Đúng 6 chữ số, điền số 0 ở đầu nếu có"
        )

        submitted = st.form_submit_button("🔍 Tra cứu điểm")

    st.markdown("</div>", unsafe_allow_html=True)  # Đóng main-card

    # ── Xử lý khi submit form ────────────────────────────────
    if submitted:
        # 1. Validate đầu vào phía client
        errors = []
        if not ho_ten_input.strip():
            errors.append("Vui lòng nhập **Họ và Tên**.")
        if not ngay_sinh_input.strip():
            errors.append("Vui lòng nhập **Ngày sinh**.")
        if not sbd_input.strip():
            errors.append("Vui lòng nhập **Số báo danh**.")
        elif not validate_sbd(sbd_input):
            errors.append("**Số báo danh** phải là đúng **6 chữ số** (ví dụ: 012345).")

        if errors:
            for err in errors:
                st.warning(f"⚠️ {err}")
            return

        # Chuẩn hóa input
        ho_ten_clean = ho_ten_input.strip()
        sbd_clean    = sbd_input.strip()
        # Chuẩn hóa ngày sinh: chấp nhận cả dd/mm/yyyy và d/m/yyyy
        ngay_sinh_clean = ngay_sinh_input.strip()

        # 2. Kiểm tra bảo mật
        security_check = check_security(client_ip, sbd_dang_tra=sbd_clean)
        if not security_check["allowed"]:
            st.error(security_check["reason"])
            # Ghi log lần bị chặn
            append_access_log(client_ip, sbd_clean, "Thất bại - Bị chặn bởi hệ thống bảo mật")
            return

        # 3. Thực hiện tra cứu
        with st.spinner("🔄 Đang tra cứu..."):
            result = lookup_score(ho_ten_clean, ngay_sinh_clean, sbd_clean)

        # 4. Xử lý kết quả
        if result["found"]:
            # Tra cứu thành công → ghi log và hiển thị
            append_access_log(client_ip, sbd_clean, "Thành công")
            st.success("✅ Tìm thấy thông tin thi sinh!")
            display_score_result(result["data"])
        else:
            # Không tìm thấy → ghi log thất bại
            append_access_log(client_ip, sbd_clean, "Thất bại - Không tìm thấy")
            st.error(
                "❌ Không tìm thấy thông tin thi sinh. "
                "Vui lòng kiểm tra lại Họ tên, Ngày sinh và Số báo danh."
            )
            # Đếm số lần thất bại để cảnh báo sớm
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
                    st.warning(
                        f"⚠️ Bạn còn **{remaining}** lần thử trước khi bị tạm khóa {LOCKOUT_MINUTES} phút."
                    )


# ── Footer ─────────────────────────────────────────────────────────────────
def render_footer():
    """Hiển thị footer thông tin."""
    st.markdown(
        """
        <div style="text-align:center; padding:32px 0 16px; color:rgba(201,168,76,0.3);
             font-size:0.72rem; letter-spacing:0.1em; text-transform:uppercase; font-family:'DM Sans',sans-serif;">
            🔒 Hệ thống được bảo vệ &nbsp;·&nbsp; Dữ liệu tra cứu được ghi lại
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__" or True:
    main()
    render_footer()
