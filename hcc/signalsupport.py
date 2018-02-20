'''
This package contains support functions for getting and handling signals that 
go into HCC events. 

## F2F & Dictionary Hits

The input schema from Madhu's proggram is 
  pat_uuid,doc_uuid,page_num,hcc_dict,f2f,f2f_value,improved_f2f,improved_f2f_value

To read in one of these files use read_signal_file()

'''
from datetime import datetime
from collections import namedtuple
import csv

__all__=['read_signal_file']

fieldnames = ['pat_uuid','doc_uuid','page_num','hcc_dict','f2f','f2f_value','improved_f2f','improved_f2f_value']
# pat_uuid,doc_uuid,page_num,hcc_dict,f2f,f2f_value,improved_f2f,improved_f2f_value

def _parse_record(r, doc_signals):
    '''
    for f2f we will start with list of booleans, we could do tuples w/ pg_num,bool 
    but we can do that later if we want a more complex function to determine f2f or not
    i'm thinking that the majority of these are single page because that's what we do with
    EHR text notes. our other option is to use the real value probability and tune the ROC
    we'll go w/ boolean right now
    '''
    if r['improved_f2f'] != '':
        doc_signals.f2f.append(r['improved_f2f'] == 'true')
    elif r['hcc_dict'] != '':
        if r['hcc_dict'].startswith('V22'):
            doc_signals.dicthits.add(r['hcc_dict'])
        
def _is_f2f(doc_signals):
    # simple metric for now, if half or greater of the pages are f2f... just a swag
    # if this is zero, then f2fs will be zero, so we will set to 1 to avoide DBZ
    pg_count = max(len(doc_signals.f2f), 1) 
    # f2f_count = len(list(filter(lambda x: x, doc_signals.f2f)))
    # elegant but slow, so
    f2f_count = 0
    for pg_f2f in doc_signals.f2f:
        if pg_f2f:
            f2f_count += 1
    return f2f_count / pg_count >= .5 

# JOS why did the is_f2f cause a "str not callable" error
def read_signal_file(signal_filename, summary_filename=None, is_f2f=_is_f2f):
    '''
    parse a Madhu format signal file 
    @ signal_filename - input csv file
    @ summary_filename - output filename for F2F positive documents and the dicthits
    @ is_f2f - function that takes list of F2F signals and returns an agregate F2F
      judgement
    for each F2F document write out the doc_uuid and dict_hits
    return map of documents and their signals. if summary_filename is 
    supplied this function will write a csv file for all the F2F positive
    lines 
    '''
    # this version of doc signals object will not care about pages or windows
    DocSignals = namedtuple("DocSignals", "f2f dicthits")
    docs = {}
    with open(signal_filename) as sigs:
        reader = csv.DictReader(sigs, fieldnames=fieldnames)
        for r in reader:
            uuid = r['doc_uuid']
            if uuid not in docs:
                docs[uuid] = DocSignals([], set())
            _parse_record(r, docs[uuid])

    with open(summary_filename, 'w') as dsum:
        writer = csv.writer(dsum)
        for uuid, doc_signals in docs.items():
            if is_f2f(doc_signals):
                writer.writerow([uuid, '|'.join(doc_signals.dicthits)])

    return docs
