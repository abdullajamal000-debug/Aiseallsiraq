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

# نماذج مجانية تدعم الصور
MODELS = [
    "minimax/minimax-m3:free",
    "openrouter/free",
]


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
            "هسه دزلي سعر المنتج، مثال:\n\n"
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

        image_base64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")


        prompt = f"""
أنت خبير تسويق ومبيعات للعطور والمكياج ومستحضرات التجميل في العراق.

حلل صورة المنتج المرفقة.

السعر:
{price} دينار عراقي.

أريد إعلاناً احترافياً باللهجة العراقية، مناسباً للنشر على Instagram وFacebook.

اكتب النتيجة بهذا الشكل:

🔥 اسم المنتج:
اسم المنتج أو البراند إذا كان واضحاً بالصورة.

✨ وصف المنتج:
وصف قصير وجذاب اعتماداً فقط على الصورة.

🛍️ الكابشن:
كابشن عراقي بيعي قوي وجذاب.
استخدم الإيموجي باعتدال.
خلي الكلام يشجع الزبون على الشراء.

💰 السعر:
{price} د.ع

📩 الطلب:
جملة تشجع الزبون على مراسلة الصفحة للطلب.

#️⃣ الهاشتاغات:
5 إلى 8 هاشتاغات مناسبة.

قواعد مهمة:
- لا تخترع معلومات غير موجودة بالصورة.
- لا تدعي أن المنتج أصلي إلا إذا كان واضحاً ومؤكداً.
- لا تذكر فوائد طبية.
- لا تدعي أن المنتج يعالج أي مرض.
- لا تخمن اسم المنتج إذا كان غير واضح.
- استخدم اللهجة العراقية.
- خلي الإعلان قصير وقوي واحترافي.
- ركز على البيع.
"""


        last_error = None


        # تجربة النماذج واحداً بعد الآخر
        for model in MODELS:

            try:

                response = requests.post(

                    OPENROUTER_URL,

                    headers={
                        "Authorization":
                            f"Bearer {OPENROUTER_API_KEY}",

                        "Content-Type":
                            "application/json",

                        "HTTP-Referer":
                            "https://t.me/Aiseallsiraq",

                        "X-Title":
                            "AI Seller Iraq",
                    },

                    json={

                        "model": model,

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
                                            "data:image/jpeg;base64,"
                                            + image_base64
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


                try:
                    data = response.json()

                except Exception:

                    last_error = (
                        f"{model}: "
                        + response.text[:2000]
                    )

                    continue


                # إذا النموذج مزدحم أو محدود
                if response.status_code == 429:

                    last_error = (
                        f"{model}: "
                        + str(data)[:2000]
                    )

                    continue


                # أي خطأ ثاني
                if response.status_code != 200:

                    last_error = (
                        f"{model}: "
                        + str(data)[:2000]
                    )

                    continue


                # التأكد من وجود choices
                if "choices" not in data:

                    last_error = (
                        f"{model}: "
                        + str(data)[:2000]
                    )

                    continue


                if not data["choices"]:

                    last_error = (
                        f"{model}: Empty choices"
                    )

                    continue


                message = data["choices"][0].get(
                    "message",
                    {}
                )


                caption = message.get("content")


                if not caption:

                    last_error = (
                        f"{model}: Empty content\n"
                        + str(data)[:2000]
                    )

                    continue


                # نجاح 🎉
                await update.message.reply_text(
                    "✅ الإعلان جاهز 🔥\n\n"
                    + caption
                )

                return


            except requests.exceptions.Timeout:

                last_error = (
                    f"{model}: Timeout"
                )

                continue


            except Exception as e:

                last_error = (
                    f"{model}: "
                    + str(e)[:2000]
                )

                continue


        # إذا كل النماذج فشلت
        await update.message.reply_text(
            "❌ حالياً كل نماذج الـAI المجانية مشغولة.\n\n"
            "جرب بعد دقيقة أو دقيقتين.\n\n"
            "تفاصيل الخطأ:\n"
            + str(last_error)[:2500]
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


    print(
        "AI Seller Iraq is running..."
    )


    app.run_polling()


if __name__ == "__main__":

    main()
