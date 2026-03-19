# FINAL_AB_RUNTIME_RELEASE_CHECKLIST_v1

## 1. Uso della checklist

Questa checklist e' riusabile come presidio manuale di rilascio della baseline runtime finale A/B.

Non sostituisce la Fase 10 della roadmap.
Non sostituisce il Metodo Cerda.
Non sostituisce il Final Compliance Gate del Livello A.

Formula di governo da confermare prima del rilascio:

**Metodo Cerda governa. RAG recupera. AI assiste. L'uomo decide e firma.**

Naming tecnico prevalente del Livello B per questa checklist:

- `RAG Normativo Governato e Federato`

## 2. Controlli tecnici obbligatori

- [ ] `python tools/final_ab_runtime_anomaly_validator.py` verde
- [ ] `python tools/final_ab_runtime_baseline_verifier.py` verde
- [ ] `tests/test_final_ab_runtime_anomaly_registry_consistency.py` verde
- [ ] `tests/test_final_ab_runtime_outcome_semantics.py` verde
- [ ] `tests/test_final_ab_runtime_anomaly_validator.py` verde
- [ ] `tests/test_final_ab_runtime_golden_cases.py` verde
- [ ] `tests/test_final_ab_runtime_baseline_verifier.py` verde
- [ ] `anomaly registry`, `severity canon` e `propagation matrix` coerenti
- [ ] `golden cases` coerenti con registry/canon/matrix
- [ ] boundary `M07` integro
- [ ] nessuna modifica interna distruttiva del runner
- [ ] nessuna nuova logica decisoria introdotta nel Livello B
- [ ] nessun campo conclusivo o validativo nel Livello B

## 3. Controlli documentali obbligatori

- [ ] presente la specifica `docs/FINAL_AB_RUNTIME_RELEASE_GATE_SPEC_v1.md`
- [ ] presente la checklist `docs/FINAL_AB_RUNTIME_RELEASE_CHECKLIST_v1.md`
- [ ] presenti i documenti essenziali Fase 8-9
- [ ] AI assiste nel Livello A ma non decide
- [ ] orchestrazione AI-assistita nel Livello A espressa nei documenti pertinenti
- [ ] approvazione umana finale obbligatoria espressa nei documenti pertinenti
- [ ] confermato che l'uomo decide e firma
- [ ] confermato che il supporto documentale a M07 non equivale a chiusura M07
- [ ] confermato che il Livello B resta `RAG Normativo Governato e Federato`
- [ ] confermato che il Livello B non contiene campi conclusivi o decisori
- [ ] confermato che il release gate non valida l'istruttoria e non conclude

## 4. Controlli raccomandati

- [ ] working tree pulito
- [ ] commit di baseline allineato alla release finale
- [ ] tag di baseline allineato alla release finale
- [ ] verifica manuale della leggibilita' del report prodotto dal baseline verifier
- [ ] verifica manuale che il workflow GitHub sia rimasto semplice, auditabile e lineare
- [ ] verifica manuale che non siano stati toccati retrieval, router, ranking o corpus
- [ ] verifica manuale che handoff service, raw validator, response-envelope gate e runner non siano stati riaperti senza necessita' meccanica dimostrata dai test

## 5. Criterio di decisione sul rilascio

### 5.1 Non rilasciabile

La baseline e' non rilasciabile se almeno uno dei controlli obbligatori fallisce.

### 5.2 Rilasciabile con warning tecnici

La baseline e' rilasciabile con warning tecnici se tutti i controlli obbligatori sono verdi ma restano warning tecnici non bloccanti da tracciare.

### 5.3 Rilasciabile pienamente

La baseline e' pienamente rilasciabile se tutti i controlli obbligatori sono verdi e non restano warning tecnici rilevanti aperti.

## 6. Chiusura manuale obbligatoria

Prima di dichiarare stabile la baseline finale:

- [ ] conferma esplicita del responsabile umano di rilascio
- [ ] conferma che il Livello A mantiene il governo metodologico
- [ ] conferma che il release gate resta solo presidio tecnico di stabilita' e readiness

