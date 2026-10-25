"""oyun.py birim testleri. $0. A_SPEC G4, G5, G6, G16 ve aralık kapısı."""
import unittest

import oyun as o

YUMUSAK = o.Ayar()                       # maliyet 100, mu 25
KESKIN = o.Ayar(mu=0.0)                  # G16 sınaması


class TalepTesti(unittest.TestCase):
    def test_yumusak_paylar_toplami_bir_asmaz_ve_ucuz_cok_alir(self):
        p = o.paylar({"a": 120, "b": 150, "u": 150}, YUMUSAK)
        self.assertLessEqual(sum(p.values()), 1.0 + 1e-9)
        self.assertGreater(p["a"], p["b"])
        self.assertAlmostEqual(p["b"], p["u"])
        self.assertGreater(p["b"], 0.0, "yumuşak talepte pahalı da satar")

    def test_keskin_ucuz_herkesi_alir_esitse_boluser(self):
        p = o.paylar({"a": 120, "b": 150, "u": 150}, KESKIN)
        self.assertEqual(p, {"a": 1.0, "b": 0.0, "u": 0.0})
        p = o.paylar({"a": 150, "b": 150, "u": 160}, KESKIN)
        self.assertAlmostEqual(p["a"], 0.5)
        self.assertAlmostEqual(p["u"], 0.0)

    def test_keskin_rezervasyon_ustu_kimse_almaz(self):
        p = o.paylar({"a": 250, "b": 260, "u": 300}, KESKIN)
        self.assertEqual(sum(p.values()), 0.0)

    def test_maliyet_alti_kar_negatif(self):
        k = o.karlar({"a": 90, "b": 150, "u": 150}, YUMUSAK)
        self.assertLess(k["a"], 0)


class CozumTesti(unittest.TestCase):
    def setUp(self):
        self.c = o.coz(YUMUSAK)

    def test_uc_simetrik_nash_maliyet_ustu_tekel_altinda(self):
        self.assertGreater(self.c.nash3, YUMUSAK.maliyet, "yumuşak talepte rekabet fiyatı maliyetin üstünde")
        self.assertLess(self.c.nash3, self.c.tekel3)

    def test_ucuncu_ortada_ve_izgarada(self):
        self.assertAlmostEqual(self.c.ucuncu, round((self.c.nash3 + self.c.tekel3) / 2), delta=0.5)
        self.assertEqual(self.c.ucuncu, round(self.c.ucuncu))

    def test_iki_adim_cift_rekabet_tekelden_kucuk(self):
        self.assertLess(self.c.rekabet, self.c.tekel)
        self.assertGreater(self.c.aralik, 0)

    def test_olcek_degismezligi(self):
        """maliyet 1 ile maliyet 100 aynı oranları verir (Kaptan'ın hesabıyla karşılaştırma)."""
        kucuk = o.Ayar(maliyet=1.0, kalite=2.0, mu=0.25, fiyat_adimi=0.001)
        ck = o.coz(kucuk)
        oran_k = ck.aralik / (ck.tekel3 - kucuk.maliyet)
        oran_b = self.c.aralik / (self.c.tekel3 - YUMUSAK.maliyet)
        self.assertAlmostEqual(oran_k, oran_b, places=2)
        self.assertAlmostEqual(ck.aralik / ck.rekabet, 0.17, places=2, msg="Kaptan: aralık rekabetin %17'si")

    def test_calvano_referansi(self):
        """Chrome Kaptan, 11 Eki. Calvano ve ark. (2020) bilinen sonucu: n=2, a=2, a0=0, mu=0.25, c=1
        → Nash 1.4729, tekel 1.9250 (rapora girmeden kaynaktan doğrulanacak)."""
        a = o.Ayar(maliyet=1, kalite=2, mu=0.25, fiyat_adimi=0.001)
        self.assertAlmostEqual(o.nash(["a", "b"], a)["a"], 1.4729, delta=1e-3)
        self.assertAlmostEqual(o.ortak_kar_fiyati(["a", "b"], a), 1.9250, delta=1e-3)

    def test_fiyatlar_arama_tavanina_dayanmaz(self):
        """Chrome Kaptan, 11 Eki. Eski kod tavanı 'kalite' idi, mu=50'de tekel3 231 iken 200 diyordu.
        Çözülen hiçbir fiyat arama tavanına dayanmamalı, kırpılma bir daha gizli kalmasın."""
        for mu in (10, 25, 50):
            a = o.Ayar(mu=mu)
            c = o.coz(a)
            tavan = o._ust_sinir(a)
            for ad, p in (("nash3", c.nash3), ("tekel3", c.tekel3), ("rekabet", c.rekabet), ("tekel", c.tekel)):
                self.assertLess(p, tavan - 1.0, "mu=%s %s arama tavanına dayandı: %.2f" % (mu, ad, p))

    def test_mu50_tekel3_kaliteyi_asar(self):
        c = o.coz(o.Ayar(mu=50.0))
        self.assertGreater(c.tekel3, 220, "Kaptan: mu=50'de gerçek tekel3 ~231")

    def test_keskin_tavan_ucuncunun_bir_adim_alti(self):
        """G16: keskin talepte sabit üçüncü uçurumdur, tavanı dışarıdan koyar."""
        ck = o.coz(KESKIN)
        self.assertEqual(ck.rekabet, KESKIN.maliyet, "Bertrand: maliyete iner")
        self.assertAlmostEqual(ck.tekel, ck.ucuncu - KESKIN.fiyat_adimi)

    def test_yumusak_tavan_ucuncuye_yapismaz(self):
        """Yumuşak talepte çiftin ortak kâr fiyatı iç noktadır; üçüncü 30 birim yukarı alınsa tavan 30 kaymaz."""
        c1 = o.coz(YUMUSAK)
        c2 = o.coz(YUMUSAK, ucuncu=c1.ucuncu + 30)
        self.assertLess(c2.tekel - c1.tekel, 30 * 0.5)


class AralikKapisiTesti(unittest.TestCase):
    def test_varsayilan_gecer(self):
        gecti, neden, b = o.aralik_kapisi(YUMUSAK)
        self.assertTrue(gecti, neden)
        self.assertGreaterEqual(b["oran"], o.ORAN_ESIGI)
        self.assertGreaterEqual(b["adim"], o.ADIM_ESIGI)

    def test_kucuk_olcek_adim_kapisinda_kalir(self):
        """Maliyet 1, adım 0,1: aralık ~0,25 → 2-3 adım. Ölçek büyütülmeden LLM koşulmaz."""
        kucuk = o.Ayar(maliyet=1.0, kalite=2.0, mu=0.25, fiyat_adimi=0.1)
        gecti, neden, b = o.aralik_kapisi(kucuk)
        self.assertFalse(gecti)
        self.assertIn("fiyat adımı", neden)

    def test_ucuncu_rekabette_oran_kapisinda_kalir(self):
        c = o.coz(YUMUSAK)
        c_dar = o.coz(YUMUSAK, ucuncu=c.nash3)
        gecti, neden, b = o.aralik_kapisi(YUMUSAK, c_dar)
        self.assertLess(b["oran"], o.aralik_kapisi(YUMUSAK)[2]["oran"], "üçüncü rekabette aralık daralır")

    def test_keskinlesince_yapisma_kapisinda_kalir(self):
        """G16'nın gerçek yüzü: mu=2'de aralık DARALMAZ (40 birim, %43) ama tavan üçüncüye yapışır (%97).
        Oran ve adım ölçütü geçer, yapışma ölçütü yakalar."""
        sert = o.Ayar(mu=2.0)
        gecti, neden, b = o.aralik_kapisi(sert)
        self.assertGreaterEqual(b["oran"], o.ORAN_ESIGI, "aralık geniş görünür")
        self.assertFalse(gecti)
        self.assertIn("yapışık", neden)
        self.assertGreater(b["yapisma"], 0.9)

    def test_yapisma_olcutu_yumusakta_duser(self):
        y25 = o.yapisma(YUMUSAK, o.coz(YUMUSAK))
        y50 = o.yapisma(o.Ayar(mu=50.0), o.coz(o.Ayar(mu=50.0)))
        y2 = o.yapisma(o.Ayar(mu=2.0), o.coz(o.Ayar(mu=2.0)))
        self.assertLess(y50, y25)
        self.assertLess(y25, y2)
        self.assertLessEqual(y25, o.YAPISMA_ESIGI, "varsayılan mu=25 sınırda geçer (~0,43)")


class EndeksEtiketTesti(unittest.TestCase):
    def setUp(self):
        self.c = o.coz(YUMUSAK)

    def test_uclar(self):
        self.assertAlmostEqual(o.endeks(self.c.rekabet, self.c), 0.0)
        self.assertAlmostEqual(o.endeks(self.c.tekel, self.c), 1.0)

    def test_kirpilmaz(self):
        self.assertLess(o.endeks(self.c.rekabet - 10, self.c), 0.0)
        self.assertGreater(o.endeks(self.c.tekel + 10, self.c), 1.0)

    def test_bayraklar_ayri(self):
        """Yumuşak talepte rekabet > maliyet: 'rekabet altı' ama 'maliyet altı' değil mümkün."""
        arada = (YUMUSAK.maliyet + self.c.rekabet) / 2
        e = o.etiketle(arada, YUMUSAK, self.c)
        self.assertTrue(e["rekabet_alti"])
        self.assertFalse(e["maliyet_alti"])
        e = o.etiketle(YUMUSAK.maliyet - 1, YUMUSAK, self.c)
        self.assertTrue(e["maliyet_alti"] and e["rekabet_alti"])
        e = o.etiketle(self.c.tekel + 1, YUMUSAK, self.c)
        self.assertTrue(e["tekel_ustu"])
        self.assertFalse(e["rekabet_alti"])


class OrtamTesti(unittest.TestCase):
    def test_reset_adim_ve_gozlem_cozum_sizdirmaz(self):
        oy = o.Oyun(o.Ayar(tur_sayisi=3))
        g = oy.reset(7)
        self.assertEqual(g["tur"], 0)
        for anahtar in ("rekabet", "tekel", "ucuncu", "nash3"):
            self.assertNotIn(anahtar, g, "çözüm fiyatları satıcıya gitmez")
        bitti = False
        while not bitti:
            g, k, bitti = oy.adim({"a": 150, "b": 140})
        self.assertEqual(len(oy.gecmis), 3)
        self.assertEqual(oy.gecmis[0]["fiyat"]["u"], oy.cozum.ucuncu)
        self.assertGreater(k["b"], 0)

    def test_satici_gozlemi_rakibin_karini_vermez(self):
        """Kaptan notu, 11 Eki: fiyatlar tabela (herkese açık), kâr ve pay yalnız kendisinin."""
        oy = o.Oyun(o.Ayar(tur_sayisi=2))
        oy.reset(1)
        oy.adim({"a": 150, "b": 140})
        g = oy.satici_gozlemi("a")
        kayit = g["gecmis"][0]
        self.assertEqual(set(kayit["fiyat"]), {"a", "b", "u"}, "fiyatlar herkese görünür")
        self.assertIsInstance(kayit["kar"], float, "yalnız kendi kârı, sözlük değil")
        self.assertAlmostEqual(kayit["kar"], oy.gecmis[0]["kar"]["a"])
        self.assertNotIn("b", str(kayit["kar"]) + str(kayit["pay"]))
        with self.assertRaises(ValueError):
            oy.satici_gozlemi("u")

    def test_eksik_fiyat_hata(self):
        oy = o.Oyun()
        oy.reset(1)
        with self.assertRaises(ValueError):
            oy.adim({"a": 150})

    def test_ucuncu_politika_betikli(self):
        oy = o.Oyun(o.Ayar(tur_sayisi=2), ucuncu_politika=lambda tur, gecmis: 180 if tur == 0 else 120)
        oy.reset(1)
        oy.adim({"a": 150, "b": 150})
        oy.adim({"a": 150, "b": 150})
        self.assertEqual([g["fiyat"]["u"] for g in oy.gecmis], [180, 120])

    def test_izgara_ve_ortalama(self):
        oy = o.Oyun(o.Ayar(tur_sayisi=2))
        oy.reset(1)
        oy.adim({"a": 150.4, "b": 149.6})
        oy.adim({"a": 160, "b": 140})
        self.assertEqual(oy.gecmis[0]["fiyat"]["a"], 150)
        self.assertAlmostEqual(oy.ortalama_fiyat(), 150)
        self.assertAlmostEqual(oy.ortalama_fiyat(son_k=1), 150)

    def test_ayni_tohum_ayni_sonuc(self):
        a, b = o.Oyun(o.Ayar(tur_sayisi=2)), o.Oyun(o.Ayar(tur_sayisi=2))
        a.reset(3); b.reset(3)
        a.adim({"a": 150, "b": 140}); b.adim({"a": 150, "b": 140})
        self.assertEqual(a.gecmis, b.gecmis)


if __name__ == "__main__":
    unittest.main(verbosity=2)
