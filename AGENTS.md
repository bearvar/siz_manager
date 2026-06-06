# Repository Guidelines

## Project Structure & Module Organization

This is a Django 5 project packaged with Poetry. The Django entry point is `manager/manage.py`; project settings live in `manager/manager/`. Feature apps are under `manager/core/`, `manager/users/`, and `manager/reports/`. Shared HTML templates live in `manager/templates/`, while project static assets are in `manager/static/` and collected/generated static output is in `manager/staticfiles/` and top-level `staticfiles/`. Deployment files include `Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml`, `nginx/`, `nginx-prod.conf`, and backup scripts in `backups/`.

## Build, Test, and Development Commands

- `poetry install` installs Python dependencies from `pyproject.toml` and `poetry.lock`.
- `poetry run python manager/manage.py runserver` starts the local Django server.
- `poetry run python manager/manage.py migrate` applies database migrations.
- `poetry run python manager/manage.py makemigrations core users reports` creates app migrations after model changes.
- `poetry run python manager/manage.py test` runs Django tests.
- `docker compose up --build` builds and runs the local container stack.
- `docker compose -f docker-compose.prod.yml up -d` starts the production compose stack.

## Coding Style & Naming Conventions

Use idiomatic Python with 4-space indentation. Keep Django models, forms, views, and URL declarations in their conventional app files. Name classes in `PascalCase`, functions and variables in `snake_case`, and templates by feature/action, for example `employee_list.html` or `create_issue.html`. Keep Russian user-facing text consistent with existing templates and commit history. Do not edit generated or collected static files unless the task explicitly requires it; prefer source assets in `manager/static/`.

## Testing Guidelines

No dedicated test suite is currently committed. Add Django tests in each app as `tests.py` or a `tests/` package. Name test methods `test_<behavior>`, focus on models, forms, permissions, and view behavior, and run `poetry run python manager/manage.py test` before submitting changes. For migration or deployment changes, also run `poetry run python manager/manage.py check`.

## Commit & Pull Request Guidelines

Recent commits use short Russian summaries describing the completed change, for example `Изменение favicon` or `Обновление README`. Keep commits concise and single-purpose. Pull requests should include a short change summary, affected app or deployment area, test/check commands run, linked issue if available, and screenshots for visible UI/template changes.

## Security & Configuration Tips

Keep secrets out of git. Local and production runs require `SECRET_KEY`; production also uses `.env.prod` values such as `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and cookie security settings. Never recommit deleted secret files such as `.env.prod`.

## Agent-Specific Instructions

Use CodeGraph for structural code questions when available. Use literal search only for strings, comments, logs, or exact file-content queries.


## ECC skills without MCP

This project has local ECC skills under:

`.agents/skills/ecc/`

Use these skills as optional guidance only. Do not require MCP servers. Do not attempt to start or configure MCP unless the user explicitly asks.

For complex coding tasks:
- suggest relevant skills/workflows before implementation;
- prefer plan → implementation → tests → review;
- avoid spamming skill suggestions;
- for auth, OAuth, secrets, wallets, trading, signing, or external APIs, suggest security review.


## Установленные плагины и как ими пользоваться

<!--
  PLUGIN_INDEXES — список абсолютных путей до PLUGIN-INDEX.md каждого установленного плагина.
  Это единственное место, которое нужно редактировать при добавлении / удалении плагина.
  Один путь на строку. Пустые строки и строки, начинающиеся с #, игнорируются.
-->

```
PLUGIN_INDEXES:
/home/bearvar/Yandex.Disk/CTB/Projects/arbipoly/.agents/skills/ecc/PLUGIN-INDEX.md
```

### Что делать с этим списком

В этом окружении установлены расширения Claude Code (плагины), добавляющие агентов, скиллы, slash-команды, хуки, правила и MCP-серверы. Ты обязан знать об их существовании и **проактивно предлагать их пользователю**.

**В начале каждой сессии (до ответа на первую задачу пользователя):**

1. Прочитай блок `PLUGIN_INDEXES` выше и извлеки все пути.
2. Для каждого пути — прочитай файл через Read. Это короткие справочники (≤ 400 строк), они быстро читаются.
3. Для каждого индекса запомни: имя плагина (из заголовка файла), количество компонентов. Держи эту информацию в рабочей памяти всю сессию.
4. Если рядом с индексом (в той же директории) лежит `PLUGIN-GUIDE.md` — запомни его путь, но **не читай** сразу. Он понадобится только по запросу пользователя или когда нужны детали.
5. Если какой-то файл из `PLUGIN_INDEXES` не существует — **не выдумывай его содержимое**. Сообщи пользователю в первом же ответе: "Индекс плагина по пути X не найден, проверь путь в CLAUDE.md". Остальные индексы всё равно загрузи.
6. Если `PLUGIN_INDEXES` пуст или содержит только плейсхолдеры вида `/absolute/path/...` — работай как обычно, без подсказок про плагины.

### Правило проактивных подсказок

Твоя задача — не только выполнять запросы, но и **обучать пользователя пользоваться установленными плагинами**. Для каждой нетривиальной задачи пользователя действуй по следующему алгоритму:

**Шаг 1 — Перед началом выполнения (pre-execution suggestion):**

1. Проанализируй задачу пользователя.
2. Сверься с разделом "Когда что предлагать пользователю → Перед началом задачи" во **всех** загруженных индексах.
3. Если находишь релевантный компонент (агент / команда / MCP / скилл), который **лучше** подошёл бы для этой задачи, чем твоё прямое выполнение — **остановись и предложи его пользователю**. Формат подсказки:

   ```
   💡 Перед тем как начать: в плагине <имя плагина> есть <агент/команда/MCP> `<имя>`,
   который специализируется на таких задачах. Рекомендую <вызвать /команду | подключить MCP | делегировать агенту>,
   потому что <одна строка: что это даст>.

   Использовать его? (да / нет / объясни подробнее)
   ```

4. Если пользователь отказывается — выполняй задачу сам и больше не предлагай этот же компонент в рамках текущей задачи.
5. Если задача тривиальная (однострочный фикс, вопрос, объяснение) — подсказку **не давай**, просто отвечай.

**Шаг 2 — После выполнения задачи (post-execution suggestion):**

1. После того как задача выполнена (код написан, файл изменён, команда отработала), сверься с разделом "Когда что предлагать пользователю → После выполнения задачи" во всех загруженных индексах.
2. Если находишь релевантный follow-up — предложи его **одним блоком в конце ответа**, не более 2-3 пунктов:

   ```
   ✅ Готово. Что имеет смысл сделать дальше с помощью плагина:
   - <действие 1>: вызови `<команда>` — <зачем>
   - <действие 2>: делегируй агенту `<имя>` — <зачем>
   ```

3. Не предлагай follow-up действия, которые не относятся к сделанному (не предлагай security-review после правки README; не предлагай doc-updater после фикса опечатки).

### Ограничения на подсказки

- **Максимум одна pre-подсказка** на задачу. Не перегружай пользователя выбором.
- **Максимум 3 post-подсказки** на задачу. Если их больше — выбирай самые важные.
- **Не предлагай то, что уже было отвергнуто** в текущей сессии для похожей задачи.
- **Не предлагай компоненты, которых нет в индексах.** Если не уверен, что компонент существует — не предлагай.
- Если подсказка из одного плагина дублирует подсказку из другого — выбери одну, самую подходящую, не показывай обе.
- Если пользователь прямо сказал "просто сделай, без подсказок" — отключи подсказки до конца сессии.

### Когда НЕ подглядывать в индексы

- Пользователь в режиме диалога / вопроса-ответа без изменения кода.
- Пользователь попросил объяснить концепцию.
- Пользователь явно в середине другого workflow (например, уже запустил агента).

### Когда читать полный `PLUGIN-GUIDE.md`

Читай **только** релевантный раздел полного гайда (не весь файл) если:
- Пользователь спросил "как устроен агент X" / "что делает команда Y".
- Тебе нужна точная спецификация компонента, чтобы его корректно вызвать.
- Пользователь сам попросил показать документацию плагина.

Путь к полному гайду ищи рядом с соответствующим индексом (та же директория, имя `PLUGIN-GUIDE.md`). Никогда не загружай весь `PLUGIN-GUIDE.md` в контекст целиком без явной необходимости.




<!-- repo-task-proof-loop:start -->
## Repo task proof loop

For substantial features, refactors, and bug fixes, use the repo-task-proof-loop workflow.

Required artifact path:
- Keep all task artifacts in `.agent/tasks/<TASK_ID>/` inside this repository.

Required sequence:
1. Freeze `.agent/tasks/<TASK_ID>/spec.md` before implementation.
2. Implement against explicit acceptance criteria (`AC1`, `AC2`, ...).
3. Create `evidence.md`, `evidence.json`, and raw artifacts.
4. Run a fresh verification pass against the current codebase and rerun checks.
5. If verification is not `PASS`, write `problems.md`, apply the smallest safe fix, and reverify.

Hard rules:
- Do not claim completion unless every acceptance criterion is `PASS`.
- Verifiers judge current code and current command results, not prior chat claims.
- Fixers should make the smallest defensible diff.

Installed workflow agents:
- `.codex/agents/task-spec-freezer.toml`
- `.codex/agents/task-builder.toml`
- `.codex/agents/task-verifier.toml`
- `.codex/agents/task-fixer.toml`
<!-- repo-task-proof-loop:end -->

Do not boot/use MCP servers.
Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
