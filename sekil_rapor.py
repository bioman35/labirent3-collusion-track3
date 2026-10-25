"""Labirent Track 3 · SPRINT İÇİ (24 Eki 2026) · rapor şekli (Figure 1) · $0, yalnız sayilar.json okur.
Neden ayrı dosya: analiz.sekil1_svg eksenleri [-0,3; 1,3] arasında kırpıyor (S hücreleri −0,97'ye iniyor). Dondurulmuş koda
dokunulmadı; bu dosya sprint içi iş olarak beyan tablosuna girer. matplotlib.
Kullanım: python sekil_rapor.py --girdi ../_sprint/kosu_mu25/rapor_girdi_hakem1 [--girdi2 ../_sprint/kosu_mu50/rapor_girdi_hakem1] --cikti ../_sprint/kosu_mu25/rapor_girdi_hakem1/sekil1_rapor
Çıktı: <cikti>.svg ve .png. Üst panel E (ortalama, %95 bootstrap aralığı, çift noktaları), alt panel M. Hücreler grup sırasıyla.
"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SIRA = ["K-0-sessiz", "K-0-soylendi", "K-yarim-sessiz", "K-yarim-soylendi", "K-tam-sessiz", "K-tam-soylendi", "K-tam-soylendi-yem",
        "R-tam-sessiz", "R-tam-soylendi", "RT-notr", "RT-levha", "RT-yasak", "S-0-sessiz", "S-tam-sessiz", "S-tam-soylendi"]
ETIKET = {"K-0-sessiz": "K · none · not told", "K-0-soylendi": "K · none · told", "K-yarim-sessiz": "K · half · not told",
          "K-yarim-soylendi": "K · half · told", "K-tam-sessiz": "K · full · not told", "K-tam-soylendi": "K · full · told",
          "K-tam-soylendi-yem": "K · full · told · deceptive agent", "R-tam-sessiz": "R · full · not told", "R-tam-soylendi": "R · full · told",
          "RT-notr": "RT · neutral", "RT-yasak": "RT · prohibition", "RT-levha": "RT · standing instruction",
          "S-0-sessiz": "S · none · not told", "S-tam-sessiz": "S · full · not told", "S-tam-soylendi": "S · full · told"}
RENK = {"K": "#1f3a5f", "R": "#8a6d3b", "RT": "#3b7a57", "S": "#7a3b5e"}


def panel(ax, hucreler, anahtar, baslik, ref=None):
    for i, ad in enumerate(SIRA):
        h = hucreler.get(ad)
        if not h:
            continue
        d = h[anahtar]; renk = RENK[ad.split("-")[0]]
        dag = h.get("e_dagilim" if anahtar == "e" else "m_dagilim") or []
        ax.scatter([i + 0.18] * len(dag), dag, s=14, color=renk, alpha=0.35, linewidths=0)
        if d.get("ort") is not None:
            if d.get("alt") is not None:
                ax.plot([i, i], [d["alt"], d["ust"]], color=renk, linewidth=2)
            ax.scatter([i], [d["ort"]], s=46, color=renk, zorder=3)
    for yv in (ref or []):
        ax.axhline(yv, color="#999", linewidth=0.6, linestyle=":")
    ax.set_xticks(range(len(SIRA)))
    ax.set_xticklabels([ETIKET[a] for a in SIRA], rotation=40, ha="right", fontsize=7.5)
    ax.set_ylabel(baslik, fontsize=9)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", labelsize=8)


def ciz(sayilar, cikti, altbaslik):
    h = sayilar["hucreler"]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10.5, 6.6), sharex=True, gridspec_kw={"height_ratios": [1.35, 1]})
    panel(a1, h, "e", "E (coordination index)\n0 = competitive, 1 = joint-profit price", ref=[0.0, 1.0])
    panel(a2, h, "m", "M (share of agreement messages,\ntwo-judge mean not applied: judge 1)", ref=[0.0, 1.0])
    a2.set_ylim(-0.05, 1.05)
    fig.suptitle("Figure 2 · %s · dots: pairs (n = 10 per cell), bars: 95%% bootstrap interval of the cell mean; E above 1 = pairs holding 200, above the joint-profit price" % altbaslik, fontsize=9.5)
    fig.tight_layout()
    fig.savefig(cikti + ".svg"); fig.savefig(cikti + ".png", dpi=160)
    print("yazildi:", cikti + ".svg", cikti + ".png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--girdi", required=True); ap.add_argument("--cikti", required=True); ap.add_argument("--baslik", default="mu = 25, judge 1")
    a = ap.parse_args()
    s = json.load(open(os.path.join(a.girdi, "sayilar.json"), encoding="utf-8"))
    ciz(s, a.cikti, a.baslik)
