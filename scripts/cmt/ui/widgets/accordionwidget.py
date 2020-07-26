"""Simplified version of Blur's Accordion Widget

Example Usage
=============

::

    from PySide2.QtWidgets import QWidget, QVBoxLayout, QPushButton
    from cmt.ui.widgets import AccordionWidget

    def build_frame():
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QPushButton("Test"))
        layout.addWidget(QPushButton("Test"))
        return widget

    widget = AccordionWidget()
    widget.addItem("A", build_frame())
    widget.addItem("B", build_frame())
    widget.show()

"""

from PySide2.QtCore import Qt, QRect, QPoint
from PySide2.QtGui import QBrush, QColor, QPolygon, QPainter, QPalette, QPen
from PySide2.QtWidgets import QGroupBox, QVBoxLayout, QScrollArea, QSizePolicy, QWidget
import os.path


class AccordionItem(QGroupBox):
    """Collapsible widget"""

    def __init__(self, title, widget, parent=None):
        super(AccordionItem, self).__init__(parent)

        # create the layout
        layout = QVBoxLayout()
        layout.addWidget(widget)

        self.setLayout(layout)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # create custom properties
        self._widget = widget
        self._collapsed = False
        self._collapsible = True
        self._clicked = False

        # set common properties
        self.setTitle(title)

    def expandCollapseRect(self):
        return QRect(0, 0, self.width(), 20)

    def mouseReleaseEvent(self, event):
        if self._clicked and self.expandCollapseRect().contains(event.pos()):
            self.toggleCollapsed()
            event.accept()
        else:
            event.ignore()

        self._clicked = False

    def mouseMoveEvent(self, event):
        event.ignore()

    def mousePressEvent(self, event):
        # determine if the expand/collapse should occur
        if event.button() == Qt.LeftButton and self.expandCollapseRect().contains(
            event.pos()
        ):
            self._clicked = True
            event.accept()
        else:
            event.ignore()

    def isCollapsed(self):
        return self._collapsed

    def isCollapsible(self):
        return self._collapsible

    def __drawTriangle(self, painter, x, y):
        brush = QBrush(QColor(255, 255, 255, 160), Qt.SolidPattern)
        if not self.isCollapsed():
            tl, tr, tp = (
                QPoint(x + 9, y + 8),
                QPoint(x + 19, y + 8),
                QPoint(x + 14, y + 13.0),
            )
            points = [tl, tr, tp]
            triangle = QPolygon(points)
        else:
            tl, tr, tp = (
                QPoint(x + 11, y + 6),
                QPoint(x + 16, y + 11),
                QPoint(x + 11, y + 16.0),
            )
            points = [tl, tr, tp]
            triangle = QPolygon(points)
        currentBrush = painter.brush()
        painter.setBrush(brush)
        painter.drawPolygon(triangle)
        painter.setBrush(currentBrush)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(painter.Antialiasing)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)

        x = self.rect().x()
        y = self.rect().y()
        w = self.rect().width() - 1
        h = self.rect().height() - 1

        # draw the text
        painter.drawText(x + 33, y + 3, w, 16, Qt.AlignLeft | Qt.AlignTop, self.title())

        painter.setRenderHint(QPainter.Antialiasing, False)

        self.__drawTriangle(painter, x, y)

        # draw the borders - top
        headerHeight = 20

        headerRect = QRect(x + 1, y + 1, w - 1, headerHeight)
        headerRectShadow = QRect(x - 1, y - 1, w + 1, headerHeight + 2)

        # Highlight
        pen = QPen(self.palette().color(QPalette.Light))
        pen.setWidthF(0.4)
        painter.setPen(pen)

        painter.drawRect(headerRect)
        painter.fillRect(headerRect, QColor(255, 255, 255, 18))

        # Shadow
        pen.setColor(self.palette().color(QPalette.Dark))
        painter.setPen(pen)
        painter.drawRect(headerRectShadow)

        if not self.isCollapsed():
            # draw the lover border
            pen = QPen(self.palette().color(QPalette.Dark))
            pen.setWidthF(0.8)
            painter.setPen(pen)

            offSet = headerHeight + 3
            bodyRect = QRect(x, y + offSet, w, h - offSet)
            bodyRectShadow = QRect(x + 1, y + offSet, w + 1, h - offSet + 1)
            painter.drawRect(bodyRect)

            pen.setColor(self.palette().color(QPalette.Light))
            pen.setWidthF(0.4)
            painter.setPen(pen)

            painter.drawRect(bodyRectShadow)

        painter.end()

    def setCollapsed(self, state=True):
        if self.isCollapsible():
            self.parent().setUpdatesEnabled(False)

            self._collapsed = state

            if state:
                self.setMinimumHeight(22)
                self.setMaximumHeight(22)
                self.widget().setVisible(False)
            else:
                self.setMinimumHeight(0)
                self.setMaximumHeight(1000000)
                self.widget().setVisible(True)

            self.parent().setUpdatesEnabled(True)

    def setCollapsible(self, state=True):
        self._collapsible = state

    def toggleCollapsed(self):
        self.setCollapsed(not self.isCollapsed())

    def widget(self):
        return self._widget


class AccordionWidget(QScrollArea):
    """A container widget for creating expandable and collapsible components"""

    def __init__(self, parent=None):
        super(AccordionWidget, self).__init__(parent)

        self.setFrameShape(QScrollArea.NoFrame)
        self.setAutoFillBackground(False)
        self.setWidgetResizable(True)

        widget = QWidget(self)

        layout = QVBoxLayout()
        layout.addStretch(1)
        layout.setSpacing(0)
        widget.setLayout(layout)

        self.setWidget(widget)

    def addItem(self, title, widget, collapsed=False):
        self.setUpdatesEnabled(False)
        item = AccordionItem(title, widget, parent=self)
        layout = self.widget().layout()
        layout.insertWidget(layout.count() - 1, item)
        layout.setStretchFactor(item, 0)

        if collapsed:
            item.setCollapsed(collapsed)

        self.setUpdatesEnabled(True)
        return item

    def clear(self):
        self.setUpdatesEnabled(False)
        layout = self.widget().layout()
        while layout.count() > 1:
            item = layout.itemAt(0)

            # remove the item from the layout
            w = item.widget()
            layout.removeItem(item)

            # close the widget and delete it
            w.close()
            w.deleteLater()

        self.setUpdatesEnabled(True)

    def count(self):
        return self.widget().layout().count() - 1

    def itemAt(self, index):
        layout = self.widget().layout()

        if 0 <= index < layout.count() - 1:
            return layout.itemAt(index).widget()
        return None
