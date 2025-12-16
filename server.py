# server.py (замените на это)
from mcp_instance import mcp
from tools import (
    tool_create_cube, tool_create_cylinder, tool_create_shapes,
    tool_create_sphere, tool_documents, tool_status, tool_open_document,
    tool_save_document, tool_close_document, tool_create_complex_shape,
    tool_test_shape
)

if __name__ == "__main__":
    # Запуск сервера с HTTP транспортом
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)