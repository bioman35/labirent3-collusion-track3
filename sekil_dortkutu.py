"""Labirent Track 3 · SPRINT İÇİ (24 Eki 2026, KARAR 59-60) · Figure 2: detector detection rate and false-alarm rate with TWO negatives.
$0, yalnız sayilar.json okur. Pozitif: doğrulanmış K (G7 anlaştı, pay-tam hücreler; `dort_kutu_pay_tam`). Negatif 1: R (pay-tam, 20 çift).
Negatif 2: S (30 çift, hücre `dedektor_pozitif` × n). Üç sürüm: message-only, action-only, combined. İki mu yan yana.
Kullanım: python sekil_dortkutu.py --girdi ../_sprint/kosu_mu25/rapor_girdi_hakem1 --girdi2 ../_sprint/kosu_mu50/rapor_girdi_hakem1 --cikti ../_sprint/kosu_mu25/rapor_girdi_hakem1/sekil2_dortkutu
Sayılar ayrıca <cikti>.json'a yazılır (rapor bunları alır).
"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURUM = [("mesaj", "message-only"), ("eylem", "action-only"), ("ikisi", "combined")]


def oranlar(s):
    dk = s["dort_kutu_pay_tam"]; h = s["hucreler"]
    out = {}
    for k, ad in SURUM:
        S = [a for a in h if a.startswith("S-")]
        n = sum(h[a]["n"] for a in S); poz = sum(h[a]["dedektor_pozitif"][k] * h[a]["n"] for a in S)
        out[ad] = {"detection_verified_K": dk[k]["yakalama"], "false_alarm_R": dk[k]["yanlis_alarm"],
                   "false_alarm_S": poz / n if n else None, "tp": dk[k]["tp"], "fp_R": dk[k]["fp"], "fp_S": round(poz), "n_S": n,
                   "n_verified_K": dk[k]["tp"] + dk[k]["fn"], "n_R": dk[k]["fp"] + dk[k]["tn"]}
    return out


def ciz(veri, cikti, basliklar):
    fig, axes = plt.subplots(1, len(veri), figsize=(5.2 * len(veri), 3.9), sharey=True)
    if len(veri) == 1:
        axes = [axes]
    renk = {"detection_verified_K": "#1f3a5f", "false_alarm_R": "#8a6d3b", "false_alarm_S": "#7a3b5e"}
    etiket = {"detection_verified_K": "detection, confirmed K pairs", "false_alarm_R": "false alarm, R pairs (independence-instructed)",
              "false_alarm_S": "false alarm, S pairs (uninstructed)"}
    for ax, (v, b) in zip(axes, zip(veri, basliklar)):
        x = range(len(SURUM)); w = 0.26
        for j, (anahtar, r) in enumerate(renk.items()):
            degerler = [v[ad][anahtar] for _, ad in SURUM]
            ax.bar([i + (j - 1) * w for i in x], degerler, width=w, color=r, label=etiket[anahtar])
            for i, d in zip(x, degerler):
                ax.text(i + (j - 1) * w, d + 0.02, "%.2f" % d, ha="center", fontsize=7.5)
        ax.set_xticks(list(x)); ax.set_xticklabels([ad for _, ad in SURUM], fontsize=9)
        ax.set_ylim(0, 1.12); ax.set_title(b, fontsize=10)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    axes[0].set_ylabel("rate", fontsize=9)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=8, frameon=False)
    fig.suptitle("Figure 1 · Detector versions: detection on confirmed colluding pairs (n = 6), false alarms on R (n = 20) and S (n = 30); combined = either version fires", fontsize=9.5)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(cikti + ".svg"); fig.savefig(cikti + ".png", dpi=160)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--girdi", required=True); ap.add_argument("--girdi2"); ap.add_argument("--cikti", required=True)
    a = ap.parse_args()
    veri, basliklar, kaynak = [], [], []
    for g, b in ((a.girdi, "mu = 25"), (a.girdi2, "mu = 50 (robustness)")):
        if g:
            s = json.load(open(os.path.join(g, "sayilar.json"), encoding="utf-8"))
            veri.append(oranlar(s)); basliklar.append(b + " · " + s["hakem"]); kaynak.append(g)
    ciz(veri, a.cikti, basliklar)
    with open(a.cikti + ".json", "w", encoding="utf-8") as f:
        json.dump({"kaynak": kaynak, "paneller": dict(zip(basliklar, veri))}, f, ensure_ascii=False, indent=1)
    for b, v in zip(basliklar, veri):
        print(b, json.dumps({ad: {k: (round(x, 2) if isinstance(x, float) else x) for k, x in d.items()} for ad, d in v.items()}))
    print("yazildi:", a.cikti + ".svg/.png/.json")
