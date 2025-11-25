# 四向穿梭车路径规划工具库

## 简介

本工具库提供四向穿梭车在仓储网格环境中的路径规划功能，包括：

- **带方向约束的A*路径规划算法** - 考虑网格方向约束和货物占用状态
- **路径冲突检测与锁定管理** - 多车路径冲突检测和位置锁定
- **动态方向锁定机制** - 负载车辆动态锁定主通道方向，防止死锁
- **仓储网格地图模型** - 支持多种通道类型和方向约束

## 快速开始

```python
from src import Grid, Vehicle, AStarPlanner, VEHICLE_TYPE_EMPTY

# 1. 创建地图（推荐使用JSON格式）
grid = Grid(10, 10)
grid.load_map_from_json("resource/test_map.json")
# 或使用Excel格式（需要pandas依赖）
# grid.load_map_from_xlsx("resource/test_map.xlsx")

# 2. 创建车辆
vehicle = Vehicle(
    id="V1",
    vehicle_type=VEHICLE_TYPE_EMPTY,
    current_position=(8, 7)
)

# 3. 创建路径规划器
planner = AStarPlanner(grid)

# 4. 规划路径
path = planner.find_path(vehicle, (8, 7), (3, 6))

if path:
    print(f"找到路径: {path}")
    vehicle.set_full_planned_path(path)
else:
    print("无法找到路径")
```

## API 文档

### AStarPlanner

路径规划器类，使用A*算法在带方向约束的网格中规划路径。

#### 构造函数

```python
AStarPlanner(grid: Grid)
```

**参数**：
- `grid` (Grid): 网格地图对象

#### 方法

##### `find_path(vehicle, start, goal) -> Optional[List[Tuple[int, int]]]`

规划从起点到终点的路径。

**参数**：
- `vehicle` (Vehicle): 车辆对象，用于判断负载状态
- `start` (Tuple[int, int]): 起点坐标 (x, y)
- `goal` (Tuple[int, int]): 终点坐标 (x, y)

**返回**：
- `Optional[List[Tuple[int, int]]]`: 路径节点列表，如果无法找到路径则返回 None

**示例**：
```python
planner = AStarPlanner(grid)
path = planner.find_path(vehicle, (8, 7), (3, 6))
```

---

### Grid

仓储网格地图类。

#### 构造函数

```python
Grid(width: int, height: int)
```

**参数**：
- `width` (int): 网格宽度
- `height` (int): 网格高度

#### 方法

##### `load_map_from_xlsx(path: str) -> None`

从Excel文件加载地图配置。

**参数**：
- `path` (str): Excel文件路径

**Excel格式**：
- 第一行第一列为坐标标识
- 每个单元格包含格子类型和允许方向
- 格子类型：通道、巷道、接驳口、货位、禁用
- 方向标识：上、下、左、右

##### `load_map_from_json(path: str) -> None`

从JSON文件加载地图配置。推荐使用此方法，相比Excel格式更清晰、易维护。

**参数**：
- `path` (str): JSON文件路径

**JSON格式**：

支持两种JSON格式，可根据需求选择：

**格式A：cells数组格式**（适合稀疏地图，只定义非障碍格子）

```json
{
  "width": 10,
  "height": 10,
  "cells": [
    {
      "x": 0,
      "y": 0,
      "type": "main_channel",
      "directions": ["up", "down", "left", "right"]
    },
    {
      "x": 1,
      "y": 0,
      "type": "normal_channel",
      "directions": ["left", "right"]
    }
  ],
  "main_channel_rows": [0, 5]
}
```

**格式B：grid二维数组格式**（适合密集地图，完整定义所有格子）

```json
{
  "width": 10,
  "height": 10,
  "grid": [
    [
      {
        "type": "main_channel",
        "directions": ["up", "down", "left", "right"]
      },
      {
        "type": "normal_channel",
        "directions": ["left", "right"]
      }
    ]
  ],
  "main_channel_rows": [0, 5]
}
```

**字段说明**：
- `width` (int): 网格宽度（必需）
- `height` (int): 网格高度（必需）
- `cells` (array) 或 `grid` (2D array): 格子数据（二选一）
  - `x` (int): x坐标（cells格式）
  - `y` (int): y坐标（cells格式）
  - `type` (string): 格子类型
    - `"normal_channel"` - 普通通道
    - `"main_channel"` - 主通道
    - `"up_down_channel"` - 上下巷道
    - `"obstacle"` - 障碍物
    - `"interface"` - 接驳口
  - `directions` (array): 允许的方向
    - `"up"` - 上
    - `"down"` - 下
    - `"left"` - 左
    - `"right"` - 右
- `main_channel_rows` (array, 可选): 主通道所在的行号列表，不提供时自动检测

##### `get_neighbors(x: int, y: int, is_empty: bool) -> List[Tuple[int, int]]`

获取指定位置的相邻可通行格子。

**参数**：
- `x` (int): x坐标
- `y` (int): y坐标
- `is_empty` (bool): 车辆是否为空载

**返回**：
- `List[Tuple[int, int]]`: 相邻可通行格子的坐标列表

##### `get_cell_type(position: Tuple[int, int]) -> str`

获取格子的类型。

**参数**：
- `position` (Tuple[int, int]): 格子坐标

**返回**：
- `str`: 格子类型常量

##### `set_cargo(x: int, y: int, has_cargo: bool) -> None`

设置格子的货物占用状态。

**参数**：
- `x` (int): x坐标
- `y` (int): y坐标
- `has_cargo` (bool): 是否有货物

---

### Vehicle

车辆数据模型。

#### 构造函数

```python
Vehicle(
    id: str,
    vehicle_type: str,
    current_position: Tuple[int, int],
    target_position: Optional[Tuple[int, int]] = None,
    full_planned_path: List[Tuple[int, int]] = [],
    current_execution_path: List[Tuple[int, int]] = [],
    current_path_index: int = 0
)
```

#### 属性

- `id` (str): 车辆标识
- `vehicle_type` (str): 车辆类型，`VEHICLE_TYPE_EMPTY` 或 `VEHICLE_TYPE_LOADED`
- `current_position` (Tuple[int, int]): 当前位置
- `target_position` (Optional[Tuple[int, int]]): 目标位置
- `full_planned_path` (List[Tuple[int, int]]): 完整规划路径
- `current_execution_path` (List[Tuple[int, int]]): 当前执行路径
- `current_path_index` (int): 当前路径索引

#### 方法

##### `is_empty() -> bool`

判断车辆是否为空载状态。

##### `set_full_planned_path(path: List[Tuple[int, int]]) -> None`

设置完整规划路径。

##### `get_full_planned_path() -> List[Tuple[int, int]]`

获取完整规划路径。

##### `set_current_execution_path(path: List[Tuple[int, int]]) -> None`

设置当前执行路径。

##### `get_next_position() -> Optional[Tuple[int, int]]`

获取下一个位置。

##### `set_target_position(target: Tuple[int, int]) -> None`

设置目标位置。

##### `get_target_position() -> Optional[Tuple[int, int]]`

获取目标位置。

##### `update_position(new_position: Tuple[int, int]) -> None`

更新车辆位置。

##### `clear_path() -> None`

清除所有路径信息。

---

### ConstraintManager

约束管理器，用于路径锁定和冲突检测。

#### 构造函数

```python
ConstraintManager()
```

#### 方法

##### `add_path_constraint(vehicle: Vehicle, path: List[Tuple[int, int]]) -> None`

为车辆添加路径锁定。

**参数**：
- `vehicle` (Vehicle): 车辆对象
- `path` (List[Tuple[int, int]]): 要锁定的路径

##### `remove_path_constraint(vehicle: Vehicle) -> None`

移除车辆的路径锁定。

##### `add_direction_constraint(vehicle: Vehicle, grid: Grid) -> None`

为负载车辆添加方向锁定（主通道）。

**参数**：
- `vehicle` (Vehicle): 负载车辆对象
- `grid` (Grid): 网格地图对象

##### `remove_direction_constraint(vehicle: Vehicle, grid: Grid) -> None`

移除车辆的方向锁定。

##### `check_path_conflicts(path: List[Tuple[int, int]], vehicle: Vehicle) -> List[str]`

检测路径冲突，返回冲突车辆ID列表。

**参数**：
- `path` (List[Tuple[int, int]]): 要检查的路径
- `vehicle` (Vehicle): 车辆对象

**返回**：
- `List[str]`: 冲突车辆ID列表，如果无冲突则返回空列表

---

## 使用示例

本节提供从入门到进阶的多个示例，帮助快速理解工具库的典型使用方式。所有示例均可在 `examples/basic_usage.py` 中找到对应实现。

### 示例0：运行完整 Demo

```bash
python examples/basic_usage.py
```

运行后将依次展示【基本路径规划】【路径冲突检测】【负载车辆路径规划】【路径操作】四个示例，并在终端打印执行日志，便于对照理解。

### 示例1：使用JSON格式加载地图

```python
from src import Grid, Vehicle, AStarPlanner, VEHICLE_TYPE_EMPTY

# 推荐：使用JSON格式加载地图
grid = Grid(10, 10)
grid.load_map_from_json("resource/test_map.json")

vehicle = Vehicle(id="V1", vehicle_type=VEHICLE_TYPE_EMPTY, current_position=(8, 7))
planner = AStarPlanner(grid)
path = planner.find_path(vehicle, (8, 7), (3, 6))

if path:
    vehicle.set_full_planned_path(path)
    print(f"路径长度: {len(path)}")
```

**JSON地图示例** (`test_map.json`):

```json
{
  "width": 15,
  "height": 10,
  "cells": [
    {"x": 0, "y": 0, "type": "main_channel", "directions": ["up", "down", "left", "right"]},
    {"x": 1, "y": 0, "type": "main_channel", "directions": ["up", "down", "left", "right"]},
    {"x": 2, "y": 0, "type": "normal_channel", "directions": ["up", "down"]},
    {"x": 3, "y": 0, "type": "normal_channel", "directions": ["up", "down"]}
  ],
  "main_channel_rows": [0, 5]
}
```

**输出说明**

- 无需依赖 pandas/openpyxl
- JSON格式更清晰易读，便于版本控制
- 支持两种格式：cells数组（稀疏）或grid二维数组（密集）

### 示例2：基本路径规划（使用Excel）

```python
from src import Grid, Vehicle, AStarPlanner, VEHICLE_TYPE_EMPTY

# 使用Excel格式（向后兼容）
grid = Grid(10, 10)
grid.load_map_from_xlsx("resource/test_map.xlsx")

vehicle = Vehicle(id="V1", vehicle_type=VEHICLE_TYPE_EMPTY, current_position=(8, 7))

planner = AStarPlanner(grid)
path = planner.find_path(vehicle, (8, 7), (3, 6))

if path:
    vehicle.set_full_planned_path(path)
    print(f"路径长度: {len(path)} -> {path}")
else:
    print("无法找到路径")
```

**输出说明**

- 成功时打印路径长度与节点序列，可用于直接下发执行
- 失败时会提示"无法找到路径"，需检查地图或目标点

### 示例3：多车路径冲突检测

```python
from src import Grid, Vehicle, AStarPlanner, ConstraintManager, VEHICLE_TYPE_EMPTY

grid = Grid(10, 10)
grid.load_map_from_xlsx("resource/test_map.xlsx")

vehicle1 = Vehicle(id="V1", vehicle_type=VEHICLE_TYPE_EMPTY, current_position=(8, 7))
vehicle2 = Vehicle(id="V2", vehicle_type=VEHICLE_TYPE_EMPTY, current_position=(6, 7))

planner = AStarPlanner(grid)
constraint_manager = ConstraintManager()

path1 = planner.find_path(vehicle1, (8, 7), (3, 6))
constraint_manager.add_path_constraint(vehicle1, path1)

path2 = planner.find_path(vehicle2, (6, 7), (10, 6))
conflicts = constraint_manager.check_path_conflicts(path2, vehicle2)

if conflicts:
    print(f"路径冲突: {conflicts}")
else:
    constraint_manager.add_path_constraint(vehicle2, path2)
    print("路径无冲突，已锁定")
```

**输出说明**

- `conflicts` 列表包含所有产生冲突的车辆 ID
- 可以在收到冲突时触发自定义避让或重规划逻辑

### 示例4：负载车辆方向锁定

```python
from src import Grid, Vehicle, AStarPlanner, ConstraintManager, VEHICLE_TYPE_LOADED

grid = Grid(10, 10)
grid.load_map_from_xlsx("resource/test_map.xlsx")

vehicle = Vehicle(id="V1", vehicle_type=VEHICLE_TYPE_LOADED, current_position=(10, 6))

planner = AStarPlanner(grid)
path = planner.find_path(vehicle, (10, 6), (11, 7))

if path:
    vehicle.set_full_planned_path(path)
    constraint_manager = ConstraintManager()
    constraint_manager.add_direction_constraint(vehicle, grid)
    print("已为负载车辆添加方向锁定")
```

**输出说明**

- 方向锁定只对主通道生效，并限制同一行的对向车进入
- 适合高价值物料或高优先级任务，保障通行权

### 示例5：路径操作与状态更新

```python
test_path = [(8, 7), (7, 7), (6, 7), (5, 7)]
vehicle.set_full_planned_path(test_path)
vehicle.set_current_execution_path(test_path[:2])

next_pos = vehicle.get_next_position()
if next_pos:
    vehicle.update_position(next_pos)
    print(f"车辆移动到 {vehicle.current_position}")

vehicle.set_target_position((4, 7))
vehicle.clear_path()
```

**输出说明**

- 展示如何操作 `Vehicle` 的路径、执行段和位置信息
- 可作为编排执行器（executor）的参考实现

---

## 项目结构

```
route_plan/
├── src/                          # 源代码目录
│   ├── __init__.py              # 包初始化，导出公共API
│   ├── algorithms/
│   │   └── a_star.py            # A*路径规划算法
│   ├── models/
│   │   ├── grid.py              # 地图模型
│   │   └── vehicle.py           # 车辆模型
│   └── utils/
│       └── constraints.py       # 约束管理器
├── examples/                     # 使用示例
│   └── basic_usage.py           # 基本使用示例
├── resource/                    # 资源文件
│   └── test_map.xlsx            # 示例地图文件
├── README.md                     # 本文件
└── .gitignore
```

---

## 常量说明

### 车辆类型
- `VEHICLE_TYPE_EMPTY` - 空载车辆
- `VEHICLE_TYPE_LOADED` - 负载车辆

### 网格类型
- `GRID_TYPE_NORMAL_CHANNEL` - 普通通道（货位区）
- `GRID_TYPE_MAIN_CHANNEL` - 主通道（主干道）
- `GRID_TYPE_UP_DOWN_CHANNEL` - 上下巷道（提升机通道）
- `GRID_TYPE_INTERFACE` - 接驳口（与输送线连接）
- `GRID_TYPE_OBSTACLE` - 障碍物（不可通行）

### 主通道状态
- `MAIN_CHANNEL_STATUS_NULL` - 无方向锁定
- `MAIN_CHANNEL_STATUS_LEFT` - 向左锁定
- `MAIN_CHANNEL_STATUS_RIGHT` - 向右锁定

---

## 依赖

### 核心依赖

- Python >= 3.7

### 可选依赖

如果使用 Excel 格式地图（`load_map_from_xlsx`），需要安装：

- pandas >= 1.0.0
- openpyxl

安装可选依赖：
```bash
pip install pandas openpyxl
```

**推荐**：使用 JSON 格式地图（`load_map_from_json`），无需额外依赖。

---

## 核心算法说明

### A*路径规划

本工具库采用A*算法进行路径规划，具有以下特点：

1. **启发式函数**：使用曼哈顿距离作为启发式函数
2. **方向约束**：根据网格格子的允许方向列表限制扩展方向
3. **货物占用**：负载车辆不能通过有货物的格子
4. **时间复杂度**：O(b^d)，其中b为分支因子，d为路径深度

### 约束管理

- **位置锁定**：锁定路径中的格子，防止其他车辆占用
- **方向锁定**：负载车辆在主通道上建立方向约束，防止对向车辆进入
- **冲突检测**：检测路径是否与已锁定的格子冲突


