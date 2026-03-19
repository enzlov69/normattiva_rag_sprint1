# LEVEL_B_DOCUMENT_ENDPOINTS_v1

## Posizionamento

Questo documento consolida in place gli endpoint o punti di ingresso/uscita logici del Livello B documentale nel collegamento runtime controllato A->B->runner->B->A.

Il Livello B resta documentale, tecnico, tracciabile e bloccabile.

## Endpoint documentali del Livello B

### Endpoint contrattuali

#### `/doc/retrieval/query`
Funzione: recupero documentale.

#### `/doc/citation/build`
Funzione: costruzione citazioni documentali.

#### `/doc/vigenza/check`
Funzione: verifica dello stato di vigenza.

#### `/doc/crossref/resolve`
Funzione: risoluzione rinvii normativi.

#### `/doc/m07/support`
Funzione: supporto documentale a M07-LPR.

#### `/doc/coverage/check`
Funzione: stima della copertura documentale.

### Endpoint interni del perimetro B

#### `/runtime/runner/invoke`
Funzione: invocazione tecnica del runner black-box tramite handoff service controllato.

#### `/runtime/runner/map_response`
Funzione: mappatura tecnica della response del runner verso il pacchetto documentale.

### Endpoint trasversali

#### `/doc/audit/fragment`
Funzione: produzione del frammento audit tecnico minimo richiesto dal runtime.

#### `/doc/shadow/fragment`
Funzione: produzione del frammento SHADOW tecnico minimo richiesto dal runtime.

## Regole di perimetro

- Gli endpoint del Livello B sono documentali o tecnici, non metodologici.
- Il runner federato resta black-box e non diventa primo punto logico di accoppiamento.
- Il Livello B puo' restituire solo documentary packet, citation packet, vigenza status, cross-reference status, coverage status, warnings, errors, blocks e trace tecnica.

## Divieti

Nessun endpoint del Livello B puo' restituire o simulare:

- GO o NO_GO
- decisione finale
- validazione finale
- autorizzazione output opponibile
- chiusura M07
- Final Compliance Gate
- Output Authorizer
