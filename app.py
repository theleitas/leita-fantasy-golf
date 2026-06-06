import streamlit as st
import streamlit.components.v1 as components
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    def st_autorefresh(*args, **kwargs):
        return None
import requests, json, base64, time, html, os, mimetypes, re
from functools import lru_cache
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

RENDER_T0 = time.perf_counter()

st.set_page_config(
    page_title="DeskCheck Golf Challenge",
    page_icon="titlethumb.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"], .stApp { background:#000!important; color:#fff!important; }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebar"] { background:#000!important; }
.stMarkdown, .stCaption, label, p, h1, h2, h3, h4, h5, h6 { color:#fff; }
div[data-testid="stExpander"] { background:#050505!important; border:1px solid #333!important; }
button { border-radius:8px!important; }
div[data-testid="stButton"] > button {
    background:#151515!important; color:#fff!important; border:1px solid #555!important;
    font-weight:800!important; white-space:normal!important; min-height:46px!important; line-height:1.2!important;
}
div[data-testid="stButton"] > button:hover { background:#222!important; color:#fff!important; border-color:#888!important; }
div[data-testid="stButton"] > button:focus {
    background:#222!important; color:#fff!important; border-color:#ffeb3b!important;
    box-shadow:0 0 0 2px rgba(255,235,59,.35)!important;
}
div[data-testid="stButton"] > button:disabled, div[data-testid="stButton"] > button[disabled] {
    background:#2b2b2b!important; color:#9a9a9a!important; border-color:#444!important; opacity:1!important;
}
.refresh-button-wrap div[data-testid="stButton"] > button {
    width:100%!important; min-height:64px!important; background:#ff4b00!important; color:#000!important;
    border:3px solid #ffb000!important; font-size:1.35rem!important; font-weight:1000!important;
    letter-spacing:.02em!important; text-transform:uppercase!important;
    box-shadow:0 0 18px rgba(255,75,0,.7), inset 0 0 10px rgba(255,255,255,.28)!important;
}
.refresh-button-wrap div[data-testid="stButton"] > button:hover {
    background:#ff7a00!important; color:#000!important; border-color:#ffe600!important;
}
.top-thumbnail-wrap { width:100%; display:flex; justify-content:center; align-items:center; margin:.2rem 0 .55rem 0; }
.top-thumbnail { width:100%; max-width:760px; max-height:220px; height:auto; object-fit:contain; border-radius:8px; display:block; }
.app-title { display:flex; align-items:center; gap:14px; margin:.6rem 0 .35rem 0; }
.app-title h1 { margin:0; padding:0; font-size:2.75rem; line-height:1.1; font-weight:800; }
.app-logo { width:3.5em; height:3.5em; object-fit:contain; flex:0 0 auto; }
.tournament-meta { font-size:1.2rem; line-height:1.45; color:#f2f2f2; margin:0 0 1.1rem 0; font-weight:700; }
.tournament-meta span { color:#c9d4df; font-weight:650; }
.payout-rules-box { border:1px solid #444; background:#0b0b0b; border-left:5px solid #ffeb3b; border-radius:8px; padding:12px 14px; margin:1.2rem 0; color:#fff; font-size:.98rem; line-height:1.4; }
.payout-rules-label { color:#ffeb3b; font-size:.76rem; font-weight:1000; letter-spacing:.04em; text-transform:uppercase; margin-bottom:5px; }
.compact-card { border-width:3px!important; border-radius:10px!important; padding:12px 14px!important; margin-bottom:1rem!important; box-shadow:0 3px 10px rgba(255,255,255,.06); }
.roster-table { width:100%; border-collapse:collapse; font-size:.82rem; background:#080808; color:#fff; overflow:hidden; border-radius:8px; }
.roster-table th { text-align:left; padding:7px 8px; color:#fff; border-bottom:1px solid rgba(255,255,255,.18); font-weight:800; }
.roster-table td { padding:7px 8px; border-bottom:1px solid rgba(255,255,255,.10); vertical-align:middle; }
.roster-table tr:last-child td { border-bottom:none; }
.roster-top-three td { background:#ffeb3b!important; color:#000!important; font-weight:900; }
.draft-stopped-note { color:#bbb; font-style:italic; margin:.5rem 0 1rem 0; }
.team-heading { display:flex; align-items:center; flex-wrap:wrap; gap:14px; min-width:0; }
.team-heading span { min-width:0; overflow-wrap:anywhere; }
.team-name { font-size:1.2em; font-weight:950; }
.team-face { width:5.6rem; height:5.6rem; border-radius:50%; object-fit:cover; border:4px solid currentColor; flex:0 0 auto; box-shadow:0 0 18px currentColor; }
.team-face-placeholder { width:5.6rem; height:5.6rem; border-radius:50%; border:4px solid currentColor; display:flex; align-items:center; justify-content:center; font-size:.72rem; font-weight:900; line-height:1.05; text-align:center; overflow:hidden; flex:0 0 auto; padding:7px; background:#050505; box-shadow:0 0 18px currentColor; }
.score-badge { display:inline-flex; align-items:center; justify-content:center; width:3.1rem; height:3.1rem; margin-left:auto; border-radius:50%; color:#000; font-size:1.35rem; font-weight:900; line-height:1; flex:0 0 auto; }
.color-chip { display:inline-flex; align-items:center; justify-content:center; width:1.05rem; height:1.05rem; border-radius:50%; border:1px solid rgba(255,255,255,.55); margin-right:.35rem; vertical-align:-.18rem; }
.color-chip.used { opacity:.28; filter:grayscale(.75); }
.current-pick-box { width:100%; display:flex; align-items:center; justify-content:center; gap:.45rem; border:3px solid currentColor; border-radius:8px; padding:12px 14px; margin:.9rem 0; color:#fff; font-size:clamp(1rem, 3.4vw, 1.7rem); font-weight:1000; white-space:nowrap; overflow:hidden; text-align:center; box-shadow:0 0 18px currentColor; }
.current-pick-label { color:#fff; }
.current-pick-coach { color:currentColor; background:#000; border-radius:6px; padding:2px 8px; text-shadow:0 0 8px currentColor; }
.draft-page-nav { display:grid; grid-template-columns:minmax(54px, 1fr) minmax(120px, 2fr) minmax(54px, 1fr); align-items:stretch; gap:0; margin:.65rem 0 1rem; border:2px solid #39ff14; border-radius:8px; overflow:hidden; background:rgba(57,255,20,.08); }
.draft-page-center { display:flex; align-items:center; justify-content:center; min-height:48px; color:#fff; border-left:1px solid rgba(57,255,20,.55); border-right:1px solid rgba(57,255,20,.55); font-weight:950; text-align:center; padding:0 8px; }
.draft-page-side div[data-testid="stButton"] > button { min-height:48px!important; border-radius:0!important; border:0!important; background:rgba(57,255,20,.12)!important; color:#39ff14!important; font-size:1.2rem!important; box-shadow:none!important; }
.draft-page-side div[data-testid="stButton"] > button:disabled { background:#111!important; color:#555!important; }
.golfer-pick-wrap div[data-testid="stButton"] > button { background:rgba(57,255,20,.08)!important; border:2px solid rgba(57,255,20,.75)!important; color:#fff!important; box-shadow:0 0 8px rgba(57,255,20,.22)!important; }
.golfer-pick-wrap div[data-testid="stButton"] > button:hover { background:rgba(57,255,20,.16)!important; border-color:#39ff14!important; }
.draft-table-wrap { overflow-x:auto; width:100%; }
@media (max-width:700px) {
    div[data-testid="column"] { width:100%!important; flex:1 1 100%!important; }
    div[data-testid="stButton"] > button { min-height:54px!important; font-size:.98rem!important; }
    .refresh-button-wrap div[data-testid="stButton"] > button { min-height:58px!important; font-size:1.05rem!important; }
    .top-thumbnail-wrap { margin:.1rem 0 .35rem 0; }
    .top-thumbnail { width:100%; max-width:100%; max-height:24vh; }
    .app-title h1 { font-size:2rem; }
    .tournament-meta { font-size:1.02rem; }
    .team-face, .team-face-placeholder { width:4rem; height:4rem; }
    .current-pick-box { padding:10px 8px; gap:.25rem; }
    .draft-page-center { font-size:.92rem; }
}
</style>
""", unsafe_allow_html=True)

def read_secret(*path):
    try:
        cur = st.secrets
        for key in path:
            if key not in cur:
                return None
            cur = cur[key]
        return cur
    except Exception:
        return None

GITHUB_TOKEN = read_secret("GITHUB", "TOKEN")
REPO_OWNER = "theleitas"
REPO_NAME = "leita-fantasy-golf"
STATE_FILE_PATH = "draft_state.json"
BRANCH = "main"
DEFAULT_APP_TITLE = "DeskCheck Golf Challenge"
DEFAULT_COACHES = ["McClure", "Red", "Marco", "Brax", "CMO", "Handler", "A-Burst", "Lutt", "Jeff"]
MAX_ROUNDS = 10
MAX_PICKS = len(DEFAULT_COACHES) * MAX_ROUNDS
ESPN_LEADERBOARD_BASE_URL = "https://site.web.api.espn.com/apis/site/v2/sports/golf/leaderboard"
ESPN_PGA_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/golf/pga/scoreboard"
AUTO_SCORE_REFRESH_SECONDS = 5 * 60
AVAILABLE_GOLFERS_PAGE_SIZE = 24
DEFAULT_PAYOUT_RULES = (
    "Each coach drafts 10 golfers and antes $50. Coach with lowest 3 golfers at end of tournaments "
    "wins with payouts of $X for 1st, $Y for 2nd, and $Z for 3rd."
)

GITHUB_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

TEAM_COLOR_OPTIONS = [
    ("Neon Green", "#39FF14"),
    ("Electric Cyan", "#00F5FF"),
    ("Hot Magenta", "#FF00FF"),
    ("Laser Yellow", "#FFF700"),
    ("Neon Red", "#FF073A"),
    ("Hyper Blue", "#1F51FF"),
    ("Bubblegum Pink", "#FF6EC7"),
    ("Safety Orange", "#FF5F1F"),
    ("Mint Flash", "#00FF9F"),
    ("Ultra Violet", "#B026FF"),
    ("Acid Lime", "#CCFF00"),
    ("Cyber Teal", "#00FFD5"),
    ("Rave Pink", "#FE019A"),
    ("Volt Purple", "#8F00FF"),
    ("Plasma Coral", "#FF4040"),
    ("Toxic Jade", "#00FF66"),
    ("Electric Lavender", "#D946FF"),
    ("Solar Gold", "#FFD300"),
    ("Ice Blue", "#7DF9FF"),
    ("Neon Peach", "#FF9966"),
]
TEAM_COLOR_BY_HEX = {hex_value: label for label, hex_value in TEAM_COLOR_OPTIONS}

APP_LOGO = "pga-tour.png"
TITLE_THUMBNAIL_PATH = "titlethumb.png"

STATIC_ODDS = {
    "Scottie Scheffler": "+450", "Rory McIlroy": "+800", "Xander Schauffele": "+1400",
    "Jon Rahm": "+1600", "Bryson DeChambeau": "+1800", "Ludvig Aberg": "+2200",
    "Cameron Young": "+2500", "Matt Fitzpatrick": "+2800", "Tommy Fleetwood": "+3000",
    "Justin Thomas": "+3500", "Brooks Koepka": "+4000", "Viktor Hovland": "+4500",
    "Hideki Matsuyama": "+5000", "Collin Morikawa": "+5500", "Patrick Cantlay": "+6000",
    "Jordan Spieth": "+6500", "Russell Henley": "+7000", "Sahith Theegala": "+7500",
    "Min Woo Lee": "+8000", "Shane Lowry": "+9000", "Tyrrell Hatton": "+10000",
    "Corey Conners": "+11000", "Adam Scott": "+12000", "Sepp Straka": "+14000",
    "Sungjae Im": "+15000", "J.T. Poston": "+18000", "Alex Smalley": "+20000",
    "Sam Burns": "+22000", "Jason Day": "+25000", "Rickie Fowler": "+28000",
    "Max Homa": "+30000", "Tony Finau": "+35000", "Justin Rose": "+40000",
}

PGA_PLAYERS = sorted([
    "Ludvig Aberg", "Angel Ayora", "Derek Berg", "Daniel Berger", "Christiaan Bezuidenhout",
    "Akshay Bhatia", "Francisco Bide", "Chandler Blanchet", "Michael Block", "Keegan Bradley",
    "Michael Brennan", "Jacob Bridgeman", "Daniel Brown", "Sam Burns", "Brian Campbell",
    "Patrick Cantlay", "Ricky Castillo", "Bud Cauley", "Stewart Cink", "Wyndham Clark",
    "Tyler Collet", "Corey Conners", "Pierceson Coody", "Jason Day", "Bryson DeChambeau",
    "Thomas Detry", "Luke Donald", "Jesse Droemer", "Jason Dufner", "Nico Echavarria",
    "Harris English", "Bryce Fisher", "Steven Fisk", "Alex Fitzpatrick", "Matt Fitzpatrick",
    "Tommy Fleetwood", "Rickie Fowler", "Ryan Fox", "Chris Gabriele", "Mark Geddes",
    "Ryan Gerard", "Lucas Glover", "Chris Gotterup", "Max Greyserman", "Ben Griffin",
    "Emiliano Grillo", "Jordan Gumberg", "Harry Hall", "Brian Harman", "Padraig Harrington",
    "Tyrrell Hatton", "Zach Haynes", "Russell Henley", "Kazuki Higa", "Garrick Higgo",
    "Joe Highsmith", "Daniel Hillier", "Ryo Hisatsune", "Rico Hoey", "Ian Holt",
    "Max Homa", "Billy Horschel", "Viktor Hovland", "Austin Hurt", "Nicolai Højgaard",
    "Rasmus Højgaard", "Sungjae Im", "Stephan Jaeger", "Casey Jarvis", "Dustin Johnson",
    "Jared Jones", "Kota Kaneko", "Michael Kartrude", "Martin Kaymer", "John Keefer",
    "Ben Kern", "Michael Kim", "Si Woo Kim", "Chris Kirk", "Kurt Kitayama",
    "Jake Knapp", "Brooks Koepka", "Min Woo Lee", "Ryan Lenahan", "Haotong Li",
    "Mikael Lindberg", "David Lipsky", "Shane Lowry", "Robert MacIntyre", "Hideki Matsuyama",
    "Denny McCarthy", "Matt McCarty", "Paul McClure", "Max McGreevy", "Rory McIlroy",
    "Tom McKibbin", "Maverick McNealy", "Shaun Micheel", "Keith Mitchell", "Collin Morikawa",
    "William Mouw", "Rasmus Neergaard-Petersen", "Joaquin Niemann", "Alex Noren", "Andrew Novak",
    "John Parry", "Taylor Pendrith", "Marco Penge", "Ben Polland", "J.T. Poston",
    "Aldrich Potgieter", "David Puig", "Andrew Putnam", "Jon Rahm", "Aaron Rai",
    "Patrick Reed", "Kristoffer Reitan", "Davis Riley", "Patrick Rodgers", "Justin Rose",
    "Adrien Saddier", "Garrett Sapp", "Jayden Schaper", "Xander Schauffele", "Scottie Scheffler",
    "Adam Schenk", "Matti Schmid", "Adam Scott", "Braden Shattuck", "Alex Smalley",
    "Cameron Smith", "Jordan Smith", "Austin Smotherman", "Elvis Smylie", "Travis Smyth",
    "Brandt Snedeker", "J.J. Spaun", "Jordan Spieth", "Sam Stevens", "Sepp Straka",
    "Andy Sullivan", "Nick Taylor", "Sahith Theegala", "Justin Thomas", "Michael Thorbjornsen",
    "Sami Valimaki", "Jhonattan Vegas", "Ryan Vermeer", "Jimmy Walker", "Matt Wallace",
    "Bernd Wiesberger", "Timothy Wiseman", "Gary Woodland", "Y.E. Yang", "Sudarshan Yellamaraju",
    "Cameron Young",
])

PLAYER_FLAGS = {
    "Ludvig Aberg": "🇸🇪", "Angel Ayora": "🇪🇸", "Christiaan Bezuidenhout": "🇿🇦",
    "Francisco Bide": "🇦🇷", "Daniel Brown": "🇬🇧", "Corey Conners": "🇨🇦",
    "Jason Day": "🇦🇺", "Thomas Detry": "🇧🇪", "Luke Donald": "🇬🇧",
    "Nico Echavarria": "🇨🇴", "Alex Fitzpatrick": "🇬🇧", "Matt Fitzpatrick": "🇬🇧",
    "Tommy Fleetwood": "🇬🇧", "Ryan Fox": "🇳🇿", "Emiliano Grillo": "🇦🇷",
    "Harry Hall": "🇬🇧", "Padraig Harrington": "🇮🇪", "Tyrrell Hatton": "🇬🇧",
    "Kazuki Higa": "🇯🇵", "Garrick Higgo": "🇿🇦", "Daniel Hillier": "🇳🇿",
    "Ryo Hisatsune": "🇯🇵", "Rico Hoey": "🇵🇭", "Viktor Hovland": "🇳🇴",
    "Nicolai Højgaard": "🇩🇰", "Rasmus Højgaard": "🇩🇰", "Sungjae Im": "🇰🇷",
    "Stephan Jaeger": "🇩🇪", "Casey Jarvis": "🇿🇦", "Kota Kaneko": "🇯🇵",
    "Martin Kaymer": "🇩🇪", "Si Woo Kim": "🇰🇷", "Min Woo Lee": "🇦🇺",
    "Haotong Li": "🇨🇳", "Mikael Lindberg": "🇸🇪", "Shane Lowry": "🇮🇪",
    "Robert MacIntyre": "🇬🇧", "Hideki Matsuyama": "🇯🇵", "Rory McIlroy": "🇬🇧",
    "Tom McKibbin": "🇬🇧", "Rasmus Neergaard-Petersen": "🇩🇰", "Joaquin Niemann": "🇨🇱",
    "Alex Noren": "🇸🇪", "John Parry": "🇬🇧", "Taylor Pendrith": "🇨🇦",
    "Marco Penge": "🇬🇧", "Aldrich Potgieter": "🇿🇦", "David Puig": "🇪🇸",
    "Jon Rahm": "🇪🇸", "Aaron Rai": "🇬🇧", "Kristoffer Reitan": "🇳🇴",
    "Justin Rose": "🇬🇧", "Adrien Saddier": "🇫🇷", "Jayden Schaper": "🇿🇦",
    "Matti Schmid": "🇩🇪", "Adam Scott": "🇦🇺", "Cameron Smith": "🇦🇺",
    "Jordan Smith": "🇬🇧", "Elvis Smylie": "🇦🇺", "Travis Smyth": "🇦🇺",
    "Sepp Straka": "🇦🇹", "Andy Sullivan": "🇬🇧", "Nick Taylor": "🇨🇦",
    "Sami Valimaki": "🇫🇮", "Jhonattan Vegas": "🇻🇪", "Matt Wallace": "🇬🇧",
    "Bernd Wiesberger": "🇦🇹", "Y.E. Yang": "🇰🇷", "Sudarshan Yellamaraju": "🇨🇦",
}

def coach_photo_filename(coach_id):
    return f"{coach_id}.jpeg"

def default_team_color(index):
    return TEAM_COLOR_OPTIONS[index % len(TEAM_COLOR_OPTIONS)][1]

def default_teams():
    return {
        coach: {
            "team_name": coach,
            "players": [],
            "color": default_team_color(index),
            "image": coach_photo_filename(coach),
        }
        for index, coach in enumerate(DEFAULT_COACHES)
    }

def default_state():
    return {
        "app_title": DEFAULT_APP_TITLE,
        "payout_rules": DEFAULT_PAYOUT_RULES,
        "draft_enabled": False,
        "draft_active": False,
        "draft_order": list(DEFAULT_COACHES),
        "last_pick_started_at": 0,
        "player_results": {},
        "hole_outcomes": {},
        "last_score_refresh_at": 0,
        "last_score_refresh_attempt_at": 0,
        "teams": default_teams(),
        "selected_tournament": {},
    }

def normalize_state(state):
    base = default_state()
    if not isinstance(state, dict):
        return base
    state.setdefault("app_title", base["app_title"])
    state.setdefault("payout_rules", base["payout_rules"])
    if not str(state.get("app_title") or "").strip():
        state["app_title"] = base["app_title"]
    if not str(state.get("payout_rules") or "").strip():
        state["payout_rules"] = base["payout_rules"]
    state.pop("thumbnail", None)
    state.setdefault("draft_enabled", base["draft_enabled"])
    state.setdefault("draft_active", base["draft_active"])
    state.setdefault("draft_order", base["draft_order"])
    state.setdefault("last_pick_started_at", base["last_pick_started_at"])
    state.setdefault("player_results", base["player_results"])
    state.setdefault("hole_outcomes", base["hole_outcomes"])
    state.setdefault("last_score_refresh_at", base["last_score_refresh_at"])
    state.setdefault("last_score_refresh_attempt_at", base["last_score_refresh_attempt_at"])
    state.setdefault("teams", base["teams"])
    state.setdefault("selected_tournament", base["selected_tournament"])
    existing_teams = state.get("teams") if isinstance(state.get("teams"), dict) else {}
    normalized_teams = {}
    used_colors = set()
    for index, coach in enumerate(DEFAULT_COACHES):
        prior = existing_teams.get(coach) if isinstance(existing_teams.get(coach), dict) else {}
        color = str(prior.get("color") or default_team_color(index)).strip()
        if color not in TEAM_COLOR_BY_HEX or color in used_colors:
            color = next(hex_value for _, hex_value in TEAM_COLOR_OPTIONS if hex_value not in used_colors)
        used_colors.add(color)
        players = prior.get("players") if isinstance(prior.get("players"), list) else []
        normalized_teams[coach] = {
            "team_name": str(prior.get("team_name") or coach).strip() or coach,
            "players": [str(player) for player in players],
            "color": color,
            "image": coach_photo_filename(coach),
        }
    state["teams"] = normalized_teams
    valid_coaches = list(DEFAULT_COACHES)
    cleaned_order = [coach for coach in state["draft_order"] if coach in valid_coaches]
    for coach in valid_coaches:
        if coach not in cleaned_order:
            cleaned_order.append(coach)
    state["draft_order"] = cleaned_order[:len(valid_coaches)]
    if not isinstance(state.get("selected_tournament"), dict):
        state["selected_tournament"] = {}
    if not isinstance(state.get("hole_outcomes"), dict):
        state["hole_outcomes"] = {}
    return state

def parse_espn_datetime(value):
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    elif re.search(r"[+-]\d{4}$", text):
        text = text[:-5] + text[-5:-2] + ":" + text[-2:]
    try:
        return datetime.fromisoformat(text)
    except Exception:
        return None

def format_tournament_title(name, start_date_iso):
    raw_name = str(name or "").strip() or "PGA Tournament"
    parsed = parse_espn_datetime(start_date_iso)
    year = parsed.year if parsed else datetime.now(ZoneInfo("America/New_York")).year
    if raw_name.startswith(f"{year} "):
        return raw_name
    return f"{year} {raw_name}"

def format_event_location(event):
    courses = event.get("courses") if isinstance(event, dict) else None
    if not isinstance(courses, list) or not courses:
        return "Location TBA"

    host_course = None
    for course in courses:
        if isinstance(course, dict) and course.get("host"):
            host_course = course
            break
    if host_course is None:
        host_course = courses[0] if isinstance(courses[0], dict) else {}

    course_name = str(host_course.get("name") or "").strip()
    address = host_course.get("address") if isinstance(host_course.get("address"), dict) else {}
    city = str(address.get("city") or "").strip()
    state_or_country = str(address.get("state") or address.get("country") or "").strip()
    city_state = ", ".join(part for part in [city, state_or_country] if part)
    if course_name and city_state:
        return f"{course_name} - {city_state}"
    if course_name:
        return course_name
    if city_state:
        return city_state
    return "Location TBA"

def format_tournament_date_range(start_date_iso, end_date_iso):
    start_dt = parse_espn_datetime(start_date_iso)
    end_dt = parse_espn_datetime(end_date_iso)
    if not start_dt and not end_dt:
        return "Date TBD"
    if start_dt and not end_dt:
        return start_dt.strftime("%b %d, %Y")
    if end_dt and not start_dt:
        return end_dt.strftime("%b %d, %Y")
    start_local = start_dt.astimezone(ZoneInfo("America/New_York"))
    end_local = end_dt.astimezone(ZoneInfo("America/New_York"))
    if start_local.year != end_local.year:
        return f"{start_local.strftime('%b %d, %Y')} - {end_local.strftime('%b %d, %Y')}"
    if start_local.month == end_local.month:
        return f"{start_local.strftime('%b %d')} - {end_local.strftime('%d, %Y')}"
    return f"{start_local.strftime('%b %d')} - {end_local.strftime('%b %d, %Y')}"

@st.cache_data(ttl=300, show_spinner=False)
def fetch_pga_calendar_payload():
    resp = requests.get(ESPN_PGA_SCOREBOARD_URL, timeout=12)
    resp.raise_for_status()
    return resp.json()

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_tournament_metadata(event_id):
    params = {"league": "pga", "event": str(event_id)}
    resp = requests.get(ESPN_LEADERBOARD_BASE_URL, params=params, timeout=12)
    resp.raise_for_status()
    payload = resp.json()
    events = payload.get("events") or []
    if not events:
        raise ValueError("No tournament events returned from ESPN.")

    event = events[0]
    return {
        "event_id": str(event.get("id") or event_id),
        "name": str(event.get("name") or "PGA Tournament"),
        "start_date": event.get("date"),
        "end_date": event.get("endDate"),
        "title": format_tournament_title(event.get("name"), event.get("date")),
        "location": format_event_location(event),
    }

def build_tournament_options(selected_event_id):
    payload = fetch_pga_calendar_payload()
    league = (payload.get("leagues") or [{}])[0]
    calendar = league.get("calendar") or []
    current_events = payload.get("events") or []
    current_event_id = str(current_events[0].get("id")) if current_events else None
    today_et = datetime.now(ZoneInfo("America/New_York")).date()
    horizon_et = today_et + timedelta(days=365)

    normalized = []
    for entry in calendar:
        event_id = str(entry.get("id") or "").strip()
        if not event_id:
            continue
        start_dt = parse_espn_datetime(entry.get("startDate"))
        end_dt = parse_espn_datetime(entry.get("endDate"))
        if end_dt and end_dt.astimezone(ZoneInfo("America/New_York")).date() < today_et:
            continue
        if start_dt and start_dt.astimezone(ZoneInfo("America/New_York")).date() > horizon_et:
            continue
        normalized.append(
            {
                "event_id": event_id,
                "name": str(entry.get("label") or "PGA Tournament"),
                "start_date": entry.get("startDate"),
                "end_date": entry.get("endDate"),
            }
        )

    if not normalized:
        return [], None

    anchor_event_id = str(selected_event_id or "").strip() or current_event_id or normalized[0]["event_id"]
    anchor_index = next((idx for idx, item in enumerate(normalized) if item["event_id"] == anchor_event_id), None)
    if anchor_index is None:
        anchor_index = 0
        anchor_event_id = normalized[0]["event_id"]

    picked = normalized
    options = []
    for item in picked:
        details = {
            "event_id": item["event_id"],
            "name": item["name"],
            "start_date": item["start_date"],
            "end_date": item["end_date"],
            "title": format_tournament_title(item["name"], item["start_date"]),
            "location": "Location TBA",
        }
        try:
            fetched = fetch_tournament_metadata(item["event_id"])
            details.update({k: v for k, v in fetched.items() if v})
            details["title"] = format_tournament_title(details.get("name"), details.get("start_date"))
        except Exception:
            pass
        options.append(details)

    return options, anchor_event_id

def current_tournament_selection(state):
    selected = state.get("selected_tournament") if isinstance(state.get("selected_tournament"), dict) else {}
    selected_event_id = str(selected.get("event_id") or "").strip()

    try:
        options, anchor_event_id = build_tournament_options(selected_event_id)
    except Exception:
        options = []
        anchor_event_id = selected_event_id

    option_lookup = {option["event_id"]: option for option in options}
    chosen_event_id = selected_event_id if selected_event_id in option_lookup else (anchor_event_id if anchor_event_id in option_lookup else "")

    chosen = dict(selected) if isinstance(selected, dict) else {}
    if chosen_event_id and chosen_event_id in option_lookup:
        chosen = dict(option_lookup[chosen_event_id])
    elif options:
        chosen = dict(options[0])

    if chosen and "title" not in chosen:
        chosen["title"] = format_tournament_title(chosen.get("name"), chosen.get("start_date"))

    return chosen, options

def tournament_option_label(option):
    date_text = format_tournament_date_range(option.get("start_date"), option.get("end_date"))
    title = str(option.get("title") or option.get("name") or "PGA Tournament")
    location = str(option.get("location") or "Location TBA")
    return f"{date_text} | {title} | {location}"

def save_selected_tournament(selection):
    chosen = {
        "event_id": str(selection.get("event_id") or "").strip(),
        "name": str(selection.get("name") or "").strip(),
        "start_date": selection.get("start_date"),
        "end_date": selection.get("end_date"),
        "title": str(selection.get("title") or "").strip(),
        "location": str(selection.get("location") or "").strip(),
    }

    def mutator(state):
        state = normalize_state(state)
        state["selected_tournament"] = chosen
        state["player_results"] = {}
        state["hole_outcomes"] = {}
        state["last_score_refresh_at"] = 0
        state["last_score_refresh_attempt_at"] = 0
        return True

    return mutate_shared_state(mutator, "Update selected tournament")

@lru_cache(maxsize=64)
def _image_to_data_uri_cached(path, modified_at):
    mime_type = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"

def image_to_data_uri(path):
    if not path:
        return ""
    try:
        abs_path = os.path.abspath(path)
        modified_at = os.path.getmtime(abs_path)
        return _image_to_data_uri_cached(abs_path, modified_at)
    except OSError:
        return ""

def image_html(path, class_name):
    data_uri = image_to_data_uri(path)
    if not data_uri:
        return ""
    return f"<img class='{class_name}' src='{data_uri}' alt=''>"

def app_logo_html():
    return image_html(APP_LOGO, "app-logo")

def thumbnail_data_uri_for_display():
    return image_to_data_uri(TITLE_THUMBNAIL_PATH)

def top_thumbnail_html():
    data_uri = thumbnail_data_uri_for_display()
    if not data_uri:
        return ""
    safe_data_uri = html.escape(data_uri, quote=True)
    return (
        "<div class='top-thumbnail-wrap'>"
        f"<img class='top-thumbnail' src='{safe_data_uri}' alt='iMessage thumbnail'>"
        "</div>"
    )

def coach_image_html(coach_id, color):
    image_path = coach_photo_filename(coach_id)
    data_uri = image_to_data_uri(image_path)
    if data_uri:
        return f"<img class='team-face' src='{data_uri}' alt=''>"
    safe_filename = html.escape(image_path)
    safe_color = html.escape(color)
    return (
        f"<div class='team-face-placeholder' style='border-color:{safe_color}; color:{safe_color};'>"
        f"{safe_filename}</div>"
    )

def flag_for_player(player):
    return PLAYER_FLAGS.get(player, "🇺🇸")

def display_player_name(player):
    return f"{flag_for_player(player)} {player}"

def last_name_key(player):
    cleaned = player.replace(".", "").replace("'", "")
    parts = cleaned.split()
    return parts[-1].lower() if parts else cleaned.lower()

def normalize_player_match_name(name):
    name = str(name or "").strip()
    replacements = {
        "Å": "A", "å": "a", "Á": "A", "á": "a", "É": "E", "é": "e", "Í": "I", "í": "i",
        "Ó": "O", "ó": "o", "Ú": "U", "ú": "u", "Ø": "O", "ø": "o",
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    name = name.replace("Højgaard", "Hojgaard").replace("Neergaard-Petersen", "Neergaard Petersen")
    name = re.sub(r"[^A-Za-z ]", "", name)
    return re.sub(r"\s+", " ", name).strip().lower()

PLAYER_NAME_LOOKUP = {normalize_player_match_name(player): player for player in PGA_PLAYERS}

def github_file_url():
    return f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{STATE_FILE_PATH}"

def load_state_from_github(show_warning=True):
    if not GITHUB_TOKEN:
        try:
            with open(STATE_FILE_PATH, "r", encoding="utf-8") as state_file:
                return normalize_state(json.load(state_file)), None
        except Exception as e:
            if show_warning:
                st.warning(f"Could not load local {STATE_FILE_PATH}: {e}")
            return default_state(), None

    try:
        resp = requests.get(github_file_url(), headers=GITHUB_HEADERS, timeout=10)
        if resp.status_code == 200:
            payload = resp.json()
            content = base64.b64decode(payload["content"]).decode("utf-8")
            return normalize_state(json.loads(content)), payload["sha"]
        if show_warning:
            st.warning(f"Could not load {STATE_FILE_PATH}. Status code: {resp.status_code}")
    except Exception as e:
        if show_warning:
            st.warning(f"Could not load {STATE_FILE_PATH}: {e}")
    return default_state(), None

def save_state_to_github(state, sha, message_prefix="Update draft state"):
    if not GITHUB_TOKEN:
        try:
            with open(STATE_FILE_PATH, "w", encoding="utf-8") as state_file:
                json.dump(normalize_state(state), state_file, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"Could not save local {STATE_FILE_PATH}: {e}")
            return False

    content_str = json.dumps(normalize_state(state), indent=2, ensure_ascii=False)
    content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
    payload = {
        "message": f"{message_prefix} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "content": content_b64,
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha
    try:
        resp = requests.put(github_file_url(), headers=GITHUB_HEADERS, json=payload, timeout=15)
        return resp.status_code in [200, 201]
    except Exception:
        return False

def mutate_shared_state(mutator, message_prefix):
    for _ in range(3):
        fresh_state, fresh_sha = load_state_from_github(show_warning=False)
        result = mutator(fresh_state)
        if result is False:
            return False, fresh_state
        if save_state_to_github(fresh_state, fresh_sha, message_prefix):
            return result, fresh_state
        time.sleep(0.5)
    st.error("Could not save after retrying. Please try again.")
    return False, None

def extract_competitors(payload):
    competitors = []
    for event in payload.get("events", []):
        for competition in event.get("competitions", []):
            competitors.extend(competition.get("competitors", []))
    return competitors

def extract_athlete_name(competitor):
    athlete = competitor.get("athlete") or competitor.get("player") or {}
    return (
        athlete.get("displayName")
        or athlete.get("fullName")
        or competitor.get("displayName")
        or competitor.get("name")
        or ""
    )

def get_status_state(competitor):
    status = competitor.get("status")
    if isinstance(status, dict):
        stype = status.get("type")
        if isinstance(stype, dict):
            state_val = stype.get("state")
            if state_val:
                return str(state_val).lower()
    return ""

def looks_like_topar(value):
    """True if the string looks like a to-par value (E, -3, +1) rather than a stroke total."""
    if value is None:
        return False
    text = str(value).strip().upper().replace("−", "-")
    if text in ("E", "EVEN"):
        return True
    if re.fullmatch(r"[+-]\d{1,2}", text):
        return True
    # bare digits like "212" or "0" are NOT to-par (those are stroke totals or pre-round zeros)
    return False

def extract_score_value(competitor):
    """
    Walk ESPN's leaderboard structure to find the to-par value.
    Order of preference: statistics[scoreToPar] -> linescores cumulative -> score field -> displayValue.
    Never return a bare "0" — that's almost always a pre-round placeholder, not even-par.
    """
    state_val = get_status_state(competitor)

    # 1. statistics array (some endpoints)
    stats = competitor.get("statistics") or []
    if isinstance(stats, list):
        for stat in stats:
            if not isinstance(stat, dict):
                continue
            name = (stat.get("name") or stat.get("abbreviation") or "").lower()
            if name in ("scoretopar", "topar", "toparscore", "totaltopar"):
                val = stat.get("displayValue") or stat.get("value")
                if val not in (None, "") and looks_like_topar(val):
                    return val

    # 2. linescores: look for a cumulative to-par
    linescores = competitor.get("linescores")
    if isinstance(linescores, list):
        for ls in linescores:
            if not isinstance(ls, dict):
                continue
            for key in ("currentScore", "cumulativeScore", "toParCumulative"):
                v = ls.get(key)
                if isinstance(v, dict):
                    dv = v.get("displayValue")
                    if dv and looks_like_topar(dv):
                        return dv
                elif looks_like_topar(v):
                    return v

    # 3. competitor-level score field — dict form
    score = competitor.get("score")
    if isinstance(score, dict):
        dv = score.get("displayValue")
        if dv and looks_like_topar(dv):
            return dv
    elif isinstance(score, str):
        if looks_like_topar(score):
            return score
        # If it's "0" and the player hasn't started, treat as N/A — not even.
        if score.strip() == "0" and state_val in ("pre", "", "scheduled"):
            return "N/A"
        # If it's "0" and player IS in/post, ESPN sometimes literally returns "0" meaning even
        if score.strip() == "0" and state_val in ("in", "post"):
            return "E"

    # 4. competitor displayValue
    dv = competitor.get("displayValue")
    if dv and looks_like_topar(dv):
        return dv

    return "N/A"

def clean_status_text(value):
    if value is None:
        return ""
    value = str(value).strip()
    if not value or value.lower() in ["none", "null", "n/a"]:
        return ""
    return value

def format_tee_time(value):
    value = clean_status_text(value)
    if not value:
        return ""

    iso_match = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?", value)
    if iso_match:
        raw = iso_match.group(0)
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        elif re.search(r"[+-]\d{4}$", raw):
            raw = raw[:-5] + raw[-5:-2] + ":" + raw[-2:]
        try:
            parsed = datetime.fromisoformat(raw)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=ZoneInfo("UTC"))
            parsed = parsed.astimezone(ZoneInfo("America/New_York"))
            return parsed.strftime("%I:%M %p").lstrip("0")
        except Exception:
            pass

    for fmt in ["%I:%M %p", "%I:%M%p", "%H:%M"]:
        try:
            parsed = datetime.strptime(value.upper(), fmt)
            return parsed.strftime("%I:%M %p").lstrip("0")
        except Exception:
            pass

    short_time = re.search(r"\b(\d{1,2}:\d{2})\s*([AP]M)?\b", value.upper())
    if short_time:
        if short_time.group(2):
            return f"{short_time.group(1)} {short_time.group(2)}"
        try:
            parsed = datetime.strptime(short_time.group(1), "%H:%M")
            return parsed.strftime("%I:%M %p").lstrip("0")
        except Exception:
            return short_time.group(1)

    return value

def display_hole_value(value):
    value = clean_status_text(value)
    if not value:
        return "—"
    if strip_thru_prefix(value).upper() in ["CUT", "MC", "MISSED CUT"]:
        return "MC"
    if strip_thru_prefix(value).upper() in ["F", "FINAL"]:
        return "Final"
    if re.search(r"\d{4}-\d{2}-\d{2}T", value) or re.search(r"\d{1,2}:\d{2}", value):
        return format_tee_time(value)
    return value

def strip_thru_prefix(value):
    """Remove a leading 'Thru ' so we don't double-label in the standings card."""
    if not value:
        return value
    return re.sub(r"^\s*thru\s+", "", str(value), flags=re.IGNORECASE).strip()

def is_finished_round_value(value):
    value = strip_thru_prefix(clean_status_text(value)).upper()
    if value in ["F", "FINAL"]:
        return True
    try:
        return int(value) >= 18
    except ValueError:
        return False

def is_missed_cut(competitor):
    status = competitor.get("status")
    if not isinstance(status, dict):
        return False

    status_type = status.get("type")
    status_words = " ".join(
        str(status.get(key, ""))
        for key in ["displayValue", "detail", "shortDetail", "description"]
    )
    position = status.get("position")
    if isinstance(position, dict):
        status_words += f" {position.get('displayName', '')}"

    if isinstance(status_type, dict):
        status_words += " " + " ".join(
            str(status_type.get(key, ""))
            for key in ["name", "description", "detail", "shortDetail"]
        )

    return bool(re.search(r"\b(cut|missed cut|mc|status_cut)\b", status_words, flags=re.IGNORECASE))

def is_finished_round(competitor):
    status = competitor.get("status")
    if isinstance(status, dict):
        status_type = status.get("type")
        if isinstance(status_type, dict):
            if status_type.get("completed") is True:
                return True
            if str(status_type.get("state", "")).lower() in ["post", "final"]:
                return True
            status_words = " ".join(
                str(status_type.get(key, ""))
                for key in ["name", "description", "detail", "shortDetail"]
            )
            if re.search(r"\b(final|complete|completed)\b", status_words, flags=re.IGNORECASE):
                return True

        status_words = " ".join(
            str(status.get(key, ""))
            for key in ["displayValue", "detail", "shortDetail", "description"]
        )
        if re.search(r"\b(final|complete|completed)\b", status_words, flags=re.IGNORECASE):
            return True

        for key in ["thru", "thruStatus"]:
            if is_finished_round_value(status.get(key)):
                return True

    linescores = competitor.get("linescores")
    if isinstance(linescores, list) and linescores:
        latest = linescores[-1]
        if isinstance(latest, dict):
            for key in ["thru", "thruStatus"]:
                if is_finished_round_value(latest.get(key)):
                    return True

    return False

def extract_hole_or_tee_time(competitor):
    if is_missed_cut(competitor):
        return "MC"

    if is_finished_round(competitor):
        return "F"

    tee_time_keys = ["teeTime", "teeTimeDisplay", "startTime", "displayTime"]

    for key in tee_time_keys:
        value = clean_status_text(competitor.get(key))
        if value:
            return format_tee_time(value)

    # Check status first — if the golfer is finished, return "F"
    state_val = get_status_state(competitor)
    if state_val == "post":
        return "F"

    play_status_keys = ["thru", "thruStatus", "currentHole", "currentHoleNumber", "hole"]

    for key in play_status_keys:
        value = clean_status_text(competitor.get(key))
        if value:
            return display_hole_value(value)

    status = competitor.get("status")
    if isinstance(status, dict):
        if get_status_state(competitor) not in ["", "pre", "scheduled"]:
            for key in play_status_keys:
                value = clean_status_text(status.get(key))
                if value and value not in ["--", "0"]:
                    return display_hole_value(value)

        for key in ["displayValue", "detail", "shortDetail", "description"]:
            value = clean_status_text(status.get(key))
            if value:
                return display_hole_value(value)

        status_type = status.get("type")
        if isinstance(status_type, dict):
            for key in ["detail", "shortDetail", "description", "name"]:
                value = clean_status_text(status_type.get(key))
                if value:
                    return display_hole_value(value)

    linescores = competitor.get("linescores")
    if isinstance(linescores, list) and linescores:
        latest = linescores[-1]
        if isinstance(latest, dict):
            for key in ["thru", "thruStatus", "currentHole", "displayValue", "value"]:
                value = clean_status_text(latest.get(key))
                if value and value not in ["--"]:
                    return display_hole_value(value)

    return "—"

def extract_player_profile_url(competitor):
    athlete = competitor.get("athlete") if isinstance(competitor.get("athlete"), dict) else {}
    links = athlete.get("links")
    if isinstance(links, list):
        for link in links:
            if not isinstance(link, dict):
                continue
            href = str(link.get("href") or "").strip()
            if href and ("player/_/id/" in href or "playercard" in " ".join(link.get("rel", []))):
                return href

    athlete_id = str(athlete.get("id") or "").strip()
    if athlete_id:
        return f"https://www.espn.com/golf/player/_/id/{athlete_id}"
    return ""

def fetch_live_scores_from_espn(event_id=""):
    params = {"league": "pga"}
    if event_id:
        params["event"] = str(event_id)
    resp = requests.get(ESPN_LEADERBOARD_BASE_URL, params=params, timeout=12)
    resp.raise_for_status()
    payload = resp.json()

    results = {}
    for competitor in extract_competitors(payload):
        raw_name = extract_athlete_name(competitor)
        matched_name = PLAYER_NAME_LOOKUP.get(normalize_player_match_name(raw_name)) or str(raw_name or "").strip()
        if not matched_name:
            continue

        score = str(extract_score_value(competitor)).strip()
        if score in ["", "--", "-"]:
            score = "N/A"

        hole_or_tee = extract_hole_or_tee_time(competitor)
        profile_url = extract_player_profile_url(competitor)

        results[matched_name] = {
            "score": score,
            "hole": hole_or_tee,
            "profile_url": profile_url,
            "competitor_id": str(competitor.get("id") or ""),
        }

    return results

@st.cache_data(ttl=900, show_spinner=False)
def fetch_tournament_field(event_id=""):
    if not event_id:
        return []
    params = {"league": "pga", "event": str(event_id)}
    resp = requests.get(ESPN_LEADERBOARD_BASE_URL, params=params, timeout=12)
    resp.raise_for_status()
    payload = resp.json()
    players = []
    seen = set()
    for competitor in extract_competitors(payload):
        raw_name = extract_athlete_name(competitor)
        player = PLAYER_NAME_LOOKUP.get(normalize_player_match_name(raw_name)) or str(raw_name or "").strip()
        if not player or player in seen:
            continue
        seen.add(player)
        players.append(player)
    players.sort(key=lambda player: (last_name_key(player), player.lower()))
    return players

def get_draft_player_pool(tournament):
    event_id = str((tournament or {}).get("event_id") or "").strip()
    if event_id:
        try:
            field_players = fetch_tournament_field(event_id)
            if field_players:
                return field_players, f"Draft field loaded from ESPN for {tournament.get('title') or 'the selected tournament'}."
        except Exception:
            pass
    return list(PGA_PLAYERS), "Tournament field is not available from ESPN yet, so the draft list is using the saved PGA player pool."

@st.cache_data(ttl=120, show_spinner=False)
def fetch_competitor_summary(event_id, competitor_id, league="pga"):
    if not event_id or not competitor_id:
        return {}
    url = (
        f"https://site.web.api.espn.com/apis/site/v2/sports/golf/{league}/leaderboard/"
        f"{event_id}/competitorsummary/{competitor_id}"
    )
    resp = requests.get(url, timeout=12)
    resp.raise_for_status()
    return resp.json()

@st.cache_data(ttl=120, show_spinner=False)
def fetch_event_competitor_lookup(event_id, league="pga"):
    if not event_id:
        return {}
    params = {"league": league, "event": str(event_id)}
    resp = requests.get(ESPN_LEADERBOARD_BASE_URL, params=params, timeout=12)
    resp.raise_for_status()
    payload = resp.json()
    lookup = {}
    for competitor in extract_competitors(payload):
        raw_name = extract_athlete_name(competitor)
        matched_name = PLAYER_NAME_LOOKUP.get(normalize_player_match_name(raw_name))
        competitor_id = str(competitor.get("id") or "").strip()
        if matched_name and competitor_id:
            lookup[matched_name] = competitor_id
    return lookup

def marker_for_hole_scoretype(linescore):
    score_type = linescore.get("scoreType") if isinstance(linescore.get("scoreType"), dict) else {}
    score_name = str(score_type.get("name") or "").upper()
    if "PAR" in score_name:
        return "P"
    if any(key in score_name for key in ["BIRDIE", "EAGLE", "ALBATROSS"]):
        return "○"
    if "BOGEY" in score_name:
        return "□"

    value = linescore.get("value")
    par = linescore.get("par")
    try:
        value_num = float(value)
        par_num = float(par)
        if value_num < par_num:
            return "○"
        if value_num > par_num:
            return "□"
        return "P"
    except (TypeError, ValueError):
        pass

    display_delta = str(score_type.get("displayValue") or "").strip()
    if display_delta.startswith("-"):
        return "○"
    if display_delta.startswith("+"):
        return "□"
    return "P"

def extract_recent_hole_outcomes_from_summary(summary):
    rounds = summary.get("rounds") if isinstance(summary, dict) else []
    if not isinstance(rounds, list) or not rounds:
        return []

    latest_round = None
    for candidate in reversed(rounds):
        if not isinstance(candidate, dict):
            continue
        linescores = candidate.get("linescores")
        if isinstance(linescores, list) and linescores:
            latest_round = candidate
            break

    if not latest_round:
        return []

    linescores = latest_round.get("linescores")
    markers = [marker_for_hole_scoretype(linescore) for linescore in linescores if isinstance(linescore, dict)]
    markers = [marker for marker in markers if marker in {"P", "○", "□"}]
    return markers[-5:]

def get_recent_outcomes_for_standings(player_name, result):
    fallback = result.get("recent_outcomes", []) if isinstance(result, dict) else []
    event_id = str(SELECTED_TOURNAMENT.get("event_id") or "").strip()
    competitor_id = str((result or {}).get("competitor_id") or "").strip()
    if not competitor_id and event_id and player_name:
        try:
            competitor_id = str(fetch_event_competitor_lookup(event_id, league="pga").get(player_name) or "").strip()
        except Exception:
            competitor_id = ""
    if not event_id or not competitor_id:
        return fallback
    try:
        summary = fetch_competitor_summary(event_id, competitor_id, league="pga")
        outcomes = extract_recent_hole_outcomes_from_summary(summary)
        return outcomes or fallback
    except Exception:
        return fallback

def coach_short_name(coach_id):
    return str(coach_id).split()[0]

def is_tee_time_status(value):
    text = display_hole_value(value).upper()
    return "AM" in text or "PM" in text

def hole_number_from_status(value):
    text = strip_thru_prefix(display_hole_value(value)).upper()
    if text in ["MC", "CUT", "MISSED CUT", "F", "FINAL", "—", "N/A", ""]:
        return None
    match = re.search(r"\d+", text)
    if not match:
        return None
    try:
        return int(match.group(0))
    except ValueError:
        return None

def is_final_hole_status(value):
    return strip_thru_prefix(display_hole_value(value)).upper() in ["F", "FINAL"]

def outcome_marker_for_delta(score_delta):
    if score_delta < 0:
        return "○"
    if score_delta > 0:
        return "□"
    return "P"

def derive_hole_outcome_markers(old_result, new_result):
    old_result = old_result if isinstance(old_result, dict) else {}
    new_result = new_result if isinstance(new_result, dict) else {}

    old_score = parse_golf_score(old_result.get("score"))
    new_score = parse_golf_score(new_result.get("score"))
    if old_score is None or new_score is None:
        return []

    old_hole_num = hole_number_from_status(old_result.get("hole"))
    new_hole_num = hole_number_from_status(new_result.get("hole"))

    holes_advanced = 0
    if old_hole_num is not None and new_hole_num is not None and new_hole_num > old_hole_num:
        holes_advanced = new_hole_num - old_hole_num
    elif old_hole_num is not None and is_final_hole_status(new_result.get("hole")):
        holes_advanced = max(0, 18 - old_hole_num)

    if holes_advanced <= 0:
        return []

    score_delta = new_score - old_score
    if holes_advanced == 1:
        return [outcome_marker_for_delta(score_delta)]

    # If multiple holes advanced between refreshes, spread the net delta over those holes:
    # treat remaining holes as pars.
    markers = []
    if score_delta < 0:
        birdies = min(-score_delta, holes_advanced)
        markers.extend(["P"] * (holes_advanced - birdies))
        markers.extend(["○"] * birdies)
    elif score_delta > 0:
        bogeys = min(score_delta, holes_advanced)
        markers.extend(["P"] * (holes_advanced - bogeys))
        markers.extend(["□"] * bogeys)
    else:
        markers.extend(["P"] * holes_advanced)
    return markers

def update_hole_outcomes(existing_outcomes, old_results, new_results):
    existing_outcomes = existing_outcomes if isinstance(existing_outcomes, dict) else {}
    old_results = old_results if isinstance(old_results, dict) else {}
    new_results = new_results if isinstance(new_results, dict) else {}

    updated = {}
    for player, prior in existing_outcomes.items():
        if isinstance(prior, list):
            updated[player] = [str(item) for item in prior if str(item) in {"P", "○", "□"}][-5:]

    for player, new_result in new_results.items():
        markers = derive_hole_outcome_markers(old_results.get(player, {}), new_result)
        if not markers:
            if player not in updated:
                updated[player] = []
            continue
        history = list(updated.get(player, []))
        history.extend(markers)
        updated[player] = history[-5:]
    return updated

def format_recent_hole_outcomes(outcomes):
    if not isinstance(outcomes, list) or not outcomes:
        return ""
    safe = [html.escape(str(item)) for item in outcomes if str(item) in {"P", "○", "□"}]
    if not safe:
        return ""
    return f" ({' '.join(safe)})"

def should_show_recent_hole_outcomes(result):
    # Only show the last-5 markers when the golfer is actively playing today's round.
    hole_value = (result or {}).get("hole", "—")
    return hole_number_from_status(hole_value) is not None

def get_team_top_three_from_results(players, results):
    scored_players = []
    for draft_index, player in enumerate(players):
        score_value = parse_golf_score(results.get(player, {}).get("score"))
        if score_value is None:
            continue
        scored_players.append((score_value, draft_index, player))
    scored_players.sort(key=lambda item: (item[0], item[1]))
    return [player for _, _, player in scored_players[:3]]

def get_team_total_from_results(players, results):
    scored_players = []
    for draft_index, player in enumerate(players):
        score_value = parse_golf_score(results.get(player, {}).get("score"))
        if score_value is None:
            continue
        scored_players.append((score_value, draft_index, player))
    scored_players.sort(key=lambda item: (item[0], item[1]))
    top_three = scored_players[:3]
    if not top_three:
        return "N/A"
    total = sum(score_value for score_value, _, _ in top_three)
    return format_golf_score(total)

def get_leader_names_from_results(state, results):
    totals = []
    for coach_id, info in state.get("teams", {}).items():
        team_total = get_team_total_from_results(info.get("players", []), results)
        team_total_value = parse_golf_score(team_total)
        if team_total_value is None:
            continue
        totals.append((team_total_value, coach_id))
    if not totals:
        return []
    best_total = min(total for total, _ in totals)
    leaders = [coach_id for total, coach_id in totals if total == best_total]
    leaders.sort()
    return leaders

def format_all_team_totals_from_results(state, results):
    parts = []
    for coach_id, info in state.get("teams", {}).items():
        total = get_team_total_from_results(info.get("players", []), results)
        parts.append(f"{coach_short_name(coach_id)} {total}")
    return " | ".join(parts)

def latest_score_refresh_marker(state):
    try:
        refreshed_at = float(state.get("last_score_refresh_at", 0) or 0)
    except (TypeError, ValueError):
        refreshed_at = 0
    try:
        attempted_at = float(state.get("last_score_refresh_attempt_at", 0) or 0)
    except (TypeError, ValueError):
        attempted_at = 0
    return max(refreshed_at, attempted_at)

def should_auto_refresh_scores(state):
    return time.time() - latest_score_refresh_marker(state) >= AUTO_SCORE_REFRESH_SECONDS

def claim_auto_score_refresh():
    now = time.time()

    def mutator(state):
        if now - latest_score_refresh_marker(state) < AUTO_SCORE_REFRESH_SECONDS:
            return False
        state["last_score_refresh_attempt_at"] = now
        return True

    result, _ = mutate_shared_state(mutator, "Mark score refresh attempt")
    return bool(result)

def auto_refresh_scores_if_needed(state):
    if should_auto_refresh_scores(state) and claim_auto_score_refresh():
        refresh_scores(show_status=False)

def refresh_scores(show_status=True):
    event_id = str(SELECTED_TOURNAMENT.get("event_id") or "").strip()
    try:
        live_results = fetch_live_scores_from_espn(event_id=event_id)
    except Exception as e:
        if show_status:
            st.error(f"Could not refresh scores from ESPN: {e}")
        return False

    if not live_results:
        if show_status:
            st.error("ESPN did not return matching player scores yet.")
        return False

    def mutator(state):
        now = time.time()
        old_results = state.get("player_results", {})
        old_outcomes = state.get("hole_outcomes", {})
        state["hole_outcomes"] = update_hole_outcomes(old_outcomes, old_results, live_results)
        state["player_results"] = live_results
        state["last_score_refresh_at"] = now
        state["last_score_refresh_attempt_at"] = now
        return True

    result, _ = mutate_shared_state(mutator, "Refresh scores")
    if result:
        if show_status:
            st.success(f"Scores refreshed for {len(live_results)} golfers.")
        time.sleep(0.5)
        st.rerun()
    return bool(result)

def format_last_score_refresh_time(state):
    try:
        refreshed_at = float(state.get("last_score_refresh_at", 0) or 0)
    except (TypeError, ValueError):
        refreshed_at = 0
    if not refreshed_at:
        return "--:--"
    return datetime.fromtimestamp(refreshed_at, ZoneInfo("America/New_York")).strftime("%H:%M")

def render_refresh_scores_button(key, state):
    button_label = f"Refresh Scores (Last Update: {format_last_score_refresh_time(state)})"
    st.markdown("<div class='refresh-button-wrap'>", unsafe_allow_html=True)
    clicked = st.button(button_label, key=key, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    if clicked:
        refresh_scores()

def leaderboard_owner_image_html(golfer, owner_lookup):
    coach_id = owner_lookup.get(golfer)
    if not coach_id:
        return ""
    image_path = coach_photo_filename(coach_id)
    data_uri = image_to_data_uri(image_path) if image_path else ""
    color = teams_data.get(coach_id, {}).get("color", "#555555")
    if not data_uri:
        safe_filename = html.escape(image_path)
        return (
            f"<div title='{safe_filename}' style='width:2rem; height:2rem; border-radius:50%; "
            f"border:2px solid {color}; color:{color}; display:flex; align-items:center; "
            f"justify-content:center; font-size:.45rem; line-height:1; text-align:center; overflow:hidden;'>"
            f"{safe_filename}</div>"
        )
    safe_coach = html.escape(coach_id)
    return (
        f"<img src='{data_uri}' alt='{safe_coach}' title='{safe_coach}' "
        f"style='width:2rem; height:2rem; border-radius:50%; object-fit:cover; "
        f"border:2px solid {color}; display:block;'>"
    )

def leaderboard_golfer_with_info_html(player, result):
    safe_player = html.escape(display_player_name(player))
    profile_url = str((result or {}).get("profile_url") or "").strip()
    if not profile_url:
        return safe_player
    safe_url = html.escape(profile_url, quote=True)
    return (
        f"{safe_player} "
        f"<a href='{safe_url}' target='_blank' rel='noopener noreferrer' "
        f"title='Player info' aria-label='Player info' "
        f"style='color:#fff; text-decoration:none; font-style:normal; font-weight:700;'>ⓘ</a>"
    )

def render_tournament_leaderboard(tournament):
    leaderboard_rows = get_tournament_leaderboard(20)
    owner_lookup = {}
    for coach_id, info in teams_data.items():
        for golfer in info.get("players", []):
            owner_lookup[golfer] = coach_id
    tournament_title = html.escape(str(tournament.get("title") or "PGA Tournament"))
    tournament_location = html.escape(str(tournament.get("location") or "Location TBA"))
    leaderboard_parts = [
        "<div style='border:5px solid #fff; background-color:rgba(255,255,255,.06); border-radius:16px; padding:20px 24px; margin-bottom:1.8rem;'>",
        f"<div class='team-heading' style='color:#fff; font-size:1.75rem; font-weight:800; margin-bottom:6px;'>"
        f"{app_logo_html()}<span>{tournament_title}</span></div>",
        f"<div style='color:#bbb; font-size:1rem; font-style:italic; margin-bottom:18px;'>{tournament_location}</div>",
    ]

    if not leaderboard_rows:
        leaderboard_parts.append("<div style='color:#aaa; font-style:italic;'>No live scores yet</div>")
    else:
        leaderboard_parts.append("<table class='roster-table'><thead><tr><th>Rank</th><th>Owner</th><th>Golfer</th><th>Score</th><th>Hole</th></tr></thead><tbody>")
        for rank, (score_value, _, player, result) in enumerate(leaderboard_rows, start=1):
            owner_html = leaderboard_owner_image_html(player, owner_lookup)
            golfer_cell = leaderboard_golfer_with_info_html(player, result)
            score = html.escape(format_golf_score(score_value))
            hole = html.escape(format_hole_status_for_card(result.get("hole", "—")))
            leaderboard_parts.append(f"<tr><td>{rank}</td><td>{owner_html}</td><td>{golfer_cell}</td><td>{score}</td><td>{hole}</td></tr>")
        leaderboard_parts.append("</tbody></table>")

    leaderboard_parts.append("</div>")
    st.markdown("".join(leaderboard_parts), unsafe_allow_html=True)

def get_coach_for_pick(pick_num, order):
    team_count = len(order)
    if team_count == 0:
        return ""
    round_idx = (pick_num - 1) // team_count
    pos = (pick_num - 1) % team_count
    return order[pos] if round_idx % 2 == 0 else order[team_count - 1 - pos]

def derive_picks_from_state(state):
    picks = []
    teams = state["teams"]
    draft_order = state["draft_order"]
    coach_pick_counts = {coach: 0 for coach in draft_order}
    for pick_num in range(1, MAX_PICKS + 1):
        coach = get_coach_for_pick(pick_num, draft_order)
        coach_players = teams.get(coach, {}).get("players", [])
        player_idx = coach_pick_counts[coach]
        if player_idx >= len(coach_players):
            break
        picks.append((pick_num, coach, coach_players[player_idx]))
        coach_pick_counts[coach] += 1
    return picks

def get_current_pick(state):
    return min(len(derive_picks_from_state(state)) + 1, MAX_PICKS + 1)

def get_picked_golfers(state):
    picked = set()
    for info in state["teams"].values():
        picked.update(info.get("players", []))
    return picked

def reset_rosters_in_state(state):
    for coach, info in state["teams"].items():
        info["players"] = []
    state["draft_active"] = False
    state["draft_enabled"] = False
    state["last_pick_started_at"] = 0
    return True

def make_draft_pick(golfer):
    def mutator(state):
        state = normalize_state(state)
        current_pick = get_current_pick(state)
        if not state["draft_enabled"]:
            st.warning("The draft is disabled.")
            return False
        if not state["draft_active"]:
            st.warning("Start the draft before making a pick.")
            return False
        if current_pick > MAX_PICKS:
            state["draft_active"] = False
            state["draft_enabled"] = False
            st.warning("The draft is complete.")
            return False
        if golfer in get_picked_golfers(state):
            st.warning(f"{display_player_name(golfer)} has already been drafted.")
            return False
        coach = get_coach_for_pick(current_pick, state["draft_order"])
        state["teams"][coach]["players"].append(golfer)
        next_pick = get_current_pick(state)
        state["last_pick_started_at"] = time.time()
        if next_pick > MAX_PICKS:
            state["draft_active"] = False
            state["draft_enabled"] = False
        return True
    return mutate_shared_state(mutator, "Draft pick")

def undo_last_pick():
    def mutator(state):
        picks = derive_picks_from_state(state)
        if not picks:
            st.warning("There are no picks to undo.")
            return False
        pick_num, coach, golfer = picks[-1]
        players = state["teams"][coach]["players"]
        if players and players[-1] == golfer:
            players.pop()
        elif golfer in players:
            players.remove(golfer)
        else:
            st.error("Could not find the last picked golfer in the roster.")
            return False
        state["draft_enabled"] = True
        state["draft_active"] = True
        state["last_pick_started_at"] = time.time()
        return pick_num, coach, golfer
    return mutate_shared_state(mutator, "Undo last pick")

def set_draft_enabled(enabled):
    def mutator(state):
        state = normalize_state(state)
        state["draft_enabled"] = enabled
        if not enabled:
            state["draft_active"] = False
        return True
    return mutate_shared_state(mutator, "Set draft enabled")

def start_draft():
    def mutator(state):
        if get_current_pick(state) > MAX_PICKS:
            state["draft_enabled"] = False
            state["draft_active"] = False
            st.warning("The draft is already complete.")
            return False
        state["draft_enabled"] = True
        state["draft_active"] = True
        state["last_pick_started_at"] = time.time()
        return True
    return mutate_shared_state(mutator, "Start draft")

def stop_draft():
    def mutator(state):
        state["draft_active"] = False
        return True
    return mutate_shared_state(mutator, "Stop draft")

def finish_draft(reason="Complete draft"):
    def mutator(state):
        state = normalize_state(state)
        state["draft_active"] = False
        state["draft_enabled"] = False
        return True
    return mutate_shared_state(mutator, reason)

def save_draft_order(new_order):
    def mutator(state):
        if state["draft_enabled"]:
            st.warning("Disable the draft before changing the draft order.")
            return False
        if len(set(new_order)) != len(new_order):
            st.warning("Each draft slot must have a different coach.")
            return False
        state["draft_order"] = new_order
        return True
    return mutate_shared_state(mutator, "Update draft order")

def save_app_settings(app_title, payout_rules):
    def mutator(state):
        state = normalize_state(state)
        state["app_title"] = str(app_title or "").strip() or DEFAULT_APP_TITLE
        state["payout_rules"] = str(payout_rules or "").strip() or DEFAULT_PAYOUT_RULES
        return True
    return mutate_shared_state(mutator, "Update app settings")

def save_team_settings(new_teams):
    def mutator(state):
        state = normalize_state(state)
        chosen_colors = [settings.get("color") for settings in new_teams.values()]
        if len(chosen_colors) != len(set(chosen_colors)):
            st.warning("Each coach must have a different color.")
            return False
        for coach, settings in new_teams.items():
            if coach in state["teams"]:
                state["teams"][coach]["team_name"] = str(settings.get("team_name") or coach).strip() or coach
                color = str(settings.get("color") or state["teams"][coach].get("color") or "").strip()
                if color in TEAM_COLOR_BY_HEX:
                    state["teams"][coach]["color"] = color
                state["teams"][coach]["image"] = coach_photo_filename(coach)
        return True
    return mutate_shared_state(mutator, "Update team settings")

def get_player_result(player):
    result = PLAYER_RESULTS_DISPLAY.get(player, {"score": "N/A", "hole": "—", "recent_outcomes": [], "competitor_id": ""})
    return {
        "score": result.get("score", "N/A"),
        "hole": result.get("hole", "—"),
        "recent_outcomes": result.get("recent_outcomes", []),
        "competitor_id": result.get("competitor_id", ""),
    }

def format_hole_status_for_card(value):
    raw_hole = display_hole_value(value)
    hole_text = strip_thru_prefix(raw_hole)
    is_tee = "AM" in raw_hole.upper() or "PM" in raw_hole.upper()
    if hole_text.upper() in ["CUT", "MC", "MISSED CUT"]:
        return "MC"
    if hole_text.upper() in ["F", "FINAL"]:
        return "Final"
    if is_tee:
        return hole_text
    return f"Thru {hole_text}"

def parse_golf_score(score):
    if score is None:
        return None
    score_text = str(score).strip().upper().replace("−", "-")
    if score_text in ["", "N/A", "—", "-", "WD", "CUT", "DQ"]:
        return None
    if score_text in ["E", "EVEN"]:
        return 0
    # Guard against stroke totals leaking through (any bare unsigned integer)
    if re.fullmatch(r"\d{2,3}", score_text):
        return None
    try:
        return int(score_text.replace("+", ""))
    except ValueError:
        return None

def format_golf_score(score_value):
    if score_value is None:
        return "N/A"
    if score_value == 0:
        return "E"
    if score_value > 0:
        return f"+{score_value}"
    return str(score_value)

def get_sorted_scored_players(players):
    scored_players = []
    for draft_index, player in enumerate(players):
        result = get_player_result(player)
        score_value = parse_golf_score(result.get("score"))
        if score_value is not None:
            scored_players.append((score_value, draft_index, player, result))
    scored_players.sort(key=lambda item: (item[0], item[1]))
    return scored_players

def get_tournament_leaderboard(limit=10):
    leaderboard = []
    for player, result in PLAYER_RESULTS.items():
        score_value = parse_golf_score(result.get("score"))
        if score_value is None:
            continue
        leaderboard.append((score_value, last_name_key(player), player, result))
    leaderboard.sort(key=lambda item: (item[0], item[1], item[2].lower()))
    return leaderboard[:limit]

def get_top_three_lowest_score_players(players):
    return {player for _, _, player, _ in get_sorted_scored_players(players)[:3]}

def get_team_total(players):
    top_three = get_sorted_scored_players(players)[:3]
    if not top_three:
        return "N/A"
    total = sum(score_value for score_value, _, _, _ in top_three)
    return format_golf_score(total)

def sorted_coach_ids_by_total(coach_ids, team_render_data):
    indexed = {coach_id: index for index, coach_id in enumerate(coach_ids)}

    def sort_key(coach_id):
        total_value = parse_golf_score(team_render_data.get(coach_id, {}).get("top_three_total"))
        if total_value is None:
            return (1, 0, indexed.get(coach_id, 999))
        return (0, total_value, indexed.get(coach_id, 999))

    return sorted(coach_ids, key=sort_key)

def parse_american_odds(value):
    try:
        if value is None:
            return None
        return int(str(value).replace("+", "").strip())
    except Exception:
        return None

def implied_probability(american_odds):
    if american_odds is None:
        return 0
    if american_odds > 0:
        return 100 / (american_odds + 100)
    return abs(american_odds) / (abs(american_odds) + 100)

def golfer_odds_label(golfer):
    return STATIC_ODDS.get(golfer, "(N/A)")

def odds_sort_key(golfer):
    odds_value = parse_american_odds(STATIC_ODDS.get(golfer))
    probability = implied_probability(odds_value)
    return (-probability, last_name_key(golfer), golfer.lower())

def render_pick_timer(start_time):
    if not start_time:
        start_time = time.time()
    start_ms = int(start_time * 1000)
    components.html(f"""
    <div style="background:#000;color:#fff;font-family:Arial,sans-serif;margin:0;padding:0;">
        <div style="font-size:1.6rem;font-weight:800;line-height:1.35;">
            ⏱️ <span id="draft-clock">00:00:00</span>
        </div>
    </div>
    <script>
    const startMs = {start_ms};
    function pad(value) {{ return String(value).padStart(2, "0"); }}
    function updateClock() {{
        const elapsed = Math.max(0, Math.floor((Date.now() - startMs) / 1000));
        const hours = Math.floor(elapsed / 3600);
        const minutes = Math.floor((elapsed % 3600) / 60);
        const seconds = elapsed % 60;
        document.getElementById("draft-clock").textContent =
            `${{pad(hours)}}:${{pad(minutes)}}:${{pad(seconds)}}`;
    }}
    updateClock();
    setInterval(updateClock, 1000);
    </script>
    """, height=45)

if "confirm_clear_rosters" not in st.session_state:
    st.session_state.confirm_clear_rosters = False
if "confirm_save_tournament" not in st.session_state:
    st.session_state.confirm_save_tournament = False

state, state_sha = load_state_from_github()
SELECTED_TOURNAMENT, TOURNAMENT_OPTIONS = current_tournament_selection(state)
teams_data = state["teams"]
draft_order = state["draft_order"]
PLAYER_RESULTS = state.get("player_results", {})
PLAYER_HOLE_OUTCOMES = state.get("hole_outcomes", {})
PLAYER_RESULTS_DISPLAY = {
    player: {
        "score": result.get("score", "N/A"),
        "hole": display_hole_value(result.get("hole", "—")),
        "recent_outcomes": PLAYER_HOLE_OUTCOMES.get(player, []),
        "competitor_id": result.get("competitor_id", ""),
    }
    for player, result in PLAYER_RESULTS.items()
}
picks = derive_picks_from_state(state)
picked_golfers = get_picked_golfers(state)
current_pick = get_current_pick(state)

st_autorefresh(interval=60000 if state.get("draft_active") else 5000, limit=None, key="shared_state_refresh")
auto_refresh_scores_if_needed(state)

selected_tournament_title = html.escape(str(SELECTED_TOURNAMENT.get("title") or "PGA Tournament"))
selected_tournament_date = format_tournament_date_range(
    SELECTED_TOURNAMENT.get("start_date"),
    SELECTED_TOURNAMENT.get("end_date"),
)
selected_tournament_location = html.escape(str(SELECTED_TOURNAMENT.get("location") or "Location TBA"))
app_title = html.escape(str(state.get("app_title") or DEFAULT_APP_TITLE))
payout_rules = html.escape(str(state.get("payout_rules") or DEFAULT_PAYOUT_RULES))

st.markdown(top_thumbnail_html(), unsafe_allow_html=True)
st.markdown(
    f"<div class='app-title'>{app_logo_html()}<h1>{app_title}</h1></div>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<div class='tournament-meta'>{selected_tournament_title} "
    f"<span>• {html.escape(selected_tournament_date)} • {selected_tournament_location}</span></div>",
    unsafe_allow_html=True,
)

st.subheader("Standings")

team_render_data = {}
for coach_id, info in teams_data.items():
    players = info.get("players", [])
    scored_players = get_sorted_scored_players(players)
    top_three_scored = scored_players[:3]
    if top_three_scored:
        top_three_total = format_golf_score(sum(score_value for score_value, _, _, _ in top_three_scored))
    else:
        top_three_total = "N/A"
    team_render_data[coach_id] = {
        "team_name": info.get("team_name", coach_id),
        "players": players,
        "color": info.get("color", "#555555"),
        "face_html": coach_image_html(coach_id, info.get("color", "#555555")),
        "scored_players": top_three_scored,
        "top_three_set": {player for _, _, player, _ in top_three_scored},
        "top_three_total": top_three_total,
    }

ordered_coach_ids = sorted_coach_ids_by_total(list(teams_data.keys()), team_render_data)

for coach_id in ordered_coach_ids:
    data = team_render_data[coach_id]
    team_name = data["team_name"]
    color = data["color"]
    players = data["players"]
    total = data["top_three_total"]
    scored_players = data["scored_players"]
    face_html = data["face_html"]

    if scored_players:
        top3_html = ""
        for score_value, _, player, result in scored_players:
            safe_player = html.escape(display_player_name(player))
            score = html.escape(format_golf_score(score_value))
            status_text = format_hole_status_for_card(result.get("hole", "—"))
            recent_outcomes = get_recent_outcomes_for_standings(player, result) if should_show_recent_hole_outcomes(result) else []
            recent_outcomes_text = format_recent_hole_outcomes(recent_outcomes)
            top3_html += (
                f"<div style='margin:3px 0; color:{color}; font-size:.92rem;'>"
                f"{safe_player} <span style='font-weight:700;'>({score})</span> {html.escape(status_text)}{recent_outcomes_text}"
                f"</div>"
            )
    elif players:
        top3_html = "<div style='color:#aaa; font-style:italic;'>No live scores yet</div>"
    else:
        top3_html = "<div style='color:#aaa; font-style:italic;'>No golfers drafted yet</div>"

    safe_total = html.escape(total)
    card = (
        f"<div class='compact-card' style='border:3px solid {color}; background-color:{color}18;'>"
        f"<div class='team-heading' style='color:{color}; font-size:1.15rem; font-weight:850;'>"
        f"{face_html}<span class='team-name'>{html.escape(team_name)}</span>"
        f"<span class='score-badge' style='background:{color};'>{safe_total}</span></div>"
        f"<div style='line-height:1.35; margin-top:7px;'>{top3_html}</div>"
        f"</div>"
    )
    st.markdown(card, unsafe_allow_html=True)

render_refresh_scores_button("refresh_scores_top", state)

st.subheader("Team Rosters")

for row_start in range(0, len(ordered_coach_ids), 3):
    team_cols = st.columns(3)
    for idx, coach_id in enumerate(ordered_coach_ids[row_start:row_start + 3]):
        info = teams_data[coach_id]
        with team_cols[idx]:
            data = team_render_data[coach_id]
            team_name = data["team_name"]
            players = data["players"]
            color = data["color"]
            face_html = data["face_html"]
            total = data["top_three_total"]
            safe_total = html.escape(total)
            lowest_three_net_score = html.escape(data["top_three_total"])
            top_three_lowest_score_players = data["top_three_set"]

            roster_parts = [
                f"<div class='compact-card' style='border:3px solid {color}; background-color:{color}18;'>",
                f"<div class='team-heading' style='color:{color}; font-size:1.08rem; font-weight:850; margin-bottom:10px;'>"
                f"{face_html}<span class='team-name'>{html.escape(team_name)}</span>"
                f"<span class='score-badge' style='background:{color};'>{safe_total}</span></div>",
            ]

            if not players:
                roster_parts.append("<div style='color:#aaa; font-style:italic;'>No golfers drafted yet</div>")
            else:
                roster_parts.append("<table class='roster-table'><thead><tr><th>Golfer</th><th>Score</th><th>Hole</th></tr></thead><tbody>")
                for player in players:
                    safe_player = html.escape(display_player_name(player))
                    result = get_player_result(player)
                    score = html.escape(str(result.get("score", "N/A")))
                    hole = html.escape(display_hole_value(result.get("hole", "—")))
                    row_class = " class='roster-top-three'" if player in top_three_lowest_score_players else ""
                    roster_parts.append(f"<tr{row_class}><td>{safe_player}</td><td>{score}</td><td>{hole}</td></tr>")
                roster_parts.append("</tbody></table>")

            roster_parts.append(
                f"<div style='color:#fff; font-size:.78rem; font-style:italic; margin-top:9px;'>"
                f"Lowest 3 Net Score = {lowest_three_net_score}</div>"
            )
            roster_parts.append("</div>")
            st.markdown("".join(roster_parts), unsafe_allow_html=True)

render_refresh_scores_button("refresh_scores_middle", state)

st.subheader("Tournament Leaderboard")
render_tournament_leaderboard(SELECTED_TOURNAMENT)

st.markdown(
    f"<div class='payout-rules-box'><div class='payout-rules-label'>Payout Rules</div>{payout_rules}</div>",
    unsafe_allow_html=True,
)

with st.expander("🎯 DRAFT SECTION", expanded=state["draft_enabled"]):
    if not state["draft_enabled"]:
        st.error("🚫 Draft is currently DISABLED in Admin section")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("▶️ Start Draft", type="primary", disabled=state["draft_active"] or current_pick > MAX_PICKS, use_container_width=True):
                result, _ = start_draft()
                if result:
                    st.rerun()

        with col2:
            if st.button("⏹️ Stop Draft", disabled=not state["draft_active"], use_container_width=True):
                result, _ = stop_draft()
                if result:
                    st.rerun()

        with col3:
            if st.button("↩️ Undo Last Pick", disabled=not picks, use_container_width=True):
                result, _ = undo_last_pick()
                if result:
                    undone_pick_num, undone_coach, undone_golfer = result
                    st.success(f"Undid Pick #{undone_pick_num}: {display_player_name(undone_golfer)}. {undone_coach} is back on the clock.")
                    time.sleep(0.5)
                    st.rerun()

        if current_pick > MAX_PICKS:
            st.success(f"🎉 Draft Complete! All {MAX_PICKS} picks are in.")
        elif state["draft_active"]:
            current_coach = get_coach_for_pick(current_pick, draft_order)
            current_color = teams_data.get(current_coach, {}).get("color", "#39FF14")
            safe_current_coach = html.escape(current_coach)
            safe_current_color = html.escape(current_color)
            st.markdown(
                f"<div class='current-pick-box' style='color:{safe_current_color}; "
                f"background:{safe_current_color}26;'>"
                f"<span class='current-pick-label'>Current Pick:</span> "
                f"<span class='current-pick-coach'>{safe_current_coach}</span> "
                f"<span class='current-pick-label'>Pick #{current_pick}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            render_pick_timer(state.get("last_pick_started_at", 0))
        else:
            current_coach = get_coach_for_pick(current_pick, draft_order)
            st.markdown(
                f"<div class='draft-stopped-note'>Draft stopped. {html.escape(current_coach)} is next at Pick #{current_pick}. "
                f"Start the draft to resume picking.</div>",
                unsafe_allow_html=True,
            )

        st.subheader("Draft Dashboard")

        grid_html = """
        <style>
        @keyframes flash { 0% { background-color:#ffeb3b; } 50% { background-color:#fff59d; } 100% { background-color:#ffeb3b; } }
        .draft-table { width:100%; min-width:980px; border-collapse:collapse; font-size:.78rem; background:#000; color:#fff; }
        .draft-table th, .draft-table td { border:1px solid #555; padding:7px; text-align:center; }
        .draft-table th { background-color:#1f1f1f; color:#fff; }
        .current-cell { animation:flash 1.2s infinite; font-weight:bold; }
        .stopped-cell { background-color:#333; color:#aaa; font-weight:bold; }
        </style>
        <div class="draft-table-wrap"><table class="draft-table"><tr><th>Round</th>
        """

        for coach in draft_order:
            grid_html += f"<th>{html.escape(coach)}</th>"
        grid_html += "</tr>"

        for round_num in range(10):
            grid_html += f"<tr><td><b>Round {round_num + 1}</b></td>"
            team_count = len(draft_order)
            for column_num in range(team_count):
                if round_num % 2 == 0:
                    pick_num = round_num * team_count + column_num + 1
                else:
                    pick_num = round_num * team_count + (team_count - 1 - column_num) + 1

                picked_golfer = next((pick[2] for pick in picks if pick[0] == pick_num), None)
                is_current = pick_num == current_pick

                if picked_golfer:
                    cell = html.escape(display_player_name(picked_golfer))
                    cell_style = ""
                elif is_current and state["draft_active"]:
                    cell = f"On Clock<br>Pick {pick_num}"
                    cell_style = "class='current-cell' style='background-color:#ffeb3b; color:#000;'"
                elif is_current and current_pick <= MAX_PICKS:
                    cell = f"Stopped<br>Pick {pick_num}"
                    cell_style = "class='stopped-cell'"
                else:
                    cell = f"Pick {pick_num}"
                    cell_style = ""

                grid_html += f"<td {cell_style}>{cell}</td>"
            grid_html += "</tr>"

        grid_html += "</table></div>"
        st.markdown(grid_html, unsafe_allow_html=True)

        st.subheader("Available Golfers — Click to Draft")
        st.caption("Sorted by odds, then last name. Use search and pages for faster loading on mobile.")

        draft_player_pool, field_note = get_draft_player_pool(SELECTED_TOURNAMENT)
        st.caption(field_note)
        sorted_players = sorted(draft_player_pool, key=odds_sort_key)
        available = [golfer for golfer in sorted_players if golfer not in picked_golfers]
        golfer_search = st.text_input("Find Golfer", value="", key="available_golfer_search").strip().lower()
        if golfer_search:
            available = [golfer for golfer in available if golfer_search in golfer.lower()]
        total_available = len(available)

        if total_available == 0 and not golfer_search and state["draft_active"] and current_pick <= MAX_PICKS:
            result, _ = finish_draft("Complete draft - golfer pool exhausted")
            if result:
                st.success("Draft complete. All available golfers have been drafted and rosters are saved.")
                time.sleep(0.5)
                st.rerun()

        total_pages = max(1, (total_available + AVAILABLE_GOLFERS_PAGE_SIZE - 1) // AVAILABLE_GOLFERS_PAGE_SIZE)
        current_page = min(max(int(st.session_state.get("available_golfers_page", 1) or 1), 1), total_pages)
        st.session_state.available_golfers_page = current_page

        if total_available:
            start_display = (current_page - 1) * AVAILABLE_GOLFERS_PAGE_SIZE + 1
            end_display = min(current_page * AVAILABLE_GOLFERS_PAGE_SIZE, total_available)
            range_text = f"Showing {start_display}-{end_display} of {total_available}"
        else:
            start_display = 0
            end_display = 0
            range_text = "No available golfers"

        nav_left, nav_center, nav_right = st.columns([1, 2.4, 1])
        with nav_left:
            st.markdown("<div class='draft-page-side'>", unsafe_allow_html=True)
            if st.button("←", disabled=current_page <= 1, use_container_width=True, key="available_prev_page"):
                st.session_state.available_golfers_page = max(1, current_page - 1)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with nav_center:
            st.markdown(
                f"<div class='draft-page-center'>Page {current_page} of {total_pages} • {html.escape(range_text)}</div>",
                unsafe_allow_html=True,
            )
        with nav_right:
            st.markdown("<div class='draft-page-side'>", unsafe_allow_html=True)
            if st.button("→", disabled=current_page >= total_pages, use_container_width=True, key="available_next_page"):
                st.session_state.available_golfers_page = min(total_pages, current_page + 1)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        page_start = (current_page - 1) * AVAILABLE_GOLFERS_PAGE_SIZE
        page_end = page_start + AVAILABLE_GOLFERS_PAGE_SIZE
        available_page = available[page_start:page_end]

        for row_start in range(0, len(available_page), 3):
            row_cols = st.columns(3)
            row_players = available_page[row_start:row_start + 3]

            for col_idx, golfer in enumerate(row_players):
                with row_cols[col_idx]:
                    odds_label = golfer_odds_label(golfer)
                    disabled = not state["draft_active"] or current_pick > MAX_PICKS

                    st.markdown("<div class='golfer-pick-wrap'>", unsafe_allow_html=True)
                    pick_clicked = st.button(
                        f"{display_player_name(golfer)} {odds_label}",
                        key=f"pick_{golfer}",
                        disabled=disabled,
                        use_container_width=True,
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
                    if pick_clicked:
                        with st.spinner(f"Saving {display_player_name(golfer)}..."):
                            result, _ = make_draft_pick(golfer)
                            if result:
                                st.rerun()

with st.expander("🔧 Admin Section", expanded=False):
    st.subheader("App Settings")
    with st.form("app_settings_form"):
        new_app_title = st.text_input("App Title", value=state.get("app_title", DEFAULT_APP_TITLE))
        new_payout_rules = st.text_area("Payout Rules", value=state.get("payout_rules", DEFAULT_PAYOUT_RULES), height=110)
        if st.form_submit_button("💾 Save App Settings", use_container_width=True):
            result, _ = save_app_settings(new_app_title, new_payout_rules)
            if result:
                st.success("App settings saved.")
                st.rerun()
            else:
                st.error("App settings were not saved.")

    st.subheader("Tournament Selection")

    if not TOURNAMENT_OPTIONS:
        st.error("Could not load tournament schedule from ESPN right now.")
    else:
        option_lookup = {option["event_id"]: option for option in TOURNAMENT_OPTIONS}
        option_ids = list(option_lookup.keys())
        saved_event_id = str((state.get("selected_tournament") or {}).get("event_id") or "")
        active_event_id = saved_event_id if saved_event_id in option_lookup else str(SELECTED_TOURNAMENT.get("event_id") or "")
        if active_event_id not in option_ids:
            active_event_id = option_ids[0]
        effective_saved_event_id = saved_event_id if saved_event_id in option_lookup else active_event_id

        selected_event_id = st.selectbox(
            "Tournament",
            options=option_ids,
            index=option_ids.index(active_event_id),
            format_func=lambda event_id: tournament_option_label(option_lookup[event_id]),
            key="admin_tournament_select_event_id",
        )

        if st.session_state.get("pending_tournament_event_id") != selected_event_id:
            st.session_state.confirm_save_tournament = False
            st.session_state.pending_tournament_event_id = selected_event_id

        chosen_option = option_lookup[selected_event_id]
        if selected_event_id == effective_saved_event_id:
            st.caption("Current saved tournament is active.")
        else:
            st.warning("Saving this updates the app's tournament target and score source. Rosters will stay untouched.")
            if not st.session_state.confirm_save_tournament:
                if st.button("💾 Save Tournament Selection", use_container_width=True):
                    st.session_state.confirm_save_tournament = True
                    st.rerun()
            else:
                st.warning(f"Are you sure you want to switch to: {tournament_option_label(chosen_option)}?")
                save_col, cancel_col = st.columns(2)
                with save_col:
                    if st.button("✅ YES, SAVE TOURNAMENT", type="primary", use_container_width=True):
                        result, _ = save_selected_tournament(chosen_option)
                        if result:
                            st.session_state.confirm_save_tournament = False
                            st.success("Tournament selection saved.")
                            time.sleep(0.5)
                            st.rerun()
                with cancel_col:
                    if st.button("Cancel Tournament Save", use_container_width=True):
                        st.session_state.confirm_save_tournament = False
                        st.rerun()

    st.subheader("Draft Control")
    st.toggle("Show Performance Debug", value=st.session_state.get("perf_debug_enabled", False), key="perf_debug_enabled")

    st.caption(f"Draft status: {'Enabled' if state['draft_enabled'] else 'Disabled'}")
    enable_col, disable_col = st.columns(2)
    with enable_col:
        if st.button("Enable Draft", disabled=state["draft_enabled"], use_container_width=True):
            result, _ = set_draft_enabled(True)
            st.session_state.confirm_clear_rosters = False
            if result:
                st.rerun()
    with disable_col:
        if st.button("Disable Draft", disabled=not state["draft_enabled"], use_container_width=True):
            result, _ = set_draft_enabled(False)
            st.session_state.confirm_clear_rosters = False
            if result:
                st.rerun()

    if state["draft_enabled"]:
        if not st.session_state.confirm_clear_rosters:
            if st.button("🛑 Reset Draft & Clear Roster", type="secondary", use_container_width=True):
                st.session_state.confirm_clear_rosters = True
                st.rerun()
        else:
            st.warning("⚠️ This will permanently clear ALL rosters and reset the draft.")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ YES, CLEAR EVERYTHING", type="primary", use_container_width=True):
                    result, _ = mutate_shared_state(reset_rosters_in_state, "Reset draft")
                    if result:
                        st.session_state.confirm_clear_rosters = False
                        st.success("✅ All rosters cleared and draft fully reset!")
                        time.sleep(1)
                        st.rerun()

            with col2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.confirm_clear_rosters = False
                    st.rerun()

    st.subheader("Draft Order")

    if state["draft_enabled"]:
        st.info("Disable the draft to change the draft order.")
    else:
        coaches = list(teams_data.keys())
        current_order = draft_order
        proposed_order = []
        for row_start in range(0, len(coaches), 3):
            order_cols = st.columns(3)
            for offset, col in enumerate(order_cols):
                slot_index = row_start + offset
                if slot_index >= len(coaches):
                    continue
                with col:
                    current_coach = current_order[slot_index] if slot_index < len(current_order) else coaches[slot_index]
                    selected_coach = st.selectbox(
                        f"{slot_index + 1}{'st' if slot_index == 0 else 'nd' if slot_index == 1 else 'rd' if slot_index == 2 else 'th'} Pick",
                        options=coaches,
                        index=coaches.index(current_coach) if current_coach in coaches else slot_index,
                        key=f"draft_order_{slot_index}",
                    )
                    proposed_order.append(selected_coach)

        if len(set(proposed_order)) < len(proposed_order):
            st.error("Each draft slot must have a different coach.")
        elif st.button("💾 Save Draft Order", use_container_width=True):
            result, _ = save_draft_order(proposed_order)
            if result:
                st.success("Draft order saved.")
                st.rerun()

    st.subheader("Team Names & Colors")
    st.caption("Color selection is first come, first serve. I'm a chemical engineer, not an IT guy.")
    used_colors = {info.get("color") for info in teams_data.values() if info.get("color")}
    palette_parts = []
    for label, color in TEAM_COLOR_OPTIONS:
        chip_class = "color-chip used" if color in used_colors else "color-chip"
        palette_parts.append(
            f"<span title='{html.escape(label)}' class='{chip_class}' style='background:{color};'></span>"
        )
    st.markdown("".join(palette_parts), unsafe_allow_html=True)

    new_team_settings = {}
    for row_start in range(0, len(teams_data), 3):
        team_setting_cols = st.columns(3)
        for idx, (coach_id, info) in enumerate(list(teams_data.items())[row_start:row_start + 3]):
            with team_setting_cols[idx]:
                st.markdown(f"### {coach_id}")
                team_name = st.text_input("Team Name", value=info.get("team_name", coach_id), key=f"name_{coach_id}")
                current_color = info.get("color", default_team_color(idx))
                colors_used_by_others = {
                    other_info.get("color")
                    for other_id, other_info in teams_data.items()
                    if other_id != coach_id and other_info.get("color")
                }
                available_colors = [current_color] + [
                    color for _, color in TEAM_COLOR_OPTIONS
                    if color not in colors_used_by_others and color != current_color
                ]
                selected_color = st.selectbox(
                    "Color",
                    options=available_colors,
                    index=0,
                    format_func=lambda color: f"{TEAM_COLOR_BY_HEX.get(color, color)} ({color})",
                    key=f"color_{coach_id}",
                )
                st.caption(f"Photo file: {coach_photo_filename(coach_id)}")
                new_team_settings[coach_id] = {"team_name": team_name, "color": selected_color}

    if st.button("💾 Save Team Settings", use_container_width=True):
        result, _ = save_team_settings(new_team_settings)
        if result:
            st.success("Team settings saved!")
            st.rerun()
        else:
            st.error("Team settings were not saved. Please try again.")

st.caption(f"{html.escape(str(state.get('app_title') or DEFAULT_APP_TITLE))} • Built by Jayme Leita")
if st.session_state.get("perf_debug_enabled", False):
    render_ms = int((time.perf_counter() - RENDER_T0) * 1000)
    team_count = len(teams_data)
    available_count = len([golfer for golfer in PGA_PLAYERS if golfer not in picked_golfers])
    st.caption(
        "Perf Debug: "
        f"Render {render_ms}ms | "
        f"Last Score Update {format_last_score_refresh_time(state)} | "
        f"Teams {team_count} | "
        f"Available Golfers {available_count}"
    )
