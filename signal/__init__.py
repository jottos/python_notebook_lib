# -*- coding: utf-8 -*-
'''
Signal class

models the Signal objects created by the reference algorithm and the SigGen job
Signals are the features passed into our later stage algorithms like ensembles 
and random forests. 

This class is available for both testing and development purposes
the companion subpackage "utils" contains a number of convenience functions
'''
__version__ = "0.1.0"
__all__ = ['Signal']


class Signal(object):
    '''
    this is where all the complexity lies
    the serialization between the two Signal formats is not harmonious
    and even within the *same* source the serialization is not consistent 
    for example the SMAS files will use both doc and documentId keys to access 
    information about the document :( 
    '''
    def __init__(self, signal, debug=False):
        try:
            # Ref provides a list for source
            if type(signal['source']) == list:
                self._source_name = signal['source'][0]
                self._source = signal['source'][1] 
                self._generator_name = signal['generator'][0]
                self._generator = signal['generator'][1]
                self._signal_source = 'ref'
            else:
                self._source = signal['source']
                self._generator = signal['generator']
                self._signal_source = 'smas'
                self._source_name = None
                self._generator_name = None

            # figure out all the source stuff
            if 'centroid' in self._source:
                self._source_type = 'PageWindowSource'
                self._source_key = 'centroid'
            elif 'pages' in self._source:
                self._source_type = 'DocumentSource'
                self._source_key = 'pages'            
            elif 'page' in self._source:
                self._source_type = 'PageSource'
                self._source_key = 'page' 
            elif 'patientId' in self._source or 'id' in self._source:
                self._source_type = 'PatientSource'
                self._source_key = 'patient' 
            else:
                print("bad source: {}".format(source))
                return 'UnkSource', 'UnkSourceType'
            
            # document_uuid is messy
            if 'doc' in self._source:
                _doc = self._source['doc']
                if 'uuid' in _doc:
                    self._doc_uuid = _doc['uuid'] 
                else:
                    self._doc_uuid = _doc['uuidString'] 
            elif 'documentId' in self._source:
                self._doc_uuid = self._source['documentId']['uuid']
            else:
                self._doc_uuid = 'NA'
                
            # patient_uuid is even messier
            # 'pat' and 'patientId' found in Ref and SMAS
            # 'id' found only in SMAS
            if 'pat' in self._source:
                _pat = self._source['pat']
                if 'uuid' in _pat:
                    self._pat_uuid = _pat['uuid']
                else:
                    self._pat_uuid = _pat['uuidString']
            elif 'id' in self._source:
                self._pat_uuid = self._source['id']['uuidString']
            elif 'patientId' in self._source:
                self._pat_uuid = self._source['patientId']['uuid']
            else:
                print(self._source)
                raise("have a patID we dont know about")
                
            self._source_val = self._source[self._source_key] if self._source_key in self._source else -1
            self._end_page = self._source['endPage'] if self._source_type == 'PageWindowSource' else -1
            self._start_page = self._source['startPage'] if self._source_type == 'PageWindowSource' else -1        
            self._name = signal['name']
            self._sig_type = signal['sigType']
            #self._value = signal['value'][1] if type(signal['value']) == list else signal['value']
            self._value = signal['value']
            self._weight = signal['wt']

            if debug:
                self._signal = signal
        except Exception as e:
            print("Exception initializing Signal: type={}, args={}".format(type(e), e.args))
            print("signal: {}".format(signal))
            traceback.print_exc()

    def to_smas_json(self):
        return {
            'name': self._name,
            'sigType': self._sig_type,
            'value': self._value,
            'source': [self._source_name, self._source],
            'generator': [self._generator_name, self._generator],
            'wt': self._weight
        }

    @property
    def pat_uuid(self):
        return self._pat_uuid

    @property
    def doc_uuid(self):
        return self._doc_uuid
        
    @property
    def source_type(self):
        return self._source_type
        
    @property
    def source_value(self):
        return self._source_val

    @property
    def source_name(self):
        return self._source_name

    @property
    def source_start_page(self):        
        return self._start_page
        
    @property
    def source_end_page(self):
        return self._end_page
    
    @property
    def generator_name(self):
        return self._generator_name
    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value

    @property
    def weight(self):
        return self._weight

    @property
    def source_object(self):
        return self._source

    @property
    def signal_object(self):
        return self._signal
