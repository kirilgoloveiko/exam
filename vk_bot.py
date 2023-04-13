import json
import sqlite3
from collections import Counter

from vk_api import VkApi
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from database_functions import check_password, insert_user_to_db
from config import VK_TOKEN, VK_GROUP_ID, VK_API_VERSION


# Общие
GROUP_ID = VK_GROUP_ID
TOKEN = VK_TOKEN
API_VERSION = VK_API_VERSION

# виды callback-кнопок
CALLBACK_TYPES = ("show_snackbar", "open_link")

user_data = {}
user_order = {}

category_list = ['Бургеры🍔', 'Картофель🍟', 'Снеки🥓', 'Соусы🥫', 'Напитки🥤', 'Десерты🍧']


def dishes_by_categories(category_list: list) -> dict:
    conn = sqlite3.connect('mcdonalds.db')
    cursor = conn.cursor()
    d = {}
    for cat in category_list:
        query = f""" select name from Dishes
                     join DishCategories
                        on Dishes.category_id = DishCategories.category_id
                     where category_name = '{cat[:-1]}' """
        cursor.execute(query)
        list_of_tuples = cursor.fetchall()
        dishes = []
        for tuple in list_of_tuples:
            for i in tuple:
                dishes.append(i)
        d[cat[:-1]] = dishes
    return d


def name_and_price_for_dish_btn(category: str):
    conn = sqlite3.connect('mcdonalds.db')
    cursor = conn.cursor()
    dishes_name_and_price = []
    query = f""" select name, price from Dishes
                join DishCategories
                    on Dishes.category_id = DishCategories.category_id
                where category_name = '{category}' """
    cursor.execute(query)
    list_of_tuples = cursor.fetchall()
    for i in list_of_tuples:
        btn_text = f'{i[0]} - {i[1]}'
        dishes_name_and_price.append(btn_text)
    return dishes_name_and_price


def keyb_gen(list, num, flag, ind=None, fix_pos=5):
    kb = VkKeyboard(inline=True)

    if fix_pos * (num + 1) > len(list):
        t = len(list)
    else:
        t = fix_pos * (num + 1)

    for i in range(fix_pos * num, t):
        kb.add_button(label=list[i], color=VkKeyboardColor.SECONDARY, payload={"type": "text"})
        kb.add_line()

    if num == 0 and t != len(list):
        kb.add_callback_button(label="Меню", color=VkKeyboardColor.PRIMARY, payload={"type": "m"})      # m - menu
        kb.add_callback_button(label='Дальше', color=VkKeyboardColor.PRIMARY, payload={"type": "n", "num": num+1, "flag": flag, "flag2": ind})
        kb.add_callback_button(label="Оформить заказ", color=VkKeyboardColor.POSITIVE, payload={"type": "o"})   # o - order
    elif t == len(list):
        kb.add_callback_button(label="Меню", color=VkKeyboardColor.PRIMARY, payload={"type": "m"})
        kb.add_callback_button(label='Назад', color=VkKeyboardColor.PRIMARY, payload={"type": "b", "num": num-1, "flag": flag, "flag2": ind})
        kb.add_callback_button(label="Оформить заказ", color=VkKeyboardColor.POSITIVE, payload={"type": "o"})
    elif num != 0 and t != len(list):
        kb.add_callback_button(label='Дальше', color=VkKeyboardColor.PRIMARY, payload={"type": "n", "num": num+1, "flag": flag, "flag2": ind})
        kb.add_callback_button(label='Назад', color=VkKeyboardColor.PRIMARY, payload={"type": "b", "num": num-1, "flag": flag, "flag2": ind})
    return kb



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


def save_data(vk_obj, container: dict, user_id, key):
    while True:
        message = vk_obj.messages.getConversations(offset=0, count=1, filter='unread')['items']
        if message:
            text = message[0]['last_message']['text']
            container[user_id][key] = text
            break


def menu_kb():
    kb = VkKeyboard(inline=True)
    kb.add_button(label="Меню!", color=VkKeyboardColor.PRIMARY, payload={"type": "Запустить бота"})
    return kb


def order_kb():
    kb = VkKeyboard(inline=True)
    kb.add_button(label="Да, верно!", color=VkKeyboardColor.POSITIVE, payload={"type": "y"})    # y - yes
    kb.add_button(label="Отменить", color=VkKeyboardColor.NEGATIVE, payload={"type": "c"})      # c - cancel
    return kb


def poll_kb():
    kb = VkKeyboard(inline=True)
    kb.add_button(label="Начать опрос", color=VkKeyboardColor.PRIMARY, payload={"type": "poll"})
    return kb


text_inst = """
MCDONALDS тоже ресторан !
1. Для начала работы нажмите : "Запустить бота"
2. Вы всегда можете найти актуальный перечень всех акций и предложений нажав кнопку : "Наш сайт"
"""

# 1 вопрос
QUESTION_1 = 'Придумайте пароль - в дальнейшем этакий вход в личный кабинет'
# 2 вопрос
QUESTION_2 = 'Как вас зовут?'
# 3 вопрос
QUESTION_3 = 'Сколько вам лет?'
# 4 вопрос
QUESTION_4 = 'Ваш мобильный телефон (формат: +375XXYYYYYYY)?'
# 3 вопрос
QUESTION_5 = 'Адрес, по которому доставить заказ?'


def main():
    # Запускаем бота
    vk_session = VkApi(token=TOKEN, api_version=API_VERSION)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)

    # Основное меню
    main_menu_kb = VkKeyboard(one_time=True)
    main_menu_kb.add_button(label='Меню!',
                            color=VkKeyboardColor.NEGATIVE,
                            payload={"type": "text"})
    main_menu_kb.add_line()
    main_menu_kb.add_callback_button(label='Наш сайт!',
                                     color=VkKeyboardColor.POSITIVE,
                                     payload={"type": "open_link",
                                              "link": "https://ksbv.by/ru/"})
    main_menu_kb.add_line()
    main_menu_kb.add_callback_button(label='Мы в Телеграме!',
                                     color=VkKeyboardColor.PRIMARY,
                                     payload={"type": "open_link", "link": "https://t.me/my_mcdonalds_bot"})

    # Запускаем пуллинг
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            if event.obj.message["text"] != "":
                if event.from_user:
                    # print(event)
                    if event.obj.message['text'] == 'start':
                        user_id = event.obj.message['from_id']
                        user_data[user_id] = {}
                        print(user_data)

                        vk.messages.send(
                            user_id=user_id,
                            random_id=get_random_id(),
                            peer_id=user_id,
                            keyboard=poll_kb().get_keyboard(),
                            message=text_inst + '\n\nНо перед началом работы небольшой опрос',
                        )
                    elif event.obj.message['text'] == 'Меню!':
                        vk.messages.send(
                            user_id=user_id,
                            random_id=get_random_id(),
                            peer_id=user_id,
                            keyboard=keyb_gen(list=category_list, num=0, flag=1).get_keyboard(),
                            message='Выбери категорию блюд',
                        )
                    for cat in category_list:
                        if event.obj.message['text'] == cat:
                            ind = category_list.index(cat)
                            vk.messages.send(
                                user_id=user_id,
                                random_id=get_random_id(),
                                peer_id=user_id,
                                keyboard=keyb_gen(list=name_and_price_for_dish_btn(cat[:-1]), num=0, flag=2, ind=ind).get_keyboard(),
                                message="Выбери 'блюдо'",
                            )
                        elif event.obj.message['text'].split('-')[0][:-1] in dishes_by_categories(category_list)[cat[:-1]]:
                            dish = event.obj.message['text'].split('-')[0][:-1]
                            # user_order[event.obj.message['from_id']] = {}

                            if cat[:-1] not in user_order:
                                user_order[cat[:-1]] = [dish]
                            else:
                                user_order[cat[:-1]].append(dish)
                            print(user_order)

                    if event.obj.message['text'] == 'Да, верно!':
                        vk.messages.send(
                            user_id=user_id,
                            random_id=get_random_id(),
                            peer_id=user_id,
                            message='Тут должна быть оплата',
                        )
                    if event.obj.message['text'] == 'Отменить':
                        vk.messages.send(
                            user_id=user_id,
                            random_id=get_random_id(),
                            peer_id=user_id,
                            message='Очень жаль..',
                        )
                    if event.obj.message['text'] == 'Начать опрос':

                        # задаем вопросы пользователю и сохраняем ответы в словарь user_data
                        vk.messages.send(user_id=user_id, random_id=get_random_id(), message=QUESTION_1)
                        save_data(vk_obj=vk, container=user_data, user_id=user_id, key='password')

                        # проверка на наличие пароля в БД
                        password = user_data[user_id]['password']
                        check_user_in_db = check_password(password)
                        if check_user_in_db:
                            vk.messages.send(
                                user_id=user_id,
                                random_id=get_random_id(),
                                keyboard=main_menu_kb.get_keyboard(),
                                message="Тебя я знаю! Привет!"
                            )
                        else:
                            vk.messages.send(user_id=user_id, random_id=get_random_id(), message=QUESTION_2)
                            save_data(vk_obj=vk, container=user_data, user_id=user_id, key='name')

                            vk.messages.send(user_id=user_id, random_id=get_random_id(), message=QUESTION_3)
                            save_data(vk_obj=vk, container=user_data, user_id=user_id, key='age')

                            vk.messages.send(user_id=user_id, random_id=get_random_id(), message=QUESTION_4)
                            save_data(vk_obj=vk, container=user_data, user_id=user_id, key='phone')

                            vk.messages.send(user_id=user_id, random_id=get_random_id(), message=QUESTION_5)
                            save_data(vk_obj=vk, container=user_data, user_id=user_id, key='address')
                            print(user_data)

                            insert_user_to_db(user_data[user_id])
                            print("Юзер в базе для юзеров")

                            vk.messages.send(
                                user_id=user_id,
                                random_id=get_random_id(),
                                keyboard=main_menu_kb.get_keyboard(),
                                message="Я тебя запомнил, можешь приступать к выбору блюд )"
                            )

        # обрабатываем клики по callback кнопкам
        elif event.type == VkBotEventType.MESSAGE_EVENT:
            if event.object.payload.get("type") in CALLBACK_TYPES:
                r = vk.messages.sendMessageEventAnswer(
                    event_id=event.object.event_id,
                    user_id=event.object.user_id,
                    peer_id=event.object.peer_id,
                    event_data=json.dumps(event.object.payload),
                )
            if event.object.payload.get("type") == "n":
                if event.object.payload.get("flag") == 1:
                    num = event.object.payload.get("num")
                    vk.messages.edit(
                        peer_id=event.obj.peer_id,
                        message='Выбери категорию блюд',
                        conversation_message_id=event.obj.conversation_message_id,
                        keyboard=keyb_gen(category_list, num, 1).get_keyboard()
                    )
                elif event.object.payload.get("flag") == 2:
                    num = event.object.payload.get("num")
                    index = event.object.payload.get("flag2")
                    vk.messages.edit(
                        peer_id=event.obj.peer_id,
                        message="Выбирай 'блюдо'",
                        conversation_message_id=event.obj.conversation_message_id,
                        keyboard=keyb_gen(name_and_price_for_dish_btn(category_list[index][:-1]), num, 2, index).get_keyboard()
                    )

            elif event.object.payload.get("type") == "b":
                if event.object.payload.get("flag") == 1:
                    num = event.object.payload.get("num")
                    vk.messages.edit(
                        peer_id=event.obj.peer_id,
                        message='Выбирай категорию блюда',
                        conversation_message_id=event.obj.conversation_message_id,
                        keyboard=keyb_gen(category_list, num, 1).get_keyboard()
                    )
                elif event.object.payload.get("flag") == 2:
                    num = event.object.payload.get("num")
                    index = event.object.payload.get("flag2")
                    vk.messages.edit(
                        peer_id=event.obj.peer_id,
                        message='Выбирай "блюдо"',
                        conversation_message_id=event.obj.conversation_message_id,
                        keyboard=keyb_gen(name_and_price_for_dish_btn(category_list[index][:-1]), num, 2, index).get_keyboard()
                    )

            if event.object.payload.get("type") == "m":
                vk.messages.send(
                    random_id=get_random_id(),
                    peer_id=event.obj.peer_id,
                    keyboard=keyb_gen(list=category_list, num=0, flag=1).get_keyboard(),
                    message='Выбери категорию блюд',
                )

            if event.object.payload.get("type") == "o":
                vk.messages.send(
                    random_id=get_random_id(),
                    peer_id=event.obj.peer_id,
                    keyboard=order_kb().get_keyboard(),
                    message='ВАШ ЗАКАЗ \nВсё верно?\n\n' + make_order_description(user_order)
                )

    print(f'USER_ORDER - {user_order}')


if __name__ == "__main__":
    main()