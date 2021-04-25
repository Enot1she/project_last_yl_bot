# -*- coding: utf-8 -*-

import json
import logging
import os
import random
import sqlite3
import time
from asyncio import sleep

from aiogram import Bot, Dispatcher, executor

from config import *

logging.basicConfig(level=logging.INFO)

bot = Bot(token="1627320066:AAEah-vfuPADJlDmIK4zZEMnoZR_hkqhjLI")
dp = Dispatcher(bot)

con = sqlite3.connect('db.sqlite', check_same_thread=False)
cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS Users (
    uid INTEGER PRIMARY KEY,
    action TEXT,
    total_solved INTEGER,
    correctly_solved INTEGER,
    selected_exam TEXT,
    problems_stat TEXT
)""")

users = {}
race = {
    '1': {'users': [], 'problems': []},
    '2': {'users': [], 'problems': []},
    '3': {'users': [], 'problems': []}
}


def get_user(uid):
    return cur.execute(f'SELECT * FROM Users WHERE uid = {uid}').fetchone()


def add_user(uid):
    user = get_user(uid)
    if user is None:
        cur.execute(f"""INSERT INTO Users VALUES (
            {uid},
            '',
            0,
            0,
            '1',
            ''
        )""")
        con.commit()
        edit_user(uid, 'problems_stat', '{}')
        user = get_user(uid)
    return user


def edit_user(uid, key, value):
    if isinstance(value, str):
        value = f"'{value}'"
    cur.execute(f'UPDATE Users SET {key} = {value} WHERE uid = {uid}')
    con.commit()


def get_problems(exam='1'):
    path = './problems'
    exams = next(os.walk(path))[1]
    if exam in exams:
        path += f'/{exam}'
        ret = set()
        problems = next(os.walk(path))[1]
        for problem in problems:
            path_ = f'{path}/{problem}'
            problems_ = next(os.walk(path_))[1]
            ret.update(set([f'{path_}/{i}' for i in problems_]))
        return list(ret)


def get_random_problem(exam='1', return_path=False, exception=None):
    if exception is None:
        exception = set()
    ret = get_problems(exam=exam)
    problems = list(set(ret) - set(exception))
    if not problems:
        return
    problem = random.choice(problems)
    path = problem + '/'
    with open(path + '3.txt') as f:
        answer = f.read()
    if return_path:
        return InputFile(path + '1.png'), InputFile(path + '2.png'), answer, problem
    return InputFile(path + '1.png'), InputFile(path + '2.png'), answer


def get_smart_problem(stat, exam='1', return_path=False, exception=None):
    if exception is None:
        exception = set()
    if random.randint(1, 100) > 33:
        return get_random_problem(exam=exam, return_path=return_path, exception=exception)

    problems = get_problems(exam=exam)
    ret = {}
    for i in problems:
        a, b = i, i.split('/')[3]
        ret[b] = ret.get(b, []) + [a]
    s = [(k, v[1] / v[0]) for k, v in stat.get(exam, {}).items()]
    if not s:
        return get_random_problem(exam=exam, return_path=return_path, exception=exception)

    s.sort(key=lambda x: x[1])
    s = s[:len(s) // 2 + 1]

    problems_ = []
    for j in s:
        problems_ += [i for i in problems if i.split('/')[3] == j[0]]
    problems = problems_
    problems = list(set(problems) - set(exception))
    if not problems:
        return get_random_problem(exam=exam, return_path=return_path, exception=exception)
    problem = random.choice(problems)
    path = problem + '/'
    with open(path + '3.txt') as f:
        answer = f.read()
    if return_path:
        return InputFile(path + '1.png'), InputFile(path + '2.png'), answer, problem
    return InputFile(path + '1.png'), InputFile(path + '2.png'), answer


def get_problem_by_type(problem, return_path=False, exam='1', exception=None, as_path=False):
    if exception is None:
        exception = set()
    problems = get_problems(exam=exam)
    problems = [i for i in problems if i not in exception and i.split('/')[3] == problem]
    if not problems:
        return
    problem = random.choice(problems)
    path = problem + '/'
    with open(path + '3.txt') as f:
        answer = f.read()
    if return_path:
        if as_path:
            return path + '1.png', path + '2.png', answer, problem
        else:
            return InputFile(path + '1.png'), InputFile(path + '2.png'), answer, problem
    if as_path:
        return path + '1.png', path + '2.png', answer
    else:
        return InputFile(path + '1.png'), InputFile(path + '2.png'), answer


@dp.message_handler(commands=['start'])
async def handler(message: Message):
    id = message.from_user.id
    user = add_user(id)
    if user[1].startswith('virtual') or user[1].startswith('race'):
        return
    await message.answer(f"""Привет!

Я Чат-бот. 😊
Со мной Вы можете подготовиться к тестовой части экзаменов ОГЭ/ЕГЭ.
У меня есть для Вас несколько режимов подготовки:
✅ 1. Умная подготовка. В этом режиме я буду предлагать Вам разные задания, а также буду очень внимательно следить за Вашей статистикой. В процессе умной подготовки будет накапливаться статистика, которая поможет мне чаще предлагать Вам задания на которые ранее был получен неверный ответ. Тем самым, я буду очень стараться улучшить Вашу подготовку по всему спектру заданий.
✅ 2. Решение номера. Этот режим поможет Вам лучше подготовиться к одному конкретному заданию. Таким образом, Вы сможете выравнивать статистику по заданиям которые даются Вам сложнее всего.
✅ 3. Виртуальный экзамен. В этом режиме Вы сможете проверить свои силы, и за два отведенных часа решить всю тестовую часть выбранного экзамена.
✅ 4. Онлайн соревнование. Это соревнование с другими участниками в реальном времени. Я буду предлагать Вам разные задания, а Вы, решая очередное задание, будете наблюдать свой рейтинг.

Инструкция 📝
📌 Чтобы выбрать нужный экзамен воспользуйтесь кнопкой Настройки.
📌 Ответы на все задания — это целое число или десятичная дробь с запятой или точкой в качестве разделителя.

Удачной подготовки!


Выбран экзамен: {EXAMS[user[4]]}""", reply_markup=KEYBOARD, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler()
async def handler(message: Message):
    id, tx = message.from_user.id, message.text
    user = add_user(id)

    if id not in users.keys() or tx == 'e':
        users[id] = {'problems': set()}
        edit_user(id, 'action', '')

    if user[1].startswith('virtual'):
        if '_' in user[1]:
            problem, mid1, mid2 = user[1].split('_')[1:]
            users[id]['virtual_progress'][int(problem)] = tx
            await bot.delete_message(chat_id=id, message_id=message.message_id)
            await bot.delete_message(chat_id=id, message_id=mid1)
            progress, t = users[id]['virtual_progress'], users[id]['virtual_time']
            kb = InlineKeyboardMarkup()
            btns = [InlineKeyboardButton((f'({i + 1})' if progress[i] != '' else str(i + 1)),
                                         callback_data=f'virtual_{i + 1}') for i in range(len(progress))]
            kb.add(*btns)
            kb.add(InlineKeyboardButton('Обновить', callback_data='virtualrefresh'))
            kb.add(InlineKeyboardButton('Завершить экзамен', callback_data='virtualfinish'))
            t = 3600 * 2 - int(time.time() - t)
            h = t // 3600
            m = (t // 60) % 60
            s = t % 60
            if m < 10:
                m = '0' + str(m)
            if s < 10:
                s = '0' + str(s)
            await bot.edit_message_text(chat_id=id, message_id=mid2,
                                        text=f'Оставшееся время: {h}:{m}:{s}\n\n'
                                             f'_Задания можно решать в любом порядке.\n'
                                             f'При необходимости ответ можно отправлять повторно._',
                                        reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

    elif user[1].startswith('race'):
        if '_' in user[1]:
            problem, mid = int(user[1].split('_')[1]), user[1].split('_')[2]
            problem = race[user[4]]['problems'][problem]

            us = race[user[4]]['users']
            x = [i['id'] for i in us].index(id)
            p = us[x]['progress']

            question, solution, answer = race[user[4]]['problems'][p]

            p += 1

            if tx == answer:
                # верно
                race[user[4]]['users'][x]['progress'] += 1
                if p == len(race[user[4]]['problems']):
                    # все решил
                    t = time.time()
                    t = int(t) % 3600
                    m = (t // 60) % 60
                    s = t % 60
                    if m < 10:
                        m = '0' + str(m)
                    if s < 10:
                        s = '0' + str(s)
                    await message.answer(f'Вы завершили соревнование!\nВаш результат: {m}:{s}')
                    return
                mid2 = (await message.answer('Верно!')).message_id
            else:
                await message.answer('Ответ неверный!\nВы покидете соревнование!')
                mid = users[id]['race_mid']
                race[user[4]]['users'].pop(x)
                edit_user(id, 'action', '')
                await bot.delete_message(chat_id=id, message_id=mid)
                return
            question, solution, answer = race[user[4]]['problems'][p]
            mid3 = (await bot.send_photo(chat_id=id, caption=f"""{PROBLEMS_LIST[int(get_user(id)[4]) - 1][p]}
*#{question.split("/")[2]}.{question.split("/")[3]}.{question.split("/")[4]}*""", photo=InputFile(question),
                                         parse_mode=ParseMode.MARKDOWN)).message_id
            edit_user(id, 'action', f'race_{p}_' + str(mid3))
            await bot.delete_message(chat_id=id, message_id=mid)
            await bot.delete_message(chat_id=id, message_id=mid2)
            await bot.delete_message(chat_id=id, message_id=message.message_id)

    elif tx.startswith('/') and tx[1:].isdigit():
        idc = int(tx[1:])
        user = get_user(idc)
        stat = []
        js = json.loads(user[5])
        if user[4] not in js.keys():
            await message.answer('По выбранному экзамену еще нет статистики!\nСначала нужно решить несколько заданий')
            return
        for a, b in js[user[4]].items():
            stat.append((int(a), b[0], b[1]))
        stat.sort(key=lambda x: (x[0], -(x[2] / x[1]), x[1]))
        tx = f'Статистика по экзамену {EXAMS[user[4]]}:\n\n'
        for a, b, c in stat:
            p = PROBLEMS_LIST[int(user[4]) - 1][a - 1]
            tx += f'{p}\n  —   *{c}/{b}*   _({int((c / b) * 100)}%)_\n\n'
        tx += f'\nОбщая статистика:\n\n' \
              f'Верных решений   —    *{user[3]}/{user[2]}*   _({int((user[3] / user[2]) * 100)}%)_'

        await message.answer(tx, parse_mode=ParseMode.MARKDOWN)

    elif tx == 'Умная подготовка':
        users[id]['problems'] = set()
        stat = json.loads(user[5])
        ret = get_smart_problem(stat, exam=user[4], return_path=True)
        if ret is None:
            await message.answer('Задания закончились! Можете попробовать другой режим, или прийти позже')
            edit_user(id, 'action', '')
            users[id]['problems'] = set()
        else:
            question, solution, answer, path = ret
            users[id]['problems'].add(path)
            await bot.send_photo(chat_id=id, caption=f"""{PROBLEMS_LIST[int(user[4]) - 1][int(path.split("/")[3]) - 1]}
*#{path.split("/")[2]}.{path.split("/")[3]}.{path.split("/")[4]}*""", photo=question, parse_mode=ParseMode.MARKDOWN)
            users[id]['current_answer'] = answer
            users[id]['current_solution'] = solution
            edit_user(id, 'action', f'solving_{path.split("/")[3]}_{answer}')

    elif tx == 'Решение номера':
        types = next(os.walk(f'./problems/{user[4]}'))[1]
        types.sort(key=lambda x: int(x))

        btns = [InlineKeyboardButton(i, callback_data=f'select_{i}') for i in types]
        kb = InlineKeyboardMarkup()
        kb.add(*btns)
        ex = EXAMS[user[4]]
        await message.answer(f'Выберите номер задания {ex}\n\n' + PROBLEMS[int(user[4]) - 1], reply_markup=kb)

    elif tx == 'Статистика':
        stat = []
        js = json.loads(user[5])
        if user[4] not in js.keys():
            await message.answer('По выбранному экзамену еще нет статистики!\nСначала нужно решить несколько заданий')
            return
        for a, b in js[user[4]].items():
            stat.append((int(a), b[0], b[1]))
        stat.sort(key=lambda x: (x[0], -(x[2] / x[1]), x[1]))
        tx = f'Статистика по экзамену {EXAMS[user[4]]}:\n\n'
        for a, b, c in stat:
            p = PROBLEMS_LIST[int(user[4]) - 1][a - 1]
            tx += f'{p}\n  —   *{c}/{b}*   _({int((c / b) * 100)}%)_\n\n'
        tx += f'\nОбщая статистика:\n\n' \
              f'Верных решений   —    *{user[3]}/{user[2]}*   _({int((user[3] / user[2]) * 100)}%)_'

        tx += f'\n\nВаш уникальный ID: {id}'

        await message.answer(tx, parse_mode=ParseMode.MARKDOWN)

    elif tx == 'Настройки':
        await message.answer('Выберите экзамен', reply_markup=KEYBOARD_EXAM)

    elif tx == 'Виртуальный экзамен':
        l = len({i.split('/')[3] for i in get_problems(exam=user[4])})
        problems = []
        for i in range(l):
            problems.append(get_problem_by_type(str(i + 1), as_path=True))
        users[id]['virtual_problems'] = problems
        users[id]['virtual_progress'] = [''] * l
        users[id]['virtual_time'] = int(time.time())
        edit_user(id, 'action', 'virtual')

        kb = InlineKeyboardMarkup()
        btns = [InlineKeyboardButton(str(i + 1), callback_data=f'virtual_{i + 1}') for i in range(l)]
        kb.add(*btns)
        kb.add(InlineKeyboardButton('Обновить', callback_data='virtualrefresh'))
        kb.add(InlineKeyboardButton('Завершить экзамен', callback_data='virtualfinish'))
        mid = (await message.answer(
            'Оставшееся время: 2:00:00\n\n_Задания можно решать в любом порядке.\n'
            'При необходимости ответ можно отправлять повторно._',
            reply_markup=kb, parse_mode=ParseMode.MARKDOWN)).message_id

        await sleep(3600 * 2)

        await bot.delete_message(chat_id=id, message_id=mid)
        progress = [i.replace(',', '.') for i in users[id]['virtual_progress']]
        answers = [i[2].replace(',', '.') for i in users[id]['virtual_problems']]
        total, right = user[2:4]
        stat = json.loads(user[5])

        a = b = 0
        tx = ''

        for i in range(len(progress)):
            b += 1
            if progress[i] != '':
                total += 1
                if user[4] not in stat.keys():
                    stat[user[4]] = {}
                if str(i + 1) not in stat[user[4]].keys():
                    stat[user[4]][str(i + 1)] = [0, 0]
                stat[user[4]][str(i + 1)][0] += 1
                if progress[i] == answers[i]:
                    right += 1
                    a += 1
                    stat[user[4]][str(i + 1)][1] += 1
                    tx += f'{i + 1}) ✅\n'
                else:
                    tx += f'{i + 1}) ❌\n'
            else:
                tx += f'{i + 1}) ❌\n'

        edit_user(id, 'problems_stat', json.dumps(stat))
        edit_user(id, 'total_solved', total)
        edit_user(id, 'correctly_solved', right)
        edit_user(id, 'action', '')

        await bot.send_message(id, f'Экзамен завершен!\nРезультат: *{a}/{b}*\n\nРезультаты по заданиям:\n{tx}',
                               reply_markup=KEYBOARD, parse_mode=ParseMode.MARKDOWN)

    elif tx == 'Онлайн соревнование':
        t = time.time()
        t = int(t) % 3600
        y = 3600 - t
        m = (y // 60) % 60
        s = y % 60
        if m < 10:
            m = '0' + str(m)
        if s < 10:
            s = '0' + str(s)
        if t > 3570:
            await message.answer(
                f'Соревнование уже в процессе!\nУспейте к следующему соревнованию, которое начнется через {m}:{s}')
            return

        l = len({i.split('/')[3] for i in get_problems(exam=user[4])})

        if len(race[user[4]]['users']) == 0:
            problems = []
            for i in range(l):
                problems.append(get_problem_by_type(str(i + 1), as_path=True))
            race[user[4]]['problems'] = problems

        race[user[4]]['users'].append({
            'id': id,
            'progress': 0,
        })

        us = race[user[4]]['users']
        us.sort(key=lambda x: -x['progress'])
        x = [i['id'] for i in us].index(id)
        tx = ''
        for i, u in enumerate(us[:3]):
            if u['id'] == id:
                tx += '\n' + str(i + 1) + ' (Вы).\n' + '🟨' * u['progress'] + '⬜️' * (l - u['progress']) + '\n'
            else:
                tx += '\n' + str(i + 1) + '.\n' + '🟨' * u['progress'] + '⬜️' * (l - u['progress']) + '\n'
        if x >= 3:
            tx += '...\n(Вы):\n'
            tx += str(x + 1) + '. ' + '🟨' * us[x]['progress'] + '⬜️' * (l - us[x]['progress']) + '\n'

        kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Обновить', callback_data='racerefresh'),
                                        InlineKeyboardButton('Покинуть соревнование', callback_data='racefinish'))

        mid = (await message.answer(f"""Оставшееся время: {m}:{s}
Участников сейчас: {len(us)}

Онлайн рейтинг:
{tx}""", reply_markup=kb)).message_id

        edit_user(id, 'action', 'race_0')
        users[id]['race_mid'] = mid

        question, solution, answer = race[user[4]]['problems'][0]
        mid = (await bot.send_photo(chat_id=id, caption=f"""{PROBLEMS_LIST[int(get_user(id)[4]) - 1][0]}
*#{question.split("/")[2]}.{question.split("/")[3]}.{question.split("/")[4]}*""", photo=InputFile(question),
                                    parse_mode=ParseMode.MARKDOWN)).message_id
        edit_user(id, 'action', 'race_0_' + str(mid))

    elif user[1].startswith('solving_'):
        problem, answer = user[1].split('_')[1:]
        tx = tx.replace(',', '.')
        answer = answer.replace(',', '.')
        edit_user(id, 'total_solved', user[2] + 1)
        stat = json.loads(user[5])
        if user[4] not in stat.keys():
            stat[user[4]] = {}
        if problem not in stat[user[4]].keys():
            stat[user[4]][problem] = [0, 0]
        stat[user[4]][problem][0] += 1
        if tx == answer:
            edit_user(id, 'correctly_solved', user[3] + 1)
            stat[user[4]][problem][1] += 1
            await bot.send_photo(chat_id=id, caption=f"""Ваш ответ: {tx}
*Правильно* ✅
Правильный ответ: {users[id]['current_answer']}""", photo=users[id]['current_solution'], parse_mode=ParseMode.MARKDOWN)
            ret = get_smart_problem(stat, exam=user[4], return_path=True, exception=users[id]['problems'])
            if ret is None:
                await message.answer('Задания закончились! Можете попробовать другой режим, или прийти позже')
                edit_user(id, 'action', '')
                users[id]['problems'] = set()
            else:
                question, solution, answer, path = ret
                users[id]['problems'].add(path)
                await bot.send_photo(chat_id=id,
                                     caption=f"""{PROBLEMS_LIST[int(user[4]) - 1][int(path.split("/")[3]) - 1]}
*#{path.split("/")[2]}.{path.split("/")[3]}.{path.split("/")[4]}*""", photo=question, parse_mode=ParseMode.MARKDOWN)
                users[id]['current_answer'] = answer
                users[id]['current_solution'] = solution
                edit_user(id, 'action', f'solving_{path.split("/")[3]}_{answer}')
        else:
            await bot.send_photo(chat_id=id, caption=f"""Ваш ответ: {tx}
*Неправильно* ❌
Правильный ответ: {users[id]['current_answer']}""", photo=users[id]['current_solution'], parse_mode=ParseMode.MARKDOWN)
            ret = get_smart_problem(stat, exam=user[4], return_path=True, exception=users[id]['problems'])
            if ret is None:
                await message.answer('Задания закончились! Можете попробовать другой режим, или прийти позже')
                edit_user(id, 'action', '')
                users[id]['problems'] = set()
            else:
                question, solution, answer, path = ret
                users[id]['problems'].add(path)
                await bot.send_photo(chat_id=id,
                                     caption=f"""{PROBLEMS_LIST[int(user[4]) - 1][int(path.split("/")[3]) - 1]}
*#{path.split("/")[2]}.{path.split("/")[3]}.{path.split("/")[4]}*""", photo=question, parse_mode=ParseMode.MARKDOWN)
                users[id]['current_answer'] = answer
                users[id]['current_solution'] = solution
                edit_user(id, 'action', f'solving_{path.split("/")[3]}_{answer}')

        edit_user(id, 'problems_stat', json.dumps(stat))

    elif user[1].startswith('selected_'):
        problem, answer = user[1].split('_')[1:]
        tx = tx.replace(',', '.')
        answer = answer.replace(',', '.')
        edit_user(id, 'total_solved', user[2] + 1)
        stat = json.loads(user[5])
        if user[4] not in stat.keys():
            stat[user[4]] = {}
        if problem not in stat[user[4]].keys():
            stat[user[4]][problem] = [0, 0]
        stat[user[4]][problem][0] += 1
        if tx == answer:
            edit_user(id, 'correctly_solved', user[3] + 1)
            stat[user[4]][problem][1] += 1
            await bot.send_photo(chat_id=id, caption=f"""Ваш ответ: {tx}
*Правильно* ✅
Правильный ответ: {users[id]['current_answer']}""", photo=users[id]['current_solution'], parse_mode=ParseMode.MARKDOWN)
            ret = get_problem_by_type(problem, exam=user[4], return_path=True, exception=users[id]['problems'])
            if ret is None:
                await message.answer('Задания закончились! Можете попробовать другой режим, или прийти позже')
                edit_user(id, 'action', '')
                users[id]['problems'] = set()
            else:
                question, solution, answer, path = ret
                users[id]['problems'].add(path)
                await bot.send_photo(chat_id=id,
                                     caption=f"""{PROBLEMS_LIST[int(user[4]) - 1][int(path.split("/")[3]) - 1]}
*#{path.split("/")[2]}.{path.split("/")[3]}.{path.split("/")[4]}*""", photo=question, parse_mode=ParseMode.MARKDOWN)
                users[id]['current_answer'] = answer
                users[id]['current_solution'] = solution
                edit_user(id, 'action', f'selected_{path.split("/")[3]}_{answer}')
        else:
            await bot.send_photo(chat_id=id, caption=f"""Ваш ответ: {tx}
*Неправильно* ❌
Правильный ответ: {users[id]['current_answer']}""", photo=users[id]['current_solution'], parse_mode=ParseMode.MARKDOWN)
            ret = get_problem_by_type(problem, exam=user[4], return_path=True, exception=users[id]['problems'])
            if ret is None:
                await message.answer('Задания закончились! Можете попробовать другой режим, или прийти позже')
                edit_user(id, 'action', '')
                users[id]['problems'] = set()
            else:
                question, solution, answer, path = ret
                users[id]['problems'].add(path)
                await bot.send_photo(chat_id=id,
                                     caption=f"""{PROBLEMS_LIST[int(user[4]) - 1][int(path.split("/")[3]) - 1]}
*#{path.split("/")[2]}.{path.split("/")[3]}.{path.split("/")[4]}*""", photo=question, parse_mode=ParseMode.MARKDOWN)
                users[id]['current_answer'] = answer
                users[id]['current_solution'] = solution
                edit_user(id, 'action', f'selected_{path.split("/")[3]}_{answer}')

        edit_user(id, 'problems_stat', json.dumps(stat))


@dp.callback_query_handler()
async def process_callback(query: CallbackQuery):
    id, data = query.from_user.id, query.data
    await query.answer()
    if data.startswith('select_'):
        users[id]['problems'] = set()
        t = data.split('_')[1]
        user = get_user(id)
        question, solution, answer, path = get_problem_by_type(t, exam=user[4], return_path=True)
        users[id]['problems'].add(path)
        await bot.send_photo(chat_id=id, caption=f"""{PROBLEMS_LIST[int(user[4]) - 1][int(path.split("/")[3]) - 1]}
*#{path.split("/")[2]}.{path.split("/")[3]}.{path.split("/")[4]}*""", photo=question, parse_mode=ParseMode.MARKDOWN)
        users[id]['current_answer'] = answer
        users[id]['current_solution'] = solution
        edit_user(id, 'action', f'selected_{path.split("/")[3]}_{answer}')
        await bot.delete_message(chat_id=id, message_id=query.message.message_id)
    elif data.startswith('exam_'):
        exam = data.split('_')[1]
        ex = EXAMS[exam]
        edit_user(id, 'selected_exam', exam)
        await bot.edit_message_text(text=f'Выбран экзамен: {ex}', chat_id=id, message_id=query.message.message_id)

    elif data == 'virtualrefresh':
        progress, t = users[id]['virtual_progress'], users[id]['virtual_time']
        kb = InlineKeyboardMarkup()
        btns = [
            InlineKeyboardButton(f'({i + 1})' if progress[i] != '' else str(i + 1), callback_data=f'virtual_{i + 1}')
            for i in range(len(progress))]
        kb.add(*btns)
        kb.add(InlineKeyboardButton('Обновить', callback_data='virtualrefresh'))
        kb.add(InlineKeyboardButton('Завершить экзамен', callback_data='virtualfinish'))
        t = 3600 * 2 - int(time.time() - t)
        h = t // 3600
        m = (t // 60) % 60
        s = t % 60
        if m < 10:
            m = '0' + str(m)
        if s < 10:
            s = '0' + str(s)
        await bot.edit_message_text(chat_id=id, message_id=query.message.message_id,
                                    text=f'Оставшееся время: {h}:{m}:{s}\n\n_Задания можно решать в любом порядке.\n'
                                         f'При необходимости ответ можно отправлять повторно._',
                                    reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

    elif data == 'virtualfinish':
        await bot.delete_message(chat_id=id, message_id=query.message.message_id)
        progress = [i.replace(',', '.') for i in users[id]['virtual_progress']]
        answers = [i[2].replace(',', '.') for i in users[id]['virtual_problems']]
        user = get_user(id)
        total, right = user[2:4]
        stat = json.loads(user[5])

        a = b = 0
        tx = ''

        for i in range(len(progress)):
            b += 1
            if progress[i] != '':
                total += 1
                if user[4] not in stat.keys():
                    stat[user[4]] = {}
                if str(i + 1) not in stat[user[4]].keys():
                    stat[user[4]][str(i + 1)] = [0, 0]
                stat[user[4]][str(i + 1)][0] += 1
                if progress[i] == answers[i]:
                    right += 1
                    a += 1
                    stat[user[4]][str(i + 1)][1] += 1
                    tx += f'{i + 1}) ✅\n'
                else:
                    tx += f'{i + 1}) ❌\n'
            else:
                tx += f'{i + 1}) ❌\n'

        edit_user(id, 'problems_stat', json.dumps(stat))
        edit_user(id, 'total_solved', total)
        edit_user(id, 'correctly_solved', right)
        edit_user(id, 'action', '')

        await bot.send_message(id, f'Экзамен завершен!\nРезультат: *{a}/{b}*\n\nРезультаты по заданиям:\n{tx}',
                               reply_markup=KEYBOARD, parse_mode=ParseMode.MARKDOWN)

    elif data.startswith('virtual_'):
        problem = int(data.split('_')[1]) - 1
        progress = users[id]['virtual_progress']
        question, solution, answer = users[id]['virtual_problems'][problem]
        mid = (await bot.send_photo(chat_id=id, caption=f"""{PROBLEMS_LIST[int(get_user(id)[4]) - 1][problem]}
*#{question.split("/")[2]}.{question.split("/")[3]}.{question.split("/")[4]}*

{("Ваш ответ: " + progress[problem] if progress[problem] else "")}""", photo=InputFile(question),
                                    parse_mode=ParseMode.MARKDOWN)).message_id
        edit_user(id, 'action', 'virtual_' + str(problem) + '_' + str(mid) + '_' + str(query.message.message_id))

    elif data == 'racerefresh':
        t = time.time()
        t = int(t) % 3600
        y = 3600 - t
        m = (y // 60) % 60
        s = y % 60
        if m < 10:
            m = '0' + str(m)
        if s < 10:
            s = '0' + str(s)

        user = get_user(id)
        l = len({i.split('/')[3] for i in get_problems(exam=user[4])})
        mid = users[id]['race_mid']

        us = race[user[4]]['users']
        us.sort(key=lambda x: -x['progress'])
        x = [i['id'] for i in us].index(id)
        tx = ''
        for i, u in enumerate(us[:3]):
            if u['id'] == id:
                tx += '\n' + str(i + 1) + ' (Вы).\n' + '🟨' * u['progress'] + '⬜️' * (l - u['progress']) + '\n'
            else:
                tx += '\n' + str(i + 1) + '.\n' + '🟨' * u['progress'] + '⬜️' * (l - u['progress']) + '\n'
        if x >= 3:
            tx += '...\n(Вы):\n'
            tx += str(x + 1) + '. ' + '🟨' * us[x]['progress'] + '⬜️' * (l - us[x]['progress']) + '\n'

        kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Обновить', callback_data='racerefresh'),
                                        InlineKeyboardButton('Покинуть соревнование', callback_data='racefinish'))

        await bot.edit_message_text(chat_id=id, message_id=mid, text=f"""Оставшееся время: {m}:{s}
Участников сейчас: {len(us)}

Онлайн рейтинг:
{tx}""", reply_markup=kb)

    elif data == 'racefinish':
        user = get_user(id)
        x = [i['id'] for i in race[user[4]]['users']]
        if id not in x:
            return
        x = x.index(id)
        mid = users[id]['race_mid']
        race[user[4]]['users'].pop(x)
        edit_user(id, 'action', '')
        await bot.delete_message(chat_id=id, message_id=mid)
        await bot.send_message(chat_id=id, text='Вы покинули соревнование! Результат сброшен!')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
