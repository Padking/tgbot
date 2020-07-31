# -*- coding: utf-8 -*-
import random
import sqlite3
import telebot
import config



class SQLighter:

    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def select_from_multiple_column(self, criterion: str, cat_name: str, table_name="my_music", column_names=("note_name", "note_price"), note_num=4):
        """ Получаем нужное количество нот с ценами согласно категории

        :param criterion: критерий - имя столбца с категориями
        :param cat_name: значение критерия - имя категории
        :param note_num: количество разыгрываемых нот в пределах категории
        """
        with self.connection:
            return self.cursor.execute(
                    """
                    SELECT DISTINCT {}, {}
                    FROM {}
                    WHERE {} LIKE '%{}%'
                    ORDER BY RANDOM()
                    LIMIT {}""".format(*column_names, table_name, criterion, cat_name, note_num)).fetchall()

    def select_from_single_column(self, category_num: 'int'=None, table_name="my_music", column_name="category_name", note_name: 'str'=None, note_num=None):
        """ Получаем неповторяющиеся имена категорий в случайном порядке для табло
        или неповторяющиеся имена нот в случайном порядке за исключением разыгрываемой ноты для НЕправильных ответов

        :param category_num: количество категорий
        :param note_name: зашифрованное имя ноты
        :param note_num: количество нот = количество нот в пределах категории минус 1
        """
        with self.connection:
            if category_num:
                return self.cursor.execute(
                        """
                        SELECT DISTINCT {} 
                        FROM {}
                        ORDER BY RANDOM()
                        LIMIT {}""".format(column_name, table_name, category_num)).fetchall()
            elif note_num:
                note_name_s = note_name[:2]
                note_name_f = note_name[2:]
                return self.cursor.execute(
                        """
                        SELECT {c_n} 
                        FROM {t_n}
                        WHERE {c_n} NOT LIKE '{0}{1}%%{2}{3}'
                        ORDER BY RANDOM()
                        LIMIT {n_n}""".format(*note_name_s, *note_name_f, c_n=column_name, t_n=table_name, n_n=note_num)).fetchall()

    def select_file_id_and_full_note_name(self, note_name: str, table_name="my_music", column_names=("file_id", "note_name")):
        """ Получаем file_id и полное имя по зашифрованному имени ноты

        :param note_name: зашифрованное имя ноты
        """
        note_name_s = note_name[:2]
        note_name_f = note_name[2:]
        with self.connection:
            return self.cursor.execute(
                    """
                    SELECT {0}, {1}
                    FROM {2}
                    WHERE {1} LIKE '{3}{4}%%{5}{6}' """.format(*column_names, table_name, *note_name_s, *note_name_f)).fetchall()[0]

    def select_for_game_result(self, chat_id, table_name="statistics", column_names=("score", "success", "attempts",)):
        """ Получаем количество баллов, успешных попыток и попыток в игре для вывода статистики по окончанию игры
        """
        with self.connection:
            return self.cursor.execute(
                    """
                    SELECT {}, {}, {}
                    FROM {}
                    WHERE user_id = {}""".format(*column_names, table_name, chat_id)).fetchall()[0]

    def select_for_cmd_stat(self, table_name="statistics", column_names=("ind", "user_id", "real_name", "username", "g_success", "g_attempts", "g_played", "total", "per"), row_count=5, seen=None):
        """ Записывает результаты 3-х запросов в список - последовательность записи важна!

        :param row_count: количество человек, о которых выдаётся инфа
        """
        with self.connection:
            seen = seen or []
            # для вывода 5-ки лучших по баллам
            seen.append(
                self.cursor.execute(
                    """
                    SELECT {ind}, {user_id}, {real_name}, {username}, {total}
                    FROM {table_name}
                    ORDER BY {total} DESC
                    LIMIT {row_count}
                    """.format(ind=column_names[0], user_id=column_names[1], real_name=column_names[2], username=column_names[3], total=column_names[7], table_name=table_name, row_count=row_count)).fetchall()
                )
            # для вывода 5-ки эффективных игроков (min игр при max баллов)
            seen.append(
                self.cursor.execute(
                    """
                    SELECT {ind}, {user_id}, {real_name}, {username}, {total}, {g_played}
                    FROM {table_name}
                    WHERE {g_played} != 0
                    ORDER BY {g_played} ASC, {total} DESC
                    LIMIT {row_count}
                    """.format(ind=column_names[0], user_id=column_names[1], real_name=column_names[2], username=column_names[3], g_played=column_names[6], total=column_names[7], table_name=table_name, row_count=row_count)).fetchall()
                )
            # для вывода лучших по проценту успешных попыток за все игры
            seen.append(
                self.cursor.execute(
                    """
                    SELECT {ind}, {user_id}, {real_name}, {username}, {per}
                    FROM {table_name}
                    ORDER BY {per} DESC
                    LIMIT {row_count}
                    """.format(ind=column_names[0], user_id=column_names[1], real_name=column_names[2], username=column_names[3], per=column_names[8], table_name=table_name, row_count=row_count)).fetchall()
                )
            return seen

    def is_there_user_id(self, chat_id, table_name="statistics", column_name="user_id"):
        """ Проверяем, есть ли пользователь в БД

        :param chat_id: id пользователя
        """
        with self.connection:
            return self.cursor.execute(
                    """
                    SELECT {} 
                    FROM {} 
                    WHERE user_id = {}""".format(column_name, table_name, chat_id)).fetchone()



    def insert_row_about_user(self, message):
        """ Добавляем в таблицу строку о новом пользователе за исключением столбцов:
        - real_name,
        - performer

        :param message: объект Bot API
        """
        with self.connection:
            self.cursor.execute(
                """
                INSERT INTO statistics (user_id, real_name, username, performer, success, g_success, attempts, g_attempts, g_played, score, total, per)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (message.from_user.id, "abra", message.from_user.username, "cada", 0, 0, 0, 0, 0, 0, 0, 0))
        
    def insert_row_about_note(self, f_id, note_n, note_p, category_n):
        """ Добавляем в таблицу строку о ноте
        """
        with self.connection:
            self.cursor.execute("""INSERT INTO my_music (file_id, note_name,
                note_price, category_name) VALUES (?, ?, ?, ?)""", (f_id, note_n, note_p, category_n))



    def update_for_game_stat(self, chat_id, answer_right: 'bool'=True, table_name="statistics", column_names=("success", "attempts", "score",), price=10):
        """ Обновляем ячейки таблицы в течение игры

        :param answer_right: признак ответа, который дал пользователь. True - ответ верный
        """
        with self.connection:
            if answer_right:
                self.cursor.execute(
                    """
                    UPDATE {0} 
                    SET {1} = {1}+1, {2} = {2}+1, {3} = {3}+{4}
                    WHERE user_id = {5}""".format(table_name, *column_names, price, chat_id))
            elif answer_right is False:
                self.cursor.execute(
                    """
                    UPDATE {t_n} 
                    SET {c_n} = {c_n}+1
                    WHERE user_id = {c_i}""".format(t_n=table_name, c_n=column_names[1], c_i=chat_id))

    def update_for_user(self, chat_id, value: str, table_name="statistics", column_name="real_name"):
        """Обновляет ячейку для пользователя в столбец column_name
        :param value: дейсвительное имя пользователя или исполнитель
        """
        with self.connection:
            self.cursor.execute(
                    """
                    UPDATE {}
                    SET {} = '{}'
                    WHERE user_id = {}""".format(table_name, column_name, value, chat_id))

    def update_for_games(self, chat_id, table_name="statistics", column_names=("success", "g_success", "attempts", "g_attempts", "g_played", "score", "total", "per",)):
        """ Обновляем ячейки таблицы
        """
        with self.connection:
            self.cursor.execute(
                """
                UPDATE {t_n} 
                SET {g_s} = {g_s} + {s}, {g_a} = {g_a} + {a}, {g_p} = {g_p} + 1, {total} = {total} + {score}, {per} = ROUND(({g_s} / {g_a})*100)
                WHERE user_id = {c_i}""".format(t_n=table_name, s=column_names[0], g_s=column_names[1], a=column_names[2], g_a=column_names[3], g_p=column_names[4], score=column_names[5], total=column_names[6], per=column_names[7], c_i=chat_id))
            self.cursor.execute(
                """
                UPDATE {t_n} 
                SET {s} = 0, {a} = 0, {score} = 0
                WHERE user_id = {c_i}""".format(t_n=table_name, s=column_names[0], a=column_names[2], score=column_names[5], c_i=chat_id))

    def update_for_incomplete_game(self, chat_id, table_name="statistics", column_names=("success", "attempts", "score")):
        """ Подготовка БД для случая, если игрок не доиграл игру до конца
        """
        with self.connection:
            self.cursor.execute(
                """
                UPDATE {t_n} 
                SET {s} = 0, {a} = 0, {score} = 0
                WHERE user_id = {c_i}""".format(t_n=table_name, s=column_names[0], a=column_names[1], score=column_names[2], c_i=chat_id))



    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.close()


# Вызов методов
# db = SQLighter(config.database_name)
