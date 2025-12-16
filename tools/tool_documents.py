# tool_documents.py
"""Инструмент для работы с документами CAD системы."""

from fastmcp import Context
from pydantic import Field
from mcp.types import TextContent
from mcp_instance import mcp
from .utils import ToolResult

@mcp.tool(
    name="get_documents",
    description="""
    Получить список CAD документов из системы.
    Возвращает список документов в формате JSON.
    """
)
async def get_documents(
    ctx: Context = None
) -> ToolResult:
    """
    Получить список CAD документов из системы.
    
    Args:
        ctx: Контекст для логирования
    
    Returns:
        ToolResult: Результат выполнения инструмента
    """
    import httpx
    
    if ctx:
        await ctx.info("🔍 Получаем список документов из CAD системы")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("http://localhost:8001/api/cad/documents")
            response.raise_for_status()
            data = response.json()
            
            documents = data.get('result', [])
            formatted_result = f"📋 Найдено документов: {len(documents)}\n\n"
            
            for doc in documents:
                formatted_result += f"• {doc}\n"
            
            if ctx:
                await ctx.info(f"✅ Получено {len(documents)} документов")
            
            return ToolResult(
                content=[TextContent(type="text", text=formatted_result)],
                structured_content={"documents": documents},
                meta={"count": len(documents)}
            )
            
    except Exception as e:
        error_msg = f"Ошибка при получении документов: {str(e)}"
        if ctx:
            await ctx.error(f"❌ {error_msg}")
        
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)],
            structured_content={"error": str(e)},
            meta={"status": "error"}
        )