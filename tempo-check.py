import requests, csv, os
from datetime import datetime

SNAP_URL = 'https://tempostorm.com/api/snapshots/findOne'
DECK_URL = 'https://tempostorm.com/api/decks/findOne'
FIELDNAMES = ['cardQuantity', 'name', 'cost', 'rarity', 'text', 'attack', 'health', 'cardType', 'expansion']
LATEST_SLUG = 'latest_slug.txt'
LOG_FILE = 'log.csv'
CURRENT_TIME_RAW = datetime.utcnow()
CURRENT_TIME = CURRENT_TIME_RAW.strftime('%Y-%m-%dT%H:%M:%S')
SLUG_QUERY_TIME = CURRENT_TIME +'.' + CURRENT_TIME_RAW.strftime('%f')[:-3] + 'Z'
LOG_FIELD_1 = 'date_ran'
LOG_FIELD_2 = 'needed_refresh'

def get_slug():
    json = {'filter': {
        'order': 'createdDate DESC',
        'fields': ['id', 'snapshotType', 'isActive', 'publishDate'],
        'where': {
            'isActive': True,
            'publishDate': { 'lte': SLUG_QUERY_TIME },
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

def set_new_slug(slug):
    with open(LATEST_SLUG, 'w+') as f:
        f.write(slug)

def init_check():
    pub_date = get_slug()
    needs_refresh = False
    if os.path.exists(LATEST_SLUG):
        with open(LATEST_SLUG) as f:
            needs_refresh = False if pub_date == f.read() else True
    else:
        needs_refresh = True
    return pub_date, needs_refresh

def make_csvs(pub_date):
    decks = get_decks(get_tiers(pub_date))
    decks.sort(key=sort_by_rank)
    for deck in decks:
        filename = pub_date +'_' +'Rank' +str(deck['rank']) +'_' + deck['playerClass'] +'_' + deck['slug'] +'.csv'
        with open(filename, 'w+') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()
            for card in deck['cards']:
                writer.writerow(card)

def alert_user(pub_date):
    from twilio.rest import Client
    import config
    client = Client(config.twilio_sid, config.twilio_auth_token)
    message = client.messages.create(
        messaging_service_sid = config.twilio_msg_svc,
        body = 'New Meta Snapshot published %s. Decks uploaded. Check cloud computer when you can.' % (pub_date),
        to = config.twilio_number
    )
    return(message.sid)    

def log_results(needs_refresh):
    is_log = True if os.path.exists(LOG_FILE) else False
    new_row = {LOG_FIELD_1: CURRENT_TIME, LOG_FIELD_2: needs_refresh}
    with open(LOG_FILE, 'a+') as f:
        logwriter = csv.DictWriter(f, fieldnames=[LOG_FIELD_1, LOG_FIELD_2])
        if not(is_log):
            logwriter.writeheader()
        else:
            pass
        logwriter.writerow(new_row)
    return new_row

def main():
    pub_date, needs_refresh = init_check()
    if needs_refresh:
        make_csvs(pub_date)
        alert_user(pub_date)
        set_new_slug(pub_date)
    log_results(needs_refresh)

main()