"""Keyboard utilities for inline and reply keyboards"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard():
    """Get main menu reply keyboard"""
    keyboard = [
        [KeyboardButton("/add_movie"), KeyboardButton("/my_slots")],
        [KeyboardButton("/my_rooms"), KeyboardButton("/profile")],
        [KeyboardButton("/help")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_movie_actions_keyboard(movie_id: int):
    """Get keyboard for movie actions"""
    keyboard = [
        [
            InlineKeyboardButton("Создать слот", callback_data=f"create_slot:{movie_id}"),
            InlineKeyboardButton("Найти слоты", callback_data=f"find_slots:{movie_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_slots_list_keyboard(slots):
    """Get keyboard with list of slots"""
    buttons = []
    for slot in slots:
        slot_datetime = slot.datetime.strftime("%d.%m.%Y %H:%M")
        buttons.append([
            InlineKeyboardButton(
                f"{slot_datetime} ({len(slot.participants)}/{slot.min_participants})",
                callback_data=f"join_slot:{slot.id}"
            )
        ])
    if not buttons:
        buttons.append([InlineKeyboardButton("Нет доступных слотов", callback_data="no_slots")])
    return InlineKeyboardMarkup(buttons)


def get_user_slots_keyboard(slots):
    """Get keyboard with user's slots"""
    buttons = []
    for slot in slots:
        slot_datetime = slot.datetime.strftime("%d.%m.%Y %H:%M")
        participants_count = len(slot.participants)
        buttons.append([
            InlineKeyboardButton(
                f"{slot.movie.title} - {slot_datetime} ({participants_count}/{slot.min_participants})",
                callback_data=f"view_slot:{slot.id}"
            )
        ])
    if not buttons:
        buttons.append([InlineKeyboardButton("У вас нет слотов", callback_data="no_slots")])
    return InlineKeyboardMarkup(buttons)


def get_participant_slots_keyboard(slots):
    """Get keyboard with slots where user is participant"""
    buttons = []
    for slot in slots:
        slot_datetime = slot.datetime.strftime("%d.%m.%Y %H:%M")
        buttons.append([
            InlineKeyboardButton(
                f"{slot.movie.title} - {slot_datetime}",
                callback_data=f"leave_slot:{slot.id}"
            )
        ])
    if not buttons:
        buttons.append([InlineKeyboardButton("Вы не участвуете в слотах", callback_data="no_slots")])
    return InlineKeyboardMarkup(buttons)


def get_rating_keyboard(room_id: int, user_id: int):
    """Get keyboard for rating users"""
    buttons = []
    for score in range(1, 6):
        buttons.append([
            InlineKeyboardButton(
                "⭐" * score,
                callback_data=f"rate_user:{room_id}:{user_id}:{score}"
            )
        ])
    return InlineKeyboardMarkup(buttons)

