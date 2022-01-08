import requests

SNAP_URL = 'https://tempostorm.com/api/snapshots/findOne'
DECK_URL = 'https://tempostorm.com/api/decks/findOne'

def get_current_time():
    from datetime import datetime
    now = datetime.utcnow()
    return now.strftime('%Y-%m-%dT%H:%M:%S.') + now.strftime('%f')[:-3] + 'Z'

def get_slug():
    current_time = get_current_time()
    json = {'filter': {
        'order': 'createdDate DESC',
        'fields': ['id', 'snapshotType', 'isActive', 'publishDate'],
        'where': {
            'isActive': True,
            'publishDate': { 'lte': current_time },
            'snapshotType': 'standard'
        },
        'include': [{ 'relation': 'slugs' }]
        }
    }
    r = requests.get(SNAP_URL, json=json)
    r_json = r.json()
    return r_json['slugs'][0]['slug']

def get_tiers():
    slug = get_slug()
    json = {
        "filter": {
            "where": { "slug": slug, "snapshotType": "standard" },
            "include": [
                {
                "relation": "deckTiers",
                "scope": {
                    "include": [
                    {
                        "relation": "deck",
                        "scope": {
                        "fields": ["id", "name", "slug", "playerClass"],
                        "include": {
                            "relation": "slugs",
                            "scope": { "fields": ["linked", "slug"] }
                        }
                        }
                    },
                    {
                        "relation": "deckTech",
                        "scope": {
                        "include": [
                            {
                            "relation": "cardTech",
                            "scope": {
                                "include": [
                                {
                                    "relation": "card",
                                    "scope": { "fields": ["name", "name_ru", "photoNames"] }
                                }
                                ]
                            }
                            }
                        ]
                        }
                    }
                    ]
                }
                }
            ]
        }
    }
    r = requests.get(SNAP_URL, json=json)
    return r.json()['deckTiers']

def get_deck(slug):
    json = {
        "filter": {
            "where": { "slug": slug },
            "fields": [
            "id",
            "createdDate",
            "name",
            "name_ru",
            "description",
            "description_ru",
            "playerClass",
            "premium",
            "dust",
            "heroName",
            "authorId",
            "deckType",
            "isPublic",
            "chapters",
            "chapters_ru",
            "youtubeId",
            "gameModeType",
            "isActive",
            "isCommentable",
            "isMultilingual"
            ],
            "include": [
            {
                "relation": "cards",
                "scope": {
                "include": "card",
                "scope": {
                    "fields": [
                    "id",
                    "name",
                    "name_ru",
                    "cardType",
                    "cost",
                    "dust",
                    "photoNames"
                    ]
                }
                }
            },
            {
                "relation": "comments",
                "scope": {
                "fields": [
                    "id",
                    "votes",
                    "voteScore",
                    "authorId",
                    "createdDate",
                    "text"
                ],
                "include": {
                    "relation": "author",
                    "scope": { "fields": ["id", "username", "gravatarUrl"] }
                },
                "order": "createdDate DESC"
                }
            },
            {
                "relation": "author",
                "scope": { "fields": ["id", "username", "gravatarUrl"] }
            },
            {
                "relation": "matchups",
                "scope": {
                "fields": ["forChance", "deckName", "deckName_ru", "className"]
                }
            },
            { "relation": "votes", "fields": ["id", "direction", "authorId"] }
            ]
        }
    }
    r = requests.get(DECK_URL, json=json)

def get_decks(decks):
    for deck in decks:
        if deck['tier'] == 1:
            new_deck = {
                'rank': deck['ranks'][0] 
            }

print(get_slug())