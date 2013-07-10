#!/usr/bin/env python

from PyQt4.QtGui import *
from PyQt4.QtCore import Qt, QMimeData

from . ui_BlockLibrary import Ui_blockLibraryDock

NAME_INDEX = 0
KEY_INDEX = 1
DOC_INDEX = 2

class Block(object):
    def __init__(self, name, key):
        self.name = name
        self.key = key

    def get_name(self):
        return self.name

    def get_key(self):
        return self.key


class BlockLibrary(QDockWidget, Ui_blockLibraryDock):

    def __init__(self, parent, platform, get_flow_graph):
        QDockWidget.__init__(self, parent)
        self.setupUi(self)

        self.platform = platform
        self.get_flow_graph = get_flow_graph

        self.blockTree.activated.connect(self._add_selected_block)
        setattr(self.blockTree, 'mimeTypes', lambda: "text/plain")
        setattr(self.blockTree, 'mimeData', _encode_mime_data)

        # ToDo: setup drag and drop

        self.clear()
        #add blocks and categories
        #self.platform.load_block_tree(self)

        self.add_block('cat A', Block('test', 'testID'))
        self.add_block('cat B', Block('test2', 'testID2'))
        self.add_block('cat C')
        self.add_block('cat C/cat D', Block('test3', 'testID4'))
        self.add_block('cat A', Block('test4', 'testID'))


    def clear(self):
        self.blockTree.clear()
        #map (sub)categories to items, automatic mapping for root
        self._categoryItems = {tuple(): self.blockTree}


    ############################################################
    ## Block Tree Methods
    ############################################################
    def add_block(self, category, block=None):
        """
        Add a block with category to this selection window.
        Add only the category when block is None.

        Args:
            category: the category list or path string
            block: the block object or None
        """
        if isinstance(category, str):
            category = category.split('/')

        category = tuple(filter(lambda x: x, category)) #tuple is hashable

        #add category and all sub categories
        for i, cat_name in enumerate(category):
            sub_category = category[:i+1]
            if sub_category not in self._categoryItems:
                parent = self._categoryItems[category[:i]]
                item = QTreeWidgetItem(parent, (cat_name, '', ''))
                item.setFlags(item.flags() & ~Qt.ItemIsDragEnabled)
                self._categoryItems[sub_category] = item
        #add block
        if block is not None:
            QTreeWidgetItem(self._categoryItems[category],
                            (block.get_name(), block.get_key(), 'Doc'))



    ############################################################
    ## Helper Methods
    ############################################################

    def _add_selected_block(self, index):
        """
        Add the selected block with the given key to the flow graph.
        """
        key = self.blockTree.itemFromIndex(index).text(KEY_INDEX)
        if key:
            print key
            #self.get_flow_graph().add_new_block(key)


def _encode_mime_data(indexes):
    mimeData = QMimeData()
    mimeData.setText(indexes[0].text(KEY_INDEX))
    return mimeData