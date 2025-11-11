"""Slot handlers - my_slots, join, leave, cancel"""
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from datetime import datetime

from bot.database.session import SessionLocal
from bot.database.repositories import (
    SlotRepository, SlotParticipantRepository, 
    RoomRepository, UserRepository
)
from bot.database.models import SlotParticipant
from bot.services.room_manager import RoomManager
from bot.utils.keyboards import get_user_slots_keyboard, get_participant_slots_keyboard
from bot.utils.formatters import format_slot_info
from bot.constants import SlotStatus


async def my_slots_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /my_slots command"""
    user_id = update.effective_user.id
    
    db: Session = SessionLocal()
    try:
        # Get slots created by user
        created_slots = SlotRepository.get_by_creator(db, user_id)
        
        if not created_slots:
            await update.message.reply_text("У вас пока нет созданных слотов.")
            return
        
        text = "📅 <b>Ваши созданные слоты:</b>\n\n"
        for slot in created_slots:
            participants_count = len(slot.participants)
            text += f"• {slot.movie.title} - {slot.datetime.strftime('%d.%m.%Y %H:%M')} "
            text += f"({participants_count}/{slot.min_participants})\n"
        
        await update.message.reply_text(text, parse_mode="HTML")
    finally:
        db.close()


async def join_slot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle join_slot callback"""
    query = update.callback_query
    await query.answer()
    
    slot_id = int(query.data.split(":")[1])
    user_id = query.from_user.id
    
    db: Session = SessionLocal()
    try:
        slot = SlotRepository.get_by_id(db, slot_id)
        if not slot:
            await query.edit_message_text("❌ Слот не найден.")
            return
        
        # Check if already participating
        existing = db.query(SlotParticipant).filter(
            SlotParticipant.slot_id == slot_id,
            SlotParticipant.user_id == user_id
        ).first()
        
        if existing:
            await query.edit_message_text("Вы уже участвуете в этом слоте.")
            return
        
        # Check if slot is full
        if slot.max_participants and len(slot.participants) >= slot.max_participants:
            await query.edit_message_text("❌ Слот заполнен.")
            return
        
        # Add participant
        SlotParticipantRepository.add_participant(db, slot_id, user_id)
        
        # Check if should create room
        if RoomManager.should_create_room(slot):
            # Create room
            room = RoomRepository.create(db, slot_id)
            slot.status = SlotStatus.FULL
            db.commit()
            
            # Stub: would create Telegram group here
            RoomManager.create_room_for_slot(slot)
            
            # Notify creator
            creator = UserRepository.get_by_id(db, slot.creator_id)
            if creator:
                await context.bot.send_message(
                    chat_id=slot.creator_id,
                    text=f"✅ Набралось достаточно участников для слота!\n\n{format_slot_info(slot)}",
                    parse_mode="HTML"
                )
        
        await query.edit_message_text(
            f"✅ Вы присоединились к слоту!\n\n{format_slot_info(slot)}",
            parse_mode="HTML"
        )
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")
    finally:
        db.close()


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command"""
    user_id = update.effective_user.id
    
    db: Session = SessionLocal()
    try:
        # Get slots where user is participant (not creator)
        participations = SlotRepository.get_user_participations(db, user_id)
        
        # Filter out slots created by user
        user_slots = [s for s in participations if s.creator_id != user_id]
        
        if not user_slots:
            await update.message.reply_text("Вы не участвуете ни в одном слоте.")
            return
        
        await update.message.reply_text(
            "Выберите слот, из которого хотите выйти:",
            reply_markup=get_participant_slots_keyboard(user_slots)
        )
    finally:
        db.close()


async def leave_slot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle leave_slot callback"""
    query = update.callback_query
    await query.answer()
    
    slot_id = int(query.data.split(":")[1])
    user_id = query.from_user.id
    
    db: Session = SessionLocal()
    try:
        slot = SlotRepository.get_by_id(db, slot_id)
        if not slot:
            await query.edit_message_text("❌ Слот не найден.")
            return
        
        # Check if user is creator
        if slot.creator_id == user_id:
            await query.edit_message_text("❌ Вы не можете выйти из своего слота. Удалите слот, если нужно.")
            return
        
        # Remove participant
        success = SlotParticipantRepository.remove_participant(db, slot_id, user_id)
        
        if success:
            await query.edit_message_text("✅ Вы вышли из слота.")
        else:
            await query.edit_message_text("❌ Вы не участвуете в этом слоте.")
    finally:
        db.close()

