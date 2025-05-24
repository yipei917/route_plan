import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Tuple, Dict, Optional
from src.models.grid import Grid, GRID_TYPE_NORMAL_CHANNEL, GRID_TYPE_MAIN_CHANNEL, GRID_TYPE_OBSTACLE, GRID_TYPE_FIRE_RESTRICTED, GRID_TYPE_COLUMN
from src.models.vehicle import Vehicle

class GridVisualizer:
    """网格可视化器"""
    def __init__(self, grid: Grid):
        self.grid = grid
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.vehicles: List[Vehicle] = []
        
        # 设置颜色映射
        self.grid_type_colors = {
            GRID_TYPE_NORMAL_CHANNEL: 'white',
            GRID_TYPE_MAIN_CHANNEL: 'lightgray',
            GRID_TYPE_OBSTACLE: 'black',
            GRID_TYPE_FIRE_RESTRICTED: 'red',
            GRID_TYPE_COLUMN: 'gray'
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
    
    def draw_grid(self) -> None:
        """绘制网格"""
        # 清除当前图形
        self.ax.clear()
        
        # 设置坐标轴
        self.ax.set_xlim(-0.5, self.grid.width - 0.5)
        self.ax.set_ylim(-0.5, self.grid.height - 0.5)
        self.ax.set_xticks(range(self.grid.width))
        self.ax.set_yticks(range(self.grid.height))
        self.ax.grid(True)
        
        # 绘制每个格子
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                cell = self.grid.get_cell(x, y)
                if cell:
                    # 绘制格子背景
                    rect = patches.Rectangle(
                        (x - 0.5, y - 0.5), 1, 1,
                        facecolor=self.grid_type_colors.get(cell.grid_type, 'white'),
                        edgecolor='black'
                    )
                    self.ax.add_patch(rect)
                    
                    # 绘制方向箭头
                    if cell.allowed_directions:
                        directions_text = "".join(self.direction_arrows[d] for d in cell.allowed_directions)
                        self.ax.text(x, y, directions_text, ha='center', va='center', fontsize=8)
                    
                    # 绘制货物标记
                    if cell.has_cargo:
                        self.ax.text(x, y + 0.3, "●", ha='center', va='center', color='red', fontsize=12)
        
        # 绘制入口和出口
        for x, y in self.grid.entrances:
            self.ax.text(x, y, "IN", ha='center', va='center', color='blue', fontsize=10, weight='bold')
        for x, y in self.grid.exits:
            self.ax.text(x, y, "OUT", ha='center', va='center', color='green', fontsize=10, weight='bold')
    
    def draw_vehicles(self) -> None:
        """绘制车辆"""
        for vehicle in self.vehicles:
            x, y = vehicle.current_position
            color = self.vehicle_colors.get(vehicle.vehicle_type, 'gray')
            
            # 绘制车辆
            circle = patches.Circle(
                (x, y), 0.3,
                facecolor=color,
                edgecolor='black',
                alpha=0.7
            )
            self.ax.add_patch(circle)
            
            # 绘制车辆ID
            self.ax.text(x, y, vehicle.id, ha='center', va='center', color='white', fontsize=8, weight='bold')
            
            # 绘制路径
            if vehicle.path:
                path_x = [p[0] for p in vehicle.path]
                path_y = [p[1] for p in vehicle.path]
                # 根据车辆状态选择路径颜色
                path_color = self.path_status_colors.get(vehicle.status, 'gray')
                # 如果车辆在等待状态，使用虚线样式
                linestyle = '--' if vehicle.status == "waiting" else '-'
                self.ax.plot(path_x, path_y, linestyle, color=path_color, alpha=0.7, linewidth=2)
                
                # 在路径上添加箭头指示方向
                if len(path_x) > 1:
                    for i in range(len(path_x) - 1):
                        mid_x = (path_x[i] + path_x[i + 1]) / 2
                        mid_y = (path_y[i] + path_y[i + 1]) / 2
                        dx = path_x[i + 1] - path_x[i]
                        dy = path_y[i + 1] - path_y[i]
                        self.ax.arrow(mid_x, mid_y, dx * 0.3, dy * 0.3,
                                    head_width=0.1, head_length=0.1,
                                    fc=path_color, ec=path_color, alpha=0.7)
    
    def save(self, filename: str) -> None:
        """保存图像"""
        plt.savefig(filename, dpi=100, bbox_inches='tight')
        # plt.close()
    
    def show(self) -> None:
        """显示图像"""
        plt.show()
        plt.close() 