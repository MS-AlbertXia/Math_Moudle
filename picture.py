import sys
import os
import tempfile
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QFrame, QScrollArea, QSizePolicy)

from qfluentwidgets import (NavigationInterface, NavigationItemPosition, NavigationWidget,
                            MessageBox, PrimaryPushButton, FluentWindow,
                            SubtitleLabel, setFont, Theme, setTheme, FluentIcon as FIF,
                            DoubleSpinBox, BodyLabel, SettingCardGroup, ExpandLayout,
                            ScrollArea, SettingCard)

# 全局绘图设置
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['lines.linewidth'] = 1.0
plt.rcParams['font.size'] = 10

# ===================== 数据模型：管理图表数据 =====================

class PlotData:
    def __init__(self):
        # 原有数据
        self.calib_h = [0, 200, 400, 600, 800, 1000]
        self.calib_Pv = [0, 1959, 3918, 5877, 7836, 9795] # 9.795 * h
        
        self.f_vac_Pv = [0, 52000, 101325]
        self.f_vac_f = [0.140, 0.230, 0.320]
        
        self.f_press_FN = [1.0, 2.0, 3.0, 4.0]
        self.f_press_f = [0.472, 0.340, 0.287, 0.260]
        
        self.f_speed_n = [300, 600, 900]
        self.f_speed_f = [0.310, 0.335, 0.308]
        
        self.wear_Pv = [0, 50000, 101325]
        self.wear_dm = [0.65, 3.20, 9.20]

        # 新增：实验一 敲击力度-打开扭矩数据
        self.tap_force_F = [5, 10, 15, 20]  # 敲击力度 (N)
        self.tap_torque_T = [3.2, 1.8, 2.5, 4.1]  # 打开所需扭矩 (N·m)

global_data = PlotData()

# ===================== 绘图逻辑 (支持动态数据) =====================

def plot_vacuum_calibration(ax, data):
    ax.clear()
    h = np.linspace(0, 1000, 100)
    slope = data.calib_Pv[-1] / data.calib_h[-1] if data.calib_h[-1] != 0 else 9.795
    Pv = slope * h
    ax.plot(h, Pv, 'k-', label=f'拟合直线 $P_v={slope:.3f}\Delta h$')
    ax.scatter(data.calib_h, data.calib_Pv, c='r', s=20, zorder=5)
    ax.set_xlabel('液柱高度差 $\Delta h$ (mm)')
    ax.set_ylabel('表压真空度 $P_v$ (Pa)')
    ax.set_xlim(0, 1000)
    ax.set_ylim(0, 12000)
    ax.legend()
    ax.set_title('图1 真空度-液柱高度差校准曲线')

def plot_friction_vs_vacuum(ax, data):
    ax.clear()
    Pv = np.linspace(0, 101325, 200)
    f = 0.14 + (0.32 - 0.14) / (1 + np.exp(-1.2e-4 * (Pv - 52000)))
    ax.plot(Pv, f, 'k-', label='拟合曲线 $f=f(P_v)$')
    ax.scatter(data.f_vac_Pv, data.f_vac_f, c='r', s=20, zorder=5)
    ax.set_xlabel('表压真空度 $P_v$ (Pa)')
    ax.set_ylabel('滑动摩擦系数 $f$ (无量纲)')
    ax.set_xlim(0, 101325)
    ax.set_ylim(0.10, 0.40)
    ax.legend(fontsize=9)
    ax.set_title('图2 滑动摩擦系数-真空度关系曲线')

def plot_friction_vs_pressure(ax, data):
    ax.clear()
    FN = np.linspace(1, 4, 100)
    f = 0.472 * (FN ** (-0.315))
    ax.plot(FN, f, 'k-', label='拟合曲线 $f=0.472\\cdot F_N^{-0.315}$')
    ax.scatter(data.f_press_FN, data.f_press_f, c='r', s=20, zorder=5)
    ax.set_xlabel('正压力 $F_N$ (N)')
    ax.set_ylabel('滑动摩擦系数 $f$ (无量纲)')
    ax.set_xlim(1, 4)
    ax.set_ylim(0.20, 0.50)
    ax.legend()
    ax.set_title('图3 滑动摩擦系数-正压力关系曲线（极限真空）')

def plot_friction_vs_speed(ax, data):
    ax.clear()
    n = np.linspace(300, 900, 100)
    f = -2.78e-7 * (n ** 2) + 3.33e-4 * n + 0.235
    ax.plot(n, f, 'k-', label='拟合曲线')
    ax.scatter(data.f_speed_n, data.f_speed_f, c='r', s=20, zorder=5)
    ax.set_xlabel('转轴转速 $n$ (r/min)')
    ax.set_ylabel('滑动摩擦系数 $f$ (无量纲)')
    ax.set_xlim(300, 900)
    ax.set_ylim(0.25, 0.40)
    ax.legend(fontsize=9)
    ax.set_title('图4 滑动摩擦系数-转速关系曲线')

def plot_wear_vs_vacuum(ax, data):
    ax.clear()
    Pv = np.linspace(0, 101325, 200)
    dm = 0.65 + 8.72e-6 * (Pv ** 1.28)
    ax.plot(Pv, dm, 'k-', label='拟合曲线')
    ax.scatter(data.wear_Pv, data.wear_dm, c='r', s=20, zorder=5)
    ax.set_xlabel('表压真空度 $P_v$ (Pa)')
    ax.set_ylabel('质量磨损量 $\Delta m$ (mg)')
    ax.set_xlim(0, 101325)
    ax.set_ylim(0, 12)
    ax.legend(fontsize=9)
    ax.set_title('图5 试件质量磨损量-真空度关系曲线')

# 新增：实验一 敲击力度-打开扭矩绘图函数
def plot_tap_force_vs_torque(ax, data):
    ax.clear()
    # 生成拟合用的连续力度区间
    F = np.linspace(0, 25, 200)
    # 二次函数拟合 (T = aF² + bF + c)
    fit_coeff = np.polyfit(data.tap_force_F, data.tap_torque_T, 2)
    a, b, c = fit_coeff
    T = a * F**2 + b * F + c
    # 计算最优敲击力度（二次函数顶点：F_opt = -b/(2a)）
    F_opt = -b/(2*a) if a != 0 else 10
    T_opt = a * F_opt**2 + b * F_opt + c
    
    # 绘制拟合曲线和实验点
    ax.plot(F, T, 'k-', label=f'拟合曲线 $T={a:.4f}F^2 + {b:.4f}F + {c:.4f}$')
    ax.scatter(data.tap_force_F, data.tap_torque_T, c='r', s=30, zorder=5, label='实验数据')
    # 标注最优敲击力度点
    ax.scatter(F_opt, T_opt, c='blue', s=50, marker='*', zorder=6, label=f'最优力度 F={F_opt:.1f}N')
    
    # 图表样式设置
    ax.set_xlabel('敲击力度 $F$ (N)')
    ax.set_ylabel('打开罐头所需扭矩 $T$ (N·m)')
    ax.set_xlim(0, 25)
    ax.set_ylim(0, 5)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    ax.set_title('实验一 敲击力度对罐头打开难易度的影响曲线')

# ===================== UI 界面组件 =====================

class DataEditCard(QFrame):
    """单行数据编辑卡片（优化排版：支持长标签换行）"""
    valueChanged = pyqtSignal(float)
    
    def __init__(self, label_text, value, min_v=0, max_v=1000000, step=0.01, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(85)
        self.setFixedWidth(330)
        # Fluent 风格卡片样式
        self.setStyleSheet("""
            DataEditCard {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }
            DataEditCard:hover {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(0, 0, 0, 0.2);
            }
        """)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 10, 15, 10)
        self.layout.setSpacing(10)
        
        # 标签：支持换行且占据大部分空间
        self.label = BodyLabel(label_text, self)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.layout.addWidget(self.label, 1) 
        
        # 数值输入框：固定合适宽度
        self.spinBox = DoubleSpinBox(self)
        self.spinBox.setRange(min_v, max_v)
        self.spinBox.setValue(value)
        self.spinBox.setSingleStep(step)
        self.spinBox.setFixedWidth(165) 
        self.layout.addWidget(self.spinBox, 0, Qt.AlignRight)
        
        self.spinBox.valueChanged.connect(self.valueChanged.emit)

class EditorPanel(ScrollArea):
    """侧边编辑面板（优化排版）"""
    dataUpdated = pyqtSignal()
    
    def __init__(self, chart_type, parent=None):
        super().__init__(parent=parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.viewport().setStyleSheet("background-color: transparent;")
        self.setStyleSheet("ScrollArea { background-color: transparent; border: none; }")
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: transparent;")
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(15)
        self.setWidget(self.container)
        
        # 标题标签代替 SettingCardGroup 以获得更好的排版控制
        self.titleLabel = SubtitleLabel("📊 数据编辑", self.container)
        self.layout.addWidget(self.titleLabel)
        
        self.init_controls(chart_type)
        self.layout.addStretch(1) # 底部留白
        
    def init_controls(self, chart_type):
        if chart_type == 'vacuum_calibration':
            for i in range(len(global_data.calib_h)):
                card = DataEditCard(f"高度差 {global_data.calib_h[i]}mm 的真空度:", global_data.calib_Pv[i])
                card.valueChanged.connect(lambda v, idx=i: self.update_val('calib_Pv', idx, v))
                self.layout.addWidget(card)
                
        elif chart_type == 'friction_vs_vacuum':
            for i in range(len(global_data.f_vac_Pv)):
                card = DataEditCard(f"真空度 {global_data.f_vac_Pv[i]}Pa 的摩擦系数:", global_data.f_vac_f[i], step=0.001)
                card.valueChanged.connect(lambda v, idx=i: self.update_val('f_vac_f', idx, v))
                self.layout.addWidget(card)
                
        elif chart_type == 'friction_vs_pressure':
            for i in range(len(global_data.f_press_FN)):
                card = DataEditCard(f"正压力 {global_data.f_press_FN[i]}N 的摩擦系数:", global_data.f_press_f[i], step=0.001)
                card.valueChanged.connect(lambda v, idx=i: self.update_val('f_press_f', idx, v))
                self.layout.addWidget(card)

        elif chart_type == 'friction_vs_speed':
            for i in range(len(global_data.f_speed_n)):
                card = DataEditCard(f"转速 {global_data.f_speed_n[i]}rpm 的摩擦系数:", global_data.f_speed_f[i], step=0.001)
                card.valueChanged.connect(lambda v, idx=i: self.update_val('f_speed_f', idx, v))
                self.layout.addWidget(card)

        elif chart_type == 'wear_vs_vacuum':
            for i in range(len(global_data.wear_Pv)):
                card = DataEditCard(f"真空度 {global_data.wear_Pv[i]}Pa 的磨损量:", global_data.wear_dm[i], step=0.1)
                card.valueChanged.connect(lambda v, idx=i: self.update_val('wear_dm', idx, v))
                self.layout.addWidget(card)

        # 新增：实验一数据编辑
        elif chart_type == 'tap_force_vs_torque':
            for i in range(len(global_data.tap_force_F)):
                card = DataEditCard(
                    f"敲击力度 {global_data.tap_force_F[i]}N 的打开扭矩:", 
                    global_data.tap_torque_T[i], 
                    min_v=0, max_v=10, step=0.01
                )
                card.valueChanged.connect(lambda v, idx=i: self.update_val('tap_torque_T', idx, v))
                self.layout.addWidget(card)

    def update_val(self, attr, idx, val):
        getattr(global_data, attr)[idx] = val
        self.dataUpdated.emit()

class ChartWidget(QWidget):
    """集成 Toolbar 和 Editor 的图表组件"""
    def __init__(self, plot_func, chart_type, parent=None):
        super().__init__(parent=parent)
        self.plot_func = plot_func
        self.chart_type = chart_type
        self.setObjectName(chart_type)
        
        self.mainLayout = QHBoxLayout(self)
        self.chartLayout = QVBoxLayout()
        
        # Matplotlib 图表部分
        self.figure = Figure(figsize=(7, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # Matplotlib 导航工具栏
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet("background-color: transparent; border: none;")
        
        self.chartLayout.addWidget(self.toolbar)
        self.chartLayout.addWidget(self.canvas)
        
        # 侧边编辑面板
        self.editor = EditorPanel(chart_type, self)
        self.editor.setFixedWidth(350)
        self.editor.dataUpdated.connect(self.update_plot)
        
        self.mainLayout.addLayout(self.chartLayout, 1)
        self.mainLayout.addSpacing(20)
        self.mainLayout.addWidget(self.editor)
        
        self.update_plot()

    def update_plot(self):
        self.plot_func(self.ax, global_data)
        self.canvas.draw()

class MainWindow(FluentWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle('开罐头方法实验数据可视化与视图编辑系统')
        
        # 初始化图表组件 (包含新增实验一)
        self.charts = {
            'vacuum_calibration': ChartWidget(plot_vacuum_calibration, 'vacuum_calibration', self),
            'friction_vs_vacuum': ChartWidget(plot_friction_vs_vacuum, 'friction_vs_vacuum', self),
            'friction_vs_pressure': ChartWidget(plot_friction_vs_pressure, 'friction_vs_pressure', self),
            'friction_vs_speed': ChartWidget(plot_friction_vs_speed, 'friction_vs_speed', self),
            'wear_vs_vacuum': ChartWidget(plot_wear_vs_vacuum, 'wear_vs_vacuum', self),
            'tap_force_vs_torque': ChartWidget(plot_tap_force_vs_torque, 'tap_force_vs_torque', self), # 新增实验一
        }
        
        # 添加子界面
        self.addSubInterface(self.charts['vacuum_calibration'], FIF.CALENDAR, '真空度校准')
        self.addSubInterface(self.charts['friction_vs_vacuum'], FIF.EDIT, '摩擦-真空度')
        self.addSubInterface(self.charts['friction_vs_pressure'], FIF.DEVELOPER_TOOLS, '摩擦-正压力')
        self.addSubInterface(self.charts['friction_vs_speed'], FIF.SPEED_HIGH, '摩擦-转速')
        self.addSubInterface(self.charts['wear_vs_vacuum'], FIF.BASKETBALL, '磨损-真空度')
        self.addSubInterface(self.charts['tap_force_vs_torque'], FIF.TAG, '实验一 敲击力度-打开扭矩') # 新增
        
        # 页脚打印
        self.navigationInterface.addItem(
            routeKey='print',
            icon=FIF.PRINT,
            text='导出/打印当前图表',
            onClick=self.showPrintDialog,
            position=NavigationItemPosition.BOTTOM
        )
        
        self.resize(1300, 850)
        
    def showPrintDialog(self):
        current_widget = self.stackedWidget.currentWidget()
        if not isinstance(current_widget, ChartWidget):
            return
            
        w = MessageBox("确认打印", "确定要打印当前图表并保存为 PDF 吗？", self)
        if w.exec():
            self.doPrint(current_widget)
            
    def doPrint(self, chart_widget):
        filepath = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", mode='w+b') as tmpfile:
                print_fig = Figure(figsize=(8, 6), dpi=300)
                print_ax = print_fig.add_subplot(111)
                chart_widget.plot_func(print_ax, global_data)
                print_fig.savefig(tmpfile.name, format='pdf')
                filepath = tmpfile.name
            
            if filepath:
                if sys.platform == "win32":
                    os.startfile(filepath, "print")
                else:
                    subprocess.run(['lpr', filepath], check=True)
                
                w = MessageBox("成功", f"图表已打印。\n临时路径: {filepath}", self)
                w.cancelButton.hide()
                w.exec()
        except Exception as e:
            MessageBox("失败", str(e), self).exec()

if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    setTheme(Theme.LIGHT)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())