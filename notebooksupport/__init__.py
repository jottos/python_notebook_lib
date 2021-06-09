# -*- coding: utf-8 -*-
from typing import List, Set, Dict, Tuple, Optional, ClassVar

__version__ = "0.1.0"
__all__ = ['NoteBookLogging']


## debugging shim
#from importlib import reload
#try:
#    logging.shutdown()
#    reload(logging)
#except Exception as e:
#    print(f"shutdown fail {type(e)}, {e}")

import sys
import logging
from logging import Logger


class NoteBookLogging(logging.Logger):
    """
    TODO - handler management
         - stream managment
         - setting of levels for default handler
    """
    def __init__(self, level=logging.DEBUG) -> Logger:
        """
        1. I am a fan of logging to the stderr in a notebook so one can differentiate the logs from print statements
        """
        # TODO - add force=True when we get to 3.8
        logging.basicConfig(level=level, stream=sys.stderr)
        # fetch the root loggers console handler we just configured
        self.console_handler = logging.getLogger().handlers[0]

    def getLogger(self, name:str, filename:Optional[str]=None, noconsole:bool=False, level:Optional[int]=None) -> Logger:
        """
        1. i'm (jos) a fan of loggers not proppogating to root logger so we have noconsole option
        2. we will inherit the logging level from the config, unless otherwise directed
        3. we will inherit the formatter from the basic config unless otherwise directed
        4. we will log to the stderr

        TODO: I have not tested what will happen if you acquire the same logger with different parameters
              If you pass no optional params, it shoud return exactly the same logger (the intention of this class)
              but I think the propogate param would break :(
            
        TODO: ability to set a formatter might be nice
        
        NOTE: Also, we don't have a rotating filehandler as we don't expect big logs in a notebook
              
        NOTE: Note that we also have a responsibility pattern here that the root logger is not going to do all the 
              work for you. if you need a particular handler, then we need to have it called out in this method as ]
              an option
        """
        logger = logging.getLogger(name)

        # create file handler if requested
        if filename:
            fh = logging.FileHandler(filename)
            logger.addHandler(fh)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)

            if level:
                logger.level = level
        else:
            pass
            # notthing really to do since the basicConfig takes care of us

        if noconsole:
            # these things in this order...
            logger.removeHandler(self.console_handler)
            logger.propagate = False

        return logger

"""
Some Logging tests

logger = None
nb_logging = NoteBookLogging()
logger1 = nb_logging.getLogger("foologger", level=logging.ERROR)
logger2 = nb_logging.getLogger("event", filename="/Users/jos/Downloads/loggertest.log", noconsole=True)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger2.handlers[0].setFormatter(formatter)

logger1.debug(f"this is logger 1 stream normal {datetime.utcnow()} ")
logger2.debug(f"this is logger 2 file normal {datetime.utcnow()}")
logger2.warning("hoping only to see this in the output file")
logger2.debug("hoping only to see this in the output file")
print(f"logger 1 and logger 2 {id(logger)}, {id(logger2)}")
print(logger1.handlers)
print(logger2.handlers)
"""
