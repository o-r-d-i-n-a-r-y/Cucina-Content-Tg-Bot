from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

inline_kb_full = ReplyKeyboardMarkup(row_width = 2, resize_keyboard = True, one_time_keyboard = True)
inline_btn_1 = KeyboardButton('Да✅', callback_data = 'btn_yes')
inline_btn_2 = KeyboardButton('Нет❌', callback_data = 'btn_no')
inline_kb_full.row(inline_btn_1, inline_btn_2) # 1 - yes, 2 - no

inline_kb_delete = ReplyKeyboardMarkup(row_width = 2, resize_keyboard = True, one_time_keyboard = True)
delete_btn_1 = KeyboardButton('Событие📰', callback_data = 'btn_del_event')
delete_btn_2 = KeyboardButton('Блюдо🍽', callback_data = 'btn_del_dish')
inline_kb_delete.row(delete_btn_1, delete_btn_2) # 1 - event, 2 - dish