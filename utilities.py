import random
import logging

#CONFIG
random.seed(0x17)
logging.basicConfig(filename="app.log", filemode='w', level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')    

#Utilities
def log(arg, MESSAGE_TYPE):
    if (MESSAGE_TYPE == "DEBUG"):
        logging.debug(arg)
    elif (MESSAGE_TYPE == "ERROR"):
        logging.error(arg)
    elif (MESSAGE_TYPE == "INFO"):
        logging.info(arg)
    elif (MESSAGE_TYPE == "WARNING"):
        logging.warning(arg)
    else:
        logging.info(f'Unknown Message Type {MESSAGE_TYPE}')

