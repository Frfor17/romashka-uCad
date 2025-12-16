"""Тестовый инструмент для создания 3D-фигуры и сохранения в файл."""

import httpx
import tempfile
import os
from fastmcp import Context
from pydantic import Field
from mcp.types import TextContent
from mcp_instance import mcp
from .utils import ToolResult, validate_shape_type, validate_size

async def _create_test_shape_impl(
    shape_type: str = "cube",
    size: float = 10.0,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
    file_name: str = None,
    ctx: Context = None
) -> ToolResult:
    """
    Создать 3D-фигуру и сохранить в файл.
    
    Args:
        shape_type: Тип фигуры: cube (куб), sphere (сфера), cylinder (цилиндр)
        size: Размер фигуры в миллиметрах
        x, y, z: Координаты центра фигуры
        file_name: Имя файла (если None, будет сгенерировано автоматически)
        ctx: Контекст для логирования
    
    Returns:
        ToolResult: Результат выполнения
    """
    if ctx:
        await ctx.info(f"🚀 Начинаем создание тестовой фигуры типа: {shape_type}")
    
    # Валидация типа фигуры
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
    
    # Валидация размера
    if not validate_size(size):
        error_msg = "Ошибка: размер должен быть положительным числом"
        if ctx:
            await ctx.error(f"❌ {error_msg}")
        
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)],
            structured_content={"error": "invalid_size"},
            meta={"status": "validation_error"}
        )
    
    # Генерация имени файла, если не указано
    if not file_name:
        import uuid
        file_name = f"test_{shape_type}_{size}mm_{uuid.uuid4().hex[:8]}.FCStd"
    
    if ctx:
        await ctx.info(f"📝 Будет создан файл: {file_name}")
    
    try:
        # 1. Открываем/создаем документ
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Открываем или создаем документ
            open_response = await client.get(
                "http://localhost:8001/api/cad/open-document",
                params={"file_path": file_name}
            )
            open_response.raise_for_status()
            open_result = open_response.json()
            
            if ctx:
                await ctx.info(f"📄 Документ: {open_result.get('result', 'открыт/создан')}")
            
            # 2. Создаем фигуру
            params = {
                "shape_type": shape_type.lower(), 
                "size": size,
                "x": x,
                "y": y,
                "z": z
            }
            create_response = await client.get(
                "http://localhost:8001/api/cad/create-shape",
                params=params
            )
            create_response.raise_for_status()
            create_data = create_response.json()
            
            # 3. Сохраняем документ
            save_response = await client.get(
                "http://localhost:8001/api/cad/save-document",
                params={"file_path": file_name}
            )
            save_response.raise_for_status()
            save_result = save_response.json()
            
            # 4. Закрываем документ
            close_response = await client.get(
                "http://localhost:8001/api/cad/close-document"
            )
            close_response.raise_for_status()
            close_result = close_response.json()
            
            if ctx:
                await ctx.info("✅ Тестовая фигура создана и сохранена успешно")
            
            # Формируем итоговое сообщение
            result_text = (
                f"✅ Тестовая фигура создана и сохранена!\n"
                f"📁 Файл: {file_name}\n"
                f"📐 Тип фигуры: {shape_type}\n"
                f"📏 Размер: {size} мм\n"
                f"📍 Координаты: ({x}, {y}, {z}) мм\n"
                f"📄 Результат открытия: {open_result.get('result', 'успешно')}\n"
                f"🎯 Результат создания: {create_data.get('result', 'успешно')}\n"
                f"💾 Результат сохранения: {save_result.get('result', 'успешно')}\n"
                f"🚪 Результат закрытия: {close_result.get('result', 'успешно')}"
            )
            
            return ToolResult(
                content=[TextContent(type="text", text=result_text)],
                structured_content={
                    "file_name": file_name,
                    "shape_data": create_data,
                    "open_result": open_result,
                    "save_result": save_result,
                    "close_result": close_result
                },
                meta={
                    "shape_type": shape_type,
                    "size": size,
                    "x": x,
                    "y": y,
                    "z": z,
                    "file_name": file_name,
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
        error_msg = f"Ошибка при создании тестовой фигуры: {str(e)}"
        if ctx:
            await ctx.error(f"❌ {error_msg}")
        
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)],
            structured_content={"error": str(e)},
            meta={"status": "error"}
        )

@mcp.tool(
    name="create_test_shape",
    description="""
    Создать тестовую 3D-фигуру в CAD системе и сохранить в файл.
    Поддерживаемые типы фигур: cube (куб), sphere (сфера), cylinder (цилиндр).
    Размер указывается в миллиметрах как положительное число.
    Координаты x, y, z указывают положение центра фигуры.
    Если имя файла не указано, будет сгенерировано автоматически.
    Файл создается с расширением .FCStd в текущей директории.
    """
)
async def create_test_shape(
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
    file_name: str = Field(
        None,
        description="Имя файла для сохранения (если None, будет сгенерировано автоматически)"
    ),
    ctx: Context = None
) -> ToolResult:
    """Создать тестовую фигуру и сохранить в файл."""
    return await _create_test_shape_impl(shape_type, size, x, y, z, file_name, ctx)
