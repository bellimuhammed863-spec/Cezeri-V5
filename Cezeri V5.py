import tkinter as tk
import os
from tkinter import simpledialog
from PIL import Image, ImageTk
import time
import requests
import speech_recognition as sr
import threading
import webbrowser
from datetime import datetime, timedelta
import re
import urllib.parse
import asyncio
import edge_tts
import pygame
import uuid
import pyautogui
from dotenv import load_dotenv

son_konu = ""
sohbetler = []
aktif_sohbet = None


bg_ana = "#050d1a"
bg_panel = "#081a2e"
mavi = "#00bfff"
acik_mavi = "#00e5ff"


gorevler = []
calisan_gorevler = []


pygame.mixer.init()



async def speak_async(text):
    file_name = f"voice_{uuid.uuid4()}.mp3"
    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice="tr-TR-EmelNeural"
        )
        await communicate.save(file_name)
        pygame.mixer.music.load(file_name)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)
    except Exception as e:
        print("Seslendirme hatası:", repr(e))
    finally:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
            except OSError:
                pass


def seslendirme(metin):
    threading.Thread(
        target=lambda: asyncio.run(speak_async(metin)),
        daemon=True
    ).start()



def seslendirme(metin):
    threading.Thread(target=lambda: asyncio.run(speak_async(metin)), daemon=True).start()



load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


def yapay_zeka_cevap(soru):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "openai/gpt-oss-20b",
            "messages": [
                {"role": "system",
                 "content": "Sen CEZERİ adlı gelişmiş Türk yapay zeka asistanısın. Yaşlı kullanıcılar için basit anlat.Karmaşık teknik terimler kullanma.adım adım anlat. Kısa cümleler kur"},
                {"role": "user", "content": soru}
            ],
            "temperature": 0.7
        }
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        return None
    except Exception as e:
        print(f"AI Hatası: {e}")
        return None



GOREV_DOSYA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gorevler.txt")

if os.path.exists(GOREV_DOSYA):
    with open(GOREV_DOSYA, "r", encoding="utf-8") as f:
        for satir in f:
            satir = satir.strip()
            if "|" in satir:
                saat, gorev = satir.split("|", 1)
                gorevler.append((saat, gorev))


def gorevleri_kaydet():
    with open(GOREV_DOSYA, "w", encoding="utf-8") as f:
        for g in gorevler:
            f.write(g[0] + "|" + g[1] + "\n")



def rounded_button(parent, text, command, width=200, height=50, r=25, color="#00bfff"):
    canvas = tk.Canvas(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, cursor="hand2")

    def draw():
        canvas.delete("all")
        canvas.create_arc(0, 0, 2 * r, 2 * r, start=90, extent=90, fill=color, outline=color)
        canvas.create_arc(width - 2 * r, 0, width, 2 * r, start=0, extent=90, fill=color, outline=color)
        canvas.create_arc(width - 2 * r, height - 2 * r, width, height, start=270, extent=90, fill=color, outline=color)
        canvas.create_arc(0, height - 2 * r, 2 * r, height, start=180, extent=90, fill=color, outline=color)
        canvas.create_rectangle(r, 0, width - r, height, fill=color, outline=color)
        canvas.create_rectangle(0, r, width, height - r, fill=color, outline=color)
        canvas.create_text(width // 2, height // 2, text=text, fill="white", font=("Arial", 12, "bold"))

    draw()
    canvas.bind("<Button-1>", lambda e: command())
    return canvas



def doviz_cevir(kaynak, hedef, miktar=1):
    try:
        url = f"https://open.er-api.com/v6/latest/{kaynak}"
        data = requests.get(url, timeout=5).json()
        if "rates" in data and hedef in data["rates"]:
            return round(data["rates"][hedef] * miktar, 2)
        return None
    except:
        return None


def haberler():
    try:
        url = "https://api.rss2json.com/v1/api.json?rss_url=https://feeds.bbci.co.uk/turkce/rss.xml"
        data = requests.get(url, timeout=5).json()
        basliklar = [item["title"] for item in data.get("items", [])[:5]]
        return "\n".join(f"{i}. {h}" for i, h in enumerate(basliklar, 1)) if basliklar else "Haber yüklenemedi"
    except:
        return "Haberler alınamadı. İnternet bağlantınızı kontrol edin."


durum_ceviri = {
    "Sunny": "Güneşli", "Clear": "Açık", "Partly cloudy": "Parçalı bulutlu",
    "Cloudy": "Bulutlu", "Overcast": "Kapalı", "Mist": "Sisli",
    "Patchy rain nearby": "Yer yer yağmurlu", "Light rain": "Hafif yağmur",
    "Moderate rain": "Orta şiddetli yağmur", "Heavy rain": "Şiddetli yağmur", "Thunderstorm": "Fırtına",
}


def hava_durumu(sehir):
    try:
        url = f"https://wttr.in/{urllib.parse.quote(sehir)}?format=j1"
        data = requests.get(url, timeout=5).json()
        durum = data["current_condition"][0]["weatherDesc"][0]["value"]
        sicaklik = data["current_condition"][0]["temp_C"]
        durum_tr = durum_ceviri.get(durum, durum)
        return f"{sehir} için hava: {durum_tr}, {sicaklik}°C"
    except:
        return f"'{sehir}' için hava durumu alınamadı."



def cezeri_cevap(veri):
    cevaplar = {
        "nasılsın": "İyiyim, sen nasılsın?",
        "adın ne": "Ben CEZERİ, senin kişisel yapay zeka asistanın!",
        "teşekkür": "Rica ederim, yardımcı olabildiğim için mutluyum!",
        "hoşça kalın": "Hoşça kalın! Tekrar görüşmek üzere.",
        "bye": "Hoşça kalın! Tekrar görüşmek üzere.",
        "selam": "Selam! Nasılsın?",
        "merhaba": "Merhaba! Size nasıl yardımcı olabilirim?"
    }
    for anahtar, cevap in cevaplar.items():
        if anahtar in veri:
            return cevap
    return None



form = tk.Tk()
form.title("CEZERİ V5 - Yapay Zeka Asistanı")
form.state("zoomed")
form.config(bg=bg_ana)


GORSEL_YOLU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cezeri_splash.png")

splash_frame = tk.Frame(form, bg="black")
splash_frame.place(relwidth=1, relheight=1)

try:
    img = Image.open(GORSEL_YOLU).resize((1200, 700))
    bg_img = ImageTk.PhotoImage(img)
    label = tk.Label(splash_frame, image=bg_img)
    label.place(relwidth=1, relheight=1)
except FileNotFoundError:
    tk.Label(splash_frame, text="CEZERİ V5", fg=acik_mavi, bg="black",
             font=("Times", 60, "bold")).place(relx=0.5, rely=0.5, anchor="center")


sol_frame = tk.Frame(form, bg=bg_panel, width=250)
sol_frame.pack(side="left", fill="y")
sol_frame.pack_propagate(False)

baslik_sol = tk.Label(sol_frame, text="🤖 CEZERİ", fg=acik_mavi, bg=bg_panel, font=("Arial", 16, "bold"))
baslik_sol.pack(pady=15)


def yeni_sohbet():
    global aktif_sohbet
    yeni = {"ad": "Yeni Sohbet", "mesajlar": []}
    sohbetler.append(yeni)
    aktif_sohbet = yeni
    chat_listbox.insert("end", yeni["ad"])
    mesaj_alani.delete("1.0", "end")


def sohbet_sec(event):
    global aktif_sohbet
    if not chat_listbox.curselection():
        return
    secim = chat_listbox.get(chat_listbox.curselection())
    for s in sohbetler:
        if s["ad"] == secim:
            aktif_sohbet = s
            mesaj_alani.delete("1.0", "end")
            for rol, metin in s["mesajlar"]:
                prefix = "Cezeri: " if rol == "cezeri" else "Sen: "
                mesaj_alani.insert("end", prefix + metin + "\n")
            break


def sohbet_sil():
    if not chat_listbox.curselection():
        return
    index = chat_listbox.curselection()[0]
    chat_listbox.delete(index)
    del sohbetler[index]


menu = tk.Menu(form, tearoff=0)
menu.add_command(label="Sil", command=sohbet_sil)


def sag_tik(event):
    try:
        chat_listbox.selection_clear(0, "end")
        chat_listbox.selection_set(chat_listbox.nearest(event.y))
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()


rounded_button(sol_frame, "➕ Yeni Sohbet", yeni_sohbet, width=220, height=45).pack(pady=10)

chat_listbox = tk.Listbox(sol_frame, bg="#081a2e", fg="white", font=("Arial", 16, "bold"), bd=0, relief="flat",
                          highlightthickness=0, selectbackground="#00bfff", selectforeground="white",
                          activestyle="none")
chat_listbox.bind("<Button-3>", sag_tik)
chat_listbox.bind("<<ListboxSelect>>", sohbet_sec)
chat_listbox.pack(fill="both", expand=True, padx=10, pady=(40, 10))


sag_frame = tk.Frame(form, bg=bg_ana)
sag_frame.pack(side="right", fill="both", expand=True)

baslik = tk.Label(sag_frame, text="CEZERİ V5 - Yapay Zeka Asistanı", fg=acik_mavi, bg=bg_ana,
                  font=("Times", 35, "bold"))
baslik.pack(pady=10)

mesaj_frame = tk.Frame(sag_frame)
mesaj_frame.pack(fill="both", expand=True, padx=20, pady=(10, 10))

mesaj_alani = tk.Text(mesaj_frame, bg="#081a2e", fg="#e2e8f0", font=("Consolas", 12),
                      insertbackground="white", wrap="word")
mesaj_alani.place(relwidth=1, relheight=1)

scroll = tk.Scrollbar(mesaj_frame, command=mesaj_alani.yview)
scroll.place(relx=0.98, rely=0, relheight=1)
mesaj_alani.config(yscrollcommand=scroll.set)


overlay_frame = tk.Frame(mesaj_frame, bg="#081a2e")
overlay_frame.place(relwidth=1, relheight=1)

try:
    img2 = Image.open(GORSEL_YOLU).resize((1700, 1000))
    overlay_img = ImageTk.PhotoImage(img2)
    overlay_lbl = tk.Label(overlay_frame, image=overlay_img, bg="#081a2e")
    overlay_lbl.place(relwidth=1, relheight=1)
except FileNotFoundError:
    pass

_overlay_gizlendi = False


def overlay_kapat():
    global _overlay_gizlendi
    if not _overlay_gizlendi:
        overlay_frame.place_forget()
        _overlay_gizlendi = True


def sohbet_adi_olustur(mesaj):
    gereksiz = ["cezeri", "acaba", "lütfen", "bir", "şey", "bana", "için", "hakkında", "whatsapp", "yaz", "aç", "misin",
                "mısın"]
    kelimeler = mesaj.strip().split()
    temiz = [k.capitalize() for k in kelimeler if k.lower() not in gereksiz]
    baslik = " ".join(temiz[:3])
    return baslik[:30] if len(baslik) >= 3 else "Yeni Sohbet"



def mesaj_ekle(metin, rol="cezeri"):
    def _ekle():
        if aktif_sohbet is not None:
            aktif_sohbet["mesajlar"].append((rol, metin))
        overlay_kapat()
        prefix = "Cezeri: " if rol == "cezeri" else "Sen: "
        mesaj_alani.insert("end", prefix + metin + "\n")
        mesaj_alani.see("end")
        if rol == "cezeri":
            seslendirme(metin)

    form.after(0, _ekle)



def dinle():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.8)
            r.energy_threshold = 300
            r.dynamic_energy_threshold = True
            ses = r.listen(source, timeout=5, phrase_time_limit=8)
        veri = r.recognize_google(ses, language="tr-TR").lower()
        return veri.replace("cezeri", "").strip() if "cezeri" in veri else ""
    except:
        return ""


def surekli_dinle():
    while True:
        veri = dinle()
        if veri:
            def _ses_mesaj(v=veri):
                overlay_kapat()
                mesaj_alani.insert("end", "Sen (ses): " + v + "\n")
                mesaj_alani.see("end")

            form.after(0, _ses_mesaj)
            gonder_mantigi(veri)



def youtube_ac(aranacak):
    query = urllib.parse.quote(aranacak)
    webbrowser.open(f"https://www.youtube.com/results?search_query={query}&sp=EgIQAQ%3D%3D")



def whatsapp_mesaj_gonder(kisi, mesaj):
    try:
        mesaj_ekle(f"{kisi} kişisine '{mesaj}' gönderiliyor...")
        windows_uygulama_ac("WhatsApp")
        time.sleep(3)
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.8)
        pyautogui.typewrite(kisi, interval=0.05)
        time.sleep(1.5)
        pyautogui.press("down")
        pyautogui.press("enter")
        time.sleep(0.8)
        pyautogui.typewrite(mesaj, interval=0.03)
        time.sleep(0.3)
        pyautogui.press("enter")
    except Exception as e:
        mesaj_ekle(f"WhatsApp hatası: {e}")


def whatsapp_arama_yap(kisi):

    windows_uygulama_ac("WhatsApp")

    time.sleep(3)

    pyautogui.hotkey("ctrl", "f")

    time.sleep(1)

    pyautogui.write(kisi)

    time.sleep(2)

    pyautogui.press("enter")

    time.sleep(1)

    pyautogui.hotkey("ctrl", "shift", "c")


def kisi_adi_temizle(isim):
    ekler = ["ye", "ya", "e", "a", "de", "da", "te", "ta", "nin", "nın", "nun", "nün", "ime", "ıma", "uma", "üme", "m",
             "im"]
    for ek in ekler:
        if isim.endswith(ek):
            return isim[:-len(ek)].strip()
    return isim.strip()



def windows_uygulama_ac(uygulama_adi):
    pyautogui.press("win")
    time.sleep(0.8)
    pyautogui.typewrite(uygulama_adi, interval=0.05)
    time.sleep(0.8)
    pyautogui.press("enter")



def dogal_gorev_ekle(veri):
    dk_eslesme = re.search(r"(\d+)\s*dakika", veri)
    st_eslesme = re.search(r"(\d+)\s*saat", veri)
    simdi = datetime.now()
    if dk_eslesme:
        hedef = simdi + timedelta(minutes=int(dk_eslesme.group(1)))
    elif st_eslesme:
        hedef = simdi + timedelta(hours=int(st_eslesme.group(1)))
    else:
        return None
    gorev = re.sub(r"\d+\s*dakika\s*sonra", "", veri)
    gorev = re.sub(r"\d+\s*saat\s*sonra", "", gorev)
    gorev = gorev.replace("hatırlat", "").strip()
    saat_str = hedef.strftime("%H:%M")
    gorevler.append((saat_str, gorev))
    gorevleri_kaydet()
    return f"{saat_str} için görev eklendi: {gorev}"


def gorev_ekle():
    pencere = tk.Toplevel()
    pencere.title("Görev Ekle")
    pencere.geometry("300x200")
    tk.Label(pencere, text="Saat (HH:MM):").pack(pady=5)
    saat_entry = tk.Entry(pencere)
    saat_entry.pack()
    tk.Label(pencere, text="Görev:").pack(pady=5)
    gorev_entry = tk.Entry(pencere)
    gorev_entry.pack()

    def kaydet():
        saat = saat_entry.get()
        gorev = gorev_entry.get()
        if saat and gorev:
            gorevler.append((saat, gorev))
            gorevleri_kaydet()
            mesaj_ekle(f"Görev eklendi: {saat} - {gorev}")
            pencere.destroy()

    tk.Button(pencere, text="Kaydet", command=kaydet).pack(pady=10)


def gorevleri_goster():
    cevap = "GÖREVLER:\n" + "\n".join(f"{g[0]} → {g[1]}" for g in gorevler) if gorevler else "Hiç görev yok."
    mesaj_ekle(cevap)


def gorev_sil():
    gorev_adi = simpledialog.askstring("Sil", "Silinecek görevi yaz:")
    if gorev_adi is None:
        return
    for g in gorevler:
        if g[1].lower() == gorev_adi.lower():
            gorevler.remove(g)
            gorevleri_kaydet()
            mesaj_ekle("Görev silindi.")
            return
    mesaj_ekle("Görev bulunamadı.")


def gorev_kontrol():
    simdi = time.strftime("%H:%M")
    for g in gorevler:
        if g[0] == simdi and g not in calisan_gorevler:
            mesaj_ekle(f"Saat {g[0]}! {g[1]} görevini hatırlatmamı istemiştiniz.")
            calisan_gorevler.append(g)
    form.after(1000, gorev_kontrol)



def gonder_mantigi(veri):
    global son_konu

    dogal = dogal_gorev_ekle(veri)
    if dogal:
        mesaj_ekle(dogal)

        return

    cevap = None


    if "whatsapp" in veri and "yaz" in veri:
        temiz = veri.replace("whatsapp", "").strip()
        if " yaz" in temiz:
            parcalar = temiz.split(" yaz")[0]
            kelimeler = parcalar.split()
            if len(kelimeler) >= 2:
                kisi = kisi_adi_temizle(kelimeler[0])
                mesaj = " ".join(kelimeler[1:])
                threading.Thread(target=lambda: whatsapp_mesaj_gonder(kisi, mesaj), daemon=True).start()
                return


    elif "ara" in veri:

        kisi = veri.replace("ara", "").strip()

        cevap = f"{kisi} aranıyor."

        threading.Thread(
            target=lambda: whatsapp_arama_yap(kisi),
            daemon=True
        ).start()


    elif any(k in veri for k in ["video", "şarkı", "izle", "dinle", "çal"]):
        aranacak = veri
        for kelime in ["cezeri", "aç", "izle", "dinle", "şarkısını", "videosunu"]:
            aranacak = aranacak.replace(kelime, "")
        aranacak = aranacak.strip()
        if aranacak:
            form.after(0, lambda: youtube_ac(aranacak))
            cevap = f"{aranacak} YouTube'da açılıyor"


    elif "dolar" in veri:
        sonuc = doviz_cevir("USD", "TRY")
        cevap = f"1 Dolar = {sonuc} TL" if sonuc else "Kur bilgisi alınamadı."
    elif "euro" in veri:
        sonuc = doviz_cevir("EUR", "TRY")
        cevap = f"1 Euro = {sonuc} TL" if sonuc else "Kur bilgisi alınamadı."


    elif "hava" in veri:
        eslesme = re.search(r"(\w+)\s*(?:hava|hava durumu)", veri)
        sehir = eslesme.group(1) if eslesme else "Istanbul"
        cevap = hava_durumu(sehir)


    elif "haber" in veri:
        cevap = haberler()


    elif "görev" in veri:
        cevap = "\n".join(f"{g[0]} → {g[1]}" for g in gorevler) if gorevler else "Görev yok."


    elif "bilgisayarı kapat" in veri:
        cevap = "Bilgisayar kapatılıyor."
        os.system("shutdown /s /t 1")
    elif "yeniden başlat" in veri:
        cevap = "Bilgisayar yeniden başlatılıyor."
        os.system("shutdown /r /t 1")
    elif "cezeriyi kapat" in veri or "çıkış yap" in veri:
        cevap = "Kendimi kapatıyorum efendim."
        mesaj_ekle(cevap)
        form.after(2000, form.destroy)
        return


    elif "aç" in veri:
        uygulama = veri.replace("aç", "").replace("uygulamasını", "").replace("uygulama", "").strip()
        cevap = f"{uygulama} açılıyor."
        threading.Thread(target=lambda: windows_uygulama_ac(uygulama), daemon=True).start()


    elif any(k in veri for k in ["saat", "zaman"]):
        cevap = time.strftime("%H:%M:%S")
    elif any(k in veri for k in ["tarih", "gün"]):
        cevap = time.strftime("%d.%m.%Y")


    if not cevap:
        cevap = cezeri_cevap(veri)
        if not cevap:
            ai_cevap = yapay_zeka_cevap(veri)
            cevap = ai_cevap if ai_cevap else "Şu an düşünemiyorum, internet bağlantını kontrol eder misin?"

    if cevap:
        mesaj_ekle(cevap)
    if veri.strip():
        son_konu = veri



alt_frame = tk.Frame(sag_frame, bg=bg_ana)
alt_frame.pack(fill="x", padx=20, pady=(5, 15))

entry = tk.Entry(alt_frame, font=("Consolas", 14), bd=0, bg="#081a2e", fg="white", insertbackground="white")
entry.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=8)


def gonder(event=None):
    if splash_frame.winfo_ismapped():
        splash_frame.place_forget()
    veri = entry.get().lower()
    if veri:
        if aktif_sohbet and aktif_sohbet["ad"] == "Yeni Sohbet":
            aktif_sohbet["ad"] = sohbet_adi_olustur(veri)
            secili_index = sohbetler.index(aktif_sohbet)
            chat_listbox.delete(secili_index)
            chat_listbox.insert(secili_index, aktif_sohbet["ad"])
        mesaj_ekle(veri, rol="sen")
        entry.delete(0, "end")
        threading.Thread(target=gonder_mantigi, args=(veri,), daemon=True).start()


entry.bind("<Return>", gonder)

gonder_btn = rounded_button(alt_frame, "Gönder", gonder, width=110, height=40, r=15)
gonder_btn.pack(side="right", padx=10)


rounded_button(sol_frame, "➕ Görev Ekle", gorev_ekle, width=220, height=45).pack(pady=10, padx=10)
rounded_button(sol_frame, "📋 Görevleri Göster", gorevleri_goster, width=220, height=45).pack(pady=10, padx=10)
rounded_button(sol_frame, "❌ Görev Sil", gorev_sil, width=220, height=45).pack(pady=10, padx=10)

tk.Frame(sol_frame, bg=bg_panel).pack(fill="both", expand=True)

info_label = tk.Label(sol_frame, text="v5.0 - AI Powered\n🎤 Dinleme Aktif",
                      fg=mavi, bg=bg_panel, font=("Arial", 9), justify="center")
info_label.pack(pady=10)


yeni_sohbet()
gorev_kontrol()
threading.Thread(target=surekli_dinle, daemon=True).start()
mesaj_ekle("Hoş geldiniz efendim. Sizin için ne yapabilirim?")

form.mainloop()

