"""Çekirdek savunma parçalarının birim testleri. Ücretsiz ($0), ajan çağırmaz.
v2: Kaptan'ın bulduğu 6 kusurun her biri için ayrı test eklendi."""
import json
import os
import tempfile
import unittest

import cekirdek as c


def gecici():
    d = tempfile.mkdtemp()
    return os.path.join(d, "defter.jsonl")


def oku(yol):
    with open(yol, encoding="utf-8") as f:
        return f.read().splitlines()


def yaz(yol, satirlar):
    with open(yol, "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")


class DefterTesti(unittest.TestCase):
    def test_saglam_zincir(self):
        d = c.Defter(gecici())
        for i in range(5):
            d.ekle("olay", {"i": i})
        self.assertTrue(c.Defter.dogrula(d.yol)[0])

    def test_satir_degisirse_kirik(self):
        d = c.Defter(gecici())
        for i in range(5):
            d.ekle("olay", {"i": i})
        satirlar = oku(d.yol)
        k = json.loads(satirlar[2])
        k["govde"]["i"] = 99
        satirlar[2] = json.dumps(k, ensure_ascii=False)
        yaz(d.yol, satirlar)
        self.assertFalse(c.Defter.dogrula(d.yol)[0])

    def test_kuyruk_kesilirse_yalniz_zincir_yetmez(self):
        d = c.Defter(gecici())
        for i in range(5):
            d.ekle("olay", {"i": i})
        yayin = d.kafa()
        yaz(d.yol, oku(d.yol)[:3])
        self.assertTrue(c.Defter.dogrula(d.yol)[0], "önek tek başına geçerli zincirdir")
        self.assertFalse(c.Defter.dogrula(d.yol, yayin)[0], "yayımlanmış kafa kesilmeyi yakalamalı")

    def test_iz_bastan_yazilirsa_yayimlanmis_kafa_yakalar(self):
        d = c.Defter(gecici())
        for i in range(4):
            d.ekle("olay", {"i": i})
        yayin = d.kafa()
        yeni = c.Defter(gecici())
        for i in range(4):
            yeni.ekle("olay", {"i": i + 100})
        self.assertTrue(c.Defter.dogrula(yeni.yol)[0])
        self.assertFalse(c.Defter.dogrula(yeni.yol, yayin)[0])

    def test_yarim_satir_cokertmez(self):  # kusur 6
        d = c.Defter(gecici())
        for i in range(3):
            d.ekle("olay", {"i": i})
        with open(d.yol, "a", encoding="utf-8") as f:
            f.write('{"sira": 3, "zaman": 1.0, "tur": "ol')  # yarım yazılmış son satır
        saglam, neden = c.Defter.dogrula(d.yol)
        self.assertFalse(saglam)
        self.assertIn("bozuk", neden)


class ZarfTesti(unittest.TestCase):
    def setUp(self):
        self.kasa = c.Kasa()
        self.h = c.Harcanan(c.Defter(gecici()))

    def test_dogru_zarf_acilir(self):
        z = c.zarfla(self.kasa, "teslim", "merhaba".encode())
        self.assertEqual(c.zarf_ac_tek(self.kasa, self.h, z), "merhaba".encode())

    def test_zarf_ikinci_kez_acilamaz(self):  # kusur 5
        z = c.zarfla(self.kasa, "teslim", b"x")
        c.zarf_ac_tek(self.kasa, self.h, z)
        with self.assertRaises(ValueError):
            c.zarf_ac_tek(self.kasa, self.h, z)

    def test_adres_degisirse_muhur_tutmaz(self):
        z = c.zarfla(self.kasa, "teslim", b"x")
        z["adres"] = "baska"
        self.assertFalse(c.zarf_gecerli(self.kasa, z))

    def test_govde_bir_bit_degisirse_tutmaz(self):
        z = c.zarfla(self.kasa, "teslim", b"x")
        g = list(z["govde"])
        g[10] = "0" if g[10] != "0" else "1"
        z["govde"] = "".join(g)
        self.assertFalse(c.zarf_gecerli(self.kasa, z))

    def test_gecersiz_muhurlu_zarf_numarayi_harcamaz(self):
        z = c.zarfla(self.kasa, "t", b"x")
        z["adres"] = "baska"
        with self.assertRaises(ValueError):
            c.zarf_ac_tek(self.kasa, self.h, z)
        self.assertTrue(self.h.harca(z["no"]), "reddedilen zarf numarayı yakmamalı")

    def test_boyut_sabit(self):
        a = c.zarfla(self.kasa, "t", b"a")
        b = c.zarfla(self.kasa, "t", b"a" * 1000)
        self.assertEqual(len(a["govde"]), len(b["govde"]))

    def test_baska_kasa_acamaz(self):
        z = c.zarfla(self.kasa, "t", b"gizli")
        with self.assertRaises(ValueError):
            c.zarf_ac_tek(c.Kasa(), self.h, z)

    def test_tasiyici_icerigi_gormez(self):
        z = c.zarfla(self.kasa, "t", b"cok gizli mektup")
        self.assertNotIn(b"cok gizli".hex(), z["govde"])


class TekKullanimTesti(unittest.TestCase):
    def test_ikinci_harcama_reddedilir(self):
        h = c.Harcanan(c.Defter(gecici()))
        self.assertTrue(h.harca("abc"))
        self.assertFalse(h.harca("abc"))

    def test_yeniden_baslatinca_harcanan_hatirlanir(self):
        d = c.Defter(gecici())
        c.Harcanan(d).harca("abc")
        self.assertFalse(c.Harcanan(d).harca("abc"))

    def test_iki_ornek_ayni_numarayi_harcayamaz(self):  # kusur 1
        d = c.Defter(gecici())
        h1, h2 = c.Harcanan(d), c.Harcanan(d)
        self.assertTrue(h1.harca("x"))
        self.assertFalse(h2.harca("x"), "ikinci örnek birincinin harcamasını görmeli")


class EsikTesti(unittest.TestCase):
    def test_k_parca_birlestirir(self):
        sir = 123456789123456789
        p = c.esik_bol(sir, 3, 5)
        self.assertEqual(c.esik_birlestir(p[:3]), sir)
        self.assertEqual(c.esik_birlestir([p[0], p[2], p[4]]), sir)

    def test_k_eksik_parca_sirri_vermez(self):
        sir = 123456789123456789
        p = c.esik_bol(sir, 3, 5)
        self.assertNotEqual(c.esik_birlestir(p[:2]), sir)

    def test_32_baytlik_anahtar_geri_gelir(self):  # kusur 2
        anahtar = os.urandom(32)
        p = c.esik_bol(c.bayt_sir(anahtar), 3, 5)
        self.assertEqual(c.sir_bayt(c.esik_birlestir(p[1:4]), 32), anahtar)

    def test_alan_disi_sir_sessizce_kesilmez(self):
        with self.assertRaises(ValueError):
            c.esik_bol(c._P + 5, 2, 3)

    def test_ayni_parca_iki_kez_hata_verir(self):
        p = c.esik_bol(42, 2, 3)
        with self.assertRaises(ValueError):
            c.esik_birlestir([p[0], p[0]])

    def test_k_n_tutarsizligi(self):
        with self.assertRaises(ValueError):
            c.esik_bol(1, 4, 3)
        with self.assertRaises(ValueError):
            c.esik_bol(1, 0, 3)


class KimlikTesti(unittest.TestCase):
    def cevap(self, k, ajan, sayac, anahtar):
        nonce = k.meydan_oku(ajan)
        return nonce, c.cevap_ver(anahtar, nonce)

    def test_dogru_cevap_gecer(self):
        k = c.Kimlik(c.Kasa())
        s, anahtar = k.yeni_anahtar("ajan1")
        nonce, cv = self.cevap(k, "ajan1", s, anahtar)
        self.assertTrue(k.dogrula("ajan1", s, nonce, cv))

    def test_kopya_eski_anahtarla_reddedilir(self):
        k = c.Kimlik(c.Kasa())
        s1, a1 = k.yeni_anahtar("ajan1")
        k.yeni_anahtar("ajan1")
        nonce, cv = self.cevap(k, "ajan1", s1, a1)
        self.assertFalse(k.dogrula("ajan1", s1, nonce, cv))

    def test_baska_ajan_reddedilir(self):
        k = c.Kimlik(c.Kasa())
        s, a = k.yeni_anahtar("ajan1")
        k.yeni_anahtar("ajan2")
        nonce = k.meydan_oku("ajan2")
        self.assertFalse(k.dogrula("ajan2", s, nonce, c.cevap_ver(a, nonce)))

    def test_nonce_tekrari_reddedilir(self):  # kusur 4
        k = c.Kimlik(c.Kasa())
        s, a = k.yeni_anahtar("ajan1")
        nonce, cv = self.cevap(k, "ajan1", s, a)
        self.assertTrue(k.dogrula("ajan1", s, nonce, cv))
        self.assertFalse(k.dogrula("ajan1", s, nonce, cv), "aynı (nonce, cevap) ikinci kez geçmemeli")

    def test_dis_nonce_kabul_edilmez(self):
        k = c.Kimlik(c.Kasa())
        s, a = k.yeni_anahtar("ajan1")
        self.assertFalse(k.dogrula("ajan1", s, "kendi-uydurdugum", c.cevap_ver(a, "kendi-uydurdugum")))

    def test_bayat_deneme_kanit_olarak_kaydedilir(self):  # kusur 3 ve kanıt boşluğu
        d = c.Defter(gecici())
        k = c.Kimlik(c.Kasa(), d)
        s1, a1 = k.yeni_anahtar("ajan1")
        k.yeni_anahtar("ajan1")
        nonce, cv = self.cevap(k, "ajan1", s1, a1)
        self.assertFalse(k.dogrula("ajan1", s1, nonce, cv))
        turler = [x["tur"] for x in d._satirlar()]
        self.assertIn("kopya_suphesi", turler)
        self.assertTrue(c.Defter.dogrula(d.yol)[0])

    def test_yeniden_baslatinca_bayat_anahtar_gecmez(self):  # kusur 3
        d = c.Defter(gecici())
        kasa = c.Kasa()
        k1 = c.Kimlik(kasa, d)
        s1, a1 = k1.yeni_anahtar("ajan1")
        k1.yeni_anahtar("ajan1")
        k2 = c.Kimlik(kasa, d)  # süreç yeniden başladı, aynı ana anahtar
        nonce = k2.meydan_oku("ajan1")
        self.assertFalse(k2.dogrula("ajan1", s1, nonce, c.cevap_ver(a1, nonce)))
        s3, a3 = k2.yeni_anahtar("ajan1")
        self.assertEqual(s3, 3, "sayaç kaldığı yerden devam etmeli")

    def test_kimlik_karakter_siniri(self):
        k = c.Kimlik(c.Kasa())
        with self.assertRaises(ValueError):
            k.yeni_anahtar("a|b")
        with self.assertRaises(ValueError):
            k.yeni_anahtar("A B")


if __name__ == "__main__":
    unittest.main(verbosity=2)
