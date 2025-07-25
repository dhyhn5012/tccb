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

# --- FORM NHẬP LIỆU ---
# Sử dụng st.form để nhóm các input và xử lý khi submit một lần
with st.form("employee_form", clear_on_submit=True): # clear_on_submit=True sẽ xóa nội dung form sau khi gửi
    st.subheader("I. Thông tin cá nhân")
    ho_ten = st.text_input("Họ và tên", placeholder="Nguyễn Văn A")
    tuoi = st.number_input("Tuổi", min_value=18, max_value=70, step=1)
    khoa_phong = st.selectbox("Khoa/Phòng/Trung tâm", options=KHOA_PHONG_OPTIONS)
    chuc_danh = st.selectbox("Chức danh", options=CHUC_DANH_OPTIONS)
    trang_thai = st.selectbox("Trạng thái cập nhật hồ sơ", options=TRANG_THAI_OPTIONS, help="Vui lòng chọn trạng thái hoàn thành hồ sơ của bạn.")

    submitted = st.form_submit_button("✅ Gửi thông tin")

if submitted:
    # Validate input: Kiểm tra xem trường Họ và tên có rỗng không
    if not ho_ten:
        st.warning("Vui lòng nhập Họ và tên.")
    else:
        with st.spinner("Đang lưu thông tin..."): # Hiển thị spinner khi đang xử lý
            success = save_employee_data(ho_ten, tuoi, khoa_phong, chuc_danh, trang_thai)
            if success:
                st.success("Cảm ơn bạn! Thông tin đã được ghi nhận thành công.")
                # Xóa cache của get_all_data để dashboard cập nhật ngay lập tức với dữ liệu mới
                st.cache_data.clear()
            else:
                st.error("Đã có lỗi xảy ra. Vui lòng thử lại.")

st.markdown("---") # Đường phân cách

# --- DASHBOARD VÀ BÁO CÁO (DÀNH CHO QUẢN LÝ) ---
st.header("📊 Dashboard và Báo cáo Tổng hợp")
all_data = get_all_data() # Lấy toàn bộ dữ liệu từ CSDL

if all_data.empty:
    st.info("Chưa có dữ liệu nào được ghi nhận.")
else:
    st.subheader("Tải Báo cáo")
    excel_data = create_excel_report(all_data) # Tạo file Excel trong bộ nhớ
    st.download_button(
        label="📥 Tải xuống file Excel",
        data=excel_data,
        file_name=f"BaoCaoNhanSu_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx", # Tên file có timestamp
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" # Kiểu MIME cho file Excel
    )

    st.subheader("Biểu đồ Trực quan")
    col1, col2 = st.columns(2) # Chia layout thành 2 cột để hiển thị biểu đồ
    with col1:
        # Hiển thị biểu đồ tròn trạng thái
        st.plotly_chart(plot_status_pie(all_data), use_container_width=True)
        # Hiển thị biểu đồ cột theo khoa/phòng
        st.plotly_chart(plot_department_bar(all_data), use_container_width=True)
    with col2:
        # Hiển thị biểu đồ histogram độ tuổi
        st.plotly_chart(plot_age_histogram(all_data), use_container_width=True)
        # Hiển thị biểu đồ cột theo chức danh
        st.plotly_chart(plot_title_bar(all_data), use_container_width=True)

    st.subheader("Xem Dữ liệu Thô")
    with st.expander("Nhấn để xem bảng dữ liệu chi tiết"): # Tạo một expander để ẩn/hiện bảng dữ liệu
        st.dataframe(all_data) # Hiển thị DataFrame dưới dạng bảng

st.markdown("---") # Đường phân cách

# --- FORM HỖ TRỢ ---
st.header("💬 Yêu cầu Hỗ trợ")
with st.form("support_form", clear_on_submit=True):
    noi_dung_ho_tro = st.text_area("Nếu bạn có thắc mắc hoặc cần hỗ trợ, vui lòng nhập nội dung vào đây:")
    submit_request = st.form_submit_button("Gửi yêu cầu")

if submit_request and noi_dung_ho_tro: # Kiểm tra nếu nút được nhấn và nội dung không rỗng
    with st.spinner("Đang gửi yêu cầu..."):
        success = save_support_request(noi_dung_ho_tro)
        if success:
            st.success("Yêu cầu của bạn đã được gửi. Chúng tôi sẽ phản hồi sớm nhất có thể.")
        else:
            st.error("Không thể gửi yêu cầu. Vui lòng thử lại.")
elif submit_request: # Nếu nút được nhấn nhưng nội dung rỗng
    st.warning("Vui lòng nhập nội dung yêu cầu.")
