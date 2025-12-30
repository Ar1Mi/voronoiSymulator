# Инструкция по сборке Windows .exe

## Автоматическая сборка через GitHub Actions

### Как это работает

1. **Push в репозиторий** - при каждом push в ветку `main` или `master` автоматически запускается сборка
2. **Ручной запуск** - можно запустить сборку вручную через интерфейс GitHub

### Как получить готовый .exe файл

#### Вариант 1: Скачать из Actions (после каждого коммита)

1. Перейдите в ваш репозиторий на GitHub
2. Откройте вкладку **Actions**
3. Выберите последний успешный запуск workflow "Build Windows Executable"
4. Прокрутите вниз до секции **Artifacts**
5. Скачайте `VoronoiSimulator-Windows.zip`
6. Распакуйте архив - внутри будет `VoronoiSimulator.exe`

#### Вариант 2: Запустить вручную

1. Перейдите в **Actions** → **Build Windows Executable**
2. Нажмите **Run workflow** → выберите ветку → **Run workflow**
3. Дождитесь завершения сборки
4. Скачайте артефакт как описано выше

#### Вариант 3: Создать Release (рекомендуется для финальных версий)

1. Создайте тег версии:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
2. GitHub автоматически создаст Release с прикрепленным .exe файлом
3. Файл будет доступен в разделе **Releases**

## Локальная сборка (если нужно)

### Требования
- Python 3.11+
- Windows (для сборки .exe)

### Шаги

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. Соберите .exe:
   ```bash
   pyinstaller --onefile --windowed --name VoronoiSimulator main.py
   ```

3. Готовый файл будет в папке `dist/VoronoiSimulator.exe`

## Параметры сборки

- `--onefile` - создает один исполняемый файл
- `--windowed` - скрывает консольное окно (для GUI приложений)
- `--name VoronoiSimulator` - имя выходного файла

## Troubleshooting

### Проблема: "Failed to execute script"
- Убедитесь, что все зависимости указаны в `requirements.txt`
- Проверьте, что нет импортов динамических модулей

### Проблема: Большой размер .exe
- Это нормально для PyInstaller (включает Python и все библиотеки)
- Обычный размер: 50-150 MB для PyQt6 приложений

### Проблема: Антивирус блокирует .exe
- Это ложное срабатывание (common для PyInstaller)
- Добавьте файл в исключения антивируса
- Или подпишите .exe цифровой подписью

## Дополнительные возможности

### Добавить иконку приложения

1. Создайте файл `icon.ico` в корне проекта
2. Измените команду сборки:
   ```bash
   pyinstaller --onefile --windowed --icon=icon.ico --name VoronoiSimulator main.py
   ```

### Включить дополнительные файлы (например, папку Dane)

Измените команду:
```bash
pyinstaller --onefile --windowed --add-data "Dane;Dane" --name VoronoiSimulator main.py
```

Примечание: на Windows используется `;`, на Linux/Mac - `:`
