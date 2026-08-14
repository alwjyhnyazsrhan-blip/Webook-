from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from config import settings
from loguru import logger


class TelegramInterface:
    def __init__(self):
        self.app = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()
        self._add_handlers()

    def _add_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("login", self.login_command))
        self.app.add_handler(CommandHandler("snipe", self.snipe_command))
        self.app.add_handler(CommandHandler("status", self.status_command))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in settings.ADMIN_IDS:
            await update.message.reply_text("\u26d4\ufe0f Unauthorized access.")
            return

        welcome_text = (
            "\U0001f680 *Webook Sniper Bot v2.0*\n\n"
            "1. /login <email> - Authenticate account\n"
            "2. /snipe <slug> <event_id> - Start hunting\n"
            "3. /status - Check active tasks"
        )
        await update.message.reply_text(welcome_text, parse_mode="Markdown")

    async def login_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /login <email>")
            return

        email = context.args[0]
        await update.message.reply_text(f"\U0001f511 Authenticating `{email}`...", parse_mode="Markdown")

    async def snipe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /snipe <event_id>")
            return

        event_id = context.args[0]
        await update.message.reply_text(
            f"\U0001f3af Sniper target set: `{event_id}`. Initializing...", parse_mode="Markdown"
        )

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "\U0001f4ca *System Status:*\n"
            "- Sniper: Idle\n"
            "- Monitor: Active\n"
            "- Proxy: Connected",
            parse_mode="Markdown",
        )

    def run(self):
        logger.info("Telegram Bot started.")
        self.app.run_polling()