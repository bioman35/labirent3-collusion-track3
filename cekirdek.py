"""Labirent Track 3 · çekirdek (savunma yapı taşları) · v2.

Yalnız standart kütüphane. floor.py'ye DOKUNMAZ (donuk, 3 dış koşu ona bağlı).
Savunma parçaları: defter, mühür, tek kullanımlık numara, sabit zarf, eşikli paylaşım,
oturum anahtarı. Ajanlar (LLM) bunlara hiç erişmez; erişen kod orkestratördür.

SINIRLAR (rapora yazılacak):
- HMAC tabanlı akış "şifresi" ve Shamir burada deney içi bütünlük ve gizlilik içindir,
  ÜRETİM KRİPTOGRAFİSİ DEĞİLDİR.
- Tek yazıcı kuralı: aynı deftere aynı anda tek süreç yazar (dosya kilidi yok).

v2 düzeltmeleri (Kaptan'ın incelemesi): çift harcama, Shamir sır kesme, yeniden başlatma
sonrası bayat anahtar, nonce tekrarı, zarfın tekrar açılması, yarım satır çökmesi.
"""
import hashlib
import hmac
import json
import re
import secrets
import threading
import time

SIFIR = "0" * 64
ZARF_BOYUT = 2048
_KIMLIK_RE = re.compile(r"^[a-z0-9_-]{1,64}$")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def kanonik(nesne) -> bytes:
    return json.dumps(nesne, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


# ── 1 · yalnız-ekle, hash zincirli defter ────────────────────────────────────
class Defter:
    """Ajan yazamaz. Yalnız orkestratör kodu ekler. Kafa dışarıya ayrıca basılır."""

    def __init__(self, yol: str):
        self.yol = yol
        open(yol, "a", encoding="utf-8").close()
        self._kilit = threading.RLock()   # 21 Eki (KARAR 28): paralel koşuda zincir sıralı kalır; kafa+ekle tek adım

    def _satirlar(self):
        satirlar = []
        with open(self.yol, encoding="utf-8") as f:
            for i, l in enumerate(f):
                if not l.strip():
                    continue
                try:
                    satirlar.append(json.loads(l))
                except json.JSONDecodeError:
                    raise ValueError("bozuk defter satırı %d" % i)
        return satirlar

    def kafa(self):
        with self._kilit:
            s = self._satirlar()
            return (len(s), s[-1]["ozet"] if s else SIFIR)

    def ekle(self, tur: str, govde: dict) -> str:
        with self._kilit:
            n, onceki = self.kafa()
            k = {"sira": n, "zaman": round(time.time(), 3), "tur": tur, "govde": govde, "onceki": onceki}
            k["ozet"] = sha(kanonik(k))
            with open(self.yol, "a", encoding="utf-8") as f:
                f.write(json.dumps(k, ensure_ascii=False) + "\n")
            return k["ozet"]

    @staticmethod
    def dogrula(yol: str, yayinlanan_kafa=None):
        """(saglam, neden). Bozuk ya da yarım satır ÇÖKERTMEZ, (False, neden) döner.
        yayinlanan_kafa = (uzunluk, ozet): dışarıda önceden basılmış kafa."""
        onceki, ozetler = SIFIR, []
        with open(yol, encoding="utf-8") as f:
            for l in f:
                if not l.strip():
                    continue
                n = len(ozetler)
                try:
                    k = json.loads(l)
                    oz = k.pop("ozet")
                    sira, bag = k["sira"], k["onceki"]
                except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
                    return False, "bozuk satır %d" % n
                if bag != onceki or sira != n:
                    return False, "zincir kırık, satır %d" % n
                if sha(kanonik(k)) != oz:
                    return False, "özet tutmuyor, satır %d" % n
                onceki = oz
                ozetler.append(oz)
        if yayinlanan_kafa:
            uzunluk, ozet = yayinlanan_kafa
            if len(ozetler) < uzunluk:
                return False, "kuyruk kesilmiş (yayımlanan %d, diskte %d)" % (uzunluk, len(ozetler))
            if uzunluk and ozetler[uzunluk - 1] != ozet:
                return False, "yayımlanmış kafa tutmuyor (iz yeniden yazılmış)"
        return True, "sağlam"


# ── 2 · kasa: anahtarlar ajanın erişemediği yerde ────────────────────────────
class Kasa:
    def __init__(self, ana: bytes = None):
        self._ana = ana or secrets.token_bytes(32)

    def turet(self, etiket: str) -> bytes:
        return hmac.new(self._ana, b"turet|" + etiket.encode("utf-8"), hashlib.sha256).digest()

    def muhur(self, alanlar: dict) -> str:
        return hmac.new(self.turet("muhur"), kanonik(alanlar), hashlib.sha256).hexdigest()

    def muhur_dogru(self, alanlar: dict, imza: str) -> bool:
        return hmac.compare_digest(self.muhur(alanlar), imza or "")


# ── 3 · tek kullanımlık numara (tekrar kullanım engeli) ──────────────────────
class Harcanan:
    def __init__(self, defter: Defter):
        self.defter = defter
        self._yukle()

    def _yukle(self):
        self._set = {k["govde"]["no"] for k in self.defter._satirlar() if k["tur"] == "harcandi"}

    def harca(self, no: str) -> bool:
        """İlk kullanımda True, sonrakinde False. Her çağrıda defter yeniden okunur:
        aynı deftere bağlı başka örnek harcamışsa o da görülür."""
        self._yukle()
        if no in self._set:
            return False
        self.defter.ekle("harcandi", {"no": no})
        self._set.add(no)
        return True


# ── 4 · sabit boyutlu kapalı zarf (taşıyıcı içeriği göremez) ─────────────────
def _akis(anahtar: bytes, no: str, n: int) -> bytes:
    cikti, i = b"", 0
    while len(cikti) < n:
        cikti += hmac.new(anahtar, b"akis|" + no.encode() + i.to_bytes(4, "big"), hashlib.sha256).digest()
        i += 1
    return cikti[:n]


def zarfla(kasa: Kasa, adres: str, mektup: bytes) -> dict:
    if len(mektup) > ZARF_BOYUT - 4:
        raise ValueError("mektup çok uzun")
    no = secrets.token_hex(8)
    dolgu = len(mektup).to_bytes(4, "big") + mektup + secrets.token_bytes(ZARF_BOYUT - 4 - len(mektup))
    govde = bytes(a ^ b for a, b in zip(dolgu, _akis(kasa.turet("zarf"), no, ZARF_BOYUT))).hex()
    z = {"no": no, "adres": adres, "govde": govde}
    z["muhur"] = kasa.muhur({"no": no, "adres": adres, "govde": govde})
    return z


def zarf_gecerli(kasa: Kasa, z: dict) -> bool:
    try:
        return len(z["govde"]) == ZARF_BOYUT * 2 and kasa.muhur_dogru(
            {"no": z["no"], "adres": z["adres"], "govde": z["govde"]}, z["muhur"])
    except (KeyError, TypeError):
        return False


def _zarf_ac(kasa: Kasa, z: dict) -> bytes:
    dolgu = bytes(a ^ b for a, b in zip(bytes.fromhex(z["govde"]), _akis(kasa.turet("zarf"), z["no"], ZARF_BOYUT)))
    return dolgu[4:4 + int.from_bytes(dolgu[:4], "big")]


def zarf_ac_tek(kasa: Kasa, harcanan: Harcanan, z: dict) -> bytes:
    """Mühür kontrolü + numarayı harcama + açma TEK adımda. İkinci açış reddedilir."""
    if not zarf_gecerli(kasa, z):
        raise ValueError("mühür tutmuyor")
    if not harcanan.harca(z["no"]):
        raise ValueError("zarf zaten açıldı")
    return _zarf_ac(kasa, z)


# ── 5 · eşikli paylaşım (k-of-n, Shamir) ─────────────────────────────────────
_P = 2 ** 521 - 1  # Mersenne asalı: 64 bayta kadar sır, 32 baytlık anahtar sığar


def bayt_sir(b: bytes) -> int:
    if len(b) > 64:
        raise ValueError("sır 64 bayttan uzun")
    return int.from_bytes(b, "big")


def sir_bayt(i: int, uzunluk: int) -> bytes:
    return i.to_bytes(uzunluk, "big")


def esik_bol(sir: int, k: int, n: int):
    if not (isinstance(sir, int) and 0 <= sir < _P):
        raise ValueError("sır alan dışında (sessizce kesilmez)")
    if not (1 <= k <= n <= 255):
        raise ValueError("k ve n tutarsız")
    kat = [sir] + [secrets.randbelow(_P) for _ in range(k - 1)]
    return [(x, sum(c * pow(x, i, _P) for i, c in enumerate(kat)) % _P) for x in range(1, n + 1)]


def esik_birlestir(parcalar) -> int:
    if not parcalar:
        raise ValueError("parça yok")
    xs = [x for x, _ in parcalar]
    if len(set(xs)) != len(xs):
        raise ValueError("aynı parça iki kez verildi")
    toplam = 0
    for i, (xi, yi) in enumerate(parcalar):
        pay = payda = 1
        for j, (xj, _) in enumerate(parcalar):
            if i != j:
                pay = pay * (-xj) % _P
                payda = payda * (xi - xj) % _P
        toplam = (toplam + yi * pay * pow(payda, -1, _P)) % _P
    return toplam


# ── 6 · oturum anahtarı: her geçişte dış üreticiyle yeniden türetilir ───────
class Kimlik:
    """Kopya eski sayaçla ya da harcanmış nonce ile gelir: reddedilir ve KANIT olarak
    kaydedilir (kopya_suphesi). Defter verilirse sayaçlar yeniden başlatmada korunur."""

    def __init__(self, kasa: Kasa, defter: Defter = None):
        self.kasa = kasa
        self.defter = defter
        self.sayac = {}
        self.bekleyen = {}
        self.olaylar = []
        if defter:
            for k in defter._satirlar():
                if k["tur"] == "anahtar_sayac":
                    a = k["govde"]["ajan"]
                    self.sayac[a] = max(self.sayac.get(a, 0), k["govde"]["sayac"])

    @staticmethod
    def _kimlik_gecerli(ajan_id: str):
        if not isinstance(ajan_id, str) or not _KIMLIK_RE.match(ajan_id):
            raise ValueError("ajan kimliği [a-z0-9_-] olmalı")

    def _olay(self, tur: str, govde: dict):
        self.olaylar.append((tur, govde))
        if self.defter:
            self.defter.ekle(tur, govde)

    def yeni_anahtar(self, ajan_id: str):
        self._kimlik_gecerli(ajan_id)
        s = self.sayac.get(ajan_id, 0) + 1
        self.sayac[ajan_id] = s
        self._olay("anahtar_sayac", {"ajan": ajan_id, "sayac": s})
        return s, self.kasa.turet("oturum|%s|%d" % (ajan_id, s))

    def meydan_oku(self, ajan_id: str) -> str:
        """Nonce'u doğrulayıcı üretir ve tek kullanımlık harcar."""
        self._kimlik_gecerli(ajan_id)
        nonce = secrets.token_hex(16)
        self.bekleyen[nonce] = ajan_id
        return nonce

    def dogrula(self, ajan_id: str, sayac: int, nonce: str, cevap: str) -> bool:
        self._kimlik_gecerli(ajan_id)
        sahip = self.bekleyen.pop(nonce, None)  # tek kullanımlık: ilk görüşte harcanır
        if sahip != ajan_id:
            self._olay("kopya_suphesi", {"ajan": ajan_id, "neden": "bilinmeyen_ya_da_harcanmis_nonce"})
            return False
        if sayac != self.sayac.get(ajan_id, 0):
            self._olay("kopya_suphesi", {"ajan": ajan_id, "neden": "bayat_anahtar", "sayac": sayac})
            return False
        anahtar = self.kasa.turet("oturum|%s|%d" % (ajan_id, sayac))
        if not hmac.compare_digest(cevap_ver(anahtar, nonce), cevap or ""):
            self._olay("kopya_suphesi", {"ajan": ajan_id, "neden": "cevap_tutmuyor"})
            return False
        return True


def cevap_ver(anahtar: bytes, nonce: str) -> str:
    """Sırrı göndermeden bilgiyi kanıtlar: her seferinde yeni nonce, yeni cevap."""
    return hmac.new(anahtar, nonce.encode("utf-8"), hashlib.sha256).hexdigest()
