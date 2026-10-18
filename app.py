import streamlit as st
import pandas as pd
import duckdb
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

st.set_page_config(page_title="Aplikasi Pivot Data Besar CSV", layout="wide")
st.title("📊 Multi-File CSV Pivot Dashboard")
st.write("Aplikasi pengolah data besar dari folder Google Drive menggunakan Python & DuckDB.")

# 1. Autentikasi Google Drive via Streamlit Secrets (Pembersihan format kunci mutlak)
@st.cache_resource
def get_drive_service():
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # Memastikan format private_key bersih dari escape character
        if "private_key" in creds_dict:
            pk = creds_dict["private_key"]
            pk = pk.replace("\\n", "\n")
            if not pk.startswith("-----BEGIN PRIVATE KEY-----"):
                pk = "-----BEGIN PRIVATE KEY-----\n" + pk
            if not pk.strip().endswith("-----END PRIVATE KEY-----"):
                pk = pk.strip() + "\n-----END PRIVATE KEY-----\n"
            creds_dict["private_key"] = pk
            
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
    else:
        st.error("Kredensial Service Account belum diatur di Streamlit Secrets!")
        st.stop()
    return build('drive', 'v3', credentials=creds)

# 2. Fungsi Mengunduh & Membaca Seluruh File CSV dalam Folder Drive
@st.cache_data(ttl=3600)
def load_all_csv_from_folder(folder_id):
    service = get_drive_service()
    
    query = f"'{folder_id}' in parents and mimeType='text/csv' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])

    if not files:
        st.warning("Tidak ditemukan file CSV (.csv) di dalam folder tersebut.")
        return None

    st.info(f"Ditemukan {len(files)} file CSV. Memulai proses membaca data...")
    
    dataframes = []
    progress_bar = st.progress(0)
    
    for idx, file_item in enumerate(files):
        file_id = file_item['id']
        
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        
        fh.seek(0)
        df = pd.read_csv(fh, low_memory=False)
        dataframes.append(df)
        
        progress_bar.progress((idx + 1) / len(files))

    st.success(f"Berhasil menggabungkan {len(files)} file CSV!")
    
    combined_df = pd.concat(dataframes, ignore_index=True)
    return combined_df

# Sidebar Input Folder ID
st.sidebar.header("📁 Konfigurasi Google Drive")
folder_id_input = st.sidebar.text_input("Masukkan Google Drive Folder ID:", "1UEjMYCAFjVHHZhYY2QO-qmcX0EKq1zDt")

if folder_id_input:
    with st.spinner("Mengunduh dan mengolah data CSV dari Google Drive..."):
        df_combined = load_all_csv_from_folder(folder_id_input)

    if df_combined is not None:
        st.subheader("📌 Ringkasan Data Tergabung")
        st.write(f"Total Baris Data: **{len(df_combined):,}** | Total Kolom: **{len(df_combined.columns)}**")

        tab1, tab2 = st.tabs(["📋 Preview Data", "🔀 Pivot Table Interaktif"])

        with tab1:
            st.dataframe(df_combined.head(100))

        with tab2:
            st.subheader("Konfigurasi Pivot Table")
            all_columns = df_combined.columns.tolist()

            col_row, col_col, col_val, col_func = st.columns(4)
            with col_row:
                selected_rows = st.multiselect("Pilih Baris (Rows):", all_columns)
            with col_col:
                selected_cols = st.multiselect("Pilih Kolom (Columns):", all_columns)
            with col_val:
                selected_vals = st.selectbox("Pilih Nilai Data (Values):", all_columns)
            with col_func:
                agg_func = st.selectbox("Fungsi Agregasi:", ["SUM", "COUNT", "AVG", "MIN", "MAX"])

            if selected_rows or selected_cols:
                group_by_cols = [c for c in (selected_rows + selected_cols) if c]
                group_by_str = ", ".join([f'"{g}"' for g in group_by_cols])

                func_map = {"SUM": "SUM", "COUNT": "COUNT", "AVG": "AVG", "MIN": "MIN", "MAX": "MAX"}
                
                query = f"""
                    SELECT {group_by_str}, {func_map[agg_func]}("{selected_vals}") AS "{agg_func} of {selected_vals}"
                    FROM df_combined
                    GROUP BY {group_by_str}
                    ORDER BY {group_by_str}
                """
                
                pivot_result = duckdb.query(query).df()
                
                st.write("### Hasil Pivot Data")
                st.dataframe(pivot_result, use_container_width=True)

                csv_buffer = pivot_result.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Hasil Pivot (CSV)",
                    data=csv_buffer,
                    file_name="hasil_pivot_data.csv",
                    mime="text/csv"
                )
else:
    st.info("Silakan masukkan Google Drive Folder ID di sidebar sebelah kiri untuk memulai.")
