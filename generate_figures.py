"""
生成文章用示意图PNG
生成3张核心创新点的示意图
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 颜色定义（符合文档规范）
COLOR_MAIN_CHANNEL = '#4A90E2'   # 主通道 蓝色
COLOR_NORMAL_CHANNEL = '#CCCCCC' # 普通通道 灰色
COLOR_UPDOWN_CHANNEL = '#9B59B6' # 上下巷道 紫色
COLOR_INTERFACE = '#FF9500'      # 接驳口 橙色
COLOR_OBSTACLE = '#000000'       # 障碍物 黑色
COLOR_CARGO = '#90EE90'          # 货物 浅绿色

COLOR_VEHICLE_1 = '#FF4444'      # 车辆1 红色
COLOR_VEHICLE_2 = '#FF69B4'      # 车辆2 玫红色
COLOR_VEHICLE_3 = '#DC143C'      # 车辆3 深红色
COLOR_PATH = '#00AA00'           # 路径 绿色
COLOR_LOCKED = COLOR_VEHICLE_1   # 锁定格子边框 与车辆颜色一致
COLOR_AVOID_PATH = '#0066FF'     # 避让路径 蓝色虚线
COLOR_CONFLICT = '#FFFF00'       # 冲突区域 黄色高亮

def create_grid_base(ax, width, height):
    """创建基础网格"""
    ax.set_xlim(-0.5, width - 0.5)
    ax.set_ylim(-0.5, height - 0.5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # 绘制网格线
    for x in range(width + 1):
        ax.plot([x - 0.5, x - 0.5], [-0.5, height - 0.5], 'k-', linewidth=0.5, alpha=0.3)
    for y in range(height + 1):
        ax.plot([-0.5, width - 0.5], [y - 0.5, y - 0.5], 'k-', linewidth=0.5, alpha=0.3)

def draw_cell(ax, x, y, cell_type='normal', locked=False, direction_lock=None, has_cargo=False):
    """绘制单个格子"""
    # 颜色选择
    if cell_type == 'main':
        color = COLOR_MAIN_CHANNEL
    elif cell_type == 'normal':
        color = COLOR_NORMAL_CHANNEL
    elif cell_type == 'updown':
        color = COLOR_UPDOWN_CHANNEL
    elif cell_type == 'interface':
        color = COLOR_INTERFACE
    elif cell_type == 'obstacle':
        color = COLOR_OBSTACLE
    else:
        color = 'white'
    
    # 绘制格子
    rect = patches.Rectangle(
        (x - 0.5, y - 0.5), 1, 1,
        facecolor=color,
        edgecolor='black',
        linewidth=1 if not locked else 3,
        alpha=0.6 if cell_type == 'normal' else 0.8
    )
    ax.add_patch(rect)
    
    # 锁定边框
    if locked:
        rect_lock = patches.Rectangle(
            (x - 0.5, y - 0.5), 1, 1,
            fill=False,
            edgecolor=COLOR_LOCKED,
            linewidth=3,
            linestyle='-'
        )
        ax.add_patch(rect_lock)
    
    # 方向锁箭头
    if direction_lock:
        if direction_lock == 'left':
            ax.annotate('', xy=(x - 0.3, y), xytext=(x + 0.3, y),
                       arrowprops=dict(arrowstyle='<-', color=COLOR_LOCKED, lw=2))
        elif direction_lock == 'right':
            ax.annotate('', xy=(x + 0.3, y), xytext=(x - 0.3, y),
                       arrowprops=dict(arrowstyle='->', color=COLOR_LOCKED, lw=2))
    
    # 坐标标注
    ax.text(x, y, f'({x},{y})', ha='center', va='center',
           fontsize=12, color='black', weight='bold')

    # 货物标记（仅用于示意图）
    if has_cargo:
        cargo_circle = patches.Circle((x, y), 0.25,
                                      facecolor='#FFB6B6',
                                      edgecolor='darkred',
                                      linewidth=1.5,
                                      alpha=0.9)
        ax.add_patch(cargo_circle)

def draw_vehicle(ax, x, y, vehicle_id, is_loaded=False, status='idle', vehicle_color=None):
    """绘制车辆
    空载车辆：长方形
    负载车辆：正方形
    最多三辆车：V1, V2, V3
    """
    # 根据vehicle_id确定颜色（V1, V2, V3对应不同颜色）
    if vehicle_color is None:
        if vehicle_id == 'V1':
            color = COLOR_VEHICLE_1
        elif vehicle_id == 'V2':
            color = COLOR_VEHICLE_2
        elif vehicle_id == 'V3':
            color = COLOR_VEHICLE_3
    
    # 根据负载状态选择图形：空载用长方形，负载用正方形
    # 长方形长度和正方形边长相同（都是0.8）
    if is_loaded:
        # 负载车辆：正方形（边长0.8）
        square = patches.Rectangle((x - 0.4, y - 0.4), 0.8, 0.8,
                                   facecolor=color,
                                   edgecolor='black',
                                   linewidth=2,
                                   zorder=10)
        ax.add_patch(square)
    else:
        # 空载车辆：长方形（长度0.8，高度0.4）
        rectangle = patches.Rectangle((x - 0.4, y - 0.2), 0.8, 0.4,
                                      facecolor=color,
                                      edgecolor='black',
                                      linewidth=2,
                                      zorder=10)
        ax.add_patch(rectangle)
    
    ax.text(x, y, vehicle_id, ha='center', va='center', 
           fontsize=12, color='white', weight='bold', zorder=11)
    
    # 状态标签
    status_text = '负载' if is_loaded else '空载'
    ax.text(x, y - 0.2, status_text, ha='center', va='top',
           fontsize=12, color='black', weight='bold', zorder=12,
           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

def draw_path(ax, path, color=COLOR_PATH, linewidth=2, linestyle='-', alpha=0.7):
    """绘制路径"""
    if len(path) < 2:
        return
    
    for i in range(len(path) - 1):
        x1, y1 = path[i]
        x2, y2 = path[i + 1]
        ax.plot([x1, x2], [y1, y2], color=color, linewidth=linewidth,
               linestyle=linestyle, alpha=alpha, zorder=5)
        
        # 箭头
        dx = x2 - x1
        dy = y2 - y1
        if dx != 0 or dy != 0:
            ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                       arrowprops=dict(arrowstyle='->', color=color, lw=linewidth, alpha=alpha))

def figure0_map_demo():
    """图0：网格地图格子类型说明示意图"""
    fig, ax = plt.subplots(figsize=(14, 10))
    # 地图格子 12 x 9
    width, height = 12, 9
    create_grid_base(ax, width, height)

    # 定义主通道行和子通道行
    main_channel_rows = [2, 6]  # 第2、6行为主通道
    sub_channel_rows = [0, 1, 3, 4, 5, 7, 8]  # 其余行为子通道

    # 先整体填充：2、6行为主通道，其余行为子通道（普通通道）
    for y in range(height):
        for x in range(width):
            if y in main_channel_rows:
                cell_type = 'main'
            else:
                cell_type = 'normal'
            draw_cell(ax, x, y, cell_type=cell_type)

    # 接驳口：(0,7)和(0,1)
    draw_cell(ax, 0, 7, cell_type='interface')
    draw_cell(ax, 0, 1, cell_type='interface')
    ax.text(0, 7.2, '接驳口', ha='center', va='bottom',
            fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    ax.text(0, 1.2, '接驳口', ha='center', va='bottom',
            fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    # 上下巷道：(2,3)到(2,5)，(9,3)到(9,5)
    for y in [3, 4, 5]:
        draw_cell(ax, 2, y, cell_type='updown')
        draw_cell(ax, 9, y, cell_type='updown')
    ax.text(2, 5.2, '上下巷道', ha='center', va='bottom',
            fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    ax.text(9, 5.2, '上下巷道', ha='center', va='bottom',
            fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    # 障碍物：(5,4)到(6,4)
    for x in [5, 6]:
        draw_cell(ax, x, 4, cell_type='obstacle')
    ax.text(5.5, 4.2, '障碍物', ha='center', va='bottom',
            fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    # 在指定位置放置货物（圆形）- 增大尺寸
    cargo_positions = [(3, 4), (6, 3), (10, 3), (2, 1), (3, 1), (6, 1), (3, 0), (4, 0), (5, 0), (11, 0), (4, 7)]
    
    # 绘制货物（圆形）- 半径从0.25增大到0.35
    for x, y in cargo_positions:
        cargo_circle = patches.Circle((x, y), 0.35,
                                      facecolor=COLOR_CARGO,
                                      edgecolor='darkgreen',
                                      linewidth=1.5,
                                      alpha=0.7,
                                      zorder=6)
        ax.add_patch(cargo_circle)
    
    # 在(4,7)位置上方添加"货物"文字标注
    ax.text(4, 7.2, '货物', ha='center', va='bottom',
            fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8), zorder=12)
    
    # 添加两辆车：一辆空载，一辆负载
    draw_vehicle(ax, 3, 6, 'V1', is_loaded=False, status='idle')  # 空载车辆V1（玫红色）
    draw_vehicle(ax, 4, 6, 'V2', is_loaded=True, status='deliver')  # 负载车辆V2（红色）

    # 标注说明
    ax.text(6, 6.2, '主通道（第2、6行）', ha='center', va='bottom',
            fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    ax.text(6, 8.2, '子通道（第0、1、3、4、5、7、8行）', ha='center', va='bottom',
            fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    # 图例
    # 创建空载车辆图例（长方形）
    empty_vehicle_legend = patches.Rectangle((0, 0), 0.8, 0.4, 
                                            facecolor=COLOR_VEHICLE_1,
                                            edgecolor='black',
                                            linewidth=1.5)
    # 创建负载车辆图例（正方形）
    loaded_vehicle_legend = plt.Line2D([0], [0], linewidth=0, label='负载车辆（正方形）')
    
    legend_elements = [
        patches.Patch(facecolor=COLOR_MAIN_CHANNEL, alpha=0.9, label='主通道'),
        patches.Patch(facecolor=COLOR_NORMAL_CHANNEL, alpha=0.9, label='货物格子（子通道）'),
        patches.Patch(facecolor=COLOR_UPDOWN_CHANNEL, alpha=0.9, label='上下巷道'),
        patches.Patch(facecolor=COLOR_INTERFACE, alpha=0.9, label='接驳口'),
        patches.Patch(facecolor=COLOR_OBSTACLE, alpha=0.9, label='障碍物'),
        patches.Patch(facecolor=COLOR_CARGO, edgecolor='darkgreen', alpha=0.7, label='货物（圆形）'),
        plt.Line2D([0], [0], linewidth=0, label='空载车辆（长方形）'),
        loaded_vehicle_legend,
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=14, framealpha=0.9)

    plt.tight_layout()
    filename = 'figure0_map_demo.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"已生成：{filename}")
    plt.close()

def figure1_segmented_locking():
    """图1：分段路径锁定策略示意图 - 四宫格布局"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    width, height = 10, 6
    main_channel_row = 4  # 第4行是主通道
    
    # 定义完整路径：从(7,4)到(2,4)再到(2,1)
    full_path_main = [(7, 4), (6, 4), (5, 4), (4, 4), (3, 4), (2, 4)]
    full_path_sub = [(2, 4), (2, 3), (2, 2), (2, 1), (2, 0)]
    full_path = full_path_main + full_path_sub[1:]  # 完整路径，去掉重复的(2,4)
    
    # ========== 左上：主通道滚动锁定 - 初始状态 ==========
    create_grid_base(ax1, width, height)
    
    # 创建地图：第4行是主通道，其他是子通道
    for y in range(height):
        for x in range(width):
            if y == main_channel_row:
                draw_cell(ax1, x, y, cell_type='main')
            else:
                draw_cell(ax1, x, y, cell_type='normal')
    
    # 标记完整路径（淡色显示，使用车辆颜色）
    main_path_seg = [(7, 4), (6, 4), (5, 4), (4, 4), (3, 4), (2, 4)]
    draw_path(ax1, main_path_seg, color=COLOR_VEHICLE_1, linewidth=3)
    transition_path = [(2, 4), (2, 3), (2, 2), (2, 1), (2, 0)]
    draw_path(ax1, transition_path, color=COLOR_VEHICLE_1, linewidth=3)
    
    # 在(2,0)放置货物
    cargo_circle1 = patches.Circle((2, 0), 0.25,
                                   facecolor=COLOR_CARGO,
                                   edgecolor='darkgreen',
                                   linewidth=1.5,
                                   alpha=0.7,
                                   zorder=6)
    ax1.add_patch(cargo_circle1)
    
    # 主通道路径（从(7,4)开始）- 当前阶段高亮
    main_path = [(7, 4), (6, 4), (5, 4), (4, 4), (3, 4)]
    draw_path(ax1, main_path, color=COLOR_VEHICLE_1, linewidth=3)
    
    # 锁定前3个主通道格子
    locked_cells = [(7, 4), (6, 4), (5, 4)]
    for x, y in locked_cells:
        draw_cell(ax1, x, y, cell_type='main', locked=True)
    
    # 车辆
    draw_vehicle(ax1, 7, 4, 'V1', is_loaded=False)
    
    # 标注
    ax1.text(5, 4.5, '锁定范围：前3个主通道格子', ha='center', va='bottom',
           fontsize=12, weight='bold', color=COLOR_LOCKED,
           bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', alpha=0.7))
    
    ax1.text(5, 2, '主通道滚动锁定', ha='center', va='center',
           fontsize=12, weight='bold',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='lightblue', alpha=0.8))
    
    # 左上图例
    legend_elements1 = [
        patches.Patch(facecolor=COLOR_MAIN_CHANNEL, alpha=0.8, label='主通道'),
        patches.Patch(facecolor=COLOR_NORMAL_CHANNEL, alpha=0.6, label='子通道'),
        patches.Patch(facecolor='none', edgecolor=COLOR_LOCKED, linewidth=3, label='锁定格子'),
        patches.Circle((0, 0), 0.1, facecolor=COLOR_CARGO, edgecolor='darkgreen', label='货物'),
    ]
    ax1.legend(handles=legend_elements1, loc='upper right', fontsize=14, framealpha=0.9)
    
    # ========== 右上：主通道滚动锁定 - 移动后 ==========
    create_grid_base(ax2, width, height)
    
    # 创建地图：第4行是主通道，其他是子通道
    for y in range(height):
        for x in range(width):
            if y == main_channel_row:
                draw_cell(ax2, x, y, cell_type='main')
            else:
                draw_cell(ax2, x, y, cell_type='normal')
    
    # 标记完整路径（淡色显示，使用车辆颜色）
    main_path_seg2 = [(7, 4), (6, 4), (5, 4), (4, 4), (3, 4), (2, 4)]
    draw_path(ax2, main_path_seg2, color=COLOR_VEHICLE_1, linewidth=3)
    transition_path2 = [(2, 4), (2, 3), (2, 2), (2, 1), (2, 0)]
    draw_path(ax2, transition_path2, color=COLOR_VEHICLE_1, linewidth=3)
    
    # 在(2,0)放置货物
    cargo_circle2 = patches.Circle((2, 0), 0.25,
                                   facecolor=COLOR_CARGO,
                                   edgecolor='darkgreen',
                                   linewidth=1.5,
                                   alpha=0.7,
                                   zorder=6)
    ax2.add_patch(cargo_circle2)
    
    # 主通道路径（车辆移动后）- 当前阶段高亮
    main_path2 = [(6, 4), (5, 4), (4, 4), (3, 4), (2, 4)]
    draw_path(ax2, main_path2, color=COLOR_VEHICLE_1, linewidth=3)
    
    # 锁定范围滚动：前3个主通道格子
    locked_cells2 = [(6, 4), (5, 4), (4, 4)]
    for x, y in locked_cells2:
        draw_cell(ax2, x, y, cell_type='main', locked=True)
    
    # 车辆
    draw_vehicle(ax2, 6, 4, 'V1', is_loaded=False)
    
    # 标注
    ax2.text(4, 4.5, '锁定范围滚动', ha='center', va='bottom',
           fontsize=12, weight='bold', color=COLOR_LOCKED,
           bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', alpha=0.7))
    
    ax2.text(5, 2, '主通道滚动锁定', ha='center', va='center',
           fontsize=12, weight='bold',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='lightblue', alpha=0.8))
    
    # 右上图例
    legend_elements2 = [
        patches.Patch(facecolor=COLOR_MAIN_CHANNEL, alpha=0.8, label='主通道'),
        patches.Patch(facecolor=COLOR_NORMAL_CHANNEL, alpha=0.6, label='子通道'),
        patches.Patch(facecolor='none', edgecolor=COLOR_LOCKED, linewidth=3, label='锁定格子'),
        patches.Circle((0, 0), 0.1, facecolor=COLOR_CARGO, edgecolor='darkgreen', label='货物'),
    ]
    ax2.legend(handles=legend_elements2, loc='upper right', fontsize=14, framealpha=0.9)
    
    # ========== 左下：子通道全程锁定 - 进入子通道 ==========
    create_grid_base(ax3, width, height)
    
    # 创建地图：第4行是主通道，其他是子通道
    for y in range(height):
        for x in range(width):
            if y == main_channel_row:
                draw_cell(ax3, x, y, cell_type='main')
            else:
                draw_cell(ax3, x, y, cell_type='normal')
    
    # 完整路径：从(7,4)到(2,4)再到(2,0)
    # 主通道段
    main_path_seg = [(7, 4), (6, 4), (5, 4), (4, 4), (3, 4), (2, 4)]
    draw_path(ax3, main_path_seg, color=COLOR_VEHICLE_1, linewidth=3)
    
    # 从主通道到子通道的过渡
    transition_path = [(2, 4), (2, 3), (2, 2), (2, 1), (2, 0)]
    draw_path(ax3, transition_path, color=COLOR_VEHICLE_1, linewidth=3)
    
    # 子通道全程锁定（从主通道到目标点的子通道段）
    locked_sub_cells = [(2, 4), (2, 3), (2, 2), (2, 1), (2, 0)]
    for x, y in locked_sub_cells:
        if y != main_channel_row:  # 只锁定子通道部分
            draw_cell(ax3, x, y, cell_type='normal', locked=True)
    
    # 车辆
    draw_vehicle(ax3, 2, 2, 'V1', is_loaded=False)
    
    # 在(2,0)放置货物
    cargo_circle3 = patches.Circle((2, 0), 0.25,
                                   facecolor=COLOR_CARGO,
                                   edgecolor='darkgreen',
                                   linewidth=1.5,
                                   alpha=0.7,
                                   zorder=6)
    ax3.add_patch(cargo_circle3)
    
    # 标注
    ax3.text(2, 0.5, '子通道全程锁定', ha='center', va='top',
           fontsize=12, weight='bold', color=COLOR_VEHICLE_1,
           bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen', alpha=0.7))
    
    ax3.text(5, 5, '子通道全程锁定', ha='center', va='center',
           fontsize=12, weight='bold',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen', alpha=0.8))
    
    # 左下图例
    legend_elements3 = [
        patches.Patch(facecolor=COLOR_MAIN_CHANNEL, alpha=0.8, label='主通道'),
        patches.Patch(facecolor=COLOR_NORMAL_CHANNEL, alpha=0.6, label='子通道'),
        patches.Patch(facecolor='none', edgecolor=COLOR_LOCKED, linewidth=3, label='锁定格子'),
        patches.Circle((0, 0), 0.1, facecolor=COLOR_CARGO, edgecolor='darkgreen', label='货物'),
    ]
    ax3.legend(handles=legend_elements3, loc='upper right', fontsize=14, framealpha=0.9)
    
    # ========== 右下：子通道全程锁定 - 到达目标 ==========
    create_grid_base(ax4, width, height)
    
    # 创建地图：第4行是主通道，其他是子通道
    for y in range(height):
        for x in range(width):
            if y == main_channel_row:
                draw_cell(ax4, x, y, cell_type='main')
            else:
                draw_cell(ax4, x, y, cell_type='normal')
    
    # 完整路径：从(7,4)到(2,4)再到(2,0)
    # 主通道段
    main_path_seg2 = [(7, 4), (6, 4), (5, 4), (4, 4), (3, 4), (2, 4)]
    draw_path(ax4, main_path_seg2, color=COLOR_VEHICLE_1, linewidth=3)
    
    # 从主通道到子通道的过渡
    transition_path2 = [(2, 4), (2, 3), (2, 2), (2, 1), (2, 0)]
    draw_path(ax4, transition_path2, color=COLOR_VEHICLE_1, linewidth=3)
    
    # 子通道全程锁定（从主通道到目标点的子通道段）
    locked_sub_cells2 = [(2, 4), (2, 3), (2, 2), (2, 1), (2, 0)]
    for x, y in locked_sub_cells2:
        if y != main_channel_row:  # 只锁定子通道部分
            draw_cell(ax4, x, y, cell_type='normal', locked=True)
    
    # 车辆
    draw_vehicle(ax4, 2, 0, 'V1', is_loaded=False)
    
    # 在(2,0)放置圆形货物
    cargo_circle4 = patches.Circle((2, 0), 0.25,
                                   facecolor=COLOR_CARGO,
                                   edgecolor='darkgreen',
                                   linewidth=1.5,
                                   alpha=0.7,
                                   zorder=6)
    ax4.add_patch(cargo_circle4)
    
    # 标注
    ax4.text(2, 0.5, '子通道全程锁定', ha='center', va='top',
           fontsize=12, weight='bold', color=COLOR_VEHICLE_1,
           bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen', alpha=0.7))
    
    ax4.text(5, 5, '子通道全程锁定', ha='center', va='center',
           fontsize=12, weight='bold',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen', alpha=0.8))
    
    # 右下图例
    legend_elements4 = [
        patches.Patch(facecolor=COLOR_MAIN_CHANNEL, alpha=0.8, label='主通道'),
        patches.Patch(facecolor=COLOR_NORMAL_CHANNEL, alpha=0.6, label='子通道'),
        patches.Patch(facecolor='none', edgecolor=COLOR_LOCKED, linewidth=3, label='锁定格子'),
        patches.Circle((0, 0), 0.1, facecolor=COLOR_CARGO, edgecolor='darkgreen', label='货物'),
    ]
    ax4.legend(handles=legend_elements4, loc='upper right', fontsize=14, framealpha=0.9)
    
    plt.tight_layout()
    filename = 'figure1_segmented_locking.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"已生成：{filename}")
    plt.close()

def figure2_smart_avoidance():
    """图2：智能避让策略示意图"""
    fig, ax = plt.subplots(figsize=(16, 8))
    create_grid_base(ax, 15, 10)
    
    # 创建主通道（y=7）
    for x in range(15):
        draw_cell(ax, x, 7, cell_type='main')
    
    # 创建其他主通道行（y=5, y=9）
    for x in range(15):
        draw_cell(ax, x, 5, cell_type='main')
        draw_cell(ax, x, 9, cell_type='main')
    
    # 车辆V1（空载，在(6,7)）
    draw_vehicle(ax, 6, 7, 'V1', is_loaded=False, status='idle')
    
    # 车辆V2（负载，在(12,7)）
    draw_vehicle(ax, 12, 7, 'V2', is_loaded=True, status='deliver')
    
    # V2的规划路径
    v2_path = [(12, 7), (11, 7), (10, 7), (9, 7), (8, 7), (7, 7)]
    draw_path(ax, v2_path, color=COLOR_VEHICLE_2, linewidth=3)
    
    # 冲突区域（黄色高亮）
    conflict_rect = patches.Rectangle((6 - 0.5, 7 - 0.5), 2, 1,
                                     facecolor=COLOR_CONFLICT, alpha=0.4, zorder=1)
    ax.add_patch(conflict_rect)
    ax.text(7, 7, '冲突区域', ha='center', va='center',
           fontsize=12, weight='bold', color='black',
           bbox=dict(boxstyle='round,pad=0.3', facecolor=COLOR_CONFLICT, alpha=0.8))
    
    # V1的避让路径（虚线）
    avoid_path = [(6, 7), (6, 6), (6, 5)]
    draw_path(ax, avoid_path, color=COLOR_AVOID_PATH, linewidth=2, linestyle='--')
    
    # 避让位置标注
    draw_vehicle(ax, 6, 5, 'V1', is_loaded=False, status='avoiding')
    ax.text(6, 4.5, '避让位置', ha='center', va='top',
           fontsize=10, color='blue', weight='bold',
           bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.8))
    
    # 决策规则标注
    ax.text(9, 9, '决策规则：\n负载车优先\n空载车避让', ha='center', va='center',
           fontsize=12, weight='bold',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8))
    
    # 箭头：V1给V2让路
    arrow = FancyArrowPatch((6, 7.5), (12, 7.5),
                           arrowstyle='->', mutation_scale=20,
                           color='red', linewidth=2)
    ax.add_patch(arrow)
    ax.text(9, 8, 'V1给V2让路', ha='center', va='bottom',
           fontsize=12, weight='bold', color='red')
    
    # 图例
    legend_elements = [
        patches.Patch(facecolor=COLOR_VEHICLE_1, label='空载车辆'),
        patches.Patch(facecolor=COLOR_VEHICLE_2, label='负载车辆'),
        plt.Line2D([0], [0], color=COLOR_VEHICLE_2, linewidth=3, label='负载车路径'),
        plt.Line2D([0], [0], color=COLOR_AVOID_PATH, linewidth=2, linestyle='--', label='避让路径'),
        patches.Patch(facecolor=COLOR_CONFLICT, alpha=0.4, label='冲突区域'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=14, framealpha=0.9)
    
    ax.set_title('图2. 基于负载状态的智能避让策略\n（负载车优先，空载车避让）', 
                fontsize=14, weight='bold', pad=20)
    
    plt.tight_layout()
    filename = 'figure2_smart_avoidance.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"已生成：{filename}")
    plt.close()

def figure3_direction_lock():
    """图3：动态方向锁定机制示意图"""
    fig, ax = plt.subplots(figsize=(18, 8))
    create_grid_base(ax, 18, 10)
    
    # 创建主通道（y=7）
    for x in range(18):
        draw_cell(ax, x, 7, cell_type='main')
    
    # V1（负载，向左行驶）
    draw_vehicle(ax, 15, 7, 'V1', is_loaded=True, status='deliver')
    
    # V1的路径
    v1_path = [(15, 7), (14, 7), (13, 7), (12, 7), (11, 7), (10, 7), (9, 7), (8, 7)]
    draw_path(ax, v1_path, color=COLOR_VEHICLE_2, linewidth=3)
    
    # 方向锁定（向左箭头）
    locked_positions = [(15, 7), (14, 7), (13, 7), (12, 7), (11, 7), (10, 7), (9, 7), (8, 7)]
    for x, y in locked_positions:
        draw_cell(ax, x, y, cell_type='main', locked=True, direction_lock='left')
    
    # V2（空载，尝试向右行驶）
    draw_vehicle(ax, 3, 7, 'V2', is_loaded=False, status='idle')
    
    # V2尝试的路径（被阻止）
    v2_attempt_path = [(3, 7), (4, 7), (5, 7), (6, 7), (7, 7), (8, 7), (9, 7), (10, 7)]
    draw_path(ax, v2_attempt_path, color='gray', linewidth=2, linestyle=':', alpha=0.5)
    
    # 标注被阻止的路径段
    blocked_positions = [(8, 7), (9, 7), (10, 7)]
    for x, y in blocked_positions:
        ax.text(x, y + 0.4, '✗', ha='center', va='center',
               fontsize=20, color='red', weight='bold')
        ax.text(x, y - 0.4, 'X', ha='center', va='center',
               fontsize=16, color='red', weight='bold',
               bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.8))
    
    # 对比说明
    # 左侧：无方向锁的情况（死锁风险）
    ax.text(4.5, 5, '无方向锁：\n死锁风险', ha='center', va='center',
           fontsize=12, weight='bold',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='red', alpha=0.3))
    
    # 右侧：有方向锁的情况（死锁已预防）
    ax.text(13.5, 5, '有方向锁：\n死锁已预防', ha='center', va='center',
           fontsize=12, weight='bold',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='green', alpha=0.3))
    
    # 说明文字
    ax.text(9, 8.5, '负载车V1建立向左方向锁，阻止对向车辆V2进入', 
           ha='center', va='center',
           fontsize=12, weight='bold',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8))
    
    # 图例
    legend_elements = [
        patches.Patch(facecolor=COLOR_VEHICLE_2, label='负载车辆'),
        patches.Patch(facecolor=COLOR_VEHICLE_1, label='空载车辆'),
        patches.Patch(facecolor='none', edgecolor=COLOR_LOCKED, linewidth=3, label='方向锁定'),
        plt.Line2D([0], [0], color=COLOR_VEHICLE_2, linewidth=3, label='负载车路径'),
        plt.Line2D([0], [0], color='gray', linewidth=2, linestyle=':', label='被阻止的路径'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=14, framealpha=0.9)
    
    ax.set_title('图3. 动态方向锁定机制预防死锁示意图', 
                fontsize=14, weight='bold', pad=20)
    
    plt.tight_layout()
    filename = 'figure3_direction_lock.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"已生成：{filename}")
    plt.close()

if __name__ == '__main__':
    # 先生成地图类型说明示意图，便于文章中统一解释
    figure0_map_demo()
    figure1_segmented_locking()
    # figure2_smart_avoidance()
    # figure3_direction_lock()