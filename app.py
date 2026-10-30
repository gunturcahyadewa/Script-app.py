import streamlit as st
import pandas as pd
import time

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Multi-Tenant GPU Sharer Simulator",
    page_icon="🖥️",
    layout="wide"
)

# --- INISIALISASI STATE (PENYIMPANAN DATA SEMENTARA) ---
if "total_vram" not in st.session_state:
    st.session_state.total_vram = 24.0  # Total VRAM GPU Fisik (GB)
if "containers" not in st.session_state:
    st.session_state.containers = []
if "logs" not in st.session_state:
    st.session_state.logs = []

# --- HEADER ---
st.title("🖥️ Simulator Multi-Tenant GPU Sharer (vGPU)")
st.caption("Modul Praktikum Sistem Operasi - Kelompok 4")
st.markdown("---")

# --- SIDEBAR: KONTROL DAN ALOKASI VRAM ---
st.sidebar.header("⚙️ Pengaturan GPU & Kontainer")

# Input Batas VRAM GPU Fisik
st.session_state.total_vram = st.sidebar.number_input(
    "Total VRAM GPU Fisik (GB):",
    min_value=4.0,
    max_value=128.0,
    value=st.session_state.total_vram,
    step=4.0
)

st.sidebar.subheader("➕ Tambah Kontainer AI Baru")
container_name = st.sidebar.text_input("Nama Kontainer / Tenant:", placeholder="Contoh: LLM-Worker-1")
req_vram = st.sidebar.number_input("Alokasi VRAM yang Diminta (GB):", min_value=1.0, max_value=st.session_state.total_vram, value=4.0)
time_slice = st.sidebar.slider("Jatah Waktu Eksekusi / Time Slice (ms):", min_value=10, max_value=200, value=50)

# Menghitung Total VRAM Terpakai
used_vram = sum([c["vram"] for c in st.session_state.containers])
free_vram = st.session_state.total_vram - used_vram

# Tombol Tambah Kontainer dengan Validasi Isolasi Memori
if st.sidebar.button("Tambah Kontainer"):
    if not container_name:
        st.sidebar.error("⚠️ Nama kontainer tidak boleh kosong!")
    elif req_vram > free_vram:
        st.sidebar.error(f"❌ **VRAM Exceeded!** Sisa VRAM hanya {free_vram:.1f} GB, tetapi kontainer meminta {req_vram:.1f} GB.")
        st.session_state.logs.append(f"[ERROR] Permintaan {container_name} ({req_vram} GB) DITOLAK: VRAM tidak cukup.")
    else:
        st.session_state.containers.append({
            "id": len(st.session_state.containers) + 1,
            "name": container_name,
            "vram": req_vram,
            "time_slice": time_slice,
            "status": "Ready"
        })
        st.session_state.logs.append(f"[SUCCESS] Kontainer '{container_name}' berhasil dialokasikan VRAM {req_vram} GB.")
        st.rerun()

# Tombol Reset
if st.sidebar.button("🗑️ Reset Semua Kontainer"):
    st.session_state.containers = []
    st.session_state.logs = []
    st.rerun()

# --- UTAMA: MONITORING VRAM & DAFTAR KONTAINER ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 Status Penggunaan Memori (VRAM)")
    vram_percent = min(100.0, (used_vram / st.session_state.total_vram) * 100)
    st.progress(vram_percent / 100)
    st.metric(label="Penggunaan VRAM Total", value=f"{used_vram:.1f} / {st.session_state.total_vram:.1f} GB", delta=f"{free_vram:.1f} GB Bebas")

with col2:
    st.subheader("📦 Daftar Kontainer Terisolasi (Tenants)")
    if st.session_state.containers:
        df = pd.DataFrame(st.session_state.containers)
        st.dataframe(df[["id", "name", "vram", "time_slice", "status"]], use_container_width=True)
    else:
        st.info("Belum ada kontainer AI yang didaftarkan.")

st.markdown("---")

# --- SIMULASI PENJADWALAN TIME-SLICING ---
st.subheader("⏱️ Simulasikan Penjadwalan Eksekusi (Time-Slicing Scheduler)")

if st.button("▶️ Jalankan Simulasi Eksekusi GPU"):
    if not st.session_state.containers:
        st.warning("Tambahkan minimal 1 kontainer untuk menjalankan simulasi.")
    else:
        st.write("🔄 **Mulai mengeksekusi antrean eksekusi (Round-Robin Scheduling)...**")
        status_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        rounds = 3  # Simulasi 3 putaran eksekusi
        total_steps = len(st.session_state.containers) * rounds
        step = 0
        
        for r in range(rounds):
            for idx, container in enumerate(st.session_state.containers):
                step += 1
                # Ubah status kontainer yang sedang aktif
                for c in st.session_state.containers:
                    c["status"] = "Waiting"
                st.session_state.containers[idx]["status"] = "⚡ RUNNING ON GPU"
                
                # Tampilkan visual status
                status_placeholder.info(f"**Putaran {r+1}** | Sedang mengeksekusi: **{container['name']}** (Mendapat jatah {container['time_slice']} ms GPU Time)")
                progress_bar.progress(step / total_steps)
                
                time.sleep(0.8)  # Efek jeda untuk visualisasi
                
        # Kembalikan status ke Ready setelah selesai
        for c in st.session_state.containers:
            c["status"] = "Ready"
        status_placeholder.success("✅ **Simulasi eksekusi GPU selesai secara adil (Fair-Sharing)!**")

# --- LOG SISTEM ---
st.markdown("---")
st.subheader("📜 Log Aktivitas Kernel / GPU Manager")
with st.container():
    log_text = "\n".join(st.session_state.logs) if st.session_state.logs else "Belum ada log aktivitas."
    st.text_area("Log Output:", value=log_text, height=150, disabled=True)
