# -*- coding: utf-8 -*-
import os
import random
import sqlite3
import time
import telebot
from telebot import types
from telebot.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
import config
import dbworker
from SQLighter import SQLighter
import utils



bot = telebot.TeleBot(config.TOKEN)



# Обработчик команды /start
# По этой команде будет начинаться любая игра: для впервые играющего пользователя или в очередной раз
@bot.message_handler(commands=['start'])
def cmd_start(message: Message):
    state = dbworker.get_current_state(message.chat.id)
    print(state)
    if state == config.States.S_ENTER_NAME.value:
        bot.send_message(message.chat.id, "Кажется, кто-то обещал отправить своё имя, но так и не сделал этого :( Жду...")
    elif state == config.States.S_ENTER_PERFORMER.value:
        bot.send_message(message.chat.id, "Кажется, кто-то обещал отправить своего исполнителя, но так и не сделал этого :( Жду...")
    else: # к самому началу действий с ботом (при этом порядковый номер состояния != 0)
        if bool(SQLighter(config.database_name).is_there_user_id(message.chat.id)) is False:
            bot.send_message(message.chat.id, "Добро пожаловать в игру 'Угадай мелодию'!")
            dbworker.set_state(message.chat.id, config.States.S_START.value)
            # Отправляем страницу с помощью
            cmd_help(message)
            # Даём время на прочтение страницы с помощью
            time.sleep(1)
            # Добавляем информацию о пользователе
            SQLighter(config.database_name).insert_row_about_user(message)
            bot.send_message(message.chat.id, "Какой замечательный человек заглянул) Как Вас зовут?")
            dbworker.set_state(message.chat.id, config.States.S_ENTER_NAME.value)
        else: # очередная игра пользователя после оконченной или недоигранной предыдущей
            bot.send_message(message.chat.id, "Рад, что Вы снова в игре! Начинаем")
            # Удаление всех ключей из хранилища
            utils.delete_for_reset(message.chat.id)
            # Здесь обнуление success, attempts, score
            SQLighter(config.database_name).update_for_incomplete_game(message.chat.id)
            categories = SQLighter(config.database_name).select_from_single_column(category_num=4)
            keyboard_c = utils.generate_inline_markup(categories, categories, category=True)
            utils.set_user(message.chat.id, cat_kb=keyboard_c)
            for category in categories:
                note_and_price = SQLighter(config.database_name).select_from_multiple_column("category_name", *category)
                note_price_ind = utils.encode_notes(*note_and_price)
                label_text = [('Нота 1', ), ('Нота 2', ), ('Нота 3', ), ('Нота 4', )]
                utils.set_user_text(message.chat.id, *category, label_text, sign=True)
                utils.set_user_callback(message.chat.id, *category, note_price_ind, sign=True)
                keyboard_n = utils.generate_inline_markup(label_text, note_price_ind)
                utils.set_user_cats_and_notes(message.chat.id, *category, attincat=0, note_kb=keyboard_n)
                print("Будет разыграна категория {} с нотами: {}{}{}{}".format(*category, *note_price_ind))
                print()
            bot.send_message(message.chat.id, f"{utils.choice_random_message('1.6')}", reply_markup=keyboard_c)
            dbworker.set_state(message.chat.id, config.States.S_ENTER_CATEGORY.value)


# Если задан 1-ый вопрос пользователю
# Обработчик 1-го ответа пользователя в диалоге
@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ENTER_NAME.value)
def ask_user_performer(message):
    # Добавляем то имя, каким представился пользователь
    SQLighter(config.database_name).update_for_user(message.chat.id, message.text)
    bot.send_message(message.chat.id, f"Очень приятно, {message.text}. Какой Ваш любимый исполнитель?")
    dbworker.set_state(message.chat.id, config.States.S_ENTER_PERFORMER.value)


# Если задан 2-ой вопрос пользователю
@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ENTER_PERFORMER.value)
# Предлагаем выбрать
def choose_category(message):
    # Добавляем исполнителя, о котором написал пользователь
    SQLighter(config.database_name).update_for_user(message.chat.id, message.text, column_name="performer")
    bot.send_message(message.chat.id, f"{utils.choice_random_message('1.4')} {message.text}")
    time.sleep(1)
    bot.send_message(message.chat.id, f"{utils.choice_random_message('1.5')}")
    # Получаем имена категорий
    categories = SQLighter(config.database_name).select_from_single_column(category_num=4)
    # Создаём клаву с категориями
    keyboard_c = utils.generate_inline_markup(categories, categories, category=True)
    # Сохраняем клаву с категориями на время игры
    utils.set_user(message.chat.id, cat_kb=keyboard_c)
    # Формируем "табло игры" - соответствие 4-х нот конкретной категории
    for category in categories: # попробовать уйти от цикла
        # Получаем 4 ноты с ценами
        note_and_price = SQLighter(config.database_name).select_from_multiple_column("category_name", *category)
        # Подготовка содержимого параметра callback_data объекта InlineKeyboardButton
        note_price_ind = utils.encode_notes(*note_and_price)
        # Запоминаем содержимое параметров text & callback_data
        label_text = [('Нота 1', ), ('Нота 2', ), ('Нота 3', ), ('Нота 4', )]
        utils.set_user_text(message.chat.id, *category, label_text, sign=True)
        utils.set_user_callback(message.chat.id, *category, note_price_ind, sign=True)
        # Создаём клаву с нотами
        keyboard_n = utils.generate_inline_markup(label_text, note_price_ind)
        # Сохраняем клаву с нотами и количеством попыток в пределах категории
        utils.set_user_cats_and_notes(message.chat.id, *category, attincat=0, note_kb=keyboard_n)
    bot.send_message(message.chat.id, f"{utils.choice_random_message('1.6')}", reply_markup=keyboard_c)
    dbworker.set_state(message.chat.id, config.States.S_ENTER_CATEGORY.value)



# Если выбрана категория
@bot.callback_query_handler(func=lambda call: dbworker.get_current_state(call.message.chat.id) == config.States.S_ENTER_CATEGORY.value)
def choose_note(call: CallbackQuery):
    if call.data:
        category_name = call.data # всегда ожидаем имя категории как в БД. Как может быть скомпрометировано?
        # Запоминаем имя категории
        utils.set_user(call.message.chat.id, chosen_category=category_name)
        # Предоставляем право выбора ноты только один раз
        utils.set_user_one_note_choise(call.message.chat.id, sign=True)
        # Восстанавливаем клаву с нотами и количеством игровых попыток в пределах категории
        note_and_attincat = utils.get_user_cats_and_notes(call.message.chat.id, category_name)
        # Проверяем кол-во сыгранных нот в пределах категории
        if note_and_attincat[1] == 4:
            # Если категория разыграна, то пользователь выбирает из присланной ранее клавы
            bot.send_message(call.message.chat.id, f"{utils.choice_random_message('1.6.1')}")
            dbworker.set_state(call.message.chat.id, config.States.S_ENTER_CATEGORY.value)
        else:
            # Удаляем клаву с категориями МОМЕНТАЛЬНО после выбора категории
            bot.delete_message(call.message.chat.id, call.message.message_id)
            # Отправляем клаву с нотами
            keyboard_n = note_and_attincat[0]
            bot.send_message(call.message.chat.id, f"{utils.choice_random_message('1.7')}", reply_markup=keyboard_n)
            dbworker.set_state(call.message.chat.id, config.States.S_ENTER_NOTE.value)


# Если выбрана нота
@bot.callback_query_handler(func=lambda call: dbworker.get_current_state(call.message.chat.id) == config.States.S_ENTER_NOTE.value)
def play_attempt(call: CallbackQuery):
    status = utils.get_user_one_note_choise(call.message.chat.id)
    if call.data and status:
        # Получаем информацию о ноте
        note_info = call.data
        category_name = utils.get_user(call.message.chat.id, chosen_category=True)
        # Проверка выбора разыгранной/неразыгранной ноты:
        note_info = note_info.split(',')
        encoded_note_name = note_info[0]
        # если строка начинается с "Нота", значит нота разыграна
        if note_info[0].startswith("Нота"):
            bot.send_message(call.message.chat.id, f"{utils.choice_random_message('1.7.1')}")
            dbworker.set_state(call.message.chat.id, config.States.S_ENTER_NOTE.value)
        elif len(encoded_note_name) == 4 and len(note_info) == 3: # снижаем вероятность, если вдруг введён подменный текст в callback
            # Устанавливаем запрет на выбор ещё одной ноты пока пользователь ожидает цену выбранной
            utils.set_user_one_note_choise(call.message.chat.id, sign=False)
            # Получаем маркировку и колбэк-текст для всех нот в пределах категории
            text = utils.get_user_text(call.message.chat.id, category_name)
            c_data = utils.get_user_callback(call.message.chat.id, category_name)
            # Преобразуем маркировку и коллбэк-текст для выбранной ноты
            new_text_and_c_data = utils.modify_params(note_info, text, c_data)
            # Генерируем клаву с нотами
            keyboard_n_edited = utils.generate_inline_markup(new_text_and_c_data[0], new_text_and_c_data[1])
            # Сохраняем обновлённый текст для формирования клавы
            utils.set_user_text(call.message.chat.id, category_name, new_text_and_c_data[0], sign=False)
            utils.set_user_callback(call.message.chat.id, category_name, new_text_and_c_data[1], sign=False)
            # Здесь сохраняем в хранилище новый вид клавы
            utils.set_user_cats_and_notes(call.message.chat.id, category_name, attincat=None, note_kb=keyboard_n_edited)
            # Сообщаем цену разыгрываемой ноты пользователю
            bot.edit_message_text("<b>А цена ноты составит..</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML', reply_markup=keyboard_n_edited)
            
            # Получаем file_id и note_name из БД
            price = int(note_info[1])
            # Запоминаем цену выбранной ноты
            utils.set_user(call.message.chat.id, price=price)
            file_id, note_name = SQLighter(config.database_name).select_file_id_and_full_note_name(encoded_note_name)
            # Получаем 3 НЕправильных ответа
            wrong_answers = SQLighter(config.database_name).select_from_single_column(column_name="note_name", note_name=encoded_note_name, note_num=3)
            # Формируем разметку:
            wrong_answers = [n+',' for note in wrong_answers for n in note]
            wrong_answers = "{}{}{}".format(*wrong_answers).strip(',')
            markup = utils.generate_markup(note_name, wrong_answers)
            # Удаляем клаву с нотами после задержки (чтобы пользователь смог увидеть цену)
            time.sleep(1.5)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            # Отправляем аудиофайл с вариантами ответа
            bot.send_voice(call.message.chat.id, file_id, reply_markup=markup)
            # Включаем "игровой режим" - записываем ожидаемый правильный ответ от пользователя
            utils.set_user(call.message.chat.id, estimated_answer=note_name)
            dbworker.set_state(call.message.chat.id, config.States.S_ENTER_ANSWER.value)



# Если пользователь дал ответ, нажав на кнопку клавы или написав текст
@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ENTER_ANSWER.value, content_types=['text']) # фиксируем факт прихода сообщения, если его нет, значит человек не играет (думает над ответом например)
def check_answer(message):
    # Удаляем выбранный вариант ответа
    bot.delete_message(message.chat.id, message.message_id)
    answer = utils.get_user(message.chat.id, estimated_answer=True)
    # Убираем клавиатуру с вариантами ответа
    keyboard_hider = types.ReplyKeyboardRemove()
    # Если ответ правильный/неправильный
    if message.text == answer:
        bot.send_message(message.chat.id, f"{utils.choice_random_message('1.8.1')}", reply_markup=keyboard_hider)
        price = utils.get_user(message.chat.id, price=True)
        SQLighter(config.database_name).update_for_game_stat(message.chat.id, price=price)
    else:
        bot.send_message(message.chat.id, f"{utils.choice_random_message('1.8.2')}", reply_markup=keyboard_hider)
        SQLighter(config.database_name).update_for_game_stat(message.chat.id, answer_right=False)
    # Фиксируем количество сыгранных нот в пределах категории
    category_name = utils.get_user(message.chat.id, chosen_category=True) # перед finish_user!!
    utils.set_user_cats_and_notes(message.chat.id, category_name, attincat=True)
    # Завершаем попытку
    utils.finish_user(message.chat.id, tour=False)
    # Фиксируем количество попыток в игре
    utils.set_user(message.chat.id, attempt_num=1)
    # Если количество попыток:
    # не превышено - продолжаем игру и
    num_of_atts = random.choice(range(5, 8)) # можно первый раз выбрать число случайно, потом вытаскивать его из БД, иначе, значение переменной всегда меняется!!
    if utils.get_user(message.chat.id, attempt_num=True) < num_of_atts:
        # получаем клаву с категориями
        keyboard_c = utils.get_user(message.chat.id, cat_kb=True)
        bot.send_message(message.chat.id, f"{utils.choice_random_message('1.10.1')}", reply_markup=keyboard_c)
        dbworker.set_state(message.chat.id, config.States.S_ENTER_CATEGORY.value)
    else: # превышено - завершаем игру и отправляем
        # сообщение с результатами игры в виде: очки - % угаданных 
        score, success_att, num_of_attempts = SQLighter(config.database_name).select_for_game_result(message.chat.id)
        percent = f"{round(int(success_att)/int(num_of_attempts)*100)}"
        bot.send_message(message.chat.id, "Набранное количество очков: <b>{}</b> \n Успешных попыток <i>{} %</i>".format(score, percent), parse_mode='HTML')
        bot.send_message(message.chat.id, f"{utils.choice_random_message('1.10.2')}")
        utils.finish_user(message.chat.id, tour=True)
        # Подготавливаем БД к следующей игре
        SQLighter(config.database_name).update_for_games(message.chat.id)
        dbworker.set_state(message.chat.id, config.States.S_BEFORE_START.value)


# Предоставляет статистику для пользователя
@bot.message_handler(commands=['statistics'])
def cmd_stat(message):
    stat_text = ""
    players_infos = SQLighter(config.database_name).select_for_cmd_stat() # список 3-х списков
    i = 0
    user_id = message.chat.id
    for key, val in config.stat_.items():
        if key == i:
            title = val
            stat_text += f"<b>{title}</b>\n" # выделяем жирным каждый заголовок
            players_info = players_infos[i] # список кортежей
            for _, p_i in enumerate(players_info):
                if user_id in p_i: # выделяем статистическую инфу для запросившего её пользователя
                    p_i = list(p_i)
                    p_i[0] = _+1 # заменяем ind на, фактически, место в итоговой стат. таблице
                    p_i.remove(user_id)
                    stat_text += "<b>{z}  |  {f}  |  {s}  |  {t}</b>".format(z=p_i[0], f=p_i[1], s=p_i[2], t=p_i[3]) + '\n'
                    continue
                p_i = list(p_i)
                p_i[0] = _+1
                id_in_db = p_i[1]
                p_i.remove(id_in_db)
                stat_text += "{z}  |  {f}  |  {s}  |  {t}".format(z=p_i[0], f=p_i[1], s=p_i[2], t=p_i[3]) + '\n'
        bot.send_message(user_id, stat_text, parse_mode='HTML')
        stat_text = ""
        i += 1


# Страница, формируемая для нового пользователя или по команде /help
@bot.message_handler(commands=['help'])
def cmd_help(message):
    help_text = "Доступные команды для бота: \n"
    for key in config.commands:  # создание страницы, которая описывает команды бота
        help_text += "/" + key + ": "
        help_text += config.commands[key] + "\n"
    bot.send_message(message.chat.id, help_text)


# Страница с описанием игры
@bot.message_handler(commands=['rules'])
def cmd_rules(message):
    bot.send_message(message.chat.id, config.rules_text, parse_mode='HTML')


# По команде /reset будем сбрасывать состояния, возвращаясь к началу диалога
@bot.message_handler(commands=["rst"])
def cmd_reset(message):
    utils.delete_for_reset(message.chat.id)
    bot.send_message(message.chat.id, "Что ж, начнём по-новой. Выберите команду /start")
    dbworker.set_state(message.chat.id, config.States.S_BEFORE_START.value)


@bot.message_handler(commands=['tst'])
def find_file_ids(message: Message):
    for file in os.listdir(r"D:\\Projects_py\\telegBot\\music"):
        if file.split('.')[-1] == 'ogg':
            f = open('music\\'+file, 'rb')
            msg = bot.send_voice(message.chat.id, f, None) # загружаю музыку на сервер Tg через бота
            bot.send_message(message.chat.id, msg.voice.file_id, disable_notification=True, reply_to_message_id=msg.message_id) # получаю ответ от бота в виде file_id
            name_parts = file.split('_')
            # print(msg.voice.file_id)
            # print(name_parts[1])
            # print(random.randrange(10, 40, 10))
            # print(name_parts[2].split('.')[0])
            SQLighter(config.database_name).insert_row_about_note(msg.voice.file_id, name_parts[1], random.randrange(10, 50, 5), name_parts[2].split('.')[0])
        time.sleep(3) # приостанавливаю выполнение программы на заданное время (сек)


if __name__ == '__main__':
    bot.infinity_polling() # none_stop=True - опрашивать всегда, interval - между опросами bot.infinity_polling() - можно попробовать так