import os
import requests
import yfinance as yf
import pandas as pd

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def kirim_surat(isi_pesan):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": isi_pesan, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def main():
    # 1. Mengambil ringkasan IHSG
    try:
        ihsg = yf.Ticker("^JKSE").history(period="2d")
        tutup_sekarang = ihsg['Close'].iloc[-1]
        tutup_kemarin = ihsg['Close'].iloc[-2]
        persen_ihsg = ((tutup_sekarang - tutup_kemarin) / tutup_kemarin) * 100
        status_ihsg = "🟢 MENGUAT" if persen_ihsg >= 0 else "🔴 MELEMAH"
        
        pesan = f"📊 *MARKET CLOSING SORE INI*\n"
        pesan += f"IHSG: {tutup_sekarang:,.0f} ({persen_ihsg:+.2f}%) {status_ihsg}\n\n"
    except Exception:
        pesan = "📊 *MARKET CLOSING SORE INI*\nGagal mengambil data IHSG.\n\n"

    # 2. Daftar Saham yang ingin selalu dipantau (Bisa Anda tambah/ubah sendiri)
    # Gunakan akhiran .JK untuk saham Indonesia
    daftar_saham = [
        "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK", 
        "ASII.JK", "ADRO.JK", "AMMN.JK", "GOTO.JK", "BRPT.JK", "PGAS.JK"
    ]
    
    pesan += "🎯 *RADAR SWING TRADING BESOK:*\n"
    ada_saham = False
    
    # 3. Proses Screening (Penyaringan)
    for saham in daftar_saham:
        try:
            # Ambil data 20 hari ke belakang untuk mencari rata-rata volume
            data = yf.Ticker(saham).history(period="20d")
            if len(data) < 20: 
                continue
            
            harga_skrg = data['Close'].iloc[-1]
            harga_kmrn = data['Close'].iloc[-2]
            persen = ((harga_skrg - harga_kmrn) / harga_kmrn) * 100
            
            vol_skrg = data['Volume'].iloc[-1]
            # Menghitung rata-rata volume 19 hari sebelumnya
            rata_vol = data['Volume'].iloc[:-1].mean() 
            vol_ratio = vol_skrg / rata_vol if rata_vol > 0 else 0
            
            # ----------------------------------------------------
            # KRITERIA SCREENING:
            # 1. Harga ditutup naik (hijau)
            # 2. Volume hari ini minimal 1.2x lipat lebih besar dari rata-rata (Volume Spike)
            # ----------------------------------------------------
            if persen > 0 and vol_ratio >= 1.2:
                kode = saham.replace(".JK", "")
                pesan += f"🚀 *{kode}* : Rp{harga_skrg:,.0f} ({persen:+.2f}%)\n"
                pesan += f"   ↳ Lonjakan Volume: {vol_ratio:.1f}x lipat\n"
                ada_saham = True
                
        except Exception:
            continue
            
    if not ada_saham:
        pesan += "_Tidak ada saham di radar yang mengalami lonjakan volume hari ini._\n"
        
    pesan += "\n⚠️ _Disclaimer: Data hasil screening kuantitatif otomatis. Tetap lakukan analisa chart (DYOR)!_"
    
    # 4. Kirim ke Telegram
    kirim_surat(pesan)

if __name__ == "__main__":
    main()
