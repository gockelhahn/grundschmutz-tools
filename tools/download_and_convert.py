#!/usr/bin/env python
# download BSI IT-Grundschutz-Kompendium and
# convert it into structural json based machine-readable data

import os
import re

from pkg_resources import parse_version

from lib.common import get_from_json, save_json
from lib.BSI import BSI

data_dir_2021 = os.path.join(os.path.curdir, '..', 'data', '2021')
j_anforderung = os.path.join(data_dir_2021, 'anforderung.json')
j_anf_gef = os.path.join(data_dir_2021, 'anforderung_gefaehrdung.json')
j_anforderungstyp = os.path.join(data_dir_2021, 'anforderungstyp.json')
j_baustein = os.path.join(data_dir_2021, 'baustein.json')
j_bausteinkat = os.path.join(data_dir_2021, 'bausteinkategorie.json')
j_gefaehrdung = os.path.join(data_dir_2021, 'gefaehrdung.json')
j_rolle = os.path.join(data_dir_2021, 'rolle.json')
j_schutzziel = os.path.join(data_dir_2021, 'schutzziel.json')


def get_or_create(jsonfile: str,
                  jsonlist: list,
                  by: str,
                  all_elems: dict) -> int:
    try:
        thisid = get_from_json(jsonfile, by, all_elems[by])
    except ValueError:
        thisid = len(jsonlist)
        obj = {'id': thisid}
        obj.update(all_elems)
        jsonlist.append(obj)
        save_json(jsonfile, jsonlist)

    return thisid


def main() -> None:
    bsi = BSI()
    # download and convert
    bsi.setup()

    # get Bausteine and Anforderungen
    bsielements = bsi.get_bausteine_with_anforderungen()

    # define lists
    d_anforderung = []
    d_anf_gef = []
    d_baustein = []
    d_bausteinkat = []
    d_gefaehrdung = []
    d_rolle = []

    # save empty json files
    save_json(j_anforderung, d_anforderung)
    save_json(j_anf_gef, d_anf_gef)
    save_json(j_baustein, d_baustein)
    save_json(j_bausteinkat, d_bausteinkat)
    save_json(j_gefaehrdung, d_gefaehrdung)
    save_json(j_rolle, d_rolle)

    # TODO: get all Bausteinkategorien with labels

    # loop through Bausteinkategorien (like APP/CON/...)
    for kat in sorted(bsielements):
        kat_data = {'name': kat, 'label': kat}
        kat_id = get_or_create(j_bausteinkat, d_bausteinkat, 'name', kat_data)
        for bauv in sorted(parse_version(x) for x in bsielements[kat]):
            rolle_data = {'name': bsielements[kat][str(bauv)]['rolle']}
            bau_rolle_id = get_or_create(j_rolle, d_rolle, 'name', rolle_data)
            baustein_data = {
                    'id': len(d_baustein),
                    'name': bsielements[kat][str(bauv)]['name'],
                    'label': bsielements[kat][str(bauv)]['label'],
                    'bausteinkategorie': kat_id,
                    'rolle': bau_rolle_id
            }
            baustein_id = get_or_create(
                j_baustein, d_baustein, 'name', baustein_data)

            for anfv in sorted(parse_version(x) for x in
                               bsielements[kat][str(bauv)]['anforderungen']):
                anf_label = bsielements[kat][str(bauv)][
                    'anforderungen'][str(anfv)]['label']
                # examine label + type + reponsible (role)
                found = re.search(r'(.*)[\s]\((.*)\)', anf_label)
                if found:
                    anf_real_label = found.groups()[0]
                    anf_typ = found.groups()[1]
                else:
                    raise ValueError(
                        'Anforderungstyp missing: {}'.format(anf_label))

                if 'B' in anf_typ.upper():
                    anf_typ = 'Basis'
                if 'S' in anf_typ.upper():
                    anf_typ = 'Standard'
                if 'H' in anf_typ.upper():
                    anf_typ = 'Hoch'

                # set Bausteinverantwortlichen in Anforderung by default
                anf_rollen_ids = [bau_rolle_id]

                # search again for responsibility
                ff = re.search(r'.*\[(.*)]', anf_real_label)
                if ff:
                    anf_real_label = anf_real_label.split(' [')[0]
                    anf_rollen = ff.groups()[0]
                    # reset rollen
                    anf_rollen_ids = []
                    # negative lookahead, split on ',' but not inside brackets
                    for entry in re.split(r',(?![^(]*\))', anf_rollen):
                        rolle_data = {'name': entry.strip()}
                        rolle_id = get_or_create(
                            j_rolle, d_rolle, 'name', rolle_data)
                        anf_rollen_ids.append(rolle_id)

                d_anforderung.append({
                    'id': len(d_anforderung),
                    'name': bsielements[kat][str(bauv)][
                        'anforderungen'][str(anfv)]['name'],
                    'label': anf_real_label,
                    'anforderungstyp':
                        get_from_json(j_anforderungstyp, 'name', anf_typ),
                    'baustein': baustein_id,
                    'rollen': anf_rollen_ids
                })

    # we dont need the id before, so only save it once!
    save_json(j_anforderung, d_anforderung)

    # TODO: get all Gefährdungen

    # loop again over all Anforderungen and get a list of Gefährdungen
    for anf in d_anforderung:
        gef_per_anf = bsi.get_gefaehrdungen_by_anforderung(anf['name'])
        for g in gef_per_anf:
            g_data = {'name': g}
            g_id = get_or_create(j_gefaehrdung, d_gefaehrdung, 'name', g_data)
            s_ids = []
            for schutzziel in gef_per_anf[g]:
                schutzziel_id = get_from_json(j_schutzziel, 'name', schutzziel)
                s_ids.append(schutzziel_id)
            d_anf_gef.append({
                'anforderung': anf['id'],
                'gefaehrdung': g_id,
                'schutzziele': s_ids
            })

    save_json(j_anf_gef, d_anf_gef)


if __name__ == '__main__':
    main()
