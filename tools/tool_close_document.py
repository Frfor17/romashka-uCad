import httpx
from fastmcp import Context
from pydantic import Field
from mcp.types import TextContent
from mcp_instance import mcp
from .utils import ToolResult

@mcp.tool(
    name="close_document",
    description="""
    Закрыть текущий открытый документ FreeCAD.
    Требует предварительного открытия документа.
    Рекомендуется сохранить перед закрытием.
    """
)
async def close_document(
    ctx: Context = None
) -> ToolResult:
    """
    Закрыть текущий открытый документ FreeCAD.
    
    Args:
        ctx: Контекст для логирования
    
    Returns:
        ToolResult: Результат выполнения инструмента
    
    Валидация: Нет параметров.
    Обработка ошибок: Возвращает ошибку если нет открытого документа или ошибка закрытия.
    Краевые случаи: Если нет документа - возвращает сообщение.
    """
    if ctx:
        await ctx.info("🚪 Закрываем документ")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("http://localhost:8001/api/cad/close-document")
            response.raise_for_status()
            data = response.json()
            
            if ctx:
                await ctx.info("✅ Документ закрыт успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=data.get("result", "успешно"))],
                structured_content=data,
                meta={"status": "success"}
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
        error_msg = f"Ошибка при закрытии документа: {str(e)}"
        if ctx:
            await ctx.error(f"❌ {error_msg}")
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)],
            structured_content={"error": str(e)},
            meta={"status": "error"}
        )