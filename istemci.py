"""Labirent Track 3 · A4 · LLM istemcisi (OpenAI uyumlu sohbet ucu, yalnız urllib).

Anahtar ortam değişkeninden okunur, hiçbir yere yazılmaz, hiçbir çıktıya basılmaz.
cagri_yap(...) -> (metin, kullanim) ; kullanim = {"giris": int, "cikis": int} API'den gelir, gelmezse None
(butce.py o zaman tahmin diye işaretler). Ağ hatası ya da zaman aşımında IstemciHatasi; orkestratör
koşuyu "cevapsız" sayıp sürdürür, defter hata satırı alır.
21 Eki: GERÇEK anahtarla TEK konuşma zorunlu (sahte istemci dersi), ondan önce "çalışıyor" denmez.
"""
import json
import os
import urllib.error
import urllib.request


class IstemciHatasi(RuntimeError):
    pass


# KARAR (danışman 18 Eki, Kaptan W kusur 16): parametreler model başına tablodan; yeni modeller max_tokens yerine
# max_completion_tokens ister ya da temperature kabul etmez. 21 Eki gerçek çağrıda tek denemeyle doğrulanır.
MODEL_AYAR = {
    "varsayilan": {"sicaklik": 0.7, "en_cok": 300, "token_anahtari": "max_tokens", "sicaklik_gonder": True},
    # 20 Eki duman testi (sunucu, gerçek anahtar): gpt-6-luna ve gpt-5.6-luna 'max_tokens' reddediyor (HTTP 400,
    # "Use 'max_completion_tokens' instead"); temperature gönderilmeden ikisi de OK. Gizli akıl yürütme tokenleri
    # çıkışa sayılır (gpt-6-luna "Merhaba" için 25), bu yüzden tavan 400. gemini-3.8-flash OpenAI uyumlu uçta max_tokens OK.
    "gpt-6":   {"token_anahtari": "max_completion_tokens", "sicaklik_gonder": False, "en_cok": 400},
    "gpt-5.6": {"token_anahtari": "max_completion_tokens", "sicaklik_gonder": False, "en_cok": 400},
    # 21 Eki sınav 1. koşu: gemini-3.8-flash 5/30 cevapsız; ham çıktı 15 token sonra KESİK ("```json\n{"anlasma": true, "neden": "Ort").
    # Düşünme tokenleri tavana sayılıyor, görünen cevap kesiliyor. Tavan 1200 (maliyet önemsiz), hakem bir kez yeniden dener.
    "gemini":  {"token_anahtari": "max_tokens", "sicaklik_gonder": True, "en_cok": 1200},
}


def model_ayari(model):
    for on_ek, a in MODEL_AYAR.items():
        if on_ek != "varsayilan" and model.startswith(on_ek):
            return dict(MODEL_AYAR["varsayilan"], **a)
    return dict(MODEL_AYAR["varsayilan"])


def cagri_yap(model, mesajlar, base_url=None, api_key=None, sicaklik=None, en_cok=None, zaman_asimi=60):
    base = (base_url or os.environ.get("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    key = api_key or os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise IstemciHatasi("anahtar yok: LLM_API_KEY ortam değişkeni tanımlı değil")
    a = model_ayari(model)
    yuk = {"model": model, "messages": mesajlar, a["token_anahtari"]: (en_cok if en_cok is not None else a["en_cok"])}
    if a["sicaklik_gonder"]:
        yuk["temperature"] = sicaklik if sicaklik is not None else a["sicaklik"]
    govde = json.dumps(yuk).encode("utf-8")
    istek = urllib.request.Request(base + "/chat/completions", data=govde, method="POST",
                                   headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(istek, timeout=zaman_asimi) as y:
            d = json.loads(y.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise IstemciHatasi("HTTP %s" % e.code) from None        # gövde basılmaz, anahtar sızmasın
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise IstemciHatasi("ağ: %s" % type(e).__name__) from None
    return cevap_ayikla(d)


def cevap_ayikla(d):
    try:
        metin = d["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise IstemciHatasi("beklenmeyen cevap biçimi")
    k = d.get("usage") or {}
    kullanim = None
    if "prompt_tokens" in k and "completion_tokens" in k:
        kullanim = {"giris": int(k["prompt_tokens"]), "cikis": int(k["completion_tokens"])}
    return metin, kullanim


def cagri_fabrikasi(model, butce, hucre_adi, base_url=None, api_key=None, **ayar):
    """ajanlar.LLMSatici / hakem.Hakem için cagri(mesajlar)->str üretir; her çağrıyı bütçeye yazar."""
    def cagri(mesajlar):
        metin, kullanim = cagri_yap(model, mesajlar, base_url, api_key, **ayar)
        if kullanim:
            butce.kaydet(hucre_adi, model, giris=kullanim["giris"], cikis=kullanim["cikis"])
        else:
            butce.kaydet(hucre_adi, model, metin_giris=json.dumps(mesajlar, ensure_ascii=False), metin_cikis=metin)
        return metin
    return cagri
