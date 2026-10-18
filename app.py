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

# Autentikasi langsung di dalam kode (Aman & Tanpa Ribet Secrets)
@st.cache_resource
def get_drive_service():
    creds_dict = {
        "type": "service_account",
        "project_id": "excel-pivot-app",
        "private_key_id": "c67cde116477efcd5924adfb0a58369f6e34754b",
        "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCZXdSpNHmixQC
E16sXgqAyJ1oOP0Qw/qsUbGpjHCxVAZ2vOq26SdS5eeoMnJze3EtLExk+zm
nX8VfWS82HqZzCIG3egamH3o+UA00R3rWVLfvS89I190QkLaPaPfTpqW39sftGpgt1
ngTLLOEghDcLE49pybx8Yro5KFSYDHpHHgMEfPfQPozo5W/SkZR11/Di464DoThq
nJfLKNsIgB2AeCeA/BSCGbS/zfFj4wilUn1M+AusJeWaAtXnva8MR2PNpVhpc5LX
NON+37ZjZabPj8w3quwhFGFuixedD94q/td7cMij4JD3caydHhshc/n5AnNhhO9QT
nr2H2jJ7bagMBAAEcgqEADW2y+i2//mMUZtqgAlTYgKgBLbqFZRlPKrza7fh2fns
nRy5b9V1PioVt1IlffsGIEDC6roZhFvOvTcmqXJcff49eacikJIOHxFJ4E8dEd7
nVqze0Fv/YjrOWF4YitD1D6mlzBS0Ids3XRxTv+osqFga7nxKAxBr3DpWM2Sw5rc
nZddNEWKcwHKDAVJ3gpppI78S8OfRUMtGd1VynQ88p/+PLxPYN+joj9XAvnS8
fzt
NODNLOGp1wyCLKbbsSRTkR4uEhBSqyG0lic+r2dn/n7vQs+KvJ7NjW5Pmt1M93Rj
n6jFVQvbkbO9oqRNKm/jNL60Xufov5hqnDERW8/LKQKBgQDI67Wc+Ny6DNe/N4wL
noNECtHPN9TYdT+q89CTCF26L9qidBd8GZS06KUG8siY1ZwbGG6I5Com/3GWxTwbc
nb0pXFD74p7PPW4xzCfvLAF4XObqm5r4pNXFnr/o+aep+56Njui18DVYCMSUirqTh
NPHL23PLX9lif7kvFxuYdL8e7EwKBgQDHRRuKpCnGE4RxkkF5mntrP93F8M+R1L9S
NmLtIH0LfCX/+7uX6gtg+EwP0w+hW/8NZOvtyoceV86fnIUV61jsxVR3QOh7JWOS
n9t5gNVMutJbNh+55rfX9IrJbO8rOY1GAnIMRvTiDN6zegkFfKCsusRml2i/HYK
nUQXjKSh+GQKBgCzW/eCUWx5izr9PBEAsGblC0H1sdjFAfqDA09tFI3S1DzhnkSJ6
nPge24WbdU2juoH6YJVaby0Vaq1Nsr/XNFN3aa7qd7RPL/jWQWpukEBzsVRAZ
nTz/WtEBtntnHlF1S+RLb8Q/4iKSRZVanCPKzAjdUUR8QLXTsGlr2yNpLaon
GBAJ2L
nT7kPDU/jAmVe+atQrZ8fgWWZ2CHt180+rtiYjQaVLRyBMifRCmrAjsaNrEByQp
n1DXOV4Fv3pZmgvnPdiDL6nnWQXELGeyJbUsXHcrhUBCg3EQrez5/kot5A9CkyT0
nrgJy3jvVecivnodLZ
+QXJ0wND18hnITSwEC2RAoGASWQylbFWs1MbhLgDkccV
9jEYc/BhUcxUoAtY3RvAUphgfy3/uzsfya4k5PkQq9FcTLR4TjceQm6xNGDT7Iz
n2CrKjDrDS2Lss2nsfYbmVQJRef19QVFg5fm0BeSjP5HEK7Qnp902WtbnnXx4rzLm
nCRCXilI7pL/oy7qWeDj27A=
-----END PRIVATE KEY-----""",
        "client_email": "excel-reader@excel-pivot-app.iam.gserviceaccount.com",
        "client_id": "112150216549019737085",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/excel-reader%40excel-pivot-app.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }
    
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    return build('drive', 'v3', credentials=creds)

# Fungsi Mengunduh & Membaca Seluruh File CSV dalam Folder Drive
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
