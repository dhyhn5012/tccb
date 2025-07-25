# Hướng dẫn tạo cấu trúc thư mục và file:
# employee_profile_app/
# ├── main.py
# ├── pages/
# │   └── 1_Cap_nhat_Ho_so.py
# ├── utils/
# │   ├── database.py
# │   └── helpers.py
# ├── assets/
# │   └── hospital_logo.png (Tùy chọn, không bắt buộc cho mã này)
# ├── .streamlit/
# │   └── config.toml
# └── requirements.txt

# --- requirements.txt ---
# streamlit
# pandas
# plotly
# openpyxl

# --- .streamlit/config.toml ---
# [theme]
# base="light"
# primaryColor="#1E90FF" # Royal Blue
# backgroundColor="#F0F8FF" # Alice Blue
# secondaryBackgroundColor="#FFFFFF"
# font="sans serif"

# --- utils/database.py ---
import streamlit as st
import pandas as pd
import io

# --- Cấu hình trang (Page Configuration) ---
import streamlit as st

DB_NAME = "employee_data.db"

# Sử dụng cache_resource để kết nối CSDL chỉ một lần
@st.cache_resource
def get_db_connection():
    """Tạo và trả về một kết nối tới CSDL SQLite."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def init_db():
    """Khởi tạo các bảng trong CSDL nếu chúng chưa tồn tại."""
    conn = get_db_connection()
    c = conn.cursor()
    # Bảng lưu thông tin nhân viên
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ho_ten TEXT NOT NULL,
            tuoi INTEGER NOT NULL,
            khoa_phong TEXT NOT NULL,
            chuc_danh TEXT NOT NULL,
            trang_thai TEXT NOT NULL,
            thoi_gian_cap_nhat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Bảng lưu các yêu cầu hỗ trợ
    c.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            noi_dung TEXT NOT NULL,
            thoi_gian_gui TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

def save_employee_data(ho_ten, tuoi, khoa_phong, chuc_danh, trang_thai):
    """Lưu thông tin nhân viên vào CSDL."""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO employees (ho_ten, tuoi, khoa_phong, chuc_danh, trang_thai)
            VALUES (?, ?, ?, ?, ?)
        ''', (ho_ten, tuoi, khoa_phong, chuc_danh, trang_thai))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Lỗi CSDL: {e}")
        return False

def save_support_request(noi_dung):
    """Lưu yêu cầu hỗ trợ vào CSDL."""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO requests (noi_dung) VALUES (?)', (noi_dung,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Lỗi CSDL: {e}")
        return False

@st.cache_data(ttl=600)  # Cache dữ liệu trong 10 phút
def get_all_data():
    """Lấy toàn bộ dữ liệu nhân viên từ CSDL và trả về dưới dạng DataFrame."""
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT ho_ten, tuoi, khoa_phong, chuc_danh, trang_thai, thoi_gian_cap_nhat FROM employees", conn)
        return df
    except Exception as e:
        st.error(f"Không thể tải dữ liệu: {e}")
        return pd.DataFrame()

# --- utils/helpers.py ---
import pandas as pd
import plotly.express as px
from io import BytesIO

def create_excel_report(df: pd.DataFrame):
    """Chuyển đổi DataFrame thành file Excel trong bộ nhớ."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='BaoCaoNhanSu')
    processed_data = output.getvalue()
    return processed_data

def plot_status_pie(df: pd.DataFrame):
    """Vẽ biểu đồ tròn thể hiện tỷ lệ trạng thái."""
    if df.empty or 'trang_thai' not in df.columns:
        return None
    status_counts = df['trang_thai'].value_counts().reset_index()
    status_counts.columns = ['Trạng thái', 'Số lượng']
    fig = px.pie(status_counts, names='Trạng thái', values='Số lượng',
                 title='Tỷ lệ Trạng thái Cập nhật Hồ sơ', hole=.3)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def plot_department_bar(df: pd.DataFrame):
    """Vẽ biểu đồ cột thể hiện số lượng nhân viên theo khoa/phòng."""
    if df.empty or 'khoa_phong' not in df.columns:
        return None
    dept_counts = df['khoa_phong'].value_counts().reset_index()
    dept_counts.columns = ['Khoa/Phòng', 'Số lượng']
    fig = px.bar(dept_counts, x='Khoa/Phòng', y='Số lượng',
                 title='Thống kê theo Khoa/Phòng/Trung tâm', text_auto=True)
    return fig

def plot_title_bar(df: pd.DataFrame):
    """Vẽ biểu đồ cột thể hiện số lượng nhân viên theo chức danh."""
    if df.empty or 'chuc_danh' not in df.columns:
        return None
    title_counts = df['chuc_danh'].value_counts().reset_index()
    title_counts.columns = ['Chức danh', 'Số lượng']
    fig = px.bar(title_counts, x='Chức danh', y='Số lượng',
                 title='Thống kê theo Chức danh', text_auto=True)
    return fig

def plot_age_histogram(df: pd.DataFrame):
    """Vẽ biểu đồ histogram phân bổ độ tuổi."""
    if df.empty or 'tuoi' not in df.columns:
        return None
    fig = px.histogram(df, x='tuoi', nbins=10,
                       title='Phân bổ Độ tuổi Nhân viên')
    return fig

# --- main.py ---
import streamlit as st
from utils.database import init_db

# Thiết lập cấu hình trang
st.set_page_config(
    page_title="Hệ thống Cập nhật Hồ sơ Nhân viên",
    page_icon="🏥",
    layout="wide"
)

# Khởi tạo CSDL khi ứng dụng khởi động lần đầu
init_db()

# Giao diện trang chủ
st.title("🏥 Chào mừng đến với Hệ thống Cập nhật Hồ sơ Nhân viên")
st.markdown("---")
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

# --- pages/1_Cap_nhat_Ho_so.py ---
import streamlit as st
import pandas as pd
from utils.database import save_employee_data, get_all_data, save_support_request
from utils.helpers import (
    create_excel_report,
    plot_status_pie,
    plot_department_bar,
    plot_title_bar,
    plot_age_histogram
)

st.set_page_config(page_title="Cập nhật & Báo cáo", page_icon="📝")

st.title("📝 Mẫu Cập nhật Thông tin Hồ sơ Nhân viên")

# --- DANH MỤC LỰA CHỌN (có thể lấy từ CSDL hoặc file cấu hình) ---
KHOA_PHONG_OPTIONS = ["Khoa Nội", "Khoa Ngoại", "Khoa Sản", "Khoa Nhi", "Trung tâm Xét nghiệm", "Phòng Hành chính"]
CHUC_DANH_OPTIONS = ["Bác sĩ", "Điều dưỡng", "Kỹ thuật viên", "Dược sĩ", "Nhân viên Hành chính", "Lãnh đạo khoa"]
TRANG_THAI_OPTIONS = ["Hoàn tất", "1 phần", "Chưa bắt đầu"]

# --- FORM NHẬP LIỆU ---
with st.form("employee_form", clear_on_submit=True):
    st.subheader("I. Thông tin cá nhân")
    ho_ten = st.text_input("Họ và tên", placeholder="Nguyễn Văn A")
    tuoi = st.number_input("Tuổi", min_value=18, max_value=70, step=1)
    khoa_phong = st.selectbox("Khoa/Phòng/Trung tâm", options=KHOA_PHONG_OPTIONS)
    chuc_danh = st.selectbox("Chức danh", options=CHUC_DANH_OPTIONS)
    trang_thai = st.selectbox("Trạng thái cập nhật hồ sơ", options=TRANG_THAI_OPTIONS, help="Vui lòng chọn trạng thái hoàn thành hồ sơ của bạn.")

    submitted = st.form_submit_button("✅ Gửi thông tin")

if submitted:
    # Validate input
    if not ho_ten:
        st.warning("Vui lòng nhập Họ và tên.")
    else:
        with st.spinner("Đang lưu thông tin..."):
            success = save_employee_data(ho_ten, tuoi, khoa_phong, chuc_danh, trang_thai)
            if success:
                st.success("Cảm ơn bạn! Thông tin đã được ghi nhận thành công.")
                # Xóa cache để dashboard cập nhật ngay lập tức
                st.cache_data.clear()
            else:
                st.error("Đã có lỗi xảy ra. Vui lòng thử lại.")

st.markdown("---")

# --- DASHBOARD VÀ BÁO CÁO (DÀNH CHO QUẢN LÝ) ---
st.header("📊 Dashboard và Báo cáo Tổng hợp")
all_data = get_all_data()

if all_data.empty:
    st.info("Chưa có dữ liệu nào được ghi nhận.")
else:
    st.subheader("Tải Báo cáo")
    excel_data = create_excel_report(all_data)
    st.download_button(
        label="📥 Tải xuống file Excel",
        data=excel_data,
        file_name=f"BaoCaoNhanSu_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.subheader("Biểu đồ Trực quan")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_status_pie(all_data), use_container_width=True)
        st.plotly_chart(plot_department_bar(all_data), use_container_width=True)
    with col2:
        st.plotly_chart(plot_age_histogram(all_data), use_container_width=True)
        st.plotly_chart(plot_title_bar(all_data), use_container_width=True)

    st.subheader("Xem Dữ liệu Thô")
    with st.expander("Nhấn để xem bảng dữ liệu chi tiết"):
        st.dataframe(all_data)

st.markdown("---")

# --- FORM HỖ TRỢ ---
st.header("💬 Yêu cầu Hỗ trợ")
with st.form("support_form", clear_on_submit=True):
    noi_dung_ho_tro = st.text_area("Nếu bạn có thắc mắc hoặc cần hỗ trợ, vui lòng nhập nội dung vào đây:")
    submit_request = st.form_submit_button("Gửi yêu cầu")

if submit_request and noi_dung_ho_tro:
    with st.spinner("Đang gửi yêu cầu..."):
        success = save_support_request(noi_dung_ho_tro)
        if success:
            st.success("Yêu cầu của bạn đã được gửi. Chúng tôi sẽ phản hồi sớm nhất có thể.")
        else:
            st.error("Không thể gửi yêu cầu. Vui lòng thử lại.")
elif submit_request:
    st.warning("Vui lòng nhập nội dung yêu cầu.")
