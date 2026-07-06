import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_URL = os.environ.get("API_URL")
API_KEY = os.environ.get("API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен!")

PHONE, NAME, PASSPORT, EMAIL = range(4)

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 По телефону", callback_data="search_phone")],
        [InlineKeyboardButton("👤 По ФИО", callback_data="search_name")],
        [InlineKeyboardButton("🪪 По паспорту", callback_data="search_passport")],
        [InlineKeyboardButton("📧 По email", callback_data="search_email")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ])

def call_api(endpoint, params):
    try:
        r = requests.get(f"{API_URL}{endpoint}", headers={"X-API-Key": API_KEY}, params=params, timeout=15)
        return r.json() if r.status_code == 200 else {"error": f"Ошибка {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def format_results(data):
    if not data or "error" in data or not data.get('success') or data.get('found') == 0:
        return "❌ Ничего не найдено."
    msg = f"🔍 Найдено {data['found']} записей:\n\n"
    for res in data.get('results', []):
        parts = []
        if res.get('full_name'): parts.append(f"👤 ФИО: {res['full_name']}")
        if res.get('phone'): parts.append(f"📱 Телефон: +{res['phone']}")
        if res.get('birth_date'): parts.append(f"🎂 Дата рождения: {res['birth_date']}")
        if res.get('address'): parts.append(f"🏠 Адрес: {res['address']}")
        if res.get('passport'): parts.append(f"🪪 Паспорт: {res['passport']}")
        if res.get('email'): parts.append(f"📧 Email: {res['email']}")
        if res.get('inn'): parts.append(f"🆔 ИНН: {res['inn']}")
        if res.get('snils'): parts.append(f"🆔 СНИЛС: {res['snils']}")
        if res.get('source'): parts.append(f"📂 Источник: {res['source']}")
        msg += "\n".join(parts) + "\n\n"
    return msg

async def start(update, context):
    await update.message.reply_text(
        "🕊️ **Бот «Ангел»**\n\nЯ ищу людей в базе данных (124 млн записей).\nВыбери режим:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "search_phone":
        await query.edit_message_text("📱 Введите номер телефона:")
        return PHONE
    elif data == "search_name":
        await query.edit_message_text("👤 Введите ФИО:")
        return NAME
    elif data == "search_passport":
        await query.edit_message_text("🪪 Введите паспорт/СНИЛС/ИНН:")
        return PASSPORT
    elif data == "search_email":
        await query.edit_message_text("📧 Введите email:")
        return EMAIL
    elif data == "stats":
        result = call_api("/stats", {})
        if result and "total_records" in result:
            msg = f"📊 **Статистика БД**\n\n📝 Записей: {result['total_records']}\n🕊️ Статус: {result.get('status', '—')}"
        else:
            msg = "❌ Не удалось получить статистику."
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_main_keyboard())
        return ConversationHandler.END
    elif data == "help":
        await query.edit_message_text(
            "🕊️ **Помощь**\n\nПросто выбери режим и введи данные.\nЯ ищу по телефону, ФИО, паспорту, СНИЛС, ИНН или email.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    return ConversationHandler.END

async def handle_phone(update, context):
    data = call_api("/search/phone", {"number": update.message.text.strip()})
    await update.message.reply_text(format_results(data), reply_markup=get_main_keyboard())
    return ConversationHandler.END

async def handle_name(update, context):
    data = call_api("/search/name", {"query": update.message.text.strip()})
    await update.message.reply_text(format_results(data), reply_markup=get_main_keyboard())
    return ConversationHandler.END

async def handle_passport(update, context):
    data = call_api("/search/passport", {"number": update.message.text.strip()})
    await update.message.reply_text(format_results(data), reply_markup=get_main_keyboard())
    return ConversationHandler.END

async def handle_email(update, context):
    data = call_api("/search/email", {"email": update.message.text.strip()})
    await update.message.reply_text(format_results(data), reply_markup=get_main_keyboard())
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^search_")],
        states={
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            PASSPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_passport)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)],
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: u.message.reply_text("Отменено.", reply_markup=get_main_keyboard()))]
    )
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^help$"))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^stats$"))
    app.add_handler(CommandHandler("start", start))
    print("🤖 Бот «Ангел» запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
