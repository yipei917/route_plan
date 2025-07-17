from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import pandas as pd

# 使用字典替代枚举
DIRECTION_MAP = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}

# 使用字符串常量替代枚举
GRID_TYPE_NORMAL_CHANNEL = "normal_channel"
GRID_TYPE_MAIN_CHANNEL = "main_channel"
GRID_TYPE_UP_DOWN_CHANNEL = "up_down_channel"
GRID_TYPE_OBSTACLE = "obstacle"
GRID_TYPE_INTERFACE = "interface"

MAIN_CHANNEL_STATUS_NULL = "null"
MAIN_CHANNEL_STATUS_LEFT = "left"
MAIN_CHANNEL_STATUS_RIGHT = "right"

@dataclass
class GridCell:
    x: int
    y: int
    grid_type: str = GRID_TYPE_NORMAL_CHANNEL
    allowed_directions: List[str] = None
    has_cargo: bool = False
    main_channel_status: str = MAIN_CHANNEL_STATUS_NULL

    def __post_init__(self):
        if self.allowed_directions is None:
            self.allowed_directions = []

    def can_pass(self, is_empty: bool) -> bool:
        """检查是否可以通行"""
        if self.grid_type == GRID_TYPE_OBSTACLE:
            return False

        if self.grid_type == GRID_TYPE_MAIN_CHANNEL or self.grid_type == GRID_TYPE_INTERFACE or self.grid_type == GRID_TYPE_UP_DOWN_CHANNEL:
            return True

        if self.grid_type == GRID_TYPE_NORMAL_CHANNEL:
            if is_empty:
                return True
            return not self.has_cargo

        return False

    def get_allowed_directions(self) -> List[str]:
        """获取格子允许的方向"""
        if self.grid_type == GRID_TYPE_MAIN_CHANNEL:
            if self.main_channel_status == MAIN_CHANNEL_STATUS_NULL:
                return ["up", "down", "left", "right"]
            elif self.main_channel_status == MAIN_CHANNEL_STATUS_LEFT:
                return ["up", "down", "left"]
            elif self.main_channel_status == MAIN_CHANNEL_STATUS_RIGHT:
                return ["up", "down", "right"]
        return self.allowed_directions

class Grid:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells: Dict[Tuple[int, int], GridCell] = {}
        self.main_channel_rows: List[int] = []

        # 初始化网格
        for y in range(height):
            for x in range(width):
                self.cells[(x, y)] = GridCell(x, y)

    def set_cell_type(self, x: int, y: int, grid_type: str) -> None:
        """设置格子类型"""
        if (x, y) in self.cells:
            self.cells[(x, y)].grid_type = grid_type

    def get_cell_type(self, target_position: Tuple[int, int]) -> str:
        """获取格子类型"""
        if target_position in self.cells:
            return self.cells[target_position].grid_type
        return ""

    def set_cell_directions(self, x: int, y: int, directions: List[str]) -> None:
        """设置格子允许的方向"""
        if (x, y) in self.cells:
            self.cells[(x, y)].allowed_directions = directions

    def get_cell(self, x: int, y: int) -> Optional[GridCell]:
        """获取格子"""
        return self.cells.get((x, y))

    def get_neighbors(self, x: int, y: int, is_empty: bool) -> List[Tuple[int, int]]:
        """获取相邻格子"""
        neighbors = []
        current_cell = self.get_cell(x, y)
        if not current_cell:
            return neighbors

        for direction in current_cell.get_allowed_directions():
            dx, dy = DIRECTION_MAP[direction]
            new_x = x + dx
            new_y = y + dy

            # 检查边界
            if not (0 <= new_x < self.width and 0 <= new_y < self.height):
                continue

            # 检查是否可以通行
            neighbor_cell = self.get_cell(new_x, new_y)
            if neighbor_cell and neighbor_cell.can_pass(is_empty):
                neighbors.append((new_x, new_y))

        return neighbors

    def is_valid_position(self, x: int, y: int) -> bool:
        """检查位置是否有效"""
        return 0 <= x < self.width and 0 <= y < self.height

    def has_cargo(self, x: int, y: int) -> bool:
        """检查格子是否有货物"""
        cell = self.get_cell(x, y)
        return cell.has_cargo if cell else False

    def set_cargo(self, x: int, y: int, has_cargo: bool) -> None:
        """设置格子是否有货物"""
        if (x, y) in self.cells:
            self.cells[(x, y)].has_cargo = has_cargo

    def load_map_from_xlsx(self, path: str) -> None:
        df = pd.read_excel(path, header=None)
        df = df.iloc[1:, 1:]  # 跳过第一行和第一列

        rows, cols = df.shape
        self.width = cols
        self.height = rows
        self.cells.clear()

        direction_map = {"上": "up", "下": "down", "左": "left", "右": "right"}

        for y in range(rows):
            for x in range(cols):
                cell_text = str(df.iat[y, x]) if pd.notna(df.iat[y, x]) else ""
                grid_type = GRID_TYPE_OBSTACLE
                allowed_directions = []

                if cell_text == "":
                    cell = GridCell(
                        x=x,
                        y=y,
                        grid_type=grid_type,
                        allowed_directions=allowed_directions,
                    )
                    self.cells[(x, y)] = cell
                    continue  # 跳过空格子

                # 判断类型
                if "禁用" in cell_text:
                    grid_type = GRID_TYPE_OBSTACLE
                elif "接驳口" in cell_text:
                    grid_type = GRID_TYPE_INTERFACE
                elif "通道" in cell_text:
                    grid_type = GRID_TYPE_MAIN_CHANNEL
                elif "巷道" in cell_text:
                    grid_type = GRID_TYPE_UP_DOWN_CHANNEL
                elif "货" in cell_text:
                    grid_type = GRID_TYPE_NORMAL_CHANNEL

                # 解析方向
                for zh_dir, en_dir in direction_map.items():
                    if zh_dir in cell_text:
                        allowed_directions.append(en_dir)

                cell = GridCell(x=x, y=y, grid_type=grid_type, allowed_directions=allowed_directions)
                self.cells[(x, y)] = cell

                # 统计主干道（main channel）所在的行，避免重复添加
                if grid_type == GRID_TYPE_MAIN_CHANNEL and y not in self.main_channel_rows:
                    self.main_channel_rows.append(y)
