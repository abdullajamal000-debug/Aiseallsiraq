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

# =========================
# Environment Variables
# =========================

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# نموذج مجاني يدعم تحليل الصور
MODEL = "google/gemma-3-27b-it:free"


# =========================
# Start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "هلا بيك 👋🔥\n\n"
        "أنا مساعدك التسويقي AI.\n\n"
        "📸 دزلي صورة العطر أو المكياج\n"
        "💰 وبعدها دز السعر\n\n"
        "وأجهزلك كابشن عراقي بيعي جاهز للنشر."
    )


# =========================
# Photo
# =========================

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
            "هسه دزلي سعر المنتج، مثال:\n\n"
            "25000"
        )

    except Exception as e:

        await update.message.reply_text(
            "❌ صار خطأ أثناء استلام الصورة:\n\n"
            + str(e)
        )


# =========================
# Text / Price
# =========================

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

        # =========================
        # Convert image to Base64
        # =========================

        image_base64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")


        # =========================
        # Prompt
        # =========================

        prompt = f"""
أنت خبير تسويق ومبيعات للعطور ومستحضرات التجميل في العراق.

حلل صورة المنتج المرفقة.

السعر الذي أعطاه صاحب المتجر:
{price} دينار عراقي.

اكتب إعلاناً تسويقياً باللهجة العراقية، مناسباً للنشر على Instagram وFacebook.

أريد النتيجة بهذا الترتيب:

اسم المنتج:
إذا كان الاسم واضحاً من الصورة اكتبه، وإذا لم يكن واضحاً اكتب "غير واضح".

وصف قصير:
وصف جذاب للمنتج اعتماداً فقط على المعلومات الظاهرة في الصورة.

الكابشن:
اكتب كابشن عراقي جذاب وبيعي، مع رموز تعبيرية بشكل مناسب.

السعر:
{price} د.ع

دعوة للشراء:
جملة تشجع الزبون على الطلب.

هاشتاغات:
اكتب 5 إلى 8 هاشتاغات مناسبة.

مهم جداً:
- لا تخترع معلومات غير موجودة بالصورة.
- لا تقل إن المنتج أصلي إلا إذا كان ذلك واضحاً ومؤكداً.
- لا تذكر فوائد طبية.
- لا تدعي أن المنتج يعالج أي مرض.
- لا تغير اسم البراند إذا كان واضحاً.
- استخدم اللهجة العراقية.
- خلي الإعلان قصير وجذاب ويدفع للشراء.
"""


        # =========================
        # OpenRouter Request
        # =========================

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
                                    "url":
                                    f"data:image/jpeg;base64,{image_base64}"
                                }
                            }

                        ]
                    }

                ],

                "temperature": 0.7,

                "max_tokens": 1000
            },

            timeout=90
        )


        # =========================
        # Read Response
        # =========================

        try:

            data = response.json()

        except Exception:

            await update.message.reply_text(
                "❌ OpenRouter رجع رد غير مفهوم:\n\n"
                + response.text[:3000]
            )

            return


        # =========================
        # API Error
        # =========================

        if response.status_code != 200:

            error_message = data.get(
                "error",
                data
            )

            await update.message.reply_text(
                "❌ صار خطأ من OpenRouter:\n\n"
                + str(error_message)[:3000]
            )

            return


        # =========================
        # Check Choices
        # =========================

        if "choices" not in data:

            await update.message.reply_text(
                "❌ OpenRouter رجع رد بدون نتيجة:\n\n"
                + str(data)[:3000]
            )

            return


        choices = data["choices"]

        if not choices:

            await update.message.reply_text(
                "❌ النموذج ما رجع أي نتيجة."
            )

            return


        message = choices[0].get(
            "message",
            {}
        )

        caption = message.get(
            "content"
        )


        if not caption:

            await update.message.reply_text(
                "❌ النموذج رجع نتيجة فارغة:\n\n"
                + str(data)[:3000]
            )

            return


        # =========================
        # Send Result
        # =========================

        await update.message.reply_text(
            "✅ الإعلان جاهز 🔥\n\n"
            + caption
        )


    except requests.exceptions.Timeout:

        await update.message.reply_text(
            "⏱️ الطلب أخذ وقت أطول من المتوقع.\n"
            "جرب مرة ثانية بعد قليل."
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


# =========================
# Main
# =========================

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


    print(
        "AI Seller Iraq is running..."
    )


    app.run_polling()


# =========================
# Run
# =========================

if __name__ == "__main__":

    main()
