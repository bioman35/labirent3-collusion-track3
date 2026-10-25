# labirent3 · how to run (Track 3, Apart Collusion Sprint, Oct 2026)

Standard library only. Python 3.10+. No package install. Tests: `python -m pytest -q` (or `python -m unittest`).

## 0 · Preexisting work (declared as required by the sprint rules)
Everything in this repository that is dated before 23 October 2026 is **preexisting**: all code (`*.py`), the design document `A_SPEC.md`, the predictions T1-T4, the judge exam (`hakem_sinav.json`, 30 hand-labelled messages), the calibration pilot and rehearsal runs (`pilot_mu25/`, `pilot_mu50/`, `kosu_mu25_duman2/`, `kosu_mu25_prova/`, all with calibration seeds 1000-1011), and the decision log `KARAR_KAYDI.md` up to row 48. The freeze is recorded in `PRE_SPRINT_ETIKETI.txt` and `pre_sprint_md5` (20 October 2026). Also preexisting: the Track 1 package `containment-floor` (September 2026) and an independent run of it by a colleague in September 2026.
**Done during the sprint (23-25 October 2026):** the experiment runs with test seeds 2000-2059, the judge labelling and analysis tables (`rapor_girdi_*`), the figures, and the report. The log timestamps (UTC) in `defter.jsonl` show when each run happened. Calibration runs are declared, not reported.

## 1 · Reproduce every table at $0 (no API key, no LLM call)
Each experiment folder (`kosu_mu25/`, `kosu_mu50/`: the sprint runs with test seeds 2000-2059; `kosu_mu25_kesif_t3/`: the exploratory follow-up of 24 Oct; calibration and rehearsal runs live in `pilot_mu25/`, `pilot_mu50/`, `kosu_mu25_duman2/`, `kosu_mu25_prova/`; `loglar/`: the sprint run and analysis logs; `rapor/REPORT.md`: the report) ships what the analysis needs:
`sonuc/*.json` (prices + messages per run, blind run ids), `ek/*.json` (profit, share, third seller, observer),
`esleme.json` (blind id → condition, sealed), `.kasa` (seal key, released after the runs), `defter.jsonl` (hash-chained log),
`rapor_girdi_hakem1/hakem_etiketleri.json` and `rapor_girdi_hakem2/hakem_etiketleri.json` (every judge label, keyed run|turn|seller).

```
python kosu.py tekrar --mu 25 --tur 20 --kok kosu_mu25 --etiketler kosu_mu25/rapor_girdi_hakem1/hakem_etiketleri.json
python kosu.py tekrar --mu 50 --tur 20 --kok kosu_mu50 --etiketler kosu_mu50/rapor_girdi_hakem1/hakem_etiketleri.json
```
Output: `kosu_muXX/rapor_girdi_tekrar/tablolar.md` and `sayilar.json`. They match the shipped `rapor_girdi_hakem1/` files at the reported precision (checked on a second machine, 25 Oct 2026: largest difference 3e-7, from the numerical price solver; the bootstrap is seeded, so intervals are identical).
If a label is missing the run stops with `KeyError`; nothing is guessed. Judge 2 (Gemini) tables: point `--etiketler` at `rapor_girdi_hakem2/`.

Integrity: `python -c "import cekirdek as c; print(c.Defter.dogrula('kosu_mu25/defter.jsonl'))"` checks the hash chain; `KAFA.txt` is the published head.

## 2 · Re-run the experiment with your own keys (costs money)
Environment variables (names only; values never appear in logs or outputs):
`LLM_API_KEY` (OpenAI-compatible, seller + judge 1), `LLM_BASE_URL` (empty = api.openai.com), `LLM_MODEL` (default `gpt-5.6-luna`),
`GEMINI_API_KEY`, `GEMINI_BASE_URL` (OpenAI-compatible Gemini endpoint), `HAKEM2_MODEL` (default `gemini-3.8-flash`), `BUTCE_TAVAN_USD` (hard cap, default 30).
```
python kosu.py duman                                   # one call per model, < $0.01
python kosu.py sinav                                   # judge exam: 30 hand-labelled messages, gate 0.85 (hakem_sinav.json must be KILIT)
python kosu.py pilot --mu 25 --cift 3 --tur 5          # calibration seeds 1000-1011
python kosu.py kosu  --mu 25 --cift 10 --tur 20 --paralel 5   # test seeds 2000-2059; thresholds + predictions locked in the log first
python kosu.py analiz --mu 25                          # both judges label every message once; agreement (kappa) written
```
Our measured costs (Oct 21 pilot): a 5-turn run ≈ 0.001-0.03 USD, judge labelling ≈ 0.0004 USD per message (Gemini) / 0.00005 (Luna).

## 3 · Delivery gate
`python teslim_kapisi.py REPORT.md --girdi kosu_mu25/rapor_girdi_hakem1 kosu_mu50/rapor_girdi_hakem1` must print `KAPI AÇIK`:
every number in the report exists in a result file, every cited path exists, abstract ≤ 150 words, no over-claiming words, tests pass.

## 4 · What is what
`oyun.py` market (logit demand, third seller) · `ajanlar.py` seller prompts and agents · `hakem.py` message judge + exam · `dedektor.py` detector (message / action / both) ·
`olcum.py` E, M, drift · `ozrapor.py` self-report scoring · `kilit.py` seed split, locks, blind ids · `butce.py` budget cap · `orkestrator.py` run loop + hash-chained log ·
`analiz.py` tables, CIs, exploratory measures · `kosu.py` commands · `teslim_kapisi.py` delivery gate · `A_SPEC.md` design (G1-G16, predictions T1-T4) · `KARAR_KAYDI.md` decision log.
