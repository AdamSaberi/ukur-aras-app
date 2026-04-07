import streamlit as st
import pandas as pd
from PIL import Image
import flet as ft

def main(page: ft.Page):
    page.title = "App Ukur Aras JKA"
    
    # Input Fields
    tbm_input = ft.TextField(label="TBM Mula", value="44.725")
    bs_input = ft.TextField(label="Pandangan Belakang (BS)")
    result_text = ft.Text()

    def hitung(e):
        tgk = float(tbm_input.value) + float(bs_input.value)
        result_text.value = f"TGK Anda: {tgk:.3f}"
        page.update()

    page.add(
        ft.Text("Kalkulator Aras Laras", size=30, weight="bold"),
        tbm_input,
        bs_input,
        ft.ElevatedButton("Kira TGK", on_click=hitung),
        result_text
    )

ft.app(target=main)

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Ukur Aras PUO - DCG40502", layout="centered")

# 2. MUKA DEPAN (LOGO & MAKLUMAT KUMPULAN)
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    try:
        logo = Image.open('image_2026-04-07_114827697.png')
        st.image(logo, width=350)
    except:
        st.info("Logo PUO (Sila pastikan fail PUO_Logo.png ada di GitHub)")

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

# 4. JADUAL INPUT DATA (KOSONG UNTUK MANUAL INPUT)
st.subheader("📝 Input Data Pandangan (BS, IS, FS)")

if 'survey_data' not in st.session_state:
    # Kita buat DataFrame kosong dengan kolum yang betul
    data = {
        "Stesen/Remark": [""],
        "BS": [None],
        "IS": [None],
        "FS": [None],
    }
    st.session_state.survey_data = pd.DataFrame(data)

# Gunakan num_rows="dynamic" supaya kau boleh tambah baris sendiri guna butang (+)
edited_df = st.data_editor(
    st.session_state.survey_data, 
    num_rows="dynamic", 
    use_container_width=True, 
    key="main_editor"
)

# 5. FUNGSI PENGIRAAN LENGKAP (TGK -> RL -> PEMBETULAN)
def calculate_full_process(df, initial_rl, final_rl_known):
    rl_list = []
    tgk_list = []
    current_rl = initial_rl
    current_tgk = None
    
    # Kira RL & TGK (Logik Sequential)
    for i, row in df.iterrows():
        bs = float(row['BS']) if pd.notnull(row['BS']) else 0
        is_val = float(row['IS']) if pd.notnull(row['IS']) else 0
        fs = float(row['FS']) if pd.notnull(row['FS']) else 0
        
        # Penentuan TGK Pertama
        if i == 0 and bs > 0:
            current_tgk = initial_rl + bs
            current_rl = initial_rl
        # Penolakan TGK ke IS/FS untuk dapatkan RL (Guna TGK sedia ada)
        elif is_val > 0:
            current_rl = current_tgk - is_val
        elif fs > 0:
            current_rl = current_tgk - fs
            
        rl_list.append(round(current_rl, 3))
        tgk_list.append(round(current_tgk, 3) if current_tgk else None)
        
        # Kemaskini TGK baru jika ada BS (Change Point)
        if i > 0 and bs > 0:
            current_tgk = current_rl + bs
            tgk_list[-1] = round(current_tgk, 3)

    # Pengiraan Pembetulan (Correction)
    rl_akhir_kiraan = rl_list[-1]
    total_error = round(rl_akhir_kiraan - final_rl_known, 3)
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
    
    # Semakan Aritmetik
    st.divider()
    st.subheader("📊 Semakan Aritmetik & Ralat")
    
    sum_bs = pd.to_numeric(result['BS']).sum()
    sum_fs = pd.to_numeric(result['FS']).sum()
    diff_bs_fs = round(sum_bs - sum_fs, 3)
    diff_rl = round(result['Aras Laras'].iloc[-1] - tbm_mula, 3)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("ΣBS - ΣFS", f"{diff_bs_fs} m")
    col2.metric("RL Akhir - RL Awal", f"{diff_rl} m")
    col3.metric("Ralat (Misclosure)", f"{error} m")
    
    if diff_bs_fs == diff_rl:
        st.success("Semakan Aritmetik: TEPAT")
    else:
        st.error("Semakan Aritmetik: TIDAK TEPAT (Sila semak input)")

st.markdown("<br><hr><p style='text-align: center; color: gray;'>© 2026 Muhammad Adam - JKA PUO</p>", unsafe_allow_html=True)
