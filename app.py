"""
================================================================================
  UNG DUNG TRA CUU DIEM THI - app.py
  Tra cuu bang: Ngay sinh + So bao danh (khong can nhap ten)
================================================================================
"""

import io
import re
import time
from datetime import datetime, timedelta

import gspread
import pandas as pd
import pytz
import qrcode
import streamlit as st
from google.oauth2.service_account import Credentials
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

st.set_page_config(
    page_title="Tra C\u1ee9u \u0110i\u1ec3m Thi",
    page_icon="\U0001f393",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    .stApp { background:#080b12; color:#f2f2f2; }
    #MainMenu, footer, header { visibility:hidden; }
    .block-container { max-width: 560px; padding-top: 2rem; }
    .top-bar { height:3px; background:linear-gradient(90deg, transparent, #e8c96d, transparent); margin-bottom:24px; }
    .title-main { text-align:center; color:#e8d5a3; margin:0; }
    .title-sub { text-align:center; color:rgba(232,213,163,0.6); margin-top:6px; }
    .lookup-card { border:1px solid rgba(184,146,42,.35); border-radius:16px; padding:20px; background:rgba(255,255,255,.03); }
    .card-hint { text-align:center; color:rgba(232,213,163,.7); }
    .result-box { border:1px solid rgba(184,146,42,.35); border-radius:16px; padding:16px; background:rgba(255,255,255,.03); margin-top:16px; }
    .total-value { font-size:2.2rem; color:#e8c96d; font-weight:700; text-align:center; }
</style>
""",
    unsafe_allow_html=True,
)

SHEET_DIEM_THI = "Diem_Thi"
SHEET_ACCESS_LOGS = "Access_Logs"
MAX_FAIL_ATTEMPTS = 5
LOCKOUT_MINUTES = 30
MAX_UNIQUE_SBD = 3

COL_HOTEN = "H\u1ecd v\u00e0 T\u00ean"
COL_DOB = "Ng\u00e0y sinh"
COL_SBD = "S\u1ed1 b\u00e1o danh"
COL_CN = "C\u00f4ng ngh\u1ec7"
COL_GDDP = "GD \u0110P"
LABEL_THI_SINH = "Th\u00ed sinh"


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


def check_release_time():
    vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
    now = datetime.now(vn_tz)
    release_time = (now + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
    remaining = int((release_time - now).total_seconds())
    if remaining > 0:
        return False, remaining, release_time
    return True, 0, release_time


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
        st.error(f"\u274c Kh\u00f4ng th\u1ec3 k\u1ebft n\u1ed1i Google Sheets. L\u1ed7i: {e}")
        return None


@st.cache_data(ttl=120)
def load_score_data() -> pd.DataFrame:
    spreadsheet = get_spreadsheet()
    if spreadsheet is None:
        return pd.DataFrame()
    try:
        ws = spreadsheet.worksheet(SHEET_DIEM_THI)
        records = ws.get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame()
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"\u274c Kh\u00f4ng t\u00ecm th\u1ea5y tab '{SHEET_DIEM_THI}'.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"\u274c L\u1ed7i \u0111\u1ecdc d\u1eef li\u1ec7u: {e}")
        return pd.DataFrame()


def load_access_logs() -> pd.DataFrame:
    spreadsheet = get_spreadsheet()
    if spreadsheet is None:
        return pd.DataFrame()
    try:
        ws = spreadsheet.worksheet(SHEET_ACCESS_LOGS)
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame(columns=["IP", "Th\u1eddi gian", "SBD_Tra_Cuu", "Tr\u1ea1ng th\u00e1i"])
        df = pd.DataFrame(records)
        df["Th\u1eddi gian"] = pd.to_datetime(df["Th\u1eddi gian"], errors="coerce")
        return df
    except gspread.exceptions.WorksheetNotFound:
        _create_access_log_sheet(spreadsheet)
        return pd.DataFrame(columns=["IP", "Th\u1eddi gian", "SBD_Tra_Cuu", "Tr\u1ea1ng th\u00e1i"])
    except Exception:
        return pd.DataFrame(columns=["IP", "Th\u1eddi gian", "SBD_Tra_Cuu", "Tr\u1ea1ng th\u00e1i"])


def _create_access_log_sheet(spreadsheet):
    try:
        ws = spreadsheet.add_worksheet(title=SHEET_ACCESS_LOGS, rows=10000, cols=4)
        ws.append_row(["IP", "Th\u1eddi gian", "SBD_Tra_Cuu", "Tr\u1ea1ng th\u00e1i"])
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
    except Exception:
        pass


def check_security(ip: str, sbd_dang_tra: str) -> dict:
    logs_df = load_access_logs()
    if logs_df.empty or "IP" not in logs_df.columns:
        return {"allowed": True, "reason": ""}

    ip_logs = logs_df[logs_df["IP"] == ip].copy()
    cutoff_time = datetime.now() - timedelta(minutes=LOCKOUT_MINUTES)
    recent_logs = ip_logs[ip_logs["Th\u1eddi gian"] >= cutoff_time]

    if "Tr\u1ea1ng th\u00e1i" in recent_logs.columns:
        fail_count = recent_logs[recent_logs["Tr\u1ea1ng th\u00e1i"].astype(str).str.contains("Th\u1ea5t b\u1ea1i", na=False)].shape[0]
        if fail_count >= MAX_FAIL_ATTEMPTS:
            return {"allowed": False, "reason": f"\U0001f512 B\u1ea1n \u0111\u00e3 nh\u1eadp sai qu\u00e1 nhi\u1ec1u l\u1ea7n ({fail_count} l\u1ea7n). Vui l\u00f2ng th\u1eed l\u1ea1i sau {LOCKOUT_MINUTES} ph\u00fat."}

    if "Tr\u1ea1ng th\u00e1i" in ip_logs.columns and "SBD_Tra_Cuu" in ip_logs.columns:
        success_logs = ip_logs[ip_logs["Tr\u1ea1ng th\u00e1i"].astype(str).str.contains("Th\u00e0nh c\u00f4ng", na=False)]
        unique_sbd = set(success_logs["SBD_Tra_Cuu"].astype(str).unique()) - {sbd_dang_tra}
        if len(unique_sbd) >= MAX_UNIQUE_SBD:
            return {"allowed": False, "reason": f"\U0001f6e1\ufe0f Thi\u1ebft b\u1ecb c\u1ee7a b\u1ea1n \u0111\u00e3 \u0111\u1ea1t gi\u1edbi h\u1ea1n tra c\u1ee9u. M\u1ed7i thi\u1ebft b\u1ecb ch\u1ec9 \u0111\u01b0\u1ee3c xem t\u1ed1i \u0111a {MAX_UNIQUE_SBD} th\u00ed sinh."}

    return {"allowed": True, "reason": ""}


def validate_sbd(sbd: str) -> bool:
    return bool(re.fullmatch(r"\d{6}", sbd.strip()))


def lookup_score(ngay_sinh: str, sbd: str) -> dict:
    df = load_score_data()
    if df.empty:
        st.error("\u274c Kh\u00f4ng t\u1ea3i \u0111\u01b0\u1ee3c d\u1eef li\u1ec7u \u0111i\u1ec3m thi t\u1eeb Google Sheets.")
        return {"found": False, "data": None}

    sbd_input = str(sbd).strip()
    df["_sbd"] = df[COL_SBD].astype(str).str.strip().str.zfill(6)

    def normalize_dob(date_val):
        if pd.isna(date_val) or str(date_val).strip() == "":
            return None
        try:
            return pd.to_datetime(date_val, dayfirst=True, errors="coerce").strftime("%d/%m/%Y")
        except Exception:
            return None

    df["_ngay_sinh"] = df[COL_DOB].apply(normalize_dob)

    try:
        input_date = pd.to_datetime(ngay_sinh, dayfirst=True, errors="coerce").strftime("%d/%m/%Y")
        if pd.isna(input_date):
            st.error("\u274c Ng\u00e0y sinh nh\u1eadp kh\u00f4ng \u0111\u00fang \u0111\u1ecbnh d\u1ea1ng (DD/MM/YYYY)")
            return {"found": False, "data": None}
    except Exception:
        st.error("\u274c Ng\u00e0y sinh nh\u1eadp kh\u00f4ng \u0111\u00fang \u0111\u1ecbnh d\u1ea1ng.")
        return {"found": False, "data": None}

    matched = df[(df["_sbd"] == sbd_input) & (df["_ngay_sinh"] == input_date)]
    if matched.empty:
        return {"found": False, "data": None}

    row = matched.iloc[0]
    return {
        "found": True,
        "data": {
            COL_HOTEN: str(row.get(COL_HOTEN, "")).strip(),
            COL_DOB: str(row.get(COL_DOB, "")).strip(),
            COL_SBD: str(row.get(COL_SBD, "")).strip(),
            COL_CN: row.get(COL_CN, "N/A"),
            COL_GDDP: row.get(COL_GDDP, "N/A"),
        },
    }


def generate_qr(data):
    def parse(val):
        try:
            return float(val) / 100
        except Exception:
            return 0.0

    diem_cn = parse(data.get(COL_CN))
    diem_gd = parse(data.get(COL_GDDP))
    tong_diem = diem_cn + diem_gd

    qr_data = (
        f"SBD:{data.get(COL_SBD, '')}|"
        f"DOB:{data.get(COL_DOB, '')}|"
        f"CONG_NGHE:{diem_cn:.2f}|"
        f"GD_DP:{diem_gd:.2f}|"
        f"TOTAL:{tong_diem:.2f}"
    )

    qr = qrcode.make(qr_data)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    return buf


def generate_pdf(data):
    try:
        diem_cn = float(data.get(COL_CN, 0))
        diem_gd = float(data.get(COL_GDDP, 0))
        tong_diem = diem_cn + diem_gd
    except Exception:
        tong_diem = 0.0

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = [
        Paragraph("B\u1ea2NG \u0110I\u1ec2M TH\u00cd SINH", styles["Title"]),
        Spacer(1, 20),
        Paragraph(f"{COL_HOTEN}: {data.get(COL_HOTEN, '')}", styles["Normal"]),
        Spacer(1, 8),
        Paragraph(f"{COL_DOB}: {data.get(COL_DOB, '')}", styles["Normal"]),
        Spacer(1, 8),
        Paragraph(f"{COL_SBD}: {data.get(COL_SBD, '')}", styles["Normal"]),
        Spacer(1, 8),
        Paragraph(f"{COL_CN}: {data.get(COL_CN, 'N/A')}", styles["Normal"]),
        Spacer(1, 8),
        Paragraph(f"{COL_GDDP}: {data.get(COL_GDDP, 'N/A')}", styles["Normal"]),
        Spacer(1, 8),
        Paragraph(f"T\u1ed5ng \u0111i\u1ec3m: {tong_diem} / 20.0", styles["Normal"]),
    ]

    doc.build(content)
    buffer.seek(0)
    return buffer


def display_score_result(data: dict):
    def parse_diem(val):
        if val is None or str(val).strip() == "":
            return None
        try:
            return float(val) / 100
        except Exception:
            return None

    diem_cn = parse_diem(data.get(COL_CN))
    diem_gd = parse_diem(data.get(COL_GDDP))
    tong_diem = sum([d for d in [diem_cn, diem_gd] if d is not None])
    tong_str = f"{tong_diem:.2f}"

    now_vn = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).strftime("%H:%M:%S - %d/%m/%Y")

    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    st.markdown(f"**\U0001f393 {data.get(COL_HOTEN, LABEL_THI_SINH)}**")
    st.markdown(f"\U0001f4c5 {data.get(COL_DOB, '')}  |  \U0001f522 SBD: **{data.get(COL_SBD, '')}**")

    c1, c2 = st.columns(2)
    c1.metric("\U0001f4d8 C\u00d4NG NGH\u1ec6", f"{diem_cn:.2f}" if diem_cn is not None else "Ch\u01b0a c\u00f3")
    c2.metric("\U0001f4d6 GI\u00c1O D\u1ee4C \u0110\u1ecaA PH\u01af\u01a0NG", f"{diem_gd:.2f}" if diem_gd is not None else "Ch\u01b0a c\u00f3")

    st.markdown(f"<div class='total-value'>\U0001f3c6 {tong_str}</div>", unsafe_allow_html=True)
    st.caption(f"Tra c\u1ee9u th\u00e0nh c\u00f4ng - {now_vn}")
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    is_open, remaining, release_time = check_release_time()

    if not is_open:
        release_label = release_time.strftime("%H:%M %d/%m/%Y")
        st.markdown("## \u23f3 H\u1ec7 th\u1ed1ng \u0111ang t\u1ea1m \u0111\u00f3ng")
        placeholder = st.empty()
        while remaining > 0:
            mins, secs = divmod(remaining, 60)
            hours, mins = divmod(mins, 60)
            placeholder.markdown(
                f"""
                <div class='lookup-card'>
                  <h3 style='text-align:center'>\u23f3 \u0110\u1ebfm ng\u01b0\u1ee3c c\u00f4ng b\u1ed1 k\u1ebft qu\u1ea3</h3>
                  <div style='text-align:center;font-size:2rem;font-weight:700'>{hours:02d}:{mins:02d}:{secs:02d}</div>
                  <p style='text-align:center'>C\u00f4ng b\u1ed1 \u0111i\u1ec3m t\u1ed5ng k\u1ebft HK2 v\u00e0 \u0111i\u1ec3m TBM C\u00f4ng ngh\u1ec7 l\u00fac <b>{release_label}</b>.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            time.sleep(1)
            remaining -= 1
        st.rerun()

    client_ip = get_client_ip()

    st.markdown('<div class="top-bar"></div>', unsafe_allow_html=True)
    st.markdown("<h1 class='title-main'>Tra C\u1ee9u \u0110i\u1ec3m Thi</h1>", unsafe_allow_html=True)
    st.markdown("<p class='title-sub'>H\u1ec7 th\u1ed1ng tra c\u1ee9u k\u1ebft qu\u1ea3 k\u1ef3 thi</p>", unsafe_allow_html=True)

    pre_check = check_security(client_ip, sbd_dang_tra="__pre_check__")
    if not pre_check["allowed"] and "nh\u1eadp sai qu\u00e1 nhi\u1ec1u" in pre_check["reason"]:
        st.error(pre_check["reason"])
        return

    st.markdown("<div class='lookup-card'>", unsafe_allow_html=True)
    st.markdown("<p class='card-hint'>Nh\u1eadp th\u00f4ng tin b\u00ean d\u01b0\u1edbi \u0111\u1ec3 xem \u0111i\u1ec3m c\u1ee7a b\u1ea1n</p>", unsafe_allow_html=True)

    with st.form("lookup_form", clear_on_submit=False):
        ngay_sinh_input = st.text_input("\U0001f4c5 Ng\u00e0y sinh", placeholder="VD: 15/08/2007", help="\u0110\u1ecbnh d\u1ea1ng: DD/MM/YYYY")
        sbd_input = st.text_input("\U0001f522 S\u1ed1 b\u00e1o danh", placeholder="VD: 012345", max_chars=6, help="\u0110\u00fang 6 ch\u1eef s\u1ed1")
        submitted = st.form_submit_button("\U0001f50d Xem k\u1ebft qu\u1ea3")

    st.markdown("</div>", unsafe_allow_html=True)

    if not submitted:
        return

    errors = []
    if not ngay_sinh_input.strip():
        errors.append("Vui l\u00f2ng nh\u1eadp **Ng\u00e0y sinh**.")
    if not sbd_input.strip():
        errors.append("Vui l\u00f2ng nh\u1eadp **S\u1ed1 b\u00e1o danh**.")
    elif not validate_sbd(sbd_input):
        errors.append("**S\u1ed1 b\u00e1o danh** ph\u1ea3i \u0111\u00fang **6 ch\u1eef s\u1ed1** - v\u00ed d\u1ee5: `012345`.")

    if errors:
        for err in errors:
            st.warning(f"\u26a0\ufe0f {err}")
        return

    sbd_clean = sbd_input.strip()
    ngay_sinh_clean = ngay_sinh_input.strip()

    security_check = check_security(client_ip, sbd_dang_tra=sbd_clean)
    if not security_check["allowed"]:
        st.error(security_check["reason"])
        append_access_log(client_ip, sbd_clean, "Th\u1ea5t b\u1ea1i - B\u1ecb ch\u1eb7n b\u1ea3o m\u1eadt")
        return

    with st.spinner("\u0110ang tra c\u1ee9u..."):
        result = lookup_score(ngay_sinh_clean, sbd_clean)

    if not result["found"]:
        append_access_log(client_ip, sbd_clean, "Th\u1ea5t b\u1ea1i - Kh\u00f4ng t\u00ecm th\u1ea5y")
        st.error("\u274c Kh\u00f4ng t\u00ecm th\u1ea5y th\u00f4ng tin. Vui l\u00f2ng ki\u1ec3m tra l\u1ea1i Ng\u00e0y sinh v\u00e0 S\u1ed1 b\u00e1o danh.")
        return

    append_access_log(client_ip, sbd_clean, "Th\u00e0nh c\u00f4ng")
    st.success("\u2705 T\u00ecm th\u1ea5y k\u1ebft qu\u1ea3 thi!")
    data = result["data"]
    display_score_result(data)

    try:
        tbm_cn = float(data.get(COL_CN, 0)) / 100
    except Exception:
        tbm_cn = 0.0

    st.info("\U0001f4e2 Th\u00f4ng b\u00e1o: \u0110\u00e3 c\u00f4ng b\u1ed1 \u0111i\u1ec3m t\u1ed5ng k\u1ebft HK2 v\u00e0 \u0111i\u1ec3m TBM C\u00f4ng ngh\u1ec7.")
    if tbm_cn > 5:
        st.balloons()
        st.success(f"\U0001f386 Ch\u00fac m\u1eebng SBD {data.get(COL_SBD, '')}! TBM C\u00f4ng ngh\u1ec7 \u0111\u1ea1t {tbm_cn:.2f} (> 5).")
        st.markdown(
            "### L\u1eddi ch\u00fac\n"
            "Xin ch\u00fac m\u1eebng em \u0111\u00e3 ho\u00e0n th\u00e0nh ch\u01b0\u01a1ng tr\u00ecnh l\u1edbp 9. "
            "Ch\u00fac em v\u1eefng tin, tr\u00e2n tr\u1ecdng h\u00e0nh tr\u00ecnh \u0111\u00e3 qua, "
            "v\u00e0 s\u1eb5n s\u00e0ng cho m\u1ed9t t\u01b0\u01a1ng lai t\u1ed1t \u0111\u1eb9p nh\u1ea5t."
        )

    st.markdown("### \U0001f510 M\u00e3 x\u00e1c th\u1ef1c")
    st.image(generate_qr(data))

    pdf = generate_pdf(data)
    st.download_button(
        label="\U0001f4c4 T\u1ea3i b\u1ea3ng \u0111i\u1ec3m PDF",
        data=pdf,
        file_name=f"bang_diem_{data.get(COL_SBD, 'khong_ro')}.pdf",
        mime="application/pdf",
    )


def render_footer():
    st.markdown(
        """
        <div class="app-footer">
            \U0001f512 H\u1ec7 th\u1ed1ng \u0111\u01b0\u1ee3c b\u1ea3o v\u1ec7 &nbsp;\u00b7&nbsp; M\u1ecdi truy c\u1eadp \u0111\u1ec1u \u0111\u01b0\u1ee3c ghi l\u1ea1i
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__" or True:
    main()
    render_footer()
