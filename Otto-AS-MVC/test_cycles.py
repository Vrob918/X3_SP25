from Otto import ottoCycleModel, ottoCycleView
from matplotlib import pyplot as plt

# 1) Otto cycle smoke‑test
m_otto = ottoCycleModel(
    p_initial=1e5,
    v_cylinder=0.0001,
    t_initial=300,
    t_high=800,
    ratio=8,
    name='Air Standard Otto Cycle'
)
print("Otto model.name =", m_otto.name)

fig1, ax1 = plt.subplots()
view1 = ottoCycleView()
view1.ax = ax1
view1.canvas = fig1.canvas        # <<— ensure view has a canvas before drawing
view1.plot_cycle_XY(m_otto, X='v', Y='P', total=True)

# 2) Diesel cycle smoke‑test
m_diesel = ottoCycleModel()       # fresh model, name resets to default
m_diesel.run_diesel_cycle(
    p_initial=1e5,
    v_cylinder=0.0001,
    t_initial=300,
    compression_ratio=18,
    cutoff_ratio=2
)
print("Diesel model.name =", m_diesel.name)

fig2, ax2 = plt.subplots()
view2 = ottoCycleView()
view2.ax = ax2
view2.canvas = fig2.canvas        # <<— same fix here
view2.plot_cycle_XY(m_diesel, X='v', Y='P', total=True)

plt.show()