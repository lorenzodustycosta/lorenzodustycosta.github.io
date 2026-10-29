# Decisioni

- Scelto venv + pip (`requirements.txt`) invece di uv perché è già incluso in Python e non richiede installare altro.
- Scelto `BASE_URL` vuoto di default invece di un URL completo perché il sito è un user site (`lorenzodustycosta.github.io`) servito dalla root, quindi bastano link assoluti `/...` sia in locale sia online.
- Scelto `http.server` + `watchfiles` invece di un dev server con live reload perché basta la libreria standard più una dipendenza leggera; il browser va ricaricato a mano.
- Scelto di eseguire `pytest` nel workflow prima della build già dalla Fase 0 perché costa pochi secondi ed evita di pubblicare un sito rotto.
- Scelto di pubblicare subito il placeholder con `noindex` invece di aspettare la Fase 1 perché verifica la pipeline di deploy in anticipo senza farlo indicizzare. Da rimuovere in Fase 1.
