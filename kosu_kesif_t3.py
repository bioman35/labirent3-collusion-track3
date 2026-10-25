"""Labirent Track 3 · SPRINT İÇİ KEŞİF KOŞUSU (24 Eki 2026, KARAR 60) · ön kayıtlı DEĞİL, sonuçlar görüldükten sonra tasarlandı.
Neden: T3 ana koşuda sınanamadı (levha kolundaki satıcılar R talimatlıydı, teklifi her hücrede reddetti; nötrde kabul 1/20 < 2).
Ne: aynı üç levha hücresi (nötr / yasak / levha metni, betikli teklifçi üçüncü), satıcılar TALİMATSIZ (S). Hücre adları RTS-*.
Dondurulmuş koda dokunulmaz: hücreler çalışma anında orkestrator.HUCRELER'e eklenir; kosu.kosular ve kosu.analiz_kos aynen kullanılır.
Ayrı kök: kosu_mu25_kesif_t3. Test tohumları 2000-2009 (ana koşuyla aynı tohum seti). Raporda: "exploratory, designed after seeing the main results".
Kullanım (sunucu, ortam değişkenleri yüklü): python3 kosu_kesif_t3.py kosu  |  python3 kosu_kesif_t3.py analiz
"""
import sys

import kosu
import orkestrator as ork

KADEME = 9   # ana koşu kademeleri 1-3; keşif 9, karışmaz
YENI = [
    ork._h("RTS-notr", "S", 0.0, False, KADEME, levha="notr", ucuncu="teklifci"),
    ork._h("RTS-yasak", "S", 0.0, False, KADEME, levha="yasak", ucuncu="teklifci"),
    ork._h("RTS-levha", "S", 0.0, False, KADEME, levha="levha", ucuncu="teklifci"),
]
for h in YENI:
    if h["ad"] not in ork.HUCRE:
        ork.HUCRELER.append(h); ork.HUCRE[h["ad"]] = h

KOK = "kosu_mu25_kesif_t3"

if __name__ == "__main__":
    kip = sys.argv[1] if len(sys.argv) > 1 else "kosu"
    if kip == "kosu":
        kosu.kosular("kosu", "25", 10, 20, {KADEME}, [h["ad"] for h in YENI], KOK, paralel=5)
    elif kip == "analiz":
        kosu.analiz_kos("25", KOK)
    else:
        sys.exit("kip: kosu | analiz")
