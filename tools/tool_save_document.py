import httpx
from fastmcp import Context
from pydantic import Field
from mcp.types import TextContent
from mcp_instance import mcp
from .utils import ToolResult

@mcp.tool(
    name="save_document",
    description="""
    Сохранить текущий открытый документ FreeCAD.
    Если указан новый путь, сохраняет как новый файл.
    Требует предварительного открытия документа через open_document.
    """
)
async def save_document(
    file_path: str = Field(
        None,
        description="Опциональный новый путь для сохранения (save as). Если не указан, сохраняет в текущий файл."
    ),
    ctx: Context = None
) -> ToolResult:
    """
    Сохранить текущий открытый документ FreeCAD.
    
    Args:
        file_path: Опциональный новый путь для сохранения.
        ctx: Контекст для логирования
    
    Returns:
        ToolResult: Результат выполнения инструмента
    
    Валидация: Нет строгой, но проверяет наличие открытого документа на стороне core.
    Обработка ошибок: Возвращает ошибку если нет открытого документа или ошибка сохранения.
    Краевые случаи: Если file_path не указан, сохраняет в оригинальный; если нет документа - ошибка.
    """
    if ctx:
        await ctx.info(f"💾 Сохраняем документ{' как ' + file_path if file_path else ''}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {}
            if file_path:
                params["file_path"] = file_path
            response = await client.get(
                "http://localhost:8001/api/cad/save-document",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if ctx:
                await ctx.info("✅ Документ сохранен успешно")
            
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
        error_msg = f"Ошибка при сохранении документа: {str(e)}"
        if ctx:
            await ctx.error(f"❌ {error_msg}")
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)],
            structured_content={"error": str(e)},
            meta={"status": "error"}
        )