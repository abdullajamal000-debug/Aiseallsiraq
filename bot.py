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

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# نموذج مجاني يدعم الصور
MODEL = "google/gemma-4-31b-it:free"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "هلا بيك 👋🔥\n\n"
        "أنا مساعدك التسويقي AI.\n\n"
        "📸 دزلي صورة العطر أو المكياج\n"
        "💰 وبعدها دز السعر\n\n"
        "وأجهزلك إعلان عراقي بيعي جاهز للنشر."
    )


async def handle_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    try:
        photo = update.message.photo[-1]

        telegram_file = await context.bot.get_file(
            photo.file_id
        )

        image_bytes = await telegram_file.download_as_bytearray()

        context.user_data["product_image"] = bytes(image_bytes)

        await update.message.reply_text(
            "📸 وصلت الصورة ✅\n\n"
            "هسه دزلي سعر المنتج، مثال:\n"
            "25000"
        )

    except Exception as e:
        await update.message.reply_text(
            "❌ صار خطأ أثناء استلام الصورة:\n\n"
            + str(e)[:2000]
        )


async def handle_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if "product_image" not in context.user_data:
        await update.message.reply_text(
            "📸 دزلي صورة المنتج أولاً."
        )
        return

    price = update.message.text.strip()
    image_bytes = context.user_data["product_image"]

    await update.message.reply_text(
        "⏳ لحظة ضلعي، دا أحلل المنتج وأجهزلك الإعلان..."
    )

    try:
        # تحويل الصورة إلى Base64
        image_base64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        prompt = f"""
أنت خبير تسويق ومبيعات للعطور والمكياج ومستحضرات التجميل في العراق.

حلل صورة المنتج المرفقة.

السعر الذي أعطاك إياه صاحب المتجر:
{price} دينار عراقي.

أريد منك كتابة إعلان احترافي باللهجة العراقية، مناسب للنشر على Instagram وFacebook.

رتب النتيجة بهذا الشكل:

🔥 اسم المنتج:
اكتب اسم المنتج أو البراند إذا كان واضحاً بالصورة.

✨ وصف المنتج:
وصف قصير وجذاب للمنتج اعتماداً على الصورة فقط.

🛍️ الكابشن:
اكتب كابشن عراقي بيعي قوي.
خليه جذاب ويشجع الزبون على الشراء.
استخدم الإيموجي باعتدال.

💰 السعر:
{price} د.ع

📩 الطلب:
اكتب جملة تشجع الزبون على مراسلة الصفحة للطلب.

#️⃣ الهاشتاغات:
اكتب 5 إلى 8 هاشتاغات مناسبة.

قواعد مهمة جداً:
- لا تخترع معلومات غير واضحة بالصورة.
- لا تدعي أن المنتج أصلي إذا لم يكن ذلك مؤكداً.
- لا تذكر فوائد طبية.
- لا تقل إن المنتج يعالج أي مرض.
- إذا كان اسم المنتج غير واضح، لا تخمن.
- استخدم اللهجة العراقية.
- خلي الإعلان قصير، قوي، واحترافي.
- الهدف الأساسي هو البيع.
"""

        response = requests.post(
            OPENROUTER_URL,

            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://t.me/Aiseallsiraq",
                "X-Title": "AI Seller Iraq",
            },

            json={
                "model": MODEL,

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
                                    "url": (
                                        "data:image/jpeg;base64,"
                                        + image_base64
                                    )
                                }
                            }
                        ]
                    }
                ],

                "temperature": 0.8,
                "max_tokens": 1200
            },

            timeout=90
        )

        # محاولة قراءة الرد
        try:
            data = response.json()
        except Exception:
            await update.message.reply_text(
                "❌ OpenRouter رجع رد غير مفهوم:\n\n"
                + response.text[:3000]
            )
            return

        # إذا API رجع خطأ
        if response.status_code != 200:
            error_message = data.get("error", data)

            await update.message.reply_text(
                "❌ صار خطأ من OpenRouter:\n\n"
                + str(error_message)[:3000]
            )
            return

        # التأكد من وجود النتيجة
        if "choices" not in data:
            await update.message.reply_text(
                "❌ OpenRouter رجع رد بدون نتيجة:\n\n"
                + str(data)[:3000]
            )
            return

        if not data["choices"]:
            await update.message.reply_text(
                "❌ النموذج ما رجع أي نتيجة."
            )
            return

        message = data["choices"][0].get(
            "message",
            {}
        )

        caption = message.get("content")

        if not caption:
            await update.message.reply_text(
                "❌ النموذج رجع نتيجة فارغة:\n\n"
                + str(data)[:3000]
            )
            return

        # إرسال الإعلان
        await update.message.reply_text(
            "✅ الإعلان جاهز 🔥\n\n"
            + caption
        )

    except requests.exceptions.Timeout:
        await update.message.reply_text(
            "⏱️ الذكاء الاصطناعي أخذ وقت أطول من المتوقع.\n"
            "جرب مرة ثانية."
        )

    except requests.exceptions.RequestException as e:
        await update.message.reply_text(
            "❌ مشكلة بالاتصال مع OpenRouter:\n\n"
            + str(e)[:2000]
        )

    except Exception as e:
        await update.message.reply_text(
            "❌ صار خطأ:\n\n"
            + str(e)[:2000]
        )

    finally:
        context.user_data.pop(
            "product_image",
            None
        )


def main():

    app = Application.builder().token(
        TELEGRAM_TOKEN
    ).build()

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

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
