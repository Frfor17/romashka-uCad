"""Инструмент для создания куба в CAD системе в указанных координатах."""

from fastmcp import Context
from pydantic import Field
from mcp.types import TextContent
from .utils import ToolResult
from mcp_instance import mcp
from .tool_create_shapes import _create_shape_impl

@mcp.tool(
    name="create_cube",
    description="""
    Создать куб в CAD системе в указанных координатах.
    Создает 3D-куб с заданным размером.
    Координаты x, y, z указывают один из углов куба (начальную точку).
    """
)
async def create_cube(
    size: float = Field(
        10.0,
        description="Размер куба в миллиметрах (положительное число)"
    ),
    x: float = Field(
        0.0,
        description="X-координата начальной точки куба (в мм)"
    ),
    y: float = Field(
        0.0,
        description="Y-координата начальной точки куба (в мм)"
    ),
    z: float = Field(
        0.0,
        description="Z-координата начальной точки куба (в мм)"
    ),
    ctx: Context = None
) -> ToolResult:
    """
    Создать куб в CAD системе.
    
    Args:
        size: Размер куба в миллиметрах (положительное число)
        x, y, z: Координаты начальной точки куба
        ctx: Контекст для логирования
    
    Returns:
        ToolResult: Результат выполнения инструмента
    """
    return await _create_shape_impl("cube", size, x, y, z, ctx)