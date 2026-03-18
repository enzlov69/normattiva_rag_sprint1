# LEVEL_A_LEVEL_B_FINAL_INTEGRATION_SPEC_v1

## Titolo

Specifica finale di integrazione controllata tra Livello A (Metodo Cerda – PPAV) e Livello B (Normattiva RAG)

---

## 1. Scopo

Il presente file definisce il collegamento finale corretto tra:
- il Livello A, titolare esclusivo del governo istruttorio;
- il Livello B, sottosistema documentale subordinato.

Lo scopo è impedire per costruzione che il Livello B sconfinI in funzioni di interpretazione, decisione, motivazione, validazione o chiusura di M07-LPR.

---

## 2. Decisione architetturale

Il collegamento finale corretto non è “attaccare il RAG al Metodo Cerda” come motore unico.

Il collegamento corretto consiste nel far sì che:
- il Livello A governi il flusso;
- il Livello B risponda tramite interfaccia versionata e bloccabile;
- i blocchi critici del Livello B si propaghino al Livello A;
- il GO / NO-GO finale e l’output opponibile restino nel Livello A.

---

## 3. Regole di non delega

Il Livello B non può:
- qualificare il fatto;
- scegliere la norma prevalente;
- valutare l’applicabilità concreta;
- motivare;
- concludere;
- validare;
- autorizzare output opponibili;
- chiudere M07-LPR;
- sostituire RAC, PPAV, Final Compliance Gate o Output Authorizer.

---

## 4. Flusso canonico A→B→A

1. Apertura caso nel Livello A.
2. Generazione `case_id`.
3. Generazione `trace_id`.
4. Apertura audit trail e SHADOW.
5. Esecuzione FASE 0.
6. Attivazione dominio.
7. Chiamata documentale A→B.
8. Restituzione pacchetto documentale minimo.
9. Governo M07-LPR nel Livello A.
10. Costruzione RAC nel Livello A.
11. Final Compliance Gate nel Livello A.
12. Output Authorizer nel Livello A.

---

## 5. Interfaccia obbligatoria

Ogni chiamata A→B e B→A deve essere:
- versionata;
- auditata;
- bloccabile;
- tracciata tramite `case_id` e `trace_id`;
- validata contro schema request/response.

---

## 6. Oggetto minimo restituito dal Livello B

Il Livello B deve restituire un pacchetto documentale minimo con:
- fonti;
- unità normative;
- citazioni valide;
- citazioni bloccate o incomplete;
- stato vigenza;
- stato rinvii;
- coverage;
- warning;
- errors;
- blocks;
- trace tecnica.

---

## 7. Collegamento con M07-LPR

Il Livello B può solo:
- ordinare il materiale normativo;
- restituire pacchetto documentale;
- segnalare omissioni;
- segnalare allegati e rinvii;
- richiedere `human_completion_required`.

Il Livello B non può:
- dichiarare lettura integrale completata;
- sostituire il presidio umano/metodologico;
- chiudere M07-LPR.

---

## 8. Collegamento con RAC, compliance e output

Il RAC nasce solo nel Livello A.
Il Final Compliance Gate nasce solo nel Livello A.
L’Output Authorizer nasce solo nel Livello A.

Il Livello B può solo produrre esiti documentali non opponibili.

---

## 9. Blocchi critici

Devono propagarsi almeno:
- `CORPUS_MISSING`
- `SOURCE_UNVERIFIED`
- `CITATION_INCOMPLETE`
- `VIGENZA_UNCERTAIN`
- `CROSSREF_UNRESOLVED`
- `M07_REQUIRED`
- `RAG_SCOPE_VIOLATION`
- `AUDIT_INCOMPLETE`
- `OUTPUT_NOT_OPPONIBLE`
- `COVERAGE_INADEQUATE`

---

## 10. Regola di stop

Il collegamento finale A/B è non conforme se:
- il Livello B conclude;
- il Livello B valida;
- il Livello B chiude M07;
- un blocco critico non si propaga;
- manca audit;
- manca SHADOW;
- il Final Compliance Gate non resta nel Livello A.

---

## 11. Clausola finale

Il collegamento finale è conforme solo se il Metodo Cerda governa il caso dall’inizio alla fine e il Normattiva RAG risponde esclusivamente come sottosistema documentale subordinato.
