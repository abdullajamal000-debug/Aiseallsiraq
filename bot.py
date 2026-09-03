import os
import io
import base64
import requests
from PIL import Image, ImageEnhance, ImageOps, ImageFilter

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

# نماذج مجانية ممتازة تدعم قراءة الصور
MODELS = [
    "minimax/minimax-m3:free",
    "openrouter/free",
]


def enhance_product_image(image_bytes: bytes) -> bytes:
    """تحسين إضاءة وألوان وأبعاد الصورة الأصلية لتظهر بشكل استوديو فخم دون قص الخلفية"""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # 1. تحسين التباين والوضوح
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.18)

    # 2. تعديل الإضاءة والسطوع
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.05)

    # 3. إبراز حيوية الألوان (خاصة للمكياج والعطور الوردية والذهبية)
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.22)

    # 4. زيادة حدة التفاصيل لتبين أسطر الكتابة والبراند بوضوح
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.35)

    # 5. إضافة تأثير تدرج ضوئي ناعم على الأطراف (Vignette) لتركيز العين على المنتجات بالوسط
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    
    # تصدير الصورة المحسنة بدقة ممتازة
    output_buffer = io.BytesIO()
    img.save(output_buffer, format="JPEG", quality=96)
    return output_buffer.getvalue()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "هلا والله بيك 👋🔥\n\n"
        "أنا مساعدك التسويقي الذكي.\n\n"
        "📸 دزلي صورة المنتج (عطر، مكياج، كوزمتك)\n"
        "💰 وبعدها دزلي السعر\n\n"
        "وأنا أصفي لك إضاءة الصورة وأكتبلك إعلان عراقي بحت يجيبلك مبيعات مباشرة!"
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
            "📸 وصلت الصورة عيناي ✅\n\n"
            "هسه اكتبلي سعر بيع المنتج بالدينار، مثلاً:\n"
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
            "📸 دزلي صورة المنتج بالبداية حبيبي."
        )
        return

    price = update.message.text.strip()
    raw_image_bytes = context.user_data["product_image"]

    await update.message.reply_text(
        "⏳ ثواني عيناي.. دا أنسق الإضاءة والألوان وأحضرلك كابشن عراقي مرتب..."
    )

    try:
        # --- 1. تحسين الصورة أوتوماتيكياً ---
        enhanced_image_bytes = enhance_product_image(raw_image_bytes)
        
        # إرسال الصورة المحسنة
        await update.message.reply_photo(
            photo=io.BytesIO(enhanced_image_bytes),
            caption="✨ تعديل إضاءة وألوان الصورة واستوائها تلقائياً!"
        )

        # --- 2. كتابة الكابشن التسويقي العراقي البحت ---
        image_base64 = base64.b64encode(raw_image_bytes).decode("utf-8")

        prompt = f"""
أنت مدير تسويق ومبيعات شاطر جداً بأرقى بيجات الكوزمتك والعطور بالعراق.

حلل صورة المنتج المرفقة بالكامل.

السعر المحدد:
{price} دينار عراقي.

اكتب كابشن تسويقي جذاب ومؤثر جداً باللهجة العراقية الدارجة والاحترافية (بدون فصحى جافة، وبدون كلمات غريبة).
الهدف: إقناع الزبونة أو الزبون بالشراء ومراسلة البيج فوراً.

صغ الإعلان بهذا الأسلوب والترتيب بالضبط:

🔥 **المنتج:** [اسم المنتج أو المجموعة مع البراند إذا واضح بالصورة]

✨ **ليه هذا المنتج يجنن؟**
[نقاط سريعة ومغرية عن المظهر والجمال والفخامة الموجودة بالصورة]

🛍️ **الكابشن البيعي:**
[كلام عراقي دافئ وجذاب جداً يشجع على الطلب، مثلاً استخدام عبارات مثل: "كولكشن يجنن"، "إطلالة فخمة"، "ثبات وجمال"، "الكمية محدودة"]

💰 **السعر:** {price} د.ع فقط!

📩 **طريقة الطلب:**
دزولنا رسالة على الخاص (خاص البيج) وتوصلكم للحساب والتوصيل لكافة محافظات العراق 🚖

#️⃣ [5-7 هاشتاغات عراقية نشطة جداً مثل: #كوزمتك_عراقي #مكياج_بغداد #عطور_عراقية]

شروط مهمة:
- الكلام يكون عراقي بحت، مفهوم، وبسيط وبنفس الوقت راقي ومحفز للشراء.
- لا تذكر فوائد طبية أو ادعاءات غير حقيقية.
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
                    "✅ الكابشن البيعي العراقي جاهز 🔥:\n\n" + caption
                )
                return

            except Exception as e:
                last_error = f"{model}: {str(e)[:2000]}"
                continue

        await update.message.reply_text(
            "❌ تعدلت الصورة، لكن سيرفر النصوص المجاني مشغول حالياً.\n\n"
            f"التفاصيل:\n{str(last_error)[:1000]}"
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

    print("AI Seller Iraq is running smoothly...")
    app.run_polling()


if __name__ == "__main__":
    main()
