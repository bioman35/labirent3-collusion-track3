"""Labirent Track 3 · A2 · izleyici (A_SPEC G2, G3).

İzleyici bir MÜDAHALEDİR, dedektör değil: pasiftir, ceza vermez, yalnız mesajların payı kadarını görür ve
gördüğünü kaydeder. Dedektör (dedektor.py) kayıtlı koşular üzerinde çevrimdışı sınanır.
Pay: 0 (hiç), 0.5 (yarım), 1 (tam). Hangi mesajın görüldüğü tohumlu rastgeleyle seçilir, deftere yazılır.
Bildirim metni ajanlar.bildirim_metni ile ÜRETİLİR ve her zaman doğrudur (G2).
"""
import random

PAYLAR = (0.0, 0.5, 1.0)


class Izleyici:
    def __init__(self, pay: float, tohum: int):
        if pay not in PAYLAR:
            raise ValueError("pay 0, 0.5 ya da 1 olmalı")
        self.pay = pay
        self.rastgele = random.Random(tohum)
        self.gorulen = []     # [{"tur", "kim", "mesaj"}]
        self.toplam = 0

    def gozle(self, tur: int, mesajlar: dict) -> list:
        """mesajlar: {kim: mesaj|None}. Dönen: bu turda görülen kayıtlar (deftere yazılır)."""
        gorulen = []
        for kim in sorted(mesajlar):
            m = mesajlar[kim]
            if not m:
                continue
            self.toplam += 1
            goruldu = (self.pay >= 1.0) or (self.pay > 0 and self.rastgele.random() < self.pay)
            if goruldu:
                k = {"tur": tur, "kim": kim, "mesaj": m}
                self.gorulen.append(k)
                gorulen.append(k)
        return gorulen

    def ozet(self) -> dict:
        return {"pay": self.pay, "toplam_mesaj": self.toplam, "gorulen": len(self.gorulen),
                "gerceklesen_pay": (len(self.gorulen) / self.toplam) if self.toplam else None}
