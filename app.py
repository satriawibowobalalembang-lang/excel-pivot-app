import streamlit as st
import pandas as pd
import duckdb

st.set_page_config(page_title="Aplikasi Pivot Data Besar CSV", layout="wide")
st.title("📊 Multi-File CSV Pivot Dashboard")
st.write("Aplikasi pengolah data besar interaktif menggunakan Python & DuckDB.")

st.sidebar.header("📁 Upload File CSV")
uploaded_files = st.sidebar.file_uploader(
    "Pilih beberapa file CSV Anda:", 
    type=["csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    dataframes = []
    progress_bar = st.progress(0)
    
    for idx, file in enumerate(uploaded_files):
        df = pd.read_csv(file, low_memory=False)
        dataframes.append(df)
        progress_bar.progress((idx + 1) / len(uploaded_files))
        
    combined_df = pd.concat(dataframes, ignore_index=True)
    
    st.success(f"Berhasil menggabungkan {len(uploaded_files)} file CSV!")
    
    st.subheader("📌 Ringkasan Data Tergabung")
    st.write(f"Total Baris Data: **{len(combined_df):,}** | Total Kolom: **{len(combined_df.columns)}**")

    tab1, tab2 = st.tabs(["📋 Preview Data", "🔀 Pivot Table Interaktif"])

    with tab1:
        st.dataframe(combined_df.head(100))

    with tab2:
        st.subheader("Konfigurasi Pivot Table")
        all_columns = combined_df.columns.tolist()

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
                FROM combined_df
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
    st.info("Silakan upload file-file CSV Anda melalui panel di sebelah kiri untuk mulai mengolah data.")
