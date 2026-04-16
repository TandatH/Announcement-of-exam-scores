"""
================================================================================
  ỨNG DỤNG TRA CỨU ĐIỂM THI - app.py
  + Hiển thị từng điểm môn riêng + Fix tổng điểm + Cải thiện lấy vị trí IP
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ============================================================
# CẤU HÌNH TRANG & CSS (giữ nguyên như cũ)
# ============================================================
st.set_page_config(page_title="Tra Cứu Điểm Thi", page_icon="🎓", layout="centered")

# ... (Giữ nguyên toàn bộ khối <style> CSS của bạn - quá dài nên mình bỏ qua ở đây, bạn copy nguyên từ code cũ)

# ============================================================
# HẰNG SỐ
# ============================================================
SHEET_DIEM_THI    = "Diem_Thi"
SHEET_ACCESS_LOGS = "Access_Logs"
MAX_FAIL_ATTEMPTS = 5
LOCKOUT_MINUTES   = 30
MAX_UNIQUE_SBD    = 3

# ============================================================
# IP & GEOLOCATION (CẢI THIỆN)
# ============================================================
def get_client_ip() -> str:
    try:
        headers = st.context.headers
        # Ưu tiên các header phổ biến trên Cloud / Proxy
        for h in ["CF-Connecting-IP", "X-Forwarded-For", "X-Real-Ip", "Forwarded"]:
            val = headers.get(h, "")
            if val:
                ip = val.split(",")[0].strip()
                if ip and not ip.startswith("192.168.") and not ip.startswith("10.") and not ip.startswith("172.16."):
                    return ip
        # Fallback
        return headers.get("X-Forwarded-For", "unknown").split(",")[0].strip()
    except:
        return "unknown"


@st.cache_data(ttl=3600)
def get_ip_location(ip: str) -> dict:
    if ip in ["unknown", "127.0.0.1", "::1", "localhost"] or ip.startswith(("192.168.", "10.", "172.16.")):
        return {"country": "Unknown", "country_code": "", "region": "", "city": "Unknown/Local", "isp": "Unknown"}
    
    try:
        response = requests.get(f"https://freeipapi.com/api/json/{ip}", timeout=6)
        if response.status_code == 200:
            data = response.json()
            return {
                "country": data.get("countryName", "Unknown"),
                "country_code": data.get("countryCode", ""),
                "region": data.get("regionName", ""),
                "city": data.get("cityName", "Unknown"),
                "isp": data.get("isp", "Unknown")
            }
    except:
        pass
    return {"country": "Unknown", "country_code": "", "region": "", "city": "Unknown", "isp": "Unknown"}


# ============================================================
# Các hàm Google Sheets, Access Logs, check_security... (giữ nguyên như code trước)
# ... (bạn copy nguyên từ phiên bản trước)

# ============================================================
# HIỂN THỊ KẾT QUẢ (ĐÃ CẢI THIỆN - HIỂN THỊ TỪNG ĐIỂM RIÊNG)
# ============================================================
def display_score_result(data: dict):
    # Fix lấy điểm an toàn
    try:
        diem_cn = float(data.get("Công nghệ") or 0)
        diem_gd = float(data.get("GD ĐP") or 0)
        tong_diem = diem_cn + diem_gd
    except:
        diem_cn = 0.0
        diem_gd = 0.0
        tong_diem = 0.0

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
        st.metric(label="Công nghệ", value=f"{diem_cn:.1f}")
    with col2:
        st.metric(label="GD ĐP", value=f"{diem_gd:.1f}")

    # Tổng điểm
    st.markdown(f"""
    <div class="total-box" style="margin-top: 24px;">
        <div class="total-label">🏆 TỔNG ĐIỂM</div>
        <div class="total-value" style="font-size: 3.8rem;">{tong_diem:.1f}</div>
        <div class="total-max" style="font-size: 1.1rem; margin-top: 8px;">/ 20.0 điểm</div>
    </div>
    <div class="timestamp-line">
        ✓ Tra cứu thành công · {datetime.now().strftime("%H:%M:%S — %d/%m/%Y")}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)


# ============================================================
# MAIN (Phần hiển thị vị trí giữ nguyên, chỉ cải thiện IP)
# ============================================================
def main():
    client_ip = get_client_ip()

    # ... (phần đầu trang giữ nguyên)

    if submitted:
        # ... (phần kiểm tra lỗi và security giữ nguyên)

        if result["found"]:
            append_access_log(client_ip, sbd_clean, "Thành công")
            st.success("✅ Tìm thấy kết quả thi!")
            display_score_result(result["data"])
            data = result["data"]

            # Thông tin truy cập
            loc = get_ip_location(client_ip)
            with st.expander("📍 Thông tin truy cập (Admin only)", expanded=True):   # expanded=True để dễ thấy
                st.write(f"**IP:** {client_ip}")
                st.write(f"**Quốc gia:** {loc.get('country')} ({loc.get('country_code')})")
                st.write(f"**Thành phố:** {loc.get('city')}")
                st.write(f"**Vùng:** {loc.get('region')}")
                st.write(f"**ISP:** {loc.get('isp')}")

            # QR và PDF giữ nguyên
            st.markdown("### 🔐 Mã xác thực")
            qr_img = generate_qr(data)
            st.image(qr_img, use_column_width=True)

            pdf = generate_pdf(data)
            sbd_safe = data.get("Số báo danh", "unknown").strip()
            st.download_button(
                label="📄 Tải bảng điểm PDF",
                data=pdf,
                file_name=f"bang_diem_{sbd_safe}.pdf",
                mime="application/pdf"
            )

        # ... (phần else giữ nguyên)

# Cuối file
if __name__ == "__main__" or True:
    main()
    render_footer()
