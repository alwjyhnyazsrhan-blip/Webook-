import re

urls = [
    "https://webook.com/ar/events/oasis-rs-24",
    "https://webook.com/ar/sa/taf/music-events/events/shafa-event-dj-dahoum-al-dossari-amr-gaber",
    "https://webook.com/en/experiences/doos-karting",
    "https://webook.com/ar/zones/boulevard-city",
    "https://webook.com/ar/events/rabeh-saer-night-jalsat-riyadh-season-387291/book"
]

regex = r'/(events|experiences|restaurants|packages|zones)/([^/?#]+)$'

for u in urls:
    match = re.search(regex, u)
    if match:
        print(f"MATCH: {u} -> Type: {match.group(1)}, Slug: {match.group(2)}")
    else:
        print(f"NO MATCH: {u}")
