import streamlit as st
from utils.database import init_db # Import hàm khởi tạo CSDL từ module database

# Thiết lập cấu hình trang cho toàn bộ ứng dụng
st.set_page_config(
    page_title="Hệ thống Cập nhật Hồ sơ Nhân viên", # Tiêu đề hiển thị trên tab trình duyệt
    page_icon="🏥", # Biểu tượng trên tab trình duyệt
    layout="wide" # Bố cục trang rộng hơn để tận dụng không gian
)

# Khởi tạo CSDL khi ứng dụng khởi động lần đầu tiên
# Hàm này sẽ tạo các bảng nếu chúng chưa tồn tại
init_db()

# Giao diện trang chủ
st.title("🏥 Chào mừng đến với Hệ thống Cập nhật Hồ sơ Nhân viên")
st.markdown("---") # Đường phân cách

st.info(
    """
    **Hướng dẫn sử dụng:**

    1.  Vui lòng di chuyển đến trang **Cập nhật Hồ sơ** ở thanh công cụ bên trái.
    2.  Điền đầy đủ và chính xác các thông tin cá nhân vào biểu mẫu.
    3.  Nhấn nút **"Gửi thông tin"** để hoàn tất.
    4.  Người quản lý có thể xem các báo cáo trực quan và tải dữ liệu tổng hợp tại cùng trang đó.
    5.  Nếu có thắc mắc, vui lòng sử dụng mục **"Yêu cầu Hỗ trợ"** ở cuối trang.

    *Trân trọng cảm ơn sự hợp tác của bạn!*
    """
)
