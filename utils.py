# -*- coding: utf-8 -*-

import random
import shelve
from telebot import types
from telebot.types import InlineKeyboardMarkup, Message
import config
from config import database_name, shelve_name
from SQLighter import SQLighter




def set_user(chat_id: int, chosen_category: 'str'=None, estimated_answer: 'str'=None, attempt_num: 'int'=None, cat_kb: 'InlineKeyboardMarkup'=None, price: 'int'=None):
    """ Записывает информацию для выполнения попытки в туре (игре)
    
    :param chat_id: id пользователя
    :param chosen_category: музыкальная категория, выбранная пользователем
    :param estimated_answer: правильный ответ, который должен быть получен от пользователя (берётся из SQLlite)
    :param attempt_num: параметр-имитатор скорости тура (игры) при условии одного и того же количества попыток, заданных в основном скрипте (bot.py)
    :param cat_kb: клава с категориями
    :param price: цена ноты
    """
    with shelve.open(shelve_name) as storage:
        if chosen_category:
            storage["cat_" + str(chat_id)] = chosen_category
        elif estimated_answer:
            storage["est_ans_" + str(chat_id)] = estimated_answer
        elif attempt_num:
            storage["att_" + str(chat_id)] = storage.get("att_" + str(chat_id), 0) + attempt_num
        elif cat_kb:
            storage["cat_kb_" + str(chat_id)] = cat_kb
        elif price:
            storage["price_" + str(chat_id)] = price

        
def set_user_cats_and_notes(chat_id, cat_name: str, attincat: 'int, bool, None', note_kb: 'InlineKeyboardMarkup'=None):
    """ Записывает таблицу "категории-ноты" в начале каждого тура (игры) в виде: 
    {chat_id: [   { cat_name: [note_kb, 0] }    ]  }, 
    где 0 - начальное количество нот, разыгранных в пределах категории

    Обновляет количество разыгранных нот в пределах категории

    Обновляет клаву с нотами

    :param cat_name: имя категории
    :param attincat: количество разыгранных нот в пределах категории, может принимать 3 типа значений
    :param note_kb: объект-клавиатуры
    """
    with shelve.open(shelve_name) as storage:
        if attincat == 0: # игра началась
            bunch = storage.get("notes_" + str(chat_id), list())
            bunch += [{cat_name: [note_kb, 0]}]
            storage["notes_" + str(chat_id)] = bunch
        elif attincat: # одна нота в пределах категории разыграна
            bunch = storage["notes_" + str(chat_id)]
            for voc in bunch: # цикл осуществляет перезапись значения словаря с определённый ключом
                for key in voc.keys():
                    if key == cat_name:
                        couple = voc[cat_name]
                        couple[1] += 1
                        voc[cat_name] = couple
                        break
            storage["notes_" + str(chat_id)] = bunch
        elif attincat is None: # пользователь выбрал ноту, нужно обновить клаву с нотами
            bunch = storage["notes_" + str(chat_id)]
            for voc in bunch:
                for key in voc.keys():
                    if key == cat_name:
                        couple = voc[cat_name]
                        couple[0] = note_kb
                        voc[cat_name] = couple
                        break
            storage["notes_" + str(chat_id)] = bunch


def set_user_text(chat_id, cat_name: str, text: list, sign: bool):
    with shelve.open(shelve_name) as storage:
        if sign is True: # игра началась
            bunch = storage.get("text_" + str(chat_id), list())
            bunch += [{cat_name: text}]
            storage["text_" + str(chat_id)] = bunch
        elif sign is False:
            bunch = storage["text_" + str(chat_id)]
            for voc in bunch:
                for key in voc.keys():
                    if key == cat_name:
                        voc[cat_name] = text
                        break
            storage["text_" + str(chat_id)] = bunch


def set_user_callback(chat_id, cat_name: str, call_text: list, sign: bool):
    """ Записывает текст для параметра callback_data типа InlineKeyboardButton в формате:
    {chat_id: [   { cat_name: call_text }    ]  }

    :param cat_name: имя категории
    :param call_text: [(имя ноты, цена, пор. №), ..]
    :param sign: флаг
    """
    with shelve.open(shelve_name) as storage:
        if sign is True: # тур начался
            bunch = storage.get("call_" + str(chat_id), list())
            bunch += [{cat_name: call_text}]
            storage["call_" + str(chat_id)] = bunch
        elif sign is False: # тур продолжается, запрос на обновление хранилища
            bunch = storage["call_" + str(chat_id)]
            for voc in bunch:
                for key in voc.keys():
                    if key == cat_name:
                        voc[cat_name] = call_text
                        break
            storage["call_" + str(chat_id)] = bunch


def set_user_one_note_choise(chat_id, sign: bool):
    """ Устанавливает право выбора только одной ноты после отправки клавы с нотами

    :param sign: флаг
    """
    with shelve.open(shelve_name) as storage:
        if sign is True: # игра началась или закончилась попытка
            storage["ones_" + str(chat_id)] = sign
        elif sign is False: # запрос на обновление хранилища в случае выбора неразыгранной ноты (ожидаемый выбор пользователя)
            storage["ones_" + str(chat_id)] = sign



def get_user(chat_id: int, chosen_category: 'bool'=None, estimated_answer: 'bool'=None, attempt_num: 'bool'=None, cat_kb: 'bool'=None, price: 'bool'=None):
    """ Предоставляет информацию для осуществления текущей и очередной попытки

    :param chosen_category: музыкальная категория, выбранная пользователем
    :param estimated_answer: правильный ответ, который должен быть получен от пользователя (берётся из SQLlite)
    :param attempt_num: параметр-имитатор скорости тура (игры) при условии одного и того же количества попыток, заданных в основном скрипте (bot.py)
    :param cat_kb: клава с категориями
    :param price: цена ноты
    """
    with shelve.open(shelve_name) as storage:
        if chosen_category:
            category = storage["cat_" + str(chat_id)]
            return category
        elif estimated_answer:
            est_answer = storage["est_ans_" + str(chat_id)]
            return est_answer
        elif attempt_num:
            attempts = storage["att_" + str(chat_id)]
            return attempts
        elif cat_kb:
            cat_kb = storage["cat_kb_" + str(chat_id)]
            return cat_kb
        elif price:
            price = storage["price_" + str(chat_id)]
            return price


def get_user_cats_and_notes(chat_id, cat_name: str):
    """ Возвращает клаву с нотами и количеством попыток в пределах категории в виде: 
    {chat_id: [   { cat_name: [note_kb, 0] }    ]  }

    :param cat_name: имя категории
    """
    with shelve.open(shelve_name) as storage:
        for voc in storage["notes_" + str(chat_id)]:
            if cat_name in voc.keys():
                note_kb_and_attincat = voc[cat_name] 
                return note_kb_and_attincat


def get_user_text(chat_id, cat_name: str):
    """ Возвращает маркировку для кнопок с нотами в виде:
    [(. ,), ..]

    :param cat_name: имя категории
    """
    with shelve.open(shelve_name) as storage:
        for voc in storage["text_" + str(chat_id)]:
            if cat_name in voc.keys():
                note = voc[cat_name]
                return note


def get_user_callback(chat_id, cat_name: str):
    """ Возвращает значение паретра callback_data в виде:
    [(. , . , .), ..]

    :param cat_name: имя категории
    """
    with shelve.open(shelve_name) as storage:
        for voc in storage["call_" + str(chat_id)]:
            if cat_name in voc.keys():
                note_name_price_ind = voc[cat_name]
                return note_name_price_ind


def get_user_one_note_choise(chat_id):
    """ Возвращает статус права выбора ноты
    если False, значит выбор ноты сделан и на се попытки пользователя выбрать ещё одну ноту не будет реакции от бота
    """
    with shelve.open(shelve_name) as storage:
        status = storage["ones_" + str(chat_id)]
        return status


def delete_for_reset(chat_id):
    """ Удаляет все ключи из хранилища.
    Используется при отправке команды /rst или при очередной игре пользователя
    """
    with shelve.open(shelve_name) as storage:
        try:
            del storage["cat_kb_" + str(chat_id)]
        except:
            pass
        try:
            del storage["text_" + str(chat_id)]
        except:
            pass
        try:
            del storage["call_" + str(chat_id)]
        except:
            pass
        try:
            del storage["notes_" + str(chat_id)]
        except:
            pass
        try:
            del storage["cat_" + str(chat_id)]
        except:
            pass
        try:
            del storage["att_" + str(chat_id)]
        except:
            pass
        try:
            del storage["est_ans_" + str(chat_id)]
        except:
            pass
        try:
            del storage["price_" + str(chat_id)]
        except:
            pass


def finish_user(chat_id, tour: 'bool'=None):
    """ Подготавливает пользователя к следующей попытке или игре

    :param attempt: признак завершения попытки в туре (игре)
    :param tour: признак игры или попытки
    """
    with shelve.open(shelve_name) as storage:
        if tour is False: # попытка
            del storage["cat_" + str(chat_id)]
            del storage["est_ans_" + str(chat_id)]
            del storage["price_" + str(chat_id)]
        elif tour is True:
            del storage["att_" + str(chat_id)]
            del storage["cat_kb_" + str(chat_id)]
            del storage["notes_" + str(chat_id)]
            del storage["text_" + str(chat_id)]
            del storage["call_" + str(chat_id)]


def encode_notes(*args, items=None):
    """Кодирует имя ноты (исполнитель + трек) в виде: 1-е два символа исполнителя + последние два символа трека

    :param args: ((имя ноты, цена), ..)
    :return items: [(имя ноты, цена, пор. №), ..]
    """
    items = items or []
    for i, tup in enumerate(args):
        note, price = tup
        note = note[:2] + note[-2:len(note) + 1]
        tup = (note, price, i,)
        items.append(tup)
    return items


def modify_params(info: list, par_name_1: tuple, par_name_2: tuple):
    """ Изменяет содержимое параметров par_name_1 & par_name_2 по правилу:
    маркировку нажатой кнопки "Нота 1" на её цену
    1-ый элемент свойства call.data объекта CallbackQuery на "Нота 1"

    :param info: информация о разыгрываемой ноте
    :param par_name_1: аналог параметра 'text' для объекта InlineKeyboardButton
    :param par_name_2: аналог параметра 'callback_data' для объекта InlineKeyboardButton
    :return: кортеж в виде (    (   ('Нота 1', ), ('20')    ),      (    ('имя ноты', 'цена', ), ('Нота 2', )    )  )
    """
    a = info[0] # имя ноты или "Нота 1"
    b = info[1] # цена ноты
    c = info[2] # порядковый номер
    modified_par_name_1 = [(b,) if i == int(c) else par_1 for i, par_1 in enumerate(par_name_1)]
    modified_par_name_2 = [tuple("{}, {}, {}".format(*par_name_1[i], par_2[1], par_2[2]).split(',')) if i == int(c) else par_2 for i, par_2 in enumerate(par_name_2)]
    return modified_par_name_1, modified_par_name_2


def generate_inline_markup(text: list, c_data: list, category: 'bool'=None, items=None,):
    """ Создаёт инлайн-клавиатуру для выбора категорий или нот

    :param text: 
        - [(имя категории,), ..] - для категорий
        - [(Нота 1), ..] - для нот
    :param c_data: 
        - [(имя категории,), ..] - для категорий
        - [(имя ноты, цена, пор. №), ..] - для нот
    :param category: признак - создавать для категорий или для нот
    :param items: список с колбэк-кнопками
    :return keyboard: объект инлайн-клавиатуры
    """
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    items = items or []
    if category:
        items = [types.InlineKeyboardButton("{0}".format(*text[_]), callback_data="{0}".format(*c_data[_])) for _ in range(len(text))]
        for item in items:
            keyboard.add(item)
    else: # если ноты
        items = [types.InlineKeyboardButton("{0}".format(*text[_]), callback_data="{0}, {1}, {2}".format(*c_data[_])) for _ in range(len(text))]
        keyboard.row(*items)
    return keyboard


def generate_markup(right_answer, wrong_answers, list_items=None):
    """ Создаёт кастомную клавиатуру для выбора ответа

    :param right_answer: правильный ответ
    :param wrong_answers: набор неправильных ответов
    :return: объект кастомной клавиатуры
    """
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    # Склеиваем правильный ответ с неправильными
    all_answers = '{},{}'.format(right_answer, wrong_answers)
    # Создаём список и записываем в него все элементы
    list_items = list_items or []
    for item in all_answers.split(','):
        list_items.append(item)
    random.shuffle(list_items)
    # Заполняем разметку перемешанными элементами
    for item in list_items:
        markup.add(item)
    return markup


def choice_random_message(k, d=config.game_messages):
    """ Выбирает случайное сообщение согласно "точке" в игре

    :param k: ключ словаря = "точке"
    :param d: словарь, из которого делается выбор
    :return: сообщение - str
    """
    msg_list = d[k]
    msg = random.choice(msg_list)
    return msg


# Служебные функции

def get(chat_id, notes_=True):
    """ Служебная функция, в основном скрипте не использется
    """
    with shelve.open(shelve_name) as storage:
        if notes_:
            return storage["notes_" + str(chat_id)]


def delete(chat_id, notes_=True):
    """ Служебная функция, в основном скрипте не использется
    """
    with shelve.open(shelve_name) as storage:
        if notes_:
            del storage["cat_kb_" + str(chat_id)]
            del storage["notes_" + str(chat_id)]
            del storage["text_" + str(chat_id)]
            del storage["call_" + str(chat_id)]