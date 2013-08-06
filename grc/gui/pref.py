from gnuradio import gr
class myclass:
	def __init__(self):
		print "-----------------------------------------------"
		print gr.prefs().get_string('my', 'cc_editor', 'Gedit')
		print "-----------------------------------------------"
