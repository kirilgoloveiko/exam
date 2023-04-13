import functools
import sqlite3
import sys
from collections import Counter

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QPixmap


user_order = []


# def make_order_description(order_dishes: list) -> str:
#     """ Просто из словаря с заказами делает красивую строку формата: Блюдо х кол-во """
#     smth = Counter(order_dishes)
#
#     order_description = ''
#     for k, v in smth.items():
#         order_description += f'{k} x{v}\n'
#     return order_description


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        hbox = QHBoxLayout()
        self.setLayout(hbox)

        menu_btn = QPushButton('МЕНЮ')
        hbox.addWidget(menu_btn)

        menu_btn.clicked.connect(self.open_menu_window)

        busket_btn = QPushButton('Корзина')
        hbox.addWidget(busket_btn)

        busket_btn.clicked.connect(self.show_busket_window)

        self.setGeometry(100, 100, 400, 300)
        self.setWindowTitle('MainWindow')
        self.show()

    # -----------------------------------------------------------------------------
    def open_menu_window(self):
        global menu_window
        menu_window = QWidget()
        vbox = QVBoxLayout()
        menu_window.setLayout(vbox)
        menu_window.setWindowTitle('Меню')
        menu_window.setGeometry(300, 300, 400, 300)

        conn = sqlite3.connect('mcdonalds.db')
        cursor = conn.cursor()
        cursor.execute(""" select category_name from DishCategories """)
        categories = cursor.fetchall()
        for cat in categories:
            for i in cat:
                button = QPushButton(f'{i}')

                vbox.addWidget(button)

                if button.text() == 'Бургеры':
                    button.clicked.connect(self.show_burgers_window)
                if button.text() == 'Картофель':
                    button.clicked.connect(self.show_potato_window)
                if button.text() == 'Снеки':
                    button.clicked.connect(self.show_snacks_window)
                if button.text() == 'Соусы':
                    button.clicked.connect(self.show_sauces_window)
                if button.text() == 'Напитки':
                    button.clicked.connect(self.show_drinks_window)
                if button.text() == 'Десерты':
                    button.clicked.connect(self.show_dessert_window)

        menu_window.show()

    def show_busket_window(self):
        global busket_window
        busket_window = QWidget()
        vbox = QVBoxLayout()
        busket_window.setLayout(vbox)
        busket_window.setWindowTitle('Корзина')
        busket_window.setGeometry(200, 200, 300, 200)

        if not user_order:
            label = QLabel()
            label.setText('На данный момент корзина пуста')
            vbox.addWidget(label)
        else:
            # text = make_order_description(order_dishes=user_order)
            for dish in user_order:
                label = QLabel(f'{dish}')
                vbox.addWidget(label)
                del_btn = QPushButton('Убрать из корзины')
                vbox.addWidget(del_btn)

                del_btn.clicked.connect(functools.partial(self.delete_from_busket, dish))

        busket_window.show()
# ----------------------------------------------------------
    def delete_from_busket(self, dish):
        print(f'Вы хотите удалить {dish}')
        vbox = QVBoxLayout()
        busket_window.setLayout(vbox)

        user_order.remove(dish)
        print(user_order)

        for dish in user_order:
            label = QLabel(f'{dish}')
            vbox.addWidget(label)

        busket_window.show()
# ----------------------------------------------------------
    def show_burgers_window(self):
        global burgers_window
        burgers_window = QWidget()
        vbox = QVBoxLayout()
        burgers_window.setLayout(vbox)

        burgers_window.setWindowTitle('Бургеры')
        burgers_window.setGeometry(200, 200, 300, 200)

        conn = sqlite3.connect('mcdonalds.db')
        cursor = conn.cursor()
        cursor.execute(""" select name, price from Dishes
                            join DishCategories
                                on Dishes.category_id = DishCategories.category_id
                            where category_name = 'Бургеры' """)
        dishes = cursor.fetchall()

        for dish in dishes:
            label = QLabel(f'{dish[0]} - {dish[1]}')
            vbox.addWidget(label)
            button = QPushButton('В корзину')
            vbox.addWidget(button)

            name_dish = dish[0]
            button.clicked.connect(functools.partial(self.add_to_bucket, name_dish))

            desc_button = QPushButton('Описание')
            vbox.addWidget(desc_button)

            desc_button.clicked.connect(functools.partial(self.show_description, name_dish))

        burgers_window.show()

    def show_potato_window(self):
        global potatos_window
        potatos_window = QWidget()
        vbox = QVBoxLayout()
        potatos_window.setLayout(vbox)
        potatos_window.setWindowTitle('Картошечка')
        potatos_window.setGeometry(200, 200, 300, 200)

        conn = sqlite3.connect('mcdonalds.db')
        cursor = conn.cursor()
        cursor.execute(""" select name, price from Dishes
                            join DishCategories
                                on Dishes.category_id = DishCategories.category_id
                            where category_name = 'Картофель' """)
        dishes = cursor.fetchall()

        for dish in dishes:
            label = QLabel(f'{dish[0]} - {dish[1]}')
            name_dish = dish[0]
            vbox.addWidget(label)
            button = QPushButton('В корзину')
            vbox.addWidget(button)

            name_dish = dish[0]
            button.clicked.connect(functools.partial(self.add_to_bucket, name_dish))

            desc_button = QPushButton('Описание')
            vbox.addWidget(desc_button)

            desc_button.clicked.connect(functools.partial(self.show_description, name_dish))

        potatos_window.show()

    def show_snacks_window(self):
        global snacks_window
        snacks_window = QWidget()
        vbox = QVBoxLayout()
        snacks_window.setLayout(vbox)
        snacks_window.setWindowTitle('Снеки')
        snacks_window.setGeometry(200, 200, 300, 200)

        conn = sqlite3.connect('mcdonalds.db')
        cursor = conn.cursor()
        cursor.execute(""" select name, price from Dishes
                            join DishCategories
                                on Dishes.category_id = DishCategories.category_id
                            where category_name = 'Снеки' """)
        dishes = cursor.fetchall()

        for dish in dishes:
            label = QLabel(f'{dish[0]} - {dish[1]}')
            name_dish = dish[0]
            vbox.addWidget(label)
            button = QPushButton('В корзину')
            vbox.addWidget(button)

            name_dish = dish[0]
            button.clicked.connect(functools.partial(self.add_to_bucket, name_dish))

            desc_button = QPushButton('Описание')
            vbox.addWidget(desc_button)

            desc_button.clicked.connect(functools.partial(self.show_description, name_dish))

        snacks_window.show()

    def show_sauces_window(self):
        global sauces_window
        sauces_window = QWidget()
        vbox = QVBoxLayout()
        sauces_window.setLayout(vbox)
        sauces_window.setWindowTitle('Соусы')
        sauces_window.setGeometry(200, 200, 300, 200)

        conn = sqlite3.connect('mcdonalds.db')
        cursor = conn.cursor()
        cursor.execute(""" select name, price from Dishes
                            join DishCategories
                                on Dishes.category_id = DishCategories.category_id
                            where category_name = 'Соусы' """)
        dishes = cursor.fetchall()

        for dish in dishes:
            label = QLabel(f'{dish[0]} - {dish[1]}')
            name_dish = dish[0]
            vbox.addWidget(label)
            button = QPushButton('В корзину')
            vbox.addWidget(button)

            name_dish = dish[0]
            button.clicked.connect(functools.partial(self.add_to_bucket, name_dish))

            desc_button = QPushButton('Описание')
            vbox.addWidget(desc_button)

            desc_button.clicked.connect(functools.partial(self.show_description, name_dish))

        sauces_window.show()

    def show_drinks_window(self):
        global drinks_window
        drinks_window = QWidget()
        vbox = QVBoxLayout()
        drinks_window.setLayout(vbox)
        drinks_window.setWindowTitle('Напитки')
        drinks_window.setGeometry(200, 200, 300, 200)

        conn = sqlite3.connect('mcdonalds.db')
        cursor = conn.cursor()
        cursor.execute(""" select name, price from Dishes
                            join DishCategories
                                on Dishes.category_id = DishCategories.category_id
                            where category_name = 'Напитки' """)
        dishes = cursor.fetchall()

        for dish in dishes:
            label = QLabel(f'{dish[0]} - {dish[1]}')
            name_dish = dish[0]
            vbox.addWidget(label)
            button = QPushButton('В корзину')
            vbox.addWidget(button)

            name_dish = dish[0]
            button.clicked.connect(functools.partial(self.add_to_bucket, name_dish))

            desc_button = QPushButton('Описание')
            vbox.addWidget(desc_button)

            desc_button.clicked.connect(functools.partial(self.show_description, name_dish))

        drinks_window.show()

    def show_dessert_window(self):
        global dessert_window
        dessert_window = QWidget()
        vbox = QVBoxLayout()
        dessert_window.setLayout(vbox)
        dessert_window.setWindowTitle('Десерты')
        dessert_window.setGeometry(200, 200, 300, 200)

        conn = sqlite3.connect('mcdonalds.db')
        cursor = conn.cursor()
        cursor.execute(""" select name, price from Dishes
                            join DishCategories
                                on Dishes.category_id = DishCategories.category_id
                            where category_name = 'Десерты' """)
        dishes = cursor.fetchall()

        for dish in dishes:
            label = QLabel(f'{dish[0]} - {dish[1]}')
            name_dish = dish[0]
            vbox.addWidget(label)
            button = QPushButton('В корзину')
            vbox.addWidget(button)

            name_dish = dish[0]
            button.clicked.connect(functools.partial(self.add_to_bucket, name_dish))

            desc_button = QPushButton('Описание')
            vbox.addWidget(desc_button)

            desc_button.clicked.connect(functools.partial(self.show_description, name_dish))

        dessert_window.show()

    def add_to_bucket(self, name):
        user_order.append(name)
        print(user_order)


    def show_description(self, name):
        global description_window
        description_window = QWidget()
        vbox = QVBoxLayout()
        description_window.setLayout(vbox)
        description_window.setWindowTitle(f'{name}')
        description_window.setGeometry(300, 300, 400, 300)

        conn = sqlite3.connect('mcdonalds.db')
        cursor = conn.cursor()
        cursor.execute(f""" select name, description, photo from Dishes
                           where name = '{name}' """)
        dish = cursor.fetchone()

        label_name = QLabel(f'{dish[0]}')

        label_photo = QLabel()
        label_photo.setText(f'{dish[0]}')
        pix = QPixmap()
        pix.loadFromData(dish[2])

        label_description = QLabel(f'{dish[1]}')
        label_description.setWordWrap(True)                                                         # !!!!!!!!!!!!!!!!!!!!!!!!!!!!
        label_description.setAlignment(QtCore.Qt.AlignJustify | QtCore.Qt.AlignVCenter)             # !!!!!!!!!!!!!!!!!!!!!!!!!!!!

        _size = QtCore.QSize(250, 250)
        label_name.setPixmap(pix.scaled(_size))
        # label2.setPixmap(pix)
        vbox.addWidget(label_photo)
        vbox.addWidget(label_name)
        vbox.addWidget(label_description)

        description_window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
