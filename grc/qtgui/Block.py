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

from .. base.Block import Block as _Block


BLOCK_MARKUP_TMPL="""\
#set $foreground = $block.is_valid() and 'black' or 'red'
<span foreground="$foreground" font_desc="Sans 8"><b>$encode($block.get_name())</b></span>"""


class Block(_Block, QGraphicsRectItem):
    """The graphical signal block."""

    def __init__(self, flow_graph, n):
        """
        Block constructor.
        Add graphics related params to the block.
        """

        _Block.__init__(
            self,
            flow_graph=flow_graph,
            n=n,
        )

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
        QGraphicsRectItem.__init__(self, None)

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

    def updateLabel(self):
        #display the params
        for port in self.get_ports_gui():
            port.updateLabel()
            port.setParentItem(self)

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
