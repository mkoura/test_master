#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=logging-format-interpolation
"""
Reads report.html and produces csv file with summary.
"""

from __future__ import unicode_literals, absolute_import

import argparse
import cStringIO
import codecs
import csv
import io
import logging
import operator
import os
import sys

from collections import Counter

import requests

from bs4 import BeautifulSoup

# requests package backwards compatibility mess
# pylint: disable=import-error,ungrouped-imports
from requests.packages.urllib3.exceptions import InsecureRequestWarning as IRWrequests
# pylint: disable=no-member
requests.packages.urllib3.disable_warnings(IRWrequests)
try:
    import urllib3
    from urllib3.exceptions import InsecureRequestWarning as IRWurllib3
    urllib3.disable_warnings(IRWurllib3)
except ImportError:
    pass


# pylint: disable=invalid-name
logger = logging.getLogger(__name__)


class UnicodeWriter(object):
    """A CSV writer that writes rows to CSV file "f" encoded in the given encoding"""

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        """writerow wrapper"""
        self.writer.writerow([s.encode('utf-8') for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode('utf-8')
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        """writerows implementation using unicode writerow"""
        for row in rows:
            self.writerow(row)


# pylint: disable=too-few-public-methods
class ErrStat(object):
    """Store for details about speciffic error type"""

    def __init__(self, body=None, count=1):
        self.bodies = []
        self.count = 0
        if body:
            self.update(body, count)

    def update(self, body, count):
        """Appends error body and increses count"""
        self.bodies.append((body, count))
        self.count += count

    def __repr__(self):
        return '<{}: {!r}>'.format(self.count, self.bodies)


def _get_args(args=None):
    """Get command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_file', required=True,
                        help="Input html with tracebacks")
    parser.add_argument('-o', '--output_file', required=True,
                        help="Output CSV file")
    parser.add_argument('--user',
                        help="Kerberos username")
    parser.add_argument('--password',
                        help="Kerberos password")
    return parser.parse_args(args)


def _get_report(location, user=None, password=None):
    """Reads report data from file or URL."""
    if 'http' in location:
        if not all((user, password)):
            logger.error("Missing credentials, cannot download")
            return
        report_file = 'report.html'
        if report_file not in location:
            location = '{0}/{1}'.format(location.rstrip('/'), report_file)
        try:
            report_data = requests.get(location, auth=(user, password), verify=False)
        # pylint: disable=broad-except
        except Exception as err:
            logger.error("Failed to download: {}".format(err))
            return
        return report_data.text

    location = os.path.expanduser(location)
    if os.path.isfile(location):
        with io.open(location, encoding='utf-8') as report_data:
            return report_data.read()


def _parse_html(html):
    return BeautifulSoup(html, 'lxml')


def _get_tracebacks(parsed_html):
    all_errors = Counter()
    for traceback in parsed_html.body.find_all('pre', attrs={'class': 'well'}):
        all_errors.update({traceback.text: 1})
    return all_errors


def _sort_errors(all_errors):
    error_types = {}
    error_variants = {}
    for full_err, err_count in all_errors.iteritems():
        full_err = full_err.strip()
        if '\n' in full_err:
            eindx = full_err.find('\n')
            err_name = full_err[:eindx]
            err_body = full_err[eindx:].strip()
            if err_name in error_variants:
                error_variants[err_name].update(err_body, err_count)
            else:
                error_variants[err_name] = ErrStat(err_body, err_count)
        else:
            error_types[full_err] = err_count

    for err_name, err_stat in error_variants.iteritems():
        if err_name in error_types:
            error_types[err_name] += err_stat.count
        else:
            error_types[err_name] = err_stat.count
        err_stat.bodies = sorted(err_stat.bodies, key=lambda tup: tup[1], reverse=True)

    return (
        sorted(error_types.items(), key=operator.itemgetter(1), reverse=True),
        sorted(error_variants.items(), key=operator.itemgetter(0)))


def _write_csv(output_file, error_types, error_variants):
    with open(output_file, 'wb') as csvfile:
        csv_writer = UnicodeWriter(csvfile)
        csv_writer.writerow(['Type', 'Count', 'Body'])
        for error in error_types:
            csv_writer.writerow([error[0], str(error[1]), ''])
        err_rows = 1 + len(error_types)
        csv_writer.writerow(['', '=SUM(B2:B{})'.format(err_rows), ''])
        csv_writer.writerow(['' * 3])

        for err_name, err_stat in error_variants:
            for rec in err_stat.bodies:
                csv_writer.writerow([err_name, str(rec[1]), rec[0]])


def main(args=None):
    """Main function for cli."""
    logging.basicConfig(format='%(name)s:%(levelname)s:%(message)s', level=logging.INFO)
    args = _get_args(args)
    html = _get_report(args.input_file, args.user, args.password)
    if not html:
        return 1
    parsed_html = _parse_html(html)
    all_errors = _get_tracebacks(parsed_html)
    if not all_errors:
        logger.error("No tracebacks found in the {}".format(args.input_file))
        return 1
    error_types, error_variants = _sort_errors(all_errors)
    _write_csv(args.output_file, error_types, error_variants)

    return 0


if __name__ == '__main__':
    sys.exit(main())
