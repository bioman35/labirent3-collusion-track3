"""Labirent Track 3 · A3 · kilit (A_SPEC G9, G10, tahminler).

1. Tohum bölmesi: kalibrasyon tohumları ve test tohumları ayrı kümeler, kesişmez.
2. Eşik kilidi: eşik dosyasının SHA-256 özeti deftere (cekirdek.Defter) yazılır. Özet defterde YOKSA
   test tohumlarıyla koşmak REDDEDİLİR. Eşik dosyası sonradan değişirse özet tutmaz, yine reddedilir.
3. Tahmin kilidi: T1-T3 metninin özeti koşudan önce deftere yazılır.
4. Kör koşu kimliği: rastgele kimlik ↔ koşul eşlemesi orkestratörde, mühürlü ayrı dosyada (Kasa.muhur).
   Dedektöre yalnız kimlik gider.
"""
import hashlib
import json
import secrets

import cekirdek as c

KALIBRASYON_TOHUMLARI = tuple(range(1000, 1012))   # 12 tohum
SIRA_TOHUMU = 7                                     # 21 Eki: koşu sırasını karıştıran sabit tohum (KARAR 32)
TEST_TOHUMLARI = tuple(range(2000, 2060))          # 60 tohum (hücre × çift için yeter)
assert not set(KALIBRASYON_TOHUMLARI) & set(TEST_TOHUMLARI)


def tohum_kumesi(tohum):
    if tohum in KALIBRASYON_TOHUMLARI:
        return "kalibrasyon"
    if tohum in TEST_TOHUMLARI:
        return "test"
    raise ValueError("tohum hiçbir kümede değil: %s" % tohum)


def ozet(nesne) -> str:
    return hashlib.sha256(c.kanonik(nesne)).hexdigest()


YER_TUTUCU = ("bekleniyor", "tbd", "todo", "yazılacak", "?")


def _yer_tutucu_yok(ad, nesne):
    """YAMA: 'bekleniyor' gibi yer tutucu tahmin kilitlenemez (yoksa test koşusu boş tahminle açılır)."""
    if isinstance(nesne, dict):
        for k, v in nesne.items():
            if v is None or (isinstance(v, str) and (not v.strip() or v.strip().lower() in YER_TUTUCU)):
                raise ValueError("%s.%s yer tutucu, kilitlenemez" % (ad, k))


def kilitle(defter: c.Defter, ad: str, nesne) -> str:
    """Eşik/tahmin nesnesini deftere özetiyle yazar. Dönen özet."""
    _yer_tutucu_yok(ad, nesne)
    h = ozet(nesne)
    defter.ekle("kilit", {"ad": ad, "ozet": h, "icerik": nesne})
    return h


def kilitli_mi(defter: c.Defter, ad: str, nesne) -> bool:
    h = ozet(nesne)
    return any(s["tur"] == "kilit" and s["govde"].get("ad") == ad and s["govde"].get("ozet") == h
               for s in defter._satirlar())


def kosu_izni(defter: c.Defter, tohum: int, esikler, tahminler) -> tuple[bool, str]:
    """Test tohumuyla koşmadan önce çağrılır. Kalibrasyon tohumu her zaman serbest."""
    kume = tohum_kumesi(tohum)
    if kume == "kalibrasyon":
        return True, "kalibrasyon tohumu"
    if not kilitli_mi(defter, "esikler", esikler):
        return False, "REDDEDİLDİ: eşik özeti defterde yok ya da eşik değişmiş (G9)"
    if not kilitli_mi(defter, "tahminler", tahminler):
        return False, "REDDEDİLDİ: tahmin özeti defterde yok ya da tahmin değişmiş"
    return True, "test tohumu, kilitler tutuyor"


class KorKimlik:
    """Koşu kimliği rastgele; kimlik→koşul eşlemesi mühürlü dosyada, dedektöre gitmez (G10)."""
    def __init__(self, kasa: c.Kasa, yol: str):
        self.kasa, self.yol = kasa, yol
        self.esleme = {}

    def yeni(self, kosul: dict) -> str:
        kid = "k" + secrets.token_hex(6)
        self.esleme[kid] = kosul
        return kid

    def kaydet(self):
        # Kasa.muhur sözlük alır (kanonik JSON'unu kendisi imzalar), hex dize döner.
        with open(self.yol, "w", encoding="utf-8") as f:
            json.dump({"esleme": self.esleme, "muhur": self.kasa.muhur(self.esleme)}, f, ensure_ascii=False)

    @staticmethod
    def yukle(kasa: c.Kasa, yol: str) -> dict:
        with open(yol, encoding="utf-8") as f:
            d = json.load(f)
        if not kasa.muhur_dogru(d["esleme"], d["muhur"]):
            raise ValueError("kör kimlik eşlemesi mührü tutmuyor")
        return d["esleme"]
