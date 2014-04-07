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
<span foreground="$foreground" font_desc="Sans 7"><b>$encode($block.get_name())</b></span>"""


class Block(QGraphicsRectItem, _Block):
    """The graphical signal block."""

    def __init__(self, flow_graph, n):
        """
        Block constructor.
        Add graphics related params to the block.
        """

        QGraphicsRectItem.__init__(self)
        _Block.__init__(self, flow_graph,  n)

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

        if not isinstance(self.get_parent(), FlowGraph):
            return

        self.setFlags(QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsScenePositionChanges)
        self.setBrush(QBrush(QColor(230, 230, 230)))

        self.text = QGraphicsTextItem(self)
        self.refresh()

        #self.setG (Qt.ActionsContextMenu)
        #self.addActions((parent.main_window.menuEdit.actions()))

    def refresh(self):
        # display the params
        markups = [param.get_markup()
                   for param in self.get_params()
                   if param.get_hide() not in ('all', 'part')]
        self.text.setHtml('<b>{name}</b><br />{desc}'.format(
            name=Utils.parse_template(BLOCK_MARKUP_TMPL, block=self),
            desc='<br />'.join(markups)
        ))
        # update port names
        for port in self.get_ports_gui():
            port.updateLabel()

        text_height = self.text.shape().boundingRect().height()
        sink_ports_height, source_ports_height = [
            # padding top/bottom
            2 * PORT_BORDER_SEPARATION +
            # total height of all ports
            sum(port.boundingRect().height() for port in ports) +
            # space between ports
            PORT_SEPARATION * (len(ports) - 1)

            for ports in (self.get_sinks_gui(), self.get_sources_gui())
        ]

        width = self.text.shape().boundingRect().width()
        height = max(sink_ports_height, text_height, source_ports_height)

        self.prepareGeometryChange()
        self.setRect(0, 0, width, height)

        port_y = PORT_BORDER_SEPARATION + (height - sink_ports_height) / 2.0
        for sink_port in self.get_sinks_gui():
            sink_port.updateSize(port_y)
            port_y += sink_port.boundingRect().height() + PORT_SEPARATION

        port_y = PORT_BORDER_SEPARATION + (height - source_ports_height) / 2.0
        for source_port in self.get_sources_gui():
            source_port.updateSize(port_y)
            port_y += source_port.boundingRect().height() + PORT_SEPARATION

    def itemChange(self, change, value):
        """Block change handler"""
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # update connections
            for port in self.get_ports_gui():
                for connection in port.get_connections():
                    connection.refresh()
        # propagate
        return QGraphicsItem.itemChange(self, change, value)

    def dropEvent(self, event):
        self.get_param('_coordinate').set_value([self.pos().x(), self.pos().y()])

    def rotate(self, rotation):
        QGraphicsRectItem.rotate(self, rotation)
        self.get_param('_rotation').set_value(self.rotation())

    def setRotation(self, rotation):
        QGraphicsRectItem.setRotation(self, rotation)
        self.get_param('_rotation').set_value(self.rotation())

    def set_highlighted(self, foo):
        pass
