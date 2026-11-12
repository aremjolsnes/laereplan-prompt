# Hva koster det å bruke `--kall`?

Her er et grovt overslag over hva det koster å sende prompten til en språkmodell. Tallene bygger på fire kall som ble gjort 12.11.2026, og på API-prisene som gjaldt da. Elevtallene er runde anslag. Tallene er ment som et grunnlag for samtale og er ikke et budsjett.

## Ett kall

Ett kall dekker én elev i ett fag på ett tidspunkt. Modellen var `claude-opus-5-5` med effort `medium`.

| Eksempel | Tokens inn | Tokens ut | Kostnad |
|---|---|---|---|
| Elev A, matematikk 10. trinn (1. kjøring) | 11 622 | 4 964 | 0,15 USD |
| Elev A, matematikk 10. trinn (2. kjøring) | 11 723 | 4 213 | 0,13 USD |
| Elev C, matematikk 1T (1. kjøring) | 9 423 | 4 283 | 0,12 USD |
| Elev C, matematikk 1T (2. kjøring) | 9 524 | 3 813 | 0,11 USD |

Med andre ord går rundt 10 500 tokens inn og rundt 4 300 tokens ut per kall, og kostnaden ligger på **ca. 0,13 USD**.

- **Svaret er den største kostnaden.** Det modellen skriver, inkludert tenkingen, utgjør rundt to tredjedeler av kostnaden. Kortere svar eller lavere effort gir altså mest å spare per kall.
- **Utsnittet er det meste av det som sendes inn.** Læreplanutsnittet utgjør ca. 85 % av prompten, og det er likt for alle elever i samme fag på samme dato. Vurderingsdataene for eleven er bare en liten del.

## Priser

Prisene er i USD per million tokens og ble hentet 12.11.2026. Se [platform.claude.com/pricing](https://platform.claude.com/docs/en/about-claude/pricing) for gjeldende priser.

| Modell | Inn | Ut | Inn, gjenbrukt fra cache |
|---|---|---|---|
| Claude Opus 5.5 | 4,00 | 20,00 | 0,20 |
| Claude Sonnet 5.5 | 2,00 | 10,00 | 0,10 |
| Claude Haiku 5.5 | 0,10 | 0,50 | (ikke regnet med) |

To måter å spare på:

- **Gjenbruk av utsnittet (prompt caching).** Systemprompten og utsnittet legges først i prompten og merkes for gjenbruk. Kall nummer to og utover for samme fag koster da 5 % av vanlig inn-pris for den delen. Det første kallet koster litt mer (1,25 ganger), men det betyr lite når mange elever har samme fag.
- **Kjøring i bunker (Batch API).** Kallene sendes samlet og kommer tilbake innen et døgn, til halv pris. Det passer når ingen trenger svaret med en gang, for eksempel når en vurderingsrunde behandles over natta.

Skriptet bruker ingen av delene i dag. Modellen velges med `--modell opus|sonnet|haiku`, og standard er `opus`. Se [README](../README.md#velge-modell).

## Per kall, med og uten innsparing

| Modell | Som i dag | Med gjenbruk av utsnittet | Med gjenbruk og bunker |
|---|---|---|---|
| Opus 5.5 | 0,13 USD | 0,09 USD | **0,05 USD** |
| Sonnet 5.5 | 0,06 USD | 0,05 USD | **0,02 USD** |
| Haiku 5.5 | 0,003 USD | – | **0,002 USD** |

Kostnadene for Sonnet og Haiku i tabellen er regnet med like lange svar som fra Opus. Testen nedenfor viste at Sonnet skriver kortere svar, så Sonnet blir litt billigere enn tabellen viser.

## Test av billigere modeller (12.11.2026)

Elev A og elev C ble kjørt med alle tre modellene, med samme prompt og effort `medium`. Svarene ligger i `demo/` (`*.svar.md`, `*.sonnet.svar.md` og `*.haiku.svar.md`).

| Modell | Tokens ut (A / C) | Kostnad per kall | Vurdering |
|---|---|---|---|
| Opus 5.5 | 4 213 / 3 813 | 0,11–0,13 USD | Grundigst. Leser verbene presist, skiller godt mellom data og tolkning, og har gode forbehold. |
| Sonnet 5.5 | 2 966 / 2 771 | ca. 0,05 USD | Nesten like god som Opus. Har samme struktur, finner de samme hullene og bruker «Bygger på» riktig. Litt kortere. |
| Haiku 5.5 | 4 742 / 5 827 | under 0,005 USD | Brukbar, men mindre presis. Den har én faktafeil: den sier at prøven om KM13322 gjaldt to mål, men den gjaldt ett. Den gjentar seg mer, og svaret for elev C mangler tittel. |

Alle de tre modellene viste bare til kompetansemål som finnes i prompten. Det ble sjekket automatisk for alle KM-koder i svarene.

Foreløpig vurdering: **Sonnet ser ut til å være et godt valg til halv pris eller mindre.** Haiku er så billig at den kan være interessant i stor skala, men den trenger en grundigere test, og helst kontroll av svarene. To elever er et lite grunnlag for å konkludere.

## Hva det blir i praksis

Hvor mange kall det blir, avhenger av hvordan løsningen skal brukes. Det er ikke avklart. Tabellen viser noen tenkte eksempler for **én vurderingsrunde**, for eksempel én gang per termin:

| Bruk | Kall | Opus, som i dag | Opus, med gjenbruk og bunker | Sonnet, med gjenbruk og bunker | Haiku, med bunker |
|---|---|---|---|---|---|
| En lærer, én klasse i ett fag (25 elever) | 25 | 3 USD | 1 USD | 0,60 USD | 0,05 USD |
| En ungdomsskole, alle fag med karakter (300 elever × 12 fag) | 3 600 | 460 USD | 170 USD | 80 USD | 6 USD |
| Hele landet, 8.–10. trinn (ca. 190 000 elever × 12 fag) | ca. 2,3 mill. | ca. 300 000 USD | ca. 110 000 USD | ca. 50 000 USD | ca. 4 000 USD |

Brukes det også underveis i året og ikke bare ved terminslutt, må tallene ganges med antall runder.

## Det som betyr mest for prisen

1. **Hvor ofte, og for hvor mange elever.** Det er dette spørsmålet som må avklares først.
2. **Modellen.** Prisforskjellen mellom Opus og Haiku er om lag 40 ganger. Kvaliteten må testes.
3. **Hvor langt svaret er.** Svaret er den største kostnaden. Et kortere svarformat eller lavere effort gir direkte utslag.
4. **Gjenbruk av utsnittet og kjøring i bunker.** Til sammen gir de om lag 60 % lavere pris for Opus, uten at svarene blir dårligere.

Utsnittet fra Grep koster ingenting å hente. Det er en SPARQL-spørring mot sandkassen, og den tar under ett sekund.
