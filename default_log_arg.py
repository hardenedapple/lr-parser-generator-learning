import logging
import sys
import argparse

def do_default_logarg():
    parser = argparse.ArgumentParser()
    add_default_logarg(parser)

def add_default_logarg(parser):
    parser.add_argument('--loglevel', default='error',
                        choices=['notset', 'debug', 'info', 'warning', 'error',
                                'critical'])
    args = parser.parse_args()
    logging.basicConfig(stream=sys.stdout,
                        level=logging.__dict__[args.loglevel.upper()])
    return args
