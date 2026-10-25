"""Labirent Track 3 · teslim kapısı ($0, standart kütüphane). PLAN.md satır 63 + Track 1 hakem dersleri.
Kırmızı varsa TESLİM YOK. Kullanım: python teslim_kapisi.py RAPOR.md [--girdi kosu_mu25/rapor_girdi_hakem1 ...] [--depo .]
Kontroller:
 0 raporda geçen her sayı rapor_girdi/ içindeki bir dosyada geçiyor mu (elle yazılmış sayı = KIRMIZI)
 1 raporda anılan her dosya yolu depoda var mı (Track 1: "3 dosya eksik")
 2 özet (Abstract / Özet bölümü) 150-250 kelime (Apart Guidelines; KARAR 54)
 3 yasak kelimeler yok: significant, verified, reproduced, proven, anlamlı, doğruladık, yeniden üretildi, kanıtladık
 4 uydurma terimler (labirent, levha, defter, başajan, signpost, floor, witness, kapı) yalnız eşleme tablosu bölümünde
 5 README_RUN.md var, $0 tekrar komutu içinde
 6 testler geçiyor (python -m pytest -q) ve tekrar kipi gerçekten koşuyor (--girdi verilmişse)
Kurallar: sayı eşlemesi ondalık ayırmadan bağımsız (0,85 = 0.85); yıl (19xx/20xx), sayfa/bölüm numarası (1-3 haneli, "Bölüm 3", "Table 2"), başlık numaraları (3.1),
tarihlerdeki gün ("23 October", "20 Ekim") ve 0/1 sayılmaz. Tasarım sabitleri (tohum, tavan, maliyet) README_RUN.md ve A_SPEC.md'den gelebilir (KARAR 46).
"""
import argparse
import os
import re
import subprocess
import sys

OZET_EN_AZ, OZET_EN_COK = 150, 250   # Apart Guidelines, 23 Eki doğrulandı (KARAR 54)
YASAK = ["significant", "verified", "reproduced", "proven", "anlamlı", "doğruladık", "yeniden üretildi", "kanıtladık"]
UYDURMA = ["labirent", "levha", "defter", "başajan", "signpost", "floor", "witness", "kapı"]
ESLEME_BASLIK = re.compile(r"^#+\s*(terim|term|glossary|eşleme|mapping)", re.I | re.M)
SAYI = re.compile(r"(?<![\w.])(\d+(?:[.,]\d+)?)(?![\w])")
YOL = re.compile(r"`([\w./\-]+\.(?:py|json|md|svg|jsonl|txt|csv))`")


def _norm(s):
    return s.replace(",", ".")


AYLAR = (r"(january|february|march|april|may|june|july|august|september|october|november|december|"
         r"ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)")
TARIH_ONCE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+" + AYLAR, re.I)      # "23 October", "20 Ekim"
TARIH_SONRA = re.compile(AYLAR + r"\s+(\d{1,2})\b", re.I)                     # "October 23"
BASLIK_NO = re.compile(r"^(#+\s+)(\d+(?:\.\d+)*)\s+", re.M)                     # "### 3.1 Market"


def _tarih_ve_baslik_disi(metin):
    """KARAR 46 (21 Eki): tarihlerdeki gün sayıları ve başlık numaraları sayı sayılmaz; metinden silinir."""
    metin = BASLIK_NO.sub(lambda m: m.group(1), metin)
    metin = TARIH_ONCE.sub(lambda m: " " + m.group(2), metin)
    metin = TARIH_SONRA.sub(lambda m: m.group(1) + " ", metin)
    return metin


def sayilar(metin):
    out = set()
    metin = _tarih_ve_baslik_disi(metin)
    for m in SAYI.finditer(metin):
        s = _norm(m.group(1))
        if re.search(r"arxiv:\s*$", metin[max(0, m.start() - 8):m.start()], re.I):   # KARAR 64: arXiv kimliği sayı değil
            continue
        if re.fullmatch(r"(19|20)\d\d", s) or s in ("0", "1") or (s.isdigit() and len(s) <= 3 and "." not in s and _baslik_no(metin, m.start())):
            continue
        out.add(s)
    return out


def _baslik_no(metin, i):
    onceki = metin[max(0, i - 12):i].lower()
    return any(w in onceki for w in ("bölüm", "section", "table", "tablo", "figure", "şekil", "fig.", "madde", "satır", "row", "#", "no "))


def girdi_sayilari(klasorler):
    """KARAR 64 (25 Eki): --girdi tek dosya da olabilir (butce_kosu.json, analiz .log); .log da havuza girer."""
    havuz = set()
    for kl in klasorler:
        yollar = [kl] if os.path.isfile(kl) else [os.path.join(k, d) for k, _, ds in os.walk(kl) for d in ds]
        for y in yollar:
            if y.endswith((".json", ".md", ".txt", ".csv", ".log")):
                with open(y, encoding="utf-8", errors="replace") as f:
                    for m in re.finditer(r"\d+(?:\.\d+)?", f.read()):
                        havuz.add(m.group(0))
    return havuz


def sayi_var(s, havuz):
    if s in havuz:
        return True
    try:
        v = float(s)
    except ValueError:
        return False
    # 0.90 raporu, 0.9 dosyada; 27/30 → 0.9 ; yüzdeler: 90 ↔ 0.9
    for h in havuz:
        try:
            hv = float(h)
        except ValueError:
            continue
        # KARAR 64: 2 ya da 3 ondalığa yuvarlama her büyüklükte kabul (1,1672 → 1,17; 142,319…); yüzde kuralı yalnız ≤1
        if abs(hv - v) < 1e-9 or abs(round(hv, 2) - v) < 1e-9 or abs(round(hv, 3) - v) < 1e-9 or (abs(hv) <= 1 and abs(hv * 100 - v) < 1e-9):
            return True
    return False


def ozet_kelime(metin):
    m = re.search(r"^#+\s*(abstract|özet)\s*$\n(.*?)(?=^#+\s|\Z)", metin, re.I | re.M | re.S)
    if not m:
        return None
    return len(m.group(2).split())


def esleme_bolumu(metin):
    m = ESLEME_BASLIK.search(metin)
    if not m:
        return "", metin
    son = re.search(r"^#+\s", metin[m.end():], re.M)
    bitis = m.end() + (son.start() if son else len(metin) - m.end())
    return metin[m.start():bitis], metin[:m.start()] + metin[bitis:]


def kontrol(rapor_yol, girdi, depo, testleri_kos=True):
    metin = open(rapor_yol, encoding="utf-8").read()
    kirmizi, yesil = [], []
    # 0 sayılar · KARAR 46: tasarım sabitleri (tohum aralığı, tavan, maliyet) README_RUN.md ve A_SPEC.md'den de gelebilir;
    #   ölçüm sayıları yine yalnız rapor_girdi'den (bu iki belge ölçüm sayısı içermez)
    if girdi:
        havuz = girdi_sayilari(girdi)
        for belge in ("README_RUN.md", "A_SPEC.md"):
            y = os.path.join(depo, belge)
            if os.path.exists(y):
                with open(y, encoding="utf-8", errors="replace") as f:
                    havuz |= set(re.findall(r"\d+(?:\.\d+)?", f.read()))
        eksik = sorted(s for s in sayilar(metin) if not sayi_var(s, havuz))
        (kirmizi if eksik else yesil).append("0 sayılar: %s" % ("rapor_girdi'de OLMAYAN sayılar: %s" % ", ".join(eksik) if eksik else "hepsi rapor_girdi'de"))
    else:
        kirmizi.append("0 sayılar: --girdi verilmedi, sayı kaynağı denetlenemedi")
    # 1 dosya yolları
    yok = sorted({y for y in YOL.findall(metin) if not os.path.exists(os.path.join(depo, y))})
    (kirmizi if yok else yesil).append("1 dosya yolları: %s" % ("depoda YOK: %s" % ", ".join(yok) if yok else "hepsi var"))
    # 2 özet · KARAR 54 (23 Eki): Apart Guidelines "Project title and abstract, 150 to 250 words" (sayfadan doğrulandı);
    #   eski kural ≤150 yanlış okumaydı. Alt sınır da kırmızı: 150'nin altı kurala uymaz.
    n = ozet_kelime(metin)
    if n is None:
        kirmizi.append("2 özet: Abstract/Özet başlığı bulunamadı")
    else:
        (kirmizi if (n < OZET_EN_AZ or n > OZET_EN_COK) else yesil).append("2 özet: %d kelime (%d-%d)" % (n, OZET_EN_AZ, OZET_EN_COK))
    # 3 yasak kelimeler
    bul = [w for w in YASAK if re.search(r"\b" + re.escape(w), metin, re.I)]
    (kirmizi if bul else yesil).append("3 yasak kelimeler: %s" % (", ".join(bul) if bul else "yok"))
    # 4 uydurma terimler yalnız eşleme bölümünde
    _, kalan = esleme_bolumu(metin)
    kalan_kod_disi = re.sub(r"`[^`]*`", "", kalan)
    kalan_kod_disi = re.sub(r"https?://\S+", " ", kalan_kod_disi)   # KARAR 66: depo adresi (URL) terim sayılmaz
    uy = [w for w in UYDURMA if re.search(r"\b" + re.escape(w), kalan_kod_disi, re.I)]
    (kirmizi if uy else yesil).append("4 uydurma terimler metinde: %s" % (", ".join(uy) if uy else "yok (yalnız eşleme tablosunda)"))
    # 5 README_RUN
    rd = os.path.join(depo, "README_RUN.md")
    if os.path.exists(rd) and "tekrar" in open(rd, encoding="utf-8").read():
        yesil.append("5 README_RUN.md var, $0 tekrar komutu içinde")
    else:
        kirmizi.append("5 README_RUN.md yok ya da $0 tekrar komutu yok")
    # 6 testler + tekrar
    if testleri_kos:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x"], cwd=depo, capture_output=True, text=True)
        (yesil if r.returncode == 0 else kirmizi).append("6 testler: %s" % (r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.returncode))
    return kirmizi, yesil


if __name__ == "__main__":
    try:   # KARAR 46: Windows konsolu (cp1254) "≤" basamıyordu
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("rapor"); ap.add_argument("--girdi", nargs="*", default=[]); ap.add_argument("--depo", default=".")
    ap.add_argument("--testsiz", action="store_true")
    a = ap.parse_args()
    kirmizi, yesil = kontrol(a.rapor, a.girdi, a.depo, testleri_kos=not a.testsiz)
    for s in yesil:
        print("YEŞİL ", s)
    for s in kirmizi:
        print("KIRMIZI", s)
    print("TESLİM:", "YOK (kırmızı var)" if kirmizi else "KAPI AÇIK")
    sys.exit(1 if kirmizi else 0)
