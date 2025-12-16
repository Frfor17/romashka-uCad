# tool_status.py
"""Инструмент для получения статуса MCP сервера."""

from fastmcp import Context
from pydantic import Field
from mcp.types import TextContent
from mcp_instance import mcp
from .utils import ToolResult

@mcp.tool(
    name="get_mcp_status",
    description="""
    Получить статус MCP сервера и доступные инструменты.
    """
)
async def get_mcp_status(
    ctx: Context = None
) -> ToolResult:
    """
    Получить статус MCP сервера и доступные инструменты.
    
    Args:
        ctx: Контекст для логирования
    
    Returns:
        ToolResult: Результат выполнения инструмента
    """
    import httpx
    
    if ctx:
        await ctx.info("📊 Запрашиваем статус MCP сервера")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("http://localhost:8001/api/mcp/status")
            response.raise_for_status()
            data = response.json()
            
            tools_list = "\n".join([f"  - {tool}" for tool in data.get("tools", [])])
            result_text = (f"📊 Статус MCP сервера:\n"
                          f"Состояние: {data.get('status', 'unknown')}\n"
                          f"Доступные инструменты:\n{tools_list}")
            
            if ctx:
                await ctx.info("✅ Статус получен успешно")
            
            return ToolResult(
                content=[TextContent(type="text", text=result_text)],
                structured_content=data,
                meta={"status": "success"}
            )
            
    except Exception as e:
        error_text = f"Не удалось получить статус: {str(e)}\nУбедитесь, что FastAPI сервер запущен на http://localhost:8001"
        if ctx:
            await ctx.error(f"❌ {error_text}")
        
        return ToolResult(
            content=[TextContent(type="text", text=error_text)],
            structured_content={"error": str(e)},
            meta={"status": "error"}
        )