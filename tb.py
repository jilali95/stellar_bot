import os
import time
import pandas as pd
import requests
import gdown
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ✅ Print environment variables for debugging
print(f"CSV_URL: {os.getenv('CSV_URL')}")
print(f"USERS_S: {os.getenv('USERS_S')}")

# ✅ Read allowed users from GitHub Secret
users_s = os.getenv("USERS_S", "").strip()
ALLOWED_USERS = [int(x) for x in users_s.split(',')] if users_s else []

# ✅ Get Google Drive file ID directly from environment variable
file_id = os.getenv("CSV_URL")  # Contains only the file ID, not a full URL

df = None  # Initialize df to avoid reference errors

if file_id:
    try:
        # ✅ Construct direct download URL
        download_url = f"https://drive.google.com/uc?id={file_id}"

        # ✅ Get last modification date from Google Drive HTTP headers
        response = requests.head(download_url, allow_redirects=True)
        if response.status_code == 200 and "Last-Modified" in response.headers:
            last_modification = time.strftime('%d.%m.%y', time.strptime(response.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S %Z"))
            print(f"✅ Last modified: {last_modification}")
        else:
            last_modification = "Unknown"
            print("⚠️ Could not retrieve last modification date.")

        # ✅ Download the CSV using gdown
        output_path = "temp_stock_data.csv"
        gdown.download(download_url, output_path, quiet=False, use_cookies=False)

        # ✅ Load the CSV into a DataFrame
        df = pd.read_csv(output_path, delimiter=';', encoding='ISO-8859-1')
        print("✅ CSV loaded successfully!")

        # ✅ Check for required columns
        required_columns = {'ARTICLE', 'DERNIER_PRIX_ACHAT', 'pharmacien', 'QTE'}
        if not required_columns.issubset(df.columns):
            raise ValueError("⚠️ Missing expected columns in CSV!")

    except Exception as e:
        print(f"⚠️ Error reading CSV: {e}")
        df = None  # Reset df on error

else:
    print("⚠️ Error: CSV_URL environment variable is missing or invalid!")

# ✅ Handle "/h" command
async def h(update: Update, context: CallbackContext):
    bot = context.bot
    commands = [
        ('a', 'Start the bot'),
        ('v', 'Get help information'),
        ('h', 'Show bot information'),
        ('z', 'Show bot information')
    ]
    await bot.set_my_commands(commands)
    await update.message.reply_text("Menu button updated with commands.")

# ✅ Handle text messages
async def handle_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    print(user_id, " _ ", user_name)

    if user_id in ALLOWED_USERS:
        if df is None:
            await update.message.reply_text("⚠️ Data not available. Please check the CSV source.")
            return

        user_input = update.message.text.strip().lower()
        search_term = user_input
        matches = []

        for _, row in df.iterrows():
            if all(word in str(row.get('ARTICLE', '')).lower() for word in search_term.split()):
                try:
                    benif = ((row['pharmacien'] - row['DERNIER_PRIX_ACHAT']) / row['DERNIER_PRIX_ACHAT']) * 100
                    matches.append(
                        f"{row['ARTICLE']},\nGrossiste: {row['DERNIER_PRIX_ACHAT']:.2f} DA,\n"
                        f"Pharmacien: {row['pharmacien']:.2f} DA,\nBénéfice: {benif:.0f} %\nQNT: {row['QTE']}"
                    )
                except KeyError:
                    print(f"⚠️ Missing expected data in row: {row}")
                    continue

        if matches:
            await update.message.reply_text(f"\n________________________________\n".join(matches))
            num_articles = len(matches)
            await update.message.reply_text(f"\nNombre d'articles: {num_articles}\nDernière mise à jour: {last_modification}")
        else:
            await update.message.reply_text("Aucune correspondance trouvée. Essayez d'affiner votre recherche.")
    else:
        await update.message.reply_text("❌ Vous n'êtes pas autorisé à utiliser ce bot.")

# ✅ Main function to start the bot
def main():
    print(os.getenv("TELEGRAM_BOT_TOKEN"))
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CommandHandler('h', h))
    application.run_polling()

if __name__ == '__main__':
    main()
