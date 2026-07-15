"""Multilingual response templates for WhatsApp Order Assistant."""

MESSAGES = {
    # ── Global / Generic ───────────────────────────────────────────
    "LANGUAGE_SELECTION": {
        "en": "🙏 Welcome to Go Chicken!\nPlease select your preferred language:",
        "hi": "🙏 Welcome to Go Chicken!\nPlease select your preferred language:",
        "te": "🙏 Welcome to Go Chicken!\nPlease select your preferred language:",
    },
    "WELCOME_WITH_RATE": {
        "en": "🐔 Good morning, {name}!\nToday's Live Bird: *₹{rate}/kg*.\nHow can I help you today?",
        "hi": "🐔 सुप्रभात {name}!\nआज का Live Bird रेट: *₹{rate}/kg*.\nमैं आपकी कैसे मदद कर सकता हूँ?",
        "te": "🐔 నమస్కారం {name}!\nఈ రోజు Live Bird ధర: *₹{rate}/kg*.\nనేను మీకు ఎలా సహాయపడగలను?",
    },
    "MAIN_MENU": {
        "en": "🐔 *Go Chicken* — How can I help?",
        "hi": "🐔 *Go Chicken* — मैं आपकी कैसे मदद कर सकता हूँ?",
        "te": "🐔 *Go Chicken* — నేను మీకు ఎలా సహాయపడగలను?",
    },
    "OFF_TOPIC": {
        "en": "Sorry, I'm the Go Chicken Order Assistant. I can only help with orders, prices, deliveries, quotes, payments, and khata.",
        "hi": "क्षमा करें, मैं Go Chicken Order Assistant हूँ। मैं केवल पोल्ट्री ऑर्डर, दरें, डिलीवरी, कोटेशन और खाता में मदद कर सकता हूँ।",
        "te": "క్షమించండి. నేను Go Chicken Order Assistant మాత్రమే. నేను poultry orders, prices, deliveries, quotes, payments మరియు khata విషయాల్లో మాత్రమే సహాయం చేయగలను.",
    },
    "RECOVERY_MENU": {
        "en": "I'm not sure I understood. How can I help?",
        "hi": "मुझे समझ नहीं आया। मैं आपकी कैसे मदद कर सकता हूँ?",
        "te": "నాకు అర్థం కాలేదు. నేను మీకు ఎలా సహాయపడగలను?",
    },
    "SESSION_EXPIRED": {
        "en": "Our previous conversation expired. Let's start fresh!",
        "hi": "हमारी पिछली बातचीत समाप्त हो गई है। आइए नई शुरुआत करें!",
        "te": "మన మునుపటి సంభాషణ ముగిసింది. మళ్లీ ప్రారంభిద్దాం!",
    },
    "HANDOFF": {
        "en": "👨‍💼 We've notified your wholesaler. Our manager will contact you shortly.",
        "hi": "👨‍💼 हमने आपके थोक व्यापारी को सूचित कर दिया है। हमारे प्रबंधक जल्द ही आपसे संपर्क करेंगे।",
        "te": "👨‍💼 మేము మీ హోల్‌సేలర్‌కు తెలియజేశాము. మా మేనేజర్ త్వరలో మిమ్మల్ని సంప్రదిస్తారు.",
    },
    "UNREGISTERED": {
        "en": "⚠️ Your number ({phone}) is not registered. Contact your wholesaler to activate ordering. 🚛",
        "hi": "⚠️ आपका नंबर ({phone}) पंजीकृत नहीं है। ऑर्डर शुरू करने के लिए अपने थोक व्यापारी से संपर्क करें। 🚛",
        "te": "⚠️ మీ నంబర్ ({phone}) నమోదు కాలేదు. ఆర్డరింగ్ ప్రారంభించడానికి దయచేసి మీ హోల్‌సేలర్‌ను సంప్రదించండి. 🚛",
    },
    "CANCEL_OPERATION": {
        "en": "Operation cancelled.",
        "hi": "ऑपरेशन रद्द कर दिया गया।",
        "te": "ఆపరేషన్ రద్దు చేయబడింది.",
    },

    # ── Ordering Flow ──────────────────────────────────────────────
    "ASK_PRODUCT": {
        "en": "Which product do you need?",
        "hi": "आपको कौन सा उत्पाद चाहिए?",
        "te": "మీకు ఏ ప్రొడక్ట్ కావాలి?",
    },
    "ASK_QUANTITY": {
        "en": "How many KG of {product} do you need?",
        "hi": "{product} कितने KG चाहिए?",
        "te": "{product} ఎన్ని KG కావాలి?",
    },
    "INVALID_QUANTITY": {
        "en": "Please enter quantity in KG (numbers only).",
        "hi": "कृपया KG में मात्रा दर्ज करें (केवल संख्याएँ)।",
        "te": "దయచేసి KG లో క్వాంటిటీ ఇవ్వండి (నంబర్స్ మాత్రమే).",
    },
    "ORDER_PREVIEW": {
        "en": "📦 *Order Preview*\n• {product}\n• {qty} kg\n• ₹{rate}/kg\n• Total: *₹{total}*\n\n💳 Khata Balance: ₹{balance}",
        "hi": "📦 *ऑर्डर प्रीव्यू*\n• {product}\n• {qty} kg\n• ₹{rate}/kg\n• कुल: *₹{total}*\n\n💳 खाता शेष: ₹{balance}",
        "te": "📦 *ఆర్డర్ ప్రివ్యూ*\n• {product}\n• {qty} kg\n• ₹{rate}/kg\n• మొత్తం: *₹{total}*\n\n💳 ఖాతా బ్యాలెన్స్: ₹{balance}",
    },
    "ORDER_CONFIRMED": {
        "en": "🎉 *Order Confirmed!*\n#{order_id}\n{qty}kg {product} locked in. 🚛✅",
        "hi": "🎉 *ऑर्डर कन्फर्म!*\n#{order_id}\n{qty}kg {product} बुक हो गया है। 🚛✅",
        "te": "🎉 *ఆర్డర్ కన్ఫర్మ్ అయింది!*\n#{order_id}\n{qty}kg {product} బుక్ చేయబడింది. 🚛✅",
    },
    "ORDER_CANCELLED": {
        "en": "❌ Cancelled. Send a new order anytime!",
        "hi": "❌ रद्द किया गया। कभी भी नया ऑर्डर भेजें!",
        "te": "❌ రద్దు చేయబడింది. ఎప్పుడైనా కొత్త ఆర్డర్ పంపవచ్చు!",
    },
    "REPEAT_ORDER_PREVIEW": {
        "en": "🔄 *Repeat Last Order?*\n• {product}\n• {qty} kg\n• ₹{rate}/kg\n• Total: *₹{total}*",
        "hi": "🔄 *पिछला ऑर्डर दोहराएं?*\n• {product}\n• {qty} kg\n• ₹{rate}/kg\n• कुल: *₹{total}*",
        "te": "🔄 *గత ఆర్డర్‌ను మళ్లీ చేయాలా?*\n• {product}\n• {qty} kg\n• ₹{rate}/kg\n• మొత్తం: *₹{total}*",
    },
    "NO_PREVIOUS_ORDER": {
        "en": "You don't have any previous orders to repeat. Let's create a new one!",
        "hi": "आपके पास दोहराने के लिए कोई पिछला ऑर्डर नहीं है। आइए एक नया ऑर्डर बनाएं!",
        "te": "రిపీట్ చేయడానికి మీకు గత ఆర్డర్‌లు లేవు. కొత్తది క్రియేట్ చేద్దాం!",
    },

    # ── Pricing ────────────────────────────────────────────────────
    "PRICE_ASK_PRODUCT": {
        "en": "Which product price do you want to check?",
        "hi": "आप किस उत्पाद की कीमत जानना चाहते हैं?",
        "te": "మీరు ఏ ప్రొడక్ట్ ధర తెలుసుకోవాలనుకుంటున్నారు?",
    },
    "PRICE_RESULT": {
        "en": "💰 *{product}*: ₹{rate}/kg\n\nWant to order?",
        "hi": "💰 *{product}*: ₹{rate}/kg\n\nक्या आप ऑर्डर करना चाहते हैं?",
        "te": "💰 *{product}*: ₹{rate}/kg\n\nఆర్డర్ చేయాలనుకుంటున్నారా?",
    },

    # ── Khata ──────────────────────────────────────────────────────
    "KHATA_SUMMARY": {
        "en": "💳 *Khata Summary*\n• Outstanding: ₹{balance}\n• Last Payment: ₹{last_payment}\n• Due Invoices: {due_count}",
        "hi": "💳 *खाता सारांश*\n• बकाया: ₹{balance}\n• अंतिम भुगतान: ₹{last_payment}\n• देय चालान: {due_count}",
        "te": "💳 *ఖాతా సారాంశం*\n• బకాయి: ₹{balance}\n• చివరి చెల్లింపు: ₹{last_payment}\n• చెల్లించాల్సిన ఇన్‌వాయిస్‌లు: {due_count}",
    },

    # ── Order Status ───────────────────────────────────────────────
    "ORDER_STATUS": {
        "en": "📦 *Order #{order_id}*\n✅ {status}\n🚚 {truck_info}\n📍 Expected: {eta}",
        "hi": "📦 *ऑर्डर #{order_id}*\n✅ {status}\n🚚 {truck_info}\n📍 अपेक्षित: {eta}",
        "te": "📦 *ఆర్డర్ #{order_id}*\n✅ {status}\n🚚 {truck_info}\n📍 అంచనా: {eta}",
    },
    "NO_ACTIVE_ORDER": {
        "en": "You don't have any active orders right now.",
        "hi": "आपके पास अभी कोई सक्रिय ऑर्डर नहीं है।",
        "te": "ప్రస్తుతం మీకు యాక్టివ్ ఆర్డర్‌లు లేవు.",
    }
}

def get_message(key: str, lang: str | None, **kwargs) -> str:
    """Get a formatted, translated message. Falls back to English."""
    if lang not in ("en", "hi", "te"):
        lang = "en"
    
    template = MESSAGES.get(key, {}).get(lang)
    if not template:
        template = MESSAGES.get(key, {}).get("en", "")
    
    return template.format(**kwargs) if kwargs else template
