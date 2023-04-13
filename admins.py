from config import bot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup


dict_admins = {}
dict_admins["1329081957"] = {"name": "Кирилл", "username": "sniker_zz", "rights": True}

super_admin = InlineKeyboardMarkup()
super_admin.add(InlineKeyboardButton("Добавить администратора", callback_data="A"))
super_admin.add(InlineKeyboardButton("Изменить права администратора", callback_data="E"))
super_admin.add(InlineKeyboardButton("Удалить администратора", callback_data="D"))


def check_rights(id):  # функция проверки прав пользователя
    if str(id) in dict_admins:
        if dict_admins[str(id)]["rights"]:
            return True
        elif dict_admins[str(id)]["rights"] == False:
            return False
    else:
        return None


def check_admins(id):  # функция выводит список Админов
    text = " Вот список действующих админов: \n\n"
    for i, n in dict_admins.items():
        if n["rights"]:
            status = "SuperAdmin"
        elif n["rights"] == False:
            status = "Admin"
        text += "Имя - " + str(n["name"]) + ", его id - " + str(i) + " и статус -" + status + "\n"
    bot.send_message(id, text)


# def out_stat_admin(id_chat,id_admin,text): # функция вывода статистики для супер админа
#     text_out = text
#     count = 0
#     for x,y in dicts.dict_stat.items():
#         if str(id_admin) in str(y["id_adm"]):
#             count +=1
#     if len(dicts.dict_stat) == 0:
#         text_out = " Словарь статистики покач-то пуст "
#     elif count == 0:
#         name = dicts.dict_admins[str(id_admin)]["name"]
#         text_out = f"У {name} покач-то нет добавленных машин"
#     else:
#         for id_car, dct in dicts.dict_stat.items():
#             if str(id_admin) == str(dct["id_adm"]):
#                 text_out +=" Id авто : " + str(id_car) + "\n всего просмотров этого авто: " + str(dct["просмотры"]) + "\n уникальных просмотров: " + str(len(dct["уникальные"])) + "\n\n"
#     # bot.send_message(id_chat, text_out)
#     return text_out


def add_id(message):
    dict_admins[message.text] = {"name": "Admin", "username": "Admin", "rights": False}
    msg = bot.send_message(message.from_user.id, " хорошо, а теперь какое имя ему дадим? ")
    bot.register_next_step_handler(msg, add_name, message.text)


def add_name(message, value):
    dict_admins[value]["name"] = message.text
    msg = bot.send_message(message.from_user.id, " ну и последнее, определите бедалаге username ")
    bot.register_next_step_handler(msg, add_username, value)


def add_username(message, value):
    dict_admins[value]["name"] = message.text
    bot.send_message(message.from_user.id, " Отлично! Все готово. ")
    check_admins(message.from_user.id)