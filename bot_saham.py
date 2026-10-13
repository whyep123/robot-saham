import os
import requests
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import warnings
warnings.filterwarnings('ignore')

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def hitung_rsi(data_close, periode=14):
    """Menghitung indikator Relative Strength Index (RSI)"""
    delta = data_close.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=periode).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periode).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def kirim_foto(pesan, file_path):
    """Mengirim gambar grafik ke Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(file_path, "rb") as photo:
        payload = {"chat_id": CHAT_ID, "caption": pesan, "parse_mode": "Markdown"}
        requests.post(url, data=payload, files={"photo": photo})

def kirim_teks(pesan):
    """Mengirim pesan teks ke Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def main():
    # 1. Ambil IHSG
    try:
        ihsg = yf.Ticker("^JKSE").history(period="2d")
        tutup_sekarang = ihsg['Close'].iloc[-1]
        tutup_kemarin = ihsg['Close'].iloc[-2]
        persen_ihsg = ((tutup_sekarang - tutup_kemarin) / tutup_kemarin) * 100
        status_ihsg = "🟢 MENGUAT" if persen_ihsg >= 0 else "🔴 MELEMAH"
        pesan_utama = f"📊 *MARKET CLOSING*\nIHSG: {tutup_sekarang:,.0f} ({persen_ihsg:+.2f}%) {status_ihsg}\n\n"
    except:
        pesan_utama = "📊 *MARKET CLOSING*\nGagal mengambil IHSG.\n\n"

    # 2. Tarik Daftar Saham LQ45 Dinamis dari Wikipedia (Otomatis Update)
    try:
        url_wiki = "https://id.wikipedia.org/wiki/LQ45"
        tabel = pd.read_html(url_wiki)
        df_lq45 = tabel[1] if 'Kode' in tabel[1].columns else tabel[0]
        daftar_saham = [f"{kode}.JK" for kode in df_lq45['Kode'].tolist()]
    except:
        # Cadangan jika Wikipedia gagal diakses
        daftar_saham = ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK", "ASII.JK", "ADRO.JK", "AMMN.JK", "GOTO.JK", "PGAS.JK", "MEDC.JK"]

    strong_watchlist = []
    early_radar = []
    maks_chart = 3 # Membatasi gambar agar tidak spam
    chart_count = 0

    # 3. Proses Screening Tingkat Lanjut
    for saham in daftar_saham:
        try:
            data = yf.Ticker(saham).history(period="60d")
            if len(data) < 30: continue

            close = data['Close']
            volume = data['Volume']
            
            # Kalkulasi Indikator
            ma20 = close.rolling(20).mean()
            vol_avg = volume.rolling(20).mean()
            rsi = hitung_rsi(close, 14)

            harga_skrg = close.iloc[-1]
            persen = ((harga_skrg - close.iloc[-2]) / close.iloc[-2]) * 100
            
            vol_ratio = volume.iloc[-1] / vol_avg.iloc[-2] if vol_avg.iloc[-2] > 0 else 0
            rsi_skrg = rsi.iloc[-1]
            ma20_skrg = ma20.iloc[-1]

            kode = saham.replace(".JK", "")

            # Format Jurnal untuk Paper Trading
            tp = harga_skrg * 1.05 # Target Profit +5%
            sl = ma20_skrg * 0.98 if harga_skrg > ma20_skrg else harga_skrg * 0.95 # SL di bawah MA20
            
            info_plan = (f"   ↳ 🎯 *Plan*: Buy Rp{harga_skrg:,.0f} | TP Rp{tp:,.0f} | SL Rp{sl:,.0f}\n"
                         f"   ↳ ⚙️ Vol: {vol_ratio:.1f}x | RSI: {rsi_skrg:.0f}\n")

            # KATEGORI 1: Strong Watchlist (Volume Breakout + Uptrend di atas MA20 + RSI Kuat)
            if persen > 0 and vol_ratio >= 1.5 and harga_skrg > ma20_skrg and rsi_skrg > 50:
                strong_watchlist.append(f"🚀 *{kode}* ({persen:+.2f}%)\n" + info_plan)
                
                # Buat dan Kirim Gambar Grafik Candlestick
                if chart_count < maks_chart:
                    df_chart = data.tail(40)
                    ap = mpf.make_addplot(df_chart['Close'].rolling(20).mean(), color='blue', width=1.5)
                    file_nama = f"chart_{kode}.png"
                    mpf.plot(df_chart, type='candle', volume=True, addplot=ap, style='yahoo', 
                             savefig=file_nama, title=f"{kode} - MA20 (Garis Biru)")
                    
                    teks_foto = f"Analisa {kode}: Harga Uptrend menembus MA20 dengan lonjakan volume."
                    kirim_foto(teks_foto, file_nama)
                    chart_count += 1

            # KATEGORI 2: Early Radar (Bottom Fishing, Rebound dari Oversold)
            elif persen > 0 and vol_ratio >= 1.2 and rsi_skrg < 45:
                early_radar.append(f"👀 *{kode}* ({persen:+.2f}%)\n" + info_plan)

        except Exception:
            continue

    # 4. Susun Pesan Rekap
    pesan_rekap = "🔥 *STRONG WATCHLIST (Uptrend & Volume Spike)*\n"
    pesan_rekap += "".join(strong_watchlist) if strong_watchlist else "_Tidak ada sinyal Strong hari ini_.\n"

    pesan_rekap += "\n🌱 *EARLY RADAR (Potensi Rebound/Bottom Fishing)*\n"
    pesan_rekap += "".join(early_radar) if early_radar else "_Tidak ada sinyal Rebound hari ini_.\n"

    kirim_teks(pesan_rekap)

if __name__ == "__main__":
    main()
