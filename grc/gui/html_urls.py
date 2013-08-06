
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
lst_blocks_lib=[]
lst_blocks_python=[]
lst_channels_lib=[]
lst_channels_python=[]
lst_analog_lib=[]
lst_analog_python=[]
lst_atsc_lib=[]
lst_atsc_python=[]
lst_audio_lib=[]
lst_audio_python=[]
lst_comedi_lib=[]
lst_comedi_python=[]
lst_digital_lib=[]
lst_digital_python=[]
lst_fcd_lib=[]
lst_fcd_python=[]
lst_fft_lib=[]
lst_fft_python=[]
lst_fec_lib=[]
lst_fec_python=[]
lst_filter_lib=[]
lst_filter_python=[]
lst_noaa_lib=[]
lst_noaa_python=[]
lst_pager_lib=[]
lst_pager_python=[]
lst_qtgui_lib=[]
lst_qtgui_python=[]
lst_trellis_lib=[]
lst_trellis_python=[]
lst_uhd_lib=[]
lst_uhd_python=[]
lst_utils_lib=[]
lst_utils_python=[]
lst_vocoder_lib=[]
lst_vocoder_python=[]
lst_wavelet_lib=[]
lst_wavelet_python=[]
lst_wxgui_lib=[]
lst_wxgui_python=[]


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
	global lst_blocks_lib
	global lst_blocks_python
	global lst_channels_lib
	global lst_channels_python
	global lst_analog_lib
	global lst_analog_python
	global lst_atsc_lib
	global lst_atsc_python
	global lst_audio_lib
	global lst_audio_python
	global lst_comedi_lib
	global lst_comedi_python
	global lst_digital_lib
	global lst_digital_python
	global lst_fcd_lib
	global lst_fcd_python
	global lst_fft_lib
	global lst_fft_python
	global lst_fec_lib
	global lst_fec_python
	global lst_filter_lib
	global lst_filter_python
	global lst_noaa_lib
	global lst_noaa_python
	global lst_pager_lib
	global lst_pager_python
	global lst_qtgui_lib
	global lst_qtgui_python
	global lst_trellis_lib
	global lst_trellis_python
	global lst_uhd_lib
	global lst_uhd_python
	global lst_utils_lib
	global lst_utils_python
	global lst_vocoder_lib
	global lst_vocoder_python
	global lst_wavelet_lib
	global lst_wavelet_python
	global lst_wxgui_lib
	global lst_wxgui_python
	path=gr.prefs().get_string('grc', 'source_code_base_uri', '').split(',')[0]
	
	while exitFlag==0:
		if network_connection() is True:
			try:
				links = lxml.html.parse(gr.prefs().get_string('grc', 'doxygen_base_uri', '').split(',')[1]+"annotated.html").xpath("//a/@href")
				for url in links: 
					lst_doxygen.append(url)
			except (IOError, AttributeError, IndexError):
				pass
			try:
				links = lxml.html.parse(gr.prefs().get_string('grc', 'sphinx_base_uri', '').split(',')[1]+"genindex.html").xpath("//a/@href")
				for url in links: 
					lst_sphinx.append(url)
			except (IOError, AttributeError, IndexError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-blocks/lib').xpath("//a/@href")
				for url in links: 
					lst_blocks_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-blocks/python/blocks').xpath("//a/@href")
				for url in links: 
					lst_blocks_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-channels/lib').xpath("//a/@href")
				for url in links: 
					lst_channels_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-channels/python/channels').xpath("//a/@href")
				for url in links: 
					lst_channels_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-analog/lib').xpath("//a/@href")
				for url in links:
					lst_analog_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-analog/python/analog').xpath("//a/@href")
				for url in links: 
					lst_analog_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-atsc/lib').xpath("//a/@href")
				for url in links: 
					lst_atsc_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-atsc/python/atsc').xpath("//a/@href")
				for url in links: 
					lst_atsc_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-audio/lib').xpath("//a/@href")
				for url in links: 
					lst_audio_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-audio/python/audio').xpath("//a/@href")
				for url in links: 
					lst_audio_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-comedi/lib').xpath("//a/@href")
				for url in links: 
					lst_comedi_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-comedi/python/comedi').xpath("//a/@href")
				for url in links: 
					lst_comedi_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-digital/lib').xpath("//a/@href")
				for url in links: 
					lst_digital_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-digital/python/digital').xpath("//a/@href")
				for url in links: 
					lst_digital_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-fcd/lib').xpath("//a/@href")
				for url in links: 
					lst_fcd_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-fcd/python/fcd').xpath("//a/@href")
				for url in links: 
					lst_fcd_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-fec/lib').xpath("//a/@href")
				for url in links: 
					lst_fec_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-fec/python/fec').xpath("//a/@href")
				for url in links: 
					lst_fec_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-fft/lib').xpath("//a/@href")
				for url in links: 
					lst_fft_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-fft/python/fft').xpath("//a/@href")
				for url in links: 
					lst_fft_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-filter/lib').xpath("//a/@href")
				for url in links: 
					lst_filter_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-filter/python/filter').xpath("//a/@href")
				for url in links: 
					lst_filter_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-noaa/lib').xpath("//a/@href")
				for url in links: 
					lst_noaa_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-noaa/python/noaa').xpath("//a/@href")
				for url in links: 
					lst_noaa_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-pager/lib').xpath("//a/@href")
				for url in links: 
					lst_pager_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-pager/python/pager').xpath("//a/@href")
				for url in links: 
					lst_pager_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-qtgui/lib').xpath("//a/@href")
				for url in links: 
					lst_qtgui_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-qtgui/python/qtgui').xpath("//a/@href")
				for url in links: 
					lst_qtgui_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-trellis/lib').xpath("//a/@href")
				for url in links: 
					lst_trellis_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-trellis/python/trellis').xpath("//a/@href")
				for url in links: 
					lst_trellis_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-uhd/lib').xpath("//a/@href")
				for url in links: 
					lst_uhd_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-uhd/python/uhd').xpath("//a/@href")
				for url in links: 
					lst_uhd_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-utils/lib').xpath("//a/@href")
				for url in links: 
					lst_utils_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-utils/python/utils').xpath("//a/@href")
				for url in links: 
					lst_utils_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-vocoder/lib').xpath("//a/@href")
				for url in links: 
					lst_vocoder_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-vocoder/python/vocoder').xpath("//a/@href")
				for url in links: 
					lst_vocoder_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-wavelet/lib').xpath("//a/@href")
				for url in links: 
					lst_wavelet_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-wavelet/python/wavelet').xpath("//a/@href")
				for url in links: 
					lst_wavelet_python.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-wxgui/lib').xpath("//a/@href")
				for url in links: 
					lst_wxgui_lib.append(url)
			except (IOError, AttributeError):
				pass
			try:
				links = lxml.html.parse(path+'/gr-wxgui/python/wxgui').xpath("//a/@href")
				for url in links: 
					lst_wxgui_python.append(url)
			except (IOError, AttributeError):
				pass
			exitFlag=1



			time.sleep(delay)
		
		
def url_lst(doc):
	if re.match(doc,'annotated.html'):
		return lst_doxygen
	if re.match(doc,'genindex.html'):
		return lst_sphinx
	if re.match(doc,'blocks'):
		return lst_blocks_lib
	if re.match(doc,'blocks_python'):
		return lst_blocks_python
	if re.match(doc,'channels'):
		return lst_channels_lib
	if re.match(doc,'channels_python'):
		return lst_channels_python
	if re.match(doc,'analog'):
		return lst_analog_lib
	if re.match(doc,'analog_python'):
		return lst_analog_python
	if re.match(doc,'atsc'):
		return lst_atsc_lib
	if re.match(doc,'atsc_python'):
		return lst_atsc_python
	if re.match(doc,'audio'):
		return lst_audio_lib
	if re.match(doc,'audio_python'):
		return lst_audio_python
	if re.match(doc,'comedi'):
		return lst_comedi_lib
	if re.match(doc,'comedi_python'):
		return lst_comedi_python
	if re.match(doc,'digital'):
		return lst_digital_lib
	if re.match(doc,'digital_python'):
		return lst_digital_python
	if re.match(doc,'fcd'):
		return lst_fcd_lib
	if re.match(doc,'fcd_python'):
		return lst_fcd_python
	if re.match(doc,'fec'):
		return lst_fec_lib
	if re.match(doc,'fec_python'):
		return lst_fec_python
	if re.match(doc,'fft'):
		return lst_fft_lib
	if re.match(doc,'fft_python'):
		return lst_fft_python
	if re.match(doc,'filter'):
		return lst_filter_lib
	if re.match(doc,'filter_python'):
		return lst_filter_python
	if re.match(doc,'noaa'):
		return lst_noaa_lib
	if re.match(doc,'noaa_python'):
		return lst_noaa_python
	if re.match(doc,'pager'):
		return lst_pager_lib
	if re.match(doc,'pager_python'):
		return lst_pager_python
	if re.match(doc,'qtgui'):
		return lst_qtgui_lib
	if re.match(doc,'qtgui_python'):
		return lst_qtgui_python
	if re.match(doc,'trellis'):
		return lst_trellis_lib
	if re.match(doc,'trellis_python'):
		return lst_trellis_python
	if re.match(doc,'uhd'):
		return lst_uhd_lib
	if re.match(doc,'uhd_python'):
		return lst_uhd_python
	if re.match(doc,'utils'):
		return lst_utils_lib
	if re.match(doc,'utils_python'):
		return lst_utils_python
	if re.match(doc,'vocoder'):
		return lst_vocoder_lib
	if re.match(doc,'vocoder_python'):
		return lst_vocoder_python
	if re.match(doc,'wavelet'):
		return lst_wavelet_lib
	if re.match(doc,'wavelet_python'):
		return lst_wavelet_python
	if re.match(doc,'wxgui'):
		return lst_wxgui_lib
	if re.match(doc,'wxgui_python'):
		return lst_wxgui_python
	else:
		return []



def network_connection():
	
	network=False
	try:
		response = urllib2.urlopen("http://google.com", None, 2.5)
		network=True
	
	except urllib2.URLError, e:
		   pass
	return network








