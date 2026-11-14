import os
import logging
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

# ================= CONFIG =================

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = "@team_shadow_striker"
CHANNEL_URL = "https://t.me/team_shadow_striker"
TZ = ZoneInfo("Asia/Dhaka")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ================= WEB SERVER =================

web = Flask(__name__)

@web.route("/")
def home():
    return "SHADOW STRIKER BOT IS RUNNING", 200

@web.route("/health")
def health():
    return "OK", 200

def run_web():
    web.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        use_reloader=False
    )

# ================= REPORT DATABASE =================

REPORTS = {
    "facebook": [
        ("Underage", [
            "I am reporting this account because there are concerns that it may involve an underage user. Please review the available evidence and verify compliance with Facebook's age requirements.",
            "Please review this profile for a possible age-policy violation. The report is based on the information and evidence provided, and I request an appropriate assessment."
        ]),
        ("Impersonation", [
            "I am reporting this profile for suspected impersonation. It may be presenting itself as another person or entity without authorization. Please review the profile and supporting evidence.",
            "This account appears to create confusion about the identity of another person or organization. Please investigate the reported content and take appropriate action if a violation is confirmed."
        ]),
        ("Harassment", [
            "I am reporting content that appears to target and harass another individual. Please review the attached evidence under your harassment and bullying policies.",
            "Please investigate this reported behavior for possible harassment. The relevant posts, messages, and dates are provided as evidence."
        ]),
        ("Privacy Violation", [
            "I am concerned that this account may be sharing personal information without consent. Please review the content for possible privacy violations.",
            "This report concerns the possible unauthorized disclosure of private information. Please assess the evidence and take appropriate action if the violation is confirmed."
        ]),
        ("Scam / Fraud", [
            "I am reporting suspected fraudulent activity. Please review the account and the relevant communications for possible scams or deceptive practices.",
            "The reported content appears potentially misleading and financially deceptive. Please investigate the evidence under your fraud policies."
        ]),
        ("Copyright", [
            "I am reporting content that may use copyrighted material without permission. Please review the original work and the reported material.",
            "Please assess this content for a possible copyright violation. Supporting ownership and original publication information can be provided."
        ])
    ],

    "tiktok": [
        ("Underage", [
            "Please review this account for a possible violation of TikTok's minimum age requirements. I am submitting this report based on the available evidence.",
            "I request a review of this profile for possible age-related policy violations."
        ]),
        ("Impersonation", [
            "This profile may be impersonating another individual or organization. Please review the identity claims and available evidence.",
            "I am reporting suspected impersonation and request an appropriate investigation."
        ]),
        ("Harassment", [
            "Please review the reported videos and interactions for possible targeted harassment or bullying.",
            "The reported behavior may violate TikTok's community guidelines regarding harassment. Please investigate."
        ]),
        ("Privacy Violation", [
            "This content may disclose personal information without the individual's consent. Please review it under your privacy policies.",
            "Please investigate the reported material for possible unauthorized sharing of private information."
        ]),
        ("Scam / Fraud", [
            "I am reporting potentially deceptive or fraudulent activity. Please review the account and associated content.",
            "Please assess this profile for possible scam-related violations based on the evidence submitted."
        ])
    ],

    "instagram": [
        ("Underage", [
            "Please review this Instagram account for a possible violation of age-related platform requirements.",
            "I request an appropriate review of the reported profile based on the available age-related evidence."
        ]),
        ("Impersonation", [
            "This profile may be pretending to represent another person or organization without authorization. Please investigate.",
            "I am reporting suspected impersonation and request a review of the account's identity claims."
        ]),
        ("Harassment", [
            "Please review the reported posts and interactions for potential harassment or bullying.",
            "The reported activity may violate Instagram's policies against targeted harassment. Please investigate."
        ]),
        ("Privacy Violation", [
            "This content may expose private information without consent. Please review the reported material.",
            "I request an investigation into possible unauthorized disclosure of personal information."
        ]),
        ("Scam / Fraud", [
            "This account may be involved in deceptive or fraudulent activity. Please review the available evidence.",
            "Please investigate the reported content for potential scams or misleading claims."
        ])
    ],

    "youtube": [
        ("Harassment", [
            "Please review this video or channel for possible targeted harassment or cyberbullying under YouTube's policies.",
            "I am reporting the linked content because it may violate YouTube's harassment policies. Please assess the evidence."
        ]),
        ("Privacy Violation", [
            "The reported video may disclose someone's private information without consent. Please review it under YouTube's privacy policies.",
            "Please assess the reported content for possible privacy violations."
        ]),
        ("Impersonation", [
            "This channel may be impersonating another creator or organization. Please investigate the reported identity claims.",
            "I request a review of this channel for suspected impersonation."
        ]),
        ("Child Safety", [
            "I am reporting content that raises a child-safety concern. Please review it under YouTube's child safety policies.",
            "Please investigate the reported content for any confirmed child-safety policy violations."
        ]),
        ("Copyright", [
            "I am reporting a possible unauthorized use of copyrighted material. Please review the original work and the reported content.",
            "Please assess this material for a potential copyright violation."
        ])
    ]
}

CONTACTS = {
    "facebook": "https://www.facebook.com/help/",
    "tiktok": "https://www.tiktok.com/legal/report/feedback",
    "instagram": "https://help.instagram.com/",
    "youtube": "https://support.google.com/youtube/"
}

NAMES = {
    "facebook": "🔵 Facebook",
    "tiktok": "🎵 TikTok",
    "instagram": "📸 Instagram",
    "youtube": "▶️ YouTube"
}

# ================= KEYBOARDS =================

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔵 Facebook", callback_data="plat:facebook"),
            InlineKeyboardButton("🎵 TikTok", callback_data="plat:tiktok")
        ],
        [
            InlineKeyboardButton("📸 Instagram", callback_data="plat:instagram"),
            InlineKeyboardButton("▶️ YouTube", callback_data="plat:youtube")
        ],
        [
            InlineKeyboardButton("🤖 AI Print", callback_data="ai")
        ]
    ])

def platform_keyboard(platform):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "📚 All Report Additional",
            callback_data=f"reports:{platform}"
        )],
        [InlineKeyboardButton(
            "📧 Mail Address / Official Contact",
            callback_data=f"contact:{platform}"
        )],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="home")]
    ])

# ================= MEMBERSHIP =================

async def is_member(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return (
            member.status in ("member", "administrator", "creator")
            or getattr(member, "is_member", False)
        )
    except Exception:
        log.exception("Membership verification failed")
        return False

def join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ Joined - Check Again", callback_data="check")]
    ])

async def require_member(update, context):
    user = update.effective_user

    if await is_member(context.bot, user.id):
        return True

    message = (
        "🔒 প্রথমে আমাদের Telegram Channel-এ Join করুন।\n\n"
        "Join করার পর নিচের Check Again বাটনে চাপ দিন।"
    )

    if update.callback_query:
        await update.callback_query.message.reply_text(
            message, reply_markup=join_keyboard()
        )
    else:
        await update.effective_message.reply_text(
            message, reply_markup=join_keyboard()
        )

    return False

# ================= PROFILE =================

def get_greeting():
    now = datetime.now(TZ)
    hour = now.hour

    if 5 <= hour < 12:
        greeting = "🌅 শুভ সকাল!"
    elif 12 <= hour < 16:
        greeting = "☀️ শুভ দুপুর!"
    elif 16 <= hour < 18:
        greeting = "🌇 শুভ বিকাল!"
    else:
        greeting = "🌙 শুভ রাত্রি!"

    return greeting, now

async def show_profile(update, context):
    user = update.effective_user
    greeting, now = get_greeting()

    username = (
        "@" + user.username if user.username else "Username নেই"
    )

    caption = (
        f"👑 SHADOW STRIKER REPORT BOT\n\n"
        f"{greeting}\n\n"
        f"👤 Name: {user.full_name}\n"
        f"🆔 Username: {username}\n"
        f"💬 Chat ID: {user.id}\n\n"
        f"🕒 Time: {now.strftime('%I:%M:%S %p')}\n"
        f"📅 Date: {now.strftime('%d %B %Y')}\n"
        f"🇧🇩 Bangladesh Time\n\n"
        f"নিচের Menu থেকে আপনার প্রয়োজনীয় বিভাগ নির্বাচন করুন।"
    )

    photos = await context.bot.get_user_profile_photos(
        user.id, limit=1
    )

    if photos.total_count:
        photo_id = photos.photos[0][-1].file_id
        await update.effective_message.reply_photo(
            photo=photo_id,
            caption=caption,
            reply_markup=main_keyboard()
        )
    else:
        await update.effective_message.reply_text(
            caption, reply_markup=main_keyboard()
        )

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_member(update, context):
        return

    await show_profile(update, context)

async def check_join(update, context):
    query = update.callback_query
    await query.answer()

    if await is_member(context.bot, query.from_user.id):
        await query.message.reply_text(
            "✅ Membership Verified!"
        )
        await show_profile(update, context)
    else:
        await query.message.reply_text(
            "❌ এখনো Channel Member পাওয়া যায়নি।",
            reply_markup=join_keyboard()
        )

# ================= CALLBACKS =================

async def callbacks(update, context):
    query = update.callback_query
    await query.answer()

    if not await require_member(update, context):
        return

    data = query.data

    if data == "home":
        await show_profile(update, context)
        return

    if data.startswith("plat:"):
        platform = data.split(":")[1]

        await query.message.reply_text(
            f"{NAMES[platform]}\n\n"
            "আপনার প্রয়োজনীয় অপশন নির্বাচন করুন:",
            reply_markup=platform_keyboard(platform)
        )
        return

    if data.startswith("reports:"):
        platform = data.split(":")[1]
        buttons = []

        for index, item in enumerate(REPORTS[platform]):
            buttons.append([
                InlineKeyboardButton(
                    "📄 " + item[0],
                    callback_data=f"report:{platform}:{index}"
                )
            ])

        buttons.append([
            InlineKeyboardButton("⬅️ Back",
                                 callback_data=f"plat:{platform}")
        ])

        await query.message.reply_text(
            f"📚 {NAMES[platform]} - Report Categories",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if data.startswith("report:"):
        _, platform, index = data.split(":")
        item = REPORTS[platform][int(index)]

        # Daily rotation based on Bangladesh date
        today = datetime.now(TZ).date()
        variants = item[1]
        selected = variants[today.toordinal() % len(variants)]

        await query.message.reply_text(
            f"📄 {item[0]} Additional\n\n"
            f"{selected}\n\n"
            f"📅 Updated: {today.strftime('%d %B %Y')}\n\n"
            "⚠️ শুধুমাত্র সত্য ও যাচাইযোগ্য তথ্য দিয়ে রিপোর্ট করুন।",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "📋 Copy Text",
                    callback_data=f"copy:{platform}:{index}"
                )],
                [InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data=f"reports:{platform}"
                )]
            ])
        )
        return

    if data.startswith("copy:"):
        _, platform, index = data.split(":")
        item = REPORTS[platform][int(index)]
        today = datetime.now(TZ).date()
        selected = item[1][today.toordinal() % len(item[1])]

        await query.message.reply_text(
            "📋 নিচের Additional-টি Copy করুন:\n\n" + selected
        )
        return

    if data.startswith("contact:"):
        platform = data.split(":")[1]

        await query.message.reply_text(
            f"📧 {NAMES[platform]} Official Contact / Help\n\n"
            "নিচের অফিসিয়াল লিংকে গিয়ে রিপোর্ট বা সাপোর্ট "
            "রিকোয়েস্ট জমা দিতে পারবেন।",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "🌐 Official Help",
                    url=CONTACTS[platform]
                )],
                [InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data=f"plat:{platform}"
                )]
            ])
        )
        return

    if data == "ai":
        await query.message.reply_text(
            "🤖 AI PRINT\n\n"
            "আপনার প্রয়োজনীয় Prompt নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "🖼️ AI Image Prompt",
                    callback_data="prompt:image"
                )],
                [InlineKeyboardButton(
                    "📄 AI Document Prompt",
                    callback_data="prompt:document"
                )],
                [InlineKeyboardButton(
                    "⬅️ Main Menu",
                    callback_data="home"
                )]
            ])
        )
        return

    if data == "prompt:image":
        await query.message.reply_text(
            "🖼️ AI IMAGE PROMPT\n\n"
            "Create a realistic close-up photograph of a hand "
            "holding a fictional sample card in a natural indoor "
            "environment. Place a clearly visible DEMO watermark "
            "on the card. Use a slightly aged transparent protective "
            "cover with subtle surface scratches, soft natural "
            "lighting, and a realistic Bangladesh-style room floor. "
            "Do not use real personal information or real identity "
            "document designs."
        )
        return

    if data == "prompt:document":
        await query.message.reply_text(
            "📄 AI DOCUMENT PROMPT\n\n"
            "Create a clean, fictional sample document for a "
            "design demonstration. Use invented names and "
            "non-functional sample numbers. Add a large, clearly "
            "visible DEMO / NOT VALID watermark. Do not imitate "
            "government-issued identity cards, official seals, "
            "or real personal documents."
        )
        return

# ================= HELP =================

async def help_command(update, context):
    if not await require_member(update, context):
        return

    await update.message.reply_text(
        "👑 SHADOW STRIKER BOT\n\n"
        "/start - Main Menu\n"
        "/help - Help\n\n"
        "Facebook, TikTok, Instagram, YouTube এবং AI Print "
        "বিভাগ থেকে প্রয়োজনীয় অপশন নির্বাচন করুন।"
    )

# ================= MAIN =================

def main():
    threading.Thread(
        target=run_web,
        daemon=True
    ).start()

    bot = Application.builder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("help", help_command))
    bot.add_handler(CallbackQueryHandler(
        check_join, pattern="^check$"
    ))
    bot.add_handler(CallbackQueryHandler(callbacks))

    log.info("SHADOW STRIKER BOT STARTING...")
    bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
