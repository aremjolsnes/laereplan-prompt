# Øving: gjennomfør demoen trinn for trinn

Dette er en praktisk veiledning til [demomanus.md](demomanus.md). Den forteller hva du gjør i hvert punkt, og hvor du gjør det. Bruk den når du øver, eller som jukselapp under møtet.

Du trenger tre ting:
- **VS Code** til terminalen og filene.
- **Nettleseren** til sparql.mjolne.com.
- Eventuelt **Mobsidian** for å ha manuset oppe ved siden av.

## Før du starter (10 minutter før)

1. **Åpne prosjektet i VS Code:** Velg **File → Open Folder…** og deretter `C:\Users\AMJ\git\grep-sandkasse\laereplan-prompt`.
2. **Åpne en terminal:** Velg **Terminal → New Terminal**. Terminalen åpnes nederst i vinduet og står allerede i riktig mappe.
3. **Gjør skriften større,** så den er lesbar ved skjermdeling: Trykk Ctrl+Shift+P, skriv `zoom in` og velg **View: Zoom In** et par ganger.
4. **Vekk Fuseki-maskinen:**
   ```
   curl.exe -s "https://grep-fuseki-v3.fly.dev/ds/query?query=ASK%7B%7D"
   ```
   Svaret skal inneholde `"boolean" : true`. I PowerShell må du skrive `curl.exe`, ikke `curl`.
5. **Sjekk at API-nøkkelen er satt:**
   ```
   python -c "import os;print(bool(os.environ.get('ANTHROPIC_API_KEY')))"
   ```
   Det skal stå `True`. Pakkene ligger i den vanlige Python-installasjonen, så du trenger ingen venv.
6. **Gjør klar nettleseren:** Åpne sparql.mjolne.com, logg inn og velg endepunktet **Sandkassen**. De fire fanene skal ligge klare.
7. **Øv på Teams:** Start et møte med bare deg selv (**Møt nå**) og del skjermen.

## Punkt 1: Problemet (bare snakk)

Du trenger ikke vise noe her. Følg manuset.

## Punkt 2: Læreplanutsnittet (nettleseren)

1. Gå til fanen **«CONSTRUCT: LP-utsnitt MAT0015»** og trykk **Kjør**.
2. Bla i Turtle-teksten. Vis læreplanen, kompetansemålene, verbene med Udirs forklaring og `bygger-paa`.

## Punkt 3: Fra utsnitt til prompt (VS Code)

### a) Vis prompten for elev A (matematikk 10. trinn)

1. Klikk i terminalen og kjør:
   ```
   python lag_prompt.py --vurdering eksempler/mat0015-elev-a.json --lagre demo/mat0015-elev-a.prompt.txt
   ```
   Etter noen sekunder skal det stå `Skrev demo/mat0015-elev-a.prompt.txt`.
2. Åpne fila. Du kan Ctrl+klikke på filnavnet i terminalen, eller åpne mappa `demo` i filutforskeren til venstre.
3. Vis de tre delene. Bruk Ctrl+F for å hoppe mellom dem:
   - `=== SYSTEM ===` øverst: rollen og reglene modellen skal følge.
   - `<laereplanutsnitt>`: utsnittet, gjort om til Markdown.
   - `<vurderingsdata>` nederst: elevens vurderinger, der hver vurdering viser til kompetansemål med kode.
4. Du kan også åpne `eksempler/mat0015-elev-a.json`. Den viser hvordan vurderingsdataene ser ut før de settes inn i prompten.

### b) Send prompten til modellen

1. Gå tilbake til terminalen og kjør:
   ```
   python lag_prompt.py --vurdering eksempler/mat0015-elev-a.json --kall
   ```
2. Svaret strømmer fram i terminalen i rundt ett minutt. Snakk mens det kommer, slik manuset foreslår. Nederst står antall tokens og kostnaden.
3. Vil du vise et pent formatert svar, åpner du `demo/mat0015-elev-a.svar.md` og trykker Ctrl+Shift+V for forhåndsvisning. Det er et lagret svar fra en tidligere kjøring.
4. **Svikter nett eller API**, viser du det lagrede svaret i stedet.

### c) Datoen betyr noe

```
python lag_prompt.py --vurdering eksempler/mat0015-elev-a.json --dato 2025-03-01
```

Vis advarselen øverst i utskriften. Den sier at læreplanen nå er MAT01-05, og at ingen av elevens mål finnes i utsnittet. Resten av prompten trenger du ikke vise.

### d) Studieforberedende: elev C i 1T (Vg1)

```
python lag_prompt.py --vurdering eksempler/mat1021-elev-c.json --kall
```

Pek på forslagene under «Neste steg» som viser til KM224, KM228, KM229 eller KM231. Det er 10.-trinnsmål i den gamle læreplanen MAT01-05. Det er dette som er avviket om `bygger-paa`.

### Valgfritt: billigere modell

```
python lag_prompt.py --vurdering eksempler/mat1021-elev-c.json --kall --modell sonnet
```

Sonnet gir nesten like gode svar til under halv pris. Kostnaden står nederst i utskriften. Se [kostnad.md](kostnad.md).

## Punkt 4: Fritekstsøk (nettleseren)

Kjør fanene **«Fritekst-søk: statistikk»** og **«Fritekst kildekritikk»**. Sjekk at endepunktet er **Sandkassen**. På Prod finnes ikke `text:`.

## Punkt 5: ESCO (nettleseren)

Kjør fanen **«ESCO-ferdigheter koblet til KM8644»**. Den gir 8 ferdigheter og kunnskaper med norske navn.

## Punkt 6 og 7: Begrensninger og videre (bare snakk)

Følg manuset. Har Johan spørsmål om pris, viser du [kostnad.md](kostnad.md).

## Praktiske tips

- **Del hele skjermen** i Teams, ikke bare ett vindu. Da kan du bytte mellom VS Code og nettleseren med Alt+Tab uten å dele på nytt.
- **Pil opp** i terminalen henter forrige kommando.
- **Ta tiden** når du øver. Hele demoen er ment å ta rundt 30 minutter, og hvert `--kall` tar rundt ett minutt.
- **Reservefiler:** Mappa `demo/` har ferdige prompter og svar fra Opus, Sonnet og Haiku. Ingenting i demoen er avhengig av at nett eller API virker der og da, bortsett fra selve kallene.
