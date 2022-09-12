from collections import Counter, OrderedDict
# import colorama
from colorama import Fore
import emoji
import flet
from flet import *
from flet import icons, dropdown, colors
import pandas as pd
from textblob import TextBlob


DIVIDER = "="*48
BAR_CHAR = "▇"
AUTOMATED_MESSAGES = ["<Media omitted>", "Missed voice call"]
PUNCTUATIONS = r".,!\?;:()[]{}"
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
ENG_COMMON_WORDS = [
    #Articles
    'a', 'an', 'the',
    #Conjunctions
    'for', 'and', 'nor', 'but', 'or', 'yet', 'so',
    #Pronouns
    'i', 'me', 'my', 'mine', 'myself', 'you', 'your', 'yours', 'yourself',
    'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it',
    'its', 'itself', 'we', 'us', 'our', 'ours', 'ourselves', 'yourselves',
    'they', 'them', 'their', 'theirs', 'themselves', 'that',
    #Prepositions
    'above', 'across', 'against', 'along', 'among', 'around', 'at', 'before',
    'behind', 'below', 'beneath', 'beside', 'between', 'by', 'down', 'from',
    'in', 'into', 'near', 'of', 'off', 'on', 'to', 'toward', 'under', 'upon',
    'with', 'within'
]


def get_dt_format(data: pd.Series):
    """Get the datetime format used in the chat file"""

    set1 = set()
    set2 = set()
    for element in data:
        date, time, meridiem, sender, message = element
        n1, n2, year = date.split("/")
        set1.add(n1)
        set2.add(n2)
    if len(set1) > len(set2): return "%d/%m/%y %I:%M %p"
    elif len(set1) < len(set2): return "%m/%d/%y %I:%M %p"
    else: return ValueError("unknown datetime fomat")


def frame_data(path: str):
    """Scrapes Whatsapp chat export file and creates a dataframe"""

    with open(path, "r", encoding="utf-8") as file:
        # groups: date, time, meridiem, sender, message
        pattern = r"(\d*?/\d*?/\d*?), (\d*?:\d*?) ([Aa]|[Pp][Mm]) - (.*?): (.*)"
        data = pd.Series(file.read()).str.findall(pattern)[0]

    df = pd.DataFrame(columns=["timestamp", "user", "message"])
    for element in data:
        date, time, meridiem, sender, message = element
        time = f"{time} {meridiem}"
        if message in AUTOMATED_MESSAGES: message = ""
        timestamp = pd.to_datetime(f"{date} {time}", format=get_dt_format(data))
        df.loc[len(df)] = [timestamp, sender, message]

    return df


class User:
    """Class to represent a user"""

    def __init__(self, username: str, df: pd.DataFrame, color: str = None):

        _df = df.loc[df["user"] == username]
        _words = [word.strip(PUNCTUATIONS+" ").lower() for msg in _df["message"] for word in msg.split()]
        _emojis = [char for msg in _df["message"] for char in msg if emoji.is_emoji(char)]
        _words = [word for word in _words if word.isalpha() and word not in ENG_COMMON_WORDS]

        self.username = username
        self.color = color
        self.word_freq = Counter(_words)
        self.emoji_freq = Counter(_emojis)
        self.longest_msg = max(df.loc[df["user"] == username]["message"], key=len)
        self.hour_freq = Counter(pd.Timestamp(timestamp).strftime("%I %p") for timestamp in _df["timestamp"])
        self.weekday_freq = Counter(pd.Timestamp(timestamp).strftime("%a") for timestamp in _df["timestamp"])
        self.day_freq = Counter(pd.Timestamp(timestamp).strftime("%d/%m/%y") for timestamp in _df["timestamp"])
        self.month_freq = Counter(pd.Timestamp(timestamp).strftime("%m/%y") for timestamp in _df["timestamp"])
        self.weekday_freq = Counter(OrderedDict(sorted(self.weekday_freq.items(), key=lambda x: WEEKDAYS.index(x[0]))))
        self.hour_freq = Counter(OrderedDict(sorted(self.hour_freq.items())))
        self.num_words = sum(self.word_freq.values())
        self.num_emojis = sum(self.emoji_freq.values())
        self.num_messages = len(_df)
        self.avg_msg_len = self.num_words / self.num_messages
        self.sentiment_polarity = sum(TextBlob(msg).sentiment.polarity for msg in _df["message"]) / self.num_messages
        self.top_swear = min(_words, key = lambda word: TextBlob(word).sentiment.polarity) if _words else None
        self.top_swear = self.top_swear if self.top_swear == None or TextBlob(self.top_swear).sentiment.polarity < 0 else None

    def display(self):
        """Displays user information"""

        return Column([
            Text(self.username),
            Divider(color=self.color),
            Row([Text("Messages sent:"), Text(self.num_messages, color=self.color)]),
            Row([Text("Avg msg length:"), Text(self.avg_msg_len, color=self.color), Text("words")]),
            Row([Text("Longest msg:"), Text(self.avg_msg_len, color=self.color), Text("chars")]),
            Row([Text("Words sent:"), Text(self.num_words, color=self.color)]),
            Row([Text("Emojis sent:"), Text(self.num_emojis, color=self.color)]),
            Text("\nTOP WORDS:"),
            Text(NotImplemented)
        ]) #width=600, alignment="center"
    

def main(page: flet.Page):
    """flet app"""

    page.title = "WhatStats"
    page.scroll = "always"
    appbar = AppBar(title=Text("WhatStats", style="headlineMedium"), center_title=True)
    page.add(appbar)

    def pick_files_result(e: FilePickerResultEvent):
        filename.value = " ,".join(map(lambda f: f.name, e.files)) if e.files else "Cancelled!"
        path.value = " ,".join(map(lambda f: f.path, e.files)) if e.files else None
        filename.update()
        analyze_chat()

    def dropdown_change(e):
        selected_user = user_select.value
        selected_user_data.controls = users[selected_user].controls
        page.update()
        print(f"user changed to: {selected_user}")

    pick_files_dialog = FilePicker(on_result=pick_files_result)
    filename = Text(italic=True)
    path = Text()
    selected_user = ""
    selected_user_data = Column([Row([Text("Choose a file")])])
    page.overlay.append(pick_files_dialog)

    btn = ElevatedButton("Pick files", icon=icons.UPLOAD_FILE, on_click=lambda _: pick_files_dialog.pick_files(allowed_extensions=["txt"]))
    user_select = Dropdown(expand=True, disabled=True, hint_text="User", on_change=dropdown_change, icon=icons.FACE)
    page.add(Row([btn, filename, user_select]))
    page.add(selected_user_data)
    
    users = dict()
    def analyze_chat():

        selected_user_data.controls = [ProgressBar()]
        page.update()
        df = frame_data(path.value)
        colors = ["red", "green", "yellow", "blue", "magenta", "cyan"]

        options = list()
        for i, username in enumerate(df["user"].unique()):
            color = colors[i % len(colors)]
            user = User(username, df, color)
            users[username] = user.display()
            options.append(dropdown.Option(username))

        user_select.options = options
        user_select.disabled = False
        selected_user_data.controls = [Text("User not chosen")]
        page.update()

flet.app(target=main)