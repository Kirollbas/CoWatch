"""Group management handlers"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
import io

from bot.database.session import SessionLocal
from bot.database.repositories import SlotRepository
from bot.services.kinopoisk_images_service import KinopoiskImagesService
from bot.services.watch_together_service import WatchTogetherService

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
        # Find the most recent slot that is ready for group creation where this user is a participant
        logger.info(f"🔍 Looking for active slots where user {creator_id} is a participant")
        slots = SlotRepository.get_user_participations(db, creator_id)
        logger.info(f"📊 Found {len(slots)} slots where user {creator_id} is a participant")
        
        active_slot = None
        
        # Find the most recent slot that is ready for group creation (full or open with enough participants)
        # Sort by ID descending to get the newest slot first
        sorted_slots = sorted(slots, key=lambda x: x.id, reverse=True)
        
        for slot in sorted_slots:
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
        logger.info(f"🔍 DEBUG: Found slot ID: {active_slot.id}")
        logger.info(f"🔍 DEBUG: Movie ID: {active_slot.movie.id}")
        logger.info(f"🔍 DEBUG: Movie title: {active_slot.movie.title}")
        logger.info(f"🔍 DEBUG: Movie Kinopoisk ID: {active_slot.movie.kinopoisk_id}")
        
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
        
        # Try to set movie poster as group avatar
        await set_movie_poster_as_avatar(context, group_id, active_slot.movie.kinopoisk_id)
        
        # Enable chat history for new members
        await enable_chat_history_for_new_members(context, group_id)
        
        # Create Watch Together room
        logger.info(f"🎬 Creating Watch Together room for slot {active_slot.id}")
        wt_room_url = None
        try:
            wt_room_url = WatchTogetherService.create_wt_room(db, active_slot)
            if wt_room_url:
                logger.info(f"✅ Watch Together room created: {wt_room_url}")
            else:
                logger.warning(f"⚠️ Failed to create Watch Together room for slot {active_slot.id}")
        except Exception as e:
            logger.error(f"❌ Error creating Watch Together room: {e}")
        
        # Create invite link
        logger.info(f"🔗 Creating invite link for group {group_id}")
        try:
            invite_link = await context.bot.create_chat_invite_link(
                chat_id=group_id,
                name=f"Приглашение на {active_slot.movie.title}",
                member_limit=len(active_slot.participants)
            )
            
            logger.info(f"✅ Created invite link: {invite_link.invite_link}")
            
            # Get participants info from database
            logger.info(f"📤 Preparing participants list for {len(active_slot.participants)} participants")
            participants_info = []
            for participant in active_slot.participants:
                user = participant.user  # Use the relationship to get User data
                if user.username:
                    participants_info.append(f"• @{user.username} ({user.first_name})")
                else:
                    participants_info.append(f"• {user.first_name}")
                logger.info(f"✅ Added participant: {user.first_name} (ID: {user.id})")
            
            # Send success message to group with participants list
            wt_section = ""
            if wt_room_url:
                wt_section = f"""
🎥 **Watch Together комната:**
{wt_room_url}

"""
            
            success_msg = f"""✅ **Группа настроена!**

🎬 **Фильм:** {active_slot.movie.title}
📅 **Время:** {active_slot.datetime.strftime('%d.%m.%Y в %H:%M')}
👥 **Участники:** {len(active_slot.participants)}

👥 **Список участников:**
{chr(10).join(participants_info)}
{wt_section}🔗 **Ссылка-приглашение создана!**
Отправляю её всем участникам слота...

🍿 **Приятного просмотра!**"""
            
            await context.bot.send_message(
                chat_id=group_id,
                text=success_msg,
                parse_mode="Markdown"
            )
            logger.info(f"✅ Sent success message to group with participants list")
            
            # Send invite link to all slot participants
            logger.info(f"📨 Sending invites to participants...")
            
            invite_msg = f"""🎉 **Группа создана!**

🎬 **Фильм:** {active_slot.movie.title}
📅 **Время:** {active_slot.datetime.strftime('%d.%m.%Y в %H:%M')}
👥 **Участники:** {len(active_slot.participants)}

🔗 **Ссылка на группу:**
{invite_link.invite_link}

👥 **Участники группы:**
{chr(10).join(participants_info)}
{wt_section}✅ **Группа готова к использованию!**
Переходите по ссылке и обсуждайте фильм.

🍿 **Приятного просмотра!**"""
            
            # Send to all participants except the creator
            logger.info(f"📨 Sending invites to participants...")
            
            for participant in active_slot.participants:
                logger.info(f"🔍 Processing participant {participant.user_id}, creator: {creator_id}")
                if participant.user_id != creator_id:
                    logger.info(f"📤 Attempting to send invite to user {participant.user_id}")
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


async def set_movie_poster_as_avatar(context: ContextTypes.DEFAULT_TYPE, group_id: int, kinopoisk_id: str):
    """Set movie poster as group avatar"""
    try:
        logger.info(f"🖼️ Attempting to set movie poster as avatar for group {group_id}")
        logger.info(f"🎬 Movie Kinopoisk ID: {kinopoisk_id}")
        
        # Check if kinopoisk_id is valid
        if not kinopoisk_id or kinopoisk_id == "None":
            logger.warning(f"⚠️ Invalid Kinopoisk ID: {kinopoisk_id}")
            return
        
        # Check bot permissions first
        try:
            bot_member = await context.bot.get_chat_member(group_id, context.bot.id)
            if bot_member.status not in ['administrator', 'creator']:
                logger.warning(f"⚠️ Bot is not admin in group {group_id}, cannot set photo")
                return
            
            # Check if bot has permission to change group info
            if hasattr(bot_member, 'can_change_info') and not bot_member.can_change_info:
                logger.warning(f"⚠️ Bot doesn't have permission to change group info")
                return
                
        except Exception as e:
            logger.warning(f"⚠️ Could not check bot permissions: {e}")
            # Continue anyway, maybe it will work
        
        # Get the best poster URL
        poster_url = KinopoiskImagesService.get_best_poster(kinopoisk_id)
        
        if not poster_url:
            logger.warning(f"⚠️ No poster found for movie {kinopoisk_id}")
            return
        
        logger.info(f"🔗 Found poster URL: {poster_url}")
        
        # Download the poster image
        image_data = KinopoiskImagesService.download_image(poster_url)
        
        if not image_data:
            logger.warning(f"⚠️ Failed to download poster from {poster_url}")
            return
        
        logger.info(f"📥 Downloaded poster image ({len(image_data)} bytes)")
        
        # Create BytesIO object for Telegram
        image_file = io.BytesIO(image_data)
        image_file.name = "poster.jpg"
        
        # Set the group photo
        await context.bot.set_chat_photo(chat_id=group_id, photo=image_file)
        logger.info(f"✅ Successfully set movie poster as group avatar")
        
    except Exception as e:
        logger.error(f"❌ Failed to set movie poster as avatar: {e}")
        logger.error(f"❌ Error details: {type(e).__name__}: {str(e)}")
        
        # Send message to group about the limitation
        try:
            await context.bot.send_message(
                chat_id=group_id,
                text="ℹ️ Не удалось установить постер фильма как аватарку группы.\n"
                     "Для этого боту нужны права администратора с возможностью изменения информации о группе.",
                parse_mode="Markdown"
            )
        except:
            pass  # Don't fail if we can't send the message


async def enable_chat_history_for_new_members(context: ContextTypes.DEFAULT_TYPE, group_id: int):
    """Enable chat history visibility for new members"""
    try:
        logger.info(f"📜 Attempting to enable chat history for new members in group {group_id}")
        
        # Bot API cannot directly change "Chat History for new members" setting
        # This setting can only be changed by group admins manually
        # We'll send instructions to the group creator instead
        
        try:
            await context.bot.send_message(
                chat_id=group_id,
                text="📜 **Настройка истории сообщений**\n\n"
                     "ℹ️ Для лучшего опыта новых участников рекомендуется включить видимость истории сообщений:\n\n"
                     "1️⃣ Откройте настройки группы\n"
                     "2️⃣ Перейдите в раздел \"Разрешения\"\n"
                     "3️⃣ Найдите \"Chat History for new members\"\n"
                     "4️⃣ Установите значение \"Visible\"\n\n"
                     "✅ Это позволит новым участникам видеть предыдущие сообщения и лучше понимать контекст обсуждения фильма.",
                parse_mode="Markdown"
            )
            logger.info(f"✅ Sent chat history instructions to group {group_id}")
        except Exception as msg_error:
            logger.warning(f"⚠️ Could not send history instructions: {msg_error}")
        
        # Set basic permissions to ensure group functionality
        from telegram import ChatPermissions
        
        try:
            # Get current chat info
            chat = await context.bot.get_chat(group_id)
            logger.info(f"📊 Current chat type: {chat.type}")
            
            # For groups and supergroups, ensure basic permissions are set
            if chat.type in ['group', 'supergroup']:
                # Create standard permissions for movie discussion groups
                permissions = ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_change_info=False,
                    can_invite_users=True,
                    can_pin_messages=False
                )
                
                # Set the permissions
                await context.bot.set_chat_permissions(group_id, permissions)
                logger.info(f"✅ Set standard chat permissions for movie discussion")
                
            else:
                logger.info(f"ℹ️ Chat type {chat.type} doesn't support permission modifications")
                
        except Exception as perm_error:
            logger.warning(f"⚠️ Could not set chat permissions: {perm_error}")
        
    except Exception as e:
        logger.error(f"❌ Failed to configure chat history settings: {e}")
        logger.error(f"❌ Error details: {type(e).__name__}: {str(e)}")
        
        # This is not a critical error, so we continue with group setup
        logger.info("ℹ️ Continuing with group setup despite history setting failure")

