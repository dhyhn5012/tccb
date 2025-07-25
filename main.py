import streamlit as st
import pandas as pd
import io

# --- Page Configuration ---
st.set_page_config(
    page_title="Hệ Thống Quản Lý Lịch Trực Bệnh Viện",
    # page_icon="🏥", # Bạn có thể bỏ ghi chú nếu muốn có icon
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- App Title and Description ---
st.title("🏥 Hệ Thống Quản Lý Lịch Trực Bệnh Viện")
st.markdown("""
Chào mừng bạn đến với trang web tổng hợp thông tin trực của bệnh viện.
Ứng dụng này cho phép bạn tải lên một tệp Excel hoặc CSV chứa lịch trực, sau đó thống kê và lọc thông tin theo các tiêu chí khác nhau.

**Hướng dẫn sử dụng:**
1.  Tải lên tệp Excel (.xlsx, .xls) hoặc CSV (.csv) của bạn bằng cách sử dụng nút 'Tải lên tệp' ở thanh bên trái.
2.  Đảm bảo tệp của bạn có cấu trúc như sau:
    * **Đối với Excel (.xlsx, .xls):** Tệp nên có thông tin 'Bộ phận' hoặc 'Đơn vị' ở các dòng đầu tiên (để xác định khoa), và dữ liệu nhân viên/lịch trực bắt đầu từ dòng có tiêu đề 'STT', 'Họ và tên' và dòng tiếp theo là các ngày tháng.
    * **Đối với CSV (.csv):** Tệp nên có thông tin 'Bộ phận' ở các dòng đầu tiên (để xác định khoa), và dữ liệu nhân viên/lịch trực bắt đầu từ dòng có tiêu đề 'STT', 'Họ và tên' và dòng tiếp theo là các ngày tháng.
    * Các ký hiệu trực ví dụ: 'X' (trực thường), 'Tr' (trực), 'NP' (nghỉ phép), 'TS' (thai sản), 'CN' (trực Chủ Nhật), 'T7' (trực Thứ Bảy).
3.  Sau khi tải lên, bạn có thể xem tổng quan dữ liệu và sử dụng các bộ lọc, thống kê ở dưới.
""")

# --- Define On-call Symbols ---
ON_CALL_SYMBOLS = {
    'regular': ['X', 'Tr'],
    'weekend': ['T7', 'CN'],
    'leave': ['NP', 'No', 'Nkl', 'Nbs', 'Nbc', 'Nhb', 'Nhbs', 'Nhbc', 'NL', 'Ncđ', 'Nô', 'Nô/2', 'Nco', 'Nco/2', 'Nts', 'Ndl', 'Nv'],
    'maternity': ['Nts']
}

# --- Function to Load and Process Data ---
@st.cache_data
def load_and_process_file(uploaded_file):
    """
    Tải tệp Excel hoặc CSV và xử lý dữ liệu.
    Trả về một DataFrame tổng hợp.
    """
    df_combined = pd.DataFrame()
    file_extension = uploaded_file.name.split('.')[-1].lower()

    try:
        if file_extension in ['xlsx', 'xls']:
            xls = pd.ExcelFile(uploaded_file)
            all_sheets_data = []

            for sheet_name in xls.sheet_names:
                raw_df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                
                department_name = "Chưa xác định"
                header_row_index = -1
                date_row_index = -1

                for i, row in raw_df.iterrows():
                    row_str = " ".join(row.dropna().astype(str).tolist())
                    if "Bộ phận:" in row_str:
                        department_name = row_str.split("Bộ phận:")[1].strip().split(',')[0].strip()
                    elif "Đơn vị:" in row_str:
                        department_name = row_str.split("Đơn vị:")[1].strip().split(',')[0].strip()
                    
                    if "STT" in row_str and "Họ và tên" in row_str:
                        header_row_index = i
                    elif header_row_index != -1 and i == header_row_index + 1:
                        date_row_index = i
                        break

                if header_row_index == -1 or date_row_index == -1:
                    st.warning(f"Sheet '{sheet_name}' không tìm thấy cấu trúc header dự kiến ('STT', 'Họ và tên' và dòng ngày tháng). Bỏ qua sheet này.")
                    continue

                df = pd.read_excel(xls, sheet_name=sheet_name, header=header_row_index)
                
                date_headers_row_data = raw_df.iloc[date_row_index]
                
                new_column_names = []
                for i, col_name in enumerate(df.columns):
                    if i < len(date_headers_row_data) and pd.notna(date_headers_row_data.iloc[i]):
                        try:
                            # Chuyển đổi sang định dạng YYYY-MM-DD để dễ xử lý và thống nhất
                            date_val = pd.to_datetime(date_headers_row_data.iloc[i]).strftime('%Y-%m-%d')
                            new_column_names.append(date_val)
                        except ValueError:
                            if str(date_headers_row_data.iloc[i]).lower() in ['t7', 'cn']:
                                new_column_names.append(str(date_headers_row_data.iloc[i]))
                            else:
                                new_column_names.append(str(col_name))
                    else:
                        new_column_names.append(str(col_name))
                
                df.columns = new_column_names

                df.columns = [str(col).strip().lower().replace(' ', '_') if isinstance(col, str) else col for col in df.columns]

                if 'họ_và_tên' in df.columns:
                    df.rename(columns={'họ_và_tên': 'tên_nhân_viên'}, inplace=True)
                
                df['khoa'] = department_name

                df = df[df['tên_nhân_viên'].notna()]
                df = df[df['tên_nhân_viên'].astype(str).str.lower() != 'tổng_cộng']

                shift_cols = [col for col in df.columns if (isinstance(col, str) and (pd.api.types.is_datetime64_any_dtype(pd.to_datetime(col, errors='coerce')) or col.lower() in ['t7', 'cn']))]
                
                for col in shift_cols:
                    df[col] = df[col].fillna('').astype(str).str.strip()

                all_sheets_data.append(df[['khoa', 'tên_nhân_viên'] + shift_cols].copy())

            if not all_sheets_data:
                st.error("Không tìm thấy dữ liệu hợp lệ từ bất kỳ sheet nào trong tệp Excel. Vui lòng kiểm tra lại cấu trúc.")
                return pd.DataFrame()

            df_combined = pd.concat(all_sheets_data, ignore_index=True)
            
            df_combined['khoa'] = df_combined['khoa'].astype(str)
            df_combined['tên_nhân_viên'] = df_combined['tên_nhân_viên'].astype(str)

        elif file_extension == 'csv':
            content = uploaded_file.getvalue().decode('utf-8').splitlines()
            department_name = "Chưa xác định"
            header_row_index = -1
            date_row_index = -1

            for i, line in enumerate(content):
                if "Bộ phận:" in line:
                    department_name = line.split("Bộ phận:")[1].strip().split(',')[0].strip()
                if "STT,Họ và tên" in line:
                    header_row_index = i
                if header_row_index != -1 and i == header_row_index + 1:
                    date_row_index = i
                    break

            if header_row_index == -1 or date_row_index == -1:
                st.error("Không tìm thấy cấu trúc header dự kiến trong tệp CSV. Vui lòng đảm bảo tệp có dòng 'STT,Họ và tên' và dòng ngày tháng ngay sau đó.")
                return pd.DataFrame()

            df = pd.read_csv(io.StringIO('\n'.join(content[header_row_index:])), header=0)
            
            date_headers = pd.read_csv(io.StringIO('\n'.join(content[date_row_index:])), header=None, nrows=1).iloc[0]

            new_column_names = list(df.columns)
            for i in range(len(new_column_names)): # Iterate through all columns
                if i < len(date_headers) and pd.notna(date_headers[i]):
                    try:
                        # Chuyển đổi sang định dạng YYYY-MM-DD
                        date_val = pd.to_datetime(date_headers[i]).strftime('%Y-%m-%d')
                        new_column_names[i] = date_val
                    except ValueError:
                        # Giữ nguyên nếu không phải ngày, ví dụ 'T7', 'CN' hoặc các cột khác
                        new_column_names[i] = str(date_headers[i]) 
                else: # Fallback to original column name if no corresponding date header
                    new_column_names[i] = str(new_column_names[i])

            df.columns = new_column_names
            
            df.columns = [str(col).strip().lower().replace(' ', '_') if isinstance(col, str) else col for col in df.columns]

            if 'họ_và_tên' in df.columns:
                df.rename(columns={'họ_và_tên': 'tên_nhân_viên'}, inplace=True)
            
            cols_to_drop = [col for col in df.columns if col.startswith('stt') or col.startswith('quy_ra_công') or col.startswith('ngày_trong_tháng')]
            df.drop(columns=cols_to_drop, errors='ignore', inplace=True)

            df['khoa'] = department_name

            df = df[df['tên_nhân_viên'].notna()]
            df = df[df['tên_nhân_viên'].astype(str).str.lower() != 'tổng_cộng']

            shift_cols = [col for col in df.columns if (isinstance(col, str) and (pd.api.types.is_datetime64_any_dtype(pd.to_datetime(col, errors='coerce')) or col.lower() in ['t7', 'cn']))]
            
            for col in shift_cols:
                df[col] = df[col].fillna('').astype(str).str.strip()

            df_combined = df[['khoa', 'tên_nhân_viên'] + shift_cols].copy()
            
            df_combined['khoa'] = df_combined['khoa'].astype(str)
            df_combined['tên_nhân_viên'] = df_combined['tên_nhân_viên'].astype(str)

        else:
            st.error("Định dạng tệp không được hỗ trợ. Vui lòng tải lên tệp .xlsx, .xls hoặc .csv.")
            return pd.DataFrame()

    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi đọc tệp: {e}")
        st.info("Vui lòng đảm bảo tệp của bạn không bị hỏng và có định dạng hợp lệ theo hướng dẫn.")
        return pd.DataFrame()

    return df_combined

# --- Sidebar for File Upload ---
with st.sidebar:
    st.header("Tải lên tệp dữ liệu")
    uploaded_file = st.file_uploader(
        "Chọn một tệp Excel (.xlsx, .xls) hoặc CSV (.csv)",
        type=["xlsx", "xls", "csv"],
        help="Tải lên tệp chứa lịch trực của bệnh viện."
    )

    if uploaded_file:
        st.success("Tệp đã được tải lên thành công!")
        st.info("Đang xử lý dữ liệu...")
        df_combined = load_and_process_file(uploaded_file)
        if not df_combined.empty:
            st.success("Dữ liệu đã được xử lý.")
            st.session_state['df_combined'] = df_combined
        else:
            st.session_state['df_combined'] = pd.DataFrame()
    else:
        st.session_state['df_combined'] = pd.DataFrame()

# --- Display Data and Functionalities ---
if 'df_combined' in st.session_state and not st.session_state['df_combined'].empty:
    df_combined = st.session_state['df_combined']

    st.subheader("📊 Tổng quan dữ liệu lịch trực")
    st.dataframe(df_combined.head())
    st.write(f"Tổng số bản ghi: {len(df_combined)}")
    st.write(f"Các khoa có trong dữ liệu: {df_combined['khoa'].unique().tolist()}")

    shift_columns = [col for col in df_combined.columns if col not in ['khoa', 'tên_nhân_viên']]
    if not shift_columns:
        st.warning("Không tìm thấy các cột trực (ví dụ: T2, T3, CN hoặc các ngày tháng) trong dữ liệu. Vui lòng kiểm tra lại cấu trúc tệp.")
    
    # --- Filter by Department ---
    st.sidebar.subheader("Bộ lọc dữ liệu")
    all_departments = ['Tất cả'] + sorted(df_combined['khoa'].unique().tolist())
    selected_department = st.sidebar.selectbox(
        "Chọn Khoa:",
        all_departments,
        help="Lọc dữ liệu theo khoa cụ thể."
    )

    df_filtered = df_combined.copy()
    if selected_department != 'Tất cả':
        df_filtered = df_combined[df_combined['khoa'] == selected_department]

    st.markdown("---")

    # --- 1. Total On-call for Each Person ---
    with st.expander("📈 Tổng số buổi trực của từng nhân viên"):
        if not shift_columns:
            st.info("Không có dữ liệu ca trực để tính toán.")
        else:
            df_filtered['tổng_buổi_trực'] = df_filtered[shift_columns].apply(
                lambda row: sum(1 for cell in row if cell in ON_CALL_SYMBOLS['regular'] + ON_CALL_SYMBOLS['weekend']),
                axis=1
            )
            
            total_on_call_summary = df_filtered.groupby(['khoa', 'tên_nhân_viên'])['tổng_buổi_trực'].sum().reset_index()
            total_on_call_summary.rename(columns={'tổng_buổi_trực': 'Tổng số buổi trực'}, inplace=True)
            st.dataframe(total_on_call_summary.sort_values(by='Tổng số buổi trực', ascending=False))

    # --- 2. Weekend On-call for Each Person ---
    with st.expander("🗓️ Số buổi trực cuối tuần của từng nhân viên"):
        weekend_shift_cols = []
        for col in shift_columns:
            try:
                date_obj = pd.to_datetime(col)
                if date_obj.weekday() in [5, 6]:
                    weekend_shift_cols.append(col)
            except ValueError:
                if str(col).lower() in ['t7', 'cn']:
                    weekend_shift_cols.append(col)
        
        if not weekend_shift_cols:
            st.info("Không tìm thấy các cột trực cuối tuần (Thứ 7, Chủ Nhật hoặc các ngày cuối tuần) để tính toán.")
        else:
            df_filtered['tổng_trực_cuối_tuần'] = df_filtered[weekend_shift_cols].apply(
                lambda row: sum(1 for cell in row if cell in ON_CALL_SYMBOLS['regular'] + ON_CALL_SYMBOLS['weekend']),
                axis=1
            )
            
            weekend_on_call_summary = df_filtered.groupby(['khoa', 'tên_nhân_viên'])['tổng_trực_cuối_tuần'].sum().reset_index()
            weekend_on_call_summary.rename(columns={'tổng_trực_cuối_tuần': 'Tổng số buổi trực cuối tuần'}, inplace=True)
            st.dataframe(weekend_on_call_summary[weekend_on_call_summary['Tổng số buổi trực cuối tuần'] > 0].sort_values(by='Tổng số buổi trực cuối tuần', ascending=False))
            if weekend_on_call_summary[weekend_on_call_summary['Tổng số buổi trực cuối tuần'] > 0].empty:
                st.info("Không có nhân viên nào trực cuối tuần trong dữ liệu đã lọc.")

    # --- 3. Weekly On-call Statistics ---
    with st.expander("📊 Thống kê số người trực theo số buổi trong tuần"):
        if not shift_columns:
            st.info("Không có dữ liệu ca trực để thống kê.")
        else:
            df_filtered['số_buổi_trực_thường'] = df_filtered[shift_columns].apply(
                lambda row: sum(1 for cell in row if cell in ON_CALL_SYMBOLS['regular'] + ON_CALL_SYMBOLS['weekend']),
                axis=1
            )
            
            weekly_stats = df_filtered.groupby(['khoa', 'tên_nhân_viên'])['số_buổi_trực_thường'].sum().reset_index()
            
            def categorize_weekly_on_call(num_shifts):
                if num_shifts == 0: # Thêm trường hợp không trực
                    return 'Không trực'
                elif num_shifts == 1:
                    return '1 buổi'
                elif num_shifts == 2:
                    return '2 buổi'
                elif num_shifts >= 3:
                    return '3 buổi trở lên'
            
            weekly_stats['Phân loại trực tuần'] = weekly_stats['số_buổi_trực_thường'].apply(categorize_weekly_on_call)
            
            category_counts = weekly_stats['Phân loại trực tuần'].value_counts().reset_index()
            category_counts.columns = ['Phân loại', 'Số lượng nhân viên']
            # Đảm bảo thứ tự hiển thị mong muốn
            desired_order = ['Không trực', '1 buổi', '2 buổi', '3 buổi trở lên']
            category_counts['Phân loại'] = pd.Categorical(category_counts['Phân loại'], categories=desired_order, ordered=True)
            category_counts = category_counts.sort_values('Phân loại')

            st.dataframe(category_counts)

            st.markdown("---")
            st.subheader("Danh sách nhân viên theo số buổi trực:")
            
            st.write("**Nhân viên trực 1 buổi:**")
            st.dataframe(weekly_stats[weekly_stats['Phân loại trực tuần'] == '1 buổi'][['khoa', 'tên_nhân_viên']])
            
            st.write("**Nhân viên trực 2 buổi:**")
            st.dataframe(weekly_stats[weekly_stats['Phân loại trực tuần'] == '2 buổi'][['khoa', 'tên_nhân_viên']])
            
            st.write("**Nhân viên trực 3 buổi trở lên:**")
            st.dataframe(weekly_stats[weekly_stats['Phân loại trực tuần'] == '3 buổi trở lên'][['khoa', 'tên_nhân_viên']])
            
            st.write("**Nhân viên không trực:**")
            st.dataframe(weekly_stats[weekly_stats['Phân loại trực tuần'] == 'Không trực'][['khoa', 'tên_nhân_viên']])


    # --- 4. Check Who is on Leave ---
    with st.expander("🏖️ Danh sách nhân viên nghỉ phép"):
        if not shift_columns:
            st.info("Không có dữ liệu ca trực để kiểm tra nghỉ phép.")
        else:
            on_leave_df = df_filtered[
                df_filtered[shift_columns].apply(
                    lambda row: any(cell in ON_CALL_SYMBOLS['leave'] for cell in row),
                    axis=1
                )
            ][['khoa', 'tên_nhân_viên']].drop_duplicates()
            
            if not on_leave_df.empty:
                st.dataframe(on_leave_df)
            else:
                st.info("Không có nhân viên nào đang nghỉ phép trong dữ liệu đã lọc.")

    # --- 5. Check Who is on Maternity Leave ---
    with st.expander("🤰 Danh sách nhân viên thai sản"):
        if not shift_columns:
            st.info("Không có dữ liệu ca trực để kiểm tra thai sản.")
        else:
            on_maternity_df = df_filtered[
                df_filtered[shift_columns].apply(
                    lambda row: any(cell in ON_CALL_SYMBOLS['maternity'] for cell in row),
                    axis=1
                )
            ][['khoa', 'tên_nhân_viên']].drop_duplicates()
            
            if not on_maternity_df.empty:
                st.dataframe(on_maternity_df)
            else:
                st.info("Không có nhân viên nào đang thai sản trong dữ liệu đã lọc.")

else:
    st.info("Vui lòng tải lên một tệp Excel hoặc CSV để bắt đầu.")

st.markdown("---")
st.markdown("© 2023 Ứng dụng Quản lý Lịch Trực Bệnh Viện. Được xây dựng với Streamlit.")
