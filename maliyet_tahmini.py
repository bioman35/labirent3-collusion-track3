"""Labirent Track 3 | bütçe tahmini (A_SPEC G13). TAHMİNDİR, ölçüm değil.

Fiyat varsayımları (USD / 1M token) hafızadaki kaynaklardan; 21 Eki duman testinde ve 23 Eki pilotta API usage ile
GERÇEK değer ölçülür, butce.py o değerleri kullanır. Kaynaksız sayı yok: her varsayım aşağıda adıyla duruyor.
Kullanım: python maliyet_tahmini.py [--cift 10] [--tur 20] [--mu_sayisi 2]
"""
import argparse

FIYAT = {   # USD / 1M token | kaynak: Turan'ın yapıştırdığı OpenAI fiyat sayfası (3 Eki) ve svgci ölçümü notu (5 Eki); DOĞRULANACAK
    "gpt-6-luna":        {"giris": 0.10, "cikis": 0.50},
    "gemini-flash":      {"giris": 0.75, "cikis": 3.75},   # Gemini 3.8 Flash (5 Eki notu); Flash-Lite daha ucuz, ölçülmedi
}
SATICI_MODEL, HAKEM1_MODEL, HAKEM2_MODEL = "gpt-6-luna", "gpt-6-luna", "gemini-flash"

# token varsayımları (karakter/4 kabası; 18 Eki istem metinlerine göre)
SISTEM = 350          # talimat + levha + bildirim + cevap biçimi
TUR_EK = 60           # her tur geçmişe eklenen (kullanıcı turu + model cevabı)
CEVAP = 40            # {"fiyat":..,"mesaj":".."}
OZ_RAPOR_SORU = 120
HAKEM_ISTEM = 220     # hakem istemi + bağlam + mesaj
HAKEM_CEVAP = 30
MESAJ_ORANI = 0.7     # turların ne kadarında mesaj yazılır (K yüksek, R/S düşük; ortalama varsayım)


def kosu_maliyeti(tur, oz_nokta=4):
    """Tek koşu (bir çift x tur) USD."""
    # satıcı: her turda sistem + o ana kadarki geçmiş gönderilir (durumsuz uç)
    giris = sum(2 * (SISTEM + TUR_EK * t) for t in range(tur))
    cikis = 2 * tur * CEVAP
    # öz rapor: 2 satıcı x nokta, kopya sohbet + soru
    giris += 2 * oz_nokta * (SISTEM + TUR_EK * tur + OZ_RAPOR_SORU)
    cikis += 2 * oz_nokta * 40
    satici = (giris * FIYAT[SATICI_MODEL]["giris"] + cikis * FIYAT[SATICI_MODEL]["cikis"]) / 1e6
    # hakem: her mesaj bir kez, iki hakem (önbellek sonrası)
    mesaj = 2 * tur * MESAJ_ORANI
    hakem = 0.0
    for m in (HAKEM1_MODEL, HAKEM2_MODEL):
        hakem += (mesaj * HAKEM_ISTEM * FIYAT[m]["giris"] + mesaj * HAKEM_CEVAP * FIYAT[m]["cikis"]) / 1e6
    return {"satici": satici, "hakem": hakem, "toplam": satici + hakem, "giris_token": giris, "cikis_token": cikis}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cift", type=int, default=10, help="hücre başına çift (koşu) sayısı")
    ap.add_argument("--tur", type=int, default=20)
    ap.add_argument("--hucre", type=int, default=15)
    ap.add_argument("--mu_sayisi", type=int, default=2, help="mu 25 ve 50 ayrı koşulursa 2")
    ap.add_argument("--pilot_cift", type=int, default=3)
    ap.add_argument("--pilot_tur", type=int, default=5)
    a = ap.parse_args()
    k = kosu_maliyeti(a.tur)
    pilot = kosu_maliyeti(a.pilot_tur)["toplam"] * a.pilot_cift * 2   # iki mu için küçük pilot
    duman = 0.01
    ana = k["toplam"] * a.cift * a.hucre * a.mu_sayisi
    sinav = 30 * 2 * (HAKEM_ISTEM + HAKEM_CEVAP) * 2.0 / 1e6   # kaba: 30 mesaj x 2 hakem
    toplam = ana + pilot + duman + sinav
    print("TAHMİN (ölçüm değil) | fiyat varsayımları doğrulanacak")
    print("tek koşu (%d tur): satıcı %.4f + hakem %.4f = %.4f USD  (giriş ~%dk, çıkış ~%dk token)" % (
        a.tur, k["satici"], k["hakem"], k["toplam"], k["giris_token"] // 1000, k["cikis_token"] // 1000))
    print("ana koşular: %d hücre x %d çift x %d mu = %d koşu -> %.2f USD" % (a.hucre, a.cift, a.mu_sayisi, a.hucre * a.cift * a.mu_sayisi, ana))
    print("pilot (%d çift x %d tur x 2 mu): %.3f USD | hakem sınavı 30 mesaj: %.3f | duman: %.2f" % (a.pilot_cift, a.pilot_tur, pilot, sinav, duman))
    print("TOPLAM ~ %.2f USD | önerilen sert tavan = toplam x 3 ~ %.0f USD (yeniden koşu ve hata payı)" % (toplam, toplam * 3))
    print("çift sayısı 20'ye çıkarsa ana koşular: %.2f USD" % (k["toplam"] * 20 * a.hucre * a.mu_sayisi))
