import sys
import os

# 1. Добавляем ваш путь
freecad_path = r'C:\Program Files\FreeCAD 1.0\bin'
sys.path.append(freecad_path)
print(f"🔍 Добавлен путь: {freecad_path}")
print(f"   Папка существует: {'✅' if os.path.exists(freecad_path) else '❌'}")

# 2. Пытаемся импортировать
print("\n🔄 Пробуем импортировать FreeCAD...")
try:
    import FreeCAD
    import Part
    
    print(f"✅ УСПЕХ! FreeCAD загружен")
    print(f"   Версия: {'.'.join(map(str, FreeCAD.Version()[0:3]))}")
    
    # 3. Простой тест - создаём куб
    print("\n🧪 Тестируем создание 3D-объекта...")
    
    # Создаём новый документ
    doc = FreeCAD.newDocument("TestDocument")
    print(f"   Создан документ: {doc.Name}")
    
    # Создаём куб 10x10x10 мм
    cube = Part.makeBox(10, 10, 10)
    
    # Добавляем объект в документ
    obj = doc.addObject("Part::Feature", "TestCube")
    obj.Shape = cube
    doc.recompute()
    
    print(f"   Создан куб 10x10x10 мм")
    print(f"   Объём куба: {cube.Volume:.2f} мм³")
    
    # Сохраняем для проверки (опционально)
    test_file = "test_cube.FCStd"
    doc.saveAs(test_file)
    print(f"   Файл сохранён: {test_file}")
    
    print("\n🎉 ВСЁ РАБОТАЕТ! FreeCAD подключён корректно.")
    
except ImportError as e:
    print(f"❌ ОШИБКА импорта: {e}")
    print("\nВозможные причины:")
    print("1. Неправильный путь - проверьте C:\\Program Files\\FreeCAD 1.0\\bin")
    print("2. FreeCAD требует дополнительные DLL - запустите FreeCAD отдельно один раз")
    print("3. Попробуйте запустить от администратора")

except Exception as e:
    print(f"❌ ОШИБКА при работе с FreeCAD: {e}")
    print("\nНо импорт прошёл успешно! Проблема в работе API.")