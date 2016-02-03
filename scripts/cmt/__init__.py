import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(name)s - %(levelname)s:  %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)
