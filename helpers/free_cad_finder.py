import os
import sys
import subprocess
import winreg  # Только для Windows

def find_freecad_windows():
    """Поиск FreeCAD на Windows через реестр и Program Files."""
    paths = []
    
    # 1. Поиск в реестре (самый надежный способ)
    try:
        # Пробуем найти через установщик Windows
        reg_keys = [
            r"SOFTWARE\FreeCAD",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\FreeCAD",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\FreeCAD.exe"
        ]
        
        for key_path in reg_keys:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                install_path, _ = winreg.QueryValueEx(key, "InstallLocation")
                if install_path:
                    bin_path = os.path.join(install_path, "bin")
                    if os.path.exists(bin_path):
                        paths.append(bin_path)
                winreg.CloseKey(key)
            except:
                pass
    except ImportError:
        pass  # Если не Windows
    
    # 2. Поиск в Program Files
    program_files = [
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    ]
    
    for pf in program_files:
        if os.path.exists(pf):
            for item in os.listdir(pf):
                if "FreeCAD" in item and os.path.isdir(os.path.join(pf, item)):
                    bin_path = os.path.join(pf, item, "bin")
                    if os.path.exists(bin_path):
                        paths.append(bin_path)
    
    return paths

def find_freecad_linux_mac():
    """Поиск FreeCAD на Linux/macOS."""
    paths = []
    
    # Стандартные пути для Linux
    linux_paths = [
        "/usr/lib/freecad/lib",
        "/usr/lib/freecad-daily/lib",
        "/opt/freecad/lib",
    ]
    
    # Стандартные пути для macOS
    mac_paths = [
        "/Applications/FreeCAD.app/Contents/Resources/lib",
        "/Applications/FreeCAD.app/Contents/Resources/Mod",  # Альтернативный путь
    ]
    
    # Проверяем все возможные пути
    test_paths = linux_paths if sys.platform == "linux" else mac_paths
    for path in test_paths:
        if os.path.exists(path):
            paths.append(path)
    
    # Пытаемся найти через which/whereis
    try:
        if sys.platform == "linux":
            result = subprocess.run(["whereis", "freecad"], capture_output=True, text=True)
            if result.stdout:
                for line in result.stdout.split():
                    if "bin" in line:
                        lib_path = line.replace("bin", "lib")
                        if os.path.exists(lib_path):
                            paths.append(lib_path)
    except:
        pass
    
    return paths

def test_freecad_import(path):
    """Проверяет, можно ли импортировать FreeCAD из данного пути."""
    original_sys_path = sys.path.copy()
    try:
        if path not in sys.path:
            sys.path.insert(0, path)
        
        import FreeCAD
        version = '.'.join(map(str, FreeCAD.Version()[0:3]))
        sys.path = original_sys_path  # Восстанавливаем оригинальный путь
        return True, version
    except ImportError as e:
        sys.path = original_sys_path
        return False, str(e)
    except:
        sys.path = original_sys_path
        return False, "Unknown error"

def main():
    print("🔍 Поиск установленного FreeCAD...")
    print("=" * 60)
    
    # Определяем ОС и ищем пути
    if sys.platform == "win32":
        print("Платформа: Windows")
        paths = find_freecad_windows()
    elif sys.platform == "linux":
        print("Платформа: Linux")
        paths = find_freecad_linux_mac()
    elif sys.platform == "darwin":
        print("Платформа: macOS")
        paths = find_freecad_linux_mac()
    else:
        print(f"Неподдерживаемая платформа: {sys.platform}")
        return
    
    if not paths:
        print("❌ FreeCAD не найден в стандартных местах.")
        print("\nРучной поиск:")
        print("1. Найдите ярлык FreeCAD на рабочем столе или в меню Пуск")
        print("2. Нажмите правой кнопкой → 'Свойства'")
        print("3. В поле 'Объект' будет путь к EXE-файлу")
        print("4. Папка 'bin' находится в той же директории, что и EXE-файл")
        return
    
    print(f"Найдено возможных путей: {len(paths)}")
    print("-" * 60)
    
    success = False
    for i, path in enumerate(paths, 1):
        print(f"\nПуть #{i}: {path}")
        if os.path.exists(path):
            print(f"   ✅ Папка существует")
            import_ok, message = test_freecad_import(path)
            if import_ok:
                print(f"   ✅ FreeCAD импортируется! Версия: {message}")
                print(f"\n🎉 УСПЕХ! Используйте этот путь:")
                print(f"   sys.path.append(r'{path}')")
                success = True
                break
            else:
                print(f"   ❌ Не удалось импортировать: {message}")
        else:
            print(f"   ❌ Папка не существует")
    
    if not success:
        print("\n" + "=" * 60)
        print("⚠️  FreeCAD найден, но не удалось импортировать.")
        print("\nВозможные причины и решения:")
        print("1. Установите FreeCAD как Python-пакет (проще всего):")
        print("   pip install freecad")
        print("\n2. Если нужно использовать именно standalone версию:")
        print("   - Убедитесь, что путь ведет к папке 'bin' (Windows) или 'lib' (Linux/macOS)")
        print("   - Проверьте, установлены ли все зависимости FreeCAD")
        print("\n3. Альтернативный способ найти путь:")
        print("   - Запустите FreeCAD")
        print("   - В консоли Python внутри FreeCAD выполните:")
        print("     import sys; print(sys.path)")

if __name__ == "__main__":
    main()