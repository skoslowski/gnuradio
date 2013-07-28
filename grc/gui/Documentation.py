

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
from os.path import expanduser, walk
from Messages import open_doc_and_code_message
import time
import lxml.html
import contextlib
from html_urls import link_urls, url_lst




class open_document_and_source_code():


	def __init__(self):
		
		self.get_webpage = webbrowser.get() 
		self.sph=gr.prefs().get_string('grc', 'sphinx_base_uri', '')
		self.dox=gr.prefs().get_string('grc', 'doxygen_base_uri', '')
		self.path=gr.prefs().get_string('grc', 'source_path', '')	
		self.data1_doc=['add_vcc','multiply_vcc','fir_filter_ccf']
		self.data2_doc=['add_cc','multiply_cc','firdes']	
		self.data1_code=['psk_mod','psk_demod','qam_mod','qam_demod','ofdm_tx','ofdm_rx','gmsk_mod','gmsk_demod','gfsk_mod','gfsk_demod','dbpsk_mod','dbpsk_demod','packet_mod_f','packet_demod_f','fir_filter_ccf']
		self.data2_code=['psk','qam','ofdm_txrx','gmsk','gfsk','bpsk','ofdm','firdes']
		self.source_code_uri=gr.prefs().get_string('grc', 'source_code_base_uri', '')

	def open_document(self,block,chck):

		block_info=block.get_make()
		check=False
		try:
			block_info_part=block_info.split('(')[0].split('.')
			
	 		class_name=block_info_part[0]
			if len(block_info_part)==3:
				block_name=block_info_part[2]
			else:
				block_name=block_info_part[1]
			
			#############################################################################################
			#For add, multiply, low pass, band pass, band reject, root raised cosine, band stop blocks
			#############################################################################################
			i=0
			for blk in self.data1_doc:
				if re.match(block_name, self.data1_doc[i]):	
					block_name=self.data2_doc[i]
					break
				i=i+1
                        ############################################################################################		
			#block name as in doxygen docs
			block_name_d=""
			block_name_parts=block_name.split('_')
			for i in range(0,len(block_name_parts)):
				if i==len(block_name_parts)-1:
					block_name_d=block_name_d+block_name_parts[i]
				else:
					block_name_d=block_name_d+block_name_parts[i]+'__'
			module_base_path=gr.prefs().get_string(class_name, 'doc_path', '')
			complete_url=self.get_valid_uri(block_name_d,class_name,self.dox,'annotated.html',self.dox)
			if complete_url is not None:
				check=True
				if chck is True:
					open_doc_and_code_message('>>> Opening:  %s\n\n'%complete_url)
					self.get_webpage.open(complete_url)
				return True
			else:	
				complete_url=self.get_valid_uri(block_name,class_name,self.sph,'genindex.html',self.sph)
				if complete_url is not None:
					check=True
					if chck is True:
						open_doc_and_code_message('>>> Opening:  %s\n\n'%complete_url)
						self.get_webpage.open(complete_url)	
					return True			
			if check is False:
				if module_base_path is not '':
					complete_url=self.out_of_tree_module(module_base_path,block_name_d)
					if complete_url is not None:
						if chck is True:
							open_doc_and_code_message('>>> Opening:  %s\n\n'%complete_url)
							self.get_webpage.open(complete_url)
						return True
					else:
						return False			
				else:
					return False
		except IndexError as e:
			return False
	
	
	def out_of_tree_module(self,address,name_d):
		uri=""
		try:
			links = lxml.html.parse("file://"+address+'annotated.html').xpath("//a/@href")
			for url in links: 
				if name_d in url.lower(): 
					if re.search(name_d+".html"+"\Z", url):
						uri=url
						break
		except IOError, AttributeError:
			return None
		if uri is not "":
			complete_uri=address+uri
			try:	
				with open(complete_uri): 
					return "file://"+complete_uri
			except IOError:
				return None
				
	
	def get_valid_uri(self,name,class_n,index_page,html_file,base_uri):
		uri=""
		remote_lst=False
		if not url_lst(html_file):
			link_urls()
		for url in url_lst(html_file):
			if class_n in url.lower() and re.search(name+".html"+"\Z", url):
				uri=url
				remote_lst=True
				break
			if re.search('\.'+name+"\Z", url):
				uri=url
				remote_lst=True
				break
		if remote_lst is False:
			try:
				links = lxml.html.parse("file://"+index_page.split(',')[0]+html_file).xpath("//a/@href")
				for url in links:
	    				if class_n in url.lower() and re.search(name+".html"+"\Z", url):
						uri=url
						break
					if re.search('\.'+name+"\Z", url):
						uri=url
						break
			except IOError,AttributeError:
				return None

		if uri is not "":
			complete_uri=base_uri.split(',')[1]+uri
			if self.network_connection() is True:
				if self.check_url(complete_uri) is True:
					return complete_uri
				
			else:
				if "sphinx" in base_uri.lower():
					complete_uri=base_uri.split(',')[0]+uri
					uri_check=complete_uri.split("#")[0]
				else:
					complete_uri=base_uri.split(',')[0]+uri
					uri_check=complete_uri

				try:	
					with open(uri_check): 
						return "file://"+complete_uri
				except IOError:
					return None
		else:
			return None
				


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
	
 
	def check_url(self,url):
	    
	    good_codes = [httplib.OK, httplib.FOUND, httplib.MOVED_PERMANENTLY]
	    return self.get_server_status_code(url) in good_codes



	def open_source_code(self,block):
		block_info=block.get_make()
		check_find=False
		OTM_check_find=False
		code_file=None
		try:
			block_info_part=block_info.split('(')[0].split('.')
			class_name=block_info_part[0]
			if len(block_info_part)==3:
				block_name=block_info_part[2]
			else:
				block_name=block_info_part[1]
			block_c=block_name+"_impl.cc"
			block_p=block_name+".py"
			####################################################################################################
			#For qpsk_mod, qpsk_demod, psk_mod, psk_demod, qam_mod, qam_demod, gmsk_mod, gmsk_demod, low pass, 
			#band pass,band reject, root raised cosine, band stop, ofdm_mod, ofdm_demod, qpsk_mod, qpsk_demod, 
			#gfsk_mod, gfsk_demod, ofdm_tx, ofdm_rx blocks
			####################################################################################################	
			i=0
			for blk in self.data1_code:
				if re.match(block_name, blk):
					block_p=self.data2_code[i/2]+'.py'
					block_c=self.data2_code[i/2]+'.cc'
					break
				i=i+1
			####################################################################################################
								
			if os.path.isdir(self.path):
				for dirs, subdirs, files in os.walk(self.path):
					for f in files:
						if os.path.isfile(os.path.join(dirs, block_c)) is True:
							check_find=True
							open_doc_and_code_message('>>> Opening:  %s\n\n'%os.path.join(dirs, block_c))
							os.system("gedit "+os.path.join(dirs, block_c))
							break
						if os.path.isfile(os.path.join(dirs, block_p)) is True:
							open_doc_and_code_message('>>> Opening:  %s\n\n'%os.path.join(dirs, block_p))
							check_find=True
							os.system("gedit "+os.path.join(dirs, block_p))
							break
			path=gr.prefs().get_string(class_name, 'module_path', '')
			if os.path.isdir(path) and check_find is False:
				for dirs, subdirs, files in os.walk(path):
					for f in files:
						if os.path.isfile(os.path.join(dirs, block_c)) is True:
							OTM_check_find=True
							open_doc_and_code_message('>>> Opening:  %s\n\n'%os.path.join(dirs, block_c))
							os.system("gedit "+os.path.join(dirs, block_c))
							break
			

			if self.network_connection() is True and OTM_check_find is False and not os.path.isdir(self.path):
				code_file=self.remote_copy_of_source_code(self.source_code_uri,class_name,block_c,block_p)
				if code_file is None:
					class_list=[]
					try:
						links = lxml.html.parse(self.source_code_uri).xpath("//a/@href")
						for url in links:
							if 'tree' in url.lower() and '/gr-' in url.lower():
								class_list.append(url)
						for cls in class_list:
							class_n=cls.split('-')[1]
							if not re.match(class_n,class_name):
								code_file=self.remote_copy_of_source_code(self.source_code_uri,class_n,block_c,block_p)
								if code_file is not None:
									break
					except AttributeError, IOError:
						pass
				if code_file is not None:
					self.get_webpage.open(code_file)
					open_doc_and_code_message('>>> Opening:  %s\n\n'%code_file)

			if os.path.isdir(self.path) is False and os.path.isdir(path) is False and self.network_connection() is False:
				Errorbox("""<b>Internet connection is not available and GNU Radio source tree does not exist in this system</b>""")
			elif OTM_check_find is False and check_find is False and code_file is None:
				Errorbox("""<b>Source code of selected block is not available</b>""")
				
		except IndexError as e:
			Errorbox("""<b>Source code of selected block is not available</b>""")



	def remote_copy_of_source_code(self,path,class_name,block_c,block_p):
		try:
			links = lxml.html.parse(path+'/gr-'+class_name+'/lib').xpath("//a/@href")
			for url in links:
				if 'tree' in url.lower() and re.search('/'+block_c+"\Z", url):
					return 'http://gnuradio.org'+url
			links = lxml.html.parse(path+'/gr-'+class_name+'/python/'+class_name).xpath("//a/@href")
			for url in links:
				if 'tree' in url.lower() and re.search('/'+block_p+"\Z", url):
					return 'http://gnuradio.org'+url
			return None
		except AttributeError, IOError:
			return None

				

def Errorbox(err_msg): MessageDialogHelper(
type=gtk.MESSAGE_ERROR,
buttons=gtk.BUTTONS_CLOSE,
title='Error',
markup=err_msg)




