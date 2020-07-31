# -*- coding: utf-8 -*-

from vedis import Vedis
import config



def get_current_state(user_id):
    """ Получаем "состояние" пользователя
    """
    with Vedis(config.db_file) as db:
        try:
            return db[user_id].decode() # если используется Vedis версии ниже, чем 0.7.1, то .decode() НЕ НУЖЕН
        except KeyError:  # если такого ключа почему-то не оказалось
            return config.States.S_BEFORE_START.value


def set_state(user_id, value):
    """ Сохраняем текущее "состояние" пользователя в базу
    """
    with Vedis(config.db_file) as db:
        try:
            db[user_id] = value
            return True
        except:
            
            return False