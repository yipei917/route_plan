#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.scheduler import Scheduler
from src.models.grid import GRID_TYPE_MAIN_CHANNEL, GRID_TYPE_NORMAL_CHANNEL

def test_single_path(scheduler, test_path, path_name):
    """测试单个路径"""
    print(f"\n--- 测试路径 {path_name} ---")
    print(f"路径: {test_path}")
    print("路径分析:")
    
    # 检查每个位置的网格类型
    for i, position in enumerate(test_path):
        cell = scheduler.grid.get_cell(position[0], position[1])
        if cell:
            grid_type = "主干道" if cell.grid_type == GRID_TYPE_MAIN_CHANNEL else "一般道路"
            print(f"  位置 {i}: {position} -> {grid_type}")
        else:
            print(f"  位置 {i}: {position} -> 无效位置")
    
    # 测试当前的 analyze_path_segments 方法
    try:
        result = scheduler.analyze_path_segments(test_path)
        print(f"方法返回: {result}")
        print(f"返回类型: {type(result)}")
        if isinstance(result, list) and len(result) > 0:
            print(f"返回长度: {len(result)}")
    except Exception as e:
        print(f"方法执行出错: {e}")

def test_analyze_path_segments():
    """测试路径段分析功能"""
    print("=== 测试 analyze_path_segments 功能 ===")
    
    # 创建调度器
    scheduler = Scheduler(num_vehicles=1, step_size=3)
    scheduler.initialize()
    
    # 创建多个测试路径
    test_paths = {
        "路径1": [(8, 7), (7, 7), (6, 7), (5, 7), (4, 7), (3, 7), (2, 7), (2, 6)],
        "路径2": [(3, 7), (2, 7), (2, 6)],
        "路径3": [(8, 7), (9, 7), (10, 7), (10, 6), (10, 5), (10, 4), (10, 3)],
        "路径4": [(10, 7), (10, 6), (10, 5), (10, 4), (10, 3)],
        "路径5": [(8, 7), (7, 7), (7, 8), (7, 9), (7, 10), (7, 11), (7, 12), (7, 13), (7, 14), (6, 14), (6, 15)]
    }
    
    # 对每个路径进行测试
    for path_name, test_path in test_paths.items():
        test_single_path(scheduler, test_path, path_name)

if __name__ == "__main__":
    test_analyze_path_segments() 