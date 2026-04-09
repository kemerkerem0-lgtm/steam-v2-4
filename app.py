from flask import Flask, render_template, request, jsonify
import requests
import random
import time

app = Flask(__name__)

def get_steam_api(endpoint, params={}):
    url = f"https://store.steampowered.com/api/{endpoint}"
    params.update({"cc": "tr", "l": "turkish", "t": int(time.time())})
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        return res.json()
    except:
        return None

@app.route("/")
def index():
    raw = get_steam_api("featuredcategories")
    all_discovery = []
    if raw:
        for key in ['featured_win', 'specials', 'new_releases', 'top_sellers']:
            if key in raw:
                all_discovery += raw[key].get('items', [])
    
    seen = set()
    unique_discovery = [x for x in all_discovery if not (x['id'] in seen or seen.add(x['id']))]
    return render_template("index.html", content={"discovery": unique_discovery[:30]})

@app.route("/game/<int:app_id>")
def game_detail(app_id):
    data = get_steam_api("appdetails", {"appids": app_id})
    if not data or str(app_id) not in data or not data[str(app_id)].get("success"):
        return "Oyun bulunamadı.", 404
    
    game = data[str(app_id)]["data"]
    try:
        rev_url = f"https://store.steampowered.com/appreviews/{app_id}?json=1&l=turkish"
        reviews = requests.get(rev_url, timeout=5).json()
    except:
        reviews = {"reviews": []}
    return render_template("detail.html", game=game, reviews=reviews)

@app.route("/api/filter/<type>")
def filter_games(type):
    raw = get_steam_api("featuredcategories")
    if not raw: return jsonify([])
    mapping = {"trend": "top_sellers", "indirim": "specials", "yeni": "new_releases"}
    key = mapping.get(type, "featured_win")
    data = raw.get(key, {}).get('items', [])
    if type == "rastgele" and data:
        random.shuffle(data)
        return jsonify([data[0]])
    return jsonify(data)

@app.route("/api/search")
def search():
    query = request.args.get("q", "")
    if not query: return jsonify([])
    res = requests.get(f"https://store.steampowered.com/api/storesearch/?term={query}&l=turkish&cc=tr").json()
    return jsonify(res.get("items", []))

if __name__ == "__main__":
    app.run(debug=True)