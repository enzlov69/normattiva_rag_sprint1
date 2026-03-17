# Runbook operativo — Sprint 13

## Scopo
Questo runbook descrive l'avvio del flusso end-to-end tecnico tra Livello B e Livello A.

## Prerequisiti
- baseline v2 attiva
- sprint 1–12 integrati
- suite test verde
- payload Normattiva disponibile nel perimetro di ingestion

## Sequenza del flusso
1. acquisizione e normalizzazione documentale nel Livello B
2. costruzione report tecnico del Livello B
3. costruzione LevelBDeliveryPackage
4. validazione del pacchetto
5. adattamento tecnico verso il Livello A
6. apertura workflow PPAV
7. governo tecnico M07
8. costruzione bozza RAC
9. final compliance gate tecnico
10. valutazione GO finale possibile nel Livello A
11. eventuale autorizzazione di output tecnico del Livello A

## Regole di uso
- il Livello B non può emettere decisioni finali
- il GO finale resta nel Livello A
- l'autorizzazione riguarda solo output tecnici consentiti
- nessun output opponibile nasce dal solo stato documentale

## Stati finali attesi
- AUTHORIZED_TECHNICAL_OUTPUT
- READY_FOR_METHOD_REVIEW
- SUPPORT_ONLY
- BLOCKED

## Gestione errori
- blocchi aperti -> verificare codes.py e TechnicalReport
- audit incompleto -> verificare AuditIntegrityResult
- M07 richiesto -> governo nel Livello A, mai chiusura dal Livello B
