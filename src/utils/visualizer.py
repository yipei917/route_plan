import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Tuple
from src.models.grid import Grid, GRID_TYPE_NORMAL_CHANNEL, GRID_TYPE_MAIN_CHANNEL, GRID_TYPE_OBSTACLE, GRID_TYPE_INTERFACE, GRID_TYPE_UP_DOWN_CHANNEL
from src.models.vehicle import VEHICLE_STATUS_AVOIDING, VEHICLE_STATUS_DELIVER, VEHICLE_STATUS_IDLE, VEHICLE_STATUS_PICKUP, VEHICLE_STATUS_WAITING, Vehicle
import os

class GridVisualizer:
    """网格可视化器"""
    def __init__(self, grid: Grid, figsize: Tuple[int, int] = (300, 200)):
        self.grid = grid
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.vehicles: List[Vehicle] = []
        
        # 设置颜色映射
        self.grid_type_colors = {
            GRID_TYPE_NORMAL_CHANNEL: 'white',
            GRID_TYPE_MAIN_CHANNEL: 'lightgray',
            GRID_TYPE_OBSTACLE: 'black',
            GRID_TYPE_INTERFACE: 'yellow',
            GRID_TYPE_UP_DOWN_CHANNEL: 'lightgray',
        }
        
        # 设置车辆颜色
        self.vehicle_colors = {
            VEHICLE_STATUS_PICKUP: 'blue',
            VEHICLE_STATUS_DELIVER: 'green',
            VEHICLE_STATUS_AVOIDING: 'orange',
            VEHICLE_STATUS_IDLE: 'gray',
            VEHICLE_STATUS_WAITING: 'red'
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
        """只绘制地图"""
        self.ax.clear()
        self.ax.set_xlim(-0.5, self.grid.width - 0.5)
        self.ax.set_ylim(-0.5, self.grid.height - 0.5)
        self.ax.set_xticks(range(self.grid.width))
        self.ax.set_yticks(range(self.grid.height))
        self.ax.grid(True)

        # 绘制每个格子
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                cell = self.grid.get_cell(x, y)
                # 默认背景色
                facecolor = self.grid_type_colors.get(cell.grid_type, 'white') if cell else 'white'
                edgecolor = 'black'
                rx = x
                ry = self.grid.height - 1 - y
                rect = patches.Rectangle(
                    (rx - 0.5, ry - 0.5), 1, 1,
                    facecolor=facecolor,
                    edgecolor=edgecolor
                )
                self.ax.add_patch(rect)

                # 绘制格子编号（数字大一点）
                self.ax.text(rx, ry, f"{x},{y}", ha='center', va='center', color='black', fontsize=28, alpha=0.5)

                # 绘制方向箭头（放在编号下方）
                if cell and cell.get_allowed_directions():
                    directions_text = "".join(self.direction_arrows[d] for d in cell.get_allowed_directions())
                    self.ax.text(rx, ry - 0.2, directions_text, ha='center', va='center', fontsize=16)

                # 货物
                if cell and cell.has_cargo:
                    # 绘制货物圆形
                    cargo_rect = patches.Circle((rx, ry), 0.4, facecolor='#FFB6B6', edgecolor='darkred', alpha=0.6)
                    self.ax.add_patch(cargo_rect)


    def draw_vehicles(self) -> None:
        """绘制车辆及其路径（所有车辆路径共用一个图例，并加粗）"""
        # 定义路径颜色列表
        path_colors = ['red', 'orange', 'purple', 'brown', 'pink', 'cyan']
        
        for i, v in enumerate(self.vehicles):
            x, y = v.current_position
            rx = x
            ry = self.grid.height - 1 - y
            color = self.vehicle_colors.get(v.status, 'blue')
            
            # 绘制车辆圆形
            vehicle_circle = patches.Circle((rx, ry), 0.35, facecolor=color, edgecolor='black', linewidth=4, alpha=0.9, zorder=10)
            self.ax.add_patch(vehicle_circle)
            
            # 标注车辆编号
            self.ax.text(rx, ry, v.id, ha='center', va='center', color='white', fontsize=18, fontweight='bold', zorder=11)
            
            # 绘制车辆路径
            if v.current_execution_path and len(v.current_execution_path) > 0:
                path_color = path_colors[i % len(path_colors)]
                
                # 为路径中的每个格子绘制填充矩形
                for px, py in v.current_execution_path:
                    ry = self.grid.height - 1 - py
                    path_rect = patches.Rectangle(
                        (px - 0.5, ry - 0.5), 1, 1,
                        facecolor=path_color,
                        alpha=0.3,
                        zorder=3
                    )
                    self.ax.add_patch(path_rect)


    def save(self, filename: str) -> None:
        """保存图像"""
        plt.savefig(filename, dpi=100, bbox_inches='tight')
    
    def visualize(self, path_name: str, filename: str) -> None:
        """可视化当前状态, 保存到output目录"""
        self.draw_grid()
        self.draw_vehicles()
        full_path = os.path.join(path_name, filename)
        self.save(full_path)
    
    def get_image_data(self) -> str:
        """获取图像数据（base64编码）"""
        import io
        import base64
        
        # 将图像保存到内存缓冲区，降低DPI以提高速度
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=50, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        
        # 转换为base64编码
        img_data = base64.b64encode(img_buffer.getvalue()).decode()
        img_buffer.close()
        
        return img_data