import os
import io
import base64
import requests
from PIL import Image
from rembg import remove, new_session

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

# تحميل نموذج الذكاء الاصطناعي الخفيف جداً (u2netp) لتفادي استهلاك الـ RAM والكراش
rembg_session = new_session("u2netp")


def process_image(image_bytes: bytes) -> bytes:
    """تفريغ خلفية صورة المنتج بآمان بدون تجهيد السيرفر"""
    input_img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    
    # تفريغ الخلفية باستخدام الجلسة الخفيفة
    no_bg_img = remove(input_img, session=rembg_session)
    
    # لون خلفية استوديو ناعم وفخم (أوف وايت)
    bg_color = (245, 245, 247, 255) 
    background = Image.new("RGBA", no_bg_img.size, bg_color)
    
    # دمج الصورة المفرغة مع الخلفية الجديدة
    final_img = Image.alpha_composite(background, no_bg_img)
    
    # تحويل الصورة إلى JPEG للإرسال
    output_buffer = io.BytesIO()
    final_img.convert("RGB").save(output_buffer, format="JPEG", quality=95)
    return output_buffer.getvalue()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "هلا بيك 👋🔥\n\n"
        "أنا مساعدك التسويقي AI.\n\n"
        "📸 دزلي صورة العطر أو المكياج\n"
        "💰 وبعدها دز السعر\n\n"
        "وأنا أترافق باقتطاع الصورة، تعديلها، وتجهيز إعلان عراقي جاهز للنشر."
    )


async def handle_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    try:
        photo = update.message.photo[-1]
        telegram_file = await context.bot.get_file(photo.file_id)
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
    raw_image_bytes = context.user_data["product_image"]

    await update.message.reply_text(
        "⏳ لحظة ضلعي، دا أعدل الصورة بالذكاء الاصطناعي وأحلل المنتج..."
    )

    try:
        # --- 1. تعديل الصورة وتفريغ خلفيتها ---
        processed_image_bytes = process_image(raw_image_bytes)
        
        # إرسال الصورة المعدلة فوراً للزبون
        await update.message.reply_photo(
            photo=io.BytesIO(processed_image_bytes),
            caption="✨ هذه صورتك بعد المعالجة وتفريغ الخلفية تلقائياً!"
        )

        # --- 2. تجهيز كود التحليل وتوليد الكابشن ---
        image_base64 = base64.b64encode(raw_image_bytes).decode("utf-8")

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

        for model in MODELS:
            try:
                response = requests.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://t.me/Aiseallsiraq",
                        "X-Title": "AI Seller Iraq",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{image_base64}"
                                        },
                                    },
                                ],
                            }
                        ],
                        "temperature": 0.8,
                        "max_tokens": 1200,
                    },
                    timeout=90,
                )

                try:
                    data = response.json()
                except Exception:
                    last_error = f"{model}: {response.text[:2000]}"
                    continue

                if response.status_code != 200 or "choices" not in data or not data["choices"]:
                    last_error = f"{model}: {str(data)[:2000]}"
                    continue

                message = data["choices"][0].get("message", {})
                caption = message.get("content")

                if not caption:
                    last_error = f"{model}: Empty content"
                    continue

                # نجاح 🎉
                await update.message.reply_text(
                    "✅ الإعلان الكتابي جاهز 🔥\n\n" + caption
                )
                return

            except Exception as e:
                last_error = f"{model}: {str(e)[:2000]}"
                continue

        await update.message.reply_text(
            "❌ الصورة تعدلت بنجاح، لكن نماذج كتابة النصوص مجانية ومشغولة حالياً.\n\n"
            f"تفاصيل الخطأ:\n{str(last_error)[:1000]}"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ صار خطأ أثناء معالجة الطلب:\n\n{str(e)[:2000]}"
        )

    finally:
        context.user_data.pop("product_image", None)


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("AI Seller Iraq is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
