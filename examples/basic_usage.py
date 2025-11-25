"""
基本使用示例

演示如何使用路径规划工具库进行基本的路径规划和冲突检测。
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src import Grid, Vehicle, AStarPlanner, ConstraintManager, VEHICLE_TYPE_EMPTY, VEHICLE_TYPE_LOADED


def example_0_json_map_loading():
    """示例0：使用JSON格式加载地图"""
    print("=" * 60)
    print("示例0：使用JSON格式加载地图（推荐）")
    print("=" * 60)
    
    # 创建一个简单的测试地图JSON
    import json
    json_map_path = os.path.join(project_root, "resource", "simple_map.json")
    
    # 如果JSON文件不存在，创建一个简单的示例
    if not os.path.exists(json_map_path):
        simple_map = {
            "width": 5,
            "height": 3,
            "cells": [
                {"x": 0, "y": 0, "type": "main_channel", "directions": ["up", "down", "left", "right"]},
                {"x": 1, "y": 0, "type": "main_channel", "directions": ["up", "down", "left", "right"]},
                {"x": 2, "y": 0, "type": "main_channel", "directions": ["up", "down", "left", "right"]},
                {"x": 3, "y": 0, "type": "main_channel", "directions": ["up", "down", "left", "right"]},
                {"x": 4, "y": 0, "type": "main_channel", "directions": ["up", "down", "left", "right"]},
                {"x": 0, "y": 1, "type": "normal_channel", "directions": ["up", "down"]},
                {"x": 1, "y": 1, "type": "normal_channel", "directions": ["up", "down"]},
                {"x": 2, "y": 1, "type": "normal_channel", "directions": ["up", "down"]},
                {"x": 3, "y": 1, "type": "normal_channel", "directions": ["up", "down"]},
                {"x": 4, "y": 1, "type": "normal_channel", "directions": ["up", "down"]},
                {"x": 0, "y": 2, "type": "interface", "directions": ["up", "down", "left", "right"]},
                {"x": 4, "y": 2, "type": "interface", "directions": ["up", "down", "left", "right"]}
            ],
            "main_channel_rows": [0]
        }
        
        os.makedirs(os.path.dirname(json_map_path), exist_ok=True)
        with open(json_map_path, 'w', encoding='utf-8') as f:
            json.dump(simple_map, f, indent=2, ensure_ascii=False)
        print(f"✓ 创建示例JSON地图: {json_map_path}")
    
    # 使用JSON格式加载地图
    grid = Grid(5, 3)
    grid.load_map_from_json(json_map_path)
    print(f"✓ 从JSON加载地图完成: 宽度={grid.width}, 高度={grid.height}")
    print(f"✓ 主通道行: {grid.get_main_rows()}")
    
    # 测试路径规划
    vehicle = Vehicle(id="V1", vehicle_type=VEHICLE_TYPE_EMPTY, current_position=(0, 2))
    planner = AStarPlanner(grid)
    path = planner.find_path(vehicle, (0, 2), (4, 2))
    
    if path:
        print(f"✓ 找到路径，长度: {len(path)}")
        print(f"  路径: {' -> '.join(str(p) for p in path)}")
    else:
        print("✗ 无法找到路径")
    
    print("✓ JSON格式优势：无需pandas依赖，格式清晰，易于版本控制")
    print()


def example_1_basic_path_planning():
    """示例1：基本路径规划"""
    print("=" * 60)
    print("示例1：基本路径规划")
    print("=" * 60)
    
    # 1. 创建地图
    grid = Grid(10, 10)
    map_path = os.path.join(project_root, "resource", "test_map.xlsx")
    grid.load_map_from_xlsx(map_path)
    print("✓ 地图加载完成")
    
    # 2. 创建车辆
    vehicle = Vehicle(
        id="V1",
        vehicle_type=VEHICLE_TYPE_EMPTY,
        current_position=(8, 7)
    )
    print(f"✓ 创建车辆: {vehicle.id}, 位置: {vehicle.current_position}")
    
    # 3. 创建路径规划器
    planner = AStarPlanner(grid)
    
    # 4. 规划路径
    start = (8, 7)
    goal = (3, 6)
    print(f"✓ 开始规划路径: {start} -> {goal}")
    
    path = planner.find_path(vehicle, start, goal)
    
    if path:
        print(f"✓ 找到路径，长度: {len(path)}")
        print(f"  路径: {' -> '.join(str(p) for p in path)}")
        vehicle.set_full_planned_path(path)
    else:
        print("✗ 无法找到路径")
    
    print()


def example_2_conflict_detection():
    """示例2：路径冲突检测"""
    print("=" * 60)
    print("示例2：路径冲突检测")
    print("=" * 60)
    
    # 1. 创建地图
    grid = Grid(10, 10)
    map_path = os.path.join(project_root, "resource", "test_map.xlsx")
    grid.load_map_from_xlsx(map_path)
    print("✓ 地图加载完成")
    
    # 2. 创建两辆车
    vehicle1 = Vehicle(id="V1", vehicle_type=VEHICLE_TYPE_EMPTY, current_position=(8, 7))
    vehicle2 = Vehicle(id="V2", vehicle_type=VEHICLE_TYPE_EMPTY, current_position=(6, 7))
    print(f"✓ 创建车辆: V1 位置 {vehicle1.current_position}, V2 位置 {vehicle2.current_position}")
    
    # 3. 创建路径规划器和约束管理器
    planner = AStarPlanner(grid)
    constraint_manager = ConstraintManager()
    
    # 4. 为车辆1规划路径并锁定
    path1 = planner.find_path(vehicle1, (8, 7), (3, 6))
    if path1:
        print(f"✓ V1 路径: {' -> '.join(str(p) for p in path1[:5])}... (长度: {len(path1)})")
        constraint_manager.add_path_constraint(vehicle1, path1)
        print("✓ V1 路径已锁定")
    
    # 5. 为车辆2规划路径并检测冲突
    path2 = planner.find_path(vehicle2, (6, 7), (10, 6))
    if path2:
        print(f"✓ V2 路径: {' -> '.join(str(p) for p in path2[:5])}... (长度: {len(path2)})")
        
        # 检测冲突
        conflicts = constraint_manager.check_path_conflicts(path2, vehicle2)
        if conflicts:
            print(f"⚠ 发现路径冲突: V2 与 {conflicts} 的路径存在冲突")
        else:
            print("✓ 未发现路径冲突")
            constraint_manager.add_path_constraint(vehicle2, path2)
            print("✓ V2 路径已锁定")
    
    print()


def example_3_loaded_vehicle():
    """示例3：负载车辆路径规划"""
    print("=" * 60)
    print("示例3：负载车辆路径规划")
    print("=" * 60)
    
    # 1. 创建地图
    grid = Grid(10, 10)
    map_path = os.path.join(project_root, "resource", "test_map.xlsx")
    grid.load_map_from_xlsx(map_path)
    print("✓ 地图加载完成")
    
    # 2. 创建负载车辆
    vehicle = Vehicle(
        id="V1",
        vehicle_type=VEHICLE_TYPE_LOADED,  # 负载状态
        current_position=(10, 6)
    )
    print(f"✓ 创建负载车辆: {vehicle.id}, 位置: {vehicle.current_position}")
    print(f"  负载状态: {'空载' if vehicle.is_empty() else '负载'}")
    
    # 3. 创建路径规划器和约束管理器
    planner = AStarPlanner(grid)
    constraint_manager = ConstraintManager()
    
    # 4. 规划路径
    path = planner.find_path(vehicle, (10, 6), (11, 7))
    
    if path:
        print(f"✓ 找到路径，长度: {len(path)}")
        print(f"  路径: {' -> '.join(str(p) for p in path)}")
        vehicle.set_full_planned_path(path)
        
        # 5. 添加方向锁定（负载车辆特有）
        constraint_manager.add_direction_constraint(vehicle, grid)
        print("✓ 已为负载车辆添加方向锁定")
    else:
        print("✗ 无法找到路径")
    
    print()


def example_4_path_operations():
    """示例4：路径操作"""
    print("=" * 60)
    print("示例4：路径操作")
    print("=" * 60)
    
    # 创建车辆
    vehicle = Vehicle(id="V1", vehicle_type=VEHICLE_TYPE_EMPTY, current_position=(8, 7))
    print(f"✓ 创建车辆: {vehicle.id}")
    
    # 设置路径
    test_path = [(8, 7), (7, 7), (6, 7), (5, 7), (4, 7)]
    vehicle.set_full_planned_path(test_path)
    print(f"✓ 设置完整路径: {' -> '.join(str(p) for p in test_path)}")
    
    # 设置执行路径
    execution_path = test_path[:3]
    vehicle.set_current_execution_path(execution_path)
    print(f"✓ 设置执行路径: {' -> '.join(str(p) for p in execution_path)}")
    
    # 获取下一个位置
    next_pos = vehicle.get_next_position()
    if next_pos:
        print(f"✓ 下一个位置: {next_pos}")
        
        # 更新位置
        vehicle.update_position(next_pos)
        print(f"✓ 更新位置到: {vehicle.current_position}")
    
    # 设置目标位置
    vehicle.set_target_position((4, 7))
    print(f"✓ 设置目标位置: {vehicle.get_target_position()}")
    
    # 清除路径
    vehicle.clear_path()
    print(f"✓ 清除路径完成")
    print(f"  完整路径: {vehicle.get_full_planned_path()}")
    
    print()


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("四向穿梭车路径规划工具库 - 使用示例")
    print("=" * 60 + "\n")
    
    try:
        example_0_json_map_loading()
        example_1_basic_path_planning()
        example_2_conflict_detection()
        example_3_loaded_vehicle()
        example_4_path_operations()
        
        print("=" * 60)
        print("所有示例运行完成！")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

