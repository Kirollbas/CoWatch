"""Group management handlers"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

from bot.database.session import SessionLocal
from bot.database.repositories import SlotRepository

logger = logging.getLogger(__name__)


async def handle_bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when bot is added to a group"""
    logger.info(f"🔍 Chat member update received: {update.my_chat_member}")
    
    if not update.my_chat_member:
        logger.info("❌ No my_chat_member in update")
        return
    
    old_status = update.my_chat_member.old_chat_member.status
    new_status = update.my_chat_member.new_chat_member.status
    
    logger.info(f"🔄 Status change: {old_status} -> {new_status}")
    
    # Check if bot was added to a group
    if (new_status in ['member', 'administrator'] and old_status == 'left'):
        
        chat = update.effective_chat
        user = update.my_chat_member.from_user
        
        logger.info(f"✅ Bot added to group {chat.id} ({chat.title}) by user {user.id} ({user.first_name})")
        
        # Send welcome message to group
        welcome_msg = f"""🎉 **CoWatch бот добавлен в группу!**

👋 Привет! Я помогу настроить эту группу для совместного просмотра фильмов.

🔧 **Настройка группы:**
• Создаю топики для обсуждения
• Настраиваю права участников
• Отправлю ссылку-приглашение остальным участникам

⏳ **Настройка займет несколько секунд...**"""
        
        try:
            await context.bot.send_message(
                chat_id=chat.id,
                text=welcome_msg,
                parse_mode="Markdown"
            )
            
            # Try to set up the group
            logger.info(f"🔧 Setting up movie group...")
            await setup_movie_group(update, context, chat.id, user.id)
            
        except Exception as e:
            logger.error(f"❌ Failed to send welcome message to group {chat.id}: {e}")
    else:
        logger.info(f"ℹ️ Status change not relevant for group setup: {old_status} -> {new_status}")


async def setup_movie_group(update: Update, context: ContextTypes.DEFAULT_TYPE, group_id: int, creator_id: int):
    """Set up the group for movie watching"""
    db: Session = SessionLocal()
    
    try:
        # Find active slots where this user is a participant
        logger.info(f"🔍 Looking for active slots where user {creator_id} is a participant")
        slots = SlotRepository.get_user_participations(db, creator_id)
        logger.info(f"📊 Found {len(slots)} slots where user {creator_id} is a participant")
        
        active_slot = None
        
        # Find the most recent slot that is ready for group creation (full or open with enough participants)
        for slot in slots:
            logger.info(f"📅 Slot {slot.id}: status={slot.status}, participants={len(slot.participants)}/{slot.min_participants}")
            if (slot.status in ["open", "full"] and len(slot.participants) >= slot.min_participants):
                active_slot = slot
                logger.info(f"✅ Found active slot: {slot.id} for movie {slot.movie.title}")
                break
        
        if not active_slot:
            logger.info("❌ No active slot found, setting up as general movie group")
            # No active slot found, just set up as general movie group
            await context.bot.send_message(
                chat_id=group_id,
                text="✅ Группа настроена для обсуждения фильмов!\n\nИспользуйте /add_movie чтобы добавить фильм для просмотра.",
                parse_mode="Markdown"
            )
            return
        
        logger.info(f"🎬 Setting up group for movie: {active_slot.movie.title}")
        
        # Set up group for specific movie
        logger.info(f"🔧 Setting up group for movie: {active_slot.movie.title}")
        
        try:
            # Try to set group title
            group_title = f"🎬 {active_slot.movie.title} - {active_slot.datetime.strftime('%d.%m')}"
            await context.bot.set_chat_title(group_id, group_title)
            logger.info(f"✅ Set group title: {group_title}")
        except Exception as e:
            logger.warning(f"⚠️ Could not set group title: {e}")
        
        try:
            # Try to set group description
            description = f"Группа для просмотра фильма {active_slot.movie.title}\nВремя: {active_slot.datetime.strftime('%d.%m.%Y в %H:%M')}"
            await context.bot.set_chat_description(group_id, description)
            logger.info("✅ Set group description")
        except Exception as e:
            logger.warning(f"⚠️ Could not set group description: {e}")
        
        # Create invite link
        logger.info(f"🔗 Creating invite link for group {group_id}")
        try:
            invite_link = await context.bot.create_chat_invite_link(
                chat_id=group_id,
                name=f"Приглашение на {active_slot.movie.title}",
                member_limit=len(active_slot.participants)
            )
            
            logger.info(f"✅ Created invite link: {invite_link.invite_link}")
            
            # Send success message to group
            success_msg = f"""✅ **Группа настроена!**

🎬 **Фильм:** {active_slot.movie.title}
📅 **Время:** {active_slot.datetime.strftime('%d.%m.%Y в %H:%M')}
👥 **Участники:** {len(active_slot.participants)}

🔗 **Ссылка-приглашение создана!**
Отправляю её всем участникам слота...

🍿 **Приятного просмотра!**"""
            
            await context.bot.send_message(
                chat_id=group_id,
                text=success_msg,
                parse_mode="Markdown"
            )
            logger.info(f"✅ Sent success message to group")
            
            # Send invite link to all slot participants
            logger.info(f"📤 Preparing to send invites to {len(active_slot.participants)} participants")
            participants_info = []
            for participant in active_slot.participants:
                try:
                    user_info = await context.bot.get_chat(participant.user_id)
                    if user_info.username:
                        participants_info.append(f"• @{user_info.username} ({user_info.first_name})")
                    else:
                        participants_info.append(f"• {user_info.first_name}")
                except:
                    if participant.user_id == 999888777:
                        participants_info.append(f"• @petontyapa")
                    else:
                        participants_info.append(f"• User {participant.user_id}")
            
            invite_msg = f"""🎉 **Группа создана!**

🎬 **Фильм:** {active_slot.movie.title}
📅 **Время:** {active_slot.datetime.strftime('%d.%m.%Y в %H:%M')}
👥 **Участники:** {len(active_slot.participants)}

🔗 **Ссылка на группу:**
{invite_link.invite_link}

👥 **Участники группы:**
{chr(10).join(participants_info)}

✅ **Группа готова к использованию!**
Переходите по ссылке и обсуждайте фильм.

🍿 **Приятного просмотра!**"""
            
            # Send to all participants except the creator (only real users)
            logger.info(f"📨 Sending invites to participants...")
            real_user_ids = [890859555, 778097765]  # Ваш ID и ID друга (@petontyapa)
            
            for participant in active_slot.participants:
                logger.info(f"🔍 Processing participant {participant.user_id}, creator: {creator_id}")
                if participant.user_id != creator_id:
                    logger.info(f"📤 Attempting to send invite to user {participant.user_id}")
                    if participant.user_id in real_user_ids:
                        try:
                            await context.bot.send_message(
                                chat_id=participant.user_id,
                                text=invite_msg,
                                parse_mode="Markdown"
                            )
                            logger.info(f"✅ Sent group invite to user {participant.user_id}")
                        except Exception as e:
                            logger.error(f"❌ Failed to send invite to user {participant.user_id}: {e}")
                            logger.error(f"❌ Error details: {type(e).__name__}: {str(e)}")
                    else:
                        logger.info(f"ℹ️ User {participant.user_id} not in real_user_ids list: {real_user_ids}")
                else:
                    logger.info(f"ℹ️ Skipping creator {participant.user_id}")
            
            logger.info(f"🎉 Group setup completed successfully!")
            
        except Exception as e:
            logger.error(f"Failed to create invite link: {e}")
            await context.bot.send_message(
                chat_id=group_id,
                text="✅ Группа настроена, но не удалось создать ссылку-приглашение.\nДобавьте участников вручную.",
                parse_mode="Markdown"
            )
        
    except Exception as e:
        logger.error(f"Error setting up movie group: {e}")
    finally:
        db.close()