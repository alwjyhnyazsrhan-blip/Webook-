import json

# Master dictionary of known Arabic details for live Webook slugs
KNOWN_DETAILS = {
    "spl-raed-vs-orobah-tickets-293804": {
        "title_ar": "دوري روشن: الرائد ضد العروبة",
        "title_en": "Saudi Pro League: Al Raed vs Al Orobah",
        "genre_slug": "sports",
        "genre_id": 1,
        "venue": "مدينة الملك عبدالله الرياضية - بريدة",
        "city": "بريدة",
        "min_price": 25,
        "max_price": 250,
        "image": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=800&auto=format&fit=crop&q=80"
    },
    "spl-alqadsiah-vs-alkhaleej-906720": {
        "title_ar": "دوري روشن: القادسية ضد الخليج",
        "title_en": "Saudi Pro League: Al Qadsiah vs Al Khaleej",
        "genre_slug": "sports",
        "genre_id": 1,
        "venue": "استاد الأمير محمد بن فهد - الدمام",
        "city": "الدمام",
        "min_price": 35,
        "max_price": 300,
        "image": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=800&auto=format&fit=crop&q=80"
    },
    "riyadh-racing-season-rsace-night-16": {
        "title_ar": "سباقات موسم الرياض للخيل - الأمسية 16",
        "title_en": "Riyadh Horse Racing Season - Night 16",
        "genre_slug": "sports",
        "genre_id": 1,
        "venue": "ميدان الملك عبدالعزيز للفروسية - الجنادرية",
        "city": "الرياض",
        "min_price": 50,
        "max_price": 850,
        "image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800&auto=format&fit=crop&q=80"
    },
    "the-yemeni-orchestra-moc": {
        "title_ar": "سيمفونية التراث - الأوركسترا اليمنية",
        "title_en": "The Yemeni Heritage Orchestra - Ministry of Culture",
        "genre_slug": "concerts",
        "genre_id": 2,
        "venue": "مركز الملك فهد الثقافي - الرياض",
        "city": "الرياض",
        "min_price": 120,
        "max_price": 950,
        "image": "https://images.unsplash.com/photo-1465847899084-d164df4dedc6?w=800&auto=format&fit=crop&q=80"
    },
    "next-gen-atp-2024-tickets-897329": {
        "title_ar": "نهائيات الجيل القادم لرابطة محترفي التنس (Next Gen ATP)",
        "title_en": "Next Gen ATP Finals Tennis Championship",
        "genre_slug": "sports",
        "genre_id": 1,
        "venue": "مدينة الملك عبدالله الرياضية - جدة",
        "city": "جدة",
        "min_price": 100,
        "max_price": 1800,
        "image": "https://images.unsplash.com/photo-1595435934249-5df7ed86e1c0?w=800&auto=format&fit=crop&q=80"
    },
    "alf-taita-we-taita-rs-24": {
        "title_ar": "مسرحية ألف تيتة وتيتة - موسم الرياض",
        "title_en": "Alf Taita We Taita Comedy Play - Riyadh Season",
        "genre_slug": "theater",
        "genre_id": 3,
        "venue": "مسرح محمد العلي - بوليفارد سيتي",
        "city": "الرياض",
        "min_price": 95,
        "max_price": 800,
        "image": "https://images.unsplash.com/photo-1507676184212-d03ab07a01bf?w=800&auto=format&fit=crop&q=80"
    },
    "al-awwal-tour-stadium-tickets-843728": {
        "title_ar": "جولة استاد الأول بارك (Al Awwal Park Tour)",
        "title_en": "Al Awwal Park Stadium Experience Tour",
        "genre_slug": "experiences",
        "genre_id": 5,
        "venue": "استاد الأول بارك - جامعة الملك سعود",
        "city": "الرياض",
        "min_price": 45,
        "max_price": 150,
        "image": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=800&auto=format&fit=crop&q=80"
    },
    "mdlbeast-beast-house-ec": {
        "title_ar": "بيست هاوس ميدل بيست (MDLBEAST Beast House)",
        "title_en": "MDLBEAST Beast House Electronic Sessions",
        "genre_slug": "festivals",
        "genre_id": 4,
        "venue": "حي جاكس للفنون - الدرعية",
        "city": "الدرعية",
        "min_price": 150,
        "max_price": 1200,
        "image": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=800&auto=format&fit=crop&q=80"
    },
    "spl-alnassr-vs-damac-533869": {
        "title_ar": "دوري روشن: النصر ضد ضمك",
        "title_en": "Saudi Pro League: Al Nassr vs Damac",
        "genre_slug": "sports",
        "genre_id": 1,
        "venue": "استاد الأول بارك - الرياض",
        "city": "الرياض",
        "min_price": 50,
        "max_price": 1200,
        "image": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=800&auto=format&fit=crop&q=80"
    },
    "chinese-contemporary-art-exhibition": {
        "title_ar": "معرض الفن الصيني المعاصر - وزارة الثقافة",
        "title_en": "Chinese Contemporary Art Exhibition",
        "genre_slug": "conferences",
        "genre_id": 6,
        "venue": "متحف قصر خزام - جدة",
        "city": "جدة",
        "min_price": 30,
        "max_price": 100,
        "image": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=800&auto=format&fit=crop&q=80"
    },
    "pfl-championships-239842": {
        "title_ar": "نهائيات بطولة القتال للفنون المختلطة (PFL World Championships)",
        "title_en": "PFL MMA World Championships - Riyadh",
        "genre_slug": "sports",
        "genre_id": 1,
        "venue": "ذا فينيو أرينا - بوليفارد سيتي",
        "city": "الرياض",
        "min_price": 120,
        "max_price": 2800,
        "image": "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=800&auto=format&fit=crop&q=80"
    },
    "final-fantasy-xiv-in-symphony": {
        "title_ar": "حفل فاينل فانتسي السيمفوني (Final Fantasy XIV in Symphony)",
        "title_en": "Final Fantasy XIV Orchestral Concert",
        "genre_slug": "concerts",
        "genre_id": 2,
        "venue": "مسرح أبو بكر سالم - بوليفارد سيتي",
        "city": "الرياض",
        "min_price": 160,
        "max_price": 1400,
        "image": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800&auto=format&fit=crop&q=80"
    },
    "assala-jalsat-riyadh-season-747983": {
        "title_ar": "جلسات موسم الرياض: ليلة أصالة نصري",
        "title_en": "Riyadh Season Jalsat: Assala Nasri Live",
        "genre_slug": "concerts",
        "genre_id": 2,
        "venue": "مسرح محمد عبده أرينا - بوليفارد سيتي",
        "city": "الرياض",
        "min_price": 350,
        "max_price": 3200,
        "image": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800&auto=format&fit=crop&q=80"
    },
    "spl-ett-vs-itt-792500": {
        "title_ar": "دوري روشن: الاتفاق ضد الاتحاد",
        "title_en": "Saudi Pro League: Al Ettifaq vs Al Ittihad",
        "genre_slug": "sports",
        "genre_id": 1,
        "venue": "استاد نادي الاتفاق - الدمام",
        "city": "الدمام",
        "min_price": 40,
        "max_price": 600,
        "image": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=800&auto=format&fit=crop&q=80"
    },
    "jeddah-gt-race-2024-630372": {
        "title_ar": "سباق جدة جي تي للسيارات (Jeddah GT World Challenge)",
        "title_en": "Jeddah GT Race - Corniche Circuit",
        "genre_slug": "sports",
        "genre_id": 1,
        "venue": "حلبة كورنيش جدة - جدة",
        "city": "جدة",
        "min_price": 90,
        "max_price": 2200,
        "image": "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800&auto=format&fit=crop&q=80"
    },
    "saudi-cup-season": {
        "title_ar": "أمسيات كأس السعودية لسباقات الخيل (The Saudi Cup)",
        "title_en": "The Saudi Cup Championship Nights",
        "genre_slug": "sports",
        "genre_id": 1,
        "venue": "ميدان الملك عبدالعزيز للفروسية - الرياض",
        "city": "الرياض",
        "min_price": 85,
        "max_price": 4500,
        "image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800&auto=format&fit=crop&q=80"
    }
}

print("Known details keys count:", len(KNOWN_DETAILS))
