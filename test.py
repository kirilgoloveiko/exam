import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import TG_TOKEN


bot = telebot.TeleBot(TG_TOKEN)


@bot.message_handler(content_types=['text'])
def rate_product(message):
    if message.text == '/start':
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item = KeyboardButton("Оценить товар")
        markup.add(item)
        bot.send_message(message.chat.id, text="Привет, оцени плиз товары из последнего заказа!\n"
                                               "Нажми Оценить товар, чтобы приступить к оценке.", reply_markup=markup)
    elif message.text == 'Оценить товар':
        markup = InlineKeyboardMarkup(row_width=5)
        markup.add(InlineKeyboardButton("⭐", callback_data='1'))
        markup.add(InlineKeyboardButton("⭐⭐", callback_data='2'))
        markup.add(InlineKeyboardButton("⭐⭐⭐", callback_data='3'))
        markup.add(InlineKeyboardButton("⭐⭐⭐⭐", callback_data='4'))
        markup.add(InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data='5'))
        bot.send_message(message.chat.id, "Пожалуйста, оцените товар:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    try:
        rating = int(call.data)
        bot.send_message(call.message.chat.id, f"Спасибо за оценку в {rating} звезд! ✨")
    except:
        pass

print('Ready..')
bot.polling(none_stop=True)
