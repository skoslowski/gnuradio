"""
Copyright 2008, 2009 Free Software Foundation, Inc.
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
import Utils
import webbrowser
import os
import httplib
import urlparse
from Constants import MIN_DIALOG_WIDTH, MIN_DIALOG_HEIGHT
class TextDisplay(gtk.TextView):
	"""A non editable gtk text view."""

	def __init__(self, text=''):
		"""
		TextDisplay constructor.
		
		Args:
		    text: the text to display (string)
		"""
		text_buffer = gtk.TextBuffer()
		text_buffer.set_text(text)
		self.set_text = text_buffer.set_text
		self.insert = lambda line: text_buffer.insert(text_buffer.get_end_iter(), line)
		gtk.TextView.__init__(self, text_buffer)
		self.set_editable(False)
		self.set_cursor_visible(False)
		self.set_wrap_mode(gtk.WRAP_WORD_CHAR)

def MessageDialogHelper(type, buttons, title=None, markup=None):
	"""
	Create a modal message dialog and run it.
	
	Args:
	    type: the type of message: gtk.MESSAGE_INFO, gtk.MESSAGE_WARNING, gtk.MESSAGE_QUESTION or gtk.MESSAGE_ERROR
	    buttons: the predefined set of buttons to use:
		gtk.BUTTONS_NONE, gtk.BUTTONS_OK, gtk.BUTTONS_CLOSE, gtk.BUTTONS_CANCEL, gtk.BUTTONS_YES_NO, gtk.BUTTONS_OK_CANCEL
	
	Args:
	    tittle: the title of the window (string)
	    markup: the message text with pango markup
	
	Returns:
	    the gtk response from run()
	"""
	message_dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL, type, buttons)
	if title: message_dialog.set_title(title)
	if markup: message_dialog.set_markup(markup)
	response = message_dialog.run()
	message_dialog.destroy()
	return response


ERRORS_MARKUP_TMPL="""\
#for $i, $err_msg in enumerate($errors)
<b>Error $i:</b>
$encode($err_msg.replace('\t', '  '))

#end for"""
def ErrorsDialog(flowgraph): MessageDialogHelper(
	type=gtk.MESSAGE_ERROR,
	buttons=gtk.BUTTONS_CLOSE,
	title='Flow Graph Errors',
	markup=Utils.parse_template(ERRORS_MARKUP_TMPL, errors=flowgraph.get_error_messages()),
)

class AboutDialog(gtk.AboutDialog):
	"""A cute little about dialog."""

	def __init__(self, platform):
		"""AboutDialog constructor."""
		gtk.AboutDialog.__init__(self)
		self.set_name(platform.get_name())
		self.set_version(platform.get_version())
		self.set_license(platform.get_license())
		self.set_copyright(platform.get_license().splitlines()[0])
		self.set_website(platform.get_website())
		self.run()
		self.destroy()
#Add a function in tool bar to open the online source code of each GRC block	
class get_source_code():
	def __init__(self,block):
		self._block=block
		get_webpage = webbrowser.get() 
		web_address=""
		#find class name
		block_info=block.get_make()
		block_info_part=block_info.split('.')
		class_name=block_info_part[0]
		#find block name
		block_name=""
		for i in range(0,len(block_info_part[1])):
			if block_info_part[1][i] is not '(':
				block_name=block_name+block_info_part[1][i]
			else:
				break
		block_name_parts=block_name.split('_')
		for i in range(0,len(block_name_parts)):
				if i==len(block_name_parts)-1:
					web_address=web_address+block_name_parts[i]
				else:
					web_address=web_address+block_name_parts[i]+'__'
		class_lst=('pager','trellis','digital','vocoder','wavelet','volk','noaa','qtgui','fcd')
		#for source code of blocks that belong to above class list
		if class_name in class_lst:
			url="http://gnuradio.org/doc/doxygen/"+class_name+"__"+web_address+"_8h_source.html"
			get_webpage.open(url)
		else:
			#for source code of blocks that belong to digital class
			if block_name=="fir_filter_ccf":
				get_webpage.open("http://gnuradio.org/doc/doxygen/firdes_8h_source.html")
			#for source code of rest of the blocks
			else:
				url_1="http://gnuradio.org/doc/doxygen/gr__"+web_address+"_8h_source.html"			
				url_2="http://gnuradio.org/doc/doxygen/"+web_address+"_8h_source.html"
				valid_url_1=self.check_url(url_1)
				valid_url_2=self.check_url(url_2)
				if valid_url_1 is True:
					get_webpage.open(url_1)		
				if valid_url_2 is True:
					get_webpage.open(url_2)

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
		

def HelpDialog(): MessageDialogHelper(
	type=gtk.MESSAGE_INFO,
	buttons=gtk.BUTTONS_CLOSE,
	title='Help',
	markup="""\
<b>Usage Tips</b>

<u>Add block</u>: drag and drop or double click a block in the block selection window.
<u>Rotate block</u>: Select a block, press left/right on the keyboard.
<u>Change type</u>: Select a block, press up/down on the keyboard.
<u>Edit parameters</u>: double click on a block in the flow graph.
<u>Make connection</u>: click on the source port of one block, then click on the sink port of another block.
<u>Remove connection</u>: select the connection and press delete, or drag the connection.

* See the menu for other keyboard shortcuts.""")

COLORS_DIALOG_MARKUP_TMPL = """\
<b>Color Mapping</b>

#if $colors
	#set $max_len = max([len(color[0]) for color in $colors]) + 10
	#for $title, $color_spec in $colors
<span background="$color_spec"><tt>$($encode($title).center($max_len))</tt></span>
	#end for
#end if
"""

def TypesDialog(platform): MessageDialogHelper(
	type=gtk.MESSAGE_INFO,
	buttons=gtk.BUTTONS_CLOSE,
	title='Types',
	markup=Utils.parse_template(COLORS_DIALOG_MARKUP_TMPL, colors=platform.get_colors()))
