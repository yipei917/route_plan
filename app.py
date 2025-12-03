"""
路径规划 API 服务
使用 FastAPI 将路径规划功能暴露为 REST API
"""

import os
import json
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from src import Grid, Vehicle, AStarPlanner, ConstraintManager, VEHICLE_TYPE_EMPTY, VEHICLE_TYPE_LOADED

app = FastAPI(
    title="四向穿梭车路径规划 API",
    description="提供带方向约束的A*路径规划、路径冲突检测等功能",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局地图存储（生产环境建议使用数据库或缓存）
grid_storage: Dict[str, Grid] = {}
constraint_manager_storage: Dict[str, ConstraintManager] = {}


# ============ 请求/响应模型 ============

class Position(BaseModel):
    """位置坐标"""
    x: int = Field(..., description="X坐标")
    y: int = Field(..., description="Y坐标")


class PathPlanRequest(BaseModel):
    """路径规划请求"""
    map_id: str = Field(..., description="地图ID")
    vehicle_id: str = Field(..., description="车辆ID")
    vehicle_type: str = Field(..., description="车辆类型: 'empty' 或 'loaded'")
    start: Position = Field(..., description="起点坐标")
    goal: Position = Field(..., description="终点坐标")
    current_position: Optional[Position] = Field(None, description="车辆当前位置（如果与起点不同）")


class PathPlanResponse(BaseModel):
    """路径规划响应"""
    success: bool
    path: Optional[List[Position]] = None
    path_length: Optional[int] = None
    message: str


class ConflictCheckRequest(BaseModel):
    """冲突检测请求"""
    map_id: str = Field(..., description="地图ID")
    vehicle_id: str = Field(..., description="车辆ID")
    vehicle_type: str = Field(..., description="车辆类型: 'empty' 或 'loaded'")
    path: List[Position] = Field(..., description="要检测的路径")
    existing_paths: Optional[Dict[str, List[Position]]] = Field(None, description="其他车辆的已锁定路径 {vehicle_id: path}")


class ConflictCheckResponse(BaseModel):
    """冲突检测响应"""
    has_conflict: bool
    conflicting_vehicles: List[str] = []
    message: str


class MapLoadRequest(BaseModel):
    """地图加载请求（JSON格式）"""
    map_id: str = Field(..., description="地图ID")
    width: int = Field(..., description="地图宽度")
    height: int = Field(..., description="地图高度")
    cells: List[Dict[str, Any]] = Field(..., description="单元格配置列表")
    main_channel_rows: Optional[List[int]] = Field(None, description="主通道行号列表")


class MapLoadResponse(BaseModel):
    """地图加载响应"""
    success: bool
    map_id: str
    width: int
    height: int
    message: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str


# ============ 辅助函数 ============

def position_to_tuple(pos: Position) -> tuple:
    """将Position模型转换为元组"""
    return (pos.x, pos.y)


def tuple_to_position(t: tuple) -> Position:
    """将元组转换为Position模型"""
    return Position(x=t[0], y=t[1])


# ============ API 端点 ============

@app.get("/", tags=["基础"])
async def root():
    """根路径"""
    return {
        "service": "四向穿梭车路径规划 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["基础"])
async def health_check():
    """健康检查"""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/api/v1/map/load", response_model=MapLoadResponse, tags=["地图管理"])
async def load_map(request: MapLoadRequest):
    """
    加载地图（JSON格式）
    
    从JSON配置创建地图并存储到内存中。
    """
    try:
        grid = Grid(request.width, request.height)
        
        # 加载单元格配置
        for cell_data in request.cells:
            x = cell_data.get("x")
            y = cell_data.get("y")
            grid_type = cell_data.get("type", "normal_channel")
            directions = cell_data.get("directions", [])
            
            if x is not None and y is not None:
                grid.set_cell_type(x, y, grid_type)
                grid.set_cell_directions(x, y, directions)
        
        # 设置主通道行
        if request.main_channel_rows:
            grid.main_channel_rows = request.main_channel_rows
        
        # 存储地图
        grid_storage[request.map_id] = grid
        
        # 为地图创建约束管理器
        if request.map_id not in constraint_manager_storage:
            constraint_manager_storage[request.map_id] = ConstraintManager()
        
        return MapLoadResponse(
            success=True,
            map_id=request.map_id,
            width=grid.width,
            height=grid.height,
            message="地图加载成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"地图加载失败: {str(e)}")


@app.post("/api/v1/map/load/file", tags=["地图管理"])
async def load_map_from_file(
    map_id: str,
    file: UploadFile = File(...)
):
    """
    从文件加载地图
    
    支持 JSON 和 Excel 格式。
    """
    try:
        # 读取文件内容
        content = await file.read()
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext == ".json":
            # JSON格式
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as tmp_file:
                tmp_file.write(content.decode("utf-8"))
                tmp_path = tmp_file.name
            
            try:
                map_data = json.loads(content.decode("utf-8"))
                width = map_data.get("width")
                height = map_data.get("height")
                
                if not width or not height:
                    raise ValueError("JSON文件必须包含width和height字段")
                
                grid = Grid(width, height)
                grid.load_map_from_json(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
        elif file_ext in [".xlsx", ".xls"]:
            # Excel格式
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            try:
                grid = Grid(10, 10)  # 默认尺寸，load_map_from_xlsx会读取实际尺寸
                grid.load_map_from_xlsx(tmp_path)
            finally:
                os.unlink(tmp_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")
        
        # 存储地图
        grid_storage[map_id] = grid
        
        # 为地图创建约束管理器
        if map_id not in constraint_manager_storage:
            constraint_manager_storage[map_id] = ConstraintManager()
        
        return {
            "success": True,
            "map_id": map_id,
            "width": grid.width,
            "height": grid.height,
            "message": "地图加载成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"地图加载失败: {str(e)}")


@app.post("/api/v1/path/plan", response_model=PathPlanResponse, tags=["路径规划"])
async def plan_path(request: PathPlanRequest):
    """
    路径规划
    
    使用A*算法规划从起点到终点的路径。
    """
    try:
        # 检查地图是否存在
        if request.map_id not in grid_storage:
            raise HTTPException(status_code=404, detail=f"地图 {request.map_id} 不存在，请先加载地图")
        
        grid = grid_storage[request.map_id]
        
        # 验证车辆类型
        if request.vehicle_type not in [VEHICLE_TYPE_EMPTY, VEHICLE_TYPE_LOADED]:
            raise HTTPException(status_code=400, detail=f"无效的车辆类型: {request.vehicle_type}")
        
        # 创建车辆对象
        start_pos = position_to_tuple(request.start)
        current_pos = position_to_tuple(request.current_position) if request.current_position else start_pos
        
        vehicle = Vehicle(
            id=request.vehicle_id,
            vehicle_type=request.vehicle_type,
            current_position=current_pos
        )
        
        # 创建路径规划器
        planner = AStarPlanner(grid)
        
        # 规划路径
        goal_pos = position_to_tuple(request.goal)
        path = planner.find_path(vehicle, start_pos, goal_pos)
        
        if path:
            path_positions = [tuple_to_position(p) for p in path]
            return PathPlanResponse(
                success=True,
                path=path_positions,
                path_length=len(path),
                message="路径规划成功"
            )
        else:
            return PathPlanResponse(
                success=False,
                path=None,
                path_length=None,
                message="无法找到路径"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"路径规划失败: {str(e)}")


@app.post("/api/v1/conflict/check", response_model=ConflictCheckResponse, tags=["冲突检测"])
async def check_conflict(request: ConflictCheckRequest):
    """
    路径冲突检测
    
    检测给定路径是否与其他车辆的已锁定路径存在冲突。
    """
    try:
        # 检查地图是否存在
        if request.map_id not in grid_storage:
            raise HTTPException(status_code=404, detail=f"地图 {request.map_id} 不存在")
        
        if request.map_id not in constraint_manager_storage:
            constraint_manager_storage[request.map_id] = ConstraintManager()
        
        constraint_manager = constraint_manager_storage[request.map_id]
        
        # 验证车辆类型
        if request.vehicle_type not in [VEHICLE_TYPE_EMPTY, VEHICLE_TYPE_LOADED]:
            raise HTTPException(status_code=400, detail=f"无效的车辆类型: {request.vehicle_type}")
        
        # 创建车辆对象
        vehicle = Vehicle(
            id=request.vehicle_id,
            vehicle_type=request.vehicle_type,
            current_position=position_to_tuple(request.path[0]) if request.path else (0, 0)
        )
        
        # 转换路径格式
        path_tuples = [position_to_tuple(p) for p in request.path]
        
        # 如果有其他车辆的路径，先添加到约束管理器
        if request.existing_paths:
            for other_vehicle_id, other_path in request.existing_paths.items():
                other_path_tuples = [position_to_tuple(p) for p in other_path]
                other_vehicle = Vehicle(
                    id=other_vehicle_id,
                    vehicle_type=VEHICLE_TYPE_EMPTY,  # 默认类型
                    current_position=other_path_tuples[0] if other_path_tuples else (0, 0)
                )
                constraint_manager.add_path_constraint(other_vehicle, other_path_tuples)
        
        # 检测冲突
        conflicts = constraint_manager.check_path_conflicts(path_tuples, vehicle)
        
        if conflicts:
            return ConflictCheckResponse(
                has_conflict=True,
                conflicting_vehicles=list(conflicts),
                message=f"发现路径冲突，与车辆 {list(conflicts)} 的路径存在冲突"
            )
        else:
            return ConflictCheckResponse(
                has_conflict=False,
                conflicting_vehicles=[],
                message="未发现路径冲突"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"冲突检测失败: {str(e)}")


@app.post("/api/v1/constraint/add", tags=["约束管理"])
async def add_path_constraint(
    map_id: str,
    vehicle_id: str,
    vehicle_type: str,
    path: List[Position]
):
    """
    添加路径约束（锁定路径）
    
    将车辆的路径添加到约束管理器中，用于后续的冲突检测。
    """
    try:
        if map_id not in constraint_manager_storage:
            constraint_manager_storage[map_id] = ConstraintManager()
        
        constraint_manager = constraint_manager_storage[map_id]
        
        # 创建车辆对象
        path_tuples = [position_to_tuple(p) for p in path]
        vehicle = Vehicle(
            id=vehicle_id,
            vehicle_type=vehicle_type,
            current_position=path_tuples[0] if path_tuples else (0, 0)
        )
        
        # 添加路径约束
        constraint_manager.add_path_constraint(vehicle, path_tuples)
        
        return {
            "success": True,
            "message": f"车辆 {vehicle_id} 的路径已锁定"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加路径约束失败: {str(e)}")


@app.delete("/api/v1/constraint/remove/{map_id}/{vehicle_id}", tags=["约束管理"])
async def remove_path_constraint(map_id: str, vehicle_id: str):
    """
    移除路径约束
    
    清除指定车辆的路径锁定。
    """
    try:
        if map_id not in constraint_manager_storage:
            return {"success": False, "message": "约束管理器不存在"}
        
        constraint_manager = constraint_manager_storage[map_id]
        
        # 创建临时车辆对象用于查找
        dummy_vehicle = Vehicle(
            id=vehicle_id,
            vehicle_type=VEHICLE_TYPE_EMPTY,
            current_position=(0, 0)
        )
        
        constraint_manager.remove_path_constraint(dummy_vehicle)
        
        return {
            "success": True,
            "message": f"车辆 {vehicle_id} 的路径约束已移除"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"移除路径约束失败: {str(e)}")


@app.get("/api/v1/map/list", tags=["地图管理"])
async def list_maps():
    """
    列出所有已加载的地图
    """
    maps = []
    for map_id, grid in grid_storage.items():
        maps.append({
            "map_id": map_id,
            "width": grid.width,
            "height": grid.height
        })
    return {"maps": maps}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

