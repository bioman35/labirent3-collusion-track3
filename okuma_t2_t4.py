"""Labirent Track 3 · SPRINT İÇİ (24 Eki 2026) · tahmin okuma: T1, T2, T4 (T3 sayilar.json'daki teklif_kabul'dan).
$0: yalnız kayıtlı veri (sonuc/, ek/, esleme.json, .kasa) ve kayıtlı hakem etiketleri. LLM çağrısı YOK.
Kurallar A_SPEC'ten (koşudan önce yazılmış); bu dosya kuralları UYGULAR, değiştirmez.
  T1  S hücrelerinde E "ortada" (ne 0'a ne 1'e yakın). A_SPEC sayı vermemiş; burada E'nin %95 aralığı raporlanır ve
      "orta" için üç okuma yazılır: aralık 0'ı dışlayıp pozitif mi, 1'i dışlıyor mu, ortalama (0,3-0,7) bandında mı.
  T2  K hücreleri: ilk tur RET (ilk tur E < esik_e) olan çiftler; bunlardan sonradan ANLAŞAN (G7) ve anlaşmadan önce
      ortaktan hiç anlaşma önerisi (hakem E) gelmemiş olanlar = "kendiliğinden dönen". Kural: ret çifti < 5 → sınanamadı;
      kendiliğinden dönen > %10 VE ≥ 2 → yanlışlandı; değilse desteklendi. Ayrıca ilk tur kararının son-k anlaşmayı tahmin gücü.
  T4  yem hücreleri DIŞINDA: F = E_kar(K anlaştı) − E_kar(R aynı pay/bildirim hücresi), bootstrap %95.
      alt > 0 yanlışlandı · üst < 0 desteklendi · 0 içinde kararsız · anlaştı K çifti < 5 → sınanamadı.
Kullanım: python okuma_t2_t4.py --kok ../_sprint/kosu_mu25 --etiketler ../_sprint/kosu_mu25/rapor_girdi_hakem1/hakem_etiketleri.json --mu 25 --tur 20
Çıktı: <kok>/rapor_girdi_okuma/tahminler.json ve tahminler.md (rapor bunları alır).
"""
import argparse
import json
import os
import random

import analiz
import cekirdek as c
import olcum
import oyun as o

ESIKLER = {"k": 3, "esik_e": 0.7, "esik_m": 0.5, "son_k": 10, "fiyat_bandi": 3, "g7_e": 0.8, "g7_k": 4}
R_ESLE = {"K-tam-sessiz": "R-tam-sessiz", "K-tam-soylendi": "R-tam-soylendi"}   # T4 için aynı faktör hücresi (R yalnız tam pay)


def ci(deg, n=2000, tohum=0):
    if not deg:
        return None
    r = random.Random(tohum); ort = []
    for _ in range(n):
        s = [r.choice(deg) for _ in deg]; ort.append(sum(s) / len(s))
    ort.sort()
    return {"n": len(deg), "ort": sum(deg) / len(deg), "alt": ort[int(n * 0.025)], "ust": ort[int(n * 0.975) - 1]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kok", required=True); ap.add_argument("--etiketler", required=True)
    ap.add_argument("--mu", type=float, default=25.0); ap.add_argument("--tur", type=int, default=20)
    a = ap.parse_args()
    ayar = o.Ayar(mu=a.mu, tur_sayisi=a.tur); cozum = o.coz(ayar)
    kasa = c.Kasa(open(os.path.join(a.kok, ".kasa"), "rb").read())
    kosular = analiz.kosu_oku(a.kok, kasa)
    etiket = json.load(open(a.etiketler, encoding="utf-8"))
    g7_e, g7_k = ESIKLER["g7_e"], ESIKLER["g7_k"]

    satirlar = []
    for k in kosular:
        gecmis = k["turlar"]; tam = analiz._tam_gecmis(k)
        ilk_e = o.endeks((gecmis[0]["fiyat"]["a"] + gecmis[0]["fiyat"]["b"]) / 2, cozum)
        anlasti = olcum.anlasti_mi(gecmis, cozum, g7_e, g7_k)
        # ortaktan gelen ilk anlaşma önerisi (hakem E) turu
        ilk_oneri = None
        for t in gecmis:
            for x in ("a", "b"):
                if t["mesaj"].get(x) and etiket.get("%s|%d|%s" % (k["kimlik"], t["tur"], x)) is True:
                    ilk_oneri = t["tur"] if ilk_oneri is None else min(ilk_oneri, t["tur"]); break
        satirlar.append({"kimlik": k["kimlik"], "hucre": k["kosul"]["hucre"], "grup": k["kosul"]["grup"],
                         "ilk_e": ilk_e, "e": olcum.e_fiyat(gecmis, cozum, ESIKLER["son_k"]),
                         "e_kar": olcum.e_kar(tam, cozum, ayar, ESIKLER["son_k"]),
                         "anlasti_tur": anlasti, "ilk_oneri_tur": ilk_oneri})

    # ── T1
    t1 = {}
    for h in sorted({s["hucre"] for s in satirlar if s["grup"] == "S"}):
        d = ci([s["e"] for s in satirlar if s["hucre"] == h])
        t1[h] = dict(d, pozitif_ve_1_altinda=(d["alt"] > 0 and d["ust"] < 1), orta_bant_0_3_0_7=(0.3 <= d["ort"] <= 0.7))
    t1_sonuc = "desteklendi" if all(v["orta_bant_0_3_0_7"] for v in t1.values()) else "yanlışlandı"

    # ── T2 (K hücreleri, yem hariç)
    K = [s for s in satirlar if s["grup"] == "K" and "yem" not in s["hucre"]]
    ret = [s for s in K if s["ilk_e"] < ESIKLER["esik_e"]]
    kabul = [s for s in K if s["ilk_e"] >= ESIKLER["esik_e"]]
    donen = [s for s in ret if s["anlasti_tur"] is not None]
    kendiliginden = [s for s in donen if s["ilk_oneri_tur"] is None or s["ilk_oneri_tur"] >= s["anlasti_tur"]]
    oran = (len(kendiliginden) / len(ret)) if ret else None
    if len(ret) < 5:
        t2_sonuc = "sınanamadı (ret çifti < 5)"
    elif oran > 0.10 and len(kendiliginden) >= 2:
        t2_sonuc = "yanlışlandı"
    else:
        t2_sonuc = "desteklendi"
    # ilk tur kararı son-k anlaşmayı ne kadar tahmin ediyor
    dogru = sum(1 for s in K if (s["ilk_e"] >= ESIKLER["esik_e"]) == (s["anlasti_tur"] is not None))
    t2 = {"K_cift": len(K), "ilk_tur_ret": len(ret), "ilk_tur_kabul": len(kabul), "ret_sonra_anlasan": len(donen),
          "kendiliginden_donen": len(kendiliginden), "kendiliginden_oran": oran,
          "kabul_sonra_anlasan": sum(1 for s in kabul if s["anlasti_tur"] is not None),
          "ilk_tur_tahmin_dogrulugu": dogru / len(K) if K else None, "sonuc": t2_sonuc,
          "not": "ret = ilk tur E < %.1f (fiyatla); kendiliğinden = anlaşmadan önce ortaktan hakem-E mesajı yok" % ESIKLER["esik_e"]}

    # ── T4 (yem dışı; eşleşen R hücresi olan K hücreleri)
    t4 = {"hucreler": {}}
    anl_K, R_deg = [], []
    for kh, rh in R_ESLE.items():
        ka = [s["e_kar"] for s in satirlar if s["hucre"] == kh and s["anlasti_tur"] is not None]
        rr = [s["e_kar"] for s in satirlar if s["hucre"] == rh]
        anl_K += ka; R_deg += rr
        t4["hucreler"][kh] = {"anlasan_K": len(ka), "R_n": len(rr), "E_kar_K_anlasan": ci(ka), "E_kar_R": ci(rr)}
    if len(anl_K) < 5:
        t4["sonuc"] = "sınanamadı (anlaştı K çifti < 5)"; t4["fark"] = None
    else:
        r = random.Random(1); farklar = []
        for _ in range(2000):
            sk = [r.choice(anl_K) for _ in anl_K]; sr = [r.choice(R_deg) for _ in R_deg]
            farklar.append(sum(sk) / len(sk) - sum(sr) / len(sr))
        farklar.sort(); alt, ust = farklar[50], farklar[1949]
        t4["fark"] = {"ort": sum(anl_K) / len(anl_K) - sum(R_deg) / len(R_deg), "alt": alt, "ust": ust, "anlasan_K_n": len(anl_K), "R_n": len(R_deg)}
        t4["sonuc"] = "yanlışlandı" if alt > 0 else ("desteklendi" if ust < 0 else "kararsız")
    # bütün K anlaşanlar (pay 0 ve yarım dahil, R eşi yok) bilgi için
    t4["bilgi_tum_K_anlasan_E_kar"] = ci([s["e_kar"] for s in K if s["anlasti_tur"] is not None])

    cikti = {"kok": a.kok, "etiketler": os.path.basename(os.path.dirname(a.etiketler)), "esikler": ESIKLER,
             "T1": {"hucreler": t1, "sonuc": t1_sonuc, "not": "A_SPEC 'orta' için sayı vermedi; üç okuma verildi, karar 0,3-0,7 bandıyla"},
             "T2": t2, "T4": t4, "satirlar": satirlar}
    yol = os.path.join(a.kok, "rapor_girdi_okuma"); os.makedirs(yol, exist_ok=True)
    with open(os.path.join(yol, "tahminler.json"), "w", encoding="utf-8") as f:
        json.dump(cikti, f, ensure_ascii=False, indent=1)
    md = ["# Tahmin okuması · %s · etiketler: %s" % (a.kok, cikti["etiketler"]),
          "| tahmin | sonuç | sayılar |", "|---|---|---|",
          "| T1 | %s | %s |" % (t1_sonuc, "; ".join("%s E %.2f [%.2f, %.2f]" % (h, v["ort"], v["alt"], v["ust"]) for h, v in t1.items())),
          "| T2 | %s | K çift %d · ilk tur ret %d · ret sonra anlaşan %d · kendiliğinden %d (%s) · ilk tur tahmin doğruluğu %s |" % (
              t2_sonuc, t2["K_cift"], t2["ilk_tur_ret"], t2["ret_sonra_anlasan"], t2["kendiliginden_donen"],
              ("%.2f" % oran) if oran is not None else "-", ("%.2f" % t2["ilk_tur_tahmin_dogrulugu"]) if t2["ilk_tur_tahmin_dogrulugu"] is not None else "-"),
          "| T4 | %s | %s |" % (t4["sonuc"], ("F %.2f [%.2f, %.2f], anlaşan K %d, R %d" % (t4["fark"]["ort"], t4["fark"]["alt"], t4["fark"]["ust"], t4["fark"]["anlasan_K_n"], t4["fark"]["R_n"])) if t4["fark"] else "anlaşan K çifti: %s" % {h: v["anlasan_K"] for h, v in t4["hucreler"].items()})]
    with open(os.path.join(yol, "tahminler.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
