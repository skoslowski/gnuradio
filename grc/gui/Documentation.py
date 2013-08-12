

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
import ConfigParser


class open_document_and_source_code():


    def __init__(self):

        self.get_webpage = webbrowser.get()
        self.sph=gr.prefs().get_string('grc', 'sphinx_base_uri', '')
        self.dox=gr.prefs().get_string('grc', 'doxygen_base_uri', '')
        self.path=gr.prefs().get_string('grc', 'source_path', '')
        self.special_cases_doc={'add_vcc': 'add_cc',
                                'multiply_vcc': 'multiply_cc',
                                'fir_filter_ccf': 'firdes'}
	self.special_cases_sourcecode={'psk_mod': 'psk',
                                'psk_demod': 'psk',
                                'qam_mod': 'qam',
                                'qam_demod':'qam',
                                'ofdm_tx': 'ofdm_txrx',
                                'ofdm_rx':'ofdm_txrx',
                                'gmsk_mod': 'gmsk',
                                'gmsk_demod': 'gmsk',
                                'gfsk_mod': 'gfsk',
                                'gfsk_demod':'gfsk',
                                'dbpsk_mod': 'bpsk',
                                'dbpsk_demod': 'bpsk',
                                'fir_filter_ccf':'firdes'}
        self.source_code_uri=gr.prefs().get_string('grc', 'source_code_base_uri', '')

    

    def open_document(self, block, open_doc):
        complete_url = self.get_document_uri(block)
        if complete_url is not None:
            if open_doc is True:
               open_doc_and_code_message('>>> Opening:  %s\n\n'%complete_url)
               self.get_webpage.open(complete_url)
            return True
        else:
            return False


    def out_of_tree_module(self, address, name_d):
        uri=""
        try:
            links = lxml.html.parse("file://"+address+'annotated.html').xpath("//a/@href")
            for url in links:
                if name_d in url.lower():
                    if re.search(name_d+".html"+"\Z", url):
                        uri=url
                        break
        except (IOError, AttributeError):
            return None

        if uri:
            if os.path.exists(address + uri):
                return "file://"+ address + uri
            else:
                return None
    def get_document_uri(self, block):
        block_info=block.get_make()
        if block_info:
            block_info_part=block_info.split('(')[0].split('.')

            class_name, block_name = block_info_part[0], block_info_part[-1]
            #############################################################################################
            #For add, multiply, low pass, band pass, band reject, root raised cosine, band stop blocks
            #############################################################################################

            for blk, repl in self.special_cases_doc.iteritems():
                if re.match(block_name, blk):
                    block_name = repl
                    break
            ############################################################################################
            #block name as in doxygen docs
            block_name_d = '__'.join(block_name.split('_'))

            module_base_path = gr.prefs().get_string(class_name, 'doc_path', '') 

            complete_url = self.get_valid_uri(block_name_d, class_name, self.dox, 'annotated.html', self.dox) or \
                           self.get_valid_uri(block_name,   class_name, self.sph, 'genindex.html',self.sph) or \
                           self.out_of_tree_module(module_base_path, block_name_d)
            return complete_url

        else:
            return None

    def get_valid_uri(self,name,class_n,index_page,html_file,base_uri):

        try:
            links = lxml.html.parse("file://"+index_page.split(',')[0]+html_file).xpath("//a/@href")
            uri=self.check_uri_list(name,class_n,links)
        except (IOError, AttributeError):
            uri=self.check_uri_list(name,class_n,url_lst(html_file))

        if uri:
            complete_uri=base_uri.split(',')[0]+uri
            if "sphinx" in base_uri.lower():
                uri_check=complete_uri.split("#")[0]
            else:    
                uri_check=complete_uri
            if os.path.exists(uri_check):
                return "file://"+complete_uri
            elif self.network_connection() is True:
                complete_uri=base_uri.split(',')[1]+uri
                if self.check_url(complete_uri) is True:
                    return complete_uri
            else:
                return None
        else:
            return None



    def check_uri_list(self,name,class_n,lst):
        if lst:
            for url in lst:
                if class_n in url.lower() and re.search(name+".html"+"\Z", url):
                    return url
                if re.search('\.'+name+"\Z", url):
                    return url
        return None



    def network_connection(self):
        try:
            urllib2.urlopen("http://google.com", None, 2.5)
            return True

        except urllib2.URLError:
            pass

        return False



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



    def open_source_code(self,block,open_code):
        block_info=block.get_make()
        code_uri=None
        local_code_file=None
        OTM_code_file=None
        if block_info:
            block_info_part=block_info.split('(')[0].split('.')
            class_name, block_name = block_info_part[0], block_info_part[-1]
            block_c=block_name+"_impl.cc"
            block_p=block_name+".py"
            ####################################################################################################
            #For qpsk_mod, qpsk_demod, psk_mod, psk_demod, qam_mod, qam_demod, gmsk_mod, gmsk_demod, low pass,
            #band pass,band reject, root raised cosine, band stop, ofdm_mod, ofdm_demod, qpsk_mod, qpsk_demod,
            #gfsk_mod, gfsk_demod, ofdm_tx, ofdm_rx blocks
            ####################################################################################################
            for blk, repl in self.special_cases_sourcecode.iteritems():
                if re.match(block_name, blk):
                    block_p = repl+'.py'
                    block_c = repl+'.cc'
                    break
            ####################################################################################################
            local_code_file=self.local_copy_of_source_code(self.path,block_c,block_p)
            if local_code_file:
                if open_code is True:
                    open_doc_and_code_message('>>> Opening:  %s\n\n'%local_code_file)
                    os.system("gedit "+local_code_file)
                return True
            else:
                path=gr.prefs().get_string(class_name, 'module_path', '')
                OTM_code_file=self.local_copy_of_source_code(path,block_c,None)
                if OTM_code_file:
                    if open_code is True:
                        open_doc_and_code_message('>>> Opening:  %s\n\n'%OTM_code_file)
                        os.system("gedit "+OTM_code_file)
                    return True
            if OTM_code_file is None and local_code_file is None and self.network_connection() is True:
                code_uri=self.remote_copy_of_source_code(class_name,block_c,block_p)
                if code_uri:
                    tagname = gr.version()
                    if tagname[0] != 'v': 
                        tagname = 'v' + tagname
                    if open_code is True:
                        self.get_webpage.open(code_uri+'?id='+tagname)
                        open_doc_and_code_message('>>> Opening:  %s\n\n'%(code_uri+'?id='+tagname))
                    return True
            return False

            '''if os.path.isdir(self.path) is False and os.path.isdir(path) is False and self.network_connection() is False:
                Errorbox("""<b>Internet connection is not available and GNU Radio source tree does not exist in this system</b>""")
            elif OTM_code_file is None and local_code_file is None and code_uri is None:
                Errorbox("""<b>Source code of selected block is not available</b>""")'''

        else:
            return False



    def remote_copy_of_source_code(self,class_name,block_c,block_p):

      
        if url_lst(class_name):
            for url in url_lst(class_name):
                if 'tree' in url.lower() and re.search('/'+block_c+"\Z", url):
                    return self.source_code_uri.split(',')[1]+url
        if url_lst(class_name+'_python'):
            for url in url_lst(class_name+'_python'):
                if 'tree' in url.lower() and re.search('/'+block_p+"\Z", url):
                    return self.source_code_uri.split(',')[1]+url
        return None

    def local_copy_of_source_code(self,path,block_c,block_p):
        if os.path.isdir(path):
                for dirs, subdirs, files in os.walk(path):
                    for f in files:
                        if os.path.isfile(os.path.join(dirs, block_c)) is True:
                            local_found=True
                            return os.path.join(dirs, block_c)
			if block_p:
                            if os.path.isfile(os.path.join(dirs, block_p)) is True:                      
                                return os.path.join(dirs, block_p)
        else:
            return None





