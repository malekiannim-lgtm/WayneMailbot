from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8104526913:AAGwJFszRsQkgSHB3xsEWgKcKgXZ8vaPACo"
OWNER_ID = 7898003403

blocked_users = set()
message_links = {}  # key: unique_id, value: user_id
reply_state = {}    # key: user_id, value: target_user_id

def build_keyboard(user_id, unique_id, seen=False):
    buttons = []
    if not seen:
        buttons.append(InlineKeyboardButton("✅ Seen", callback_data=f"seen_{unique_id}"))
    buttons.append(InlineKeyboardButton("✉️ پاسخ", callback_data=f"reply_{unique_id}"))
    buttons.append(InlineKeyboardButton("🚫 مسدود", callback_data=f"block_{user_id}"))
    return InlineKeyboardMarkup([buttons])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! پیام ناشناس خودتو بفرست.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in blocked_users:
        return

    msg = update.message
    msg_id = msg.message_id

    # حالت پاسخ‌دهی
    if user_id in reply_state:
        target_id = reply_state.pop(user_id)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ پاسخ متقابل", callback_data=f"backreply_{user_id}")]
        ])

        if msg.text:
            await context.bot.send_message(chat_id=target_id, text=f"🗨️ پاسخ:\n{msg.text}", reply_markup=keyboard)
        elif msg.photo:
            await context.bot.send_photo(chat_id=target_id, photo=msg.photo[-1].file_id, caption="🗨️ پاسخ تصویری", reply_markup=keyboard)
        elif msg.document:
            await context.bot.send_document(chat_id=target_id, document=msg.document.file_id, caption="🗨️ پاسخ فایل", reply_markup=keyboard)
        elif msg.video:
            await context.bot.send_video(chat_id=target_id, video=msg.video.file_id, caption="🗨️ پاسخ ویدیویی", reply_markup=keyboard)
        elif msg.sticker:
            await context.bot.send_sticker(chat_id=target_id, sticker=msg.sticker.file_id)
        await msg.reply_text("✅ پاسخ ارسال شد.")
        return

    # پیام جدید از کاربر
    unique_id = f"{user_id}_{msg_id}"
    message_links[unique_id] = user_id

    if msg.text:
        await context.bot.send_message(chat_id=OWNER_ID, text=f"📩 پیام جدید:\n{msg.text}", reply_markup=build_keyboard(user_id, unique_id))
    elif msg.photo:
        await context.bot.send_photo(chat_id=OWNER_ID, photo=msg.photo[-1].file_id, caption="📩 عکس جدید", reply_markup=build_keyboard(user_id, unique_id))
    elif msg.document:
        await context.bot.send_document(chat_id=OWNER_ID, document=msg.document.file_id, caption="📩 فایل جدید", reply_markup=build_keyboard(user_id, unique_id))
    elif msg.video:
        await context.bot.send_video(chat_id=OWNER_ID, video=msg.video.file_id, caption="📩 ویدیو جدید", reply_markup=build_keyboard(user_id, unique_id))
    elif msg.sticker:
        await context.bot.send_sticker(chat_id=OWNER_ID, sticker=msg.sticker.file_id)
        await context.bot.send_message(chat_id=OWNER_ID, text="📩 استیکر جدید", reply_markup=build_keyboard(user_id, unique_id))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("reply_"):
        unique_id = data.split("_", 1)[1]
        target_id = message_links.get(unique_id)
        if target_id:
            reply_state[OWNER_ID] = target_id
            await query.message.reply_text("✏️ پاسخ خود را بنویسید:")

    elif data.startswith("seen_"):
        unique_id = data.split("_", 1)[1]
        user_id = message_links.get(unique_id)

        # حذف فقط دکمه Seen از کیبورد
        current_keyboard = query.message.reply_markup.inline_keyboard
        new_keyboard = []

        for row in current_keyboard:
            new_row = [btn for btn in row if not btn.callback_data.startswith("seen_")]
            if new_row:
                new_keyboard.append(new_row)

        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(new_keyboard))

        # پیام به ادمین
        await query.message.reply_text("✅ پیام سین شد و برای کاربر ارسال شد.")

        # پیام به کاربر
        try:
            await context.bot.send_message(chat_id=user_id, text="👀 پیام شما توسط ادمین دیده شد.")
        except Exception as e:
            await query.message.reply_text(f"❗️ ارسال پیام به کاربر ناموفق بود: {e}")

    elif data.startswith("block_"):
        user_id = int(data.split("_")[1])
        if user_id in blocked_users:
            blocked_users.remove(user_id)
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚫 مسدود", callback_data=f"block_{user_id}")]
            ]))
            await query.message.reply_text("🔓 کاربر رفع مسدود شد.")
        else:
            blocked_users.add(user_id)
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔓 رفع مسدودیت", callback_data=f"block_{user_id}")]
            ]))
            await query.message.reply_text("🚫 کاربر مسدود شد.")

    elif data.startswith("backreply_"):
        sender_id = int(data.split("_")[1])
        reply_state[query.from_user.id] = sender_id
        await query.message.reply_text("✏️ پاسخ خود را بنویسید:")

# راه‌اندازی ربات
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()