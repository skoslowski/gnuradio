

"""
Copyright 2007, 2008, 2009 Free Software Foundation, Inc.
This file is part of GNU Radio

GNU Radio Companion is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

GNU Radio Companion is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
"""

import pygtk
pygtk.require('2.0')
import gtk
import webbrowser
from os.path import expanduser
import urllib2
import httplib
import urlparse
from sgmllib import SGMLParser
import urllib
from Dialogs import MessageDialogHelper
from gnuradio import gr



class FetchDocument():


	def __init__(self,block):
		self._block=block
		get_webpage = webbrowser.get() 
		version=self._block.get_parent().get_parent().get_version()
		block_info=self._block.get_make()
		block_info_part=block_info.split('.')
		#block name as in sphinx docs
		block_name=block_info_part[1].split('(')[0]
		#block name as in doxygen docs
		block_name_d=""
		block_name_parts=block_name.split('_')
		for i in range(0,len(block_name_parts)):
			if i==len(block_name_parts)-1:
				block_name_d=block_name_d+block_name_parts[i]
			else:
				block_name_d=block_name_d+block_name_parts[i]+'__'
#Below addresses and locations are stored in grc.conf file using gedit ~/.gnuradio/config.conf
'''
sphinx_base_uri=http://gnuradio.org/doc/sphinx/
sphinx_index_page_local=/gnuradio/build/docs/sphinx/sphinx_out/genindex.html
sphinx_index_page_net=http://gnuradio.org/doc/sphinx/genindex.html
sphinx_local_base_uri=/gnuradio/build/docs/sphinx/sphinx_out/
doxygen_base_uri=http://gnuradio.org/doc/doxygen/
doxygen_index_page_local=/gnuradio/build/docs/doxygen/html/annotated.html
doxygen_index_page_net=http://gnuradio.org/doc/doxygen/annotated.html
doxygen_local_base_uri=/usr/local/share/doc/gnuradio-'''

		#location and address of genindex.html
		sph_index_local="file://"+expanduser("~")+gr.prefs().get_string('grc', 'sphinx_index_page_local', '')
		sph_index_net=gr.prefs().get_string('grc', 'sphinx_index_page_net', '')
		#sphinx base uri for web address and local address
		sph_base_uri=gr.prefs().get_string('grc', 'sphinx_base_uri', '')
		sph_local_base_uri=expanduser("~")+gr.prefs().get_string('grc', 'sphinx_local_base_uri', '')
		#location and address of annotated.html
		dox_index_local="file://"+expanduser("~")+gr.prefs().get_string('grc', 'doxygen_index_page_local', '')
		dox_index_net=gr.prefs().get_string('grc', 'doxygen_index_page_net', '')
		#doxygen base uri for web address and local address
		dox_base_uri=gr.prefs().get_string('grc', 'doxygen_base_uri', '')
		dox_local_base_uri=gr.prefs().get_string('grc', 'doxygen_local_base_uri', '')+version+"/html/"

		#doxygen doc
		url_lst=self.index(dox_index_local,dox_index_net)
		complete_url=self.get_valid_uri(block_name_d,url_lst,dox_base_uri,dox_local_base_uri)
		if complete_url is not None:
			get_webpage.open(complete_url)
		#sphinx doc
		else:	
			url_lst=self.index(sph_index_local,sph_index_net)
			complete_url=self.get_valid_uri(block_name,url_lst,sph_base_uri,sph_local_base_uri)
			if complete_url is not None:
				get_webpage.open(complete_url)
		#file does not exist
			else:
				self.Errorbox()
		
		
	#makes complete uri and checks if uri exists or file at this location exits		
	def get_valid_uri(self,name,lst,base_uri,local_uri):
		uri=""
		for url in lst.urls: 
			if name in url.lower():
				uri=url
				break
		if uri is not "":
			complete_uri=base_uri+uri
			#for remote copy of doc
			if self.network_connection() is True:
				if self.check_url(complete_uri) is True:
					return complete_uri
				else:
					return None
			#for local copy of doc
			else:
				complete_uri=local_uri+uri
				try:
					if "sphinx" in complete_uri.lower():
						uri_check=complete_uri.split("#")[0]
					else:
						uri_check=complete_uri
					with open(uri_check): 
						return "file://"+complete_uri
				except IOError:
					return None
		else:
			return None

	#returns a list of url's in html file
	def index(self,url1,url2):
		try:
			open_index = urllib.urlopen(url2)
		except IOError as e:
			try:
				open_index = urllib.urlopen(url1)
			except IOError as e:
				self.Errorbox()
		url_list = URLLister()
		url_list.feed(open_index.read())
		url_list.close()
		open_index.close()
		return url_list

	#checks network connection
	def network_connection(self):
		network=False
		try:
		    response = urllib2.urlopen("http://google.com", None, 2.5)
		    network=True
	
		except urllib2.URLError, e:
		    pass
		return network


	
	def get_server_status_code(self,url):

	    host, path = urlparse.urlparse(url)[1:3]    
	    try:
		conn = httplib.HTTPConnection(host)
		conn.request('HEAD', path)
		return conn.getresponse().status
	    except StandardError:
		return None
	

	#checks valid url 
	def check_url(self,url):
	    
	    good_codes = [httplib.OK, httplib.FOUND, httplib.MOVED_PERMANENTLY]
	    return self.get_server_status_code(url) in good_codes

	def Errorbox(self): MessageDialogHelper(
	type=gtk.MESSAGE_ERROR,
	buttons=gtk.BUTTONS_CLOSE,
	title='Error',
	markup="""<b>File not found</b>""")

class URLLister(SGMLParser):
	def reset(self):
		SGMLParser.reset(self)
		self.urls = []

	def start_a(self, attrs):
		href = [v for k, v in attrs if k=='href']
		if href:
			self.urls.extend(href)

'''
		sphinx_base_uri="http://gnuradio.org/doc/sphinx/"
		sphinx_index_page1="file://"+expanduser("~")+"/gnuradio/build/docs/sphinx/sphinx_out/genindex.html"
		sphinx_index_page2="http://gnuradio.org/doc/sphinx/genindex.html"
		sphinx_local_base_uri=expanduser("~")+"/gnuradio/build/docs/sphinx/sphinx_out/"

		doxygen_base_uri="http://gnuradio.org/doc/doxygen/"
		doxygen_index_page1="file://"+expanduser("~")+"/gnuradio/build/docs/doxygen/html/annotated.html"
		doxygen_index_page2="http://gnuradio.org/doc/doxygen/annotated.html"
		doxygen_local_base_uri="/usr/local/share/doc/gnuradio-"+version+"/html/"
'''
