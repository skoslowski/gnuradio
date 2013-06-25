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
import Platform
from Dialogs import TextDisplay
from Constants import MIN_DIALOG_WIDTH, MIN_DIALOG_HEIGHT

def get_title_label(title):
	"""
	Get a title label for the params window.
	The title will be bold, underlined, and left justified.
	
	Args:
	    title: the text of the title
	
	Returns:
	    a gtk object
	"""
	label = gtk.Label()
	label.set_markup('\n<b><span underline="low">%s</span>:</b>\n'%title)
	hbox = gtk.HBox()
	hbox.pack_start(label, False, False, padding=11)
	return hbox

class PropsDialog(gtk.Dialog):
	"""
	A dialog to set block parameters, view errors, and view documentation.
	"""

	def __init__(self, block):
		"""
		Properties dialog contructor.
		
		Args:
		    block: a block instance
		"""
		self._hash = 0
		LABEL_SPACING = 7
		gtk.Dialog.__init__(self,
			title='Properties: %s'%block.get_name(),
			buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
		)
		self._block = block
		self.set_size_request(MIN_DIALOG_WIDTH, MIN_DIALOG_HEIGHT)
		vbox = gtk.VBox()
		#Create the scrolled window to hold all the parameters
		scrolled_window = gtk.ScrolledWindow()
		scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		scrolled_window.add_with_viewport(vbox)
		self.vbox.pack_start(scrolled_window, True)
		#Params box for block parameters
		self._params_box = gtk.VBox()
		self._params_box.pack_start(get_title_label('Parameters'), False)
		self._input_object_params = list()
		#Error Messages for the block
		self._error_box = gtk.VBox()
		self._error_messages_text_display = TextDisplay()
		self._error_box.pack_start(gtk.Label(), False, False, LABEL_SPACING)
		self._error_box.pack_start(get_title_label('Error Messages'), False)
		self._error_box.pack_start(self._error_messages_text_display, False)
		#Docs for the block
		self._docs_box = err_box = gtk.VBox()
		self._docs_text_display = TextDisplay()
		self._docs_box.pack_start(gtk.Label(), False, False, LABEL_SPACING)
		self._docs_box.pack_start(get_title_label('Documentation'), False)
		self._docs_box.pack_start(self._docs_text_display, False)
		#Add the boxes
		vbox.pack_start(self._params_box, False)
		vbox.pack_start(self._error_box, False)
		vbox.pack_start(self._docs_box, False)
		#Add the button to fetch the document
		button = gtk.Button("Fetch documentation")
		self.action_area.pack_end(button)
		button.connect("clicked", self.doc_button_on_clicked)
		button.show()
		#connect events
		self.connect('key-press-event', self._handle_key_press)
		self.connect('show', self._update_gui)
		#show all (performs initial gui update)
		self.show_all()

	#button to get documentation
	def doc_button_on_clicked(self,widget):
		
		get_webpage = webbrowser.get() 
		#get gnuradio version
		version=self._block.get_parent().get_parent().get_version()
		#find class name
		block_info=self._block.get_make()
		block_info_part=block_info.split('.')
		class_name=block_info_part[0]
		#find block name
		block_name=""
		if block_info_part[1]=="qam" or block_info_part[1]=="psk":
			for i in range(0,len(block_info_part[2])):
				if block_info_part[2][i] is not '(':
					block_name=block_name+block_info_part[2][i]
				else:
					break
		else:
			for i in range(0,len(block_info_part[1])):
				if block_info_part[1][i] is not '(':
					block_name=block_name+block_info_part[1][i]
				else:
					break
		#get web address for documentation of python blocks
		python_blocks_class_list=("blks2","uhd")		
		if class_name in python_blocks_class_list:
			if class_name=="uhd":
				complete_web_address="http://gnuradio.org/doc/sphinx/uhd.html"
			if class_name=="blks2":
				complete_web_address="http://gnuradio.org/doc/sphinx/blks2/blks.html#gnuradio.blks2."+block_name
		#get web address for documentation of non-python blocks
		else:
			#get tha part of web address in format "classgr_1_1blocks_1_1.....__.....__...." from class name and block name
			block_name_parts=block_name.split('_')
			lst_not_classgr=('audio','vocoder','qtgui','fcd','noaa','pager','trellis','wavelet','digital','gr')
			if class_name in lst_not_classgr:
				web_address=class_name+"__"
			else:
				web_address="gr_1_1"+class_name+"_1_1"
			#for blocks that belong to firdes class
			if block_name=="fir_filter_ccf":
				web_address="gr__firdes"
			else:

				for i in range(0,len(block_name_parts)):
					if i==len(block_name_parts)-1:
						web_address=web_address+block_name_parts[i]
					else:
						web_address=web_address+block_name_parts[i]+'__'
			#blocks in digital class have different web addresses for their documentations; deals them separately 
			if class_name=="digital" or class_name=="grc_blks2":
				complete_web_address=self.digital_class(block_name_parts,block_name)
			else:
				complete_web_address="http://gnuradio.org/doc/doxygen/class"+web_address+".html"
		#opens remote copy
		if self.network_connection() is True:
			get_webpage.open(complete_web_address)
		#opens local copy
		else:
			#for python blocks
			if class_name in python_blocks_class_list:
				if class_name=="uhd":
					complete_local_address="file://"+expanduser("~")+"/gnuradio/build/docs/sphinx/sphinx_out/uhd.html"
				if class_name=="blks2":
					complete_local_address="file://"+expanduser("~")+"/gnuradio/build/docs/sphinx/sphinx_out/blks2/blks.html#gnuradio.blks2."+block_name
			#for non-python blocks
			else:				
				if class_name=="digital" or class_name=="grc_blks2":
					l=address_parts=complete_web_address.split('/')
					if "sphinx" in address_parts:
						complete_local_address="file://"+expanduser("~")+"/gnuradio/build/docs/sphinx/sphinx_out/"+l[len(l)-2]+"/"+l[len(l)-1]
					else:					
						complete_local_address="/usr/local/share/doc/gnuradio-"+version+"/html/class"+web_address+".html"
				else:
					complete_local_address="/usr/local/share/doc/gnuradio-"+version+"/html/class"+web_address+".html"
			get_webpage.open(complete_local_address)
			
			
	#checks internet connection
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


	def digital_class(self,block_lst,block):
		address=""
		for i in range(0,len(block_lst)):
			if i==len(block_lst)-1:
				address=address+block_lst[i]			
			else:
				address=address+block_lst[i]+'__'	
		#blocks of digital class have two different formats for web address of doxygen documentation				
		address1="http://gnuradio.org/doc/doxygen/classdigital__"+address+".html"
		address2="http://gnuradio.org/doc/doxygen/classgr_1_1digital_1_1"+address+".html"
		#checks which format is a valid url
		if self.check_url(address1) is True:
			return address1
		else:
			if self.check_url(address2) is True:
				return address2
			else:
				#for python blocks of digital class. each block has different format for web address of sphinx documetation. write their web addresses individually
				if block=="packet_mod_f":
					return "http://gnuradio.org/doc/sphinx/digital/blocks.html#gnuradio.digital.ofdm_mod"
				if block=="ofdm_sync_pn":
					return "http://gnuradio.org/doc/sphinx/digital/blocks.html#gnuradio.digital.ofdm_sync_pn"
				if block=="packet_demod_f":
					return "http://gnuradio.org/doc/sphinx/digital/blocks.html#gnuradio.digital.ofdm_demod"
				if block=="ofdm_rx":
					return "http://gnuradio.org/doc/sphinx/digital/blocks.html#gnuradio.digital.ofdm_receiver"
				if block=="qam_mod":
					return "http://gnuradio.org/doc/sphinx/digital/blocks.html#gnuradio.digital.qam.qam_mod"
				if block=="qam_demod":
					return "http://gnuradio.org/doc/sphinx/digital/blocks.html#gnuradio.digital.qam.qam_demod"
				if block=="psk_mod":
					return "http://gnuradio.org/doc/sphinx/digital/blocks.html#gnuradio.digital.psk.psk_mod"
				if block=="psk_demod":
					return "http://gnuradio.org/doc/sphinx/digital/blocks.html#gnuradio.digital.psk.psk_demod"
				if block=="gmsk_mod":
					return "http://gnuradio.org/doc/sphinx/digital/blocks.html#gnuradio.digital.gmsk.gmsk_mod"
				if block=="gmsk_demod":
					return "http://gnuradio.org/doc/sphinx/digital/blocks.html#gnuradio.digital.gmsk.gmsk_demod"
				if block=="dbpsk_mod":
					return "http://gnuradio.org/doc/sphinx/digital/blocks.html#gnuradio.digital.bpsk.dbpsk_mod"
				if block=="dbpsk_demod":
					return "http://gnuradio.org/doc/sphinx/digital/blocks.html#gnuradio.digital.bpsk.dbpsk_demod"
				else:
					return ""
							

	def _params_changed(self):
		"""
		Have the params in this dialog changed?
		Ex: Added, removed, type change, hide change...
		To the props dialog, the hide setting of 'none' and 'part' are identical.
		Therfore, the props dialog only cares if the hide setting is/not 'all'.
		Make a hash that uniquely represents the params' state.
		
		Returns:
		    true if changed
		"""
		old_hash = self._hash
		#create a tuple of things from each param that affects the params box
		self._hash = hash(tuple([(
			hash(param), param.get_type(), param.get_hide() == 'all',
		) for param in self._block.get_params()]))
		return self._hash != old_hash

	def _handle_changed(self, *args):
		"""
		A change occured within a param:
		Rewrite/validate the block and update the gui.
		"""
		#update for the block
		self._block.rewrite()
		self._block.validate()
		self._update_gui()

	def _update_gui(self, *args):
		"""
		Repopulate the parameters box (if changed).
		Update all the input parameters.
		Update the error messages box.
		Hide the box if there are no errors.
		Update the documentation block.
		Hide the box if there are no docs.
		"""
		#update the params box
		if self._params_changed():
			#hide params box before changing
			self._params_box.hide_all()
			#empty the params box
			for io_param in list(self._input_object_params):
				self._params_box.remove(io_param)
				self._input_object_params.remove(io_param)
				io_param.destroy()
			#repopulate the params box
			for param in self._block.get_params():
				if param.get_hide() == 'all': continue
				io_param = param.get_input(self._handle_changed)
				self._input_object_params.append(io_param)
				self._params_box.pack_start(io_param, False)
			#show params box with new params
			self._params_box.show_all()
		#update the errors box
		if self._block.is_valid(): self._error_box.hide()
		else: self._error_box.show()
		messages = '\n\n'.join(self._block.get_error_messages())
		self._error_messages_text_display.set_text(messages)
		#update the docs box
		if self._block.get_doc(): self._docs_box.show()
		else: self._docs_box.hide()
		self._docs_text_display.set_text(self._block.get_doc())

	def _handle_key_press(self, widget, event):
		"""
		Handle key presses from the keyboard.
		Call the ok response when enter is pressed.
		
		Returns:
		    false to forward the keypress
		"""
		if event.keyval == gtk.keysyms.Return:
			self.response(gtk.RESPONSE_ACCEPT)
			return True #handled here
		return False #forward the keypress

	def run(self):
		"""
		Run the dialog and get its response.
		
		Returns:
		    true if the response was accept
		"""
		response = gtk.Dialog.run(self)
		self.destroy()
		return response == gtk.RESPONSE_ACCEPT
