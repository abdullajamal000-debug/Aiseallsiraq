import os
import base64
import requests

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "هلا بيك 👋🔥\n\n"
        "أنا مساعدك التسويقي AI.\n\n"
        "📸 دزلي صورة العطر أو المكياج\n"
        "💰 وبعدها دز السعر\n\n"
        "وأجهزلك كابشن عراقي بيعي."
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    photo = update.message.photo[-1]

    file = await context.bot.get_file(photo.file_id)

    image_bytes = await file.download_as_bytearray()

    context.user_data["product_image"] = bytes(image_bytes)

    await update.message.reply_text(
        "📸 وصلت الصورة ✅\n\n"
        "هسه دزلي السعر، مثال:\n"
        "25000"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if "product_image" not in context.user_data:
        await update.message.reply_text(
            "📸 دزلي صورة المنتج أولاً."
        )
        return

    price = update.message.text.strip()

    image_bytes = context.user_data["product_image"]

    await update.message.reply_text(
        "⏳ لحظة ضلعي، دا أحلل المنتج..."
    )

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt = f"""
أنت خبير تسويق ومبيعات للعطور ومستحضرات التجميل في العراق.

حلل صورة المنتج المرفقة.

السعر: {price} دينار عراقي.

أريد منك كتابة إعلان باللهجة العراقية يتضمن:

- اسم المنتج إذا كان واضحاً.
- وصف جذاب وقصير.
- السعر.
- دعوة للشراء.
- هاشتاغات مناسبة.

ممنوع اختراع معلومات غير واضحة من الصورة.
لا تدعي أن المنتج أصلي أو طبي أو يعالج أي شيء إلا إذا كانت المعلومة مؤكدة.

اجعل النص مناسباً لـ Instagram وFacebook.
استخدم أسلوب تجاري جذاب يدفع الزبون للشراء.
"""

    try:

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",

            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://t.me/Aiseallsiraq",
                "X-Title": "AI Seller Iraq",
            },

            json={
                "model": "openrouter/free",

                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]
            },

            timeout=60
        )

        data = response.json()

        if response.status_code != 200:
            await update.message.reply_text(
                "❌ صار خطأ من خدمة الذكاء الاصطناعي:\n\n"
                + str(data)
            )
            return

        caption = data["choices"][0]["message"]["content"]

        await update.message.reply_text(
            "✅ الإعلان جاهز:\n\n" + caption
        )

    except Exception as e:

        await update.message.reply_text(
            "❌ صار خطأ:\n\n" + str(e)
        )

    finally:

        context.user_data.pop("product_image", None)


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

    print("AI Seller Iraq is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
