from enum import Enum
import random
import logging


class MessageType(Enum):
    DEBUG = 0,
    ERROR = 1,
    INFO = 2,
    WARNING = 3


#CONFIG
random.seed(0x17)
logging.basicConfig(filename="app.log", filemode='w', level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')    

#Utilities
def log(arg, MESSAGE_TYPE):
    if not isinstance(MESSAGE_TYPE, MessageType):
        logging.error("Message Type should be of type 'MessageType'")
        return
    
    if (MESSAGE_TYPE == MessageType.DEBUG):
        logging.debug(arg)
    elif (MESSAGE_TYPE == MessageType.ERROR):
        logging.error(arg)
    elif (MESSAGE_TYPE == MessageType.INFO):
        logging.info(arg)
    elif (MESSAGE_TYPE == MessageType.WARNING):
        logging.warning(arg)
    else:
        logging.info(f'Unknown Message Type {MESSAGE_TYPE}')

