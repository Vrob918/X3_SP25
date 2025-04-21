#utilized ChatGPT
from PyQt5.QtWidgets import QApplication, QWidget
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
import PyQt5.QtCore as qtc
from X3P2SP25_GUI import Ui_Form
from CircuitClass import circuitController
import sys

# Define the main GUI window class that brings together layout and behavior
class main_window(Ui_Form, QWidget):
    """
    Main application window for the circuit sketch tool.

    This class inherits the layout from Ui_Form and QWidget, sets up the
    interface, initializes the circuit controller, and binds user actions
    (zoom, open file) to their handlers.
    """
    def __init__(self):
        """
        Initialize the main window:
        - Call the generated setupUi to place widgets.
        - Store references to input and display controls.
        - Create the circuitController to manage file import and drawing.
        - Connect the zoom spinbox and open-file button to the controller.
        - Show the window on screen.
        """
        super().__init__()
        self.setupUi(self)

        # Field where the user enters or selects a circuit file path
        self.le_FileName = self.lineEdit

        # Tuples of widgets passed to the controller for drawing and input
        self.displayWidgets = (self.gv_Main, self.lineEdit, self)
        self.inputWidgets = (self.spnd_Zoom)

        # Create controller with GUI context for file loading and zoom
        self.Controller = circuitController((self, self.displayWidgets, self.inputWidgets))
        self.setWindowTitle("Circuit Sketch")

        # Wire signals: zoom changes and open-file button
        self.spnd_Zoom.valueChanged.connect(self.Controller.setZoom)
        self.pb_Open.clicked.connect(self.Controller.openFile)

        self.show()

    def eventFilter(self, obj, event):
        """
        Intercept and handle specialized events before default processing.

        - Mouse move: update status label with scene coordinates and item name.
        - Mouse wheel: adjust zoom level via spinbox steps.
        - Delete key: remove selected pipes, nodes, or loops in relevant tables.

        Returns the base class's eventFilter result after custom handling.
        """
        # Region: track mouse movement over the circuit scene
        if obj == self.Controller.View.scene:
            if event.type() == qtc.QEvent.GraphicsSceneMouseMove:
                scenePos = event.scenePos()
                name_item = self.Controller.View.scene.itemAt(scenePos, self.gv_Main.transform())
                coords = f"Mouse Position:  x = {round(scenePos.x(),2)}, y = {round(-scenePos.y(),2)}"
                if name_item is not None and name_item.data(0) is not None:
                    coords += ' ' + name_item.data(0)
                self.lbl_MousePosition.setText(coords)

            elif event.type() == qtc.QEvent.GraphicsSceneWheel:
                # Zoom in or out depending on wheel delta
                if event.delta() > 0:
                    self.spnd_Zoom.stepUp()
                else:
                    self.spnd_Zoom.stepDown()

        # Region: handle delete key for selection-based removal
        if event.type() == qtc.QEvent.KeyPress and event.key() == qtc.Qt.Key_Delete:
            if obj == self.table_Pipes:
                self.deletePipe()
            elif obj == self.table_Nodes:
                self.deleteNode()
            elif obj == self.tree_LoopPipes:
                self.deleteLoopPipe()
            elif obj == self.tree_Loops:
                self.deleteLoop()

        # Fallback to default processing
        return super(main_window, self).eventFilter(obj, event)


if __name__ == "__main__":
    """
    Entry point: ensure one QApplication runs, instantiate main_window, and
    start the Qt event loop. Clean up on exit.
    """
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    main_win = main_window()
    sys.exit(app.exec_())