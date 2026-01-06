# main.py
from fastapi import FastAPI, HTTPException
import httpx
import uvicorn
from common_logic import core
import asyncio
from mcp_instance import mcp
import threading
import math
from dotenv import load_dotenv
import os
import json

load_dotenv()


# Импорт всех инструментов для регистрации MCP
from tools import tool_create_cube, tool_create_cylinder, tool_create_shapes, tool_create_sphere, tool_documents, tool_status, tool_open_document, tool_save_document, tool_close_document, tool_create_complex_shape, tool_test_shape

app = FastAPI(title="CAD API Gateway")

@app.get("/api/mcp/status")
async def get_mcp_status():
    """Получить статус MCP сервера."""
    return {
        "status": "running",
        "tools": ["get_mcp_status", "get_documents", "create_shape", "create_cube", "create_sphere", "create_cylinder", "open_document", "save_document", "close_document", "create_complex_shape", "create_test_shape"],
        "description": "CAD MCP Server for FreeCAD operations"
    }

@app.get("/api/cad/documents")
async def get_documents():
    """Получить документы из FreeCAD."""
    result = await core.get_onshape_documents()
    return {"result": result}

@app.get("/api/cad/create-shape")
async def create_shape(
    shape_type: str = "cube", 
    size: float = 10.0,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0
):
    """
    Создать фигуру в FreeCAD в указанных координатах.
    
    Parameters:
    - shape_type: Тип фигуры (cube, sphere, cylinder)
    - size: Размер фигуры в мм
    - x, y, z: Координаты центра фигуры (в мм)
    """
    # Валидация параметров
    if size <= 0:
        raise HTTPException(
            status_code=400, 
            detail="Размер должен быть положительным числом"
        )
    
    valid_shapes = ["cube", "sphere", "cylinder"]
    if shape_type.lower() not in valid_shapes:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип фигуры. Доступно: {', '.join(valid_shapes)}"
        )
    
    # Вызов метода из common_logic с координатами
    result = await core.create_simple_shape(
        shape_type.lower(), 
        size,
        x,
        y,
        z
    )
    
    return {
        "result": result,
        "parameters": {
            "shape_type": shape_type,
            "size": size,
            "x": x,
            "y": y,
            "z": z
        }
    }

@app.get("/api/cad/create-complex-shape")
async def create_complex_shape(
    shape_type: str,
    num_points: int = None,
    inner_radius: float = None,
    outer_radius: float = None,
    height: float = None,
    teeth: int = None,
    module: float = None,
    major_radius: float = None,
    minor_radius: float = None
):
    """
    Создать сложную 3D-фигуру в CAD системе.
    
    Поддерживаемые типы фигур:
    - star (звезда): требуется num_points, inner_radius, outer_radius, height
    - gear (шестеренка): требуется teeth, module, outer_radius, height
    - torus (тор): требуется major_radius, minor_radius
    """
    # Валидация типа фигуры
    valid_shapes = ["star", "gear", "torus"]
    if shape_type.lower() not in valid_shapes:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип фигуры. Доступно: {', '.join(valid_shapes)}"
        )
    
    # Проверяем подключение к FreeCAD
    if not core.freecad:
        result = core.connect()
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка подключения к FreeCAD: {result.get('error', 'Неизвестная ошибка')}"
            )
    
    # Проверяем наличие открытого документа
    if not core.current_doc:
        raise HTTPException(
            status_code=400,
            detail="Нет открытого документа. Сначала откройте документ с помощью /api/cad/open-document"
        )
    
    try:
        doc = core.current_doc
        
        if shape_type.lower() == "torus":
            # Проверка параметров
            if major_radius is None or minor_radius is None:
                raise HTTPException(
                    status_code=400,
                    detail="Для тора требуются major_radius и minor_radius"
                )
            if major_radius <= 0 or minor_radius <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Радиусы должны быть положительными"
                )
            if minor_radius >= major_radius:
                raise HTTPException(
                    status_code=400,
                    detail="minor_radius должен быть меньше major_radius"
                )
            
            # Создание тора
            torus = core.part.makeTorus(major_radius, minor_radius)
            obj = doc.addObject("Part::Feature", f"Torus_{major_radius}x{minor_radius}")
            obj.Shape = torus
            doc.recompute()
            
            result_message = f"Тор создан с большим радиусом {major_radius} мм и малым радиусом {minor_radius} мм"
            
        elif shape_type.lower() == "star":
            if num_points is None or inner_radius is None or outer_radius is None or height is None:
                raise HTTPException(
                    status_code=400,
                    detail="Для звезды требуются num_points, inner_radius, outer_radius, height"
                )
            if num_points < 5 or num_points % 2 == 0:
                raise HTTPException(
                    status_code=400,
                    detail="num_points для звезды должно быть нечетным числом >=5"
                )
            if inner_radius <= 0 or outer_radius <= 0 or height <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Радиусы и высота должны быть положительными"
                )
            if inner_radius >= outer_radius:
                raise HTTPException(
                    status_code=400,
                    detail="inner_radius должен быть меньше outer_radius"
                )
            
            # Создание звезды
            import math
            points = []
            for i in range(num_points * 2):
                angle = i * math.pi / num_points
                radius = inner_radius if i % 2 == 0 else outer_radius
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                points.append(core.freecad.Vector(x, y, 0))
            
            # Замыкаем контур
            points.append(points[0])
            
            # Создаем полигон
            wire = core.part.makePolygon(points)
            face = core.part.Face(wire)
            
            extruded = face.extrude(core.freecad.Vector(0, 0, height))
            obj = doc.addObject("Part::Feature", f"Star_{num_points}pts")
            obj.Shape = extruded
            doc.recompute()
            
            result_message = f"Звезда создана с {num_points} лучами, высотой {height} мм"
            
        elif shape_type.lower() == "gear":
            if teeth is None or module is None or outer_radius is None or height is None:
                raise HTTPException(
                    status_code=400,
                    detail="Для шестеренки требуются teeth, module, outer_radius, height"
                )
            if teeth < 3:
                raise HTTPException(
                    status_code=400,
                    detail="teeth должно быть >=3"
                )
            if module <= 0 or outer_radius <= 0 or height <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="module, outer_radius и height должны быть положительными"
                )
            # В реальном проекте нужно использовать более сложную геометрию
            cylinder = core.part.makeCylinder(outer_radius, height)
            obj = doc.addObject("Part::Feature", f"Gear_{teeth}teeth")
            obj.Shape = cylinder
            doc.recompute()
            
            result_message = f"Упрощенная шестеренка создана с {teeth} зубьями, высотой {height} мм. Для точной геометрии используйте специализированные библиотеки."
        
        return {
            "result": result_message,
            "parameters": {
                "shape_type": shape_type,
                "num_points": num_points,
                "inner_radius": inner_radius,
                "outer_radius": outer_radius,
                "height": height,
                "teeth": teeth,
                "module": module,
                "major_radius": major_radius,
                "minor_radius": minor_radius
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка создания сложной фигуры: {str(e)}"
        )

@app.get("/api/cad/open-document")
async def open_document(file_path: str):
    if not file_path:
        raise HTTPException(status_code=400, detail="Путь к файлу обязателен")
    result = await core.open_document(file_path)
    return {"result": result}

@app.get("/api/cad/save-document")
async def save_document(file_path: str = None):
    result = await core.save_document(file_path)
    return {"result": result}

@app.get("/api/cad/close-document")
async def close_document():
    result = await core.close_document()
    return {"result": result}

@app.get("/api/cad/create-test-shape")
async def create_test_shape_endpoint(
    shape_type: str = "cube",
    size: float = 10.0,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
    file_name: str = None
):
    """
    Создать тестовую 3D-фигуру и сохранить в файл.
    
    Parameters:
    - shape_type: Тип фигуры (cube, sphere, cylinder)
    - size: Размер фигуры в мм
    - x, y, z: Координаты центра фигуры (в мм)
    - file_name: Имя файла (если None, будет сгенерировано автоматически)
    """
    # Валидация параметров
    if size <= 0:
        raise HTTPException(
            status_code=400, 
            detail="Размер должен быть положительным числом"
        )
    valid_shapes = ["cube", "sphere", "cylinder"]
    if shape_type.lower() not in valid_shapes:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип фигуры. Доступно: {', '.join(valid_shapes)}"
        )
    if not file_name:
        import uuid
        file_name = f"test_{shape_type}_{size}mm_{uuid.uuid4().hex[:8]}.FCStd"
    elif not file_name.lower().endswith('.fcstd'):
        raise HTTPException(
            status_code=400,
            detail="Файл должен иметь расширение .FCStd"
        )
    
    try:
        open_result = await core.open_document(file_name)
        create_result = await core.create_simple_shape(
            shape_type.lower(), 
            size,
            x,
            y,
            z
        )
        save_result = await core.save_document(file_name)
        close_result = await core.close_document()
        return {
            "success": True,
            "result": "Тестовая фигура создана и сохранена успешно",
            "details": {
                "file": file_name,
                "shape_type": shape_type,
                "size": size,
                "coordinates": {"x": x, "y": y, "z": z},
                "open_result": open_result,
                "create_result": create_result,
                "save_result": save_result,
                "close_result": close_result
            },
            "message": (
                f"✅ Файл создан: {file_name}\n"
                f"📐 Тип фигуры: {shape_type}\n"
                f"📏 Размер: {size} мм\n"
                f"📍 Координаты: ({x}, {y}, {z}) мм\n"
                f"📄 Открытие документа: {open_result}\n"
                f"🎯 Создание фигуры: {create_result}\n"
                f"💾 Сохранение: {save_result}\n"
                f"🚪 Закрытие: {close_result}"
            )
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании тестовой фигуры: {str(e)}"
        )

@app.get("/reward_url")
async def

@app.get("/")
async def root():
    return {
        "message": "FreeCAD API Gateway",
        "endpoints": {
            "documents": "/api/cad/documents",
            "create_shape": "/api/cad/create-shape?shape_type=cube&size=10",
            "create_cube_15mm": "/api/cad/create-shape?shape_type=cube&size=15",
            "create_sphere": "/api/cad/create-shape?shape_type=sphere&size=20",
            "create_cylinder": "/api/cad/create-shape?shape_type=cylinder&size=10",
            "create_complex_shape": "/api/cad/create-complex-shape?shape_type=star&num_points=5&inner_radius=10&outer_radius=20&height=5",
            "open_document": "/api/cad/open-document?file_path=test.FCStd",
            "save_document": "/api/cad/save-document?file_path=test.FCStd",
            "close_document": "/api/cad/close-document",
            "create_test_shape": "/api/cad/create-test-shape?shape_type=cube&size=10&file_name=my_test.FCStd",
            "create_test_cube": "/api/cad/create-test-shape?shape_type=cube&size=15",
            "create_test_sphere": "/api/cad/create-test-shape?shape_type=sphere&size=20",
            "create_test_cylinder": "/api/cad/create-test-shape?shape_type=cylinder&size=10&size=30",
            "agent_query": "/api/agent/query (POST)",
            "agent_status": "/api/agent/status",
            "agent_help": "/api/agent/help"
        },
        "notes": "Размер указывается в миллиметрах. Для test_shape можно указать имя файла или оно будет сгенерировано автоматически"
    }

# УДАЛЕНО: старый эндпоинт /api/agent/query (перенесен в agent_router)

if __name__ == "__main__":
    # Запуск MCP сервера в отдельном потоке
    mcp_thread = threading.Thread(target=lambda: mcp.run(transport="streamable-http", host="0.0.0.0", port=8000), daemon=True)
    mcp_thread.start()

    print("=" * 60)
    print("FreeCAD FastAPI Server запущен")
    print("MCP Server запущен на порту 8000")
    print("AI Agent (LangChain) инициализирован")
    print("=" * 60)
    print("Swagger UI: http://localhost:8001/docs")
    print("Тест документов: http://localhost:8001/api/cad/documents")
    print("Создать куб 15мм: http://localhost:8001/api/cad/create-shape?shape_type=cube&size=15")
    print("Создать тестовый куб: http://localhost:8001/api/cad/create-test-shape?shape_type=cube&size=15")
    print("AI Agent запрос: POST http://localhost:8001/api/agent/query")
    print("AI Agent статус: GET http://localhost:8001/api/agent/status")
    print("Пример запроса к агенту:")
    print('curl -X POST http://localhost:8001/api/agent/query -H "Content-Type: application/json" -d \'{"query": "Создай куб размером 20мм"}\'')
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8001)