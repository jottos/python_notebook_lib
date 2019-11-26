# -*- coding: utf-8 -*-
'''
*** This file is deprecated in this package and has been moved to joslib.signal.utils ***

This package contains support functions for getting and handling signals that 
go into HCC events. 

## F2F & Dictionary Hits

The input schema from Madhu's proggram is 
  pat_uuid,doc_uuid,page_num,hcc_dict,f2f,f2f_value,improved_f2f,improved_f2f_value

To read in one of these files use read_signal_file()

'''
from collections import namedtuple
import csv

__version__ = "0.1.0"
__all__=['read_signal_file']

# coming soon.... __all__ = [a lot more stuff ]


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


## header for CSV outputs generated from JSON inputs
ref_header = ["pat_uuid", "doc_uuid", "sig_type", "source_val_type", 
              "source_location", "start_page", "end_page", "value", "wt"]
    
def create_signal_table_from_ref(signals, output_file_name):
    def write_row(signal):
        signal = Signal(signal)
        sig_writer.writerow(
            [signal.pat_uuid, signal.doc_uuid, signal.name, signal.source_type, 
             signal.source_value, signal.source_start_page, 
             signal.source_end_page, signal.value, signal.weight])

    with open(output_file_name, 'w') as sigout:
        sig_writer = csv.writer(sigout)
        sig_parser = parse('signals[*][*].name')
        sig_list = [match for match in sig_parser.find(signals)]
        sig_writer.writerow(ref_header)
        [write_row(c) for c in [m.context.value for m in sig_list]]


def create_signal_table_from_smas(signals, output_file_name):
    def write_row(signal):
        signal = Signal(signal)
        sig_writer.writerow(
            [signal.pat_uuid, signal.doc_uuid, signal.name, signal.source_type, 
             signal.source_value, signal.source_start_page, 
             signal.source_end_page, signal.value, signal.weight])

    with open(output_file_name, 'w') as sigout:
        sig_writer = csv.writer(sigout)
        sig_parser = parse('[*].name')
        sig_list = [match for match in sig_parser.find(signals)]

        '''pat_id, doc_id, sig_type, source_val_type, source_location, value, wt'''
        sig_writer.writerow(ref_header)
        [write_row(c) for c in [m.context.value for m in sig_list]]

## jos check to see if this is in our library
def make_timestamp():
    from datetime import datetime
    d = datetime.utcnow()
    return f'{d.year}{d.month:02}{d.day:02}'

## set this to point at where your data are
working_directory = '/Users/jos/Downloads/SMAS-SIGS'
timestamp = make_timestamp()
def _make_filename(base, ext="", working_directory="", timestamp=None):
    timestamp = f"-{timestamp}" if timestamp else ""
    if ext == "":
        return os.path.join(working_directory, f"{base}{timestamp}")
    else:
        return os.path.join(working_directory, f"{base}{timestamp}.{ext}")

def make_filename(base, ext="", working_directory=working_directory, timestamp=timestamp):
    return _make_filename(base, ext, working_directory, timestamp)

    
def convert_json_signal_input_to_csv(reference_signals_file_name, smas_signals_file_name):
    with open(reference_signals_file_name) as ref, open(smas_signals_file_name) as smas:
        ref_sigs = json.load(ref)
        smas_sigs = json.load(smas)

    ref_csv_filename = make_filename("ref-sigs", "csv")
    smas_csv_filename = make_filename("smas-sigs", "csv")

    create_signal_table_from_ref(ref_sigs, ref_csv_filename)
    create_signal_table_from_smas(smas_sigs, smas_csv_filename)

    return ref_csv_filename, smas_csv_filename


def smas_json_to_csv(reference_signals_file_name, smas_signals_file_name):
    ''' this is NOT DONE yet, we need to accomodate both the line by line and the array'''
    with open(smas_signals_file_name) as smas:
        smas_sigs = json.load(smas)

    smas_csv_filename = make_filename("smas-sigs", "csv")
    create_signal_table_from_smas(smas_sigs, smas_csv_filename)

    return smas_csv_filename


def ref_json_to_csv(reference_signals_file_name, filename_generator=make_filename):
    with open(reference_signals_file_name) as ref:
        ref_sigs = json.load(ref)

    # lets reuse the name we were sent
    #basename = path.splitext(reference_signals_file_name)[0]
    def make_filename(ref_sigs):
        # use pat_uuid:doc_uuid-ref format filename
        for sig in ref_sigs['signals'][1]:
            try:
                source = sig['source'][1]
                doc = source['documentId']['uuid']
                pat = source['patientId']['uuid']
                return filename_generator(f"{pat}:{doc}-ref", "csv", timestamp=None)
            except:
                print(f"bad source: {source}")

    ref_csv_filename = make_filename(ref_sigs)
    print(f"doing file {ref_csv_filename}")
    create_signal_table_from_ref(ref_sigs, ref_csv_filename)


def ref_json_to_smas_json(reference_signals_file_name, filename_generator=make_filename):
    '''
    convert a Reference Signal dump to a SMAS signal dump which contains json signals 
    one per line
    '''
    def write_row(signal):
        '''
        write a json 'row' representation of the signal

        signal: a ref json subobject to be used to construct a Signal object
        '''
        signal = Signal(signal)
        print(json.dumps(signal.to_smas_json()), file=sigout)
                     
    #basename = path.splitext(reference_signals_file_name)[0]
    #ref_csv_filename = filename_generator(basename, "csv")
    smas_version_filename = '/Users/jos/Downloads/SMAS-SIGS/foopy.json'

    with open(reference_signals_file_name) as ref, open(smas_version_filename, 'w') as sigout:
        ref_sigs = json.load(ref)
        sig_parser = parse('signals[*][*].name')
        sig_list = [match for match in sig_parser.find(ref_sigs)]
        [write_row(c) for c in [m.context.value for m in sig_list]]


def diff_csv_files(ref_csv_filename, smas_csv_filename):
    Signal = collections.namedtuple("Signal", "pat_uuid doc_uuid sig_type source_val_type source_location start_page end_page value wt")
    smas_dupes_filename = make_filename("smas-duplicate-sigs", "csv")

    with open(smas_csv_filename) as sigfile, open(smas_dupes_filename, 'w') as dupfile:
        sig_reader = csv.DictReader(sigfile)
        sig_writer = csv.writer(dupfile)
        sig_writer.writerow(ref_header)
        smas_sigs = set()
        for s in sig_reader:
            signal = Signal(s['pat_uuid'], s['doc_uuid'],s['sig_type'], s['source_val_type'], s['source_location'], s['start_page'], s['end_page'], s['value'], s['wt'])
            if signal in smas_sigs:
                sig_writer.writerow(signal)
            else:
                smas_sigs.add(signal)

    with open(ref_csv_filename) as sigfile:
        sig_reader = csv.DictReader(sigfile)
        ref_sigs = set()
        for s in sig_reader:
            ref_sigs.add(Signal(s['pat_uuid'], s['doc_uuid'],s['sig_type'], s['source_val_type'], s['source_location'], s['start_page'], s['end_page'], s['value'], s['wt']))

    print(f"number of unique smas-sigs = {len(smas_sigs)}\nnumber of unique ref-sigs = {len(ref_sigs)}")
    print(f"intersection size = {len(smas_sigs & ref_sigs)}")

    extra_smas_sigs = smas_sigs - ref_sigs
    missing_smas_sigs = ref_sigs - smas_sigs

    print(f"SMAS has {len(extra_smas_sigs)} extra and {len(missing_smas_sigs)} missing sigs")

    smas_extra_filename = make_filename("smas-extra-sigs", "csv")
    smas_missing_filename = make_filename("smas-missing_sigs", "csv")

    with open(smas_extra_filename, 'w') as sigfile:
        sig_writer = csv.writer(sigfile)
        sig_writer.writerow(ref_header)
        for s in extra_smas_sigs:
            sig_writer.writerow(s)

    with open(smas_missing_filename, 'w') as sigfile:
        sig_writer = csv.writer(sigfile)
        sig_writer.writerow(ref_header)
        for s in missing_smas_sigs:
            sig_writer.writerow(s)        
            

## this is the driver program
##   convert json to csv
##   
def compare_smas_and_reference_signals(reference_signals_file_name, smas_signals_file_name):
    ref_csv_filename, smas_csv_filename = convert_json_signal_input_to_csv(reference_signals_file_name,
                                                                           smas_signals_file_name)
    smas_df = pd.read_csv(smas_csv_filename)
    ref_df = pd.read_csv(ref_csv_filename)
    print('SMAS results')
    print(smas_df[['source_val_type', 'sig_type']].groupby(['source_val_type']).describe())
    print('REF results')
    print(ref_df[['source_val_type', 'sig_type']].groupby(['source_val_type']).describe())

    diff_csv_files(ref_csv_filename, smas_csv_filename)
    
    