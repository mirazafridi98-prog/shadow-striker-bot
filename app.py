
import asyncio
import logging
import os
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL = os.getenv("CHANNEL", "@team_shadow_striker").strip()
CHANNEL_URL = os.getenv(
    "CHANNEL_URL", "https://t.me/team_shadow_striker"
).strip()
TZ = ZoneInfo("Asia/Dhaka")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("shadow-striker")

web = Flask(__name__)


@web.get("/")
def home():
    return "SHADOW STRIKER BOT IS RUNNING", 200


@web.get("/health")
def health():
    return "OK", 200


def run_web():
    port = int(os.getenv("PORT", "10000"))
    web.run(host="0.0.0.0", port=port, use_reloader=False)


REPORTS = {
    "facebook": [
        ("Underage", [
            "Please review this account for a possible age-policy concern. Verify the available evidence before taking action.",
            "I request a review of this profile for a possible age-related policy issue.",
        ]),
        ("Impersonation", [
            "This profile may be impersonating another person or organization. Please review the identity claims and supporting evidence.",
            "I am reporting a possible impersonation concern and request an appropriate review.",
        ]),
        ("Harassment", [
            "Please review the reported content for possible targeted harassment under the platform's policies.",
            "The reported activity may violate policies concerning harassment. Please assess the evidence and context.",
        ]),
        ("Privacy Violation", [
            "This content may disclose someone's personal information without consent. Please review the material.",
            "Please assess this report for a possible unauthorized disclosure of private information.",
        ]),
        ("Scam / Fraud", [
            "I am reporting activity that may be deceptive or fraudulent. Please review the available evidence.",
            "Please assess the reported content for possible scam-related policy violations.",
        ]),
        ("Copyright", [
            "I am reporting a possible unauthorized use of copyrighted material. Please review the original work and reported content.",
            "Please assess this material for a possible copyright violation.",
        ]),
    ],
    "tiktok": [
        ("Underage", [
            "Please review this account for a possible violation of age-related platform requirements.",
            "I request a review of this profile for a possible age-policy concern.",
        ]),
        ("Impersonation", [
            "This profile may be impersonating another person or organization. Please investigate the identity claims.",
            "I am reporting a possible impersonation concern.",
        ]),
        ("Harassment", [
            "Please review the reported videos and interactions for possible targeted harassment or bullying.",
            "The reported behavior may violate policies concerning harassment. Please investigate the context.",
        ]),
        ("Privacy Violation", [
            "This content may disclose personal information without consent. Please review the material.",
            "Please investigate the reported material for a possible privacy violation.",
        ]),
        ("Scam / Fraud", [
            "I am reporting potentially deceptive or fraudulent activity. Please review the account.",
            "Please assess this profile for possible scam-related policy violations.",
        ]),
    ],
    "instagram": [
        ("Underage", [
            "Please review this account for a possible violation of age-related platform requirements.",
            "I request an appropriate review based on the available age-related information.",
        ]),
        ("Impersonation", [
            "This profile may be pretending to represent another person or organization without authorization.",
            "I am reporting a possible impersonation concern.",
        ]),
        ("Harassment", [
            "Please review the reported posts and interactions for possible targeted harassment or bullying.",
            "The reported activity may violate policies against harassment.",
        ]),
        ("Privacy Violation", [
            "This content may expose private information without consent. Please review the reported material.",
            "I request an investigation into the possible unauthorized disclosure of personal information.",
        ]),
        ("Scam / Fraud", [
            "This account may be involved in deceptive or fraudulent activity. Please review the evidence.",
            "Please investigate the reported content for possible scams or misleading claims.",
        ]),
    ],
    "youtube": [
        ("Harassment", [
            "Please review this video or channel for possible targeted harassment or cyberbullying.",
            "I am reporting the linked content because it may violate harassment policies.",
        ]),
        ("Privacy Violation", [
            "The reported video may disclose someone's private information without consent.",
            "Please assess the reported content for a possible privacy violation.",
        ]),
        ("Impersonation", [
            "This channel may be impersonating another creator or organization. Please investigate.",
            "I request a review of this channel for a possible impersonation violation.",
        ]),
        ("Child Safety", [
            "I am reporting content that raises a child-safety concern. Please review the material.",
            "Please investigate the reported content for any confirmed child-safety policy violation.",
        ]),
        ("Copyright", [
            "I am reporting a possible unauthorized use of copyrighted material.",
            "Please assess this material for a possible copyright violation.",
        ]),
    ],
}

CONTACTS = {
    "facebook": "https://www.facebook.com/help/",
    "tiktok": "https://www.tiktok.com/legal/report/feedback",
    "instagram": "https://help.instagram.com/",
    "youtube": "https://support.google.com/youtube/",
}

NAMES = {
    "facebook": "🔵 Facebook",
    "tiktok": "🎵 TikTok",
    "instagram": "📸 Instagram",
    "youtube": "▶️ YouTube",
}


def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔵 Facebook", callback_data="plat:facebook"),
            InlineKeyboardButton("🎵 TikTok", callback_data="plat:tiktok"),
        ],
        [
            InlineKeyboardButton("📸 Instagram", callback_data="plat:instagram"),
            InlineKeyboardButton("▶️ YouTube", callback_data="plat:youtube"),
        ],
        [InlineKeyboardButton("🤖 AI Print", callback_data="ai")],
    ])


def platform_keyboard(platform):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "📚 All Report Additional", callback_data=f"reports:{platform}"
        )],
        [InlineKeyboardButton(
            "📧 Official Contact / Help", callback_data=f"contact:{platform}"
        )],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="home")],
    ])


def join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ Joined - Check Again", callback_data="check")],
    ])


async def is_member(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ("member", "administrator", "creator") or bool(
            getattr(member, "is_member", False)
        )
    except Exception:
        logger.exception("Could not verify channel membership")
        return False


async def require_member(update, context):
    user = update.effective_user
    if user and await is_member(context.bot, user.id):
        return True

    message = (
        "🔒 প্রথমে আমাদের Telegram Channel-এ Join করুন।\n\n"
        "Join করার পর Check Again বাটনে চাপ দিন।"
    )
    if update.callback_query:
        await update.callback_query.message.reply_text(
            message, reply_markup=join_keyboard()
        )
    elif update.effective_message:
        await update.effective_message.reply_text(
            message, reply_markup=join_keyboard()
        )
    return False


def get_greeting():
    now = datetime.now(TZ)
    if 5 <= now.hour < 12:
        greeting = "🌅 শুভ সকাল!"
    elif 12 <= now.hour < 16:
        greeting = "☀️ শুভ দুপুর!"
    elif 16 <= now.hour < 18:
        greeting = "🌇 শুভ বিকাল!"
    else:
        greeting = "🌙 শুভ রাত্রি!"
    return greeting, now


async def show_profile(update, context):
    user = update.effective_user
    greeting, now = get_greeting()
    username = f"@{user.username}" if user.username else "Username নেই"

    caption = (
        "👑 SHADOW STRIKER REPORT BOT\n\n"
        f"{greeting}\n\n"
        f"👤 Name: {user.full_name}\n"
        f"🆔 Username: {username}\n"
        f"💬 Chat ID: {user.id}\n\n"
        f"🕒 Time: {now.strftime('%I:%M:%S %p')}\n"
        f"📅 Date: {now.strftime('%d %B %Y')}\n"
        "🇧🇩 Bangladesh Time\n\n"
        "নিচের Menu থেকে প্রয়োজনীয় বিভাগ নির্বাচন করুন।"
    )

    photos = await context.bot.get_user_profile_photos(user.id, limit=1)
    if photos.total_count:
        photo_id = photos.photos[0][-1].file_id
        await update.effective_message.reply_photo(
            photo=photo_id, caption=caption, reply_markup=main_keyboard()
        )
    else:
        await update.effective_message.reply_text(
            caption, reply_markup=main_keyboard()
        )


async def start(update, context):
    if not await require_member(update, context):
        return
    await show_profile(update, context)


async def help_command(update, context):
    if not await require_member(update, context):
        return
    await update.message.reply_text(
        "👑 SHADOW STRIKER BOT\n\n"
        "/start - Main Menu\n"
        "/help - Help\n\n"
        "নিচের Menu থেকে প্রয়োজনীয় বিভাগ নির্বাচন করুন।"
    )


async def check_join(update, context):
    query = update.callback_query
    await query.answer()
    if await is_member(context.bot, query.from_user.id):
        await query.message.reply_text("✅ Membership Verified!")
        await show_profile(update, context)
    else:
        await query.message.reply_text(
            "❌ এখনো Channel Member পাওয়া যায়নি।",
            reply_markup=join_keyboard(),
        )


async def callbacks(update, context):
    query = update.callback_query
    await query.answer()

    if not await require_member(update, context):
        return

    data = query.data or ""

    if data == "home":
        await show_profile(update, context)
        return

    if data.startswith("plat:"):
        platform = data.split(":", 1)[1]
        if platform not in NAMES:
            return
        await query.message.reply_text(
            f"{NAMES[platform]}\n\nআপনার প্রয়োজনীয় অপশন নির্বাচন করুন:",
            reply_markup=platform_keyboard(platform),
        )
        return

    if data.startswith("reports:"):
        platform = data.split(":", 1)[1]
        if platform not in REPORTS:
            return
        buttons = [
            [InlineKeyboardButton(
                "📄 " + item[0],
                callback_data=f"report:{platform}:{index}",
            )]
            for index, item in enumerate(REPORTS[platform])
        ]
        buttons.append([
            InlineKeyboardButton("⬅️ Back", callback_data=f"plat:{platform}")
        ])
        await query.message.reply_text(
            f"📚 {NAMES[platform]} - Report Categories",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    if data.startswith("report:"):
        try:
            _, platform, index_text = data.split(":")
            index = int(index_text)
            item = REPORTS[platform][index]
        except (ValueError, KeyError, IndexError):
            await query.message.reply_text("এই অপশনটি পাওয়া যায়নি। /start দিন।")
            return

        today = datetime.now(TZ).date()
        selected = item[1][today.toordinal() % len(item[1])]
        await query.message.reply_text(
            f"📄 {item[0]} Additional\n\n{selected}\n\n"
            f"📅 Updated: {today.strftime('%d %B %Y')}\n\n"
            "⚠️ শুধু সত্য ও যাচাইযোগ্য তথ্য দিয়ে রিপোর্ট করুন।",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "📋 Copy Text", callback_data=f"copy:{platform}:{index}"
                )],
                [InlineKeyboardButton(
                    "⬅️ Back", callback_data=f"reports:{platform}"
                )],
            ]),
        )
        return

    if data.startswith("copy:"):
        try:
            _, platform, index_text = data.split(":")
            index = int(index_text)
            item = REPORTS[platform][index]
        except (ValueError, KeyError, IndexError):
            await query.message.reply_text("এই টেক্সটটি পাওয়া যায়নি।")
            return

        today = datetime.now(TZ).date()
        selected = item[1][today.toordinal() % len(item[1])]
        await query.message.reply_text(
            "📋 নিচের Additional-টি Copy করুন:\n\n" + selected
        )
        return

    if data.startswith("contact:"):
        platform = data.split(":", 1)[1]
        if platform not in CONTACTS:
            return
        await query.message.reply_text(
            f"📧 {NAMES[platform]} Official Contact / Help",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "🌐 Official Help", url=CONTACTS[platform]
                )],
                [InlineKeyboardButton(
                    "⬅️ Back", callback_data=f"plat:{platform}"
                )],
            ]),
        )
        return

    if data == "ai":
        await query.message.reply_text(
            "🤖 AI PRINT\n\nআপনার প্রয়োজনীয় Prompt নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "🖼️ AI Image Prompt", callback_data="prompt:image"
                )],
                [InlineKeyboardButton(
                    "📄 AI Document Prompt", callback_data="prompt:document"
                )],
                [InlineKeyboardButton(
                    "⬅️ Main Menu", callback_data="home"
                )],
            ]),
        )
        return

    if data == "prompt:image":
        await query.message.reply_text(
            "🖼️ AI IMAGE PROMPT\n\n"
            "Create a fictional sample image for a design demonstration. "
            "Use invented details and a visible DEMO watermark. "
            "Do not imitate real identity documents."
        )
        return

    if data == "prompt:document":
        await query.message.reply_text(
            "📄 AI DOCUMENT PROMPT\n\n"
            "Create a fictional sample document using invented details. "
            "Add a visible DEMO / NOT VALID watermark."
        )
        return


def main():
    threading.Thread(target=run_web, daemon=True).start()

    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(check_join, pattern=r"^check$"))
    application.add_handler(CallbackQueryHandler(callbacks))

    logger.info("SHADOW STRIKER BOT STARTING...")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
