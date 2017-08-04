#!/usr/bin/env python

# -*- coding: utf-8 -*-
# pylint: disable=logging-format-interpolation
"""
Reads junit-report.xml and produces text file(s) with tracebacks.
"""

from __future__ import unicode_literals, absolute_import

import argparse
import io
import logging
import os
import sys

from lxml import etree

import requests
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


def _get_args(args=None):
    """Get command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_file', required=True,
                        help="Input junit-report.xml")
    parser.add_argument('-f', '--output-file', required=True,
                        help="Output file")
    parser.add_argument('-d', '--output-dir', required=True,
                        help="Output dir for tracebacks in one files per test case")
    parser.add_argument('--user',
                        help="Kerberos username")
    parser.add_argument('--password',
                        help="Kerberos password")
    return parser.parse_args(args)


def _get_report(location, user=None, password=None):
    """Reads report data from file or URL."""
    if 'http' in location:
        if not all((user, password)):
            logger.error('Missing credentials, cannot download')
            return
        try:
            report_data = requests.get(location, auth=(user, password), verify=False)
        # pylint: disable=broad-except
        except Exception as err:
            logger.error('Failed to download: {}'.format(err))
            return
        return report_data.content

    location = os.path.expanduser(location)
    if os.path.isfile(location):
        with open(location, 'rb') as report_data:
            return report_data.read()


def _get_xml_root(xml):
    try:
        # pylint: disable=no-member
        return etree.fromstring(xml)
    except Exception as err:
        raise Exception('Failed to parse XML file: {}'.format(err))


def _get_polarion_name(classname, title):
    """Gets Polarion test case name."""
    last_comp = classname.split('.')[-1]
    if last_comp[0].isupper():
        polarion_name = '{0}.{1}'.format(last_comp, title)
    else:
        polarion_name = title
    return polarion_name


def _get_tracebacks(xml_root):
    for test_data in xml_root:
        if test_data.tag != 'testcase':
            continue

        traceback = ''
        for element in test_data:
            if element.tag in ('error', 'failure'):
                traceback = element.text
                break

        if traceback:
            title = test_data.get('name')
            classname = test_data.get('classname')
            yield (classname, title, traceback)


def _get_unicode_str(obj):
    if isinstance(obj, unicode):
        return obj
    if isinstance(obj, str):
        return obj.decode('utf-8', errors='ignore')
    return unicode(obj)


def _get_test_file(output_dir, test_name):
    return os.path.join(output_dir, test_name.replace('/', '_'))


def _output_test_data(name, fail, output_desc):
    output_desc.write('{}\n'.format(name))
    output_desc.write('{}\n'.format('#' * len(name)))
    output_desc.write('{}\n'.format(fail))


def _write_tracebacks(xml, output_file, output_dir):
    xml_root = _get_xml_root(xml)
    tracebacks_gen = _get_tracebacks(xml_root)
    with io.open(output_file, 'w', encoding='utf-8') as output_single:
        for classname, title, fail in tracebacks_gen:
            name = '{0}.{1}'.format(classname, title)
            name, fail = _get_unicode_str(name), _get_unicode_str(fail)

            # write to file with all test cases
            _output_test_data(name, fail, output_single)
            output_single.write('\n\n')

            # write to single file for test case
            polarion_name = _get_polarion_name(classname, title)
            test_file = _get_test_file(output_dir, polarion_name)
            with io.open(test_file, 'w', encoding='utf-8') as output_multi:
                _output_test_data(name, fail, output_multi)


def main(args=None):
    """Main function for cli."""
    logging.basicConfig(format='%(name)s:%(levelname)s:%(message)s', level=logging.INFO)
    args = _get_args(args)
    xml = _get_report(args.input_file, args.user, args.password)
    if not xml:
        return 1
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    _write_tracebacks(xml, args.output_file, args.output_dir)

    return 0


if __name__ == '__main__':
    # pylint: disable=invalid-name
    logger = logging.getLogger()
    sys.exit(main())
