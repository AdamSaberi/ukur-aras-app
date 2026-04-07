import streamlit as st
import pandas as pd
import streamlit as st
import pandas as pd
from PIL import Image

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Ukur Aras PUO", layout="centered")

# 2. Susunan Logo di Tengah
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    try:
        logo = Image.open('PUO_Logo.png')
        st.image(logo, width=180)
    except:
        st.info("Logo PUO akan dipaparkan di sini.")

# 3. Muka Depan (Maklumat Kumpulan & Kursus)
st.markdown("<h1 style='text-align: center; color: #FFD700;'>SISTEM PEMBUKUAN UKUR ARAS (TGK)</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>DIPLOMA GEOMATIK, JKA PUO</h3>", unsafe_allow_html=True)

# Guna container untuk nampak macam 'kad' maklumat
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

# 4. Input Aras Mula (Bahagian Pengiraan Bermula Sini)
st.subheader("⚙️ Tetapan Aras Laras")
tbm_mula = st.number_input("Aras Laras Awal (TBM 1):", value=44.725, format="%.3f")
tbm_akhir_sebenar = st.number_input("Aras Laras Akhir Sebenar (Closing TBM):", value=44.729, format="%.3f")

# ... Sambung dengan koding st.data_editor dan fungsi calculate kau yang sebelum ni ...
st.title("📟 Kalkulator Ukur Aras (Lengkap dengan Pembetulan)")

tbm_mula = st.number_input("Aras Laras Awal (TBM 1):", value=44.725, format="%.3f")
tbm_akhir_sebenar = st.number_input("Aras Laras Akhir Sebenar (Closing TBM):", value=44.729, format="%.3f")

if 'survey_data' not in st.session_state:
    data = {
        "Stesen/Remark": ["TBM 1", "IS 1", "CP 1", "IS 2", "CP 2", "IS 3", "IS 4", "IS 5", "CP 3", "IS 6", "CP 4", "IS 7", "CP 5", "IS 8", "IS 9", "IS 10", "TBM 1 (End)"],
        "BS": [1.181, None, 1.356, None, 1.214, None, None, None, 1.493, None, 1.453, None, 1.967, None, None, None, None],
        "IS": [None, 1.485, None, 2.047, None, 1.390, 1.571, 1.848, None, 1.345, None, 0.948, None, 1.697, 1.900, 1.910, None],
        "FS": [None, None, 1.575, None, 1.602, None, None, None, 2.036, None, 1.507, None, 1.110, None, None, None, 0.830],
    }
    st.session_state.survey_data = pd.DataFrame(data)

edited_df = st.data_editor(st.session_state.survey_data, num_rows="dynamic", use_container_width=True)

def calculate_full_final(df, initial_rl, final_rl_known):
    rl_list = []
    tgk_list = []
    current_rl = initial_rl
    current_tgk = None
    
    # 1. KIRA RL & TGK (Logik asal jangan ubah)
    for i, row in df.iterrows():
        bs = float(row['BS']) if pd.notnull(row['BS']) else 0
        is_val = float(row['IS']) if pd.notnull(row['IS']) else 0
        fs = float(row['FS']) if pd.notnull(row['FS']) else 0
        
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

    # 2. PENGIRAAN PEMBETULAN (CORRECTION)
    rl_akhir_kiraan = rl_list[-1]
    total_error = round(rl_akhir_kiraan - final_rl_known, 3)
    num_stations = len(df) - 1 # Tolak stesen pertama
    
    pembetulan_list = []
    rl_sebenar_list = []
    
    for i in range(len(df)):
        if i == 0:
            corr = 0.000
        else:
            # Formula: -(Error / Total Stesen) * i
            corr = -(total_error / num_stations) * i
            
        pembetulan_list.append(round(corr, 4))
        rl_sebenar_list.append(round(rl_list[i] + corr, 3))

    df['TGK'] = tgk_list
    df['RL'] = rl_list
    df['Pembetulan'] = pembetulan_list
    df['Aras Laras Sebenar'] = rl_sebenar_list
    
    return df, total_error

if st.button("Kira Aras Laras Sebenar"):
    result, error = calculate_full_final(edited_df.copy(), tbm_mula, tbm_akhir_sebenar)
    st.subheader("Jadual Pembukuan Lengkap")
    st.dataframe(result, use_container_width=True)
    
    # Paparan Rumusan
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Misclosure (Error)", f"{error} m")
    col2.metric("RL Akhir (Kiraan)", f"{result['RL'].iloc[-1]}")
    col3.metric("RL Akhir (Sebenar)", f"{tbm_akhir_sebenar}")
    
    if abs(error) < 0.012: # Contoh toleransi 12mm
        st.success("Bagus! Ralat dalam had toleransi.")
    else:
        st.warning("Ralat agak besar. Sila semak semula bacaan staf.")
