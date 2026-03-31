#!/usr/bin/env python3
"""
Patches your font into SFUI.ttf so that it works well on iOS. 
by roooot

python3 tools/fontpatch.py --template /path/to/SFUI.ttf --source /path/to/yourfont.ttf --out ./yourfont_patched.ttf
"""

import argparse
import copy
import sys

from fontTools.ttLib import TTFont, newTable


def collectbasenamerecords(base):
    nameidsneeded = set()
    if 'fvar' in base:
        for a in base['fvar'].axes:
            nameidsneeded.add(a.axisNameID)
        for inst in base['fvar'].instances:
            nameidsneeded.add(inst.subfamilyNameID)
            if inst.postscriptNameID != 0xFFFF:
                nameidsneeded.add(inst.postscriptNameID)
    if 'STAT' in base:
        stat = base['STAT'].table
        try:
            for axis in stat.DesignAxisRecord.Axis:
                nameidsneeded.add(axis.AxisNameID)
        except Exception:
            pass
        try:
            for av in stat.AxisValueArray.AxisValue:
                nameidsneeded.add(av.ValueNameID)
        except Exception:
            pass

    basenamerecords = {}
    if 'name' in base:
        for nr in base['name'].names:
            if nr.nameID in nameidsneeded:
                key = (nr.platformID, nr.platEncID, nr.langID, nr.nameID)
                basenamerecords[key] = nr
    return basenamerecords


def mergenametable(dst_name, base_records):
    existing = set((nr.platformID, nr.platEncID, nr.langID, nr.nameID) for nr in dst_name.names)
    for key, nr in base_records.items():
        if key not in existing:
            dst_name.names.append(copy.copy(nr))


def buldzerogvar(font):
    gvar = newTable('gvar')
    gvar.version = 1
    if 'fvar' in font:
        gvar.axisCount = len(font['fvar'].axes)
    else:
        gvar.axisCount = 0
    gvar.sharedTuples = []
    gvar.variations = {g: [] for g in font.getGlyphOrder()}
    return gvar


def fontpatch(sfuipath, sourcepath, out_path):
    base = TTFont(sfuipath)
    src = TTFont(sourcepath)
    if 'glyf' not in src:
        raise RuntimeError('source font has no glyf table (likely CFF/OTF).')

    basenamerecords = collectbasenamerecords(base)

    dst = TTFont(sfuipath)
    dst.setGlyphOrder(src.getGlyphOrder())

    for t in ['glyf','loca','hmtx','maxp','head','hhea','OS/2','post','cmap','prep','fpgm','cvt ','gasp','VDMX','LTSH','hdmx']:
        if t in src:
            dst[t] = copy.deepcopy(src[t])

    for t in ['GPOS', 'GSUB', 'GDEF']:
        if t in src:
            dst[t] = copy.deepcopy(src[t])
        elif t in dst:
            del dst[t]

    if 'name' in src:
        dst['name'] = copy.deepcopy(src['name'])
        mergenametable(dst['name'], basenamerecords)

    for t in ['HVAR', 'MVAR', 'VVAR']:
        if t in dst:
            del dst[t]

    if 'gvar' in dst:
        del dst['gvar']
    dst['gvar'] = buldzerogvar(dst)
    dst.save(out_path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--template', required=True, help='path to SFUI.ttf')
    ap.add_argument('--source', required=True, help='path to your font')
    ap.add_argument('--out', required=True, help='output TTF')
    args = ap.parse_args()

    try:
        fontpatch(args.template, args.source, args.out)
    except Exception as e:
        print(f'error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
