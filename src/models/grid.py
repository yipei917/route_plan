from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import json
from matplotlib.pyplot import grid
import pandas as pd

# 使用字典替代枚举
DIRECTION_MAP = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}

# 使用字符串常量替代枚举
GRID_TYPE_NORMAL_CHANNEL = "normal_channel"
GRID_TYPE_MAIN_CHANNEL = "main_channel"
GRID_TYPE_OBSTACLE = "obstacle"


@dataclass
class GridCell:
    x: int
    y: int
    grid_type: str = GRID_TYPE_NORMAL_CHANNEL
    allowed_directions: List[str] = None
    has_cargo: bool = False

    def __post_init__(self):
        if self.allowed_directions is None:
            self.allowed_directions = []

    def can_pass(self, is_empty: bool) -> bool:
        """检查是否可以通行"""
        if self.grid_type == GRID_TYPE_OBSTACLE:
            return False

        if self.grid_type == GRID_TYPE_MAIN_CHANNEL:
            return True

        if self.grid_type == GRID_TYPE_NORMAL_CHANNEL:
            if is_empty:
                return True
            return not self.has_cargo

        return False


class Grid:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells: Dict[Tuple[int, int], GridCell] = {}
        self.entrances: List[Tuple[int, int]] = []
        self.exits: List[Tuple[int, int]] = []
        self.main_channel_rows: List[int] = []
        self.main_channel_columns: List[int] = []

        # 初始化网格
        for y in range(height):
            for x in range(width):
                self.cells[(x, y)] = GridCell(x, y)

    def set_cell_type(self, x: int, y: int, grid_type: str) -> None:
        """设置格子类型"""
        if (x, y) in self.cells:
            self.cells[(x, y)].grid_type = grid_type

    def set_cell_directions(self, x: int, y: int, directions: List[str]) -> None:
        """设置格子允许的方向"""
        if (x, y) in self.cells:
            self.cells[(x, y)].allowed_directions = directions

    def add_entrance(self, x: int, y: int) -> None:
        """添加入口"""
        if (x, y) not in self.entrances:
            self.entrances.append((x, y))

    def add_exit(self, x: int, y: int) -> None:
        """添加出口"""
        if (x, y) not in self.exits:
            self.exits.append((x, y))

    def get_cell(self, x: int, y: int) -> Optional[GridCell]:
        """获取格子"""
        return self.cells.get((x, y))

    def get_neighbors(self, x: int, y: int, is_empty: bool) -> List[Tuple[int, int]]:
        """获取相邻格子"""
        neighbors = []
        current_cell = self.get_cell(x, y)
        if not current_cell:
            return neighbors

        for direction in current_cell.allowed_directions:
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

    def get_all_entrances(self) -> List[Tuple[int, int]]:
        """获取所有入口"""
        return self.entrances.copy()

    def get_all_exits(self) -> List[Tuple[int, int]]:
        """获取所有出口"""
        return self.exits.copy()

    def has_cargo(self, x: int, y: int) -> bool:
        """检查格子是否有货物"""
        cell = self.get_cell(x, y)
        return cell.has_cargo if cell else False

    def set_cargo(self, x: int, y: int, has_cargo: bool) -> None:
        """设置格子是否有货物"""
        if (x, y) in self.cells:
            self.cells[(x, y)].has_cargo = has_cargo

    def save_to_json(self, filename: str) -> None:
        """将地图保存为 JSON 文件"""
        cargo_positions = [
            (x, y) for (x, y), cell in self.cells.items() if cell.has_cargo
        ]
        obstacle_positions = [
            (x, y)
            for (x, y), cell in self.cells.items()
            if cell.grid_type == GRID_TYPE_OBSTACLE
        ]

        map_data = {
            "width": self.width,
            "height": self.height,
            "main_channels": {
                "rows": self.main_channel_rows,
                "columns": self.main_channel_columns,
            },
            "obstacles": obstacle_positions,
            "entrances": self.entrances,
            "exits": self.exits,
            "cargo": cargo_positions,
        }

        with open(filename, "w") as f:
            json.dump(map_data, f, indent=2)

    def load_from_json(self, filename: str) -> None:
        """从 JSON 文件加载地图"""
        with open(filename, "r") as f:
            map_data = json.load(f)

        # 初始化网格
        self.width = map_data["width"]
        self.height = map_data["height"]
        self.cells.clear()
        for y in range(self.height):
            for x in range(self.width):
                self.cells[(x, y)] = GridCell(x, y)

        # 设置主通道
        self.main_channel_rows = map_data["main_channels"]["rows"]
        self.main_channel_columns = map_data["main_channels"]["columns"]
        for row in self.main_channel_rows:
            for x in range(self.width):
                self.set_cell_type(x, row, GRID_TYPE_MAIN_CHANNEL)
        for col in self.main_channel_columns:
            for y in range(self.height):
                self.set_cell_type(col, y, GRID_TYPE_MAIN_CHANNEL)

        # 设置障碍物
        for x, y in map_data["obstacles"]:
            self.set_cell_type(x, y, GRID_TYPE_OBSTACLE)

        # 设置入口和出口
        self.entrances = [tuple(pos) for pos in map_data["entrances"]]
        self.exits = [tuple(pos) for pos in map_data["exits"]]

        # 设置货物
        for x, y in map_data["cargo"]:
            self.set_cargo(x, y, True)

    def load_map_from_excel(self, path: str) -> None:
        df = pd.read_excel(path, header=None)
        df = df.iloc[1:, 1:]  # 跳过第一行和第一列

        rows, cols = df.shape
        self.width = cols
        self.height = rows
        self.cells.clear()
        self.entrances.clear()
        self.exits.clear()
        self.main_channel_rows.clear()
        self.main_channel_columns.clear()

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
                    grid_type = GRID_TYPE_MAIN_CHANNEL
                    self.add_entrance(x, y)
                    self.add_exit(x, y)
                elif "道" in cell_text:
                    grid_type = GRID_TYPE_MAIN_CHANNEL
                elif "货" in cell_text:
                    grid_type = GRID_TYPE_NORMAL_CHANNEL

                # 解析方向
                for zh_dir, en_dir in direction_map.items():
                    if zh_dir in cell_text:
                        allowed_directions.append(en_dir)

                cell = GridCell(
                    x=x, y=y, grid_type=grid_type, allowed_directions=allowed_directions
                )
                self.cells[(x, y)] = cell
