import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons, Button
import os
import tempfile
import sys
import subprocess

# 全局绘图设置
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['lines.linewidth'] = 1.0
plt.rcParams['font.size'] = 10

# ===================== 绘图函数定义 =====================

def plot_vacuum_calibration(ax):
    """图1 真空度校准曲线"""
    ax.clear()
    delta_h = np.linspace(0, 1000, 100)
    Pv1 = 9.795 * delta_h
    ax.plot(delta_h, Pv1, 'k-', label='拟合直线 $P_v=9.795\Delta h$')
    key_h = [0, 200, 400, 600, 800, 1000]
    key_Pv1 = [9.795*h for h in key_h]
    ax.scatter(key_h, key_Pv1, c='r', s=20, zorder=5)
    ax.set_xlabel('液柱高度差 $\Delta h$ (mm)')
    ax.set_ylabel('表压真空度 $P_v$ (Pa)')
    ax.set_xlim(0, 1000)
    ax.set_ylim(0, 10000)
    ax.text(200, 8000, '$R^2=1.000$', fontsize=10)
    ax.legend()
    ax.set_title('图1 真空度-液柱高度差校准曲线')

def plot_friction_vs_vacuum(ax):
    """图2 摩擦系数-真空度曲线"""
    ax.clear()
    Pv2 = np.linspace(0, 101325, 200)
    f2 = 0.32 - 0.18 / (1 + np.exp(1.2e-4 * (Pv2 - 52000)))
    ax.plot(Pv2, f2, 'k-', label='拟合曲线 $f=0.32-\\frac{0.18}{1+e^{1.2\\times10^{-4}(P_v-52000)}}$')
    key_Pv2 = [0, 52000, 101325]
    key_f2 = [0.140, 0.230, 0.320]
    ax.scatter(key_Pv2, key_f2, c='r', s=20, zorder=5)
    ax.set_xlabel('表压真空度 $P_v$ (Pa)')
    ax.set_ylabel('滑动摩擦系数 $f$ (无量纲)')
    ax.set_xlim(0, 101325)
    ax.set_ylim(0.10, 0.35)
    ax.text(20000, 0.30, '$R^2=0.982$', fontsize=10)
    ax.legend(fontsize=9)
    ax.set_title('图2 滑动摩擦系数-真空度关系曲线')

def plot_friction_vs_pressure(ax):
    """图3 摩擦系数-正压力曲线"""
    ax.clear()
    FN3 = np.linspace(1, 4, 100)
    f3 = 0.472 * (FN3 ** (-0.315))
    ax.plot(FN3, f3, 'k-', label='拟合曲线 $f=0.472\\cdot F_N^{-0.315}$')
    key_FN3 = [1.0, 2.0, 3.0, 4.0]
    key_f3 = [0.472, 0.340, 0.287, 0.260]
    ax.scatter(key_FN3, key_f3, c='r', s=20, zorder=5)
    ax.set_xlabel('正压力 $F_N$ (N)')
    ax.set_ylabel('滑动摩擦系数 $f$ (无量纲)')
    ax.set_xlim(1, 4)
    ax.set_ylim(0.25, 0.48)
    ax.text(3.0, 0.45, '$R^2=0.974$', fontsize=10)
    ax.legend()
    ax.set_title('图3 滑动摩擦系数-正压力关系曲线（极限真空）')

def plot_friction_vs_speed(ax):
    """图4 摩擦系数-转速曲线"""
    ax.clear()
    n4 = np.linspace(300, 900, 100)
    f4 = -2.78e-7 * (n4 ** 2) + 3.33e-4 * n4 + 0.235
    ax.plot(n4, f4, 'k-', label='拟合曲线 $f=-2.78\\times10^{-7}n^2+3.33\\times10^{-4}n+0.235$')
    key_n4 = [300, 600, 900]
    key_f4 = [0.310, 0.335, 0.308]
    ax.scatter(key_n4, key_f4, c='r', s=20, zorder=5)
    ax.set_xlabel('转轴转速 $n$ (r/min)')
    ax.set_ylabel('滑动摩擦系数 $f$ (无量纲)')
    ax.set_xlim(300, 900)
    ax.set_ylim(0.30, 0.34)
    ax.text(700, 0.335, '$R^2=0.961$', fontsize=10)
    ax.legend(fontsize=9)
    ax.set_title('图4 滑动摩擦系数-转速关系曲线（极限真空+2N正压力）')

def plot_wear_vs_vacuum(ax):
    """图5 磨损量-真空度曲线"""
    ax.clear()
    Pv5 = np.linspace(0, 101325, 200)
    delta_m5 = 0.65 + 8.72e-6 * (Pv5 ** 1.28)
    ax.plot(Pv5, delta_m5, 'k-', label='拟合曲线 $\Delta m=0.65+8.72\\times10^{-6}\\cdot P_v^{1.28}$')
    key_Pv5 = [0, 50000, 101325]
    key_deltam5 = [0.65, 3.20, 9.20]
    ax.scatter(key_Pv5, key_deltam5, c='r', s=20, zorder=5)
    ax.set_xlabel('表压真空度 $P_v$ (Pa)')
    ax.set_ylabel('质量磨损量 $\Delta m$ (mg)')
    ax.set_xlim(0, 101325)
    ax.set_ylim(0, 10)
    ax.text(20000, 8, '$R^2=0.991$', fontsize=10)
    ax.legend(fontsize=9)
    ax.set_title('图5 试件质量磨损量-真空度关系曲线（30min摩擦）')

# 映射
plot_functions = {
    '图1: 真空度校准': plot_vacuum_calibration,
    '图2: 摩擦-真空度': plot_friction_vs_vacuum,
    '图3: 摩擦-正压力': plot_friction_vs_pressure,
    '图4: 摩擦-转速': plot_friction_vs_speed,
    '图5: 磨损-真空度': plot_wear_vs_vacuum,
}
plot_labels = list(plot_functions.keys())

# ===================== 全局对象，防止垃圾回收 =====================
app = {
    'fig': None,
    'ax': None,
    'radio': None,
    'preview_btn': None,
    'current_label': plot_labels[0]
}

# ===================== 功能函数 =====================

def switch_plot(label):
    app['current_label'] = label
    plot_functions[label](app['ax'])
    app['fig'].canvas.draw_idle()

def preview_and_print(event):
    """创建打印预览窗口"""
    preview_fig = plt.figure(figsize=(8, 6))
    preview_ax = preview_fig.add_subplot(111)
    
    # 在预览窗口中重绘当前选中的图表
    plot_functions[app['current_label']](preview_ax)
    preview_fig.suptitle('打印预览', fontsize=12, color='blue')
    
    # 在预览窗口中添加“确认打印”按钮
    ax_confirm = preview_fig.add_axes([0.4, 0.02, 0.2, 0.05])
    confirm_btn = Button(ax_confirm, '确认打印')
    
    def confirm_print(ev):
        # 隐藏按钮进行打印
        ax_confirm.set_visible(False)
        preview_fig.suptitle('') # 移除标题
        preview_fig.canvas.draw()
        
        filepath = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", mode='w+b') as tmpfile:
                preview_fig.savefig(tmpfile.name, format='pdf', dpi=300)
                filepath = tmpfile.name
            
            if filepath:
                if sys.platform == "win32":
                    os.startfile(filepath, "print")
                else:
                    subprocess.run(['lpr', filepath], check=True)
                print(f"已发送至打印队列: {filepath}")
        except Exception as e:
            print(f"打印失败: {e}")
        finally:
            ax_confirm.set_visible(True)
            preview_fig.suptitle('打印预览', fontsize=12, color='blue')
            preview_fig.canvas.draw()
            # 自动关闭预览窗口
            # plt.close(preview_fig)

    confirm_btn.on_clicked(confirm_print)
    # 必须保留按钮引用，防止被回收
    confirm_btn._confirm_ref = confirm_btn 
    
    preview_fig.tight_layout(rect=[0, 0.08, 1, 0.95])
    plt.show()

# ===================== 初始化界面 =====================

def init_ui():
    app['fig'] = plt.figure(figsize=(12, 8))
    app['fig'].canvas.manager.set_window_title('实验图表管理系统')
    
    # 绘图区域
    app['ax'] = app['fig'].add_axes([0.3, 0.15, 0.65, 0.75])
    
    # 单选按钮背景
    rax = app['fig'].add_axes([0.05, 0.45, 0.2, 0.4])
    rax.set_facecolor('#f0f0f0')
    app['radio'] = RadioButtons(rax, plot_labels, active=0, activecolor='red')
    app['radio'].on_clicked(switch_plot)
    
    # 预览打印按钮
    pax = app['fig'].add_axes([0.05, 0.3, 0.2, 0.08])
    app['preview_btn'] = Button(pax, '🔍 打印预览', color='lightblue', hovercolor='skyblue')
    app['preview_btn'].on_clicked(preview_and_print)
    
    # 默认绘制第一张图
    switch_plot(plot_labels[0])
    
    # 说明文字
    app['fig'].text(0.05, 0.2, '操作指南:\n1. 选择左侧列表切换图表\n2. 点击预览按钮打开新窗口\n3. 在预览窗口确认打印', 
                   fontsize=9, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.show()

if __name__ == "__main__":
    init_ui()
