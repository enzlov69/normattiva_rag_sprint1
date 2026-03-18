# FINAL AB Runtime Hardening Acceptance Spec v1

## Scopo
Consolidare il runtime handoff A->B->runner->B->A con guard contrattuali stabili, mantenendo i confini Metodo Cerda / Livello B e la retrocompatibilita' dei contratti gia' verdi.

## Perimetro
- Service: `runtime/final_ab_runtime_handoff_service.py`
- Nessuna modifica a runner black-box, raw validator, response-envelope gate, invoker reale, retrieval/router/ranking/corpus.

## Contratti ingresso request (A -> handoff service)
Request minima valida:
- `request_id` non vuoto
- `case_id` non vuoto
- `trace_id` non vuoto
- `target_module` non vuoto

Target compatibili ammessi:
- `level_b_runtime_handoff`
- `B_RUNTIME_HANDOFF`
- `B_Runtime`
- eventuale `expected_target_module` esplicitato nel costruttore

Errori contrattuali request:
- request invalida -> `status=REJECTED`, `errors[0].code=INVALID_AB_REQUEST`, `blocks[0].block_code=AUDIT_INCOMPLETE`
- target mismatch -> `status=REJECTED`, `errors[0].code=TARGET_MODULE_MISMATCH`, `blocks[0].block_code=RAG_SCOPE_VIOLATION`

## Contratti runtime interni
Pipeline nominale:
1. invocazione runner (black-box invariato)
2. raw validation gate pre-mapper
3. mapper
4. post-mapper response-envelope gate (solo sui flussi envelope-based che arrivano al mapper)

Stop-before-mapper ammesso:
- se raw validation e' `BLOCKED/REJECTED/ERROR` e il risultato raw e' validator-structured
- in questo caso il mapper non viene invocato
- l'envelope finale resta bloccante e propaga warnings/errors/blocks dal raw validation result

Flusso post-mapper gate:
- se il mapper produce envelope con `payload.documentary_packet`, il response-envelope gate e' applicato
- il gate puo' ripristinare blocchi critici persi, audit/shadow guards e coerenza status

## Contratti output (B -> A)
Envelope minimo valido:
- `request_id`, `case_id`, `trace_id`, `api_version`
- `responder_module`, `status`, `payload`
- `warnings`, `errors`, `blocks`, `timestamp`

Documentary packet minimo (quando presente):
- `sources`, `norm_units`, `citations_valid`, `citations_blocked`
- `vigenza_records`, `cross_reference_records`, `coverage_assessment`
- `warnings`, `errors`, `blocks`, `shadow_fragment`

## Regole di stabilita' e incompatibilita'
- Nessun downgrade improprio di blocchi critici verso stati meno restrittivi.
- Nessun campo conclusivo/decisorio nel Livello B (`output_authorized`, `final_decision`, chiusure M07, ecc.).
- Boundary M07 invariato: il Livello B segnala e blocca, non conclude.
- Livello B subordinato al Metodo Cerda: recupera, struttura, traccia, segnala, blocca.

## Fallback ammessi
- Normalizzazione interna di risultati raw validator in formati eterogenei (mapping, dataclass, object) senza modificare il validator.
- Fallback mapper legacy (function adapter) solo per strutturazione documentale non conclusiva.
- Payload parziali ammessi solo come output non conclusivo, senza estendere responsabilita' decisorie del Livello B.
