# Тестовая версия на GitHub Pages

1. Создай публичный репозиторий `mechanic-petersburg` на GitHub.
2. Распакуй архив и залей всё его содержимое в корень ветки `main`, включая скрытую папку `.github`. В корне должен лежать `project.godot`.
3. Открой Settings → Pages и выбери GitHub Actions в поле Source.
4. Открой Actions → Godot Web → GitHub Pages и нажми Run workflow для ветки `main`. Если запуск от первого коммита произошёл до настройки Pages, повтори его после настройки.
5. Возьми ссылку из Settings → Pages и открой в Safari на iPhone.

Каждое следующее изменение в `main` пересобирает игру по тому же адресу.
Для быстрых правок из браузера открой репозиторий на `github.dev`. Текст заявки сейчас находится в `scripts/phone.gd`, скорость ходьбы — в `scripts/room.gd`.
