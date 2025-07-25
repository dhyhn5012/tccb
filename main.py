import streamlit as st
import pandas as pd
# Import các hàm tương tác CSDL từ module database
from utils.database import save_employee_data, get_all_data, save_support_request
# Import các hàm vẽ biểu đồ và tạo báo cáo từ module helpers
from utils.helpers import (
    create_excel_report,
    plot_status_pie,
    plot_department_bar,
    plot_title_bar,
    plot_age_histogram
)

# Thiết lập cấu hình trang cụ thể cho trang này
st.set_page_config(page_title="Cập nhật & Báo cáo", page_icon="📝")

st.title("📝 Mẫu Cập nhật Thông tin Hồ sơ Nhân viên")

# --- DANH MỤC LỰA CHỌN (có thể được lấy từ CSDL hoặc file cấu hình lớn hơn trong thực tế) ---
KHOA_PHONG_OPTIONS = ["Khoa Nội", "Khoa Ngoại", "Khoa Sản", "Khoa Nhi", "Trung tâm Xét nghiệm", "Phòng Hành chính"]
CHUC_DANH_OPTIONS = ["Bác sĩ", "Điều dưỡng", "Kỹ thuật viên", "Dược sĩ", "Nhân viên Hành chính", "Lãnh đạo khoa"]
TRANG_THAI_OPTIONS = ["Hoàn tất", "1 phần", "Chưa bắt đầu"]

