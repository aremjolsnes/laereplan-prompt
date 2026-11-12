"""Fra fagkode til AI-prompt: henter læreplanutsnittet fra Grep-sandkassen og bygger en prompt med vurderingsdata.

Kjeden:
  1. Kjør laereplanutsnitt.rq (fra grep-jena-fuseki) mot sandkassens SPARQL-endepunkt for fagkoden og datoen.
  2. Gjør grafen om til lesbar Markdown (eller behold Turtle med --format turtle).
  3. Sett utsnittet og vurderingsdataene inn i malene i maler/.
  4. Vis prompten (standard), eller send den til Claude med --kall.

Eksempler:
  python lag_prompt.py --vurdering eksempler/mat0015-elev-a.json
  python lag_prompt.py MAT0015 --dato 2025-03-01
  python lag_prompt.py --vurdering eksempler/mat0015-elev-a.json --kall
  python lag_prompt.py --vurdering eksempler/mat0015-elev-a.json --kall --modell sonnet

--kall krever ANTHROPIC_API_KEY. Vurderingsdataene i eksempler/ er oppdiktet.
"""

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import rdflib
from rdflib import RDF, Namespace

ROT = Path(__file__).resolve().parent
ENDEPUNKT = os.environ.get('GREP_SPARQL_URL', 'https://grep-fuseki-v3.fly.dev/ds/query')
RQ_URL = ('https://raw.githubusercontent.com/aremjolsnes/grep-jena-fuseki/main/'
          'docs/eksempler/laereplanutsnitt.rq')
# Modellene --modell kan velge. Pris i USD per million tokens (inn, ut), hentet 12.11.2026.
# reserve: om API-et skal prøve en annen modell hvis sikkerhetsfilteret avslår (finnes ikke for Haiku).
MODELLER = {
    'opus':   {'id': 'claude-opus-5-5',   'inn': 4.00, 'ut': 20.00, 'reserve': True},
    'sonnet': {'id': 'claude-sonnet-5-5', 'inn': 2.00, 'ut': 10.00, 'reserve': True},
    'haiku':  {'id': 'claude-haiku-5-5',  'inn': 0.10, 'ut': 0.50,  'reserve': False},
}

U = Namespace('http://psi.udir.no/ontologi/kl06/')

GF = [('grunnleggende-ferdigheter-muntlig', 'Muntlige ferdigheter'),
      ('grunnleggende-ferdigheter-skrive', 'Å kunne skrive'),
      ('grunnleggende-ferdigheter-lese', 'Å kunne lese'),
      ('grunnleggende-ferdigheter-regne', 'Å kunne regne'),
      ('grunnleggende-ferdigheter-digitale', 'Digitale ferdigheter')]
TT = [('tverrfaglige-temaer-folkehelse-og-livsmestring', 'Folkehelse og livsmestring'),
      ('tverrfaglige-temaer-demokrati-og-medborgerskap', 'Demokrati og medborgerskap'),
      ('tverrfaglige-temaer-baerekraftig-utvikling', 'Bærekraftig utvikling')]


def meld(*tekst):
    print(*tekst, file=sys.stderr, flush=True)


# --- 1. Hent utsnittet ---------------------------------------------------------------------------

def les_rq(kilde):
    if re.match(r'https?://', kilde):
        with urllib.request.urlopen(kilde, timeout=30) as svar:
            return svar.read().decode('utf-8')
    return Path(kilde).read_text(encoding='utf-8')


def sett_parametre(rq, fagkode, dato):
    verdi = '"%s"^^xsd:date' % dato if dato else 'UNDEF'
    ny, antall = re.subn(r'VALUES \(\?fk \?datoInn\) \{ \(d:\w+ [^)]*\) \}',
                         'VALUES (?fk ?datoInn) { (d:%s %s) }' % (fagkode, verdi), rq)
    if antall != 1:
        sys.exit('Fant ikke VALUES-linjen i spørringen. Har laereplanutsnitt.rq endret form?')
    return ny


def hent_utsnitt(rq):
    data = urllib.parse.urlencode({'query': rq}).encode('utf-8')
    foresp = urllib.request.Request(ENDEPUNKT, data=data, headers={
        'Accept': 'text/turtle', 'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'laereplan-prompt'})
    start = time.time()
    with urllib.request.urlopen(foresp, timeout=150) as svar:
        turtle = svar.read().decode('utf-8')
    meld('Utsnitt hentet på %.1f s (%d kB Turtle)' % (time.time() - start, len(turtle) // 1024))
    return turtle


# --- 2. Graf → Markdown --------------------------------------------------------------------------

def tekst(html_tekst):
    """Grep-tekstene er HTML. Gjør dem om til ren tekst med punktlister."""
    if html_tekst is None:
        return ''
    t = str(html_tekst)
    t = re.sub(r'<li[^>]*>', '\n- ', t)
    t = re.sub(r'</p>|<br\s*/?>|</ul>|</ol>', '\n', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = html.unescape(t)
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r'\n\s*\n+', '\n\n', t)
    return '\n'.join(linje.strip() for linje in t.strip().splitlines())


def tittel(g, ressurs):
    return str(g.value(ressurs, U.tittel) or g.value(ressurs, U.kode) or ressurs)


def etter_kode(g, ressurser):
    return sorted(set(ressurser), key=lambda r: str(g.value(r, U.kode)))


def til_markdown(g):
    fk = g.value(predicate=RDF.type, object=U.fagkode, any=False)
    lp = g.value(predicate=RDF.type, object=U.laereplan, any=False)
    kms = g.value(predicate=RDF.type, object=U.kompetansemaalsett, any=False)
    if not (fk and lp and kms):
        sys.exit('Utsnittet er tomt. Fagkoden har ingen LK20-læreplan på datoen '
                 '(gjelder f.eks. privatskolekoder og UPF), eller koden er feil.')

    mål = sorted(g.objects(kms, U.kompetansemaal),
                 key=lambda m: int(g.value(m, U.rekkefoelge) or 0))
    ut = []
    s = ut.append

    s('# Læreplanutsnitt: %s (%s)' % (tittel(g, fk), g.value(fk, U.kode)))
    s('')
    s('- Læreplan: %s (%s), gyldig fra %s' % (tittel(g, lp), g.value(lp, U.kode),
                                              str(g.value(lp, U['gyldig-fra']) or 'ukjent')[:10]))
    s('- Kompetansemålsett: %s (%s)' % (tittel(g, kms), g.value(kms, U.kode)))
    s('- Kilde: Grep (Utdanningsdirektoratet), via Grep-sandkassen')

    if g.value(lp, U['fagets-relevans']):
        s('\n## Fagets relevans og sentrale verdier\n')
        s(tekst(g.value(lp, U['fagets-relevans'])))

    s('\n## Kjerneelementer\n')
    for ke in etter_kode(g, g.objects(lp, U.kjerneelementer)):
        s('### %s (%s)\n' % (tittel(g, ke), g.value(ke, U.kode)))
        s(tekst(g.value(ke, U.beskrivelse)) + '\n')

    for overskrift, liste in (('Grunnleggende ferdigheter i faget', GF),
                              ('Tverrfaglige temaer i faget', TT)):
        deler = [(navn, g.value(lp, U[egenskap])) for egenskap, navn in liste]
        deler = [(navn, t) for navn, t in deler if t]
        if deler:
            s('\n## %s\n' % overskrift)
            for navn, t in deler:
                s('### %s\n' % navn)
                s(tekst(t) + '\n')

    s('\n## %s\n' % tittel(g, kms))
    s('Mål for opplæringen er at eleven skal kunne\n')
    verb_brukt = set()
    for m in mål:
        s('### %s: %s\n' % (g.value(m, U.kode), tittel(g, m)))
        ke = [tittel(g, k) for k in etter_kode(g, g.objects(m, U['tilknyttede-kjerneelementer']))]
        gf = [tittel(g, k) for k in etter_kode(g, g.objects(m, U['tilknyttede-grunnleggende-ferdigheter']))]
        tt = [tittel(g, k) for k in etter_kode(g, g.objects(m, U['tilknyttede-tverrfaglige-temaer']))]
        verb = etter_kode(g, g.objects(m, U['tilknyttede-verb']))
        verb_brukt.update(verb)
        if ke:
            s('- Kjerneelementer: ' + '; '.join(ke))
        if gf:
            s('- Grunnleggende ferdigheter: ' + '; '.join(gf))
        if tt:
            s('- Tverrfaglige temaer: ' + '; '.join(tt))
        if verb:
            s('- Verb: ' + ', '.join(tittel(g, v) for v in verb))
        forrige = etter_kode(g, g.objects(m, U['bygger-paa']))
        if forrige:
            s('- Bygger på mål fra tidligere trinn:')
            for f in forrige:
                s('  - %s: %s' % (g.value(f, U.kode), tittel(g, f)))
        if g.value(m, U.forklaring):
            s('- Forklaring av målet (didaktisk støtte fra Udir):\n')
            s('  ' + tekst(g.value(m, U.forklaring)).replace('\n', '\n  '))
        s('')

    if verb_brukt:
        s('\n## Verbene i kompetansemålene (Udirs forklaring)\n')
        for v in sorted(verb_brukt, key=lambda v: tittel(g, v)):
            beskr = tekst(g.value(v, U.beskrivelse))
            s('- **%s**: %s' % (tittel(g, v), beskr or '(ingen forklaring)'))

    s('\n## Vurdering\n')
    for overskrift, ressurs, egenskap in (
            ('Underveisvurdering', kms, 'underveisvurdering'),
            ('Standpunktvurdering', kms, 'standpunktvurdering'),
            ('Vurderingsordning: standpunkt', lp, 'vurderingsordning-standpunkt'),
            ('Vurderingsordning: eksamen for elever', lp, 'vurderingsordning-eksamen-elev'),
            ('Vurderingsordning: sluttvurdering', lp, 'vurderingsordning-sluttvurdering')):
        if g.value(ressurs, U[egenskap]):
            s('### %s\n' % overskrift)
            s(tekst(g.value(ressurs, U[egenskap])) + '\n')

    return '\n'.join(ut).strip() + '\n', {str(g.value(m, U.kode)) for m in mål}


# --- 3. Bygg prompten ----------------------------------------------------------------------------

def bygg_prompt(utsnitt, vurdering):
    system = (ROT / 'maler' / 'system.md').read_text(encoding='utf-8').strip()
    mal = (ROT / 'maler' / 'oppgave.md').read_text(encoding='utf-8')
    vurd = json.dumps(vurdering, ensure_ascii=False, indent=2) if vurdering else '(ingen vurderingsdata)'
    bruker = mal.replace('{utsnitt}', utsnitt.strip()).replace('{vurdering}', vurd).strip()
    return system, bruker


def sjekk_koder(vurdering, koder):
    brukt = set()
    for v in vurdering.get('vurderinger', []):
        brukt.update(v.get('kompetansemaal', []))
    ukjente = sorted(brukt - koder)
    if ukjente:
        meld('ADVARSEL: vurderingsdataene viser til mål som ikke er i utsnittet: ' + ', '.join(ukjente))
        meld('          (feil fagkode eller dato, eller målene hører til en annen versjon av læreplanen)')
    uten = sorted(koder - brukt)
    meld('Vurderingsdataene dekker %d av %d kompetansemål.' % (len(koder) - len(uten), len(koder)))


# --- 4. Send til Claude --------------------------------------------------------------------------

def kall_claude(system, bruker, effort, modell):
    import anthropic
    m = MODELLER[modell]
    klient = anthropic.Anthropic()
    meld('Sender til %s (effort %s) ...\n' % (m['id'], effort))
    ekstra = {}
    if m['reserve']:
        # avslår sikkerhetsfilteret, prøver API-et en annen modell i samme kall
        ekstra = {'betas': ['server-side-fallback-2026-07-01'], 'fallbacks': 'default'}
    try:
        with klient.beta.messages.stream(
            model=m['id'],
            max_tokens=32000,
            output_config={'effort': effort},
            system=system,
            messages=[{'role': 'user', 'content': bruker}],
            **ekstra,
        ) as strøm:
            for bit in strøm.text_stream:
                print(bit, end='', flush=True)
            svar = strøm.get_final_message()
    except anthropic.AuthenticationError:
        sys.exit('\nAPI-nøkkelen ble avvist. Sjekk ANTHROPIC_API_KEY.')
    except anthropic.RateLimitError:
        sys.exit('\nFor mange forespørsler (429). Prøv igjen om litt.')
    except anthropic.APIConnectionError:
        sys.exit('\nFikk ikke kontakt med API-et. Sjekk nettet.')
    print()
    if svar.stop_reason == 'refusal':
        meld('Modellen avslo (%s).' % (svar.stop_details.category if svar.stop_details else '?'))
    elif svar.stop_reason == 'max_tokens':
        meld('Svaret ble kuttet (max_tokens).')
    u = svar.usage
    kost = (u.input_tokens * m['inn'] + u.output_tokens * m['ut']) / 1e6
    meld('\n%s: %d tokens inn, %d ut, ca. %.3f USD' % (svar.model, u.input_tokens, u.output_tokens, kost))


# --- Hovedprogram --------------------------------------------------------------------------------

def main():
    for strøm in (sys.stdout, sys.stderr):
        strøm.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(description='Fra fagkode til AI-prompt med læreplanutsnitt fra Grep.')
    ap.add_argument('fagkode', nargs='?', help='f.eks. MAT0015 (standard: fagkoden i vurderingsfila)')
    ap.add_argument('--vurdering', help='JSON-fil med (oppdiktede) vurderingsdata')
    ap.add_argument('--dato', help='datoen læreplanen skal gjelde på, ÅÅÅÅ-MM-DD '
                                   '(standard: vurderingsdato i fila, ellers i dag)')
    ap.add_argument('--format', choices=['markdown', 'turtle'], default='markdown',
                    help='hvordan utsnittet står i prompten')
    ap.add_argument('--rq', default=RQ_URL, help='sti eller URL til laereplanutsnitt.rq')
    ap.add_argument('--lagre', help='skriv prompten til denne fila i stedet for skjermen')
    ap.add_argument('--kall', action='store_true', help='send prompten til Claude og vis svaret')
    ap.add_argument('--effort', default='medium', choices=['low', 'medium', 'high', 'xhigh', 'max'])
    ap.add_argument('--modell', default='opus', choices=list(MODELLER),
                    help='hvilken Claude-modell --kall bruker (standard: opus)')
    a = ap.parse_args()

    vurdering = None
    if a.vurdering:
        vurdering = json.loads(Path(a.vurdering).read_text(encoding='utf-8'))
    fagkode = (a.fagkode or (vurdering or {}).get('fagkode') or '').upper()
    if not re.fullmatch(r'[A-ZÆØÅ0-9]+', fagkode):
        ap.error('oppgi en fagkode, f.eks. MAT0015, eller en vurderingsfil med "fagkode"')
    dato = a.dato or (vurdering or {}).get('vurderingsdato') or date.today().isoformat()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', dato):
        ap.error('datoen må ha formen ÅÅÅÅ-MM-DD')

    meld('Fagkode %s, dato %s, endepunkt %s' % (fagkode, dato, ENDEPUNKT))
    turtle = hent_utsnitt(sett_parametre(les_rq(a.rq), fagkode, dato))
    g = rdflib.Graph().parse(data=turtle, format='turtle')
    markdown, koder = til_markdown(g)
    utsnitt = markdown if a.format == 'markdown' else turtle
    if vurdering:
        sjekk_koder(vurdering, koder)

    system, bruker = bygg_prompt(utsnitt, vurdering)
    meld('Prompt: %d tegn (system %d, bruker %d)' % (len(system) + len(bruker), len(system), len(bruker)))

    if a.kall:
        kall_claude(system, bruker, a.effort, a.modell)
        return
    prompt = '=== SYSTEM ===\n\n%s\n\n=== BRUKER ===\n\n%s\n' % (system, bruker)
    if a.lagre:
        Path(a.lagre).write_text(prompt, encoding='utf-8')
        meld('Skrev ' + a.lagre)
    else:
        print(prompt)


if __name__ == '__main__':
    main()
