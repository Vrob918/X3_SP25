#utilized ChatGPT
#utilized PipeNetwork files from Smay
import math
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui
from PyQt5.QtGui import QPainterPath
from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QGraphicsLineItem
from copy import deepcopy as dc

class Position():
    """
    A utility class representing a point or vector in 3D space.
    Supports arithmetic operations and common vector operations like
    magnitude, normalization, and angle calculation.
    """
    def __init__(self, pos=None, x=None, y=None, z=None):
        """Initialize the Position. You can pass a tuple (x, y, z) or individual x, y, z values."""
        # set default values
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        # unpack position from a tuple if given
        if pos is not None:
            self.x, self.y, self.z = pos
        # override the x,y,z defaults if they are given as arguments
        self.x = x if x is not None else self.x
        self.y = y if y is not None else self.y
        self.z = z if z is not None else self.z
        self.pt = qtc.QPointF(self.x, self.y)

    # region operator overloads $NEW$ 4/7/21
    def __add__(self, other):
        """Return a new Position that is the elementwise sum of this and another."""
        return Position((self.x + other.x, self.y + other.y, self.z + other.z))

    def __iadd__(self, other):
        """Add another Position or scalar to this one in place."""
        if other in (float, int):
            self.x += other
            self.y += other
            self.z += other
            return self
        if isinstance(other, Position):
            self.x += other.x
            self.y += other.y
            self.z += other.z
            return self

    def __sub__(self, other):
        """Return a new Position representing this minus another."""
        return Position((self.x - other.x, self.y - other.y, self.z - other.z))

    def __isub__(self, other):
        """Subtract another Position or scalar from this one in place."""
        if other in (float, int):
            self.x -= other
            self.y -= other
            self.z -= other
            return self
        if isinstance(other, Position):
            self.x -= other.x
            self.y -= other.y
            self.z -= other.z
            return self

    def __mul__(self, other):
        """Multiply by a scalar or perform elementwise product with another Position."""
        if isinstance(other, (float, int)):
            return Position((self.x * other, self.y * other, self.z * other))
        if isinstance(other, Position):
            return Position((self.x * other.x, self.y * other.y, self.z * other.z))

    def __rmul__(self, other):
        """Allow scalar * Position by deferring to __mul__."""
        return self * other

    def __imul__(self, other):
        """Multiply this Position in place by a scalar."""
        if isinstance(other, (float, int)):
            self.x *= other
            self.y *= other
            self.z *= other
            return self

    def __truediv__(self, other):
        """Return a new Position divided by the given scalar."""
        if isinstance(other, (float, int)):
            return Position((self.x / other, self.y / other, self.z / other))

    def __idiv__(self, other):
        """Divide this Position in place by the given scalar."""
        if isinstance(other, (float, int)):
            self.x /= other
            self.y /= other
            self.z /= other
            return self

    def __round__(self, n=None):
        """Return a new Position with each coordinate rounded to n decimals."""
        if n is not None:
            return Position(x=round(self.x, n), y=round(self.y, n), z=round(self.z, n))
        return self
    # endregion

    def set(self, strXYZ=None, tupXYZ=None, SI=True):
        """Update the coordinates from a string 'x,y,z' or a tuple, applying unit scaling if needed."""
        lenCF = 1 if SI else 3.3
        if strXYZ is not None:
            cells = strXYZ.replace('(', '').replace(')', '').strip().split(',')
            x, y, z = float(cells[0]), float(cells[1]), float(cells[2])
            self.x = lenCF * x
            self.y = lenCF * y
            self.z = lenCF * z
        elif tupXYZ is not None:
            x, y, z = tupXYZ
            self.x = lenCF * x
            self.y = lenCF * y
            self.z = lenCF * z

    def getTup(self):
        """Return this Position as an (x, y, z) tuple."""
        return (self.x, self.y, self.z)

    def getStr(self, nPlaces=3, SI=True):
        """Return a formatted string of the coordinates, rounded to nPlaces and optionally scaled."""
        lenCF = 1 if SI else 3.3
        return '{}, {}, {}'.format(
            round(self.x * lenCF, nPlaces),
            round(self.y * lenCF, nPlaces),
            round(self.z * lenCF, nPlaces)
        )

    def mag(self):
        """Compute and return the Euclidean magnitude of the vector."""
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5

    def normalize(self):
        """Convert this vector to unit length (3D) if its magnitude is nonzero."""
        length = self.mag()
        if length > 0.0:
            self.__idiv__(length)

    def normalize2D(self):
        """Normalize only the x and y components, treating this as a 2D vector."""
        self.z = 0.0
        self.normalize()

    def getAngleRad(self):
        """Return the angle of this Position in the XY plane, in radians."""
        length = self.mag()
        if length <= 0.0:
            return 0
        angle = math.acos(self.x / length)
        return angle if self.y >= 0.0 else 2.0 * math.pi - angle

    def getAngleDeg(self):
        """Return the angle of this Position in the XY plane, in degrees."""
        return 180.0 / math.pi * self.getAngleRad()

    def midPt(self, p2=None):
        """Compute the midpoint between this Position and another."""
        return Position(
            x=self.x + 0.5 * (p2.x - self.x),
            y=self.y + 0.5 * (p2.y - self.y),
            z=self.z + 0.5 * (p2.z - self.z)
        )

class circuitNode:
    """A connection point in the circuit, storing its name and 2D coordinates for drawing."""
    def __init__(self, name='none', x=0, y=0):
        """Initialize the node with a name, position, and mark it as drawable."""
        self.name = name
        self.position = Position((x, y, 0))
        self.draw = True

class resistor:
    """An electrical resistor element, defined by its resistance and endpoint node names."""
    def __init__(self, name='none', R=10, node1Name='a', node2Name='b'):
        """Initialize the resistor with a label, resistance value (Ohms), and two node connections."""
        self.name = name
        self.R = R
        self.node1Name = node1Name
        self.node2Name = node2Name

class inductor:
    """An electrical inductor element, defined by its inductance and endpoint node names."""
    def __init__(self, name='none', L=20, node1Name='a', node2Name='b'):
        """Initialize the inductor with a label, inductance value (Henrys), and two node connections."""
        self.name = name
        self.L = L
        self.node1Name = node1Name
        self.node2Name = node2Name

class QGraphicsArcItem(qtw.QGraphicsEllipseItem):
    """A custom graphics item that renders only the perimeter arc of an ellipse."""
    def paint(self, painter, option, widget):
        """Override to draw the ellipse’s arc instead of filling a wedge."""
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawArc(self.rect(), self.startAngle(), self.spanAngle())

class capacitor:
    """An electrical capacitor element, defined by its capacitance and endpoint node names."""
    def __init__(self, name='none', C=0.05, node1Name='a', node2Name='b'):
        """Initialize the capacitor with a label, capacitance value (Farads), and two node connections."""
        self.name = name
        self.C = C
        self.node1Name = node1Name
        self.node2Name = node2Name

class wire:
    """A simple conductive link between two circuit nodes without any impedance."""
    def __init__(self, name='none', node1Name='a', node2Name='b'):
        """Initialize the wire with a label and its two endpoint node names."""
        self.name = name
        self.node1Name = node1Name
        self.node2Name = node2Name

class voltageSource:
    """Ideal voltage source element, defined by a label and two terminal nodes."""

    def __init__(self, name='none', node1Name='a', node2Name='2'):
        """Initialize the voltage source with its name and the names of its two connection nodes."""
        self.name = name
        self.node1Name = node1Name
        self.node2Name = node2Name
#endreigon

#region circuit MVC
class circuitModel():
    """Stores all circuit elements and nodes in lists for modeling and lookup."""
    def __init__(self):
        """Set up empty lists for nodes, resistors, capacitors, inductors, voltage sources, and wires."""
        self.nodes=[]
        self.resistors=[]
        self.capacitors=[]
        self.inductors=[]
        self.voltageSources=[]
        self.wires=[]

    def getNode(self, name=None):
        """Return the circuitNode with the matching name, or None if not found."""
        for n in self.nodes:
            if n.name == name:
                return n

class circuitView():
    def __init__(self, dw=None):
        """Initialize the view: bind display widgets if provided, configure drawing tools,
        set up the scene and grid, and establish default scale, zoom, and element sizing."""
        if dw is not None:
            self.setWidgets(dw)
        self.setupPensAndBrushes()
        self.setupScene()
        self.drawAGrid()
        self.scale=2.0
        self.Zoom=1.0
        self.elementFraction = 1/2
    def setupPensAndBrushes(self):
         #copied from pipe network program
        self.penPipe = qtg.QPen(qtc.Qt.darkGray)
        self.penPipe.setWidth(4)
        #a fine black pen
        self.penNode = qtg.QPen(qtc.Qt.black)
        self.penNode.setStyle(qtc.Qt.SolidLine)
        self.penNode.setWidth(1)

        #a fine black pen
        self.penVS = qtg.QPen(qtc.Qt.black)
        self.penVS.setStyle(qtc.Qt.SolidLine)
        self.penVS.setWidth(1)

        #a medium black pen
        self.penConnect = qtg.QPen(qtc.Qt.black)
        self.penConnect.setStyle(qtc.Qt.SolidLine)
        self.penConnect.setWidth(2)

        #a pen for the grid lines
        self.penGridLines = qtg.QPen()
        self.penGridLines.setWidth(1)
        self.penGridLines.setColor(qtg.QColor.fromHsv(197, 144, 228, alpha=25))
        #now make some brushes
        #build a brush for filling with solid red
        self.brushFill = qtg.QBrush(qtc.Qt.darkRed)
        self.brushVS = qtg.QBrush(qtg.QColor.fromHsv(0, 0, 128, alpha=25))
        # a brush that makes a hatch pattern
        self.brushNode = qtg.QBrush(qtc.Qt.black)
        # a brush for the background of the grid
        self.brushGrid = qtg.QBrush(qtg.QColor.fromHsv(87, 98, 245, alpha=128))
        # the scene where circuit objects are drawn
        self.scene = qtw.QGraphicsScene()
        # endregion

    def setWidgets(self, dw):
        self.gv_Main, self.lineEdit, self.form = dw

    def setupScene(self):
        """Initialize the graphics scene, set its bounds, enable event filtering and mouse tracking, and attach it to the view."""
        self.scene = qtw.QGraphicsScene()
        self.scene.setObjectName("MyScene")
        self.scene.setSceneRect(-200, -200, 400, 400)  # define scene coordinates: x-left, y-top, width, height
        self.scene.installEventFilter(self.form)  # route scene events (e.g. mouse) through the form’s filter
        self.gv_Main.setMouseTracking(True)  # allow cursor movement events over the view
        self.gv_Main.setScene(self.scene)  # bind this scene to the graphics view widget

    def setZoom(self):
        """Reset any existing transformations and apply the current zoom factor to the graphics view."""
        self.gv_Main.resetTransform()  # clear previous scaling/rotation
        self.gv_Main.scale(self.Zoom, self.Zoom)  # scale view horizontally and vertically by Zoom

    def drawAGrid(self, DeltaX=5, DeltaY=5, Height=200, Width=200, CenterX=0, CenterY=0):
        """Draw a reference grid and optional background fill across the scene with given spacing."""
        # Choose the pen for grid lines and the brush for the background fill
        Pen = self.penGridLines
        Brush = self.brushGrid

        # Determine grid dimensions, defaulting to the scene rectangle if parameters are None
        height = self.scene.sceneRect().height() if Height is None else Height
        width = self.scene.sceneRect().width() if Width is None else Width

        # Calculate the left/right/top/bottom boundaries in scene coordinates
        left = self.scene.sceneRect().left() if CenterX is None else (CenterX - width / 2.0)
        right = self.scene.sceneRect().right() if CenterX is None else (CenterX + width / 2.0)
        top = -self.scene.sceneRect().top() if CenterY is None else (-CenterY + height / 2.0)
        bottom = -self.scene.sceneRect().bottom() if CenterY is None else (-CenterY - height / 2.0)

        # Grid spacing in X and Y
        Dx = DeltaX
        Dy = DeltaY

        # Fallback in case no pen was set
        pen = qtg.QPen() if Pen is None else Pen

        # Draw the background rectangle if a brush is provided
        if Brush is not None:
            rect = qtw.QGraphicsRectItem(left, -top, width, height)
            rect.setBrush(Brush)
            rect.setPen(pen)
            self.scene.addItem(rect)

        # Draw vertical lines at each X interval
        x = left
        while x <= right:
            lVert = qtw.QGraphicsLineItem(x, top, x, bottom)
            lVert.setPen(pen)
            self.scene.addItem(lVert)
            x += Dx

        # Draw horizontal lines at each Y interval
        y = bottom
        while y <= top:
            lHor = qtw.QGraphicsLineItem(left, -y, right, -y)
            lHor.setPen(pen)
            self.scene.addItem(lHor)
            y += Dy

    def drawCircuit(self, Model=circuitModel()):
        """Iterate through all elements in the given model and draw each on the scene."""
        # Draw each node as a circle if its draw flag is set
        for n in Model.nodes:
            if n.draw:
                self.drawACircle(
                    centerX=n.position.x * self.scale,
                    centerY=n.position.y * self.scale,
                    Radius=1 * self.scale,
                    brush=self.brushNode,
                    pen=self.penNode,
                    tooltip=n.name
                )
        # Draw each wire as a straight line
        for w in Model.wires:
            self.drawWire(w, Model=Model)
        # Draw each voltage source symbol
        for V in Model.voltageSources:
            self.drawVoltageSource(V, Model=Model)
        # Draw each resistor zigzag symbol
        for R in Model.resistors:
            self.drawResistor(R, Model=Model)
        # Draw each capacitor plate symbol
        for C in Model.capacitors:
            self.drawCapacitor(C, Model=Model)
        # Draw each inductor coil symbol
        for L in Model.inductors:
            self.drawInductor(L, Model=Model)

    def drawVoltageSource(self, V=voltageSource(), Model=circuitModel()):
        """Render a voltage source between two nodes, showing its circular symbol, polarity marks, and connection leads."""
        # Look up the start and end nodes by name
        n1 = Model.getNode(V.node1Name)
        n2 = Model.getNode(V.node2Name)

        # Compute the vector between nodes and find the center point scaled for drawing
        vec = n2.position - n1.position
        center = n1.position.midPt(n2.position) * self.scale

        # Determine the drawing radius based on distance and elementFraction
        dist = self.scale * vec.mag()
        radius = dist * self.elementFraction / 2

        # Draw the circular body of the voltage source
        self.drawACircle(
            centerX=center.x,
            centerY=center.y,
            Radius=radius,
            brush=self.brushVS,
            pen=self.penConnect,
            tooltip=V.name
        )

        # Draw the '+' and '-' polarity markers on the circle
        self.drawALine(
            StartPt=Position(x=center.x - radius / 3, y=center.y - radius / 3),
            EndPt=Position(x=center.x + radius / 3, y=center.y - radius / 3),
            Pen=self.penConnect
        )
        self.drawALine(
            StartPt=Position(x=center.x - radius / 3, y=center.y + radius / 3),
            EndPt=Position(x=center.x + radius / 3, y=center.y + radius / 3),
            Pen=self.penConnect
        )
        self.drawALine(
            StartPt=Position(x=center.x, y=center.y),
            EndPt=Position(x=center.x, y=center.y + 2 * radius / 3),
            Pen=self.penConnect
        )

        # Draw the connecting leads from each node to the source symbol
        self.drawALine(
            StartPt=n1.position * self.scale,
            EndPt=(n1.position + (1 - self.elementFraction) / 2 * vec) * self.scale,
            Pen=self.penConnect
        )
        self.drawALine(
            StartPt=n2.position * self.scale,
            EndPt=(n2.position - (1 - self.elementFraction) / 2 * vec) * self.scale,
            Pen=self.penConnect
        )

    def drawWire(self, w=wire(), Model=circuitModel()):
        """Draw a straight connection line for a wire, skipping if another element occupies the same node pair."""
        # Gather all node pairs that have elements (resistors, capacitors, inductors, or sources)
        elem_pairs = {
            frozenset((E.node1Name, E.node2Name))
            for E in (Model.resistors + Model.capacitors + Model.inductors + Model.voltageSources)
        }
        # If this wire’s endpoints match an existing element, do not draw the wire line
        if frozenset((w.node1Name, w.node2Name)) in elem_pairs:
            return

        # Look up the node objects for each end of the wire
        n1 = Model.getNode(w.node1Name)
        n2 = Model.getNode(w.node2Name)

        # Draw the line between the two node positions, applying the current scale and pen style
        self.drawALine(
            StartPt=n1.position * self.scale,
            EndPt=self.scale * (n2.position),
            Pen=self.penConnect
        )

    def drawResistor(self, R=resistor(), Model=circuitModel()):
        """Render a zigzag resistor symbol between two nodes, with connecting leads."""
        # 1) Scale the raw node positions by the current view scale
        n1 = Model.getNode(R.node1Name)
        n2 = Model.getNode(R.node2Name)
        p1 = n1.position * self.scale
        p2 = n2.position * self.scale

        # 2) Compute the direction vector and its perpendicular for zigzag orientation
        dx, dy = p2.x - p1.x, p2.y - p1.y
        L = math.hypot(dx, dy)
        if L == 0:
            return  # nothing to draw if both nodes coincide
        ux, uy = dx / L, dy / L
        perp = Position(x=-uy, y=ux)

        # 3) Offset the zigzag path slightly for visual spacing
        offset_px = 8
        offset = perp * (-offset_px)
        p1o = Position(x=p1.x + offset.x, y=p1.y + offset.y)
        p2o = Position(x=p2.x + offset.x, y=p2.y + offset.y)

        # 4) Determine the start and end points of the zigzag section (divide into thirds)
        thirdL = L / 3
        startZig = Position(x=p1o.x + ux * thirdL, y=p1o.y + uy * thirdL)
        endZig = Position(x=p1o.x + ux * 2 * thirdL, y=p1o.y + uy * 2 * thirdL)

        # 5) Draw the straight connector lines and the ends of the zigzag
        self.drawALine(StartPt=p1, EndPt=p1o, Pen=self.penConnect)
        self.drawALine(StartPt=p2o, EndPt=p2, Pen=self.penConnect)
        self.drawALine(StartPt=p1o, EndPt=startZig, Pen=self.penConnect)
        self.drawALine(StartPt=endZig, EndPt=p2o, Pen=self.penConnect)

        # 6) Construct the zigzag path with five peaks and add it to the scene
        path = QPainterPath(QPointF(startZig.x, -startZig.y))
        peaks = 5
        amp = 6  # amplitude of each zigzag peak
        zigL = math.hypot(endZig.x - startZig.x, endZig.y - startZig.y)
        for i in range(1, peaks + 1):
            t = i / (peaks + 1)
            bx = startZig.x + ux * zigL * t
            by = startZig.y + uy * zigL * t
            sign = 1 if i % 2 else -1
            off = perp * (amp * sign)
            path.lineTo(QPointF(bx + off.x, -(by + off.y)))
        path.lineTo(QPointF(endZig.x, -endZig.y))

        zig = qtw.QGraphicsPathItem(path)
        zig.setPen(self.penConnect)
        self.scene.addItem(zig)

    def drawInductor(self, L=inductor(), Model=circuitModel()):
        """Draw coil loops for an inductor symbol between two nodes and connect them with leads."""
        # 1) Retrieve the two node objects by their names
        n1 = Model.getNode(L.node1Name)
        n2 = Model.getNode(L.node2Name)

        # 2) Compute the vector from node1 to node2 and find its midpoint
        vec = n2.position - n1.position
        center = n1.position.midPt(n2.position) * self.scale

        # 3) Determine orientation (vertical vs horizontal) and compute loop geometry
        vert = (n2.position.x == n1.position.x)
        dist = self.scale * vec.mag()
        # width and height of loops depend on orientation
        width = (self.elementFraction / 2 * dist) if vert else (self.elementFraction * dist)
        height = (self.elementFraction * dist) if vert else (self.elementFraction / 2 * dist)

        # 4) Draw four coil loops using arcs
        if not vert:
            # horizontal orientation: loops spread left-to-right
            left = center.x - width / 2
            for i in range(4):
                # choose start and span angles for each loop
                if i in (0, 3):
                    stAng, spnAng = (300, 240)  # end loops
                else:
                    stAng, spnAng = (300, 300)  # middle loops
                # draw the arc for this loop
                self.drawAnArc(
                    centerX=left + (i + 1) * width / 5,
                    centerY=center.y,
                    Radius=width / 5,
                    startAngle=stAng,
                    spanAngle=spnAng,
                    pen=self.penConnect
                )
        else:
            # vertical orientation: loops spread top-to-bottom
            bottom = center.y - height / 2
            for i in range(4):
                # choose start and span angles for each loop
                if i in (0, 3):
                    stAng, spnAng = (270, 240)  # end loops
                else:
                    stAng, spnAng = (210, 300)  # middle loops
                # draw the arc for this loop
                self.drawAnArc(
                    centerX=center.x,
                    centerY=bottom + (i + 1) * (height / 15),
                    Radius=height / 15,
                    startAngle=stAng,
                    spanAngle=spnAng,
                    pen=self.penConnect
                )

        # 5) Draw straight leads connecting the loops back to the node positions
        self.drawALine(
            StartPt=n1.position * self.scale,
            EndPt=(n1.position + (1 - self.elementFraction) / 2 * vec) * self.scale,
            Pen=self.penConnect
        )
        self.drawALine(
            StartPt=n2.position * self.scale,
            EndPt=(n2.position - (1 - self.elementFraction) / 2 * vec) * self.scale,
            Pen=self.penConnect
        )

    def drawCapacitor(self, C=capacitor(), Model=circuitModel()):
        """Render a capacitor symbol between two nodes, including offset branch, elbow leads, and parallel plates."""
        # Scale the node positions by the current view scale
        n1 = Model.getNode(C.node1Name)
        n2 = Model.getNode(C.node2Name)
        p1 = n1.position * self.scale
        p2 = n2.position * self.scale

        # Compute the normalized direction vector along the branch and its perpendicular for plate orientation
        dx, dy = p2.x - p1.x, p2.y - p1.y
        L = math.hypot(dx, dy)
        if L == 0:
            return  # nothing to draw if both nodes coincide
        ux, uy = dx / L, dy / L
        perp = Position(x=-uy, y=ux)

        # Offset the branch slightly to one side for plate placement
        off = perp * 8
        p1o = Position(x=p1.x + off.x, y=p1.y + off.y)
        p2o = Position(x=p2.x + off.x, y=p2.y + off.y)

        # Draw elbow connectors from each node to the offset branch
        self.drawALine(StartPt=p1, EndPt=p1o, Pen=self.penConnect)
        self.drawALine(StartPt=p2o, EndPt=p2, Pen=self.penConnect)

        # Determine plate geometry: maximum half‑length, segment size, and gap between plates
        plate_len = min(L * 0.4, 20)
        third_pl = plate_len / 3
        gap = self.penConnect.width() * 4

        # Compute the midpoint of the offset branch where plates will be centered
        center = Position(x=(p1o.x + p2o.x) / 2, y=(p1o.y + p2o.y) / 2)

        # Draw the two capacitor plates and their connectors
        if abs(dx) < abs(dy):
            # Branch is mostly vertical → draw horizontal plates
            y_top = center.y + gap / 2
            y_bottom = center.y - gap / 2
            # Vertical connectors to the plates
            self.drawALine(StartPt=p1o, EndPt=Position(x=p1o.x, y=y_top), Pen=self.penConnect)
            self.drawALine(StartPt=Position(x=p2o.x, y=y_bottom), EndPt=p2o, Pen=self.penConnect)
            # Top and bottom horizontal plates
            x0, x1 = center.x - third_pl, center.x + third_pl
            self.drawALine(StartPt=Position(x=x0, y=y_top), EndPt=Position(x=x1, y=y_top), Pen=self.penConnect)
            self.drawALine(StartPt=Position(x=x0, y=y_bottom), EndPt=Position(x=x1, y=y_bottom), Pen=self.penConnect)
        else:
            # Branch is mostly horizontal → draw vertical plates
            x_left, x_right = center.x - gap / 2, center.x + gap / 2
            # Horizontal connectors to the plates
            self.drawALine(StartPt=p1o, EndPt=Position(x=x_left, y=p1o.y), Pen=self.penConnect)
            self.drawALine(StartPt=Position(x=x_right, y=p2o.y), EndPt=p2o, Pen=self.penConnect)
            # Left and right vertical plates
            y0, y1 = center.y - third_pl, center.y + third_pl
            self.drawALine(StartPt=Position(x=x_left, y=y0), EndPt=Position(x=x_left, y=y1), Pen=self.penConnect)
            self.drawALine(StartPt=Position(x=x_right, y=y0), EndPt=Position(x=x_right, y=y1), Pen=self.penConnect)

    def drawACircle(self, centerX, centerY, Radius, startAngle=0, spanAngle=360, ccw=True, brush=None, pen=None,
                    name=None, tooltip=None):
        """Draw a circle in the scene at the given center with optional styling, rotation, and metadata."""
        # get a reference to the graphics scene
        scene = self.scene

        # convert start and span angles from degrees to Qt’s 1/16-degree units, applying CCW direction
        stAng = startAngle * 16
        spnAngle = spanAngle * 16 * (1 if ccw else -1)

        # create the ellipse item, flipping the Y-coordinate for scene coordinate system
        ellipse = qtw.QGraphicsEllipseItem(
            centerX - Radius,
            -1.0 * (centerY + Radius),
            2 * Radius,
            2 * Radius
        )
        ellipse.setStartAngle(stAng)
        ellipse.setSpanAngle(spnAngle)

        # apply optional pen and brush if provided
        if pen is not None:
            ellipse.setPen(pen)
        if brush is not None:
            ellipse.setBrush(brush)

        # attach optional metadata: a name for lookup and a tooltip for hover info
        if name is not None:
            ellipse.setData(0, name)
        if tooltip is not None:
            ellipse.setToolTip(tooltip)

        # add the fully configured ellipse to the scene for rendering
        scene.addItem(ellipse)

    def drawAnArc(self, centerX, centerY, Radius, startAngle=0, spanAngle=360, ccw=True, brush=None, pen=None,
                  name=None, tooltip=None):
        """Draw a partial arc of a circle at the specified center, with optional styling and metadata."""
        # reference the QGraphicsScene for item placement
        scene = self.scene

        # convert angles from degrees to Qt’s 1/16-degree units, applying direction flag
        stAng = startAngle * 16
        spnAng = spanAngle * 16 * (1 if ccw else -1)

        # define the bounding rectangle for the arc, flipping Y to match scene coordinates
        rect = qtc.QRectF(centerX - Radius, -1.0 * (centerY + Radius), 2 * Radius, 2 * Radius)

        # create the custom arc item and set its geometry
        arc = QGraphicsArcItem()
        arc.setRect(rect)
        arc.setStartAngle(stAng)
        arc.setSpanAngle(spnAng)

        # apply optional pen and brush styling
        if pen is not None:
            arc.setPen(pen)
        if brush is not None:
            arc.setBrush(brush)

        # attach optional name and tooltip for interactivity
        if name is not None:
            arc.setData(0, name)
        if tooltip is not None:
            arc.setToolTip(tooltip)

        # add the configured arc into the scene for rendering
        scene.addItem(arc)

    def drawARectangle(self, centerX, centerY, height, width, brush=None, pen=None, name=None, tooltip=None):
        """Draw a centered rectangle at the specified scene coordinates with optional styling and metadata."""
        # get the scene to add items into
        scene = self.scene

        # create a rectangle item, flipping Y so that positive Y goes upward
        rect = qtw.QGraphicsRectItem(
            centerX - width / 2,
            -1.0 * (centerY + height / 2),
            width,
            height
        )

        # apply the provided pen for the outline if any
        if pen is not None:
            rect.setPen(pen)
        # apply the provided brush for filling if any
        if brush is not None:
            rect.setBrush(brush)

        # attach a name for identification if provided
        if name is not None:
            rect.setData(0, name)
        # attach a tooltip for hover information if provided
        if tooltip is not None:
            rect.setToolTip(tooltip)

        # add the rectangle to the scene for rendering
        scene.addItem(rect)

    def drawALine(self, StartPt=Position(), EndPt=Position, Pen=qtg.QPen(qtg.QColor(qtc.Qt.black))):
        """Draw a straight connection line between two Position points in the graphics scene."""
        scene = self.scene  # reference the current QGraphicsScene
        ln = qtw.QGraphicsLineItem(
            StartPt.x, -StartPt.y,  # start point (flip Y for scene coords)
            EndPt.x, -EndPt.y  # end point
        )
        ln.setPen(Pen)  # set the line’s pen style and width
        scene.addItem(ln)  # add the line item into the scene

class circuitController():
    """Manage the interaction between the main window, circuit data model, and view rendering."""

    def __init__(self, args):
        """Initialize controller with references to the main window, display widgets, and input widgets; set up model and view."""
        self.main_window_instance, self.displayWidgets, self.inputWidgets = args  # Pass main_window instance
        self.spnd_Zoom = self.inputWidgets
        self.dlg = qtw.QFileDialog()

        self.Model = circuitModel()
        self.View = circuitView(self.displayWidgets)

    def openFile(self):
        """Prompt the user to select a circuit file, read its contents, and import the circuit data."""
        print("le_FileName:", self.main_window_instance.le_FileName)  # Access le_FileName from main_window instance
        filename = self.dlg.getOpenFileName(caption='Select a circuit file to open.')[0]
        if len(filename) == 0:  # no file selected
            return
        self.main_window_instance.le_FileName.setText(filename)  # echo the filename on the GUI
        file = open(filename, 'r')  # open the file
        data = file.readlines()  # read all the lines of the file into a list of strings
        try:
            self.importCircuit(data)
        except Exception:
            import traceback
            traceback.print_exc()
            return

    def importCircuit(self, data):
        """Parse the raw file lines into circuit nodes and elements, update the model, and redraw the view."""
        try:
            # Reset model
            self.Model = circuitModel()

            i = 0
            while i < len(data):
                line = data[i].strip()
                low  = line.lower()

                # PARSE NODE
                if low.startswith('<node>'):
                    i += 1
                    n = circuitNode()
                    while not data[i].lower().strip().startswith('</node>'):
                        part = data[i].strip()
                        if part.lower().startswith('name:'):
                            n.name = part.split(':', 1)[1].strip()
                        elif part.lower().startswith('position:'):
                            raw = part.split(':', 1)[1].strip()
                            raw = raw.split('<!--')[0].strip()
                            coords = [c.strip() for c in raw.split(',')]
                            n.position.x = float(coords[0])
                            n.position.y = float(coords[1])
                        i += 1
                    self.Model.nodes.append(dc(n))

                # PARSE WIRE
                elif low.startswith('<wire>'):
                    i += 1
                    w = wire()
                    while not data[i].lower().strip().startswith('</wire>'):
                        part = data[i].strip()
                        if part.lower().startswith('node1:'):
                            w.node1Name = part.split(':',1)[1].strip()
                        elif part.lower().startswith('node2:'):
                            w.node2Name = part.split(':',1)[1].strip()
                        i += 1
                    self.Model.wires.append(dc(w))

                # PARSE RESISTOR
                elif low.startswith('<resistor>'):
                    i += 1
                    R = resistor()
                    while not data[i].lower().strip().startswith('</resistor>'):
                        part = data[i].strip()
                        if part.lower().startswith('name:'):
                            R.name = part.split(':',1)[1].strip()
                        elif part.lower().startswith('resistance:'):
                            R.R = float(part.split(':',1)[1].strip())
                        elif part.lower().startswith('node1:'):
                            R.node1Name = part.split(':',1)[1].strip()
                        elif part.lower().startswith('node2:'):
                            R.node2Name = part.split(':',1)[1].strip()
                        i += 1
                    self.Model.resistors.append(dc(R))

                # PARSE CAPACITOR
                elif low.startswith('<capacitor>'):
                    i += 1
                    C = capacitor()
                    while not data[i].lower().strip().startswith('</capacitor>'):
                        part = data[i].strip()
                        if part.lower().startswith('name:'):
                            C.name = part.split(':',1)[1].strip()
                        elif part.lower().startswith('capacitance:'):
                            C.C = float(part.split(':',1)[1].strip())
                        elif part.lower().startswith('node1:'):
                            C.node1Name = part.split(':',1)[1].strip()
                        elif part.lower().startswith('node2:'):
                            C.node2Name = part.split(':',1)[1].strip()
                        i += 1
                    self.Model.capacitors.append(dc(C))

                # PARSE INDUCTOR
                elif low.startswith('<inductor>'):
                    i += 1
                    L = inductor()
                    while not data[i].lower().strip().startswith('</inductor>'):
                        part = data[i].strip()
                        if part.lower().startswith('name:'):
                            L.name = part.split(':',1)[1].strip()
                        elif part.lower().startswith('inductance:'):
                            L.L = float(part.split(':',1)[1].strip())
                        elif part.lower().startswith('node1:'):
                            L.node1Name = part.split(':',1)[1].strip()
                        elif part.lower().startswith('node2:'):
                            L.node2Name = part.split(':',1)[1].strip()
                        i += 1
                    self.Model.inductors.append(dc(L))

                # PARSE VOLTAGE SOURCE
                elif low.startswith('<voltage source>'):
                    i += 1
                    V = voltageSource()
                    while not data[i].lower().strip().startswith('</voltage source>'):
                        part = data[i].strip()
                        if part.lower().startswith('name:'):
                            V.name = part.split(':',1)[1].strip()
                        elif part.lower().startswith('value:'):
                            raw = part.split(':',1)[1].strip().rstrip('Vv')
                            V.value = float(raw)
                        elif part.lower().startswith('node1:'):
                            V.node1Name = part.split(':',1)[1].strip()
                        elif part.lower().startswith('node2:'):
                            V.node2Name = part.split(':',1)[1].strip()
                        i += 1
                    self.Model.voltageSources.append(dc(V))

                # OTHERWISE: skip
                i += 1

            # Now that everything’s parsed, draw it
            self.drawCircuit()

        except Exception:
            import traceback
            traceback.print_exc()

    def setZoom(self):
        """Update the view’s zoom factor based on the spinbox value."""
        self.View.Zoom = self.spnd_Zoom.value()
        self.View.setZoom()

    def drawCircuit(self):
        """Trigger a full redraw of the circuit elements in the view."""
        self.View.drawCircuit(Model=self.Model)

    def getScene(self):
        """Provide access to the QGraphicsScene for event filtering."""
        return self.View.scene