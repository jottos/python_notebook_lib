# -*- coding: utf-8 -*-
__version__ = "0.1.0"

__all__ = ['icd_2_hcc', 'icd_2_hcc_mapping', 'hierarchy_filter', 'ClaimsDB']

import os
from dateutil.parser import parse as date_parser
from collections import defaultdict

import apxapi
from apxapi.hoisting import Code
from apxapi.hoisting import ICD10
from apxapi.hoisting import ICD9

_mapping_file = "./code_mappings.txt"
_icd_10_date = date_parser("10/1/2015")


class ClaimsDB(object):
    '''
    ussage:
      cdb = ClaimsDB(acp2_claims_file_uuid, apx_session)

      for p in patient_list:
        print("{},{}\n".format(p, cdb.check_patient(p, clean=True))
    '''
    def __init__(self, claims_db_uuid, apx_session, claims_org=None):
        r = apx_session.dataorchestrator.get_archive_document(claims_org, claims_db_uuid)
        if r.status_code == 200:
            self.claims_db = r.json()
        else:
            self.claims_db = None
            
    def check_patient(self, patient_uuid, clean=False):
        stuff = self.claims_db.get(patient_uuid, [])
        if clean and stuff:
            stuff = [h[0]['c'] for h in stuff]
        return stuff



def icd_2_hcc(icd, dos=None, mapping=None, label_or_payment_year="2016-icd-hcc"):
    if mapping or dos:
        try:
            if not mapping:
                # mostly worried taht the date might be bad
                code_date = date_parser(dos)
                mapping = ICD9 if code_date < _icd_10_date else ICD10
            return Code(icd, mapping).toHcc(label_or_payment_year)
        except Exception as e:
            print("Exception {} occurred mapping icd->hcc: icd:{} dos:{} mapping:{}, label_or_payment:{}"
                  .format(e, icd, dos, mapping, label_or_payment_year))
            return []
    else:
        # make things go boom, dos or mapping required
        raise Exception("icd_2_hcc requires either DOS or a mapping")

icd_2_hcc_mapping = defaultdict(str)
def setup_mapping(mapping_file):
    # todo, convert this file to csv, but it works now...
    with open(mapping_file) as mf:
        for line in mf:
            (s, c, apxs, apxc) = line.strip().split("\t")
            icd_2_hcc_mapping[(s, c)] = apxc
            assert apxs == "APXCAT"


def hierarchy_filter(hcc_list):
    children_codes = []
    for hcc in hcc_list:
        children_codes += Code(hcc, 'HCCV22').children()
    
    children_codes = [c.code for c in children_codes]
    return set(hcc_list) - set(children_codes)



setup_mapping(os.path.join(os.path.dirname(__file__), _mapping_file))

