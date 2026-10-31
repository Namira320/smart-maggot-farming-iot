import io
import json
import time
from datetime import datetime
import pandas as pd
import streamlit as st
import paho.mqtt.client as mqtt

# Impor modul database lokal
import database

# Inisialisasi database SQLite (membuat berkas & tabel jika belum ada)
database.init_db()

# Konfigurasi Halaman Streamlit
st.set_page_config(page_title="Dashboard IoT BSF", page_icon="🐛", layout="wide")
st.title("🐛 Dashboard Monitoring Budidaya Maggot BSF")

# ==========================================
# LOGIKA EVALUASI PERKEMBANGAN MAGGOT BSF
# ==========================================
def analisis_maggot(suhu, kelembapan):
    """
    Menilai kondisi pertumbuhan maggot BSF berdasarkan referensi biologis:
    - Optimal: Suhu 27-32 C, Kelembaban 60-80%
    - Cukup Baik: Suhu 22-26.9 C atau 32.1-36 C, Kelembaban 50-59.9% atau 80.1-90%
    - Kurang Optimal: Suhu 15-21.9 C atau 36.1-40 C, Kelembaban 40-49.9% atau 90.1-95%
    - Berisiko: Suhu < 15 C atau > 40 C, atau Kelembaban < 40% atau > 95%
    """
    # 1. KONDISI OPTIMAL
    if (27.0 <= suhu <= 32.0) and (60.0 <= kelembapan <= 80.0):
        status = "Optimal"
        rekomendasi = "Kondisi ideal untuk metabolisme dan nafsu makan maggot. Pertahankan suhu dan kelembaban pakan."
        warna = "green"
    # 2. KONDISI CUKUP BAIK
    elif (22.0 <= suhu <= 36.0) and (50.0 <= kelembapan <= 90.0):
        status = "Cukup Baik"
        rekomendasi = "Mendekati ideal. Lakukan pemantauan berkala dan pastikan pakan tidak terlalu kering atau terlalu becek."
        warna = "blue"
    # 3. KONDISI KURANG OPTIMAL
    elif (15.0 <= suhu <= 40.0) and (40.0 <= kelembapan <= 95.0):
        status = "Kurang Optimal"
        rekomendasi = "Pertumbuhan maggot melambat. Tambahkan naungan jika terlalu panas, atau tambahkan bahan pakan kering jika terlalu lembab."
        warna = "orange"
    # 4. KONDISI BERISIKO (EKSTREM)
    else:
        status = "Berisiko"
        rekomendasi = "Bahaya kematian maggot! Segera evakuasi biobox ke ruangan dengan sirkulasi udara lebih baik atau sesuaikan kondisi ruangan."
        warna = "red"
        
    return status, rekomendasi, warna

# ==========================================
# SETUP PENYIMPANAN DATA (SESSION STATE)
# ==========================================
if "suhu" not in st.session_state:
    st.session_state.suhu = 0.0
if "hum" not in st.session_state:
    st.session_state.hum = 0.0
if "status" not in st.session_state:
    st.session_state.status = "Menunggu Data Lokal..."
if "status_maggot" not in st.session_state:
    st.session_state.status_maggot = "Menunggu Analisis..."
if "rekomendasi" not in st.session_state:
    st.session_state.rekomendasi = "Hubungkan node sensor untuk mendapatkan analisis tindakan."
if "warna_maggot" not in st.session_state:
    st.session_state.warna_maggot = "grey"
if "last_updated" not in st.session_state:
    st.session_state.last_updated = 0

# ==========================================
# CALLBACK PENERIMAAN PESAN MQTT
# ==========================================
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
        
        suhu = float(data.get("temp", 0))
        hum = float(data.get("hum", 0))
        status_kondisi = data.get("status", "UNKNOWN")
        
        # Evaluasi kondisi maggot BSF
        status_maggot, rekomendasi, warna = analisis_maggot(suhu, hum)
        
        # Simpan ke Database SQLite secara otomatis
        database.insert_data(suhu, hum, status_kondisi, status_maggot, rekomendasi)
        
        # Perbarui nilai session state
        st.session_state.suhu = suhu
        st.session_state.hum = hum
        st.session_state.status = status_kondisi
        st.session_state.status_maggot = status_maggot
        st.session_state.rekomendasi = rekomendasi
        st.session_state.warna_maggot = warna
        
        # Trigger penyegaran data (mengubah token agar cache diperbarui)
        st.session_state.last_updated += 1
            
    except Exception as e:
        pass

# ==========================================
# SETUP MQTT CLIENT (CACHED RESOURCE)
# ==========================================
@st.cache_resource
def get_mqtt_client():
    if hasattr(mqtt, 'CallbackAPIVersion'):
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    else:
        client = mqtt.Client()
    client.on_message = on_message
    client.connect("127.0.0.1", 1883, 60)
    client.subscribe("iot/sensor")
    return client

client = get_mqtt_client()
client.loop(timeout=0.1)  # Proses antrean pesan MQTT secara sinkron

# ==========================================
# OPTIMALISASI CACHE DATA (MENGURANGI DISK I/O)
# ==========================================
@st.cache_data
def fetch_realtime_data(update_token):
    return database.get_historical_data(limit=30)

@st.cache_data
def fetch_all_data(update_token):
    return database.get_all_data()

@st.cache_data
def fetch_summary(update_token):
    return database.get_analytics_summary()

# Mengambil data dari cache (hanya query ulang jika ada pesan MQTT baru)
df_realtime = fetch_realtime_data(st.session_state.last_updated)
df_all = fetch_all_data(st.session_state.last_updated)
summary = fetch_summary(st.session_state.last_updated)

# ==========================================
# LAYOUT WEB DASHBOARD (TABS)
# ==========================================
tab1, tab2 = st.tabs(["🌡️ Pemantauan Real-Time", "📊 Analitik & Riwayat Lengkap"])

# ──────────────────────────────────────────
# TAB 1: PEMANTAUAN REAL-TIME
# ──────────────────────────────────────────
with tab1:
    # 1. Metrik Indikator Besar
    col1, col2, col3 = st.columns(3)
    col1.metric("Suhu Lingkungan Saat Ini", f"{st.session_state.suhu} °C")
    col2.metric("Kelembaban Saat Ini", f"{st.session_state.hum} %")
    
    status_text = st.session_state.status
    if status_text == "NORMAL":
        col3.success(f"STATUS KONDISI: {status_text}")
    elif status_text == "PERINGATAN":
        col3.warning(f"STATUS KONDISI: {status_text}")
    elif status_text == "BAHAYA":
        col3.error(f"STATUS KONDISI: {status_text}")
    else:
        col3.info(f"STATUS KONDISI: {status_text}")
        
    st.divider()
    
    # 2. Kotak Analisis Perkembangan Maggot BSF
    st.subheader("🐛 Analisis Perkembangan Maggot BSF")
    maggot_status = st.session_state.status_maggot
    warna = st.session_state.warna_maggot
    
    # Render kotak dengan warna sesuai tingkat kedaruratan
    if maggot_status == "Optimal":
        st.success(f"### Kategori: **{maggot_status}**  \n**Rekomendasi Tindakan:** {st.session_state.rekomendasi}")
    elif maggot_status == "Cukup Baik":
        st.info(f"### Kategori: **{maggot_status}**  \n**Rekomendasi Tindakan:** {st.session_state.rekomendasi}")
    elif maggot_status == "Kurang Optimal":
        st.warning(f"### Kategori: **{maggot_status}**  \n**Rekomendasi Tindakan:** {st.session_state.rekomendasi}")
    elif maggot_status == "Berisiko":
        st.error(f"### Kategori: **{maggot_status}**  \n**Rekomendasi Tindakan:** {st.session_state.rekomendasi}")
    else:
        st.info(f"### Kategori: **{maggot_status}**  \n**Rekomendasi Tindakan:** {st.session_state.rekomendasi}")
        
    st.divider()
    
    # 3. Log Data Terbaru & Grafik Tren Jangka Pendek
    if not df_realtime.empty:
        st.subheader("📈 Riwayat Pergerakan Data (30 Data Terakhir)")
        col_tabel, col_grafik = st.columns([1, 2])
        
        with col_tabel:
            st.write("**Tabel Runtunan (Log):**")
            st.dataframe(df_realtime, use_container_width=True, hide_index=True)
            
        with col_grafik:
            st.write("**Grafik Fluktuasi Sensor:**")
            # Urutan waktu dibalik (kronologis) agar alur grafik mengarah ke kanan
            df_chart = df_realtime.iloc[::-1]
            st.line_chart(df_chart.set_index("Waktu")[["Suhu (°C)", "Kelembaban (%)"]])
    else:
        st.info("Menunggu aliran data dari sensor untuk merender log tabel dan grafik.")

# ──────────────────────────────────────────
# TAB 2: ANALITIK & RIWAYAT LENGKAP
# ──────────────────────────────────────────
with tab2:
    st.subheader("📊 Analitik Ringkasan Data Historis")
    
    # 1. KPI Cards
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    col_stat1.metric("Total Data Tersimpan", f"{summary['total_data']} baris")
    col_stat2.metric("Rata-rata Suhu", f"{summary['avg_temp']} °C")
    col_stat3.metric("Rata-rata Kelembaban", f"{summary['avg_hum']} %")
    
    st.divider()
    
    if not df_all.empty:
        col_an1, col_an2 = st.columns(2)
        
        # 2. Grafik Perkembangan Kondisi Maggot (Bar Chart Distribusi)
        with col_an1:
            st.write("**Distribusi Kondisi Pertumbuhan Maggot BSF:**")
            dist_data = summary['distribution']
            if dist_data:
                dist_df = pd.DataFrame(list(dist_data.items()), columns=["Status Maggot", "Jumlah Data"])
                st.bar_chart(dist_df.set_index("Status Maggot"), use_container_width=True)
            else:
                st.write("Belum ada sebaran data kondisi.")
                
        # 3. Grafik Tren Keseluruhan
        with col_an2:
            st.write("**Tren Fluktuasi Lingkungan Jangka Panjang:**")
            # Urutkan berdasarkan waktu terkecil (tertua ke terbaru) agar garis tren benar
            df_long_chart = df_all.sort_values(by="Waktu")
            st.line_chart(df_long_chart.set_index("Waktu")[["Suhu (°C)", "Kelembaban (%)"]], use_container_width=True)
            
        st.divider()
        
        # 4. Tabel Unduhan & Laporan Lengkap
        st.subheader("📥 Ekspor Laporan Telemetri")
        st.write(f"Menampilkan total {len(df_all)} data sensor yang terdaftar di database.")
        
        # Pembuatan Data Ekspor
        # CSV
        csv_data = df_all.to_csv(index=False).encode('utf-8')
        
        # Excel (.xlsx) dengan penanganan robust jika module excel belum terpasang
        excel_data = None
        excel_error = None
        try:
            excel_buffer = io.BytesIO()
            # Coba menggunakan xlsxwriter terlebih dahulu, fallback ke openpyxl
            try:
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    df_all.to_excel(writer, index=False, sheet_name='Data Sensor BSF')
            except ImportError:
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df_all.to_excel(writer, index=False, sheet_name='Data Sensor BSF')
            excel_data = excel_buffer.getvalue()
        except Exception as e:
            excel_error = str(e)
            
        col_btn1, col_btn2 = st.columns(2)
        
        # Tombol Download CSV
        col_btn1.download_button(
            label="📥 Download Laporan (CSV)",
            data=csv_data,
            file_name=f"laporan_budidaya_maggot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_csv"
        )
        
        # Tombol Download Excel
        if excel_data:
            col_btn2.download_button(
                label="📥 Download Laporan (Excel)",
                data=excel_data,
                file_name=f"laporan_budidaya_maggot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel"
            )
        else:
            col_btn2.warning("Gagal membuat berkas Excel. Silakan jalankan `pip install xlsxwriter openpyxl` di terminal laptop Anda.")
            
        st.divider()
        
        st.write("**Daftar Seluruh Log Data Sensor:**")
        st.dataframe(df_all, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data historis yang tersimpan di database.")

# ==========================================
# REFRESH LAYAR
# ==========================================
time.sleep(0.5)
st.rerun()
