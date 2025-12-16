"""Инструмент для создания цилиндра в CAD системе в указанных координатах."""

from fastmcp import Context
from pydantic import Field
from mcp.types import TextContent
from .utils import ToolResult
from mcp_instance import mcp
from .tool_create_shapes import _create_shape_impl

@mcp.tool(
    name="create_cylinder",
    description="""
    Создать цилиндр в CAD системе в указанных координатах.
    Создает 3D-цилиндр с заданным диаметром.
    Координаты x, y, z указывают центр основания цилиндра.
    """
)
async def create_cylinder(
    size: float = Field(
        10.0,
        description="Диаметр цилиндра в миллиметрах (положительное число)"
    ),
    x: float = Field(
        0.0,
        description="X-координата центра основания цилиндра (в мм)"
    ),
    y: float = Field(
        0.0,
        description="Y-координата центра основания цилиндра (в мм)"
    ),
    z: float = Field(
        0.0,
        description="Z-координата центра основания цилиндра (в мм)"
    ),
    ctx: Context = None
) -> ToolResult:
    """
    Создать цилиндр в CAD системе.
    
    Args:
        size: Диаметр цилиндра в миллиметрах (положительное число)
        x, y, z: Координаты центра основания цилиндра
        ctx: Контекст для логирования
    
    Returns:
        ToolResult: Результат выполнения инструмента
    """
    return await _create_shape_impl("cylinder", size, x, y, z, ctx)