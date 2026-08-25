#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re

EXPECTED_CORRECTIONS = 41


def patch_spell_builder(text: str):
    marker = 'window.GM_DATA = '
    start = text.index(marker) + len(marker)
    data, end_rel = json.JSONDecoder().raw_decode(text[start:])
    end = start + end_rel
    rows = data.get('Deities', [])
    changes = []

    for row in rows:
        polarity = str(row.get('Polarity') or row.get('Energy') or '').strip().lower()
        desired = None
        if re.search(r'\b(?:both|dual|all)\b', polarity):
            desired = 'Both'
        elif 'feminine' in polarity or 'female' in polarity:
            desired = 'Goddess'
        elif 'masculine' in polarity or 'male' in polarity:
            desired = 'God'
        if desired and row.get('Deity Gender') != desired:
            changes.append({
                'name': row.get('Name') or row.get('Name/Entity'),
                'from': row.get('Deity Gender'),
                'to': desired,
                'polarity': row.get('Polarity'),
                'energy': row.get('Energy'),
            })
            row['Deity Gender'] = desired

    if len(changes) != EXPECTED_CORRECTIONS:
        raise SystemExit(f'Expected {EXPECTED_CORRECTIONS} Deity Gender corrections, found {len(changes)}')

    text = text[:start] + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + text[end:]

    # Retire earlier deity visibility owners instead of stacking another competing filter.
    p55 = re.compile(r"  function filterDeityCards\(\)\{.*?\n  \}\n\n  /\* 4\. Spell herbs", re.S)
    m = p55.search(text)
    if not m:
        raise SystemExit('V55 deity filter block not found')
    text = text[:m.start()] + "  function filterDeityCards(){/* retired: V75 single deity owner */}\n\n  /* 4. Spell herbs" + text[m.end():]

    p67 = re.compile(r"  function filterDeities\(\)\{.*?\n  \}\n\n  var filterTimer=0;", re.S)
    m = p67.search(text)
    if not m:
        raise SystemExit('V67 deity filter block not found')
    text = text[:m.start()] + "  function filterDeities(){/* retired: V75 single deity owner */}\n\n  var filterTimer=0;" + text[m.end():]

    old = """  function gender(r){return norm([r&&r['Deity Gender'],r&&r.Polarity,r&&r.Energy,r&&r.Gender,r&&r.Type].join(' '));}\n  function dual(r){return /\\bdual\\b|\\bboth\\b|\\ball\\b|balance|god and goddess/.test(gender(r));}\n  function feminine(r){var g=gender(r);return dual(r)||/goddess|feminine|female/.test(g);}\n  function masculine(r){var g=gender(r);return !dual(r)&&(/masculine|male/.test(g)||(/\\bgod\\b/.test(g)&&!/goddess|feminine|female/.test(g)));}"""
    new = """  function polarity(r){return norm(first(r&&r.Polarity,r&&r.Energy));}\n  function dual(r){return /\\bdual\\b|\\bboth\\b|\\ball\\b/.test(polarity(r));}\n  function feminineOnly(r){var g=polarity(r);return !dual(r)&&/feminine|female/.test(g);}\n  function masculineOnly(r){var g=polarity(r);return !dual(r)&&/masculine|male/.test(g);}"""
    if text.count(old) != 1:
        raise SystemExit(f'V69 gender block count {text.count(old)}')
    text = text.replace(old, new, 1)

    old2 = """  function eligible(){\n    var s=state(), god=/15_god/.test(file()), dualChosen=s.goddess&&dual(s.goddess);\n    return data().filter(function(r){return god?(dualChosen?dual(r):masculine(r)):feminine(r);})\n      .map(function(r,i){return {r:r,i:i,sc:score(r)};})"""
    new2 = """  function eligible(){\n    var s=state(), god=/15_god/.test(file()), hasGoddess=!!(s.goddess&&name(s.goddess));\n    return data().filter(function(r){\n      if(god) return masculineOnly(r) || (!hasGoddess && dual(r));\n      return feminineOnly(r) || dual(r);\n    })\n      .map(function(r,i){return {r:r,i:i,sc:score(r)};})"""
    if text.count(old2) != 1:
        raise SystemExit(f'V69 eligible block count {text.count(old2)}')
    text = text.replace(old2, new2, 1)

    text = text.replace('<script id="gm-v69-final-deity-seven-card-owner">', '<script id="gm-v75-final-deity-seven-card-owner">', 1)
    text = text.replace('/* V69 FINAL DEITY OWNER', '/* V75 FINAL DEITY OWNER', 1)
    needle = '/* V75 FINAL DEITY OWNER\n'
    if needle not in text:
        raise SystemExit('V75 owner marker missing')
    text = text.replace(
        needle,
        needle + '   Gender source: Polarity/Energy only. Goddess = Feminine + Dual. God = Masculine + Dual only when no Goddess has been selected.\n',
        1,
    )

    return text, changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input_html')
    ap.add_argument('output_html')
    ap.add_argument('--report')
    args = ap.parse_args()

    src = Path(args.input_html)
    out = Path(args.output_html)
    patched, changes = patch_spell_builder(src.read_text(encoding='utf-8'))
    out.write_text(patched, encoding='utf-8')

    report = {
        'deities_total': 110,
        'deity_gender_records_corrected': len(changes),
        'changes': changes,
        'legacy_v55_filter_retired': True,
        'legacy_v67_filter_retired': True,
        'authoritative_owner': 'gm-v75-final-deity-seven-card-owner',
        'gender_source': 'Polarity/Energy',
        'goddess_rule': 'Feminine + Dual',
        'god_rule': 'Masculine + Dual only if no Goddess is selected; otherwise Masculine only',
    }
    if args.report:
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"OK corrected {len(changes)} deity gender records")


if __name__ == '__main__':
    main()
