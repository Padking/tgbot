# tgbot
Бот "Угадай мелодию"

## Описание

В данном репозитории находятся скрипт и набор вспомогательных файлов Telegram-бота, 
который проводит приближённый аналог ТВ-игры "Угадай мелодию". 
Написан с использованием библиотеки [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI).

### Особенности:

* ведёт диалог с новыми игроками;
* количество попыток в игре от 5 до 8;
* собирает статистику по каждому игроку.

### Действия в игре:
  
  Игроку предлагаются категории на выбор:
  ![f](https://github.com/Padking/tgbot/blob/master/screenshots/cat.jpg)
  
  
  Далее выбор ноты:
  
  ![s](https://github.com/Padking/tgbot/blob/master/screenshots/note.jpg)
  
  Затем, выбор одного из вариантов ответа:
  ![t](https://github.com/Padking/tgbot/blob/master/screenshots/ans.jpg)
    
### Требования к окружению:

* Python 3.7 и выше;
* Linux/Windows;

### Запуск:

1. $ mkdir my_bot # создание каталога проекта,
2. $ cd my_bot # переход в созданный каталог,
3. поместить bot.py и остальные файлы репозитория в созданный каталог,
4. создать файл ".env" и поместить токен бота, полученный у [@BotFather](https://t.me/botfather),
5. $ python3 -m venv venv # создание каталога виртуального окружения,
6. source venv/bin/activate # активация виртуального окружения,
7. pip install -r requirements.txt # установка зависимостей,
8. deactivate # деактивация виртуального окружения,
9. chmod +x bot.py # наделение файла правами на исполнение,
10. $ ./bot.py # исполнение скрипта
11. /test # получение file_id музыкальных композиций в чат с ботом
12. поместить полученные file_id в одноимённую графу БД



