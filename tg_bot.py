import sqlite3
import time

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

from collections import Counter
import prettytable as pt

from config import TG_TOKEN, TG_PAYMENTS_TOKEN, SUPER_ADMIN_ID, bot, PAYMENTS_TOKEN
from database_functions import insert_user_to_db, check_password, get_dishes_list
from admins import check_rights, check_admins, super_admin, add_id, dict_admins


# bot = telebot.TeleBot(TG_TOKEN)
# PAYMENTS_TOKEN = TG_PAYMENTS_TOKEN

menu = ['Бургеры🍔', 'Картофель🍟', 'Снеки🥓', 'Соусы🥫', 'Напитки🥤', 'Десерты🍧']

user_data = {}
user_order = {}


def menu_kb():
    kb = InlineKeyboardMarkup()
    for dish in menu:
        btn = InlineKeyboardButton(text=dish, callback_data='1' + dish)
        kb.add(btn)
    return kb


def make_table(dct: dict):
    """ формирует заказ в виде таблицы """
    all_dishes = []
    for key, value in dct.items():
        for i in value:
            all_dishes.append(i)
    smth = Counter(all_dishes)
    table = pt.PrettyTable()
    table.field_names = ['Наименование', 'Количество', 'Цена', 'Сумма']
    table._max_width = {"Наименование": 20}
    table.align['Наименование'] = 'l'
    table.align['Количество'] = 'r'
    table.align['Цена'] = 'r'
    table.align['Сумма'] = 'r'

    name_and_count = []

    for k, v in smth.items():
        name_and_count.append((k, v))

    conn = sqlite3.connect('mcdonalds.db')
    cursor = conn.cursor()
    select_query = """ SELECT name, price FROM Dishes """
    cursor.execute(select_query)
    price_list = cursor.fetchall()

    new_price_list = []
    for i in name_and_count:
        for j in price_list:
            if j[0] == i[0]:
                price_tuple = (j[1][:-1],)
                new_price_list.append(price_tuple)

    res = [(x + y) for x, y in zip(name_and_count, new_price_list)]

    data = []
    for i in res:
        sum_str = str(float(i[1]) * float(i[2]))
        sum_tuple = (sum_str,)
        record = i + sum_tuple
        data.append(record)

    total = 0
    for i in data:
        total += float(i[-1])

    table.add_rows(data)
    table.add_row(['', '', '', ''])
    table.add_row(['', '', 'Итого', f'{total}'])

    text = f'<pre>{table}</pre>'
    return text, total


def make_order_description(order_dishes: dict) -> str:
    """ Просто из словаря с заказами делает красивую строку формата: Блюдо х кол-во """
    all_ordered_dishes = []
    for key, value in order_dishes.items():
        for i in value:
            all_ordered_dishes.append(i)
    smth = Counter(all_ordered_dishes)

    order_description = ''
    for k, v in smth.items():
        order_description += f'{k} x{v}\n'
    return order_description


@bot.callback_query_handler(func=lambda callback: callback.data == 'pay')
def buy(call):
    _, amount = make_table(user_order[call.message.chat.id])
    amount = int(amount * 10)
    print(amount)
    PRICE = LabeledPrice(label="Заказ в McDonald's", amount=amount * 10)

    bot.send_message(call.message.chat.id, text="‼️Белорусские рубли почему-то не хочет пропускать 'BYN', "
                                                "поэтому будут указаны российские 'RYB', но цена посчитана в 'BYN'!")

    bot.send_invoice(call.message.chat.id,
                     title="Заказ в McDonald's",
                     description=make_order_description(user_order[call.message.chat.id]),
                     provider_token=PAYMENTS_TOKEN,
                     currency='rub',
                     # photo_url='',
                     # photo_width=415,
                     # photo_height=235,
                     # photo_size=415,
                     is_flexible=False,
                     prices=[PRICE],
                     start_parameter='mcdonalds-order',
                     invoice_payload='test-invoice-payload')


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    print('successful_payment')
    bot.send_message(message.chat.id,
                     f'Платёж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} прошёл успешно\n'
                     'Благодарим вас за заказ!\n'
                     'Заказ приедет к вам в течение 30-35 мин\n'
                     'Приятного аппетита !!!')
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(text='Да', callback_data='review+'),
        InlineKeyboardButton(text='Нет', callback_data='review-')
    )
    time.sleep(2)
    bot.send_message(message.chat.id, text='Спустя 2-3 часа после заказа...')
    time.sleep(2)
    bot.send_message(message.chat.id, text='Нам важно получить <b>Ваш отзыв от "блюдах", которые Вы заказали.</b>\n'
                                           'Ваше мнение поможет другим клиентам сделать выбор\n'
                                           'Также вы получите скидку 15% на свой следующий заказ)\n'
                                           'Оставить отзыв?', parse_mode='HTML', reply_markup=kb)

def get_review(message):
    review_text = message.text
    print(review_text)
    bot.forward_message(SUPER_ADMIN_ID, message.chat.id, message.message_id)
    bot.send_message(message.chat.id, text='Благодарим Вас за отзыв!')


@bot.message_handler(content_types=["text"])
def start(message):
    if message.text == '/start':
        user_data[message.chat.id] = {}
        user_order[message.chat.id] = {}

        bot.send_message(message.chat.id, text='Для начала небольшой опрос, чтобы, в случае плохого отзыва, я смог тебя найти :)')
        time.sleep(2)
        msg = bot.send_message(message.chat.id, text='Введите пароль - в дальнейшем этакий вход в личный кабинет')
        bot.register_next_step_handler(msg, get_password)
    elif message.text == "":
        bot.send_message(message.chat.id, text='Для начала работы бота необходимо прописать команду /start')

    # ----------------------------------------------------------------------------------------------
    elif message.text == '/check':
        check_admins(message)

    elif message.text == '/admin':  # чисто для проверки
        rights = check_rights(message.from_user.id)
        if rights == True:
            bot.send_message(message.from_user.id, "Вы SuperAdmin, в твоих силах ", reply_markup=super_admin)
        elif rights == False:
            bot.send_message(message.from_user.id, "Вы Admin, вы можете помогать клиентам решать их вопросы ")
        else:
            bot.send_message(message.from_user.id, "К сожалению у вас отсутсвуют права доступа Администатора"
                                                   "Но вы можете приобрести админку всего за 5$ и 99€")

    elif message.text == '/add_admin':
        if check_rights(message.from_user.id) == True:
            msg = bot.send_message(message.from_user.id, "введите id пользователя ")
            bot.register_next_step_handler(msg, add_id)
    # ----------------------------------------------------------------------------------------------

def get_password(message):
    password = message.text
    print(password)

    check_user_in_db = check_password(password)
    if check_user_in_db:
        # name =  как вариант брать из БД
        bot.send_message(message.chat.id, text=f'Тебя я знаю !Привет!', reply_markup=menu_kb())
    else:
        user_data[message.chat.id]['password'] = password
        msg = bot.send_message(message.chat.id, text='Как вас зовут?')
        bot.register_next_step_handler(msg, get_username)


def get_username(message):
    username = message.text
    print(username)
    user_data[message.chat.id]['username'] = username
    msg = bot.send_message(message.chat.id, text="Сколько вам лет?")
    bot.register_next_step_handler(msg, get_userage)


def get_userage(message):
    userage = message.text
    print(userage)
    user_data[message.chat.id]['age'] = userage
    msg = bot.send_message(message.chat.id, text="Ваш телефон? (Формат: +375(ХХ)УУУУУУУ")
    bot.register_next_step_handler(msg, get_phone_number)


def get_phone_number(message):
    phone_number = message.text
    print(phone_number)
    user_data[message.chat.id]['phone'] = phone_number
    msg = bot.send_message(message.chat.id, text="Укажите ваш адрес? Формат: город, улица, дом, подъезд, квартира\n"
                                                 "(Введешь коряво - курьер хер тебя найдёт! В твоих же интересах).")
    bot.register_next_step_handler(msg, get_address)


def get_address(message):
    address = message.text
    user_data[message.chat.id]['address'] = address

    insert_user_to_db(user_data[message.chat.id])
    print("Юзер в базе для юзеров")

    bot.send_message(message.chat.id, text="А теперь номер карты, срок действия, имя держателя и cvc-код")
    time.sleep(2)
    bot.send_message(message.chat.id, text="😂😂😂😂😂😂😂 \nШУЧУ..!")
    time.sleep(2)
    bot.send_message(message.chat.id, text='Вот наше МЕНЮ', reply_markup=menu_kb())

    print(user_data)


@bot.callback_query_handler(func=lambda call: True)
def main_menu_answer(call):
    print(call.data)
    flag = call.data[0]
    data = call.data[1:]

    if flag == '1':
        if data[:-1] == 'Бургеры':
            burgers_kb = InlineKeyboardMarkup()                     # вынести в отдельную функцию?
            dishes_by_categories = get_dishes_list(data[:-1])
            for i in dishes_by_categories:
                btn = InlineKeyboardButton(text=f'{i[0]} - {i[1]}', callback_data='2' + ',' + 'burger' + ',' + i[0])
                burgers_kb.add(btn)
            burgers_kb.add(InlineKeyboardButton(text='Вернуться в меню🔙', callback_data='b'))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Выбирайте 🥰', reply_markup=burgers_kb)

        if data[:-1] == 'Картофель':
            french_fries_kb = InlineKeyboardMarkup()
            dishes_by_categories = get_dishes_list(data[:-1])
            for i in dishes_by_categories:
                btn = InlineKeyboardButton(text=f'{i[0]} - {i[1]}', callback_data='2' + ',' + 'potato' + ',' + i[0])
                french_fries_kb.add(btn)
            french_fries_kb.add(InlineKeyboardButton(text='Вернуться в меню🔙', callback_data='b'))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Выбирайте 🥰', reply_markup=french_fries_kb)

        if data[:-1] == 'Снеки':
            snacks_kb = InlineKeyboardMarkup()
            dishes_by_categories = get_dishes_list(data[:-1])
            for i in dishes_by_categories:
                btn = InlineKeyboardButton(text=f'{i[0]} - {i[1]}', callback_data='2' + ',' + 'snack' + ',' + i[0])
                snacks_kb.add(btn)
            snacks_kb.add(InlineKeyboardButton(text='Вернуться в меню🔙', callback_data='b'))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Выбирайте 🥰', reply_markup=snacks_kb)

        if data[:-1] == 'Соусы':
            sauces_kb = InlineKeyboardMarkup()
            dishes_by_categories = get_dishes_list(data[:-1])
            for i in dishes_by_categories:
                btn = InlineKeyboardButton(text=f'{i[0]} - {i[1]}', callback_data='2' + ',' + 'sauce' + ',' + i[0])
                sauces_kb.add(btn)
            sauces_kb.add(InlineKeyboardButton(text='Вернуться в меню🔙', callback_data='b'))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Выбирайте 🥰', reply_markup=sauces_kb)

        if data[:-1] == 'Напитки':
            drinks_kb = InlineKeyboardMarkup()
            dishes_by_categories = get_dishes_list(data[:-1])
            for i in dishes_by_categories:
                btn = InlineKeyboardButton(text=f'{i[0]} - {i[1]}', callback_data='2' + ',' + 'drink' + ',' + i[0])
                drinks_kb.add(btn)
            drinks_kb.add(InlineKeyboardButton(text='Вернуться в меню🔙', callback_data='b'))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Выбирайте 🥰', reply_markup=drinks_kb)

        if data[:-1] == 'Десерты':
            dessert_kb = InlineKeyboardMarkup()
            dishes_by_categories = get_dishes_list(data[:-1])
            for i in dishes_by_categories:
                btn = InlineKeyboardButton(text=f'{i[0]} - {i[1]}', callback_data='2' + ',' + 'dessert' + ',' + i[0])
                dessert_kb.add(btn)
            dessert_kb.add(InlineKeyboardButton(text='Вернуться в меню🔙', callback_data='b'))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Выбирайте 🥰', reply_markup=dessert_kb)

        if len(user_order[call.message.chat.id].keys()) == 0:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton(text='✅', callback_data='yes'))
            bot.send_message(call.message.chat.id, text='Могу принять заказ?', reply_markup=kb)

    if flag == '2':
        bot.answer_callback_query(callback_query_id=call.id, text="Добавлено!", show_alert=False)
        if call.data.split(',')[1] == 'burger':
            if 'burger' not in user_order[call.message.chat.id]:                 # Вынести в отдельную функцию?
                user_order[call.message.chat.id]['burger'] = [call.data.split(',')[2]]
            else:
                user_order[call.message.chat.id]['burger'].append(call.data.split(',')[2])
            print(user_order)
        if call.data.split(',')[1] == 'potato':
            if 'potato' not in user_order[call.message.chat.id]:
                user_order[call.message.chat.id]['potato'] = [call.data.split(',')[2]]
            else:
                user_order[call.message.chat.id]['potato'].append(call.data.split(',')[2])
            print(user_order)
        if call.data.split(',')[1] == 'snack':
            if 'snack' not in user_order[call.message.chat.id]:
                user_order[call.message.chat.id]['snack'] = [call.data.split(',')[2]]
            else:
                user_order[call.message.chat.id]['snack'].append(call.data.split(',')[2])
            print(user_order)
        if call.data.split(',')[1] == 'sauce':
            if 'sauce' not in user_order[call.message.chat.id]:
                user_order[call.message.chat.id]['sauce'] = [call.data.split(',')[2]]
            else:
                user_order[call.message.chat.id]['sauce'].append(call.data.split(',')[2])
            print(user_order)
        if call.data.split(',')[1] == 'drink':
            if 'drink' not in user_order[call.message.chat.id]:
                user_order[call.message.chat.id]['drink'] = [call.data.split(',')[2]]
            else:
                user_order[call.message.chat.id]['drink'].append(call.data.split(',')[2])
            print(user_order)
        if call.data.split(',')[1] == 'dessert':
            if 'dessert' not in user_order[call.message.chat.id]:
                user_order[call.message.chat.id]['dessert'] = [call.data.split(',')[2]]
            else:
                user_order[call.message.chat.id]['dessert'].append(call.data.split(',')[2])
            print(user_order)

    if call.data == 'yes':
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton(text='Да, верно👍🏻', callback_data='pay'),
            InlineKeyboardButton(text='Измененить✏️', callback_data='change'),
            InlineKeyboardButton(text='Отменить❌', callback_data='cancel')
            )
        table, _ = make_table(user_order[call.message.chat.id])
        bot.send_message(call.message.chat.id, text="ВАШ ЗАКАЗ\n" + table, parse_mode='HTML')
        bot.send_message(call.message.chat.id, text='Все верно?', reply_markup=kb)

    if call.data == 'change':
        ordered_dishes = []
        for key, value in user_order[call.message.chat.id].items():
            for i in value:
                ordered_dishes.append(i)

        kb = InlineKeyboardMarkup()
        for dish in ordered_dishes:
            btn = InlineKeyboardButton(text=dish, callback_data='C' + dish)
            kb.add(btn)
        kb.add(
            InlineKeyboardButton(text='Меню🧾', callback_data='b'),
            InlineKeyboardButton(text='К оплате💳', callback_data='pay')
        )
        bot.send_message(call.message.chat.id, text='Ваш заказ на данный момент.\n\nВыберите, что хотели бы убрать.', reply_markup=kb)

    if flag == 'C':
        bot.answer_callback_query(callback_query_id=call.id, text="Удалено!", show_alert=False)
        user_order_copy = user_order[call.message.chat.id].copy()

        for k, v in user_order_copy.items():
            for i in user_order_copy.keys():
                if i == k and data in v:
                    user_order_copy[i].remove(data)

        ordered_dishes = []
        for key, value in user_order_copy.items():
            for i in value:
                ordered_dishes.append(i)

        if ordered_dishes:
            kb = InlineKeyboardMarkup()
            for dish in ordered_dishes:
                btn = InlineKeyboardButton(text=dish, callback_data='C' + dish)
                kb.add(btn)
            kb.add(
                InlineKeyboardButton(text='Меню🧾', callback_data='b'),
                InlineKeyboardButton(text='К оплате💳', callback_data='pay')
                )
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Ваш заказ на данный момент.\n\nВыберите, что хотели бы убрать.', reply_markup=kb)

        else:
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton(text='Меню🧾', callback_data='b'),
                InlineKeyboardButton(text='Передумал..', callback_data='wait')
                   )
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Слишком много удалил, бро..', reply_markup=kb)

    if call.data == 'cancel':
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton(text='Давай', callback_data='b'),
            InlineKeyboardButton(text='Нет', callback_data='offended')
        )
        photo = open("D:\EXAM\photos\sadness.jpg", 'rb')
        bot.send_photo(call.message.chat.id, photo=photo, caption='Попробуем еще разок?', reply_markup=kb)

    if call.data == 'wait':
        photo = open("D:\EXAM\photos\be_waiting_for.jpg", 'rb')
        bot.send_photo(call.message.chat.id, photo=photo)

    if call.data == 'offended':
        photo = open("D:\EXAM\photos\offended.jpg", 'rb')
        bot.send_photo(call.message.chat.id, photo=photo)

    if call.data == 'review+':
        msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Ваш отзыв👇')
        bot.register_next_step_handler(msg, get_review)

    if flag == 'b':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Наше меню', reply_markup=kb)

# -----------------------------------------------------------------------------------------------------------
#     if flag == "A":  # добавление Админа
#         if check_rights(call.message.chat.id):
#             bot.send_message(call.message.chat.id, "Что бы добавить администратора, введите команду '/add_admin' ")
#
#     if flag == "D":  # список Админов на удаление
#         if check_rights(call.message.chat.id):
#
#             admin_del = InlineKeyboardMarkup()
#             for i, n in dict_admins.items():
#                 admin_del.add(InlineKeyboardButton(n["name"], callback_data="d" + str(i)))
#             bot.send_message(call.message.chat.id, " Кого из администраторов вы хотите удалить? ", reply_markup=admin_del)
#
#     if flag == "d":  # удаление Админа
#         if check_rights(call.message.chat.id):
#             rmk = InlineKeyboardMarkup()
#             rmk.add(InlineKeyboardButton("Да, точно", callback_data="1" + str(data)),
#                     InlineKeyboardButton("Нет, не надо", callback_data="2"))
#             name = dict_admins[str(data)]["name"]
#             bot.send_message(call.message.chat.id, f" Вы точно хотите удалить {name} из списка администраторов? ", reply_markup=rmk)
#
#     elif flag == "1":
#         dict_admins.pop(data)
#         bot.send_message(call.message.chat.id, " Хорошо. Мы удалили его ")
#         check_admins(call.message.chat.id)
#
#     elif flag == "2":
#         bot.send_message(call.message.chat.id, " Хорошо. Не будем ")
#         check_admins(call.message.chat.id)
#
#     elif flag == "E":  # список Админов для изменения их прав
#         if check_rights(call.message.chat.id):
#
#             admin_edit = InlineKeyboardMarkup()
#             for i, n in dict_admins.items():
#                 admin_edit.add(InlineKeyboardButton(n["name"], callback_data="e" + str(i)))
#             bot.send_message(call.message.chat.id, " Права кого из администраторов вы хотите изменить? ", reply_markup=admin_edit)
#
#     elif flag == "e":  # список вариантов изменения прав
#         decision = InlineKeyboardMarkup()
#         decision.add(InlineKeyboardButton(f"Сделать {dict_admins[str(data)]['name']} SuperAdmin'ом? ",
#                                           callback_data="3" + str(data)))
#         decision.add(InlineKeyboardButton(f"Сделать {dict_admins[str(data)]['name']} Admin'ом? ",
#                                           callback_data="4" + str(data)))
#         decision.add(InlineKeyboardButton(f"Удалить {dict_admins[str(data)]['name']} из администраторов? ",
#                                           callback_data="d" + str(data)))
#         bot.send_message(call.message.chat.id, f' Что вы хотите сделать с {dict_admins[str(data)]["name"]} ?',
#                          reply_markup=decision)
#
#     elif flag == "3":  # права SuperAdmin
#         if check_rights(id):
#             dict_admins[str(data)]["rights"] = True
#             bot.send_message(call.message.chat.id, f' Теперь {dict_admins[str(data)]["name"]} - SuperAdmin')
#             check_admins(id)
#
#     elif flag == "4":  # права Admin'а
#         if check_rights(id):
#             dict_admins[str(data)]["rights"] = False
#             bot.send_message(call.message.chat.id, f' Теперь {dict_admins[str(data)]["name"]} - Admin')
#             check_admins(id)

# -----------------------------------------------------------------------------------------------------------

print('ready')
bot.polling()
