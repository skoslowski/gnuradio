import lxml.html
import contextlib
import urllib2
import urllib
from gnuradio import gr
import re
import os
import sys


lst_doxygen=[]
lst_sphinx=[]

def link_urls():
	global lst_doxygen
	global lst_sphinx


	if network_connection() is True:
		try:
			links = lxml.html.parse(gr.prefs().get_string('grc', 'doxygen_base_uri', '').split(',')[1]+"annotated.html").xpath("//a/@href")
			for url in links: 
				lst_doxygen.append(url)
			links = lxml.html.parse(gr.prefs().get_string('grc', 'sphinx_base_uri', '').split(',')[1]+"genindex.html").xpath("//a/@href")
			for url in links: 
				lst_sphinx.append(url)
		except (IOError, AttributeError, IndexError):
			pass
		
		
def url_lst(doc):
	if re.match(doc,'annotated.html'):
		return lst_doxygen
	if re.match(doc,'genindex.html'):
		return lst_sphinx
def network_connection():
	
	network=False
	try:
		response = urllib2.urlopen("http://google.com", None, 2.5)
		network=True
	
	except urllib2.URLError, e:
		   pass
	return network


