import streamlit as st
import pandas as pd
from PIL import Image
import math

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Ukur Aras PUO - DCG40502", layout="centered")

# 2. MUKA DEPAN (LOGO & MAKLUMAT KUMPULAN)
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    try:
        logo = Image.open('image_2026-04-07_114827697.png')
        st.image(logo, width=350)
    except:
        st.info("Logo PUO (Sila pastikan fail logo ada di GitHub)")

st.markdown("<h1 style='text-align: center; color: #FFD700;'>SISTEM PEMBUKUAN UKUR ARAS (TGK)</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>DIPLOMA GEOMATIK, JKA PUO</h3>", unsafe_allow_html=True)

with st.container():
    st.divider()
    col_a, col_b = st.columns([0.4, 0.6])
    with col_a:
        st.write("**Kod Kursus:**")
        st.write("**Pereka App:**")
        st.write("**Ahli Kumpulan:**")
    with col_b:
        st.write("DCG40502")
        st.write("Muhammad Adam bin Saberi")
        st.write("1. Ainur Farisha Husna binti Abdul Hakim")
        st.write("2. Nur Jazzrene Fatishah binti Azmi")
        st.write("3. Muhammad Adam bin Saberi")
    st.divider()

# 3. INPUT TETAPAN ARAS
st.subheader("⚙️ Tetapan Aras Laras")
tbm_mula = st.number_input("Aras Laras Awal (TBM 1):", value=0.000, format="%.3f", key="input_tbm_awal")
tbm_akhir_sebenar = st.number_input("Aras Laras Akhir Sebenar (Closing TBM):", value=0.000, format="%.3f", key="input_tbm_akhir")

# 4. JADUAL INPUT DATA
st.subheader("📝 Input Data Pandangan (BS, IS, FS) & Jarak")

if 'survey_data' not in st.session_state:
    data = {
        "Stesen/Remark": [""],
        "BS": [None],
        "IS": [None],
        "FS": [None],
        "Jarak (m)": [0.0] # Tambah kolum Jarak
    }
    st.session_state.survey_data = pd.DataFrame(data)

edited_df = st.data_editor(
    st.session_state.survey_data, 
    num_rows="dynamic", 
    use_container_width=True, 
    key="main_editor"
)

# 5. FUNGSI PENGIRAAN LENGKAP
def calculate_full_process(df, initial_rl, final_rl_known):
    rl_list = []
    tgk_list = []
    current_rl = initial_rl
    current_tgk = None
    
    # Tukar data ke numerik untuk elak error
    df['BS'] = pd.to_numeric(df['BS']).fillna(0)
    df['IS'] = pd.to_numeric(df['IS']).fillna(0)
    df['FS'] = pd.to_numeric(df['FS']).fillna(0)
    df['Jarak (m)'] = pd.to_numeric(df['Jarak (m)']).fillna(0)
    
    for i, row in df.iterrows():
        bs = row['BS']
        is_val = row['IS']
        fs = row['FS']
        
        if i == 0 and bs > 0:
            current_tgk = initial_rl + bs
            current_rl = initial_rl
        elif is_val > 0:
            current_rl = current_tgk - is_val
        elif fs > 0:
            current_rl = current_tgk - fs
            
        rl_list.append(round(current_rl, 3))
        tgk_list.append(round(current_tgk, 3) if current_tgk else None)
        
        if i > 0 and bs > 0:
            current_tgk = current_rl + bs
            tgk_list[-1] = round(current_tgk, 3)

    # Kira Ralat (Misclosure)
    rl_akhir_kiraan = rl_list[-1]
    total_error = round(rl_akhir_kiraan - final_rl_known, 3)
    
    # Pengiraan Pembetulan
    num_stations = len(df) - 1 if len(df) > 1 else 1
    pembetulan_list = []
    rl_sebenar_list = []
    
    for i in range(len(df)):
        if i == 0:
            corr = 0.000
        else:
            corr = -(total_error / num_stations) * i
        pembetulan_list.append(round(corr, 4))
        rl_sebenar_list.append(round(rl_list[i] + corr, 3))

    df['TGK'] = tgk_list
    df['Aras Laras'] = rl_list
    df['Pembetulan'] = pembetulan_list
    df['Aras Laras Sebenar'] = rl_sebenar_list
    
    return df, total_error

# 6. PAPARAN KEPUTUSAN
if st.button("JALANKAN PENGIRAAN", type="primary", key="btn_kira"):
    result, error = calculate_full_process(edited_df.copy(), tbm_mula, tbm_akhir_sebenar)
    
    st.success("✅ Pengiraan Selesai!")
    st.write("### Jadual Pembukuan Lengkap")
    st.dataframe(result, use_container_width=True)
    
    # Semakan Aritmetik & Had Selisih
    st.divider()
    st.subheader("📊 Semakan Aritmetik & Had Selisih")
    
    # 1. Kira Jumlah Jarak & Had Selisih
    total_distance_m = result['Jarak (m)'].sum()
    total_distance_km = total_distance_m / 1000
    
    # Formula: 0.012 * sqrt(K)
    allowable_error = round(0.012 * math.sqrt(total_distance_km), 3) if total_distance_km > 0 else 0.000
    abs_error = abs(error)

    col1, col2, col3 = st.columns(3)
    col1.metric("Jumlah Jarak", f"{total_distance_m} m")
    col2.metric("Had Selisih (0.012√km)", f"± {allowable_error} m")
    col3.metric("Ralat (Misclosure)", f"{error} m")

    # Logik Semakan
    st.write("---")
    
    # Semakan 1: Aritmetik
    sum_bs = result['BS'].sum()
    sum_fs = result['FS'].sum()
    diff_bs_fs = round(sum_bs - sum_fs, 3)
    diff_rl = round(result['Aras Laras'].iloc[-1] - tbm_mula, 3)
    
    if diff_bs_fs == diff_rl:
        st.write("✔️ **Semakan Aritmetik:** Tepat")
    else:
        st.write("❌ **Semakan Aritmetik:** Tidak Tepat")

    # Semakan 2: Had Selisih
    if abs_error <= allowable_error:
        st.success(f"✅ **HASIL:** Semakan Tepat!! (Ralat {abs_error}m ≤ Had {allowable_error}m)")
    else:
        st.error(f"⚠️ **HASIL:** Semakan Gagal dan perlu buat pengukuran semula. (Ralat {abs_error}m > Had {allowable_error}m)")

st.markdown("<br><hr><p style='text-align: center; color: gray;'>© 2026 Muhammad Adam - JKA PUO</p>", unsafe_allow_html=True)
