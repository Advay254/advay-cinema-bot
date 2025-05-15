import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler
from pymongo import MongoClient

BOT_TOKEN = os.environ.get('BOT_TOKEN')
MONGO_URI = os.environ.get('MONGO_URI')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

client = MongoClient(MONGO_URI)
db = client.filebot
files_collection = db.files

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎬 Movies", callback_data='movies')],
        [InlineKeyboardButton("📺 Anime Series", callback_data='anime')],
        [InlineKeyboardButton("🔍 Search", callback_data='search')],
        [InlineKeyboardButton("📁 Categories", callback_data='categories')],
        [InlineKeyboardButton("📩 Request Content", callback_data='request')],
        [InlineKeyboardButton("❓ How to Download", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def movies_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🆕 Latest Uploads", callback_data='latest_movies')],
        [InlineKeyboardButton("⭐ Popular", callback_data='popular_movies')],
        [InlineKeyboardButton("🎭 Genres", callback_data='movie_genres')],
        [InlineKeyboardButton("📅 Year", callback_data='movie_year')],
        [InlineKeyboardButton("↩️ Back", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def anime_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📺 Ongoing Series", callback_data='ongoing_anime')],
        [InlineKeyboardButton("✅ Completed Series", callback_data='completed_anime')],
        [InlineKeyboardButton("🎬 Anime Movies", callback_data='anime_movies')],
        [InlineKeyboardButton("🎭 Anime Genres", callback_data='anime_genres')],
        [InlineKeyboardButton("↩️ Back", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def categories_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎭 Action", callback_data='category_action')],
        [InlineKeyboardButton("❤️ Romance", callback_data='category_romance')],
        [InlineKeyboardButton("🔪 Horror", callback_data='category_horror')],
        [InlineKeyboardButton("🤣 Comedy", callback_data='category_comedy')],
        [InlineKeyboardButton("🌟 Adventure", callback_data='category_adventure')],
        [InlineKeyboardButton("🎭 Drama", callback_data='category_drama')],
        [InlineKeyboardButton("↩️ Back", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def start(update: Update, context: CallbackContext) -> None:
    welcome_text = "🎉 Welcome to Advay Cinema Bot!\n\nYour one-stop destination for Movies and Anime."
    update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())

def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    if query.data == 'main_menu':
        query.edit_message_text(
            text="🎉 Welcome to Advay Cinema Bot!\n\nYour one-stop destination for Movies and Anime.",
            reply_markup=main_menu_keyboard()
        )
    elif query.data == 'movies':
        query.edit_message_text(
            text="🎬 Movies Section\nChoose from the options below:",
            reply_markup=movies_menu_keyboard()
        )
    elif query.data == 'anime':
        query.edit_message_text(
            text="📺 Anime Section\nChoose from the options below:",
            reply_markup=anime_menu_keyboard()
        )
    elif query.data == 'categories':
        query.edit_message_text(
            text="📁 Categories\nSelect your preferred genre:",
            reply_markup=categories_menu_keyboard()
        )
    elif query.data == 'search':
        query.edit_message_text(
            text="🔍 Search\nUse /search followed by the movie or anime name to search our database."
        )
    elif query.data == 'request':
        query.edit_message_text(
            text="📩 Request Content\nSend your movie or anime requests here. We'll try to add them as soon as possible!"
        )
    elif query.data == 'help':
        query.edit_message_text(
            text="❓ How to Download\n\n1. Search for your content using /search\n2. Click on the download button\n3. The file will be sent to you directly\n\nFor any issues, contact @admin"
        )

def search_files(update: Update, context: CallbackContext) -> None:
    query = ' '.join(context.args)
    if not query:
        update.message.reply_text('🔍 Please provide a search term.')
        return

    results = files_collection.find({'file_name': {'$regex': query, '$options': 'i'}})
    
    if results.count() == 0:
        update.message.reply_text('❌ No files found matching your search.')
        return

    for result in results:
        file_id = result['file_id']
        file_name = result['file_name']
        
        keyboard = [[InlineKeyboardButton("📥 Download", callback_data=f"download_{file_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(
            f"📁 File: {file_name}",
            reply_markup=reply_markup
        )

def store_file(update: Update, context: CallbackContext) -> None:
    file = update.message.document
    if not file:
        update.message.reply_text('📤 Please send a file.')
        return

    file_name = file.file_name
    file_id = file.file_id
    
    file_data = {
        'file_name': file_name,
        'file_id': file_id,
        'uploaded_by': update.effective_user.id
    }
    files_collection.insert_one(file_data)
    
    context.bot.forward_message(
        chat_id=CHANNEL_ID,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id
    )
    
    update.message.reply_text(f'✅ File "{file_name}" has been stored successfully!')

def main() -> None:
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("search", search_files))
    dispatcher.add_handler(MessageHandler(Filters.document, store_file))
    dispatcher.add_handler(CallbackQueryHandler(button_callback))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
