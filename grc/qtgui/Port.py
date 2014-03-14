from PyQt4.QtGui import *
from PyQt4.QtCore import Qt

import Utils

PORT_MARKUP_TMPL="""\
<span foreground="black" font_desc="Sans 7.5">$encode($port.get_name())</span>"""


class Port(QGraphicsRectItem):

    def __init__(self, parent=None, scence=None):
        """
        Port contructor.
        Add graphics related params to the block.
        """
        PORT_H, PORT_W = 10, 10

        QGraphicsRectItem.__init__(self, parent, scence)
        #self.setRect(-PORT_W, -PORT_H, PORT_W, PORT_H)
        self.setRect(100, 20, PORT_W, PORT_H)
        self.setFlags(QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsPanel)
        self.setBrush(QColor(255, 255, 0))

        self.text = QGraphicsTextItem(self)
        #print "you should see something now!"

    def updateLabel(self):
        print "Port updateLabel"
        label = Utils.parse_template(PORT_MARKUP_TMPL, port=self)
        print "this is the label = " + label
        self.text.setHtml('<b>{label}</b>'.format(
            label=label
        ))
        print self.shape().boundingRect()
        rect = self.text.shape().boundingRect()
        self.setRect(0, 0, rect.width(), rect.height())
        #
        ##markups = [param.get_markup()
        ## for param in self.get_params()
        ## if param.get_hide() not in ('all', 'part')]
        #
        #self.text.setHtml('<b>{name}</b><br />{desc}'.format(
        # name=Utils.parse_template(PORT_MARKUP_TMPL, block=self),
        # desc='<br />'.join(markups)
        #))
        #rect = self.text.shape().boundingRect()
        #self.setRect(0, 0, rect.width(), rect.height())

    def create_shapes(self):
        pass

    def modify_height(self, start_height):
        return 0

    def create_labels(self):
        pass

    def draw(self):
        print "this should be drawn"

    def get_connector_coordinate(self):
        return (10, 10)

    def get_connector_direction(self):
        """
Get the direction that the socket points: 0,90,180,270.
This is the rotation degree if the socket is an output or
the rotation degree + 180 if the socket is an input.

Returns:
the direction in degrees
"""
        if self.is_source(): return self.get_rotation()
        elif self.is_sink(): return (self.get_rotation() + 180)%360

    def get_connector_length(self):
        """
Get the length of the connector.
The connector length increases as the port index changes.

Returns:
the length in pixels
"""
        return self._connector_length

    def get_rotation(self):
        """
Get the parent's rotation rather than self.

Returns:
the parent's rotation
"""
        return self.get_parent().get_rotation()

    def move(self, delta_coor):
        """
Move the parent rather than self.

Args:
delta_corr: the (delta_x, delta_y) tuple
"""
        self.get_parent().move(delta_coor)

    def rotate(self, direction):
        """
Rotate the parent rather than self.

Args:
direction: degrees to rotate
"""
        self.get_parent().rotate(direction)

    def get_coordinate(self):
        """
Get the parent's coordinate rather than self.

Returns:
the parents coordinate
"""
        return self.get_parent().get_coordinate()

    def set_highlighted(self, highlight):
        """
Set the parent highlight rather than self.

Args:
highlight: true to enable highlighting
"""
        self.get_parent().set_highlighted(highlight)

    def is_highlighted(self):
        """
Get the parent's is highlight rather than self.

Returns:
the parent's highlighting status
"""
        return self.get_parent().is_highlighted()