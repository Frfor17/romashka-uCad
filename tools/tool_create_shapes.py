"""Инструмент для создания 3D-фигуры в CAD системе с указанными координатами."""

import httpx
from fastmcp import Context
from pydantic import Field
from mcp.types import TextContent
from mcp_instance import mcp
from .utils import ToolResult, validate_shape_type, validate_size

async def _create_shape_impl(
    shape_type: str,
    size: float,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
    ctx: Context = None
) -> ToolResult:
    """
    Внутренняя реализация создания 3D-фигуры (без декоратора для прямого вызова).
    
    Args:
        shape_type: Тип фигуры: cube (куб), sphere (сфера), cylinder (цилиндр)
        size: Размер фигуры в миллиметрах (положительное число)
        x, y, z: Координаты центра фигуры в миллиметрах
        ctx: Контекст для логирования
    
    Returns:
        ToolResult: Результат выполнения инструмента
    """
    if ctx:
        await ctx.info(f"🚀 Начинаем создание фигуры типа: {shape_type} в точке ({x}, {y}, {z})")
    
    if not validate_shape_type(shape_type):
        valid_shapes = ["cube", "sphere", "cylinder"]
        error_msg = f"Ошибка: неподдерживаемый тип фигуры. Используйте: {', '.join(valid_shapes)}"
        if ctx:
            await ctx.error(f"❌ {error_msg}")
        
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)],
            structured_content={"error": "invalid_shape_type"},
            meta={"status": "validation_error"}
        )
    
    if not validate_size(size):
        error_msg = "Ошибка: размер должен быть положительным числом"
        if ctx:
            await ctx.error(f"❌ {error_msg}")
        
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)],
            structured_content={"error": "invalid_size"},
            meta={"status": "validation_error"}
        )
    
    if ctx:
        await ctx.info(f"🔧 Параметры: тип={shape_type}, размер={size}мм, координаты=({x}, {y}, {z})")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "shape_type": shape_type.lower(), 
                "size": size,
                "x": x,
                "y": y,
                "z": z
            }
            response = await client.get(
                "http://localhost:8001/api/cad/create-shape",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if ctx:
                await ctx.info("✅ Фигура создана успешно")
            
            result_text = (
                f"✅ Фигура создана успешно!\n"
                f"📐 Тип: {data.get('parameters', {}).get('shape_type', 'неизвестно')}\n"
                f"📏 Размер: {data.get('parameters', {}).get('size', 'неизвестно')} мм\n"
                f"📍 Координаты: ({x}, {y}, {z}) мм\n"
                f"🎯 Результат: {data.get('result', 'успешно')}"
            )
            
            return ToolResult(
                content=[TextContent(type="text", text=result_text)],
                structured_content=data,
                meta={
                    "shape_type": shape_type,
                    "size": size,
                    "x": x,
                    "y": y,
                    "z": z,
                    "status": "success"
                }
            )
            
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP ошибка: {e.response.status_code} - {e.response.text}"
        if ctx:
            await ctx.error(f"❌ {error_msg}")
        
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)],
            structured_content={"error": str(e)},
            meta={"status": "http_error"}
        )
    except Exception as e:
        error_msg = f"Ошибка при создании фигуры: {str(e)}"
        if ctx:
            await ctx.error(f"❌ {error_msg}")
        
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)],
            structured_content={"error": str(e)},
            meta={"status": "error"}
        )

@mcp.tool(
    name="create_shape",
    description="""
    Создать 3D-фигуру в CAD системе в указанных координатах.
    Поддерживаемые типы фигур: cube (куб), sphere (сфера), cylinder (цилиндр).
    Размер указывается в миллиметрах как положительное число.
    Координаты x, y, z указывают положение центра фигуры (или начальную точку для куба).
    """
)
async def create_shape(
    shape_type: str = Field(
        "cube",
        description="Тип фигуры: cube (куб), sphere (сфера), cylinder (цилиндр)"
    ),
    size: float = Field(
        10.0,
        description="Размер фигуры в миллиметрах (положительное число)"
    ),
    x: float = Field(
        0.0,
        description="X-координата центра фигуры (в мм)"
    ),
    y: float = Field(
        0.0,
        description="Y-координата центра фигуры (в мм)"
    ),
    z: float = Field(
        0.0,
        description="Z-координата центра фигуры (в мм)"
    ),
    ctx: Context = None
) -> ToolResult:
    """Обертка для MCP-инструмента."""
    return await _create_shape_impl(shape_type, size, x, y, z, ctx)