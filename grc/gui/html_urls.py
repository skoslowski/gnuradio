
import threading
import lxml.html
import contextlib
import time
import urllib2
import urllib
from gnuradio import gr
import re
import signal
import os
import sys

exitFlag = 0
lst_doxygen=[]
lst_sphinx=[]
class myThread (threading.Thread):
    def __init__(self, counter):
        threading.Thread.__init__(self)
	self.counter=counter
    def run(self):
        link_urls(self.counter)

def link_urls(delay):
	global lst_doxygen
	global lst_sphinx
 	global exitFlag
	
	while exitFlag==0:
		if True:
			if network_connection() is True:
				try:
					links = lxml.html.parse(gr.prefs().get_string('grc', 'doxygen_base_uri', '').split(',')[1]+"annotated.html").xpath("//a/@href")
					for url in links: 
						lst_doxygen.append(url)
					links = lxml.html.parse(gr.prefs().get_string('grc', 'sphinx_base_uri', '').split(',')[1]+"genindex.html").xpath("//a/@href")
					for url in links: 
						lst_sphinx.append(url)
					exitFlag=1
				except (IOError, AttributeError, IndexError):
					pass
			time.sleep(delay)
		
		
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








