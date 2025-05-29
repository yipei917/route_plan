import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.patches as patches
from typing import List
from src.models.grid import Grid, GRID_TYPE_NORMAL_CHANNEL, GRID_TYPE_MAIN_CHANNEL, GRID_TYPE_OBSTACLE
from src.models.vehicle import Vehicle

class GridVisualizer:
    """网格可视化器"""
    def __init__(self, grid: Grid):
        self.grid = grid
        self.fig, self.ax = plt.subplots(figsize=(300, 200))
        self.vehicles: List[Vehicle] = []
        
        # 设置颜色映射
        self.grid_type_colors = {
            GRID_TYPE_NORMAL_CHANNEL: 'white',
            GRID_TYPE_MAIN_CHANNEL: 'lightgray',
            GRID_TYPE_OBSTACLE: 'black',
        }
        
        # 设置车辆颜色
        self.vehicle_colors = {
            "empty": 'blue',
            "loaded": 'green'
        }
        
        # 设置路径状态颜色
        self.path_status_colors = {
            "idle": 'gray',
            "moving": 'blue',
            "waiting": 'red',
            "completed": 'green'
        }
        
        # 设置方向箭头
        self.direction_arrows = {
            "up": "↑",
            "down": "↓",
            "left": "←",
            "right": "→"
        }
    
    def add_vehicle(self, vehicle: Vehicle) -> None:
        """添加车辆到可视化器"""
        self.vehicles.append(vehicle)
    
    def draw_grid(self, constraint_manager=None) -> None:
        """绘制网格，车辆占用块染色并显示图例"""
        self.ax.clear()
        self.ax.set_xlim(-0.5, self.grid.width - 0.5)
        self.ax.set_ylim(-0.5, self.grid.height - 0.5)
        self.ax.set_xticks(range(self.grid.width))
        self.ax.set_yticks(range(self.grid.height))
        self.ax.grid(True)

        # 车辆占用块染色准备
        cmap = plt.get_cmap('tab20')
        vehicle_ids = [v.id for v in self.vehicles]
        color_map = {vid: cmap(i % 20) for i, vid in enumerate(vehicle_ids)}
        legend_elements = []

        # 获取占用信息
        occupied_positions = {}
        if constraint_manager is not None:
            occupied_positions = getattr(constraint_manager.vehicle_conflict_constraint, "occupied_positions", {})

        # 绘制每个格子
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                cell = self.grid.get_cell(x, y)
                pos = (x, y)
                # 默认背景色
                facecolor = self.grid_type_colors.get(cell.grid_type, 'white') if cell else 'white'
                edgecolor = 'black'
                # 如果被车辆占用，染色
                if pos in occupied_positions:
                    vid = occupied_positions[pos]
                    facecolor = color_map.get(vid, 'yellow')
                # 绘制格子
                rx = x
                ry = self.grid.height - 1 - y
                rect = patches.Rectangle(
                    (rx - 0.5, ry - 0.5), 1, 1,
                    facecolor=facecolor,
                    edgecolor=edgecolor
                )
                self.ax.add_patch(rect)

                # 绘制方向箭头
                if cell and cell.allowed_directions:
                    directions_text = "".join(self.direction_arrows[d] for d in cell.allowed_directions)
                    self.ax.text(rx, ry, directions_text, ha='center', va='center', fontsize=8)

                # 货物
                if cell and cell.has_cargo:
                    cargo_rect = patches.Rectangle(
                        (rx - 0.18, ry - 0.18), 0.36, 0.36,
                        facecolor='red', edgecolor='darkred', alpha=0.85
                    )
                    self.ax.add_patch(cargo_rect)

        # 绘制入口和出口
        for x, y in self.grid.entrances:
            self.ax.text(x, self.grid.height - 1 - y, "IN", ha='center', va='center', color='blue', fontsize=10, weight='bold')
        for x, y in self.grid.exits:
            self.ax.text(x, self.grid.height - 1 - y, "OUT", ha='center', va='center', color='green', fontsize=10, weight='bold')

        # 图例：车辆ID-占用块颜色
        for vid in vehicle_ids:
            legend_elements.append(
                Line2D([0], [0], marker='s', color='w', markerfacecolor=color_map[vid], markersize=15, label=f'占用 {vid}')
            )
        if legend_elements:
            self.ax.legend(handles=legend_elements, loc='upper right', fontsize=8, title="车辆占用块")
    
    def draw_vehicles(self) -> None:
        """绘制车辆及其路径（每辆车路径不同颜色，并添加图例）"""
        # 为每辆车分配唯一颜色
        cmap = plt.get_cmap('tab20')
        vehicle_ids = [v.id for v in self.vehicles]
        color_map = {vid: cmap(i % 20) for i, vid in enumerate(vehicle_ids)}

        legend_elements = []

        for vehicle in self.vehicles:
            x, y = vehicle.current_position
            color = self.vehicle_colors.get(vehicle.vehicle_type, 'gray')

            # 绘制车辆
            rx = x
            ry = self.grid.height - 1 - y
            circle = patches.Circle(
                (rx, ry), 0.3,
                facecolor=color,
                edgecolor='black',
                alpha=0.7
            )
            self.ax.add_patch(circle)
            self.ax.text(rx, ry, vehicle.id, ha='center', va='center', color='white', fontsize=8, weight='bold')

            # 绘制路径（每辆车唯一颜色）
            if vehicle.path:
                path_x = [p[0] for p in vehicle.path]
                path_y = [self.grid.height - 1 - p[1] for p in vehicle.path]
                path_color = color_map[vehicle.id]
                linestyle = '--' if vehicle.status == "waiting" else '-'
                self.ax.plot(path_x, path_y, linestyle, color=path_color, alpha=0.7, linewidth=2)
                # 图例元素
                legend_elements.append(Line2D([0], [0], color=path_color, lw=2, label=f'Path {vehicle.id}'))

        # 添加图例
        if legend_elements:
            self.ax.legend(handles=legend_elements, loc='upper right', fontsize=8, title="车辆路径")
    
    def save(self, filename: str) -> None:
        """保存图像"""
        plt.savefig(filename, dpi=100, bbox_inches='tight')
        # plt.close()
    
    def show(self) -> None:
        """显示图像"""
        plt.show()
        plt.close()