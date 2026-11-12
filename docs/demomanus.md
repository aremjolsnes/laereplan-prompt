# Demomanus: Grep som kunnskapsgraf for AI på vurderingsdata

Ca. 30 minutter med skjermdeling. Hovedsporet er fellesfag og studieforberedende: læreplanutsnittet og prompten. ESCO er bare et kort sideblikk.

Alle elevdata i demoen er oppdiktet.

## Før møtet

- [ ] **Vekk Fuseki-maskinen** 2–3 minutter før møtet. Den sover når ingen bruker den, og første spørring kan ta et halvt minutt:
      `curl -s "https://grep-fuseki-v3.fly.dev/ds/query?query=ASK%7B%7D"`
- [ ] Aktiver venv i `laereplan-prompt` og sjekk at `ANTHROPIC_API_KEY` er satt: `python -c "import os;print(bool(os.environ.get('ANTHROPIC_API_KEY')))"`
- [ ] Åpne sparql.mjolne.com med fanene under (punkt 2, 4 og 5) klare.
- [ ] Stor skrift i terminalen. Ha `demo/` åpen i editoren som reserve: der ligger ferdige prompter og svar hvis nett eller API svikter.

## 1. Problemet (3 min)

- Spørsmålet var om Udir har en kunnskapsgraf for læreplandata. Svaret er «ja og nei»: Grep-dataene er RDF, men uten ontologi som binder dem sammen, og ontologiene ligger ikke i noe repo.
- Sandkassen er et forsøk på å vise hva som skal til: ontologi (`udir:`), normaliserte perioder, utledede typer, SKOS, koblinger til EU-vokabularer og et fritekstsøk. Alt lastes inn på nytt fra Grep hver natt.
- Koblingen til det dere gjør: **en prompt bygd av vurderingsdata og den relevante delen av læreplanen.** Det vanskelige er «den relevante delen». Det er det sandkassen løser.

## 2. Læreplanutsnittet (5 min)

I sparql.mjolne.com, endepunktet «Sandkassen»: kjør `laereplanutsnitt.rq` for `MAT0015` (matematikk 10. trinn).

Vis i resultatet:
- **Kjeden** fagkode → opplæringsfag → læreplan og kompetansemålsett, valgt etter **datoen**. Fagkoden er det skolens systemer har. Læreplanen er det modellen trenger.
- **Kompetansemålene** med kjerneelementer, grunnleggende ferdigheter og tverrfaglige temaer.
- **Verbene** med Udirs forklaring. «Utforske» betyr noe annet enn «bruke», og det må modellen vite.
- **Forklaring av målet** (didaktisk støtte) for KM13328 og KM13323.
- **Bygger på**: målene fra 8. og 9. trinn som et mål bygger på.

Poeng: dette er 30 kB, ikke hele læreplanverket. Det får plass i én prompt, og alt har en kode som kan etterprøves.

## 3. Fra utsnitt til prompt (12 min, hoveddelen)

I terminalen, i `laereplan-prompt`:

**a) Vis prompten for elev A (matematikk 10. trinn)**

```
python lag_prompt.py --vurdering eksempler/mat0015-elev-a.json --lagre demo/mat0015-elev-a.prompt.txt
```

Åpne fila. Vis de tre delene: systemprompten (rollen og reglene), utsnittet som Markdown og vurderingsdataene som JSON. Pek på at vurderingene viser til kompetansemål med **kode**. Det er koblingen som gjør resten mulig.

**b) Send den til modellen**

```
python lag_prompt.py --vurdering eksempler/mat0015-elev-a.json --kall
```

Mens svaret kommer: legg merke til at modellen viser til koder, at den skiller mellom det dataene viser og det den tolker, og at den foreslår å gå tilbake til mål fra tidligere trinn (fra «Bygger på»). Ingen karakter.

**c) Datoen betyr noe**

```
python lag_prompt.py --vurdering eksempler/mat0015-elev-a.json --dato 2025-03-01
```

Samme fagkode, men nå gjaldt MAT01-05 (fra 2020) og ikke MAT01-06 (fra 1. august 2026). Skriptet advarer om at ingen av elevens mål finnes i utsnittet. En vurdering skal leses mot den læreplanen som gjaldt da den ble gitt.

**d) Studieforberedende: elev C i 1T (Vg1)**

```
python lag_prompt.py --vurdering eksempler/mat1021-elev-c.json --kall
```

Poeng: eleven sliter med andregradsuttrykk (KM12759). «Bygger på» peker tilbake til 10. trinn (KM231, multiplikasjon av polynomer), og modellen kan bruke det til å foreslå hva som bør repeteres.

Ærlig merknad: 1T-planen (MAT09-02) peker på 10.-trinnsmål i **MAT01-05**. Det stemmer for dem som går Vg1 nå, men ikke for kullene etter.

**Ekstra hvis det er tid: elev B i naturfag 10. trinn** (`eksempler/nat0021-elev-b.json`). Naturfag har mange forklaringer av målene.

## 4. Fritekstsøk (3 min)

I sparql.mjolne.com:

```sparql
SELECT ?km ?tekst ?score WHERE {
  (?km ?score) text:query (udir:bokmaalTittel "statistikk") .
  ?km a u:kompetansemaal_lk20 ;
      u:tilhoerer-laereplan d:MAT01-06 ;
      udir:bokmaalTittel ?tekst .
} ORDER BY DESC(?score)
```

Poeng: norsk stamming («modellering» finner «modeller»). Nyttig når vurderingsdata har fritekst, men ikke koder: da kan man finne kandidatmål og la et menneske velge.

Prøv også `"kildekritikk"` uten læreplanfilteret (16 treff på tvers av fag).

## 5. ESCO, kort (2 min)

Alle 223 gjeldende Vg3-læreplaner i yrkesfag har kompetansemål koblet til ESCO-ferdigheter, til sammen 23 940 koblinger, foreslått av en språkmodell og kontrollert med stikkprøver.

```sparql
SELECT ?relasjon ?ferdighet ?type WHERE {
  d:KM8644 ?r ?f .
  ?f a esco:Skill ; skos:prefLabel ?ferdighet ; esco:skillType/skos:prefLabel ?type .
  VALUES ?r { skos:closeMatch skos:narrowMatch skos:broadMatch skos:relatedMatch }
  BIND(STRAFTER(STR(?r), "#") AS ?relasjon)
} ORDER BY ?relasjon ?ferdighet
```

Fellesfag og studieforberedende ↔ ESCO står på idélista (via ISCED-F og kunnskapsbegreper). Det er ikke gjort.

## 6. Begrensninger (3 min)

- Utsnittet gjelder bare **LK20**. Fagkoder uten LK20-læreplan (privatskolekoder, UPF og forsøk) gir tomt svar. Det er tilsiktet i Grep.
- **Bygger på** er registrert for noen fag (blant annet matematikk 1.–10., 1T, naturfag, samfunnsfag, engelsk og historie), men ikke for R1, S1, Fysikk 1 og Kjemi 1.
- **Forklaring av målet** finnes for rundt 400 mål i 77 læreplaner, flest i matematikk og naturfag.
- Sandkassen er et eksperiment, ikke en tjeneste fra Udir. Den kjører på en liten maskin og kan være treg første gang.
- **Ekte elevdata** til en språkmodell krever avklart behandlingsgrunnlag, databehandleravtale og personvernvurdering.

## 7. Videre (2 min)

- **Deres egne data:** Hvordan ser vurderingsdataene deres ut? Har de koder for kompetansemål eller bare fritekst? Et anonymisert eller oppdiktet eksempel i deres format er neste naturlige steg.
- **Egen bruker i workbench** er laget, med faner for spørringene over.
- **Som verktøy for en AI-agent:** Utsnittet kan tilbys som et MCP-verktøy, slik at en agent selv henter riktig læreplan for en fagkode og dato. Vi har en tidligere prototype av dette.
- Koden ligger i repoene `laereplan-prompt` (dette skriptet) og `grep-jena-fuseki` (sandkassen, åpent).
