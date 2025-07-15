"""
约束控制器使用示例

演示路径冲突检测功能：
1. 添加限制路径 - 锁定路径中的坐标
2. 删除约束信息 - 释放车辆锁定的坐标  
3. 冲突检测 - 检查新路径是否与已锁定坐标冲突
"""

from src.models.constraints import ConstraintManager
from src.models.vehicle import Vehicle, VEHICLE_TYPE_EMPTY

def demonstrate_constraint_system():
    print("=== 约束控制器演示 ===\n")
    
    # 创建约束管理器
    constraint_manager = ConstraintManager()
    
    # 创建几辆车
    vehicle1 = Vehicle(id="V001", vehicle_type=VEHICLE_TYPE_EMPTY, current_position=(1, 1))
    vehicle2 = Vehicle(id="V002", vehicle_type=VEHICLE_TYPE_EMPTY, current_position=(1, 2))
    vehicle3 = Vehicle(id="V003", vehicle_type=VEHICLE_TYPE_EMPTY, current_position=(1, 3))
    
    print("创建了三辆车: V001, V002, V003\n")
    
    # 1. 演示添加路径约束
    print("=== 1. 添加路径约束 ===")
    path1 = [(1, 1), (2, 1), (3, 1), (4, 1)]
    path2 = [(1, 2), (2, 2), (3, 2), (4, 2)]
    
    # 为车辆1添加路径约束
    success1 = constraint_manager.add_path_constraint(vehicle1, path1)
    print(f"车辆V001路径添加结果: {success1}")
    
    # 为车辆2添加路径约束
    success2 = constraint_manager.add_path_constraint(vehicle2, path2)
    print(f"车辆V002路径添加结果: {success2}")
    
    # 打印当前锁定状态
    constraint_manager.print_lock_info()
    
    # 2. 演示冲突检测
    print("\n=== 2. 冲突检测 ===")
    
    # 测试与现有路径冲突的新路径
    conflicting_path = [(2, 1), (3, 1), (4, 1), (5, 1)]  # 与V001的路径有重叠
    conflicts = constraint_manager.get_conflicting_vehicles(conflicting_path)
    print(f"冲突车辆: {conflicts}")
    
    # 测试无冲突的路径
    safe_path = [(1, 3), (2, 3), (3, 3), (4, 3)]
    conflicts = constraint_manager.get_conflicting_vehicles(safe_path)
    print(f"安全路径冲突检测: {conflicts}")
    
    # 3. 演示尝试添加冲突路径
    print("\n=== 3. 尝试添加冲突路径 ===")
    success3 = constraint_manager.add_path_constraint(vehicle3, conflicting_path)
    print(f"车辆V003冲突路径添加结果: {success3}")
    
    # 4. 演示单点查询
    print("\n=== 4. 单点查询 ===")
    test_positions = [(2, 1), (2, 2), (5, 5)]
    for pos in test_positions:
        is_locked = constraint_manager.is_position_locked(pos)
        owner = constraint_manager.get_position_owner(pos)
        print(f"位置 {pos}: 锁定={is_locked}, 拥有者={owner}")
    
    # 5. 演示删除约束
    print("\n=== 5. 删除车辆约束 ===")
    print(f"删除前锁定状态: {constraint_manager.get_lock_status()}")
    
    removed_count = constraint_manager.remove_vehicle_constraints(vehicle1)
    print(f"删除车辆V001的约束，释放了 {removed_count} 个坐标")
    
    print(f"删除后锁定状态: {constraint_manager.get_lock_status()}")
    
    # 6. 演示现在可以添加之前冲突的路径
    print("\n=== 6. 重新尝试添加之前冲突的路径 ===")
    success4 = constraint_manager.add_path_constraint(vehicle3, conflicting_path)
    print(f"车辆V003路径添加结果: {success4}")
    
    # 7. 最终状态
    print("\n=== 7. 最终状态 ===")
    constraint_manager.print_lock_info()
    
    # 8. 清除所有约束
    print("\n=== 8. 清除所有约束 ===")
    constraint_manager.clear_all_constraints()
    final_status = constraint_manager.get_lock_status()
    print(f"清除后状态: {final_status}")

def demonstrate_realistic_scenario():
    """演示真实场景中的约束管理"""
    print("\n\n=== 真实场景演示 ===")
    
    constraint_manager = ConstraintManager()
    
    # 模拟三辆车同时执行任务
    vehicles = [
        Vehicle(id="V001", vehicle_type=VEHICLE_TYPE_EMPTY, current_position=(0, 0)),
        Vehicle(id="V002", vehicle_type=VEHICLE_TYPE_EMPTY, current_position=(0, 1)),
        Vehicle(id="V003", vehicle_type=VEHICLE_TYPE_EMPTY, current_position=(0, 2))
    ]
    
    # 定义各车辆的路径
    paths = {
        "V001": [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],
        "V002": [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)],
        "V003": [(0, 2), (1, 2), (2, 2), (2, 1), (2, 0)]  # 这个路径会与前两个冲突
    }
    
    print("模拟三辆车的路径分配：")
    for vehicle in vehicles:
        path = paths[vehicle.id]
        print(f"\n尝试为 {vehicle.id} 分配路径: {path}")
        
        # 先检查冲突
        conflicts = constraint_manager.get_conflicting_vehicles(path)
        if conflicts:
            print(f"⚠️  路径冲突，与车辆 {conflicts} 冲突")
            print("需要重新规划路径或等待")
        else:
            success = constraint_manager.add_path_constraint(vehicle, path)
            if success:
                print(f"✅ 路径分配成功")
            else:
                print(f"❌ 路径分配失败")
    
    print(f"\n最终分配状态:")
    constraint_manager.print_lock_info()

if __name__ == "__main__":
    demonstrate_constraint_system()
    demonstrate_realistic_scenario() 