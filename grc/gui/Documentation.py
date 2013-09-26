

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
from gnuradio import gr
import re
import os
from os.path import expanduser, walk
from Messages import open_doc_and_code_message
import lxml.html
import contextlib
from HtmlUrl import link_urls, url_lst


class open_document_and_source_code():


    def __init__(self):
        
        """
        Initilize the base URI and path address for Doxygen and Sphinx manual and source codes.
        """
        self.get_webpage = webbrowser.get()
        self.sphinx=gr.prefs().get_string('grc', 'sphinx_base_uri', '')
        self.doxygen=gr.prefs().get_string('grc', 'doxygen_base_uri', '')
        self.source_path=gr.prefs().get_string('grc', 'source_path', '')
        self.special_cases_doc={'add_vcc': 'add_cc',
                                'multiply_vcc': 'multiply_cc',
                                'fir_filter_ccf': 'firdes'}
	self.special_cases_source_code={'psk_mod': 'psk',
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
                                'fir_filter_ccf':'firdes',
                                'am_demod_cf':'am_demod',
                                'fm_demod_cf':'fm_demod',
                                'fm_deemph':'fm_emph',
                                'fm_preemph':'fm_emph',
                                'tcp_sink':'tcp',
                                'tcp_source':'tcp'}
        self.source_code_uri=gr.prefs().get_string('grc', 'source_code_base_uri', '').split(',')[1]

    

    def open_document(self, block, open_doc):
        """
        Open documentation in web browser.  
        
        Args:
            block: a block instance.
            open_doc: If True then documentation will be opened.
                      
        Returns:
            true if documentation is available (to make the 'open Documentation' Icon accessible).
        """     
        complete_url = self.get_document_uri(block)

        if complete_url is not None:
            if open_doc is True:
               open_doc_and_code_message('>>> Opening:  %s\n\n'%complete_url)
               self.get_webpage.open(complete_url)
            return True
        else:
            return False

    def out_of_tree_module(self, address, name_d):
        """
        open the documentation of out of tree modules.
        
        Args:
            address: path to out of tree module.
            name_d:  block name as in doxygen manual.

        Returns:
            complete path of documentation if exists.
        """
        uri=""
        try:
            #extracts a list of uri's from html file.
            links = lxml.html.parse("file://"+address+'annotated.html').xpath("//a/@href")
            #check uri list to get required block uri.
            for url in links:
                if name_d in url.lower():
                    if re.search(name_d+".html\Z", url):
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
        """
        check the Doxygen and Sphinx manual (both local and remote copies) 
        and out of tree module paths to open doc.

        Returns:
            complete url of documentation if exists.
        """
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
            #check Doxygen manual, Sphinx manual and OTM's respectively to get the valid doc uri.
            complete_url = self.get_valid_uri(block_name_d, class_name, self.doxygen, 'annotated.html', self.doxygen) or \
                           self.get_valid_uri(block_name,   class_name, self.sphinx, 'genindex.html',self.sphinx) or \
                           self.out_of_tree_module(module_base_path, block_name_d)
            return complete_url

        else:
            return None

    def get_valid_uri(self,name,class_n,index_page_path,html_file,base_uri):
        """
        get a list of uri's from html file.
        check local and remote copies of manuals respectively. 

        Args:
            name: block name
            class_n: module name
            index_page_path: locations of local copy html files
            html_file: a string, 'annotated.html' for Doxygen manual and 'genindex.html' for Sphinx manuals
            base_uri: addresses of remote copy html files

        Returns:
            complete url of documentation if exists.
        """

        try:
            links = lxml.html.parse("file://"+index_page_path.split(',')[0]+html_file).xpath("//a/@href")
            uri=self.check_uri_list(name,class_n,links)
        except (IOError, AttributeError):
            #url_lst caches the list of uri's from remote html index page.
            uri=self.check_uri_list(name,class_n,url_lst(html_file))

        if uri:
            #get address to local copy of doc
            complete_uri=base_uri.split(',')[0]+uri
            if "sphinx" in base_uri.lower():
                uri_check=complete_uri.split("#")[0]
            else:    
                uri_check=complete_uri
            if os.path.exists(uri_check):
                return "file://"+complete_uri
            #get url to remote copy of doc
            elif self.network_connection() is True:
                complete_uri=base_uri.split(',')[1]+uri
                if self.check_url(complete_uri) is True:
                    return complete_uri
            else:
                return None
        else:
            return None



    def check_uri_list(self,name,class_n,lst):
        """
        pick correct uri for given block name.

        Args:
            name: block name
            class_n: module name
            lst: a list of URL's

        Returns:
            correct url for given block name if exists.
        """
        if lst:
            for url in lst:
                if class_n in url.lower() and re.search(name+".html\Z", url):
                    return url
                if re.search('\.'+name+"\Z", url):
                    return url
        return None



    def network_connection(self):
        """
        check network connection.
        """
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
        """
        check url if it exists.
        """
        good_codes = [httplib.OK, httplib.FOUND, httplib.MOVED_PERMANENTLY]
        return self.get_server_status_code(url) in good_codes



    def open_source_code(self,block,open_code):
        """
        Open source code.  
        
        Args:
            block: a block instance
            open_doc: If True then code will be opened.
                      
        Returns:
            true if code is available (to make the 'open source code' Icon accessible).
        """
        block_info=block.get_make()
        code_uri=None
        local_code_file=None
        OTM_code_file=None
        if block_info:
            block_info_part=block_info.split('(')[0].split('.')
            class_name, block_name = block_info_part[0], block_info_part[-1]
            #.cc and .py file names
            block_c=block_name+"_impl.cc"
            block_p=block_name+".py"
            ####################################################################################################
            #For qpsk_mod, qpsk_demod, psk_mod, psk_demod, qam_mod, qam_demod, gmsk_mod, gmsk_demod, low pass,
            #band pass,band reject, root raised cosine, band stop, ofdm_mod, ofdm_demod, qpsk_mod, qpsk_demod,
            #gfsk_mod, gfsk_demod, ofdm_tx, ofdm_rx blocks
            ####################################################################################################
            for blk, repl in self.special_cases_source_code.iteritems():
                if re.match(block_name, blk):
                    block_p = repl+'.py'
                    block_c = repl+'.cc'
                    break
            ####################################################################################################

            #first preference is to open local copy of source code. 
            local_code_file=self.local_copy_of_source_code(self.source_path,block_c,block_p)
            if local_code_file:
                if open_code is True:
                    open_doc_and_code_message('>>> Opening:  %s\n\n'%local_code_file)
                    os.system("gedit "+local_code_file)
                return True
            #second preference is to check OTM's for source code.
            else:
                path=gr.prefs().get_string(class_name, 'module_path', '')
                OTM_code_file=self.local_copy_of_source_code(path,block_c,None)
                if OTM_code_file:
                    if open_code is True:
                        open_doc_and_code_message('>>> Opening:  %s\n\n'%OTM_code_file)
                        os.system("gedit "+OTM_code_file)
                    return True
            #last preference is to open remote copy of source code.      
            if OTM_code_file is None and local_code_file is None and self.network_connection() is True:
                code_uri=self.remote_copy_of_source_code(class_name,block_c,block_p)
                if code_uri:
                    #open the remote copy of source code from suitable commit ID.
                    tagname = gr.version()
                    if tagname[0] != 'v': 
                        tagname = 'v' + tagname
                    if open_code is True:
                        self.get_webpage.open(code_uri+'?id='+tagname)
                        open_doc_and_code_message('>>> Opening:  %s\n\n'%(code_uri+'?id='+tagname))
                    return True
            return False

        else:
            return False



    def remote_copy_of_source_code(self,class_name,block_c,block_p):
        """
        check the list of uri's from html file.

        Args:            
            class_name: module name
            block_c: name of .cc file
            block_p: name of .py file

        Returns:
            valid uri for source code.
        """
        print self.source_code_uri
        if url_lst(class_name):
            for url in url_lst(class_name):
                if 'tree' in url.lower() and re.search('/'+block_c+"\Z", url):
                    return self.source_code_uri+url
        if url_lst(class_name+'_python'):
            for url in url_lst(class_name+'_python'):
                if 'tree' in url.lower() and re.search('/'+block_p+"\Z", url):
                    return self.source_code_uri+url
        return None

    def local_copy_of_source_code(self,path,block_c,block_p):
        """
        do a python walk in gnuradio source dir to find the source code.

        Args:            
            path: path of gnuradio source tree
            block_c: name of .cc file
            block_p: name of .py file

        Returns:
            valid location of source code.
        """
        if os.path.isdir(path):
                for dirs, subdirs, files in os.walk(path):
                    for f in files:
                        if os.path.isfile(os.path.join(dirs, block_c)) is True:
                            return os.path.join(dirs, block_c)
			if block_p:
                            if os.path.isfile(os.path.join(dirs, block_p)) is True:                      
                                return os.path.join(dirs, block_p)
        else:
            return None





