import httpx


QUERY = """
uery exploreCounts($lang: String, $limit: Int, $skip: Int, $eventWhere: EventFilter, $experienceWhere: ExperienceFilter, $restaurantWhere: RestaurantFilter, $zoneWhere: ZoneFilter) {
  eventCollection(locale: $lang, limit: $limit, skip: $skip, where: $eventWhere) {
    total
    items { title slug ticketingUrlSlug organizationSlug category { title slug } schedule { openDateTime closeDateTime } }
  }
  experienceCollection(locale: $lang, limit: $limit, skip: $skip, where: $experienceWhere) {
    total
    items { title slug ticketingUrlSlug category { title slug } schedule { openDateTime closeDateTime } }
  }
  restaurantCollection(locale: $lang, limit: $limit, skip: $skip, where: $restaurantWhere) {
    total
    items { title slug ticketingUrlSlug category { title slug } schedule { openDateTime closeDateTime } }
  }
  zoneCollection(locale: $lang, limit: $limit, skip: $skip, where: $zoneWhere) {
    total
    items { title slug category { title slug } schedule { openDateTime closeDateTime } }
  }
}
"""


def main():
    with httpx.Client(timeout=30, headers={
        "Content-Type": "application/json",
        "Origin": "https://webook.com",
        "Referer": "https://webook.com/",
        "User-Agent": "Mozilla/5.0",
    }) as client:
        resp = client.post(
            "https://cdn.webook.com",
            json={
                "uery": QUERY,
                "variables": {
                    "lang": "en-US",
                    "limit": 5,
                    "skip": 0,
                    "eventWhere": {
                        "visibility_not": "private",
                        "AND": [
                            {
                                "category": {
                                    "slug_in": [
                                        "restaurants",
                                        "theater",
                                        "sports-event",
                                        "experience",
                                        "music-events",
                                    ]
                                }
                            }
                        ],
                        "OR": [
                            {"schedule": {"closeDateTime_exists": False}},
                            {"schedule": {"closeDateTime_gte": "2026-05-07T00:00:00.000Z"}},
                        ],
                    },
                    "experienceWhere": {
                        "visibility_not": "private",
                        "OR": [
                            {"schedule": {"closeDateTime_exists": False}},
                            {"schedule": {"closeDateTime_gte": "2026-05-07T00:00:00.000Z"}},
                        ],
                    },
                    "restaurantWhere": {
                        "visibility_not": "private",
                    },
                    "zoneWhere": {
                        "visibility_not": "private",
                    },
                },
            },
        )
    print("STATUS", resp.status_code)
    print(resp.text[:3000])


if __name__ == "__main__":
    main()
