#utilized ChatGPT
from Air import *
from matplotlib import pyplot as plt
from PyQt5 import QtWidgets as qtw
import sys
import numpy as np
from copy import deepcopy as dc

class ottoCycleModel:
    def __init__(self,
                 p_initial=1000.0,
                 v_cylinder=1.0,
                 t_initial=298,
                 t_high=1500.0,
                 ratio=6.0,
                 name='Air Standard Otto Cycle'):
        self.name = name
        self.units = units()
        self.air = air()
        self.air.set(P=p_initial, T=t_initial)
        self.p_initial = p_initial
        self.T_initial = t_initial
        self.T_high = t_high
        self.Ratio = ratio
        self.V_Cylinder = v_cylinder
        self.air.n = self.V_Cylinder / self.air.State.v
        self.air.m = self.air.n * self.air.MW

        # initial four states
        self.State1 = self.air.set(P=self.p_initial, T=self.T_initial)
        self.State2 = self.air.set(v=self.State1.v / self.Ratio, s=self.State1.s)
        self.State3 = self.air.set(T=self.T_high, v=self.State2.v)
        self.State4 = self.air.set(v=self.State1.v, s=self.State3.s)

        # works and heats
        self.W_Compression = self.air.n * (self.State2.u - self.State1.u)
        self.W_Power       = self.air.n * (self.State3.u - self.State3.u)  # zero by construction
        self.Q_In          = self.air.n * (self.State3.u - self.State2.u)
        self.Q_Out         = self.air.n * (self.State4.u - self.State1.u)

        self.W_Cycle = self.W_Power - self.W_Compression
        self.Eff     = self.W_Cycle / self.Q_In

        self.upperCurve = StateDataForPlotting()
        self.lowerCurve = StateDataForPlotting()

    def run_diesel_cycle(self,
                         p_initial,
                         v_cylinder,
                         t_initial,
                         compression_ratio,
                         cutoff_ratio):
        self.name = 'Diesel Cycle'
        self.p_initial   = p_initial
        self.V_Cylinder  = v_cylinder
        self.T_initial   = t_initial
        self.Ratio       = compression_ratio
        rc = cutoff_ratio

        # state 1
        self.State1 = self.air.set(P=self.p_initial, T=self.T_initial, name='State 1 - BDC')
        v2   = self.State1.v / self.Ratio
        s1   = self.State1.s
        # state 2
        self.State2 = self.air.set(v=v2, s=s1, name='State 2 - TDC')
        P2   = self.State2.P
        # state 3
        v3   = v2 * rc
        self.State3 = self.air.set(P=P2, v=v3, name='State 3')
        v1   = self.State1.v
        s3   = self.State3.s
        # state 4
        self.State4 = self.air.set(v=v1, s=s3, name='State 4')

        self.air.n = self.V_Cylinder / self.air.State.v
        self.air.m = self.air.n * self.air.MW

        Wc   = self.State2.u - self.State1.u
        Wp   = self.State3.u - self.State4.u
        Qin  = self.State3.u - self.State2.u
        Qout = self.State4.u - self.State1.u

        self.W_Cycle       = Wp - Wc
        self.Eff           = 100.0 * self.W_Cycle / Qin
        self.W_Compression = Wc
        self.W_Power       = Wp
        self.Q_In          = Qin
        self.Q_Out         = Qout

        self.upperCurve.clear()
        self.lowerCurve.clear()

        # P–V data for Diesel cycle segments
        for v in np.linspace(self.State1.v, self.State2.v, 30):
            st = self.air.set(v=v, s=s1)
            self.lowerCurve.add((st.T, st.P, st.u, st.h, st.s, st.v))
        for v in np.linspace(self.State2.v, self.State3.v, 30):
            st = self.air.set(P=P2, v=v)
            self.upperCurve.add((st.T, st.P, st.u, st.h, st.s, st.v))
        for v in np.linspace(self.State3.v, self.State4.v, 30):
            st = self.air.set(v=v, s=s3)
            self.upperCurve.add((st.T, st.P, st.u, st.h, st.s, st.v))
        for T in np.linspace(self.State4.T, self.State1.T, 30):
            st = self.air.set(T=T, v=v1)
            self.upperCurve.add((st.T, st.P, st.u, st.h, st.s, st.v))

    def getSI(self):
        return self.units.SI


class ottoCycleController:
    def __init__(self, model=None, ax=None):
        self.model = ottoCycleModel() if model is None else model
        self.view  = ottoCycleView()
        self.view.ax     = ax
        self.view.canvas = None

    def calc(self):
        T0  = float(self.view.le_TLow.text())
        P0  = float(self.view.le_P0.text())
        V0  = float(self.view.le_V0.text())
        TH  = float(self.view.le_THigh.text())
        CR  = float(self.view.le_CR.text())
        SI  = self.view.rdo_Metric.isChecked()

        if self.view.rdo_Diesel.isChecked():
            rc = float(self.view.le_CutoffRatio.text())
            self.model.run_diesel_cycle(
                p_initial=P0,
                v_cylinder=V0,
                t_initial=T0,
                compression_ratio=CR,
                cutoff_ratio=rc
            )
        else:
            self.set(T_0=T0, P_0=P0, V_0=V0, T_High=TH, ratio=CR, SI=SI)

        self.updateView()

    def set(self, T_0=25.0, P_0=100.0, V_0=1.0, T_High=1500.0, ratio=6.0, SI=True):
        m = self.model
        m.units.set(SI=SI)
        m.T_initial  = T_0   if SI else T_0   / m.units.CF_T
        m.p_initial  = P_0   if SI else P_0   / m.units.CF_P
        m.T_high     = T_High if SI else T_High / m.units.CF_T
        m.V_Cylinder = V_0   if SI else V_0   / m.units.CF_V
        m.Ratio      = ratio

        m.State1 = m.air.set(P=m.p_initial, T=m.T_initial, name='State 1 - BDC')
        m.State2 = m.air.set(v=m.State1.v / m.Ratio, s=m.State1.s, name='State 2 - TDC')
        m.State3 = m.air.set(T=m.T_high, v=m.State2.v, name='State 3 - TDC')
        m.State4 = m.air.set(v=m.State1.v, s=m.State3.s, name='State 4 - BDC')

        m.air.n = m.V_Cylinder / m.air.State.v
        m.air.m = m.air.n * m.air.MW

        m.W_Compression = m.State2.u - m.State1.u
        m.W_Power       = m.State3.u - m.State4.u
        m.Q_In          = m.State3.u - m.State2.u
        m.Q_Out         = m.State4.u - m.State1.u

        m.W_Cycle = m.W_Power - m.W_Compression
        m.Eff     = 100.0 * m.W_Cycle / m.Q_In

        self.buildDataForPlotting()
        self.updateView()

    def buildDataForPlotting(self):
        m = self.model
        m.upperCurve.clear()
        m.lowerCurve.clear()
        a = air()

        # 2→3
        for T in np.linspace(m.State2.T, m.State3.T, 30):
            st = a.set(T=T, v=m.State2.v)
            m.upperCurve.add((st.T, st.P, st.u, st.h, st.s, st.v))
        # 3→4
        for v in np.linspace(m.State3.v, m.State4.v, 30):
            st = a.set(v=v, s=m.State3.s)
            m.upperCurve.add((st.T, st.P, st.u, st.h, st.s, st.v))
        # 4→1
        for T in np.linspace(m.State4.T, m.State1.T, 30):
            st = a.set(T=T, v=m.State4.v)
            m.upperCurve.add((st.T, st.P, st.u, st.h, st.s, st.v))
        # 1→2
        for v in np.linspace(m.State1.v, m.State2.v, 30):
            st = a.set(v=v, s=m.State1.s)
            m.lowerCurve.add((st.T, st.P, st.u, st.h, st.s, st.v))

    def updateView(self):
        self.view.updateView(cycle=self.model)

    def setWidgets(self, w=None):
        ( self.view.lbl_THigh,    self.view.lbl_TLow,
          self.view.lbl_P0,       self.view.lbl_V0,
          self.view.lbl_CR,
          self.view.le_THigh,     self.view.le_TLow,
          self.view.le_P0,        self.view.le_V0,
          self.view.le_CR,
          self.view.lbl_CutoffRatio, self.view.le_CutoffRatio,
          self.view.le_T1,        self.view.le_T2,
          self.view.le_T3,        self.view.le_T4,
          self.view.lbl_T1Units,  self.view.lbl_T2Units,
          self.view.lbl_T3Units,  self.view.lbl_T4Units,
          self.view.le_PowerStroke, self.view.le_CompressionStroke,
          self.view.le_HeatAdded,   self.view.le_Efficiency,
          self.view.lbl_PowerStrokeUnits, self.view.lbl_CompressionStrokeUnits,
          self.view.lbl_HeatInUnits,
          self.view.rdo_Metric,    self.view.rdo_Otto,
          self.view.rdo_Diesel,
          self.view.cmb_Abcissa,   self.view.cmb_Ordinate,
          self.view.chk_LogAbcissa, self.view.chk_LogOrdinate,
          self.view.ax,            self.view.canvas
        ) = w


class ottoCycleView:
    def __init__(self):
        self.lbl_THigh        = qtw.QLabel()
        self.lbl_TLow         = qtw.QLabel()
        self.lbl_P0           = qtw.QLabel()
        self.lbl_V0           = qtw.QLabel()
        self.lbl_CR           = qtw.QLabel()
        self.lbl_CutoffRatio  = qtw.QLabel()
        self.le_THigh         = qtw.QLineEdit()
        self.le_TLow          = qtw.QLineEdit()
        self.le_P0            = qtw.QLineEdit()
        self.le_V0            = qtw.QLineEdit()
        self.le_CR            = qtw.QLineEdit()
        self.le_CutoffRatio   = qtw.QLineEdit()
        self.le_T1            = qtw.QLineEdit()
        self.le_T2            = qtw.QLineEdit()
        self.le_T3            = qtw.QLineEdit()
        self.le_T4            = qtw.QLineEdit()
        self.lbl_T1Units      = qtw.QLabel()
        self.lbl_T2Units      = qtw.QLabel()
        self.lbl_T3Units      = qtw.QLabel()
        self.lbl_T4Units      = qtw.QLabel()
        self.le_Efficiency    = qtw.QLineEdit()
        self.le_PowerStroke   = qtw.QLineEdit()
        self.le_CompressionStroke = qtw.QLineEdit()
        self.le_HeatAdded     = qtw.QLineEdit()
        self.lbl_PowerStrokeUnits = qtw.QLabel()
        self.lbl_CompressionStrokeUnits = qtw.QLabel()
        self.lbl_HeatInUnits  = qtw.QLabel()
        self.rdo_Metric       = qtw.QRadioButton()
        self.rdo_Otto         = qtw.QRadioButton()
        self.rdo_Diesel       = qtw.QRadioButton()
        self.cmb_Abcissa      = qtw.QComboBox()
        self.cmb_Ordinate     = qtw.QComboBox()
        self.chk_LogAbcissa   = qtw.QCheckBox()
        self.chk_LogOrdinate  = qtw.QCheckBox()
        self.canvas           = None
        self.ax               = None

    def updateView(self, cycle):
        cycle.units.SI = self.rdo_Metric.isChecked()
        logx = self.chk_LogAbcissa.isChecked()
        logy = self.chk_LogOrdinate.isChecked()
        X    = self.cmb_Abcissa.currentText()
        Y    = self.cmb_Ordinate.currentText()
        self.plot_cycle_XY(cycle, X=X, Y=Y, logx=logx, logy=logy, mass=False, total=True)
        self.updateDisplayWidgets(cycle)

    def convertDataCol(self, cycle, data=None, colName='T', mass=False, total=False):
        UC  = cycle.units
        n   = cycle.air.n
        MW  = cycle.air.MW
        TCF = 1.0 if UC.SI else UC.CF_T
        PCF = 1.0 if UC.SI else UC.CF_P
        hCF = 1.0 if UC.SI else UC.CF_e
        uCF = 1.0 if UC.SI else UC.CF_e
        sCF = 1.0 if UC.SI else UC.CF_s
        vCF = 1.0 if UC.SI else UC.CF_v
        nCF = 1.0 if UC.SI else UC.CF_n
        if mass:
            hCF /= MW; uCF /= MW; sCF /= MW; vCF /= MW
        elif total:
            hCF *= n*nCF; uCF *= n*nCF; sCF *= n*nCF; vCF *= n*nCF
        w = colName.lower()
        if w=='t': return [T*TCF for T in data]
        if w=='h': return [h*hCF for h in data]
        if w=='u': return [u*uCF for u in data]
        if w=='s': return [s*sCF for s in data]
        if w=='v': return [v*vCF for v in data]
        if w=='p': return [P*PCF for P in data]

    def plot_cycle_XY(self, cycle, X='s', Y='T', logx=False, logy=False, mass=False, total=False):
        if X==Y:
            return
        usingQT = self.ax is not None
        if not usingQT:
            self.ax = plt.subplot()
        ax = self.ax
        ax.clear()
        ax.set_xscale('log' if logx else 'linear')
        ax.set_yscale('log' if logy else 'linear')
        Xlc = self.convertDataCol(cycle, cycle.lowerCurve.getDataCol(X), X, mass, total)
        Ylc = self.convertDataCol(cycle, cycle.lowerCurve.getDataCol(Y), Y, mass, total)
        Xuc = self.convertDataCol(cycle, cycle.upperCurve.getDataCol(X), X, mass, total)
        Yuc = self.convertDataCol(cycle, cycle.upperCurve.getDataCol(Y), Y, mass, total)
        ax.plot(Xlc, Ylc)
        ax.plot(Xuc, Yuc)
        cycle.units.setPlotUnits(SI=cycle.units.SI, mass=mass, total=total)
        ax.set_xlabel(cycle.lowerCurve.getAxisLabel(X, Units=cycle.units), fontsize='large')
        ax.set_ylabel(cycle.lowerCurve.getAxisLabel(Y, Units=cycle.units), fontsize='large')
        ax.set_title(cycle.name, fontsize='large')
        ax.tick_params(axis='both', which='both', direction='in', top=True, right=True, labelsize='large')
        for st in (dc(cycle.State1), dc(cycle.State2), dc(cycle.State3), dc(cycle.State4)):
            st.ConvertStateData(SI=cycle.getSI(), Units=cycle.units,
                                n=cycle.air.n, MW=cycle.air.MW,
                                mass=mass, total=total)
            ax.plot(st.getVal(X), st.getVal(Y), marker='o', markerfacecolor='w', markeredgecolor='k')
        if usingQT:
            self.canvas.draw()
        else:
            plt.show()

    def updateDisplayWidgets(self, cycle):
        U   = cycle.units
        SI  = U.SI
        CFT = 1.0 if SI else U.CF_T
        CFE = 1.0 if SI else U.CF_e
        self.lbl_THigh.setText(f'T High ({U.TUnits})')
        self.lbl_TLow.setText(f'T Low ({U.TUnits})')
        self.lbl_P0.setText(f'P0 ({U.PUnits})')
        self.lbl_V0.setText(f'V0 ({U.VUnits})')
        self.lbl_CR.setText(f'CR')
        self.lbl_CutoffRatio.setText('Cutoff Ratio (r\u209C)')
        self.le_T1.setText(f'{cycle.State1.T*CFT:0.2f}')
        self.le_T2.setText(f'{cycle.State2.T*CFT:0.2f}')
        self.le_T3.setText(f'{cycle.State3.T*CFT:0.2f}')
        self.le_T4.setText(f'{cycle.State4.T*CFT:0.2f}')
        self.lbl_T1Units.setText(U.TUnits)
        self.lbl_T2Units.setText(U.TUnits)
        self.lbl_T3Units.setText(U.TUnits)
        self.lbl_T4Units.setText(U.TUnits)
        self.le_Efficiency.setText(f'{cycle.Eff:0.3f}')
        self.le_PowerStroke.setText(f'{cycle.air.n*cycle.W_Power*CFE:0.3f}')
        self.le_CompressionStroke.setText(f'{cycle.air.n*cycle.W_Compression*CFE:0.3f}')
        self.le_HeatAdded.setText(f'{cycle.air.n*cycle.Q_In*CFE:0.3f}')
        self.lbl_PowerStrokeUnits.setText(U.EUnits)
        self.lbl_CompressionStrokeUnits.setText(U.EUnits)
        self.lbl_HeatInUnits.setText(U.EUnits)


if __name__ == '__main__':
    # quick smoke‑test when running Otto.py directly
    app = qtw.QApplication(sys.argv)
    ctrl = ottoCycleController()
    ctrl.calc()
    sys.exit(0)