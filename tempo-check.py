import requests

SNAP_URL = 'https://tempostorm.com/api/snapshots/findOne'
DECK_URL = 'https://tempostorm.com/api/decks/findOne'
FIELDNAMES = ['cardQuantity', 'name', 'cost', 'rarity', 'text', 'attack', 'health', 'cardType', 'expansion']

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

def get_tiers(slug):
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

def get_card(card):
    card_data = card['card']
    new_card = dict((key, value) for key, value in card_data.items() if key in FIELDNAMES)
    new_card['cardQuantity'] = card['cardQuantity']
    return new_card

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
    r_json = r.json()
    name = r_json['name']
    player_class = r_json['playerClass']
    cards_raw = r_json['cards']
    cards = []
    for card in cards_raw:
        cards.append(get_card(card))
    return {
        'name': name,
        'slug': slug,
        'playerClass': player_class,
        'cards': cards
    }

def get_decks(decks):
    deck_list = []
    for deck in decks:
        if deck['tier'] == 1:
            new_deck = get_deck(deck['deck']['slugs'][0]['slug'])
            new_deck['rank'] = deck['ranks'][0]
            deck_list.append(new_deck)
    return deck_list

def sort_by_rank(e):
    return e['rank']

def make_csvs():
    import csv
    pub_date = get_slug()
    decks = get_decks(get_tiers(pub_date))
    decks.sort(key=sort_by_rank)
    for deck in decks:
        filename = pub_date +'_' +'Rank' +str(deck['rank']) +'_' + deck['playerClass'] +'_' + deck['slug'] +'.csv'
        with open(filename, 'w+') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()
            for card in deck['cards']:
                writer.writerow(card)

make_csvs()