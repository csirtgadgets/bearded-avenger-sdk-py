#!/usr/bin/env python

import logging
import os.path
import select
import textwrap
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

from cifsdk.constants import CONFIG_PATH, REMOTE_ADDR, TOKEN, SEARCH_LIMIT, FORMAT
from cifsdk.exceptions import AuthError
from csirtg_indicator.format import FORMATS
from cifsdk.utils import setup_logging, get_argument_parser, read_config
from csirtg_indicator import Indicator
from pprint import pprint

logger = logging.getLogger(__name__)


class Client(object):

    def __init__(self, remote, token, **kwargs):
        self.remote = remote
        self.token = str(token)

        self.fireball = False
        if kwargs.get('fireball'):
            self.fireball = kwargs['fireball']

    def _kv_to_indicator(self, kv):
        return Indicator(**kv)

    def ping(self):
        raise NotImplemented

    def search(self):
        raise NotImplemented

    def feed(self):
        raise NotImplemented


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
        example usage:
            $ cif -q example.org -d
            $ cif --search 1.2.3.0/24
            $ cif --ping
        '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='cif',
        parents=[p]
    )
    p.add_argument('--token', help='specify api token', default=TOKEN)
    p.add_argument('--remote', help='specify API remote [default %(default)s]', default=REMOTE_ADDR)
    p.add_argument('-p', '--ping', action="store_true") # meg?
    p.add_argument('-q', '--search', help="search")
    p.add_argument('--itype', help='filter by indicator type')  ## need to fix sqlite for non-ascii stuff first
    p.add_argument("--submit", action="store_true", help="submit an indicator")
    p.add_argument('--limit', help='limit results [default %(default)s]', default=SEARCH_LIMIT)
    p.add_argument('-n', '--nolog', help='do not log search', action='store_true')
    p.add_argument('-f', '--format', help='specify output format [default: %(default)s]"', default=FORMAT, choices=FORMATS.keys())

    p.add_argument('--indicator')
    p.add_argument('--tags', nargs='+')
    p.add_argument('--provider')
    p.add_argument('--confidence', help="specify confidence level")

    p.add_argument("--zmq", help="use zmq as a transport instead of http", action="store_true")

    p.add_argument('--config', help='specify config file [default %(default)s]', default=CONFIG_PATH)

    p.add_argument('--feed', action='store_true')

    p.add_argument('--no-verify-ssl', action='store_true')

    args = p.parse_args()

    setup_logging(args)
    logger = logging.getLogger(__name__)

    o = read_config(args)
    options = vars(args)
    for v in options:
        if v == 'remote' and options[v] == REMOTE_ADDR and o.get('remote'):
            options[v] = o['remote']
        if options[v] is None:
            options[v] = o.get(v)

    if not options.get('token'):
        raise RuntimeError('missing --token')

    verify_ssl = True
    if o.get('no_verify_ssl') or options.get('no_verify_ssl'):
        verify_ssl = False

    if options.get("zmq"):
        from cifsdk.client.zeromq import ZMQ as ZMQClient
        cli = ZMQClient(**options)
    else:
        from cifsdk.client.http import HTTP as HTTPClient
        cli = HTTPClient(args.remote, args.token, verify_ssl=verify_ssl)

    if options.get('ping'):
        logger.info('running ping')
        for num in range(0, 4):
            ret = cli.ping()
            if ret != 0:
                print("roundtrip: {} ms".format(ret))
                select.select([], [], [], 1)
            else:
                logger.error('ping failed')
                raise RuntimeError
    elif options.get('feed'):
        logger.info('searching for {}'.format(options['itype']))
        try:
            rv = cli.feed({
                'itype': options['itype'],
                'limit': options['limit'],
            })
        except AuthError as e:
            logger.error('unauthorized')
        except RuntimeError as e:
            import traceback
            traceback.print_exc()
            logger.error(e)
        else:
            print(FORMATS[options.get('format')](data=rv))

    elif options.get('itype'):
        logger.info('searching for {}'.format(options['itype']))
        try:
            rv = cli.search({
                'itype': options['itype'],
                'limit': options['limit'],
                'provider': options.get('provider'),
                'indicator': options.get('search')
            })
        except AuthError as e:
            logger.error('unauthorized')
        except RuntimeError as e:
            import traceback
            traceback.print_exc()
            logger.error(e)
        else:
            print(FORMATS[options.get('format')](data=rv))
    elif options.get('search'):
        logger.info("searching for {0}".format(options.get("search")))
        try:
            rv = cli.indicators_search({
                    'indicator': options['search'],
                    'limit': options['limit'],
                    'nolog': options['nolog']
                }
            )
        except RuntimeError as e:
            import traceback
            traceback.print_exc()
            logger.error(e)
        except AuthError as e:
            logger.error('unauthorized')
        else:
            print(FORMATS[options.get('format')](data=rv))
    elif options.get("submit"):
        logger.info("submitting {0}".format(options.get("submit")))
        i = Indicator(indicator=args.indicator, tags=args.tags, confidence=args.confidence)
        rv = cli.indicators_create(i)

        logger.info('success id: {}'.format(rv))

if __name__ == "__main__":
    main()