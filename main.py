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
        [InlineKeyboardButton("🎬 Movies", callback_data="movies")],
        [InlineKeyboardButton("📺 Anime Series", callback_data="anime")],
        [InlineKeyboardButton("🔍 Search", callback_data="search")],
        [InlineKeyboardButton("📁 Categories", callback_data="categories")],
        [InlineKeyboardButton("📩 Request Content", callback_data="request")],
        [InlineKeyboardButton("❓ How to Download", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def movies_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🆕 Latest Uploads", callback_data="latest_movies")],
        [InlineKeyboardButton("⭐ Popular", callback_data="popular_movies")],
        [InlineKeyboardButton("🎭 Genres", callback_data="movie_genres")],
        [InlineKeyboardButton("📅 Year", callback_data="movie_year")],
        [InlineKeyboardButton("↩️ Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def anime_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📺 Ongoing Series", callback_data="ongoing_anime")],
        [InlineKeyboardButton("✅ Completed Series", callback_data="completed_anime")],
        [InlineKeyboardButton("🎬 Anime Movies", callback_data="anime_movies")],
        [InlineKeyboardButton("🎭 Anime Genres", callback_data="anime_genres")],
        [InlineKeyboardButton("↩️ Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def categories_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎭 Action", callback_data="cat_action")],
        [InlineKeyboardButton("❤️ Romance", callback_data="cat_romance")],
        [InlineKeyboardButton("🔪 Horror", callback_data="cat_horror")],
        [InlineKeyboardButton("🤣 Comedy", callback_data="cat_comedy")],
        [InlineKeyboardButton("🌟 Adventure", callback_data="cat_adventure")],
        [InlineKeyboardButton("🎭 Drama", callback_data="cat_drama")],
        [InlineKeyboardButton("↩️ Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def start(update: Update, context: CallbackContext):
    welcome_text = (
        "🎬 Welcome to Advay Cinema Bot!\n\n"
        "Browse our collection of Movies and Anime Series.\n"
        "Select an option below:"
    )
    update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if query.data == "main_menu":
        query.edit_message_text(
            "🎬 Main Menu\nSelect an option:",
            reply_markup=main_menu_keyboard()
        )
    elif query.data == "movies":
        query.edit_message_text(
            "🎬 Movies Section\nChoose category:",
            reply_markup=movies_menu_keyboard()
        )
    elif query.data == "anime":
        query.edit_message_text(
            "📺 Anime Section\nChoose category:",
            reply_markup=anime_menu_keyboard()
        )
    elif query.data == "categories":
        query.edit_message_text(
            "📁 Categories\nSelect genre:",
            reply_markup=categories_menu_keyboard()
        )

def search(update: Update, context: CallbackContext):
    query = ' '.join(context.args).lower()
    results = files_collection.find({
        '$or': [
            {'title': {'$regex': query, '$options': 'i'}},
            {'tags': query}
        ]
    })

    for result in results:
        keyboard = [[InlineKeyboardButton(
            "⬇️ Download",
            url=f"https://t.me/c/{CHANNEL_ID.strip('-')}/{result['message_id']}"
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        content_type = "🎬 Movie" if "#movie" in result['tags'] else "📺 Anime"
        message_text = (
            f"{content_type}: {result['title']}\n"
            f"Quality: {result.get('quality', 'N/A')}\n"
            f"Size: {result.get('size', 'N/A')}\n"
            f"Genre: {', '.join(tag for tag in result['tags'] if not tag in ['#movie', '#anime'])}"
        )
        
        update.message.reply_text(message_text, reply_markup=reply_markup)

def index_file(update: Update, context: CallbackContext):
    if update.channel_post:
        msg = update.channel_post
        if msg.video or msg.document:
            caption = msg.caption or ''
            tags = [word.lower() for word in caption.split() if word.startswith('#')]
            
            title_parts = [word for word in caption.split('\n')[0].split() 
                          if not word.startswith('#')]
            title = ' '.join(title_parts)
            
            quality = next((line.split(': ')[1] for line in caption.split('\n') 
                          if line.startswith('Quality:')), 'N/A')
            
            file_data = {
                'message_id': msg.message_id,
                'title': title,
                'tags': tags,
                'quality': quality,
                'size': msg.video.file_size if msg.video else msg.document.file_size
            }
            
            files_collection.insert_one(file_data)

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("search", search))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.update.channel_post, index_file))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
