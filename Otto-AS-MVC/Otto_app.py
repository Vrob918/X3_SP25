#utilized ChatGPT
from Otto import ottoCycleController
from Otto_GUI import Ui_Form
from PyQt5 import QtWidgets as qtw
from PyQt5.QtWidgets import QButtonGroup
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import sys

class MainWindow(qtw.QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # embed matplotlib canvas
        self.figure = Figure(figsize=(8,8), tight_layout=True, frameon=True, facecolor='none')
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax     = self.figure.add_subplot()
        self.main_VerticalLayout.addWidget(self.canvas)

        # signal/slot
        self.btn_Calculate.clicked.connect(self.calcOtto)
        self.rdo_Otto.toggled.connect(self.toggleCutoff)
        self.rdo_Diesel.toggled.connect(self.toggleCutoff)
        self.rdo_Metric.toggled.connect(self.setUnits)
        self.cmb_Abcissa.currentIndexChanged.connect(self.doPlot)
        self.cmb_Ordinate.currentIndexChanged.connect(self.doPlot)
        self.chk_LogAbcissa.stateChanged.connect(self.doPlot)
        self.chk_LogOrdinate.stateChanged.connect(self.doPlot)

        # controller
        self.controller = ottoCycleController()

        # pass all the widgets in the exact same order as controller.setWidgets expects
        someWidgets = []
        someWidgets += [self.lbl_THigh,    self.lbl_TLow,
                        self.lbl_P0,       self.lbl_V0,
                        self.lbl_CR]
        someWidgets += [self.le_THigh,     self.le_TLow,
                        self.le_P0,        self.le_V0,
                        self.le_CR]
        someWidgets += [self.lbl_CutoffRatio, self.le_CutoffRatio]
        someWidgets += [self.le_T1,        self.le_T2,
                        self.le_T3,        self.le_T4]
        someWidgets += [self.lbl_T1Units,  self.lbl_T2Units,
                        self.lbl_T3Units,  self.lbl_T4Units]
        someWidgets += [self.le_PowerStroke, self.le_CompressionStroke,
                        self.le_HeatAdded, self.le_Efficiency]
        someWidgets += [self.lbl_PowerStrokeUnits, self.lbl_CompressionStrokeUnits,
                        self.lbl_HeatInUnits]
        someWidgets += [self.rdo_Metric,   self.rdo_Otto,   self.rdo_Diesel]
        someWidgets += [self.cmb_Abcissa,  self.cmb_Ordinate]
        someWidgets += [self.chk_LogAbcissa, self.chk_LogOrdinate]
        someWidgets += [self.ax,           self.canvas]

        self.controller.setWidgets(w=someWidgets)
        self.toggleCutoff()  # enable/disable cutoff initially
        self.show()
        unitGroup = QButtonGroup(self)
        unitGroup.addButton(self.rdo_Metric)
        unitGroup.addButton(self.rdo_English)
        unitGroup.setExclusive(True)

        cycleGroup = QButtonGroup(self)
        cycleGroup.addButton(self.rdo_Otto)
        cycleGroup.addButton(self.rdo_Diesel)
        cycleGroup.setExclusive(True)

    def calcOtto(self):
        self.controller.calc()

    def doPlot(self):
        self.controller.updateView()

    def setUnits(self):
        self.controller.updateView()

    def toggleCutoff(self):
        enabled = self.rdo_Diesel.isChecked()
        self.le_CutoffRatio.setEnabled(enabled)
        self.lbl_CutoffRatio.setEnabled(enabled)

if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    mw = MainWindow()
    mw.setWindowTitle('Otto/Diesel Cycle Calculator')
    sys.exit(app.exec())