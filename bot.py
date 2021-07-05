import config
import logging
import threading
import keyboard as kb
import pymysql

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.helper import Helper, HelperMode, ListItem
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode, InputMediaPhoto, InputMediaVideo, ChatActions
from aiogram.utils.markdown import text, bold, italic, code, pre
from aiogram.types.message import ContentType

from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

# for events
event_data = dict()

# for dishes
dish_data = dict()

# delete data (for dishes and events)
delete_data = dict()

class EventDishStates(Helper):
	mode = HelperMode.snake_case

	# event states
	S0 = ListItem() # event type
	S1 = ListItem()	# header state
	S2 = ListItem()	# content state
	S3 = ListItem()	# img state
	S4 = ListItem()	# city state
	S5 = ListItem()	# check state
	S6 = ListItem()	# correction state
	S7 = ListItem() # delete state

	# for both them
	S8 = ListItem() # final state (for both event and dish!)

	# dish states
	SA = ListItem() # name state 9
	SB = ListItem() # category state 10
	SC = ListItem() # group state 11
	SD = ListItem() # desc state 12
	SE = ListItem() # img state 13
	SF = ListItem()	# check state 14
	SG = ListItem()	# correction state 15
	SH = ListItem() # delete state 16

	# for both them
	SI = ListItem() # deletement refinement 17
	SJ = ListItem() # delete confirmation 18

# logging setup
logging.basicConfig(level = logging.INFO)

connection = pymysql.connect(host = "localhost", user = "root", passwd = "", database = "cucina_db")
cursor = connection.cursor()

bot = Bot(token = config.TOKEN)
dp = Dispatcher(bot, storage = MemoryStorage())

# start message
@dp.message_handler(commands = ["start"], commands_prefix = "/")
async def on_start(message: types.Message):
	if(message.from_user.id == config.ADMIN_ID):
		await message.answer("Здравствуйте!🤗\nВы запустили контент-бота сети пиццерий Cucina🍕🍕🍕" +
			"\nДля продолжения введите одну из следующих команд:" + "\n/add_event - Добавить новость\n/add_dish - Добавить новое блюдо")

# help cmd
@dp.message_handler(state = '*', commands = ["help"], commands_prefix = "/")
async def help_cmd(message: types.Message):
	await message.answer("Доступные команды:" + "\n/add_event - Добавить новость\n/add_dish - Добавить новое блюдо")

# delete cmd
@dp.message_handler(state = '*', commands = ["delete"], commands_prefix = "/")
async def delete_cmd(message: types.Message):
	if(message.from_user.id == config.ADMIN_ID):
		if(bool(dish_data)):
			await message.answer("Добавление блюда отменено⚠")
			dish_data.clear()
		elif(bool(event_data)):
			await message.answer("Добавление новости отменено⚠")
			event_data.clear()

		state = dp.current_state(user = message.from_user.id)

		await message.answer("Выберите, что именно следует удалитьℹ️", reply_markup = kb.inline_kb_delete)
		await state.set_state(EventDishStates.all()[17])

# refine deletement
@dp.message_handler(state = EventDishStates.SI)
async def refine_del(message: types.Message):
	state = dp.current_state(user = message.from_user.id)

	if(message.text == "Событие📰"):
		await message.answer("Введите заголовок события, которое желаете удалить:")

		delete_data["type"] = "events"

		await state.set_state(EventDishStates.all()[7])
	elif(message.text == "Блюдо🍽"):
		await message.answer("Введите название блюда, которое желаете удалить:")

		delete_data["type"] = "dishes"

		await state.set_state(EventDishStates.all()[16])

# event search to delete
@dp.message_handler(state = EventDishStates.S7)
async def refine_event_del(message: types.Message):
	state = dp.current_state(user = message.from_user.id)

	reply_text = text("Результаты поиска (id - событие):\n\n")

	search_key = "%" + message.text + "%"
	select_query = "SELECT * FROM events WHERE HEADER LIKE %s;"
	cursor.execute(select_query, search_key)

	rows = cursor.fetchall()
	for row in rows:
		reply_text += str(row[0]) + " - " + row[3] + "\n\n"

	connection.commit()

	reply_text += "Введите id новости для удаленияℹ️"

	await message.answer(reply_text)
	await state.set_state(EventDishStates.all()[18])

# dish search to delete
@dp.message_handler(state = EventDishStates.SH)
async def refine_dish_del(message: types.Message):
	state = dp.current_state(user = message.from_user.id)

	reply_text = text("Результаты поиска (id - название):\n\n")

	search_key = "%" + message.text + "%"
	select_query = "SELECT * FROM dishes WHERE NAME LIKE %s;"
	cursor.execute(select_query, search_key)

	rows = cursor.fetchall()
	for row in rows:
		reply_text += str(row[0]) + " - " + row[1] + "\n\n"

	connection.commit()

	reply_text += "Введите id блюда для удаленияℹ️"

	await message.answer(reply_text)
	await state.set_state(EventDishStates.all()[18])

# dish/event delete
@dp.message_handler(state = EventDishStates.SJ)
async def delete_dish_event(message: types.Message):
	state = dp.current_state(user = message.from_user.id)

	delete_data["id"] = int(message.text)

	del_query = ""
	if(delete_data["type"] == "events"):
		del_query = "DELETE FROM events WHERE ID = %s;"
	else:
		del_query = "DELETE FROM dishes WHERE ID = %s;"

	cursor.execute(del_query, delete_data["id"])

	connection.commit()

	delete_data.clear()

	await message.answer("Успешно удалено✅")
	await state.set_state(EventDishStates.all()[8])

# add event cmd
@dp.message_handler(state = '*', commands = ["add_event"], commands_prefix = "/")
async def add_event(message: types.Message):
	if(message.from_user.id == config.ADMIN_ID):
		if(bool(dish_data)):
			await message.answer("Добавление блюда отменено⚠")
			dish_data.clear()

		state = dp.current_state(user = message.from_user.id)

		await message.answer("Добавление новости начато!✅\nСперва введите тип новости:\n0 - Открытие в новом месте" +
			"\n1 - Позитивная новость\n2 - Предупреждение\n3 - Плохая новость (закрытие и тп)")
		await state.set_state(EventDishStates.all()[0])
	else:
		await message.answer("Вы не являетесь администратором!❌\nВыполнение комманды невозможно!")

# event type request
@dp.message_handler(state = EventDishStates.S0)
async def request_name(message: types.Message):
	if(message.text.isdigit() and len(message.text) == 1):
		if(int(message.text) <= 3 and int(message.text) >= 0):
			state = dp.current_state(user = message.from_user.id)

			event_data["type"] = int(message.text)
			await message.answer("Замечательно!\nДалее введите заголовок новости (не более 35 символов):")

			await state.set_state(EventDishStates.all()[1])
		else:
			await message.answer("Недопустимый тип. Введите значение от 0 до 3!")
	else:
		await message.answer("Неверно введён тип новости. Введите одно число от 0 до 3!")

# event name request
@dp.message_handler(state = EventDishStates.S1)
async def request_name(message: types.Message):
	state = dp.current_state(user = message.from_user.id)

	if(len(message.text) <= 35):
		event_data["header"] = message.text

		await message.answer("Отлично!😉\nДалее введите содержимое (не более 500 символов)." +
			"\nПеред каждым переносом строки, не забывайте вставлять символ '^'.\nПример:\n" +
			"Не забывайте использовать промокод CUCINA^\nДействитетлен до 17.09.2077😎")
		await state.set_state(EventDishStates.all()[2])
	else:
		await message.answer("❌Длина заголовка не должна превышать 35 символов!❌")

# event content request
@dp.message_handler(state = EventDishStates.S2)
async def request_content(message: types.Message):
	state = dp.current_state(user = message.from_user.id)

	if(len(message.text) <= 500):
		event_data["content"] = message.text

		await message.answer("Хорошо!\nДалее вам нужно отправить ссылку на картинку для события.\nДля этого используйте сайт https://postimg.cc"
		 + "\nОбязательно выберите ссылку с подписью \'Direct link!\'⚠️")
		await state.set_state(EventDishStates.all()[3])
	else:
		await message.answer("❌Длина содержимого не должна превышать 500 символов!❌")

# event img-url request
@dp.message_handler(state = EventDishStates.S3)
async def request_img(message: types.Message):
	state = dp.current_state(user = message.from_user.id)

	event_data["img-url"] = message.text

	# использовать срез строки, чтобы проверить, является ли ссылкой строка

	reply_text = text("Уже почти!🙃\nТеперь укажите город(-а), где будет проходить событие.", 
		"\n1 - Киев\n2 - Харьков\n3 - Львов\n4 - Днепр\n5 - Одесса\n6 - Ивано-Франковск\n7 - Херсон",
		"\nall - Для всех\n", bold("\nВводите города одной строкой, без пробелов⚠️\n"), "Например:", italic("\n1457\nall"), sep = "")

	await message.answer(reply_text, parse_mode = ParseMode.MARKDOWN)
	await state.set_state(EventDishStates.all()[4])

# event city request
@dp.message_handler(state = EventDishStates.S4)
async def request_city(message: types.Message):
	state = dp.current_state(user = message.from_user.id)

	if((message.text.isdigit() or message.text == "all") and (len(message.text) <= 7)):
		if(message.text != "all"):
			for num in message.text:
				if(int(num) > 7 or int(num) < 1):
					await message.answer("❌Неверно указаны города. Проверьте правильность ввода!❌")
					return

		event_data["city"] = message.text

		city_list = ["Киев", "Харьков", "Львов", "Днепр", "Одесса", "Ивано-Франковск", "Херсон"]
		types = {0: "Открытие в новом месте", 1: "Позитивная новость", 2: "Предупреждение", 3: "Плохая новость"}
		cities = ""

		if(event_data["city"] != "all"):
			for i in range(0, len(event_data["city"])):
				cities += str(city_list[int(event_data["city"][i]) - 1]) + "\n"
		else:
			cities = "Все города\n"

		await message.answer("Готово!🥳\nПроверьте данные и нажиите 'Да✅', чтобы подтвердить отправку или 'Нет❌', чтобы редактировать пост.\n\n"
			+ "Тип: " + types[event_data["type"]] + "\n\n" + event_data["header"] + "\n" + event_data["content"] + "\n\nГорода:\n" + cities + "\nСсылка на изображение: " + event_data["img-url"],
			 reply_markup = kb.inline_kb_full)

		await state.set_state(EventDishStates.all()[5])
	else:
		await message.answer("❌Неверно указаны города. Проверьте правильность ввода!❌")

# event confirmation
@dp.message_handler(state = EventDishStates.S5)
async def event_confirmation_request(message: types.Message):
	state = dp.current_state(user = message.from_user.id)

	if(message.text == 'Да✅'):
		# creating insert query
		insert_query = "INSERT INTO events(TYPE, HEADER, CONTENT, IMG_URL, CITY) VALUES(%s, %s, %s, %s, %s);"	
		cursor.execute(insert_query, (event_data["type"], event_data["header"], event_data["content"], event_data["img-url"], event_data["city"]))

		connection.commit()

		event_data.clear()

		await message.answer("Событие добавлено в базу данных!😎\nДля продолжения работы введите команду.")
		await state.set_state(EventDishStates.all()[7])
	elif(message.text == 'Нет❌'):
		await message.answer("Отправка отменена⚠️\nНовость отправлена на доработку!")
		await message.answer("Сперва введите параметр (цифрой), который желаете изменить.\nЧерез пробел введите новое значение параметра.\n\n"
			+ "Параметры:\n" + "1 - Тип\n" + "2 - Заголовок\n" + "3 - Содержимое\n" + "4 - Картинка\n" + "5 - Город\n" + "delete - Удалить событие\n\n"
			+ "Пример:\n" + "2 Открытие в городе Львов!")

		await state.set_state(EventDishStates.all()[6])

# event correction
@dp.message_handler(state = EventDishStates.S6)
async def event_correction(message: types.Message):
	corrected = False

	state = dp.current_state(user = message.from_user.id)

	if(message.text[0].isdigit() and len(message.text) >= 3):
		if(int(message.text[0]) == 1):
			if(len(message.text) == 3 and message.text[2].isdigit()):
				if(int(message.text[2]) <= 3 and int(message.text[2]) >= 0):
					event_data["type"] = int(message.text[2])

					corrected = True
				else:
					await message.answer("Неверный формат! Попробуйте снова!")
			else:
				await message.answer("Неверный формат! Попробуйте снова!")
		elif(int(message.text[0]) == 2):
			if(len(message.text[2:]) <= 35):
				event_data["header"] = message.text[2:]

				corrected = True
			else:
				await message.answer("Неверный формат! Попробуйте снова!")
		elif(int(message.text[0]) == 3):
			if(len(message.text[2:]) <= 500):
					event_data["content"] = message.text[2:]

					corrected = True
			else:
				await message.answer("Неверный формат! Попробуйте снова!")
		elif(int(message.text[0]) == 4):
			event_data["img-url"] = message.text[2:]

			await state.set_state(EventDishStates.all()[5])

			corrected = True
		elif(int(message.text[0]) == 5):
			if((message.text[2:].isdigit() and len(message.text[2:]) <= 7) or (message.text[2:] == "all")):
				event_data["city"] = message.text[2:]

				corrected = True
			else:
				await message.answer("Неверный формат! Попробуйте снова!")
		else:
			await message.answer("Неверный формат! Попробуйте снова!")
	elif(message.text == "delete"):
		event_data.clear()
		await message.answer("Событие удалено!⚠️")
		await state.set_state(EventDishStates.all()[8])
	else:
		await message.answer("Неверный формат!⚠️\nПопробуйте снова!")

	# resending confirmation msg (if it was corrected)
	if(corrected):
		await message.answer("Правки внесены!")
		await state.set_state(EventDishStates.all()[5])

		city_list = ["Киев", "Харьков", "Львов", "Днепр", "Одесса", "Ивано-Франковск", "Херсон"]
		types = {0: "Открытие в новом месте", 1: "Позитивная новость", 2: "Предупреждение", 3: "Плохая новость"}
		cities = ""

		if(event_data["city"] != "all"):
			for i in range(0, len(event_data["city"])):
				cities += str(city_list[int(event_data["city"][i]) - 1]) + "\n"
		else:
			cities = "Все города\n"

		await message.answer("Готово!🥳\nПроверьте данные и нажиите 'Да✅', чтобы подтвердить отправку или 'Нет❌', чтобы редактировать пост.\n\n"
				+ "Тип: " + types[event_data["type"]] + "\n\n" + event_data["header"] + "\n" + event_data["content"] +
				 "\n\nГорода:\n" + cities + "\nСсылка на изображение: " + event_data["img-url"],
				 reply_markup = kb.inline_kb_full)

# add dish cmd
@dp.message_handler(state = '*', commands = ["add_dish"], commands_prefix = "/")
async def add_dish(message: types.Message):
	if(message.from_user.id == config.ADMIN_ID):
		if(bool(event_data)):
			await message.answer("Добавление новости отменено⚠")
			event_data.clear()

		state = dp.current_state(user = message.from_user.id)

		await message.answer("Добавление блюда начато!✅\nСперва введите название (не более 25 символов):")
		await state.set_state(EventDishStates.all()[9])
	else:
		await message.answer("Вы не являетесь администратором!❌\nВыполнение комманды невозможно!")

# dish name
@dp.message_handler(state = EventDishStates.SA)
async def set_dish_name(message: types.Message):
	state = dp.current_state(user = message.from_user.id)

	if(len(message.text) <= 25):
		dish_data["name"] = message.text

		await message.answer("Чудно! Далее введите номер категории:\n1 - Готовое меню\n2 - Самостоятельное блюдо")
		await state.set_state(EventDishStates.all()[10])
	else:
		await message.answer("❌Длина названия не должна превышать 25 символов!❌")

# dish category
@dp.message_handler(state = EventDishStates.SB)
async def set_dish_category(message: types.Message):
	state = dp.current_state(user = message.from_user.id)

	if(message.text.isdigit() and len(message.text) == 1):
		if(int(message.text) == 1 or int(message.text) == 2):
			dish_data["category"] = int(message.text)

			await message.answer("Хорошо!\nДалее введите название группы (сверьте с уже существующими группами в приложении; не более 25 символов⚠️):")
			await state.set_state(EventDishStates.all()[11])
		else:
			await message.answer("Неверный формат!⚠️\nПопробуйте снова!")
	else:
		await message.answer("Неверный формат!⚠️\nПопробуйте снова!")

# dish group
@dp.message_handler(state = EventDishStates.SC)
async def set_dish_group(message: types.Message):
	state = dp.current_state(user = message.from_user.id)

	if(len(message.text) <= 25):
		dish_data["group"] = message.text

		await message.answer("Отлично!🙃\nДалее введите описание блюда/меню (не более 100 символов):")
		await state.set_state(EventDishStates.all()[12])
	else:
		await message.answer("❌Длина названия группы не должна превышать 25 символов!❌")

# dish desc.
@dp.message_handler(state = EventDishStates.SD)
async def set_dish_desc(message: types.Message):
	state = dp.current_state(user = message.from_user.id)

	if(len(message.text) <= 100):
		dish_data["desc"] = message.text

		await message.answer("Хорошо!\nДалее вам нужно отправить ссылку на картинку для блюда.\nДля этого используйте сайт https://postimg.cc"
		 + "\nОбязательно выберите ссылку с подписью \'Direct link!\'⚠️")
		await state.set_state(EventDishStates.all()[13])
	else:
		await message.answer("❌Длина описания не должна превышать 100 символов!❌")

# dish img
@dp.message_handler(state = EventDishStates.SE)
async def set_dish_img(message: types.Message):
	state = dp.current_state(user = message.from_user.id)

	dish_data["img-url"] = message.text

	# использовать срез строки, чтобы проверить, является ли ссылкой строка

	category = ""
	if(dish_data["category"] == 1):
		category = "Готовое меню"
	else:
		category = "Самостоятельное блюдо"

	await message.answer("Готово!🥳\nПроверьте данные и нажиите 'Да✅', чтобы подтвердить отправку или 'Нет❌', чтобы редактировать блюдо.\n\n"
				+ "Название: " + dish_data["name"] + "\n\nКатегория: " + category + "\n\nГруппа: " + dish_data["group"] +
				 "\n\nОписание: " + dish_data["desc"] + "\n\nСсылка на изображение: " + dish_data["img-url"],
				 reply_markup = kb.inline_kb_full)

	await state.set_state(EventDishStates.all()[14])

# dish sending confirmation
@dp.message_handler(state = EventDishStates.SF)
async def conf_dish(message: types.Message):
	state = dp.current_state(user = message.from_user.id)

	if(message.text == 'Да✅'):
		# creating insert query
		insert_query = "INSERT INTO dishes(NAME, CATEGORY, DISH_GROUP, DESCRIPTION, IMG_URL) VALUES(%s, %s, %s, %s, %s);"	
		cursor.execute(insert_query, (dish_data["name"], dish_data["category"], dish_data["group"], dish_data["desc"], dish_data["img-url"]))

		connection.commit()

		dish_data.clear()

		await message.answer("Новое блюдо добавлено в базу данных!😎\nДля продолжения работы введите команду.", reply_markup = None)
		await state.set_state(EventDishStates.all()[8])
	elif(message.text == 'Нет❌'):
		await message.answer("Отправка отменена⚠️\nБлюдо отправлено на доработку!")
		await message.answer("Сперва введите параметр (цифрой), который желаете изменить.\nЧерез пробел введите новое значение параметра.\n\n"
			+ "Параметры:\n" + "1 - Имя\n" + "2 - Категория\n" + "3 - Группа\n" + "4 - Описание\n" + "5 - Ссылка на изображение\n" + "delete - Удалить блюдо\n\n"
			+ "Пример:\n" + "3 Десерт")

		await state.set_state(EventDishStates.all()[15])

# dish correction
@dp.message_handler(state = EventDishStates.SG)
async def corr_dish(message: types.Message):
	corrected = False

	state = dp.current_state(user = message.from_user.id)

	if(message.text[0].isdigit() and len(message.text) >= 3):
		if(int(message.text[0]) == 1):
			if(len(message.text[2:]) <= 25):
				dish_data["name"] = message.text[2:]

				corrected = True
			else:
				await message.answer("Длина названия не должна превышать 25 символов⚠️")
		elif(int(message.text[0]) == 2):
			if(len(message.text) == 3 and message.text[2].isdigit()):
				dish_data["name"] = message.text[2]

				corrected = True
			else:
				await message.answer("Неверный формат! Введите данный параметр в виде \"НОМЕР_ПАРАМЕТРА НОМЕР_КАТЕГОРИИ\"⚠️")
		elif(int(message.text[0]) == 3):
			if(len(message.text[2:]) <= 25):
				dish_data["group"] = message.text[2:]

				corrected = True
			else:
				await message.answer("Длина названия групы не должна превышать 25 символов⚠️")
		elif(int(message.text[0]) == 4):
			if(len(message.text[2:]) <= 100):
				dish_data["desc"] = message.text[2:]

				corrected = True
			else:
				await message.answer("Длина описания не должна превышать 100 символов⚠️")
		elif(int(message.text[0]) == 5):
			dish_data["img-url"] = message.text[2:]

			corrected = True
	elif(message.text == "delete"):
		dish_data.clear()
		await message.answer("Блюдо удалено!⚠️")
		await state.set_state(EventDishStates.all()[8])
	else:
		await message.answer("Неверный формат! Попробуйте снова!")

	if(corrected):
		await message.answer("Правки внесены!")
		await state.set_state(EventDishStates.all()[14]) #!!!

		category = ""
		if(dish_data["category"] == 1):
			category = "Готовое меню"
		else:
			category = "Самостоятельное блюдо"

		await message.answer("Готово!🥳\nПроверьте данные и нажиите 'Да✅', чтобы подтвердить отправку или 'Нет❌', чтобы редактировать блюдо.\n\n"
					+ "Название: " + dish_data["name"] + "\n\nКатегория: " + category + "\n\nГруппа: " + dish_data["group"] +
					 "\n\nОписание: " + dish_data["desc"] + "\n\nСсылка на изображение: " + dish_data["img-url"],
					 reply_markup = kb.inline_kb_full)

# final state (neutral)
@dp.message_handler(state = EventDishStates.S8)
async def final_state_reply(message: types.Message):
	if(message.text != "/add_dish" and message.text != "/add_event" and message.text != "/help" and message.text != "/delete"):
		await message.answer("Введите одну из команд для продолжения работы.\nПолный список команд - /help")

# run long-polling
if __name__ == "__main__":
	executor.start_polling(dp, skip_updates = True)