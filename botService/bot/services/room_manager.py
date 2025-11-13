"""Room manager service (stub implementation)"""
import logging
from typing import List
from bot.database.models import Slot, Room

logger = logging.getLogger(__name__)

class RoomManager:
    """Manager for creating and managing rooms (stub implementation)"""
    
    @staticmethod
    def should_create_room(slot: Slot) -> bool:
        """Check if room should be created for slot"""
        participants_count = len(slot.participants)
        # Room should be created when we have enough participants and slot is not yet processed
        return participants_count >= slot.min_participants and slot.status in ["open", "full"]
    
    @staticmethod
    async def create_room_for_slot(slot: Slot, bot) -> Room:
        """
        Create Telegram channel with topics and send invite link to participants
        """
        try:
            logger.info(f"Creating Telegram channel for slot {slot.id}")
            logger.info(f"Movie: {slot.movie.title}")
            logger.info(f"Participants: {[p.user_id for p in slot.participants]}")
            
            # Create channel title and description
            channel_title = f"🎬 {slot.movie.title} - {slot.datetime.strftime('%d.%m %H:%M')}"
            channel_description = f"Канал для обсуждения фильма {slot.movie.title}\n📅 Время просмотра: {slot.datetime.strftime('%d.%m.%Y в %H:%M')}"
            
            # Автоматизированное решение: Последний участник создает группу одной кнопкой
            logger.info("Sending automated group creation request...")
            
            # Находим последнего участника (того, кто присоединился последним)
            last_participant = slot.participants[-1]
            other_participants = [p for p in slot.participants if p.user_id != last_participant.user_id]
            
            logger.info(f"Last participant (group creator): {last_participant.user_id}")
            logger.info(f"Other participants: {[p.user_id for p in other_participants]}")
            
            # Собираем информацию об участниках
            participants_info = []
            for participant in slot.participants:
                try:
                    user_info = await bot.get_chat(participant.user_id)
                    if user_info.username:
                        participants_info.append(f"• @{user_info.username} ({user_info.first_name})")
                    else:
                        participants_info.append(f"• {user_info.first_name}")
                except Exception as e:
                    logger.warning(f"Could not get info for user {participant.user_id}: {e}")
                    # Fallback to user data from database
                    user = participant.user
                    if user and user.username:
                        participants_info.append(f"• @{user.username} ({user.first_name})")
                    elif user and user.first_name:
                        participants_info.append(f"• {user.first_name}")
                    else:
                        participants_info.append(f"• User {participant.user_id}")
            
            # Создаем ссылку для автоматического создания группы
            # Используем Telegram deep linking для создания группы
            bot_username = (await bot.get_me()).username
            group_creation_link = f"https://t.me/{bot_username}?startgroup=movie_{slot.id}"
            
            # Отправляем последнему участнику кнопку для создания группы
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎬 Создать группу одним кликом", url=group_creation_link)]
            ])
            
            creator_msg = f"""🎉 **Слот заполнен! Создаем группу...**

🎬 **Фильм:** {slot.movie.title}
📅 **Время:** {slot.datetime.strftime('%d.%m.%Y в %H:%M')}
👥 **Участники:** {len(slot.participants)}

👥 **Все участники:**
{chr(10).join(participants_info)}

🤖 **Автоматическое создание группы:**
Нажмите кнопку ниже, чтобы автоматически создать группу для всех участников!

После создания группы:
1. Добавьте всех участников из списка выше
2. Бот автоматически отправит ссылку остальным участникам

💡 **Это займет всего 30 секунд!**"""
            
            try:
                # Отправляем создателю группы (последнему участнику)
                await bot.send_message(
                    chat_id=last_participant.user_id,
                    text=creator_msg,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                logger.info(f"✅ Sent group creation request to user {last_participant.user_id}")
                
                # Отправляем остальным участникам уведомление о том, что группа создается
                waiting_msg = f"""🎉 **Слот заполнен!**

🎬 **Фильм:** {slot.movie.title}
📅 **Время:** {slot.datetime.strftime('%d.%m.%Y в %H:%M')}
👥 **Участники:** {len(slot.participants)}

👥 **Участники слота:**
{chr(10).join(participants_info)}

⏳ **Создание группы...**
Один из участников создает группу для общения.
Вы получите ссылку-приглашение в течение минуты!

🍿 **Приятного просмотра!**"""
                
                # Отправляем всем остальным участникам
                for participant in other_participants:
                    try:
                        await bot.send_message(
                            chat_id=participant.user_id,
                            text=waiting_msg,
                            parse_mode="Markdown"
                        )
                        logger.info(f"✅ Sent waiting message to user {participant.user_id}")
                    except Exception as e:
                        logger.error(f"❌ Failed to send waiting message to user {participant.user_id}: {e}")
                
                # Сохраняем информацию о слоте для последующей обработки
                # Когда пользователь создаст группу, бот получит уведомление
                logger.info(f"📊 Group creation initiated for slot {slot.id}")
                
                return slot.room if slot.room else None
                
            except Exception as e:
                logger.error(f"Failed to send group creation request: {e}")
                return await RoomManager._fallback_notification(slot, bot)
            
        except Exception as e:
            logger.error(f"Failed to create room: {e}")
            return await RoomManager._fallback_notification(slot, bot)
    
    @staticmethod
    async def _fallback_notification(slot: Slot, bot) -> Room:
        """Send enhanced notification with participant contacts"""
        logger.info(f"Sending enhanced room notifications for slot {slot.id}")
        
        # Collect participant information
        participants_info = []
        for participant in slot.participants:
            try:
                user_info = await bot.get_chat(participant.user_id)
                if user_info.username:
                    participants_info.append(f"• @{user_info.username} ({user_info.first_name})")
                else:
                    participants_info.append(f"• {user_info.first_name}")
            except Exception as e:
                logger.warning(f"Could not get info for user {participant.user_id}: {e}")
                # Fallback to user data from database
                user = participant.user
                if user and user.username:
                    participants_info.append(f"• @{user.username} ({user.first_name})")
                elif user and user.first_name:
                    participants_info.append(f"• {user.first_name}")
                else:
                    participants_info.append(f"• User {participant.user_id}")
        
        # Create enhanced room message
        room_msg = f"""🎉 **Комната создана!**

🎬 **Фильм:** {slot.movie.title}
📅 **Время:** {slot.datetime.strftime('%d.%m.%Y в %H:%M')}
👥 **Участники:** {len(slot.participants)}

👥 **Контакты участников:**
{chr(10).join(participants_info)}

📱 **Как создать группу:**
1. Один из участников создает группу в Telegram
2. Добавляет всех участников по контактам выше
3. Включает темы (Topics): "💬 Обсуждение" и "⭐ Оценки"
4. Можно добавить описание: "Просмотр {slot.movie.title}"

💡 **Рекомендации:**
• Создайте группу за 30 минут до просмотра
• Используйте топики для структурированного общения
• После просмотра поделитесь впечатлениями в топике "Обсуждение"
• Оцените друг друга в топике "Оценки"

🍿 **Приятного просмотра!**"""
        
        # Send notification to all participants
        sent_count = 0
        failed_count = 0
        
        for participant in slot.participants:
            try:
                await bot.send_message(
                    chat_id=participant.user_id,
                    text=room_msg,
                    parse_mode="Markdown"
                )
                logger.info(f"✅ Sent enhanced notification to user {participant.user_id}")
                sent_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to notify user {participant.user_id}: {e}")
                failed_count += 1
        
        logger.info(f"📊 Fallback notification summary: {sent_count} sent, {failed_count} failed")
        
        return slot.room if slot.room else None
    
    @staticmethod
    def notify_participants(room: Room, message: str):
        """Notify all participants (stub)"""
        logger.info(f"STUB: Would notify participants of room {room.id}: {message}")
        # In future: send messages to all participants

