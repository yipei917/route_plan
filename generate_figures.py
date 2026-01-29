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

def draw_cell(ax, x, y, cell_type='normal', locked=False, direction_lock=None, has_cargo=False, lock_color=None):
    """绘制单个格子。lock_color 为 None 时使用 COLOR_LOCKED（红色），可指定以区分不同车的锁定。"""
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
        ec = lock_color if lock_color is not None else COLOR_LOCKED
        rect_lock = patches.Rectangle(
            (x - 0.5, y - 0.5), 1, 1,
            fill=False,
            edgecolor=ec,
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
    for x, y in [(5, 4), (6, 4)]:
        draw_cell(ax, x, y, cell_type='obstacle')
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
    """图1：分段路径锁定策略示意图 - 每行5张图，输出每一步移动"""
    width, height = 8, 5
    main_channel_row = 3  # 主通道索引为3（第4行）
    
    # 每一步：(车辆x, 车辆y, 是否负载, 主通道锁定列表, 是否子通道全程锁定)
    # 小车从(6,3)开始在主通道 -> (1,3) -> 子通道(1,0)取货 -> 返回(1,3)
    steps = [
        ((6, 3), False, [(6, 3), (5, 3), (4, 3)], False),   # 0 起点，主通道滚动锁定
        ((5, 3), False, [(5, 3), (4, 3), (3, 3)], False),   # 1
        ((4, 3), False, [(4, 3), (3, 3), (2, 3)], False),   # 2
        ((3, 3), False, [(3, 3), (2, 3), (1, 3)], False),   # 3
        ((2, 3), False, [(2, 3), (1, 3)], False),           # 4
        ((1, 3), False, [], True),   # 5 进入子通道入口，子通道全程锁定
        ((1, 2), False, [], True),   # 6
        ((1, 1), False, [], True),   # 7
        ((1, 0), True, [], True),    # 8 到达取货，负载（取货后货物不显示）
        ((1, 1), True, [], True),    # 9 返回主通道
        ((1, 2), True, [], True),    # 10
        ((1, 3), True, [(1, 3)], False),    # 11
    ]
    n_steps = len(steps)
    n_cols = 4  # 每行四张图
    n_rows = (n_steps + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 5 * n_rows))
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    for idx in range(n_cols * n_rows):
        row, col = idx // n_cols, idx % n_cols
        ax = axes[row, col]
        if idx >= n_steps:
            ax.axis('off')
            continue
        (vx, vy), is_loaded, locked_main, lock_sub = steps[idx]
        create_grid_base(ax, width, height)
        for y in range(height):
            for x in range(width):
                if y == main_channel_row:
                    draw_cell(ax, x, y, cell_type='main')
                else:
                    draw_cell(ax, x, y, cell_type='normal')
        # 只画尚未走过的路径（走过后什么都不画）
        full_path = [(6, 3), (5, 3), (4, 3), (3, 3), (2, 3), (1, 3), (1, 2), (1, 1), (1, 0), (1, 1), (1, 2), (1, 3)]
        remaining = full_path[idx:]
        if len(remaining) >= 2:
            # 返回段 (1,0)->(1,3) 用虚线
            if (1, 0) in remaining:
                j = remaining.index((1, 0))
                draw_path(ax, remaining[: j + 1], color=COLOR_VEHICLE_1, linewidth=2, alpha=0.35)
                if j + 1 < len(remaining):
                    draw_path(ax, remaining[j:], color=COLOR_VEHICLE_1, linewidth=2, linestyle='--', alpha=0.35)
            else:
                draw_path(ax, remaining, color=COLOR_VEHICLE_1, linewidth=2, linestyle='--', alpha=0.35)
        # 锁定
        for (lx, ly) in locked_main:
            draw_cell(ax, lx, ly, cell_type='main', locked=True)
        if lock_sub:
            for y in range(height - 1):
                if y == main_channel_row:
                    draw_cell(ax, 1, y, cell_type='main', locked=True)
                else:
                    draw_cell(ax, 1, y, cell_type='normal', locked=True)
        # 货物：取货后（已负载）不显示
        if not is_loaded:
            cargo_circle = patches.Circle((1, 0), 0.25, facecolor=COLOR_CARGO, edgecolor='darkgreen',
                                          linewidth=1.5, alpha=0.7, zorder=6)
            ax.add_patch(cargo_circle)
        # 车辆
        draw_vehicle(ax, vx, vy, 'V1', is_loaded=is_loaded)
        # 图例放右上角（仅第一格）
        if idx == 3:
            legend_elements = [
                patches.Patch(facecolor=COLOR_MAIN_CHANNEL, alpha=0.8, label='主通道'),
                patches.Patch(facecolor=COLOR_NORMAL_CHANNEL, alpha=0.6, label='子通道'),
                patches.Patch(facecolor='none', edgecolor=COLOR_LOCKED, linewidth=3, label='锁定格子'),
                patches.Circle((0, 0), 0.1, facecolor=COLOR_CARGO, edgecolor='darkgreen', label='货物'),
            ]
            ax.legend(handles=legend_elements, loc='upper right', fontsize=12, framealpha=0.9)
    plt.tight_layout()
    filename = 'figure1_segmented_locking.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"已生成：{filename}")
    plt.close()

def figure2_smart_avoidance():
    """图2：长9宽6，主通道第1、4行。负载V1从(7,4)到(0,4)；空车V2从(1,4)到(6,3)。仅(5,3)有货物。两车动一步后在(4,4)冲突，V2避让到(2,1)。"""
    width, height = 9, 6
    main_channel_rows = [1, 4]

    # V1 目的地 (0,4)，每次锁定三格
    # V1：第三张再往前一格到(5,4)，之后一直等待；再往后继续到(0,4)
    full_path = [(7, 4), (6, 4), (5, 4), (5, 4), (5, 4), (4, 4), (3, 4), (2, 4), (1, 4), (0, 4)]
    # V2：前两张(1,4)->(2,4)；第三到第五张第二条路径(2,4)->(2,1)避让全程锁定；之后第三条路径
    v2_positions = [(1, 4), (2, 4), (2, 4), (2, 3), (2, 2), (2, 1), (3, 1), (4, 1), (5, 1), (5, 2)]
    v2_path_to_53 = [(1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (5, 3)]  # V2 第一条路径：(1,4)到(5,3)，仅前两张图
    v2_path_2_avoid = [(2, 4), (2, 3), (2, 2), (2, 1)]  # V2 第二条路径：(2,4)到(2,1)，第三到第五张，全程锁定
    v2_path_3 = [(2, 1), (3, 1), (4, 1), (5, 1), (5, 2), (5, 3)]  # V2 第三条路径，idx>=5 时用
    v2_full_path = [(1, 4), (2, 4), (2, 3), (2, 2), (2, 1)]
    v2_avoid_path = [(2, 4), (2, 3), (2, 2), (2, 1)]
    conflict_cell = (4, 4)
    n_steps = len(full_path)
    n_cols = 4
    n_rows = (n_steps + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 5 * n_rows))
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    for idx in range(n_cols * n_rows):
        row, col = idx // n_cols, idx % n_cols
        ax = axes[row, col]
        if idx >= n_steps:
            ax.axis('off')
            continue
        (vx, vy) = full_path[idx]
        (v2x, v2y) = v2_positions[idx]
        create_grid_base(ax, width, height)
        for y in range(height):
            for x in range(width):
                if y in main_channel_rows:
                    draw_cell(ax, x, y, cell_type='main')
                else:
                    draw_cell(ax, x, y, cell_type='normal')
        # 仅 (5,3) 有货物
        cargo_circle = patches.Circle((5, 3), 0.25, facecolor=COLOR_CARGO, edgecolor='darkgreen',
                                      linewidth=1.5, alpha=0.7, zorder=6)
        ax.add_patch(cargo_circle)
        # 冲突格 (4,4)：仅第二张图标出，框黄色、字样加大
        if idx == 1:
            conflict_rect = patches.Rectangle((4 - 0.5, 4 - 0.5), 1, 1,
                                              facecolor=COLOR_CONFLICT, alpha=0.4, edgecolor='gold',
                                              linewidth=3, zorder=1)
            ax.add_patch(conflict_rect)
            ax.text(4, 4, '冲突', ha='center', va='center', fontsize=16, weight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor=COLOR_CONFLICT, alpha=0.8))
        # V2 路径：前两张第一条(1,4)->(5,3)；第三到第五张第二条(2,4)->(2,1)避让；之后第三条
        if idx <= 1:
            remaining_v2 = v2_path_to_53[v2_path_to_53.index((v2x, v2y)):]
            if len(remaining_v2) >= 2:
                draw_path(ax, remaining_v2, color=COLOR_VEHICLE_2, linewidth=2, alpha=0.35)
        elif idx <= 4:
            # 第三到第五张：第二条路径 (2,4)到(2,1)
            try:
                i = v2_path_2_avoid.index((v2x, v2y))
                remaining_avoid = v2_path_2_avoid[i:]
                if len(remaining_avoid) >= 2:
                    draw_path(ax, remaining_avoid, color=COLOR_AVOID_PATH, linewidth=2, linestyle='--', alpha=0.35)
            except ValueError:
                pass
        elif idx >= 5:
            # 第六到第十张：V2 第三条路径 (2,1)到(5,3)
            remaining_v2_3 = v2_path_3[v2_path_3.index((v2x, v2y)):]
            if len(remaining_v2_3) >= 2:
                draw_path(ax, remaining_v2_3, color=COLOR_VEHICLE_2, linewidth=2, alpha=0.35)
        # V1 锁定：第三、四、五张与第五张一致，均为 (3,4)(4,4)(5,4)；其余为当前及后续两格
        if idx in (2, 3, 4):
            locked = [(3, 4), (4, 4), (5, 4)]
        else:
            locked = full_path[idx : idx + 3]
        for (lx, ly) in locked:
            if ly in main_channel_rows:
                draw_cell(ax, lx, ly, cell_type='main', locked=True)
            else:
                draw_cell(ax, lx, ly, cell_type='normal', locked=True)
        # V2 锁定：前两张三格；第三到第五张第二条路径全程锁定；图8为(4,1)(5,1)；图10与图9一致；其余三格
        try:
            if idx <= 1:
                j = v2_path_to_53.index((v2x, v2y))
                v2_locked = v2_path_to_53[j : j + 3]
            elif idx <= 4:
                v2_locked = v2_path_2_avoid
            elif idx == 7:
                # 图8：V2 锁定 (4,1)(5,1)
                v2_locked = [(4, 1), (5, 1)]
            elif idx == 9:
                # 图10：与图9一致，(5,1)(5,2)(5,3)
                v2_locked = [(5, 1), (5, 2), (5, 3)]
            else:
                j = v2_path_3.index((v2x, v2y))
                v2_locked = v2_path_3[j : j + 3]
            for (lx, ly) in v2_locked:
                if ly in main_channel_rows:
                    draw_cell(ax, lx, ly, cell_type='main', locked=True, lock_color=COLOR_VEHICLE_2)
                else:
                    draw_cell(ax, lx, ly, cell_type='normal', locked=True, lock_color=COLOR_VEHICLE_2)
        except ValueError:
            pass
        # V1 尚未走过的路径
        remaining = full_path[idx:]
        if len(remaining) >= 2:
            draw_path(ax, remaining, color=COLOR_VEHICLE_1, linewidth=2, alpha=0.35)
        draw_vehicle(ax, vx, vy, 'V1', is_loaded=True)
        draw_vehicle(ax, v2x, v2y, 'V2', is_loaded=False)
        if idx == 3:
            legend_elements = [
                patches.Patch(facecolor=COLOR_MAIN_CHANNEL, alpha=0.8, label='主通道'),
                patches.Patch(facecolor=COLOR_NORMAL_CHANNEL, alpha=0.6, label='子通道'),
                patches.Circle((0, 0), 0.1, facecolor=COLOR_CARGO, edgecolor='darkgreen', label='货物'),
                patches.Patch(facecolor='none', edgecolor=COLOR_LOCKED, linewidth=3, label='锁定格子'),
                patches.Patch(facecolor=COLOR_CONFLICT, alpha=0.4, label='冲突'),
                plt.Line2D([0], [0], color=COLOR_AVOID_PATH, linewidth=2, linestyle='--', label='避让路径'),
            ]
            ax.legend(handles=legend_elements, loc='upper right', fontsize=10, framealpha=0.9)
    plt.tight_layout()
    filename = 'figure2_smart_avoidance.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"已生成：{filename}")
    plt.close()

def figure3_direction_lock():
    """图3：连续多子图，地图 8×8，第2、7行为主通道。V1 终点(7,6)。V2 (3,6)→(5,6)→(5,7)放货→(0,6)，第11张起不出现。V3 空车从(6,1)，(6,0)有货，先去(6,0)再回(6,1)再往(0,1)。"""
    width, height = 8, 8
    main_channel_rows = [6, 1]  # 第2行(y=6)、第7行(y=1)
    updown_cells = [(4, 5), (4, 4), (4, 3), (4, 2)]  # 第5列 上下巷道（两主通道之间）

    # V1 完整路径：(1,1)→(4,1)→(4,6)→(7,6)，共 12 步
    full_path = [(1, 1), (2, 1), (3, 1), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (5, 6), (6, 6), (7, 6)]
    # V2 路径：(3,6)→(5,6)→(5,7)放货→(0,6)；第10张到(0,6)后，第11张起不出现
    v2_path = [(3, 6), (4, 6), (5, 6), (5, 7), (5, 6), (4, 6), (3, 6), (2, 6), (1, 6), (0, 6)]
    v2_positions = [(3, 6), (4, 6), (5, 6), (5, 7), (5, 6), (4, 6), (3, 6), (2, 6), (1, 6), (0, 6), None, None]  # idx>=10 不画 V2
    v2_loaded = [True, True, True, True, False, False, False, False, False, False, False, False]
    # V3 空车从(6,1)；第一张(6,0)有货，第二张V3到(6,0)取货即负载，第三四张回(6,1)停住，第五张起往(0,1)
    v3_path = [(6, 1), (6, 0), (6, 1), (6, 1), (5, 1), (4, 1), (3, 1), (2, 1), (1, 1), (0, 1)]
    v3_positions = [(6, 1), (6, 0), (6, 1), (6, 1), (5, 1), (4, 1), (3, 1), (2, 1), (1, 1), (0, 1), (0, 1), (0, 1)]  # 第二张到(6,0)，第三四张停(6,1)，第五张起动
    v3_loaded = [False, True, True, True, True, True, True, True, True, True, True, True]  # 第二张到(6,0)即负载
    n_steps = 8
    n_cols = 4
    n_rows = (n_steps + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 5 * n_rows))
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    for idx in range(n_cols * n_rows):
        row, col = idx // n_cols, idx % n_cols
        ax = axes[row, col]
        if idx >= n_steps:
            ax.axis('off')
            continue
        (vx, vy) = full_path[idx]
        v2_pos = v2_positions[idx]
        (v2x, v2y) = v2_pos if v2_pos is not None else (None, None)
        v2_is_loaded = v2_loaded[idx]
        (v3x, v3y) = v3_positions[idx]
        v3_is_loaded = v3_loaded[idx]
        create_grid_base(ax, width, height)
        for y in range(height):
            for x in range(width):
                if (x, y) in updown_cells:
                    draw_cell(ax, x, y, cell_type='updown')
                elif y in main_channel_rows:
                    draw_cell(ax, x, y, cell_type='main')
                else:
                    draw_cell(ax, x, y, cell_type='normal')
        # 第一、二张 (6,0) 有货物；从第五张开始 (5,7) 一直有货物
        if idx <= 1:
            cargo_circle = patches.Circle((6, 0), 0.25, facecolor=COLOR_CARGO, edgecolor='darkgreen',
                                          linewidth=1.5, alpha=0.7, zorder=6)
            ax.add_patch(cargo_circle)
        if idx >= 4:
            cargo_circle = patches.Circle((5, 7), 0.25, facecolor=COLOR_CARGO, edgecolor='darkgreen',
                                          linewidth=1.5, alpha=0.7, zorder=6)
            ax.add_patch(cargo_circle)
        # V1：只画尚未走过的路径
        remaining = full_path[idx:]
        if len(remaining) >= 2:
            draw_path(ax, remaining, color=COLOR_VEHICLE_1, linewidth=2, alpha=0.35)
        # V2：只画尚未走过的路径
        if v2_pos is not None and idx <= 9:
            remaining_v2 = v2_path[idx:]
            if len(remaining_v2) >= 2:
                draw_path(ax, remaining_v2, color=COLOR_VEHICLE_2, linewidth=2, alpha=0.35)
        # V3：前两张只展示 (6,1)→(6,0) 和 (6,0)→(6,1)；第三四张无路径；第五张起展示到(0,1)的路径
        if idx <= 1:
            seg = [(6, 1), (6, 0)] if idx == 0 else [(6, 0), (6, 1)]
            draw_path(ax, seg, color=COLOR_VEHICLE_3, linewidth=2, alpha=0.35)
        elif idx >= 4:
            remaining_v3 = v3_path[idx:]
            if len(remaining_v3) >= 2:
                draw_path(ax, remaining_v3, color=COLOR_VEHICLE_3, linewidth=2, alpha=0.35)
        # 每次锁定三格：从自己开始往后算三格（参考V2）
        locked = full_path[idx : idx + 3]
        for (lx, ly) in locked:
            if (lx, ly) in updown_cells:
                draw_cell(ax, lx, ly, cell_type='updown', locked=True)
            elif ly in main_channel_rows:
                draw_cell(ax, lx, ly, cell_type='main', locked=True)
            else:
                draw_cell(ax, lx, ly, cell_type='normal', locked=True)
        # V2 前两张图锁定到 (5,6)；第3、4张锁定 (5,7)(5,6)；从第5张开始锁定三格
        if v2_pos is not None and idx <= 1:
            v2_locked = [(3, 6), (4, 6), (5, 6)] if idx == 0 else [(4, 6), (5, 6)]
            for (lx, ly) in v2_locked:
                if (lx, ly) in updown_cells:
                    draw_cell(ax, lx, ly, cell_type='updown', locked=True, lock_color=COLOR_VEHICLE_2)
                elif ly in main_channel_rows:
                    draw_cell(ax, lx, ly, cell_type='main', locked=True, lock_color=COLOR_VEHICLE_2)
                else:
                    draw_cell(ax, lx, ly, cell_type='normal', locked=True, lock_color=COLOR_VEHICLE_2)
        elif v2_pos is not None and 2 <= idx <= 3:
            v2_locked = [(5, 7), (5, 6)]
            for (lx, ly) in v2_locked:
                if (lx, ly) in updown_cells:
                    draw_cell(ax, lx, ly, cell_type='updown', locked=True, lock_color=COLOR_VEHICLE_2)
                elif ly in main_channel_rows:
                    draw_cell(ax, lx, ly, cell_type='main', locked=True, lock_color=COLOR_VEHICLE_2)
                else:
                    draw_cell(ax, lx, ly, cell_type='normal', locked=True, lock_color=COLOR_VEHICLE_2)
        elif v2_pos is not None and idx >= 4:
            # 从自己开始往后算三格
            v2_locked = v2_path[idx : idx + 3]
            for (lx, ly) in v2_locked:
                if (lx, ly) in updown_cells:
                    draw_cell(ax, lx, ly, cell_type='updown', locked=True, lock_color=COLOR_VEHICLE_2)
                elif ly in main_channel_rows:
                    draw_cell(ax, lx, ly, cell_type='main', locked=True, lock_color=COLOR_VEHICLE_2)
                else:
                    draw_cell(ax, lx, ly, cell_type='normal', locked=True, lock_color=COLOR_VEHICLE_2)
        # V3 第一、二张锁定 (6,1)(6,0)；第三四张只锁定 (6,1)，无路径；第五张起锁定三格并展示到(0,1)路径
        if idx <= 1:
            v3_locked = [(6, 1), (6, 0)]
            for (lx, ly) in v3_locked:
                if (lx, ly) in updown_cells:
                    draw_cell(ax, lx, ly, cell_type='updown', locked=True, lock_color=COLOR_VEHICLE_3)
                elif ly in main_channel_rows:
                    draw_cell(ax, lx, ly, cell_type='main', locked=True, lock_color=COLOR_VEHICLE_3)
                else:
                    draw_cell(ax, lx, ly, cell_type='normal', locked=True, lock_color=COLOR_VEHICLE_3)
        elif 2 <= idx <= 3:
            draw_cell(ax, 6, 1, cell_type='main', locked=True, lock_color=COLOR_VEHICLE_3)
        elif idx >= 4:
            # 从自己开始往后算三格（参考V2）
            v3_locked = v3_path[idx : idx + 3]
            for (lx, ly) in v3_locked:
                if (lx, ly) in updown_cells:
                    draw_cell(ax, lx, ly, cell_type='updown', locked=True, lock_color=COLOR_VEHICLE_3)
                elif ly in main_channel_rows:
                    draw_cell(ax, lx, ly, cell_type='main', locked=True, lock_color=COLOR_VEHICLE_3)
                else:
                    draw_cell(ax, lx, ly, cell_type='normal', locked=True, lock_color=COLOR_VEHICLE_3)
        draw_vehicle(ax, vx, vy, 'V1', is_loaded=True)
        if v2_pos is not None and idx <= 9:
            draw_vehicle(ax, v2x, v2y, 'V2', is_loaded=v2_is_loaded)
        draw_vehicle(ax, v3x, v3y, 'V3', is_loaded=v3_is_loaded)
        if idx == 3:
            legend_elements = [
                patches.Patch(facecolor=COLOR_MAIN_CHANNEL, alpha=0.8, label='主通道'),
                patches.Patch(facecolor=COLOR_NORMAL_CHANNEL, alpha=0.6, label='子通道'),
                patches.Patch(facecolor=COLOR_UPDOWN_CHANNEL, alpha=0.8, label='上下巷道'),
                patches.Patch(facecolor='none', edgecolor=COLOR_LOCKED, linewidth=3, label='锁定格子'),
                plt.Line2D([0], [0], color=COLOR_VEHICLE_1, linewidth=2, label='V1路径'),
                plt.Line2D([0], [0], color=COLOR_VEHICLE_2, linewidth=2, label='V2路径'),
                plt.Line2D([0], [0], color=COLOR_VEHICLE_3, linewidth=2, label='V3路径'),
                patches.Circle((0, 0), 0.1, facecolor=COLOR_CARGO, edgecolor='darkgreen', label='货物'),
            ]
            ax.legend(handles=legend_elements, loc='upper right', fontsize=10, framealpha=0.9)
    plt.tight_layout()
    filename = 'figure3_direction_lock.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"已生成：{filename}")
    plt.close()

if __name__ == '__main__':
    # 先生成地图类型说明示意图，便于文章中统一解释
    figure0_map_demo()
    figure1_segmented_locking()
    figure2_smart_avoidance()
    figure3_direction_lock()