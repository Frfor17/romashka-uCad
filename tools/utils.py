"""
Общие утилиты для CAD MCP сервера.
"""

from mcp.types import TextContent
from typing import List, Dict, Any, Optional


class ToolResult:
    """
    Результат выполнения инструмента.
    
    Attributes:
        content: Текстовое содержимое для отображения пользователю
        structured_content: Структурированные данные для дальнейшей обработки
        meta: Метаданные выполнения
    """
    
    def __init__(
        self,
        content: List[TextContent],
        structured_content: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.structured_content = structured_content or {}
        self.meta = meta or {}
    
    def __str__(self) -> str:
        """Преобразует ToolResult в строку для отображения."""
        if not self.content:
            return ""
        
        # Извлекаем текстовое содержимое из TextContent
        texts = []
        for item in self.content:
            if hasattr(item, 'text'):
                texts.append(item.text)
            elif isinstance(item, dict) and 'text' in item:
                texts.append(item['text'])
            else:
                texts.append(str(item))
        
        return "\n".join(texts)
    
    def __repr__(self) -> str:
        return f"ToolResult(content={self.content})"


def validate_shape_type(shape_type: str) -> bool:
    """
    Проверяет, является ли тип фигуры допустимым.
    
    Returns:
        bool: True если тип допустим, иначе False
    """
    valid_shapes = ["cube", "sphere", "cylinder"]
    return shape_type.lower() in valid_shapes


def validate_size(size: float) -> bool:
    """
    Проверяет, является ли размер допустимым.
    
    Returns:
        bool: True если размер положительный, иначе False
    """
    return size > 0