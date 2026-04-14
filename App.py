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
        # Pastikan nama fail imej betul mengikut fail anda
        logo = Image.open('image_2026-04-07_114827697.png')
        st.image(logo, width=350)
    except:
        st.info("Logo PUO (Sila pastikan fail imej ada dalam folder yang sama)")

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
col_tbm1, col_tbm2 = st.columns(2)
with col_tbm1:
    tbm_mula = st.number_input("Aras Laras Awal (TBM 1):", value=0.000, format="%.3f", key="input_tbm_awal")
with col_tbm2:
    tbm_akhir_sebenar = st.number_input("Aras Laras Akhir Sebenar:", value=0.000, format="%.3f", key="input_tbm_akhir")

# 4. JADUAL INPUT DATA
st.subheader("📝 Input Data Pandangan & Jarak")
st.caption("Nota: Masukkan jarak kumulatif (meter). Jarak pada baris terakhir akan digunakan untuk had selisih.")

if 'survey_data' not in st.session_state:
    data = {
        "Stesen/Remark": ["TBM 1", "CP 1"],
        "BS": [None, None],
        "IS": [None, None],
        "FS": [None, None],
        "Jarak (m)": [0.0, 0.0]
    }
    st.session_state.survey_data = pd.DataFrame(data)

edited_df = st.data_editor(
    st.session_state.survey_data, 
    num_rows="dynamic", 
    use_container_width=True, 
    key="main_editor"
)

# 5. FUNGSI PENGIRAAN
def calculate_full_process(df, initial_rl, final_rl_known):
    # Pastikan data adalah jenis numerik
    df['BS'] = pd.to_numeric(df['BS']).fillna(0)
    df['IS'] = pd.to_numeric(df['IS']).fillna(0)
    df['FS'] = pd.to_numeric(df['FS']).fillna(0)
    df['Jarak (m)'] = pd.to_numeric(df['Jarak (m)']).fillna(0)
    
    rl_list = []
    tgk_list = []
    current_rl = initial_rl
    current_tgk = None
    
    for i, row in df.iterrows():
        bs = row['BS']
        is_val = row['IS']
        fs = row['FS']
        
        # Penentuan TGK Pertama (Baris 1)
        if i == 0:
            if bs > 0:
                current_tgk = initial_rl + bs
            current_rl = initial_rl
        else:
            # Pengiraan RL melalui TGK sedia ada
            if is_val > 0:
                current_rl = current_tgk - is_val
            elif fs > 0:
                current_rl = current_tgk - fs
        
        rl_list.append(round(current_rl, 3))
        tgk_list.append(round(current_tgk, 3) if current_tgk else None)
        
        # Kemaskini TGK jika ada BS pada baris seterusnya (Change Point)
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
if st.button("JALANKAN PENGIRAAN", type="primary"):
    if not edited_df.empty:
        result, error = calculate_full_process(edited_df.copy(), tbm_mula, tbm_akhir_sebenar)
        
        st.success("✅ Pengiraan Selesai!")
        st.dataframe(result, use_container_width=True)
        
        # --- SEMAKAN ARITMETIK & HAD SELISIH ---
        st.divider()
        st.subheader("📊 Semakan Aritmetik & Had Selisih")
        
        # Ambil jarak pada baris terakhir (K)
        jarak_akhir_m = float(result['Jarak (m)'].iloc[-1])
        jarak_akhir_km = jarak_akhir_m / 1000
        
        # Had Selisih = 0.012 * sqrt(K_km)
        had_selisih = round(0.012 * math.sqrt(jarak_akhir_km), 3) if jarak_akhir_km > 0 else 0.000
        ralat_mutlak = abs(error)

        m1, m2, m3 = st.columns(3)
        m1.metric("Jarak Akhir (K)", f"{jarak_akhir_m} m")
        m2.metric("Had Selisih (0.012√K)", f"± {had_selisih} m")
        m3.metric("Ralat (Misclosure)", f"{error} m")
        
        st.write("---")
        
        # Logik Keputusan Had Selisih
        if ralat_mutlak <= had_selisih:
            st.success("### HASIL: SEMAKAN TEPAT!!")
            st.write(f"Ralat anda ({ralat_mutlak}m) berada di bawah had yang dibenarkan (±{had_selisih}m).")
        else:
            st.error("### HASIL: SEMAKAN GAGAL DAN PERLU BUAT PENGUKURAN SEMULA.")
            st.write(f"Ralat anda ({ralat_mutlak}m) telah melebihi had selisih (±{had_selisih}m).")

        # Semakan Aritmetik Tambahan
        sum_bs = result['BS'].sum()
        sum_fs = result['FS'].sum()
        if round(sum_bs - sum_fs, 3) == round(result['Aras Laras'].iloc[-1] - tbm_mula, 3):
            st.info("💡 Semakan Aritmetik (ΣBS - ΣFS) adalah Konsisten.")
    else:
        st.warning("Sila masukkan data terlebih dahulu.")

st.markdown("<br><hr><p style='text-align: center; color: gray;'>© 2026 Muhammad Adam - JKA PUO</p>", unsafe_allow_html=True)
