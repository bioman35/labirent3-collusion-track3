"""Labirent Track 3 · A3 · bütçe (A_SPEC G13).

Çağrı başına token sayacı, hücre ve toplam USD tavanı. Tavan aşılınca BUTCE_ASIMI yükselir ve koşu durur.
Fiyatlar (USD / 1M token) ayarda verilir; kaynaksız sayı yok: pilotta GERÇEK kullanım (API usage) ölçülür,
ölçülmediyse rapora "ölçülmedi" yazılır. Token sayısı API'den gelmezse kaba tahmin (karakter/4) ve "tahmin"
diye işaretlenir.
"""


import threading


class ButceAsimi(RuntimeError):
    pass


class Butce:
    def __init__(self, fiyatlar: dict, hucre_tavani_usd: float, toplam_tavan_usd: float):
        """fiyatlar: {model: {"giris": usd/1M, "cikis": usd/1M}}"""
        self.fiyatlar = fiyatlar
        self.hucre_tavani, self.toplam_tavan = hucre_tavani_usd, toplam_tavan_usd
        self.kayitlar = []          # {hucre, model, giris, cikis, usd, tahmin}
        self.hucre_usd = {}
        self.toplam_usd = 0.0
        self._kilit = threading.Lock()   # 21 Eki: paralel koşuda (iş parçacıkları) tek sayaç, tek tavan

    def maliyet(self, model, giris, cikis):
        f = self.fiyatlar.get(model)
        if f is None:
            raise ValueError("fiyatı bilinmeyen model: %s (kaynaksız sayı yok)" % model)
        return (giris * f["giris"] + cikis * f["cikis"]) / 1_000_000

    def kaydet(self, hucre, model, giris=None, cikis=None, metin_giris="", metin_cikis=""):
        tahmin = giris is None or cikis is None
        if tahmin:
            giris = giris if giris is not None else max(1, len(metin_giris) // 4)
            cikis = cikis if cikis is not None else max(1, len(metin_cikis) // 4)
        usd = self.maliyet(model, giris, cikis)
        with self._kilit:
            self.kayitlar.append({"hucre": hucre, "model": model, "giris": giris, "cikis": cikis, "usd": usd, "tahmin": tahmin})
            self.hucre_usd[hucre] = self.hucre_usd.get(hucre, 0.0) + usd
            self.toplam_usd += usd
            h_usd, t_usd = self.hucre_usd[hucre], self.toplam_usd
        if h_usd > self.hucre_tavani:
            raise ButceAsimi("hücre tavanı aşıldı: %s %.4f > %.4f USD" % (hucre, h_usd, self.hucre_tavani))
        if t_usd > self.toplam_tavan:
            raise ButceAsimi("toplam tavan aşıldı: %.4f > %.4f USD" % (t_usd, self.toplam_tavan))
        return usd

    def ozet(self):
        tahminli = sum(1 for k in self.kayitlar if k["tahmin"])
        return {"cagri": len(self.kayitlar), "toplam_usd": self.toplam_usd, "hucre_usd": dict(self.hucre_usd),
                "tahminli_cagri": tahminli, "olcum_durumu": "ölçülmedi" if not self.kayitlar else ("tahmin" if tahminli else "ölçüldü")}
