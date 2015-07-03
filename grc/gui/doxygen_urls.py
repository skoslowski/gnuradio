
import urllib2
import json
import itertools
import os

from gnuradio.grc.python.Platform import Platform


BASE_URL = 'http://gnuradio.org/doc/doxygen'

def load_classes_data():
    url = os.path.join(BASE_URL, 'search/classes_{:x}.js')
    url_base = os.path.dirname(url)
    prefix = 'var searchData='

    doc_urls = dict()

    for i in itertools.count():
        req = urllib2.Request(url.format(i), None, {'User-Agent': 'wget/1.0'})
        print url.format(i)
        try:
            result = urllib2.urlopen(req).read().decode()
        except urllib2.HTTPError as e:
            if e.code == 404:
                break  # no more data

        if not result.startswith(prefix) or result[-1] != ';':
            raise ValueError('Unexpected format while fetching Doxygen URLs')

        data = result[len(prefix):-1].replace("'", '"')

        for entry in json.loads(data):
            try:
                field, (cls, (path, _, ns)) = entry
            except ValueError:
                print field
                continue
            if ns:
                cls = ns.replace('::', '.') + '.' + cls

            if cls.endswith('_xx'):
                cls = cls[:-3]

            doc_url = os.path.normpath(os.path.join(url_base, path))

            doc_urls[cls] = doc_url
    return doc_urls



try:
    # raise Exception()
    urls = json.load(open('urls.json'))
except:
    print 'building url cache'
    urls = load_classes_data()
    json.dump(urls, open('urls.json', 'w'))

try:
    blocks = json.load(open('blocks.json'))
except:
    print 'building block cache'
    pf = Platform()
    blocks = [(b._make, b._key) for b in pf.get_blocks()]
    json.dump(blocks, open('blocks.json', 'w'))







def cut_from(string, keys):
    for key in (keys if isinstance(keys, (list, tuple)) else (keys,)):
        if key in string:
            string = string[:string.index(key)].strip()
    return string

found = found2 = searched = 0
for make_raw, key_raw in blocks:

    for line in make_raw.split('\n'):
        make = line.strip()
        if not make.startswith('#'):
            break
    else:
        continue

    searched += 1

    if '_' not in key_raw:
        continue
    key = cut_from(key_raw.split('_', 1)[1], ('_x', '_vx'))
    if key and any(key in cls for cls in urls):
        found += 1
        continue

    make = cut_from(make, ('#', '_x', '_vx', '_$', '(', '$'))
    if make and any(make in cls for cls in urls):
        found2 += 1
        print key_raw




print found, found2, searched


