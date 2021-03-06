# -*- coding: utf-8 -*-
from typing import List, Set, Dict, Tuple, Optional, ClassVar
import apxapi
from apxapi import APXAuthException
import os

__version__ = "0.1.0"
__all__ = ['login_apxapi', 'get_document_apo', 'get_document_pages_text',
           'download_archived_document', 'download_pdf_doc', 'set_default_download_directory',
           'get_default_download_directory']

def set_prod_data_orchestrator(do_host_and_port):
    apxapi.ENVMAP[apxapi.PRD]['dataorchestrator'] = do_host_and_port


def login_apxapi(username=None, password=None, environment=apxapi.PRD):
    if not username:
        userusername = input('Username: ')
    try:
        apx_session = apxapi.APXSession(username=username, password=password, environment=environment)
        print("login good: {}".format(apx_session.internal_token()))
        return apx_session
    except APXAuthException as ae:
        print(ae)
        return None
    except Exception as e:
        print("unknown kaboom: {}".format(e))
        return None


def get_document_apo(doc_uuid:str):
    """
    doc_uuid - document to pull APO for
    
    returns a json representation of a document

    NOTE: you are only using this to access and stage a PDF for use meaning you
          will be re-encrypting it, OR you are using it to diagnose an issue with
          the system and will be deleting the document right after
    """
    try:
        return apx_session.dataorchestrator.patient_object_by_doc(d_uuid).json()
    except:
        return {}

def get_document_pages_text(apx_session:apxapi.APXSession, doc_uuid:str, pages:List[int]=None, keep_line_breaks=True, include_raw_text:bool=False) -> List[Dict]:
    """usage: get_document_pages_text(session, doc_uuid)
    usage: get_document_pages_text(session, doc_uuid, [2, 5, 8]) 

    gets the clean text and HTML text from a set of pages in a document post OCR/ETL

    doc_uuid - document to get text from
    pages    - list of ints representing pages we want text from, no list 
      means all pages
    keep_line_breaks - if true, will preserve ocr_lines, otherwise \n will 
      be converted to space char
    inclue_raw_text - provide text w/ HTML markup (can be very verbose)

    currrently we only support the extracted_text type which is the text that
    the Tesseract OCR module delivers. there is an option here to ask for the
    raw version of the text which includes all the HTML markup from the HOCR
    that Tesseract produces (include_raw_text)

    returns an array of dictionaries, one per page requested with page_number,
    image_type, plain_text, and extracted_text
        
    TODO:
    plain_text - right now this is unused, in the past we used to extract the
      plain text from a PDF using various tools but we found them completely
      unreliable and when they failed they did so silently. I am keeping the
      support here because we keep thinking we'll reinvest in this...

    
    NOTE: Users! you are only using this to access and stage the text from a
          PDF for use; meaning you will be re-encrypting it, OR you are using
          it to diagnose an issue with the system and will be deleting the
          document right after if not only using the values in memory. don't
          print in a notebook and forget to clear all the cells, that saves the
          text in the ipynb file

    """
    from bs4 import BeautifulSoup
    import xml.etree.cElementTree as ET

    r = apx_session.dataorchestrator.patient_object_by_doc(doc_uuid)
    if not r.status_code == 200:
        print(f"Unable to fetch doc: {doc_uuid}, status_code: {r.status_code}")
        return
  
    j = r.json()
    document_text:List({}) = []
    xdoc = ET.fromstring(j['documents'][0]['stringContent'].encode('utf-8'))

    # NOTE: the classes in the xml library have a very funky deal going on, if you cast 
    # an instance to bool, it will return false, definitely forcing an explicit comparison
    for page in xdoc.iterfind('pages/page'):
        if page:
            pt = page.find('plainText')
            pn = page.find('pageNumber')
            et = page.find('extractedText/content')
            it = page.find('imgType')

            if pages and int(pn.text) not in pages:
                continue

            page_rec = {'page_number': pn.text, 'image_type': it.text, 'plain_text': None, 'extracted_text': None}

            # plainText is a key we added if we had extracted text from PDF if it contained text
            if pt is not None and pt.text:
                if include_raw_text:
                    page_rec['plain_text_w_markup'] = pt.text
                # assumption here is plain_text is in html form...
                soup = BeautifulSoup(pt.text, 'html.parser')
                spans = soup.find_all('span', class_='ocr_line')
                text_lines = [s.text.replace('\n', ' ') for s in spans]
                page_rec['plain_text'] = '\n'.join(text_lines) if keep_line_breaks else ' '.join(text_lines)

            if et is not None and et.text:
                if include_raw_text:
                    page_rec['extracted_text_w_markup'] = et.text
                soup = BeautifulSoup(et.text, 'html.parser')
                spans = soup.find_all('span', class_='ocr_line')
                text_lines = [s.text.replace('\n', ' ') for s in spans]
                page_rec['extracted_text'] = '\n'.join(text_lines) if keep_line_breaks else ' '.join(text_lines)

            document_text.append(page_rec)
            
    return document_text


_download_dir = "/Users/jschneider/Downloads/"

def set_default_download_directory(download_dir):
    global _download_dir
    if os.path.isdir(download_dir):
        _download_dir = download_dir


def get_default_download_directory():
    return _download_dir


def _write_file(file_name, file_content, download_dir):
    if _download_dir not in file_name:
        file_name = download_dir + file_name
    # make sure directory path exists
    file_dir = os.path.dirname(file_name)
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    # write the file
    f = open(file_name, 'wb')
    f.write(file_content)
    f.close()


def download_archived_document(session, doc_uuid, output_file_name=None, download_dir=_download_dir, org_id=None):
    """
    take a document UUID and download the associate PDF to the download_dir
    NOTE: you are only using this to access and stage a PDF for use meaning you
          will be re-encrypting it, OR you are using it to diagnose an issue with
          the system and will be deleting the document right after

    doc_uuid - the document you want. Regular UUID not XUUID 

    org=None no need to use this, we set None to let system deal with the look up

    download_dir - you need to provide this or set it using the set_default_download_directory()
             call

    NOTE: you are only using this to access and stage a PDF for use meaning you
          will be re-encrypting it, OR you are using it to diagnose an issue with
          the system and will be deleting the document right after
    """
    if org_id is None:
        org_id = session.dataorchestrator.document_org_id(doc_uuid).text

    if not output_file_name:
        output_file_name = "{}_{}.arcfile".format(doc_uuid, org_id)

    filepath = os.path.join(download_dir, output_file_name)
    print("Fetching into {}".format(filepath))

    r = session.dataorchestrator.get_archive_document(org_id, doc_uuid)
    if r.status_code == 200:
        print("got file writing now")
        _write_file(filepath, r.content, download_dir)
    else:
        print("Fetch failed, got {}".format(r.status_code))


def download_pdf_doc(s, doc_uuid:str, org=None, download_dir:str=_download_dir):
    """
    take a document UUID and download the associate PDF to the download_dir
    NOTE: you are only using this to access and stage a PDF for use meaning you
          will be re-encrypting it, OR you are using it to diagnose an issue with
          the system and will be deleting the document right after

    doc_uuid - the document you want. Regular UUID not XUUID 

    org=None no need to use this, we set None to let system deal with the look up

    download_dir - you need to provide this or set it using the set_default_download_directory()
             call

    NOTE: you are only using this to access and stage a PDF for use meaning you
          will be re-encrypting it, OR you are using it to diagnose an issue with
          the system and will be deleting the document right after
    """
    if org is None:
        org = s.dataorchestrator.document_org_id(doc_uuid).text
    
    filepath = os.path.join(download_dir,"{}_{}.pdf".format(org, doc_uuid))
    print("Fetching into {}".format(filepath))

    r = s.dataorchestrator.file(doc_uuid)
    if r.status_code == 200:
        print("got file writing now")
        _write_file(filepath, r.content, download_dir)
    else:
        print("Fetch failed, got {}".format(r.status_code))


