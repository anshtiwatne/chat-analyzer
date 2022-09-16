from collections import Counter, OrderedDict
import emoji
import flet
from flet import *
from flet import icons, dropdown, colors
import pandas as pd
from textblob import TextBlob


DIVIDER = "="*48
BAR_CHAR = "█"
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
        self.top_hour = self.hour_freq.most_common(1)[0][0]

    def graph_freq(self, freq: Counter, title: str, page: Page):
        """Returns a Unicode bar graph for a given frequency distribution"""

        if not freq: return Text(None)
        title = title.title()
        words, bars = Column(spacing=0), Column(spacing=0)
        top = freq.most_common(1)[0][1]
        # total = sum(freq.values())
        scale = page.window_width/20
        for element, count in freq.most_common(5):
            len_bar = int(round(count / top * scale))
            words.controls.append(Row([Text(element)]))
            bars.controls.append(Row([Text("|"), Text(BAR_CHAR*len_bar, color=self.color), Text(count)]))
        
        graph = Column([Row([Text(title)], alignment="center"), Row([words, bars])])
        return graph

    def display(self, page: Page):
        """Displays user information"""

        return Column([
            Row([Text("Messages sent:"), Text(self.num_messages, color=self.color)]),
            Row([Text("Avg msg length:"), Text(round(self.avg_msg_len, 2), color=self.color), Text("words")]),
            Row([Text("Longest msg:"), Text(len(self.longest_msg), color=self.color), Text("chars")]),
            Row([Text("Words sent:"), Text(self.num_words, color=self.color)]),
            Row([Text("Emojis sent:"), Text(self.num_emojis, color=self.color)]),
            self.graph_freq(self.word_freq, "top words", page),
            self.graph_freq(self.emoji_freq, "top emojs", page),
            Row([Text("Top swear:"), Text(self.top_swear if self.top_swear != None else "None", color=self.color)]),
            Row([Text("Left on read coefficient:"), Text(NotImplemented, color=self.color)]),
            Row([Text("Most active at:"), Text(self.top_hour, color=self.color)]),
            Row([Text("Average message sentiment:"), Text(round(self.sentiment_polarity, 2), color=self.color)])
            # self.graph_freq(self.emoji_freq, "top emojis")
        ]) #width=600, alignment="center"


def stacked_graph(data: dict[str: Counter], title:str, page: Page):
    """Returns a Unicode bar graph for a given frequency distribution"""

    scale = page.window_width/10
    freq_distribution = {element: [] for freq in data.values() for element in freq}
    for user, freq in data.items():
        for key, value in freq.items():
            freq_distribution[key].append({user: value})
 
    total = sum(freq.total() for freq in data.values())
    graph = Column()
    elements, bars = Column(spacing=0), Column(spacing=0)
    title = title.title()
    for element, distribution in freq_distribution.items():
        bar = Row(spacing=0)
        for freq in distribution:
            for user, count in freq.items():
                len_bar = int(round(count / total * scale))
                bar.controls.append(Text(f"{BAR_CHAR*len_bar}", color=user.color))
        # only add the bar if it's not empty (it's empty if the length was rounded to 0)
        if len_bar >= 1:
            elements.controls.append(Text(element))
            bars.controls.append(bar)
        
        graph = Column([Row([Text(title)], alignment="center"), Row([elements, bars])])

    return graph


def chat_stats(users: list[User], df: pd.DataFrame, page: Page):
    """chat statistics"""

    total_words = sum(user.num_words for user in users)
    total_emojis = sum(user.num_emojis for user in users)
    words_sent, emojis_sent = Row(), Row()
    if total_words: words_sent = Row([Text(f"{BAR_CHAR*int(round(user.num_words/total_words*25))}", color=user.color) for user in users], spacing=0)
    if total_emojis: emojis_sent = Row([Text(f"{BAR_CHAR*int(round(user.num_emojis/total_emojis*25))}", color=user.color) for user in users], spacing=0)
    day_freq = Counter()
    for user in users: day_freq += user.day_freq

    return Column([
        Row([Text("Words sent |"), words_sent]),
        Row([Text("Emojis sent |"), emojis_sent]),
        stacked_graph({user: user.month_freq for user in users}, "timeline", page),
        Row([Text("Most active day:"), Text(day_freq.most_common(1)[0][0], color=None)]), # color by top user that day
        stacked_graph({user: user.weekday_freq for user in users}, "activity by weekday", page),
        stacked_graph({user: user.hour_freq for user in users}, "activity by hour", page),
        Row([Text("Average message sentiment:"), Text(round(sum(user.sentiment_polarity for user in users)/len(users), 2))]), # color by top user sentiment
        Row([Text("(Positive > 0 > Negative)")])
    ])


def main(page: flet.Page):
    """flet app"""

    page.title = "WhatStats"
    page.scroll = "always"
    appbar = AppBar(title=Text("WhatStats", style="headlineMedium"), center_title=True)
    page.add(appbar)
    page.window_width = 360
    page.window_height = 640
    print(f"window: {page.window_width}x{page.window_height}")
    # page.theme = Theme(font_family="Seoge UI", page_transitions="cupertino")
    # page.update()

    def pick_files_result(e: FilePickerResultEvent):
        filename.value = " ,".join(map(lambda f: f.name, e.files)) if e.files else "Cancelled!"
        path.value = " ,".join(map(lambda f: f.path, e.files)) if e.files else None
        btn.text = None
        print(f"{filename.value} loaded")
        btn.update()
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
    user_select = Dropdown(expand=True, disabled=True, hint_text="User", on_change=dropdown_change)
    page.add(Row([btn, filename, user_select]))
    page.add(Divider())
    page.add(selected_user_data)
    
    users = dict()
    def analyze_chat():

        selected_user_data.controls = [ProgressBar()]
        page.update()
        df = frame_data(path.value)
        colors = ["#1EB980", "#FF6859", "#FFCF44", "#B15DFF", "#72DEFF"]
        authors = list()

        options = list()
        for i, username in enumerate(df["user"].unique()):
            color = colors[i % len(colors)]
            user = User(username, df, color)
            authors.append(user)
            users[username] = user.display(page)
            options.append(dropdown.Option(username))

        print("analysis complete")
        selected_user_data.controls = [chat_stats(authors, df, page)]
        user_select.options = options
        user_select.disabled = False
        # selected_user_data.controls = [Text("CHAT STATISTICS")]
        page.update()

flet.app(target=main)