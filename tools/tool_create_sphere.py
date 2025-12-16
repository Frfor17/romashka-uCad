"""Инструмент для создания сферы в CAD системе в указанных координатах."""

from fastmcp import Context
from pydantic import Field
from mcp.types import TextContent
from .utils import ToolResult
from mcp_instance import mcp
from .tool_create_shapes import _create_shape_impl

@mcp.tool(
    name="create_sphere",
    description="""
    Создать сферу в CAD системе в указанных координатах.
    Создает 3D-сферу с заданным диаметром.
    Координаты x, y, z указывают центр сферы.
    """
)
async def create_sphere(
    size: float = Field(
        10.0,
        description="Диаметр сферы в миллиметрах (положительное число)"
    ),
    x: float = Field(
        0.0,
        description="X-координата центра сферы (в мм)"
    ),
    y: float = Field(
        0.0,
        description="Y-координата центра сферы (в мм)"
    ),
    z: float = Field(
        0.0,
        description="Z-координата центра сферы (в мм)"
    ),
    ctx: Context = None
) -> ToolResult:
    """
    Создать сферу в CAD системе.
    
    Args:
        size: Диаметр сферы в миллиметрах (положительное число)
        x, y, z: Координаты центра сферы
        ctx: Контекст для логирования
    
    Returns:
        ToolResult: Результат выполнения инструмента
    """
    return await _create_shape_impl("sphere", size, x, y, z, ctx)