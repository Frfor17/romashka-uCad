# run_all.py
import subprocess
import sys
import os
import time
import webbrowser
from threading import Thread

def start_fastapi():
    """Запуск FastAPI сервера."""
    print("🚀 Запуск FastAPI сервера...")
    subprocess.run([sys.executable, "main.py"])

def start_agent_cli():
    """Запуск CLI интерфейса агента."""
    time.sleep(3) 
    print("\n🤖 Запуск CLI интерфейса агента...")
    subprocess.run([sys.executable, "ai_agent/agent.py"])

def open_browser():
    """Открыть браузер с документацией API."""
    time.sleep(5)
    webbrowser.open("http://localhost:8001/docs")

if __name__ == "__main__":
    print("=" * 60)
    print("CAD System Launcher")
    print("=" * 60)
    
    os.chdir("ai_dev_tools_hack_2025")
    
    fastapi_thread = Thread(target=start_fastapi)
    fastapi_thread.daemon = True
    fastapi_thread.start()
    
    time.sleep(2)
    
    browser_thread = Thread(target=open_browser)
    browser_thread.start()
    
    # Выводим информацию о запуске
    print("\n✅ Система запущена:")
    print("1. FastAPI сервер: http://localhost:8001")
    print("2. MCP сервер: порт 8000")
    print("3. Swagger UI: http://localhost:8001/docs")
    print("4. Agent API: POST http://localhost:8001/api/agent/query")
    print("\nВыберите опцию:")
    print("1. Запустить CLI интерфейс агента")
    print("2. Протестировать через HTTP (curl)")
    print("3. Только сервер (без CLI)")
    
    choice = input("\nВаш выбор (1-3): ").strip()
    
    if choice == "1":
        start_agent_cli()
    elif choice == "2":
        print("\nПримеры curl запросов:")
        print('curl -X POST http://localhost:8001/api/agent/query \\')
        print('  -H "Content-Type: application/json" \\')
        print('  -d \'{"query": "Создай куб размером 20мм"}\'')
        print("\nОжидание завершения сервера (Ctrl+C для выхода)...")
        try:
            fastapi_thread.join()
        except KeyboardInterrupt:
            print("\nЗавершение работы...")
    else:
        print("\nСервер запущен. Для выхода нажмите Ctrl+C")
        print("\nПример использования агента:")
        print('curl -X POST http://localhost:8001/api/agent/query \\')
        print('  -H "Content-Type: application/json" \\')
        print('  -d \'{"query": "Проверь здоровье системы"}\'')
        try:
            fastapi_thread.join()
        except KeyboardInterrupt:
            print("\nЗавершение работы...")