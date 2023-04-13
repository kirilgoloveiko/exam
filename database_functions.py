import sqlite3


conn = sqlite3.connect('mcdonalds.db', check_same_thread=False)
cursor = conn.cursor()


def check_password(password: str) -> bool:
    conn = sqlite3.connect('mcdonalds.db')
    cursor = conn.cursor()
    cursor.execute(f"""SELECT * FROM Users WHERE password = {password}""")
    if cursor.fetchone() is None:
        return False
    return True


def convert_to_binary_data(filename):
    # Преобразование данных(фоток) в двоичный формат
    with open(filename, 'rb') as file:
        blob_data = file.read()
    return blob_data


def insert_to_table(name_lst, description_lst, price_lst, time_lst, photo_lst, category_lst):
    try:
        insert_dishes_query = """ INSERT INTO Dishes (name, description, price, time, photo, category_id)
                                                                                            VALUES (?,?,?,?,?,?) """
        photos_rb = []
        for photo in photo_lst:
            photo = convert_to_binary_data(photo)
            photos_rb.append(photo)

        records = zip(name_lst, description_lst, price_lst, time_lst, photos_rb, category_lst)

        cursor.executemany(insert_dishes_query, records)
        conn.commit()
        print("Данные успешно занесены в таблицу")
        cursor.close()

    except sqlite3.Error as er:
        print("Ошибка при работе с SQLite", er)
    finally:
        conn.close()
        print("Соединение с SQLite закрыто")

# insert_to_table(name_lst, description_lst, price_lst, time_lst, photos_lst, category_lst)


def get_dishes_list(name):
    query = f""" select name, price from Dishes
                join DishCategories
                    on Dishes.category_id = DishCategories.category_id
                where category_name = '{name}' """
    cursor.execute(query)
    name_n_price = cursor.fetchall()
    return name_n_price


def insert_user_to_db(user_data: dict):
    """ словарь вида user = {'name': name, 'age': age, ..} """

    query = """ INSERT INTO Users (password, name, age, phone, address) VALUES (?, ?, ?, ?, ?)"""
    cursor.execute(query, tuple(user_data.values()))

    conn.commit()
    cursor.close()
    conn.close()
