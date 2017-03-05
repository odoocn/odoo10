import logging


def write_log(msg):
    logger = logging.getLogger('security_log')
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler('security_log.log')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    logger.info(msg)
    return True
