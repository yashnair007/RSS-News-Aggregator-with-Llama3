from flask import Flask, render_template, request
import feedparser
import requests
from datetime import datetime
from urllib.parse import quote_plus, urlparse
import re

app = Flask(__name__)

# --- CONFIG ---
GROQ_API_KEY = ""  # Replace with your actual Groq API key
GROQ_MODEL = "llama3-70b-8192"
groq_summary_cache = {}

REGIONS = {
    "Argentina": "AR", "Australia": "AU", "Austria": "AT", "Bangladesh": "BD", "Belgium": "BE",
    "Brazil": "BR", "Canada": "CA", "Chile": "CL", "China Chinese": "CN", "Colombia": "CO",
    "Czech Republic": "CZ", "Denmark": "DK", "Egypt": "EG", "Finland": "FI", "France": "FR",
    "Germany": "DE", "Greece": "GR", "Hong Kong": "HK", "Hungary": "HU", "India": "IN",
    "Indonesia": "ID", "Ireland": "IE", "Israel": "IL", "Italy": "IT", "Japan": "JP",
    "Kenya": "KE", "Malaysia": "MY", "Mexico": "MX", "Netherlands": "NL", "New Zealand": "NZ",
    "Nigeria": "NG", "Norway": "NO", "Pakistan": "PK", "Philippines": "PH", "Poland": "PL",
    "Portugal": "PT", "Romania": "RO", "Russia": "RU", "Saudi Arabia": "SA", "Singapore": "SG",
    "South Africa": "ZA", "South Korea": "KR", "Spain": "ES", "Sweden": "SE", "Switzerland": "CH",
    "Taiwan": "TW", "Thailand": "TH", "Turkey": "TR", "UAE": "AE", "UK": "GB", "USA": "US",
    "Vietnam": "VN"
}

COUNTRY_TLDS = {
    "AR": [".ar", "argentina", "argentine"], "AU": [".au", "australia", "australian"],
    "AT": [".at", "austria", "austrian"], "BD": [".bd", "bangladesh"],
    "BE": [".be", "belgium", "belgian"], "BR": [".br", "brazil", "brazilian"],
    "CA": [".ca", "canada", "canadian"], "CL": [".cl", "chile", "chilean"],
    "CN": [".cn", "china", "chinese"], "CO": [".co", "colombia", "colombian"],
    "CZ": [".cz", "czech"], "DK": [".dk", "denmark", "danish"],
    "EG": [".eg", "egypt", "egyptian"], "FI": [".fi", "finland", "finnish"],
    "FR": [".fr", "france", "french"], "DE": [".de", "germany", "german"],
    "GR": [".gr", "greece", "greek"], "HK": [".hk", "hong kong"],
    "HU": [".hu", "hungary", "hungarian"], "IN": [".in", "india", "indian"],
    "ID": [".id", "indonesia", "indonesian"], "IE": [".ie", "ireland", "irish"],
    "IL": [".il", "israel", "israeli"], "IT": [".it", "italy", "italian"],
    "JP": [".jp", "japan", "japanese"], "KE": [".ke", "kenya", "kenyan"],
    "MY": [".my", "malaysia", "malaysian"], "MX": [".mx", "mexico", "mexican"],
    "NL": [".nl", "netherlands", "dutch"], "NZ": [".nz", "new zealand"],
    "NG": [".ng", "nigeria", "nigerian"], "NO": [".no", "norway", "norwegian"],
    "PK": [".pk", "pakistan", "pakistani"], "PH": [".ph", "philippines", "filipino"],
    "PL": [".pl", "poland", "polish"], "PT": [".pt", "portugal", "portuguese"],
    "RO": [".ro", "romania", "romanian"], "RU": [".ru", "russia", "russian"],
    "SA": [".sa", "saudi", "arab news", "saudi gazette"], "SG": [".sg", "singapore"],
    "ZA": [".za", "south africa", "south african"], "KR": [".kr", "korea", "korean"],
    "ES": [".es", "spain", "spanish"], "SE": [".se", "sweden", "swedish"],
    "CH": [".ch", "switzerland", "swiss"], "TW": [".tw", "taiwan", "taiwanese"],
    "TH": [".th", "thailand", "thai"], "TR": [".tr", "turkey", "turkish"],
    "AE": [".ae", "uae", "emirates"], "GB": [".uk", ".co.uk", "britain", "british", "uk"],
    "US": [".us", "america", "american", "usa"], "VN": [".vn", "vietnam", "vietnamese"]
}

NEWS_SOURCES = [
    "Times of India", "Hindustan Times", "The Hindu", "Indian Express", "NDTV",
    "Economic Times", "Business Standard", "Financial Express", "LiveMint", "Moneycontrol",
    "Zee News", "India Today", "News18", "Firstpost", "The Tribune",
    "Deccan Chronicle", "Asian Age", "The Pioneer", "Statesman", "Telegraph India",
    "CNN", "BBC", "Reuters", "The Guardian", "Al Jazeera", "Sky News",
    "The New York Times", "The Washington Post", "USA Today", "Wall Street Journal",
    "Los Angeles Times", "Chicago Tribune", "The Times", "Daily Mail", "The Independent",
    "Financial Times", "Le Monde", "El País", "Der Spiegel", "The Sydney Morning Herald",
    "The Globe and Mail", "The Japan Times", "South China Morning Post", "The Straits Times",
    "Haaretz", "The Moscow Times", "The Irish Times", "The Age", "The Australian",
    "Bloomberg", "CNBC", "Forbes", "Yahoo Finance", "MarketWatch", "The Economist",
    "Business Insider", "Fortune", "Barron's", "Financial Post", "BloombergQuint",
    "ET Now", "Zee Business", "The Motley Fool", "Seeking Alpha",
    "TechCrunch", "Wired", "Engadget", "The Verge", "CNET", "Gizmodo",
    "Ars Technica", "ZDNet", "TechRadar", "VentureBeat", "Mashable",
    "Digital Trends", "PC Magazine", "Tom's Hardware", "IEEE Spectrum",
    "ESPN", "Goal.com", "The Athletic", "Fox Sports", "Sportstar", "Bleacher Report",
    "Sports Illustrated", "NBC Sports", "Sky Sports", "Eurosport", "The Score",
    "CBSSports", "Yahoo Sports", "Marca", "L'Équipe",
    "Healthline", "WebMD", "Medical News Today", "Nature", "Science Daily", "NASA",
    "MIT News", "Scientific American", "New Scientist", "National Geographic",
    "Psychology Today", "Mayo Clinic", "The Lancet", "Popular Science", "Discover Magazine",
    "Variety", "The Hollywood Reporter", "Entertainment Weekly", "Rolling Stone", "Vogue",
    "Vanity Fair", "People", "E! Online", "TMZ", "Billboard", "Pitchfork",
    "Harper's Bazaar", "Elle", "Cosmopolitan", "Men's Health",
    "Arab News", "Saudi Gazette", "Dawn", "The Nation", "Jakarta Post", "Bangkok Post",
    "Manila Times", "The Star", "Daily Nation", "The Standard", "This Day",
    "The Punch", "Vanguard", "The Korea Herald", "The Daily Star", "The Citizen"
]

SOURCE_NAME_VARIATIONS = {
    "times of india": ["times of india", "the times of india", "toi"],
    "toi": ["times of india", "the times of india", "toi"],
    "hindustan times": ["hindustan times"],
    "the hindu": ["the hindu", "hindu"],
    "indian express": ["indian express", "the indian express"],
    "ndtv": ["ndtv"],
    "economic times": ["economic times"],
    "business standard": ["business standard"],
    "financial express": ["financial express"],
    "livemint": ["livemint"],
    "moneycontrol": ["moneycontrol"],
    "zee news": ["zee news"],
    "india today": ["india today"],
    "news18": ["news18"],
    "firstpost": ["firstpost"],
    "the tribune": ["the tribune", "tribune"],
    "deccan chronicle": ["deccan chronicle"],
    "asian age": ["asian age"],
    "the pioneer": ["the pioneer", "pioneer"],
    "statesman": ["statesman", "the statesman"],
    "telegraph india": ["telegraph india", "the telegraph"],
    "cnn": ["cnn"],
    "bbc": ["bbc", "bbc news"],
    "reuters": ["reuters"],
    "the guardian": ["the guardian", "guardian"],
    "al jazeera": ["al jazeera"],
    "sky news": ["sky news"],
    "the new york times": ["new york times", "nytimes", "the new york times"],
    "the washington post": ["washington post", "the washington post"],
    "usa today": ["usa today"],
    "wall street journal": ["wall street journal", "wsj"],
    "los angeles times": ["los angeles times", "la times"],
    "chicago tribune": ["chicago tribune"],
    "the times": ["the times", "times uk"],
    "daily mail": ["daily mail"],
    "the independent": ["the independent", "independent"],
    "financial times": ["financial times", "ft"],
    "le monde": ["le monde"],
    "el país": ["el pais", "el país"],
    "der spiegel": ["der spiegel", "spiegel"],
    "the sydney morning herald": ["sydney morning herald", "smh"],
    "the globe and mail": ["globe and mail", "the globe and mail"],
    "the japan times": ["japan times", "the japan times"],
    "south china morning post": ["south china morning post", "scmp"],
    "the straits times": ["straits times", "the straits times"],
    "haaretz": ["haaretz"],
    "the moscow times": ["moscow times", "the moscow times"],
    "the irish times": ["irish times", "the irish times"],
    "the age": ["the age"],
    "the australian": ["the australian", "australian"],
    "bloomberg": ["bloomberg"],
    "cnbc": ["cnbc"],
    "forbes": ["forbes"],
    "yahoo finance": ["yahoo finance"],
    "marketwatch": ["marketwatch"],
    "the economist": ["the economist", "economist"],
    "business insider": ["business insider"],
    "fortune": ["fortune"],
    "barron's": ["barron's"],
    "financial post": ["financial post"],
    "bloombergquint": ["bloombergquint"],
    "et now": ["et now"],
    "zee business": ["zee business"],
    "the motley fool": ["motley fool", "the motley fool"],
    "seeking alpha": ["seeking alpha"],
    "techcrunch": ["techcrunch"],
    "wired": ["wired"],
    "engadget": ["engadget"],
    "the verge": ["the verge"],
    "cnet": ["cnet"],
    "gizmodo": ["gizmodo"],
    "ars technica": ["ars technica"],
    "zdnet": ["zdnet"],
    "techradar": ["techradar"],
    "venturebeat": ["venturebeat"],
    "mashable": ["mashable"],
    "digital trends": ["digital trends"],
    "pc magazine": ["pc magazine", "pcmag"],
    "tom's hardware": ["tom's hardware"],
    "ieee spectrum": ["ieee spectrum"],
    "espn": ["espn"],
    "goal.com": ["goal.com", "goal"],
    "the athletic": ["the athletic", "athletic"],
    "fox sports": ["fox sports"],
    "sportstar": ["sportstar"],
    "bleacher report": ["bleacher report"],
    "sports illustrated": ["sports illustrated"],
    "nbc sports": ["nbc sports"],
    "sky sports": ["sky sports"],
    "eurosport": ["eurosport"],
    "the score": ["the score"],
    "cbs sports": ["cbs sports", "cbssports"],
    "yahoo sports": ["yahoo sports"],
    "marca": ["marca"],
    "l'équipe": ["l'equipe", "l'équipe"],
    "healthline": ["healthline"],
    "webmd": ["webmd"],
    "medical news today": ["medical news today"],
    "nature": ["nature"],
    "science daily": ["science daily"],
    "nasa": ["nasa"],
    "mit news": ["mit news"],
    "scientific american": ["scientific american"],
    "new scientist": ["new scientist"],
    "national geographic": ["national geographic"],
    "psychology today": ["psychology today"],
    "mayo clinic": ["mayo clinic"],
    "the lancet": ["the lancet", "lancet"],
    "popular science": ["popular science"],
    "discover magazine": ["discover magazine", "discover"],
    "variety": ["variety"],
    "the hollywood reporter": ["hollywood reporter", "the hollywood reporter"],
    "entertainment weekly": ["entertainment weekly", "ew"],
    "rolling stone": ["rolling stone"],
    "vogue": ["vogue"],
    "vanity fair": ["vanity fair"],
    "people": ["people"],
    "e! online": ["e! online", "eonline"],
    "tmz": ["tmz"],
    "billboard": ["billboard"],
    "pitchfork": ["pitchfork"],
    "harper's bazaar": ["harper's bazaar", "harpers bazaar"],
    "elle": ["elle"],
    "cosmopolitan": ["cosmopolitan", "cosmo"],
    "men's health": ["men's health"],
    "arab news": ["arab news"],
    "saudi gazette": ["saudi gazette"],
    "dawn": ["dawn"],
    "the nation": ["the nation", "nation"],
    "jakarta post": ["jakarta post", "the jakarta post"],
    "bangkok post": ["bangkok post"],
    "manila times": ["manila times", "the manila times"],
    "the star": ["the star", "star"],
    "daily nation": ["daily nation"],
    "the standard": ["the standard", "standard"],
    "this day": ["this day"],
    "the punch": ["the punch", "punch"],
    "vanguard": ["vanguard"],
    "the korea herald": ["korea herald", "the korea herald"],
    "the daily star": ["daily star", "the daily star"],
    "the citizen": ["the citizen", "citizen"]
}

DATE_OPTIONS = {
    "Today": 0, "Yesterday": 1, "Last 2 Days": 2, "Last 3 Days": 3, "Last 7 Days": 7, "All": None
}

def fetch_articles(query=None, limit=8, region_code=None, date_range_days=None, source_filter=None):
    today = datetime.now().date()
    if query and source_filter and source_filter.lower() != "all":
        query_encoded = quote_plus(f"{query} from:{source_filter}")
    elif source_filter and source_filter.lower() != "all":
        query_encoded = quote_plus(f"from:{source_filter}")
    elif query:
        query_encoded = quote_plus(query)
    else:
        query_encoded = ""
    rss_region = region_code if region_code else "US"
    url = f"https://news.google.com/rss/search?q={query_encoded}&hl=en-{rss_region}&gl={rss_region}&ceid={rss_region}:en"
    feed = feedparser.parse(url)
    articles = []
    filtered_out_sources = set()

    for entry in feed.entries[:limit * 3]:
        pub_date = datetime(*entry.published_parsed[:6]).date()
        if date_range_days is not None and (today - pub_date).days > date_range_days:
            continue

        source_title = entry.get("source", {}).get("title", "").lower()
        source_url = entry.get("source", {}).get("href", "") or entry.get("link", "")
        
        if region_code and region_code != "US":
            country_indicators = COUNTRY_TLDS.get(region_code, [])
            source_matched = False
            parsed_url = urlparse(source_url)
            domain = parsed_url.netloc.lower()
            source_title_lower = source_title.lower()
            for indicator in country_indicators:
                if indicator.startswith(".") and domain.endswith(indicator):
                    source_matched = True
                    break
                elif indicator in source_title_lower:
                    source_matched = True
                    break
            if not source_matched:
                filtered_out_sources.add(source_title)
                continue

        if source_filter and source_filter.lower() != "all":
            source_matched = False
            source_variations = SOURCE_NAME_VARIATIONS.get(source_filter.lower(), [source_filter.lower()])
            for variation in source_variations:
                if variation in source_title:
                    source_matched = True
                    break
            if not source_matched:
                filtered_out_sources.add(source_title)
                continue

        articles.append({
            "title": entry.title,
            "link": entry.link,
            "published": pub_date,
            "source": entry.get("source", {}).get("title", "Unknown")
        })

        if len(articles) >= limit:
            break

    warning = None
    if not articles:
        region_name = [k for k, v in REGIONS.items() if v == region_code][0] if region_code else "All"
        if source_filter and source_filter.lower() != "all":
            warning = f"No articles found for source '{source_filter}' in region '{region_name}' with date range '{date_range_days or 'All'} days'. Try selecting 'All' publishers or a broader date range."
        elif query:
            warning = f"No articles found for topic '{query}' in region '{region_name}' with date range '{date_range_days or 'All'} days'. Try selecting 'All' regions or a broader date range."
        else:
            warning = f"No articles found with date range '{date_range_days or 'All'} days'. Try a broader date range."
    
    return articles, warning

def call_groq(prompt, max_tokens=300):
    if prompt in groq_summary_cache:
        return groq_summary_cache[prompt]
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "system", "content": "You are a helpful AI news summarizer."},
                             {"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": max_tokens
            },
            timeout=15
        )
        data = res.json()
        if "choices" in data:
            content = data["choices"][0]["message"]["content"].strip()
            groq_summary_cache[prompt] = content
            return content
    except Exception as e:
        return f"❌ Error: {e}"
    return "❌ Groq API error"

def summarize_articles(articles):
    if not articles:
        return "No articles to summarize."
    headlines = "\n".join(f"- {a['title']}" for a in articles)
    prompt = f"Write a 6-line news summary based on these headlines:\n{headlines}"
    return call_groq(prompt)

@app.route("/", methods=["GET", "POST"])
def index():
    headlines = ["India", "AI", "Sports", "Oil Prices", "Stock Market", "Climate Change", "Exchange Rates", "Country Economy"]
    headline_articles = []
    for topic in headlines:
        articles, _ = fetch_articles(topic, limit=2)
        headline_articles.append({"topic": topic, "articles": articles})

    topic_groups = [["Technology", "Finance"], ["Health", "Politics"], ["Climate", "Sports"], ["AI", "Defence"]]
    category_data = []
    for group in topic_groups:
        combined_articles = []
        for topic in group:
            articles, _ = fetch_articles(topic, limit=3)
            combined_articles.extend(articles)
        summary = summarize_articles(combined_articles)
        category_data.append({"group": group, "articles": combined_articles, "summary": summary})

    search_results = None
    search_summary = None
    search_warning = None
    followup_answer = None

    if request.method == "POST":
        query = request.form.get("query", "Apple")
        region_name = request.form.get("region", "All")
        publisher = request.form.get("publisher", "All")
        date_option = request.form.get("date_range", "All")
        followup = request.form.get("followup", "")

        region_code = None if region_name == "All" else REGIONS.get(region_name, "US")
        date_limit = DATE_OPTIONS.get(date_option, None)
        source_filter = None if publisher == "All" else publisher

        articles, search_warning = fetch_articles(query, limit=8, region_code=region_code, date_range_days=date_limit, source_filter=source_filter)
        search_results = articles
        search_summary = summarize_articles(articles) if articles else None

        if followup and search_summary:
            q_prompt = f"Based on this summary:\n{search_summary}\n\nAnswer this clearly: {followup}"
            followup_answer = call_groq(q_prompt, max_tokens=200)

        source_selected = request.form.get("source_select", "Select a source")
        source_date_option = request.form.get("source_date_range", "All")
        source_articles = None
        source_summary = None
        source_warning = None

        if source_selected != "Select a source":
            source_articles, source_warning = fetch_articles(
                query=None, limit=8, region_code=None, date_range_days=DATE_OPTIONS.get(source_date_option, None), source_filter=source_selected
            )
            source_summary = summarize_articles(source_articles) if source_articles else None

        return render_template(
            "index.html",
            headline_articles=headline_articles,
            category_data=category_data,
            regions=["All"] + sorted(REGIONS.keys()),
            news_sources=["All"] + sorted(NEWS_SOURCES),
            date_options=DATE_OPTIONS.keys(),
            search_results=search_results,
            search_summary=search_summary,
            search_warning=search_warning,
            followup_answer=followup_answer,
            query=query,
            region=region_name,
            publisher=publisher,
            date_range=date_option,
            source_articles=source_articles,
            source_summary=source_summary,
            source_warning=source_warning,
            source_select=source_selected,
            source_date_range=source_date_option
        )

    return render_template(
        "index.html",
        headline_articles=headline_articles,
        category_data=category_data,
        regions=["All"] + sorted(REGIONS.keys()),
        news_sources=["All"] + sorted(NEWS_SOURCES),
        date_options=DATE_OPTIONS.keys(),
        search_results=None,
        search_summary=None,
        search_warning=None,
        followup_answer=None,
        query="Apple",
        region="All",
        publisher="All",
        date_range="All",
        source_articles=None,
        source_summary=None,
        source_warning=None,
        source_select="Select a source",
        source_date_range="All"
    )

if __name__ == "__main__":
     app.run(host="0.0.0.0", port=81, debug=True)