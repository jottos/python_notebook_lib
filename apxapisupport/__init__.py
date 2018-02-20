# -*- coding: utf-8 -*-
__version__ = "0.1.0"
__all__ = ['login_apxapi', 'get_apo', 'download_archived_document', 'download_pdf_doc', 'set_default_base_directory', 'get_default_base_directory']

import apxapi
from apxapi import APXAuthException
import os

def set_prod_data_orchestrator(do_host_and_port):
    apxapi.ENVMAP[apxapi.PRD]['dataorchestrator'] = do_host_and_port


def login_apxapi(username=None):
    if not username:
        userusername = input('Username: ')
    try:
        apx_session = apxapi.APXSession(username,environment=apxapi.PRD)
        print("login good: {}".format(apx_session.internal_token()))
        return apx_session
    except APXAuthException as ae:
        print(ae)
        return None
    except Exception as e:
        print("unknown kaboom: {}".format(e))
        return None


def get_apo(d_uuid):
    try:
        return apx_session.dataorchestrator.patient_object_by_doc(d_uuid).json()
    except:
        return {}


_base_dir = "/Users/jos/Downloads/"

def set_default_base_directory(base_dir):
    global _base_dir
    if os.path.isdir(base_dir):
        _base_dir = base_dir


def get_default_base_directory():
    return _base_dir


def _write_file(file_name, file_content):
    if _base_dir not in file_name:
        file_name = base_dir + file_name
    # make sure directory path exists
    file_dir = os.path.dirname(file_name)
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    # write the file
    f = open(file_name, 'wb')
    f.write(file_content)
    f.close()

    
def download_archived_document(session, document_uuid, output_file_name=None, base_dir=_base_dir, org_id=None):
    # org=None to use link table
    if org_id is None:
        org_id = session.dataorchestrator.document_org_id(document_uuid).text
    
    if not output_file_name:
        output_file_name = "{}_{}.arcfile".format(document_uuid, org_id)

    filepath = os.path.join(base_dir, output_file_name)
    print("Fetching into {}".format(filepath))

    r = session.dataorchestrator.get_archive_document(org_id, document_uuid)
    if r.status_code == 200:
        print("got file writing now")
        _write_file(filepath, r.content)
    else:
        print("Fetch failed, got {}".format(r.status_code))

def download_pdf_doc(s, docuuid, org=None, base_dir=_base_dir):
    # org=None to use link table
    if org is None:
        org = s.dataorchestrator.document_org_id(docuuid).text
    
    filepath = os.path.join(base_dir,"{}_{}.pdf".format(org, docuuid))
    print("Fetching into {}".format(filepath))

    r = s.dataorchestrator.file(docuuid)
    if r.status_code == 200:
        print("got file writing now")
        _write_file(filepath, r.content)
    else:
        print("Fetch failed, got {}".format(r.status_code))


