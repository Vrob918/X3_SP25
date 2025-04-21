#utilized ChatGPT
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QScrollArea, QMessageBox
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
from PyQt5.QtCore import Qt
from Problem1 import Ui_Form
import sys
import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

class main_window(Ui_Form, QWidget):  # define main window class combining UI form and QWidget
    """Main GUI window for RLC circuit simulation, combining the form layout with plotting and simulation logic."""
    def __init__(self):  # constructor
        super().__init__()  # initialize base classes
        self.setupUi(self)  # set up the UI components from the form
        self.resize(600, 900)  # increase window height for toolbar visibility
        self.setupImageLabel()  # call helper to set up the circuit diagram image
        self.setupInputFields()  # call helper to set up input widgets
        self.setupPlot()  # call helper to set up the plot area
        self.show()  # display the window

    def setupImageLabel(self):  # method to add circuit image
        self.pixMap = qtg.QPixmap()  # create a QPixmap object
        self.pixMap.load("Circuit1.png")  # load the image file
        self.image_label = qtw.QLabel()  # create a QLabel for displaying images
        self.image_label.setPixmap(self.pixMap)  # set the pixmap on the label
        self.layout_GridInput.addWidget(  # add the label to the grid layout
            self.image_label, 0, 0, 1, 2, Qt.AlignCenter)

    def setupInputFields(self):  # method to create and place input controls
        self.L_label = qtw.QLabel("L (H):")  # label for inductance input
        self.L_input = QLineEdit("20")  # default inductance value
        self.R_label = qtw.QLabel("R (Ω):")  # label for resistance input
        self.R_input = QLineEdit("10")  # default resistance value
        self.C_label = qtw.QLabel("C (F):")  # label for capacitance input
        self.C_input = QLineEdit("0.05")  # default capacitance value
        self.Vm_label = qtw.QLabel("Voltage Magnitude (V):")  # label for voltage magnitude
        self.Vm_input = QLineEdit("20")  # default voltage magnitude
        self.freq_label = qtw.QLabel("Frequency (rad/s):")  # label for frequency
        self.freq_input = QLineEdit("20")  # default frequency
        self.phase_label = qtw.QLabel("Phase (rad):")  # label for phase
        self.phase_input = QLineEdit("0")  # default phase

        self.simulate_button = QPushButton("Simulate")  # create simulate button
        self.simulate_button.clicked.connect(self.simulate)  # connect button click to simulate method

        # place each widget into the grid layout
        self.layout_GridInput.addWidget(self.L_label, 1, 0)
        self.layout_GridInput.addWidget(self.L_input, 1, 1)
        self.layout_GridInput.addWidget(self.R_label, 2, 0)
        self.layout_GridInput.addWidget(self.R_input, 2, 1)
        self.layout_GridInput.addWidget(self.C_label, 3, 0)
        self.layout_GridInput.addWidget(self.C_input, 3, 1)
        self.layout_GridInput.addWidget(self.Vm_label, 4, 0)
        self.layout_GridInput.addWidget(self.Vm_input, 4, 1)
        self.layout_GridInput.addWidget(self.freq_label, 5, 0)
        self.layout_GridInput.addWidget(self.freq_input, 5, 1)
        self.layout_GridInput.addWidget(self.phase_label, 6, 0)
        self.layout_GridInput.addWidget(self.phase_input, 6, 1)
        self.layout_GridInput.addWidget(self.simulate_button, 7, 0, 1, 2)

    def setupPlot(self):  # method to set up Matplotlib canvas and toolbar
        self.figure, self.ax = plt.subplots(figsize=(5, 4))  # create figure and axes
        self.canvas = FigureCanvas(self.figure)  # wrap figure in a Qt canvas
        self.toolbar = NavigationToolbar(self.canvas, self)  # create a navigation toolbar
        plot_layout = QVBoxLayout()  # vertical layout for toolbar + canvas
        plot_layout.addWidget(self.toolbar, alignment=Qt.AlignHCenter)  # add toolbar centered
        plot_layout.addWidget(self.canvas)  # add the plot canvas
        self.verticalLayout.addLayout(plot_layout)  # insert into the main vertical layout

    def simulate(self):  # method triggered by simulate button
        """Read and validate inputs, solve the RLC ODEs, and plot i1, i2, and vC; show warnings or errors as needed."""
        try:
            # Get and convert user inputs to floats
            L = float(self.L_input.text())
            R = float(self.R_input.text())
            C = float(self.C_input.text())
            Vm = float(self.Vm_input.text())
            freq = float(self.freq_input.text())
            phase = float(self.phase_input.text())

            # Validate that L, R, C are positive and frequency non-negative
            if L <= 0 or R <= 0 or C <= 0:
                qtw.QMessageBox.warning(self, "Invalid Input", "L, R, and C must be positive.")
                return
            if freq < 0:
                qtw.QMessageBox.warning(self, "Invalid Input", "Frequency must be non-negative.")
                return

            # Define the system of ODEs for the RLC circuit
            def circuit_model(y, t, L, R, C, Vm, freq, phase):
                i1, vC = y
                v_t = Vm * np.sin(freq * t + phase)  # source voltage
                di1_dt = (v_t - vC) / L  # inductor equation
                dvC_dt = (i1 - vC / R) / C  # capacitor equation
                return [di1_dt, dvC_dt]

            # Set up time grid and initial conditions
            t = np.linspace(0, 2, 2000)  # simulate for 2 seconds with 2000 points
            y0 = [0, 0]  # initial current and capacitor voltage
            sol = odeint(circuit_model, y0, t, args=(L, R, C, Vm, freq, phase))  # solve ODE
            i1 = sol[:, 0]  # extract current through inductor
            vC = sol[:, 1]  # extract voltage across capacitor
            i2 = vC / R  # compute resistor current

            # Plot the results on the axes
            self.ax.clear()  # clear any existing plot
            self.ax.plot(t, i1,    # time array vs. inductor current array
                         label="i1 (A)", # legend entry for i1
                         linewidth=2,    # line thickness
                         color="black",  # line color
                         linestyle='-')  # solid line style
            self.ax.plot(t, i2,    # time array vs. resistor current array (i2)
                         label="i2 (A)", # legend entry for i2
                         linewidth=2,    # line thickness
                         color="black",  # line color
                         linestyle='--') # dashed line style
            self.ax.plot(t, vC,    # time array vs. capacitor voltage array
                         label="vC (V)", # legend entry for vC
                         linewidth=2,    # line thickness
                         color="black",  # line color
                         linestyle=':')  # dotted line style
            self.ax.set_xlabel("Time (s)")  # label x-axis
            self.ax.set_ylabel("Current (A) / Voltage (V)")  # label y-axis
            self.ax.set_title("RLC Circuit Transient Response")  # set plot title
            self.ax.legend()  # show legend
            self.ax.grid(True)  # enable grid
            self.canvas.draw()  # refresh the canvas display
        except ValueError:  # handle invalid numeric input
            qtw.QMessageBox.warning(self, "Invalid Input", "Please enter valid numeric values.")
        except Exception as e:  # handle unexpected errors
            qtw.QMessageBox.critical(self, "Error", f"Simulation failed: {e}")

if __name__ == "__main__":  # entry point guard
    """Launch the QApplication, instantiate main_window, and start the Qt event loop."""
    app = QApplication.instance()  # check for existing application
    if not app:
        app = QApplication(sys.argv)  # create a new application if none exists
    app.aboutToQuit.connect(app.deleteLater)  # ensure proper cleanup on exit
    main_win = main_window()  # instantiate and show the main window
    sys.exit(app.exec_())  # start event loop and exit when done