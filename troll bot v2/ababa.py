import sqlite3
import time

# открываем соединение с базой данных
conn = sqlite3.connect('bot.db')

cursor = conn.cursor()

# cursor.execute("INSERT INTO businesses (user_id, business_name, created, level) VALUES (5042083234, 'Ботоводня 🤖', 1, 5)")

# cursor.execute("DELETE FROM businesses WHERE user_id = 5042083234")

# data = [
#     (409305738, ),
#     (807675887, ),
#     (975377823, ),
#     (600108327, ),
#     (633398015, ),
#     (818161873, ),
#     (678780807, ),
#     (674874728, ),
#     (382328456, )
# ]

# sql = '''INSERT INTO cooldowns (user_id) VALUES (?)'''

# cursor.executemany(sql, data)

# cursor.execute("DELETE FROM cooldowns")

# conn.execute("UPDATE users SET troll_count = 0, trolled_count = 0, troll_cooldown = 0, casino_cooldown = 0, work_cooldown = 0")

# conn.execute("ALTER TABLE users DROP COLUMN mt_used")
# conn.execute("ALTER TABLE cooldowns DROP COLUMN ta_cooldown")

# conn.execute("ALTER TABLE users ADD COLUMN ri_used INTEGER NOT NULL DEFAULT 0")
# conn.execute("ALTER TABLE cooldowns ADD COLUMN ri_cooldown INTEGER NOT NULL DEFAULT 0")

# conn.execute("UPDATE users SET money = 100000000000")
# conn.execute("UPDATE cooldowns SET get_job_cooldown = 0")
# conn.execute("UPDATE cooldowns SET get_job_cooldown = 0")

# conn.execute("UPDATE businesses SET current_income = 10000000")

# conn.execute("DELETE FROM user_inventory")

# conn.execute("UPDATE user_inventory SET quantity = 0 WHERE item_type = '\U0001F9F0 Тролл-Кейс'")


# cursor.execute("INSERT INTO users (user_id) VALUES (5943023867)")

# conn.execute('DELETE FROM user_inventory WHERE user_id = ?', (633398015, ))

# conn.execute("CREATE TABLE trollito (user_id INTEGER NOT NULL, item_type varchar(50) NOT NULL DEFAULT '', price INTEGER NOT NULL DEFAULT 0)")

# conn.execute("DROP TABLE trollito")

# conn.execute("INSERT INTO trollito (user_id, item_type, price) VALUES (373753753 ,'\U00002796 Удаление', 20)")

# cursor.execute("SELECT user_id FROM users")
# user_ids = cursor.fetchall()

# conn.execute("UPDATE users SET money = 35592 WHERE user_id = 738046155")

# for user_id in user_ids:
#     cursor.execute("INSERT INTO cooldowns (user_id) VALUES (?)", (user_id))

# conn.execute('DROP TABLE cooldowns')

# cursor.execute("INSERT INTO businesses (user_id, created) VALUES (?, ?)", (441148955, 1, ))

# cursor.execute('UPDATE businesses SET report_time = report_time - 750 WHERE user_id = 6105316427')

# cursor.execute('UPDATE businesses SET experience = 100000')

# cursor.execute('INSERT INTO users (user_id, money) VALUES (?, ?)', (441148955, 1000000))

# cursor.execute("DELETE FROM users WHERE user_id = ?", (5293190031, ))

# cursor.execute("INSERT INTO user_inventory (user_id, item_type, quantity) VALUES (?, ?, ?)", (633398015, '🗃 Тролл-Кейс', 500))

# cursor.execute("DELETE FROM user_inventory WHERE user_id = ? AND item_type = ?", (633398015, '\U0001F5C3 Тролл-Кейс',))

# cursor.execute("DELETE FROM businesses")

# conn.execute("UPDATE users SET trolled_count = 1 WHERE user_id = ?", (633398015, ))

# conn.execute("UPDATE users SET troll_cooldown = 215161616516 WHERE user_id = ?", (633398015, ))

# conn.execute("UPDATE user_inventory SET quantity = 10 WHERE user_id = ? AND item_type = ?", (633398015, '🗃 Тролл-Кейс'))

# conn.execute("UPDATE users SET money = 1000000")

# cursor.execute("UPDATE users SET money = money + 5000 WHERE troll_cooldown != 0 OR casino_cooldown != 0 OR work_cooldown != 0 OR charity_cooldown != 0")

# сохраняем изменения
conn.commit()

# закрываем соединение
conn.close()
