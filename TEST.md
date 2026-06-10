# Как протестировать (Windows)

Две части: **A** — быстрый тест без Доты (подделать данные), **B** — на живом матче.

---

## A. Быстрый тест без Доты

Проверяет, что сервер, `/state` и веб-оверлей работают.

### 1. Установить зависимость (один раз)
```
cd %USERPROFILE%\Desktop\dota-gsi
python -m pip install flask
```
Если `python` не находится — поставь Python с python.org с галкой **«Add to PATH»**.
Проверка: `python --version`.

### 2. Запустить сервер (оставь это окно открытым)
```
python gsi_server.py
```
Должно написать: `[i] Слушаю GSI на http://127.0.0.1:3000/`

### 3. Открыть оверлей в браузере
```
http://127.0.0.1:3000/
```
Сейчас будет «Спектатор-данных нет» — это нормально, данных ещё не слали.

### 4. В НОВОМ окне терминала отправить тестовый payload

**cmd:**
```
cd %USERPROFILE%\Desktop\dota-gsi
curl -X POST -H "Content-Type: application/json" -d @test.json http://127.0.0.1:3000/
```

**PowerShell** (тут `curl` — алиас, нужен именно `curl.exe`):
```
cd $env:USERPROFILE\Desktop\dota-gsi
curl.exe -X POST -H "Content-Type: application/json" -d "@test.json" http://127.0.0.1:3000/
```

**Если curl недоступен (PowerShell, запасной вариант):**
```
Invoke-RestMethod -Uri http://127.0.0.1:3000/ -Method Post -ContentType "application/json" -InFile test.json
```

### Что должно произойти
- В окне сервера появятся предметы по командам.
- В браузере (макс. через 1 сек): Radiant — Alice / Juggernaut с предметами,
  Dire — Bob / Lina. Индикатор слева станет зелёным, время `10:42`.

Если так — весь конвейер исправен.

---

## B. Тест на живом матче (настоящий GSI)

### 1. Сгенерить конфиг для клиента Доты
```
cd %USERPROFILE%\Desktop\dota-gsi
python gsi_server.py --make-config
```
Создастся `gamestate_integration_items.cfg`.

### 2. Скопировать конфиг в папку Доты
```
C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\dota\cfg\gamestate_integration\
```
- Папку `gamestate_integration` создай, если её нет.
- Если Steam на другом диске — ищи там `steamapps\common\dota 2 beta\...`.

### 3. Полностью перезапустить Доту
Не просто матч — закрыть и открыть клиент заново.

### 4. Запустить сервер
```
python gsi_server.py
```

### 5. Зайти в режим СПЕКТАТОРА живого матча
Watch -> Live, или зрителем в лобби.

> ВАЖНО: предметы всех 10 игроков приходят ТОЛЬКО в спектаторе.
> В своей обычной игре GSI отдаст лишь тебя — это by design (античит).

### 6. Смотреть
- Браузер `http://127.0.0.1:3000/` — предметы обеих команд, обновляются на ходу.
- Рядом со скриптом появится `raw_payload.json` — первый сырой payload от Доты.

---

## Если на живом матче не парсится
Открой `raw_payload.json`, глянь раздел `items`. Если ключи не `team2`/`team3`
или слоты называются иначе (Valve мог поменять в патче) — пришли этот файл,
подгоним `extract()` под текущую структуру.
