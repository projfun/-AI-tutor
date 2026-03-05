# 🚀 Установка и запуск AI-Tutor

## 📋 Системные требования

### 🔧 Минимальные требования
- **ОС:** Windows 10+, macOS 10.15+, Ubuntu 20.04+
- **CPU:** 4+ ядер с поддержкой AVX
- **RAM:** 8 ГБ (минимум 4 ГБ для легких моделей)
- **Storage:** 10 ГБ свободного места
- **Python:** 3.13+ (рекомендуется 3.13)

### 🚀 Рекомендуемые требования
- **CPU:** 8+ ядер
- **RAM:** 16 ГБ+
- **GPU:** NVIDIA GTX 1060+ (опционально для ускорения)
- **Storage:** 20 ГБ+ SSD
- **Интернет:** Для веб-поиска и портала

---

## ⚡ Быстрая установка (5 минут)

### 🎯 Шаг 1: Клонирование репозитория
```bash
git clone https://github.com/projfun/-AI-tutor.git
cd AI-tutor
```

### 📦 Шаг 2: Установка зависимостей
```bash
# Создание виртуального окружения (рекомендуется)
python -m venv venv

# Активация
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 🤖 Шаг 3: Автоматическая установка Ollama
```bash
# Приложение автоматически проверит и установит Ollama
python main.py

# Следуйте инструкциям в консоли
```

### 🎉 Шаг 4: Первый запуск
```bash
# Основной запуск
python main.py

# или для Windows:
run.bat
```

---

## 🎮 Для проверяющего: Полная инструкция

### 📋 Проверка системы перед установкой
```bash
# Проверка версии Python
python --version

# Должна быть 3.13+ для совместимости
```

### 🚀 Быстрый старт (без виртуального окружения)
Если вы хотите просто проверить работоспособность:

```bash
# 1. Скачайте архив
git clone https://github.com/projfun/-AI-tutor.git
cd AI-tutor

# 2. Установите зависимости напрямую
pip install -r requirements.txt

# 3. Запустите приложение
python main.py
```

### 🔧 Полная установка с виртуальным окружением
Для стабильной работы:

```bash
# 1. Клонирование
git clone https://github.com/projfun/-AI-tutor.git
cd AI-tutor

# 2. Создание виртуального окружения
python -m venv ai_tutor_env

# 3. Активация
# Windows:
ai_tutor_env\Scripts\activate
# Linux/macOS:
source ai_tutor_env/bin/activate

# 4. Установка зависимостей
pip install -r requirements.txt

# 5. Первый запуск (установит Ollama автоматически)
python main.py
```

### 🎯 Что происходит при первом запуске

Приложение автоматически выполнит:
1. ✅ **Проверку системы** - Python, зависимости, свободные порты
2. 🤖 **Установку Ollama** - Скачает и установит если нужно
3. 📦 **Загрузку модели** - Llama 3.1 8B (квантованная)
4. 🌐 **Запуск веб-интерфейса** - Откроет http://localhost:8000
5. 📋 **Диагностику** - Покажет статус всех компонентов

### 🎮 Первый запуск: Что делать дальше

После успешного запуска:

1. 🏫 **Авторизация в портале**
   - Откройте [Мою Школу](https://authedu.mosreg.ru)
   - Нажмите F12 → Network
   - Найдите запрос и скопируйте Authorization
   - Вставьте токен в приложение

2. 💬 **Начало диалога с ИИ**
   - Задайте любой школьный вопрос
   - Получите пошаговое объяснение
   - Используйте кнопки подсказок

3. 📚 **Загрузка учебников**
   - Нажмите "Загрузить учебники"
   - Выберите PDF файлы
   - Дождитесь индексации

4. 📅 **Работа с расписанием**
   - Расписание загрузится автоматически
   - Нажмите на урок для получения контекста
   - Спрашивайте про домашние задания

### 🔧 Если что-то пошло не так

#### ❌ "Python не найден"
```bash
# Windows: Скачайте с python.org
https://www.python.org/downloads/

# Добавьте в PATH
set PATH=%PATH%;C:\Python313\Scripts
```

#### ❌ "Ollama не запускается"
```bash
# Проверка службы
ollama list

# Ручная установка
curl -fsSL https://ollama.ai/install.sh | sh
```

#### ❌ "Порт 8000 занят"
```bash
# Найти процесс
netstat -ano | findstr :8000

# Закрыть процесс
# Windows:
taskkill /PID <PID> /F
```

#### ❌ "Модель не загружается"
```bash
# Проверка интернета
ping google.com

# Ручная загрузка
ollama pull llama3.1:8b-q4_K_M
```

---

## 🔧 Ручная установка (для продвинутых)

### 📦 Установка Python 3.13
```bash
# Windows (с помощью winget)
winget install Python.Python.3.13

# macOS (с помощью Homebrew)
brew install python@3.13

# Ubuntu/Debian
sudo apt update
sudo apt install python3.13 python3.13-pip python3.13-venv
```

### 🤖 Установка Ollama вручную
```bash
# Скачивание
curl -fsSL https://ollama.ai/install.sh | sh

# Проверка установки
ollama --version

# Загрузка модели
ollama pull llama3.1:8b-q4_K_M
```

### 📦 Установка зависимостей вручную
```bash
pip install eel==0.16.0
pip install requests==2.31.0
pip install ollama==0.6.1
pip install chromadb==0.5.0
pip install duckduckgo-search==3.9.10
pip install beautifulsoup4==4.12.2
pip install aiohttp==3.10.0
pip install pydantic==2.9.0
pip install python-dotenv==1.0.0
pip install aiofiles==23.2.0
pip install numpy==1.26.0
pip install pymupdf4llm==0.0.6
```

---

## 🔑 Конфигурация

### 📝 Создание .env файла
Создайте файл `.env` в корне проекта:

```bash
# Токен доступа к школьному порталу
SCHOOL_PORTAL_TOKEN=your_token_here

# Настройки Ollama
OLLAMA_PORT=11434
MODEL_NAME=llama3.1:8b-q4_K_M

# Опциональные настройки
DEBUG=false
RAG_DEBUG=false
LOG_LEVEL=INFO
```

### 🏫 Получение токена школьного портала
1. Откройте [Мою Школу](https://authedu.mosreg.ru)
2. Нажмите **F12** → вкладка **Network**
3. Обновите страницу (**F5**)
4. Найдите любой запрос к API
5. Скопируйте заголовок **Authorization**
6. Вставьте в `.env` файл

---

## 🚀 Запуск приложения

### 🎮 Основные способы запуска

#### Windows
```bash
# Через bat файл
run.bat

# Прямой командой
python main.py
```

#### Linux/macOS
```bash
# Через терминал
python3 main.py

# Или через Python launcher
python main.py
```

### 🌐 Веб-интерфейс
После запуска приложение автоматически откроет браузер с:
- **Адрес:** http://localhost:8000
- **Интерфейс:** Веб-приложение в браузере
- **Функции:** Чат с ИИ, расписание, загрузка учебников

---

## 🔍 Проверка установки

### ✅ Автоматическая проверка
Приложение автоматически проверит:
- ✅ Наличие Python 3.13+
- ✅ Установленные зависимости
- ✅ Доступность Ollama
- ✅ Наличие модели Llama 3.1
- ✅ Свободный порт для веб-интерфейса

### 🧪 Ручное тестирование
```bash
# Тест AI движка
python -c "from engine import AITutorEngine; print('AI Engine OK')"

# Тест портала
python -c "from portal import SchoolPortalClient; print('Portal OK')"

# Тест веб-интерфейса
python -c "import eel; print('Eel OK')"
```

---

## 🐛 Устранение проблем

### 🔧 Частые проблемы

#### ❌ "Python не найден"
```bash
# Windows: Добавьте Python в PATH
# Проверка:
python --version

# Установка переменной:
set PATH=%PATH%;C:\Python313\Scripts
```

#### ❌ "Ollama не запускается"
```bash
# Проверка службы
ollama list

# Перезапуск службы
# Windows:
net stop ollama && net start ollama
# Linux:
sudo systemctl restart ollama
```

#### ❌ "Порт 8000 занят"
```bash
# Поиск процесса
netstat -ano | findstr :8000

# Убийство процесса
# Windows:
taskkill /PID <PID> /F
# Linux:
kill -9 <PID>
```

#### ❌ "Модель не загружается"
```bash
# Ручная загрузка
ollama pull llama3.1:8b-q4_K_M

# Проверка списка моделей
ollama list
```

### 📝 Логирование
При проблемах проверьте логи:
```bash
# Основной лог
tail -f logs/app.log

# Лог ошибок
tail -f logs/errors.log

# Отладочный режим
DEBUG=true python main.py
```

---

## 🚀 Продвинутая конфигурация

### 🎚️ Оптимизация производительности
```bash
# Включение GPU (если доступно)
CUDA_VISIBLE_DEVICES=0 python main.py

# Настройка потоковой генерации
STREAM_RESPONSES=true

# Оптимизация памяти
MEMORY_EFFICIENT=true
```

### 🔒 Безопасность
```bash
# Отключение телеметрии
TELEMETRY=false

# Шифрование кэша
ENCRYPT_CACHE=true

# Ограничение доступа
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 🌐 Сетевые настройки
```bash
# Настройка прокси
HTTP_PROXY=http://proxy:port
HTTPS_PROXY=http://proxy:port

# Таймауты
REQUEST_TIMEOUT=30
OLLAMA_TIMEOUT=60
```

---

## 📱 Мобильная версия

### 📲 Установка на смартфон
```bash
# Требования:
- Android 8+ / iOS 13+
- 4 ГБ+ RAM
- 2 ГБ+ свободного места

# Установка через PWA
# Откройте в браузере: http://your-server:8000
# Добавьте на главный экран
```

### 🔄 Синхронизация
```bash
# Настройка синхронизации
SYNC_ENABLED=true
SYNC_SERVER=http://your-server:port
SYNC_API_KEY=your_key
```

---

## 🎯 Следующие шаги

После успешной установки:

1. 🎫 **Авторизуйтесь** в школьном портале через приложение
2. 📚 **Загрузите** учебные материалы (PDF)
3. 🗄️ **Дождитесь** индексации в RAG системе
4. 💬 **Начните диалог** с ИИ-наставником
5. 📊 **Отслеживайте** прогресс обучения

---

## 📞 Поддержка

При возникновении проблем:

- 📖 **Документация:** [ARCHITECTURE.md](ARCHITECTURE.md)
- 🐛 **Сообщить об ошибке:** [GitHub Issues](https://github.com/projfun/-AI-tutor/issues)
- 💬 **Сообщество:** [Telegram](https://t.me/proj_1)

---

**Готово к работе! 🎉**
