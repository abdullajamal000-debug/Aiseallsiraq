import os
import io
import base64
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# إعدادات
# =========================

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)


# =========================
# /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "هلا بيك 👋\n\n"
        "أنا مساعدك التسويقي 🤖🔥\n\n"
        "دزلي صورة العطر أو المكياج، "
        "وبعدها اكتبلي السعر.\n\n"
        "وأجهزلك إعلان احترافي + كابشن جاهز للنشر."
    )


# =========================
# استقبال الصور
# =========================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    photo = update.message.photo[-1]

    file = await context.bot.get_file(photo.file_id)

    image_bytes = await file.download_as_bytearray()

    context.user_data["product_image"] = bytes(image_bytes)

    await update.message.reply_text(
        "📸 وصلت الصورة ✅\n\n"
        "هسه دزلي سعر المنتج فقط، مثال:\n\n"
        "25000"
    )


# =========================
# استقبال السعر
# =========================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if "product_image" not in context.user_data:
        await update.message.reply_text(
            "دزلي أولاً 📸 صورة المنتج."
        )
        return

    price = update.message.text.strip()

    image_bytes = context.user_data["product_image"]

    await update.message.reply_text(
        "⏳ لحظة ضلعي، دا أجهز الإعلان..."
    )

    # تحويل الصورة إلى Base64
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt = f"""
أنت خبير تسويق للمنتجات في العراق.

حلل صورة المنتج المرفقة.

المنتج غالباً عطر أو مكياج.

اكتب لي إعلان تسويقي باللهجة العراقية.

السعر:
{price} دينار عراقي

أريد منك:

1. اسم مناسب للمنتج إذا كان واضحاً من الصورة.
2. وصف قصير جذاب.
3. كابشن عراقي بيعي.
4. دعوة واضحة للشراء.
5. اذكر أن التوصيل متوفر إذا لم توجد معلومات أخرى.

ممنوع اختراع معلومات غير واضحة عن المنتج.
لا تدعي أن المنتج أصلي أو طبي أو له فوائد صحية إلا إذا كانت المعلومة واضحة ومؤكدة.

اجعل النص مناسباً للنشر على Instagram وFacebook.
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt,
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_base64}",
                    },
                ],
            }
        ],
    )

    caption = response.output_text

    # إرسال الكابشن للمستخدم
    await update.message.reply_text(
        "✅ جهزتلك الكابشن:\n\n" + caption
    )

    # تنظيف الصورة من الذاكرة
    context.user_data.pop("product_image", None)


# =========================
# تشغيل البوت
# =========================

def main():

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            handle_photo
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text
        )
    )

    print("AI Seller Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
