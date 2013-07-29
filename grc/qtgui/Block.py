from __future__ import division

from PyQt4.QtGui import *
from PyQt4.QtCore import Qt

from . Element import Element
from .FlowGraph import FlowGraph
from .. base import odict
import Utils
from Constants import \
    BLOCK_LABEL_PADDING, \
    PORT_SEPARATION, LABEL_SEPARATION, \
    PORT_BORDER_SEPARATION, POSSIBLE_ROTATIONS



BLOCK_MARKUP_TMPL="""\
#set $foreground = $block.is_valid() and 'black' or 'red'
<span foreground="$foreground" font_desc="Sans 8"><b>$encode($block.get_name())</b></span>"""


class Block(Element, QGraphicsRectItem):
    """The graphical signal block."""

    def __init__(self, parent=None, scence=None):
        """
        Block contructor.
        Add graphics related params to the block.
        """

        #add the position param
        self.get_params().append(self.get_parent().get_parent().Param(
            block=self,
            n=odict({
                'name': 'GUI Coordinate',
                'key': '_coordinate',
                'type': 'raw',
                'value': '(0, 0)',
                'hide': 'all',
            })
        ))
        self.get_params().append(self.get_parent().get_parent().Param(
            block=self,
            n=odict({
                'name': 'GUI Rotation',
                'key': '_rotation',
                'type': 'raw',
                'value': '0',
                'hide': 'all',
            })
        ))
        Element.__init__(self)

        x, y, w, h = 50, -40, 200, 150

        QGraphicsRectItem.__init__(self, parent, scence)

        if not isinstance(self.get_parent(), FlowGraph):
            return

        self.setPos(0, 0)
        self.setRect(0, 0, w, h)

        self.setFlags(QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsPanel)
        self.setBrush(QBrush(QColor(200, 200, 200)))

        self.text = QGraphicsTextItem(self)
        self.text.setTextWidth(w)
        self.updateLabel()


        #self.setG (Qt.ActionsContextMenu)
        #self.addActions((parent.main_window.menuEdit.actions()))

    def updateLabel(self):
        #display the params

        markups = [param.get_markup()
                   for param in self.get_params()
                   if param.get_hide() not in ('all', 'part')]

        self.text.setHtml('<b>{name}</b><br />{desc}'.format(
            name=Utils.parse_template(BLOCK_MARKUP_TMPL, block=self),
            desc='<br />'.join(markups)
        ))

    def setPos(self, *args):
        QGraphicsRectItem.setPos(self, *args)
        # FixMe: detect drag and drop of blocks
        #self.get_param('_coordinate').set_value(str(args))

    def rotate(self, rotation):
        QGraphicsRectItem.rotate(self, rotation)
        self.get_param('_rotation').set_value(str(self.rotation()))

    def setRotation(self, rot):
        QGraphicsRectItem.setRotation(self, rot)
        self.get_param('_rotation').set_value(str(rot))

    def testPorts(self):
        x, y, w, h = 50, -40, 200, 150
        PORT_H, PORT_W = 10, 10

        # source port(s)
        num_sink_ports = 3
        self.souce_ports = []
        for i in range(num_sink_ports):
            y_port = (i + 0.5) * h / num_sink_ports - PORT_H / 2
            port = QGraphicsRectItem(self)
            port.setBrush(QColor(255,255,255))
            port.setRect(-PORT_W, y_port, PORT_W, PORT_H)
            port.setFlag(QGraphicsItem.ItemIsFocusable)
            self.souce_ports.append(port)

        # sink port(s)
        num_source_ports = 4
        self.sink_ports = []
        for i in range(num_source_ports):
            y_port = (i + 0.5) * h / num_source_ports - PORT_H / 2
            port = QGraphicsRectItem(self)
            port.setBrush(QColor(255,255,255))
            port.setPos(w, 0)
            port.setRect(0, y_port, PORT_W, PORT_H)
            port.setFlag(QGraphicsItem.ItemIsFocusable)

            self.sink_ports.append(port)


        print port.parentItem()