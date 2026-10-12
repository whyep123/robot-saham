import os
import requests
import pandas as pd
import yfinance as yf

# Mengambil kunci dan alamat dari brankas
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Daftar saham yang mau dipantau robot
SAHAM = ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK", "GOTO.JK"]

def tugas_robot():
    pesan = "Halo boss! Ini laporan saham sore ini:\n\n"
    
    # Robot mengecek saham satu per satu
    for nama in SAHAM:
        try:
            # Mengambil data saham hari ini
            data = yf.Ticker(nama)
            info = data.history(period="1d")
            
            if not info.empty:
                harga_tutup = int(info['Close'].iloc[0])
                pesan += f"📈 {nama}: Rp {harga_tutup:,}\n"
        except:
            pesan += f"❓ {nama}: Gagal dicek\n"
            
    pesan += "\nSemoga cuan ya boss! 🚀"
    
    # Mengirim surat ke Telegram
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": pesan})

# Menyuruh robot bekerja
if __name__ == "__main__":
    tugas_robot()
