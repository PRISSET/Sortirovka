import asyncio
import csv
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

class ContactBot:
    def __init__(self):
        self.contacts = []
        self.current_index = 0
        self.load_contacts()
    
    def load_contacts(self):
        self.contacts = []
        if os.path.exists('base.csv'):
            with open('base.csv', 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row and len(row) >= 2:
                        name = row[0].strip()
                        phone = row[1].strip()
                        if name and phone:
                            self.contacts.append((name, phone))
    
    def save_contacts(self):
        with open('base.csv', 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            for name, phone in self.contacts:
                writer.writerow([name, phone])
    
    def save_to_file(self, filename, name, phone):
        with open(filename, 'a', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([name, phone])
    
    def get_current_contact(self):
        if self.current_index < len(self.contacts):
            return self.contacts[self.current_index]
        return None
    
    def remove_current_contact(self):
        if self.current_index < len(self.contacts):
            removed = self.contacts.pop(self.current_index)
            if self.current_index >= len(self.contacts):
                self.current_index = 0
            self.save_contacts()
            return removed
        return None

bot_instance = ContactBot()

async def start_handler(message: types.Message):
    await show_next_contact(message)

async def show_next_contact(message: types.Message):
    contact = bot_instance.get_current_contact()
    
    if not contact:
        await message.reply("Все контакты обработаны!")
        return
    
    name, phone = contact
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅", callback_data="verified"),
            InlineKeyboardButton(text="❌", callback_data="called")
        ]
    ])
    
    message_text = f"{name} - `{phone}`"
    
    await message.reply(
        message_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def button_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    
    contact = bot_instance.get_current_contact()
    if not contact:
        await callback_query.message.edit_text("Все контакты обработаны!")
        return
    
    name, phone = contact
    
    if callback_query.data == "verified":
        bot_instance.save_to_file('verified.csv', name, phone)
        bot_instance.remove_current_contact()
        await callback_query.message.edit_text(f"✅ {name} добавлен в verified")
        await asyncio.sleep(1)
        await show_next_contact_callback(callback_query)
    
    elif callback_query.data == "called":
        bot_instance.save_to_file('called.csv', name, phone)
        bot_instance.remove_current_contact()
        await callback_query.message.edit_text(f"❌ {name} добавлен в called")
        await asyncio.sleep(1)
        await show_next_contact_callback(callback_query)

async def show_next_contact_callback(callback_query: types.CallbackQuery):
    contact = bot_instance.get_current_contact()
    
    if not contact:
        await callback_query.message.edit_text("Все контакты обработаны!")
        return
    
    name, phone = contact
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅", callback_data="verified"),
            InlineKeyboardButton(text="❌", callback_data="called")
        ]
    ])
    
    message_text = f"{name} - `{phone}`"
    
    await callback_query.message.edit_text(
        message_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def next_contact_handler(message: types.Message):
    await show_next_contact(message)

async def reload_base_handler(message: types.Message):
    bot_instance.load_contacts()
    bot_instance.current_index = 0
    await message.reply(f"База перезагружена. Контактов: {len(bot_instance.contacts)}")
    await show_next_contact(message)

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    dp.message.register(start_handler, Command("start"))
    dp.message.register(next_contact_handler, Command("next"))
    dp.message.register(reload_base_handler, Command("reload"))
    dp.callback_query.register(button_callback, F.data.in_(["verified", "called"]))
    
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
