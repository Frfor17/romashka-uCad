"""Инструмент для создания сложной 3D-фигуры в CAD системе."""

import httpx
from fastmcp import Context
from pydantic import Field
from mcp.types import TextContent
from mcp_instance import mcp
from .utils import ToolResult

async def _create_complex_shape_impl(
    shape_type: str,
    num_points: int = None,
    inner_radius: float = None,
    outer_radius: float = None,
    height: float = None,
    teeth: int = None,
    module: float = None,
    major_radius: float = None,
    minor_radius: float = None,
    ctx: Context = None
) -> ToolResult:
    """
    Внутренняя реализация создания сложной 3D-фигуры.
    
    Args:
        shape_type: Тип фигуры: star (звезда), gear (шестеренка), torus (тор)
        num_points: Для star: количество лучей (нечетное число >=5)
        inner_radius: Для star: внутренний радиус (>0)
        outer_radius: Для star/gear: внешний радиус (> inner_radius для star, >0 для gear)
        height: Высота экструзии для star/gear или толщина для torus (>0)
        teeth: Для gear: количество зубьев (>=3)
        module: Для gear: модуль (>0)
        major_radius: Для torus: большой радиус (>0)
        minor_radius: Для torus: малый радиус (>0, < major_radius)
        ctx: Контекст для логирования
    
    Returns:
        ToolResult: Результат выполнения инструмента
    
    Валидация: Проверяет тип фигуры и требуемые параметры.
    Обработка ошибок: Возвращает ToolResult с ошибкой при валидации или HTTP ошибке.
    Краевые случаи: Обрабатывает отсутствие параметров, отрицательные значения, неверные типы.
    """
    if ctx:
        await ctx.info(f"🚀 Начинаем создание сложной фигуры типа: {shape_type}")
    
    # Валидация типа фигуры
    valid_shapes = ["star", "gear", "torus"]
    if shape_type.lower() not in valid_shapes:
        error_msg = f"Ошибка: неподдерживаемый тип фигуры. Используйте: {', '.join(valid_shapes)}"
        if ctx:
            await ctx.error(f"❌ {error_msg}")
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)],
            structured_content={"error": "invalid_shape_type"},
            meta={"status": "validation_error"}
        )
    
    shape_type = shape_type.lower()
    params = {"shape_type": shape_type}
    required_params = []
    
    # Валидация по типу
    if shape_type == "star":
        required_params = [num_points, inner_radius, outer_radius, height]
        if any(p is None for p in required_params):
            error_msg = "Ошибка: для 'star' требуются num_points, inner_radius, outer_radius, height"
            if ctx:
                await ctx.error(f"❌ {error_msg}")
            return ToolResult(
                content=[TextContent(type="text", text=error_msg)],
                structured_content={"error": "missing_params"},
                meta={"status": "validation_error"}
            )
        if num_points < 5 or num_points % 2 == 0:
            error_msg = "Ошибка: num_points для star должно быть нечетным числом >=5"
            if ctx:
                await ctx.error(f"❌ {error_msg}")
            return ToolResult(
                content=[TextContent(type="text", text=error_msg)],
                structured_content={"error": "invalid_num_points"},
                meta={"status": "validation_error"}
            )
        if inner_radius <= 0 or outer_radius <= 0 or height <= 0:
            error_msg = "Ошибка: радиусы и высота должны быть положительными"
            if ctx:
                await ctx.error(f"❌ {error_msg}")
            return ToolResult(
                content=[TextContent(type="text", text=error_msg)],
                structured_content={"error": "invalid_positive_value"},
                meta={"status": "validation_error"}
            )
        if inner_radius >= outer_radius:
            error_msg = "Ошибка: inner_radius должен быть меньше outer_radius"
            if ctx:
                await ctx.error(f"❌ {error_msg}")
            return ToolResult(
                content=[TextContent(type="text", text=error_msg)],
                structured_content={"error": "invalid_radius_order"},
                meta={"status": "validation_error"}
            )
        params.update({
            "num_points": num_points,
            "inner_radius": inner_radius,
            "outer_radius": outer_radius,
            "height": height
        })
    
    elif shape_type == "gear":
        required_params = [teeth, module, outer_radius, height]
        if any(p is None for p in required_params):
            error_msg = "Ошибка: для 'gear' требуются teeth, module, outer_radius, height"
            if ctx:
                await ctx.error(f"❌ {error_msg}")
            return ToolResult(
                content=[TextContent(type="text", text=error_msg)],
                structured_content={"error": "missing_params"},
                meta={"status": "validation_error"}
            )
        if teeth < 3:
            error_msg = "Ошибка: teeth для gear должно быть >=3"
            if ctx:
                await ctx.error(f"❌ {error_msg}")
            return ToolResult(
                content=[TextContent(type="text", text=error_msg)],
                structured_content={"error": "invalid_teeth"},
                meta={"status": "validation_error"}
            )
        if module <= 0 or outer_radius <= 0 or height <= 0:
            error_msg = "Ошибка: module, outer_radius и height должны быть положительными"
            if ctx:
                await ctx.error(f"❌ {error_msg}")
            return ToolResult(
                content=[TextContent(type="text", text=error_msg)],
                structured_content={"error": "invalid_positive_value"},
                meta={"status": "validation_error"}
            )
        params.update({
            "teeth": teeth,
            "module": module,
            "outer_radius": outer_radius,
            "height": height
        })
    
    elif shape_type == "torus":
        required_params = [major_radius, minor_radius]
        if any(p is None for p in required_params):
            error_msg = "Ошибка: для 'torus' требуются major_radius, minor_radius"
            if ctx:
                await ctx.error(f"❌ {error_msg}")
            return ToolResult(
                content=[TextContent(type="text", text=error_msg)],
                structured_content={"error": "missing_params"},
                meta={"status": "validation_error"}
            )
        if major_radius <= 0 or minor_radius <= 0:
            error_msg = "Ошибка: радиусы должны быть положительными"
            if ctx:
                await ctx.error(f"❌ {error_msg}")
            return ToolResult(
                content=[TextContent(type="text", text=error_msg)],
                structured_content={"error": "invalid_positive_value"},
                meta={"status": "validation_error"}
            )
        if minor_radius >= major_radius:
            error_msg = "Ошибка: minor_radius должен быть меньше major_radius"
            if ctx:
                await ctx.error(f"❌ {error_msg}")
            return ToolResult(
                content=[TextContent(type="text", text=error_msg)],
                structured_content={"error": "invalid_radius_order"},
                meta={"status": "validation_error"}
            )
        params.update({
            "major_radius": major_radius,
            "minor_radius": minor_radius
        })
    
    if ctx:
        await ctx.info(f"🔧 Параметры: {params}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "http://localhost:8001/api/cad/create-complex-shape",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if ctx:
                await ctx.info("✅ Сложная фигура создана успешно")
            
            result_text = (
                f"✅ Сложная фигура создана успешно!\n"
                f"📐 Тип: {data.get('parameters', {}).get('shape_type', 'неизвестно')}\n"
                f"🎯 Результат: {data.get('result', 'успешно')}"
            )
            
            return ToolResult(
                content=[TextContent(type="text", text=result_text)],
                structured_content=data,
                meta={
                    "shape_type": shape_type,
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
        error_msg = f"Ошибка при создании сложной фигуры: {str(e)}"
        if ctx:
            await ctx.error(f"❌ {error_msg}")
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)],
            structured_content={"error": str(e)},
            meta={"status": "error"}
        )

@mcp.tool(
    name="create_complex_shape",
    description="""
    Создать сложную 3D-фигуру в CAD системе.
    Поддерживаемые типы фигур: star (звезда), gear (шестеренка), torus (тор).
    Для star: укажите num_points, inner_radius, outer_radius, height.
    Для gear: укажите teeth, module, outer_radius, height.
    Для torus: укажите major_radius, minor_radius.
    Все размеры в миллиметрах как положительные числа.
    """
)
async def create_complex_shape(
    shape_type: str = Field(
        ...,
        description="Тип фигуры: star (звезда), gear (шестеренка), torus (тор)"
    ),
    num_points: int = Field(
        None,
        description="Для star: количество лучей (нечетное число >=5)"
    ),
    inner_radius: float = Field(
        None,
        description="Для star: внутренний радиус в мм (>0)"
    ),
    outer_radius: float = Field(
        None,
        description="Для star/gear: внешний радиус в мм (>0)"
    ),
    height: float = Field(
        None,
        description="Высота экструзии для star/gear в мм (>0)"
    ),
    teeth: int = Field(
        None,
        description="Для gear: количество зубьев (>=3)"
    ),
    module: float = Field(
        None,
        description="Для gear: модуль в мм (>0)"
    ),
    major_radius: float = Field(
        None,
        description="Для torus: большой радиус в мм (>0)"
    ),
    minor_radius: float = Field(
        None,
        description="Для torus: малый радиус в мм (>0)"
    ),
    ctx: Context = None
) -> ToolResult:
    """Обертка для MCP-инструмента создания сложной фигуры."""
    return await _create_complex_shape_impl(
        shape_type, num_points, inner_radius, outer_radius, height,
        teeth, module, major_radius, minor_radius, ctx
    )