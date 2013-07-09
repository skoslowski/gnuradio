

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
import urllib2
import httplib
import urlparse
from sgmllib import SGMLParser
import urllib
from Dialogs import MessageDialogHelper
from gnuradio import gr
import re
import os
from os.path import expanduser
from os.path import walk



class FetchDocument():


	def __init__(self,block):
		self._block=block
		get_webpage = webbrowser.get() 
		block_info=self._block.get_make()
		print block_info
		try:
			block_info_part=block_info.split('(')[0].split('.')
	 		class_name=block_info_part[0]
			if len(block_info_part)==3:
				block_name=block_info_part[2]
			else:
				block_name=block_info_part[1]
			print class_name+" "+block_name
			#block name as in doxygen docs
			block_name_d=""
			block_name_parts=block_name.split('_')
			for i in range(0,len(block_name_parts)):
				if i==len(block_name_parts)-1:
					block_name_d=block_name_d+block_name_parts[i]
				else:
					block_name_d=block_name_d+block_name_parts[i]+'__'

			sph=gr.prefs().get_string('grc', 'sphinx_address', '')
			dox=gr.prefs().get_string('grc', 'doxygen_address', '')
			
			module_base_path=gr.prefs().get_string(class_name, 'base_path', '')

			if module_base_path is '':
				url_lst_d=self.index(dox,'annotated.html')
				url_lst_s=self.index(sph,'genindex.html')
				if not url_lst_s and not url_lst_d:
					self.Errorbox("""<b>annotated.html and genindex.html are not found</b>""")
				else:
					complete_url=self.get_valid_uri(block_name_d,class_name,url_lst_d,dox)
					if complete_url is not None:
						get_webpage.open(complete_url)
					#sphinx doc
					else:	
						complete_url=self.get_valid_uri(block_name,class_name,url_lst_s,sph)
						if complete_url is not None:
							get_webpage.open(complete_url)
					#file does not exist
						else:
							if url_lst_s and url_lst_d:
								self.Errorbox("""<b>Document not found</b>""")
							if not url_lst_s and url_lst_d:
								self.Errorbox("""<b>genindex.html is not found</b>""")
							if not url_lst_d and url_lst_s:
								self.Errorbox("""<b>annotated.html is not found</b>""")
			#blocks from out of tree modules
			else:
				complete_url=self.out_of_tree_module(module_base_path,block_name_d)
				if complete_url is not None:
					print complete_url
					get_webpage.open(complete_url)
				else:
					self.Errorbox("""<b>Document not found</b>""")						
		except IndexError as e:
			self.Errorbox("""<b>Document not found</b>""")
	
	
	def out_of_tree_module(self,address,name_d):
		uri=""
		try: 
			open_index = urllib.urlopen("file://"+address+'annotated.html')
		except IOError as e:
			open_index = []
		if not open_index:
			return None
		else:
			url_list = URLLister()
			url_list.feed(open_index.read())
			url_list.close()
			open_index.close()
			for url in url_list.urls: 
					if name_d in url.lower(): 
						if re.search(name_d+".html"+"\Z", url):
							uri=url
							break
			if uri is not "":
				complete_uri=address+uri
				try:	
					with open(complete_uri): 
						return "file://"+complete_uri
				except IOError:
					return None
			else:
				return None
				


	

	#makes complete uri and checks if uri exists or file at this location exits		
	def get_valid_uri(self,name,class_n,lst,base_uri):
		uri=""
		if lst:
			for url in lst.urls: 
				if name in url.lower(): 
					if "doxygen" in base_uri:
						if class_n in url.lower() and re.search(name+".html"+"\Z", url):
							uri=url
							break
					elif re.search(name+"\Z", url):
						uri=url
						break
			if uri is not "":
				complete_uri=base_uri.split(',')[1]+uri
				#for remote copy of doc
				if self.network_connection() is True:
					if self.check_url(complete_uri) is True:
						return complete_uri
					else:
						return None
				#for local copy of doc
				else:
					try:
						if "sphinx" in base_uri.lower():
							complete_uri=base_uri.split(',')[0]+uri
							uri_check=complete_uri.split("#")[0]
						else:
							complete_uri=base_uri.split(',')[0]+uri
							uri_check=complete_uri
						with open(uri_check): 
							return "file://"+complete_uri
					except IOError:
						return None
			else:
				return None
		else:
			return None
	#returns a list of url's in html file
	def index(self,index_page,html_file):
		try:
			open_index = urllib.urlopen(index_page.split(',')[1]+html_file)
		except IOError as e:
			try:
				open_index = urllib.urlopen("file://"+index_page.split(',')[0]+html_file)
			except IOError as e:
				return []
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

	def Errorbox(self,err_msg): MessageDialogHelper(
	type=gtk.MESSAGE_ERROR,
	buttons=gtk.BUTTONS_CLOSE,
	title='Error',
	markup=err_msg)

class find_source_code():

	def __init__(self,block):
		self._block=block
		block_info=self._block.get_make()
		check_find=False
		try:
			block_info_part=block_info.split('(')[0].split('.')
			if len(block_info_part)==3:
				block_name=block_info_part[2]+"_impl.cc"
				block_p=block_info_part[2]+".py"
			else:
				block_name=block_info_part[1]+"_impl.cc"
				block_p=block_info_part[1]+".py"

			path=gr.prefs().get_string('grc', 'source_path', '')
			if os.path.isdir(path):
				for dirs, subdirs, files in os.walk(path):
					for f in files:
						if os.path.isfile(os.path.join(dirs, block_name)) is True:
							check_find=True
							os.system("gedit "+os.path.join(dirs, block_name))
							break
						if os.path.isfile(os.path.join(dirs, block_p)) is True:
							check_find=True
							os.system("gedit "+os.path.join(dirs, block_p))
							break
				
				if check_find is False:
					self.Errorbox("""<b>Document not found</b>""")
				
			else:
				self.Errorbox("""<b>Document not found</b>""")
		except IndexError as e:
			self.Errorbox("""<b>Document not found</b>""")
	def Errorbox(self,err_msg): MessageDialogHelper(
	type=gtk.MESSAGE_ERROR,
	buttons=gtk.BUTTONS_CLOSE,
	title='Error',
	markup=err_msg)

class URLLister(SGMLParser):
	def reset(self):
		SGMLParser.reset(self)
		self.urls = []

	def start_a(self, attrs):
		href = [v for k, v in attrs if k=='href']
		if href:
			self.urls.extend(href)


