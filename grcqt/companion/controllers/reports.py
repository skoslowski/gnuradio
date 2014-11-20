class ReportsController(object):
    def __init__(self, view):

        # Save a reference to the view (from MainController)
        # Also save reference to text object
        self.view = view
        self.text = view.getText()

    ############################################################
    # Report Window
    ############################################################

    def add_line(self, line):
        self.text.append('spam: spam spam spam spam')
            
    def clear(self):
        self.text.clear()



    ############################################################
    # Pages: create and close
    ############################################################

    def new_page(self, file_path='', show=False):
        pass

    def close_pages(self):
        pass

    def close_page(self, index=None):
        pass
    ############################################################
    # Misc
    ############################################################

    def closeEvent(self, event):
        pass

    def update(self):
        pass

    def get_page(self):
        pass

    def get_flow_graph(self):
        pass

    ############################################################
    # Helpers
    ############################################################

    def _save_changes(self):
       pass



