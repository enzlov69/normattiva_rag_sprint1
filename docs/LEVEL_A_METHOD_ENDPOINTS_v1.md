# LEVEL_A_METHOD_ENDPOINTS_v1

## Posizionamento

Questo documento consolida in place gli endpoint o punti di ingresso/uscita logici del Livello A metodologico nel collegamento runtime controllato A->B->runner->B->A.

Il Livello A resta il solo livello di governo metodologico.

## Endpoint metodologici del Livello A

### Endpoint interni

#### `/method/case/register`
Funzione: apertura e registrazione del caso.

#### `/method/domain/activate`
Funzione: attivazione del dominio documentale e dei moduli coerenti.

#### `/method/m07/open`
Funzione: apertura e governo del presidio M07-LPR.

#### `/method/rac/build`
Funzione: costruzione del RAC sotto governo metodologico.

#### `/method/compliance/finalize`
Funzione: esecuzione del Final Compliance Gate.

#### `/method/output/authorize`
Funzione: autorizzazione finale dell'output opponibile.

### Endpoint contrattuali verso il collegamento A/B

#### `/method/runtime/handoff/request`
Funzione: costruzione e inoltro della request documentale controllata verso il Livello B runtime.

#### `/method/runtime/handoff/receive`
Funzione: ricezione del pacchetto documentale tecnico, dei warning, degli errori e dei blocchi propagati.

### Endpoint trasversali

#### `/method/audit/runtime`
Funzione: registrazione audit trail del collegamento runtime.

#### `/method/shadow/runtime`
Funzione: registrazione SHADOW del percorso A->B->runner->B->A.

## Regole di perimetro

- Gli endpoint del Livello A sono metodologici o trasversali, non documentali.
- Il Livello A puo' chiamare il Livello B solo tramite handoff controllato.
- Il Livello A puo' ricevere dal Livello B solo output documentali e tecnici.
- Final Compliance Gate e Output Authorizer restano interni al Livello A.

## Divieti

Nessuno di questi endpoint puo' essere delegato al Livello B.
Il Livello B non puo' esporre equivalenti di:

- `compliance/finalize`
- `output/authorize`
- chiusura M07
- decisione finale
- firma
