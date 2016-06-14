
from __future__ import print_function

import re
import os
import glob
import xml.etree.ElementTree as ET
from collections import defaultdict
import HTMLParser

html = HTMLParser.HTMLParser()

BLOCKS_PATHS = '/home/koslowski/code/gnuradio/gr-**/grc/*.xml'

xml_tag_matcher = re.compile(r'<(?P<tag>\w+)>(?P<text>[^<]+?)</(?P=tag)>', flags=re.DOTALL)


def get_param_keys(data):
    namespace = {'id': None}

    root = ET.parse(data).getroot()
    for param in root.findall('param'):
        key = param.find('key').text
        namespace[key] = param.findall('option/value')

        values = defaultdict(list)
        for opt in param.findall('option/opt'):
            subkey, value = opt.text.split(':')
            values[subkey].append(value)
        for subkey, values in values.items():
            namespace['{}.{}'.format(key, subkey)] = values
    return namespace


def extend_param_keys(keys):
    templates = ['{}', '({})', '{}()', '({}())', '{{{}}}', '{{{}()}}']
    extended = []
    for key in keys:
        for template in templates:
            extended.append(template.format(key))
    return extended


def iter_templates(filename):
    with open(filename) as fp:
        data = fp.read().decode(encoding='utf-8', errors='replace')

    data = re.sub(r'<!--.*?-->', '', data, flags=re.DOTALL)
    for match in xml_tag_matcher.finditer(data):
        text = match.group('text')
        if '$' in text:
            yield html.unescape(text)


def iter_hard_templates(filename, params):
    for template in iter_templates(filename):
        if template[0] == '$' and template[1:] in params:
            continue
        if all(any(t.startswith(p) for p in params) for t in template.split('$')[1:]):
            continue
        yield template


def main():
    count = 0
    for count, filename in enumerate(glob.iglob(BLOCKS_PATHS), 1):
        params = get_param_keys(filename)
        templates = list(iter_hard_templates(filename, extend_param_keys(params)))

        if templates:
            print('\n{}:\t{}'.format(os.path.basename(filename)[:-4], ', '.join(params)))
        for template in templates:
            print('\t', template)

    print('Total number of files:', count)


if __name__ == '__main__':
    main()
