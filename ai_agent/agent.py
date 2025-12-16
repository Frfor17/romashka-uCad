# agent.py
import os
import json
import time
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_classic.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_classic.memory import ConversationBufferMemory
from langchain.tools import tool
import httpx

load_dotenv()

# Конфигурация
MODEL = os.getenv("SBER_MODEL", "Qwen/Qwen3-Next-80B-A3B-Instruct")

# Настройка логирования
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CADAgent")

# ============ ИНИЦИАЛИЗАЦИЯ LLM С SBERCLOUD ============
def get_llm():
    """Инициализация LLM для SberCloud через LangChain"""
    
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("API_KEY не найден в .env файле")
    
    return ChatOpenAI(
        base_url="https://foundation-models.api.cloud.ru/v1",
        api_key=api_key,
        model=MODEL,
        temperature=0.3,
        max_tokens=2000,
        timeout=60.0,
        max_retries=2,
        presence_penalty=0,
        frequency_penalty=0.1,
        model_kwargs={}
    )

# ============ ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ СОЗДАНИЯ ФИГУР ============
def _create_shape_http(shape_type: str, size: float, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> str:
    """Внутренняя функция для создания фигуры через FastAPI."""
    try:
        params = {
            "shape_type": shape_type,
            "size": size,
            "x": x,
            "y": y,
            "z": z
        }
        response = httpx.get(
            "http://localhost:8001/api/cad/create-shape",
            params=params,
            timeout=30.0
        )
        response.raise_for_status()
        return json.dumps(response.json(), ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"Ошибка создания {shape_type}: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

# ============ ИНСТРУМЕНТЫ LANGCHAIN ============
@tool
def get_health() -> str:
    """Проверить здоровье системы через FastAPI."""
    logger.info("Проверка здоровья системы через FastAPI")
    
    try:
        # Проверяем FastAPI
        fastapi_resp = httpx.get("http://localhost:8001/", timeout=5.0)
        fastapi_ok = fastapi_resp.status_code == 200
        
        # Проверяем MCP через FastAPI эндпоинт
        mcp_resp = httpx.get("http://localhost:8001/api/mcp/status", timeout=5.0)
        mcp_ok = mcp_resp.status_code == 200
        
        # Проверяем CAD через FastAPI
        cad_resp = httpx.get("http://localhost:8001/api/cad/documents", timeout=5.0)
        cad_ok = cad_resp.status_code == 200
        
        result = {
            "fastapi_server": fastapi_ok,
            "mcp_server": mcp_ok,
            "cad_system": cad_ok,
            "agent": True,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"Ошибка проверки здоровья: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

@tool
def open_document(file_path: str) -> str:
    """Открыть или создать документ через FastAPI."""
    logger.info(f"Открытие документа через FastAPI: {file_path}")
    
    try:
        response = httpx.get(
            "http://localhost:8001/api/cad/open-document",
            params={"file_path": file_path},
            timeout=30.0
        )
        response.raise_for_status()
        return json.dumps(response.json(), ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"Ошибка открытия документа: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

@tool
def save_document(file_path: Optional[str] = None) -> str:
    """Сохранить текущий документ через FastAPI."""
    logger.info(f"Сохранение документа через FastAPI: {file_path or 'текущий'}")
    
    try:
        params = {"file_path": file_path} if file_path else {}
        response = httpx.get(
            "http://localhost:8001/api/cad/save-document",
            params=params,
            timeout=30.0
        )
        response.raise_for_status()
        return json.dumps(response.json(), ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"Ошибка сохранения документа: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

@tool
def close_document() -> str:
    """Закрыть текущий документ через FastAPI."""
    logger.info("Закрытие документа через FastAPI")
    
    try:
        response = httpx.get(
            "http://localhost:8001/api/cad/close-document",
            timeout=30.0
        )
        response.raise_for_status()
        return json.dumps(response.json(), ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"Ошибка закрытия документа: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

@tool
def create_shape(shape_type: str, size: float, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> str:
    """Создать фигуру через FastAPI."""
    logger.info(f"Создание фигуры через FastAPI: {shape_type}")
    return _create_shape_http(shape_type, size, x, y, z)

@tool
def create_cube(size: float = 10.0, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> str:
    """Создать куб через FastAPI."""
    logger.info(f"Создание куба через FastAPI, размер: {size}")
    return _create_shape_http("cube", size, x, y, z)

@tool
def create_sphere(size: float = 10.0, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> str:
    """Создать сферу через FastAPI."""
    logger.info(f"Создание сферы через FastAPI, диаметр: {size}")
    return _create_shape_http("sphere", size, x, y, z)

@tool
def create_cylinder(size: float = 10.0, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> str:
    """Создать цилиндр через FastAPI."""
    logger.info(f"Создание цилиндра через FastAPI, диаметр: {size}")
    return _create_shape_http("cylinder", size, x, y, z)

@tool 
def get_documents() -> str:
    """Получить список документов через FastAPI."""
    logger.info("Получение документов через FastAPI")
    
    try:
        response = httpx.get(
            "http://localhost:8001/api/cad/documents",
            timeout=30.0
        )
        response.raise_for_status()
        return json.dumps(response.json(), ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"Ошибка получения документов: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

@tool
def get_mcp_status() -> str:
    """Получить статус MCP через FastAPI."""
    logger.info("Получение статуса MCP через FastAPI")
    
    try:
        response = httpx.get(
            "http://localhost:8001/api/mcp/status",
            timeout=30.0
        )
        response.raise_for_status()
        return json.dumps(response.json(), ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"Ошибка получения статуса MCP: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

# ============ КЛАСС ПОЛНОЦЕННОГО АГЕНТА ============
class FullCADAgent:
    """Полноценный CAD агент с памятью и продвинутыми функциями"""
    
    def __init__(self):
        # Проверяем наличие API ключа
        api_key = os.getenv("API_KEY")
        if not api_key:
            raise ValueError("API_KEY не найден в .env. Установите API_KEY для SberCloud")
        
        # Инициализация LLM
        self.llm = get_llm()
        
        # Сбор всех инструментов
        self.tools = [
            open_document,
            save_document,
            close_document,
            create_shape,
            create_cube,
            create_sphere,
            create_cylinder,
            get_documents,
            get_mcp_status,
            get_health
        ]
        
        # Инициализация памяти
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Создание промпта
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Ты - профессиональный AI ассистент для CAD системы FreeCAD.
            Используй доступные инструменты для выполнения задач. Всегда работай последовательно:
            1. Открой документ (open_document)
            2. Создай фигуру (create_shape, create_cube и т.д.)
            3. Сохрани документ (save_document)
            4. Закрой документ (close_document)
            
            Будь точным и профессиональным. Отвечай на русском языке.
            
            Примеры команд:
            - "Создай куб 20мм" → open_document(auto_cube.FCStd) → create_cube(size=20) → save_document() → close_document()
            - "Покажи все документы" → get_documents()
            - "Проверь здоровье системы" → get_health()
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Создание агента
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Создание исполнителя
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
        
        logger.info("✅ Full CAD Agent инициализирован")
        logger.info(f"Модель: {MODEL}")
        logger.info(f"Инструментов: {len(self.tools)}")
    
    def process(self, query: str) -> Dict[str, Any]:
        """Обработать запрос пользователя"""
        logger.info(f"📨 Запрос: {query}")
        
        try:
            # Запуск агента
            result = self.agent_executor.invoke({"input": query})
            
            response = {
                "success": True,
                "query": query,
                "response": result.get("output", "Нет ответа")
            }
            
            logger.info("✅ Запрос успешно обработан")
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки: {str(e)}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "response": f"Произошла ошибка при обработке запроса: {str(e)}"
            }
    
    def clear_memory(self):
        """Очистить память агента"""
        self.memory.clear()
        logger.info("🧹 Память агента очищена")

# ============ SINGLETON ДЛЯ ПРОЕКТА ============
_agent_instance = None

def get_agent() -> FullCADAgent:
    """Получить глобальный экземпляр агента"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = FullCADAgent()
    return _agent_instance

# ============ ТЕСТОВЫЙ СКРИПТ ============
if __name__ == "__main__":
    # Инициализация агента
    try:
        agent = get_agent()
        print("=" * 60)
        print("✅ CAD Agent успешно инициализирован")
        print(f"Модель: {MODEL}")
        print(f"Инструментов: {len(agent.tools)}")
        print("=" * 60)
        
        # Тестовый запрос
        test_query = "Проверь здоровье системы"
        print(f"Тестовый запрос: {test_query}")
        result = agent.process(test_query)
        print(f"Ответ: {result['response']}")
        print("=" * 60)
        
        # Интерактивный режим
        print("Чат с агентом (нажмите Ctrl+C для выхода)")
        print("-" * 50)
        
        while True:
            user_input = input("Вы: ").strip()
            if not user_input:
                continue
            
            result = agent.process(user_input)
            print(f"🤖 Агент: {result['response']}\n")
            
    except Exception as e:
        print(f"❌ Ошибка инициализации: {str(e)}")
        print("Убедитесь что:")
        print("1. Установлены переменные окружения в .env файле")
        print("2. API_KEY указан для SberCloud")
        print("3. FastAPI сервер запущен (python main.py)")