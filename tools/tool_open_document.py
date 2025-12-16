"""Инструмент для открытия документа в CAD системе."""

import httpx
from fastmcp import Context
from pydantic import Field
from mcp.types import TextContent
from mcp_instance import mcp
from .utils import ToolResult

@mcp.tool(
    name="open_document",
    description="""
    Открыть существующий файл FreeCAD в CAD системе или создать новый, если файл не существует.
    Закрывает предыдущий открытый документ, если он был.
    После открытия можно редактировать документ другими инструментами (create_cube и т.д.).
    Путь должен быть абсолютным или относительным, файл должен быть в формате .FCStd.
    Если файл не существует, создается новый пустой документ и сохраняется по указанному пути.
    """
)
async def open_document(
    file_path: str = Field(
        ...,
        description="Путь к файлу FreeCAD (.FCStd). Если не существует, будет создан новый."
    ),
    ctx: Context = None
) -> ToolResult:
    """
    Открыть существующий файл FreeCAD в CAD системе или создать новый если не существует.
    
    Args:
        file_path: Путь к файлу FreeCAD (.FCStd). Обязательный параметр.
        ctx: Контекст для логирования
    
    Returns:
        ToolResult: Результат выполнения инструмента
    
    Валидация: Проверяет наличие пути.
    Обработка ошибок: Возвращает ошибку если путь не указан, или ошибка открытия/создания.
    Краевые случаи: Если документ уже открыт, закрывает его перед открытием/созданием нового.
    Если файл не существует, создает новый.
    """
    if not file_path:
        error_msg = "Ошибка: путь к файлу обязателен"
        if ctx:
            await ctx.error(f"❌ {error_msg}")
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)],
            structured_content={"error": "missing_file_path"},
            meta={"status": "validation_error"}
        )
    
    if ctx:
        await ctx.info(f"📂 Открываем или создаем документ: {file_path}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {"file_path": file_path}
            response = await client.get(
                "http://localhost:8001/api/cad/open-document",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if ctx:
                await ctx.info("✅ Документ открыт или создан успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=data.get("result", "успешно"))],
                structured_content=data,
                meta={"status": "success", "file_path": file_path}
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
        error_msg = f"Ошибка при открытии/создании документа: {str(e)}"
        if ctx:
            await ctx.error(f"❌ {error_msg}")
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)],
            structured_content={"error": str(e)},
            meta={"status": "error"}
        )