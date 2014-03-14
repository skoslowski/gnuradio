from __future__ import division

from PyQt4.QtGui import *
from PyQt4.QtCore import Qt

from .. base import odict
from . Element import Element
from . FlowGraph import FlowGraph
from . Port import Port
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
        Block constructor.
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
        QGraphicsRectItem.__init__(self, parent, scence)

        if not isinstance(self.get_parent(), FlowGraph):
            return

        self.setFlags(QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsPanel)
        self.setBrush(QBrush(QColor(200, 200, 200)))

        self.text = QGraphicsTextItem(self)
        #self.text.setTextWidth(w)
        self.updateLabel()

        #self.setG (Qt.ActionsContextMenu)
        #self.addActions((parent.main_window.menuEdit.actions()))
        for port in self.get_ports_gui():
            port.updateLabel()

        #self.ports = []
        #PORT_H = 20
        #PORT_W = 20
        #for i in range(3):
        # y_port = (i + 0.5) * h / 3 - PORT_H / 2
        # port = QGraphicsRectItem(self)
        # #port.setBrush(QColor(255,255,255))
        # #port.setPos(w, 0)
        # port.setRect(0, y_port, PORT_W, PORT_H)
        ## port.setFlag(QGraphicsItem.ItemIsFocusable)
        ## self.ports.append(port)
        self.testPorts()

    def updateLabel(self):
        #display the params
        self.update()

        markups = [param.get_markup()
                   for param in self.get_params()
                   if param.get_hide() not in ('all', 'part')]

        self.text.setHtml('<b>{name}</b><br />{desc}'.format(
            name=Utils.parse_template(BLOCK_MARKUP_TMPL, block=self),
            desc='<br />'.join(markups)
        ))
        self.updateSize()

    def updateSize(self):
        width = self.text.shape().boundingRect().width()
        height = max(*(
            # text height
            [self.text.shape().boundingRect().height()] +
            # port height
            [2 * PORT_BORDER_SEPARATION +  # space above and below
             sum(port.H for port in ports) +  # ports themselves
             PORT_SEPARATION * (len(ports) - 1)  # port spacing
                for ports in (self.get_sources_gui(), self.get_sinks_gui())]  # for ins and outs
        ))
        self.setRect(0, 0, width, height)
        # ToDo: Relocate Ports

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

    def set_highlighted(self, foo):
        pass

    def testPorts(self):
        x, y, w, h = 50, -40, 200, 150
        PORT_H, PORT_W = 10, 10

        ports = self.get_ports_gui()
        print "ports: " + str(len(ports) )

        for port in ports:
            print "ports type is" + str(type(port))

        #print "src ports = " + str()

        self.source_ports = []
        for port in ports:
            self.source_ports.append(port)

        return
        # source port(s)
        num_sink_ports = 3
        self.source_ports = []
        for i in range(num_sink_ports):
            y_port = (i + 0.5) * h / num_sink_ports - PORT_H / 2
            port = QGraphicsRectItem(self)
            port.setBrush(QColor(255,255,255))
            port.setRect(-PORT_W, y_port, PORT_W, PORT_H)
            port.setFlag(QGraphicsItem.ItemIsFocusable)
            self.source_ports.append(port)

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