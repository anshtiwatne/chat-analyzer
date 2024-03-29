#!/usr/bin/env python3
"""Script to analyze WhatsApp chats"""
# pylint: disable=invalid-name, multiple-statements, redefined-outer-name

from collections import Counter, OrderedDict
import colorama
from colorama import Fore
import emoji
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
        pattern = r"(\d*?/\d*?/\d*?), (\d*?:\d*?)\s([Aa]|[Pp][Mm]) - (.*?): (.*)"
        data = pd.Series(file.read()).str.findall(pattern)[0]

    df = pd.DataFrame(columns=["timestamp", "user", "message"])
    dt_format = "%m/%d/%y %I:%M %p"
    for element in data:
        date, time, meridiem, sender, message = element
        # print(element)
        time = f"{time} {meridiem}"
        if message in AUTOMATED_MESSAGES: message = ""
        timestamp = pd.to_datetime(f"{date} {time}", format=dt_format)
        df.loc[len(df)] = [timestamp, sender, message]
    # print(dt_format)
    # print(df)
    return df


class User:
    """Class to represent a user"""

    def __init__(self, username: str, df: pd.DataFrame, color: str = Fore.RESET):

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

    def graph_freq(self, freq: Counter, padding: int = 10, scale: int = 100):
        """Returns a Unicode bar graph for a given frequency distribution"""

        graph = ""
        total = sum(freq.values())
        for element, count in freq.most_common(5):
            len_bar = int(round(count / total * scale))
            graph += f"{element:<{padding}} | {self.color}{BAR_CHAR*len_bar}{Fore.RESET} {count}\n"
        return graph

    def display(self):
        """Displays user information"""
    
        top_hour = self.hour_freq.most_common(1)[0][0]
        return f"""
{self.username.upper()}{self.color}\n{DIVIDER}{Fore.RESET}
Messages sent: {self.color}{self.num_messages}{Fore.RESET}
Avg msg length: {self.color}{self.avg_msg_len:.2f} {Fore.RESET}words
Longest msg: {self.color}{len(self.longest_msg)}{Fore.RESET} chars
Words sent: {self.color}{self.num_words}{Fore.RESET}
Emojis sent: {self.color}{self.num_emojis}{Fore.RESET}
\nTOP WORDS:\n{self.graph_freq(self.word_freq, scale=200)}
TOP EMOJIS:\n{self.graph_freq(self.emoji_freq, padding=1)}
Top swear: {self.color}{self.top_swear}{Fore.RESET}
Left on read coefficient: {self.color}{NotImplemented}{Fore.RESET}
Most active at: {self.color}{top_hour}{Fore.RESET}
Avg msg sentiment: {self.color}{self.sentiment_polarity:.3f}{Fore.RESET}
"""

    def __repr__(self):
        return self.username

def stacked_graph(data: dict[str: Counter], padding: int = 8, scale: int = 100):
    """Returns a Unicode bar graph for a given frequency distribution"""

    graph = ""
    freq_distribution = {element: [] for freq in data.values() for element in freq}
    for user, freq in data.items():
        for key, value in freq.items():
            freq_distribution[key].append({user: value})
 
    total = sum(freq.total() for freq in data.values())
    graph = ""
    for element, distribution in freq_distribution.items():
        bar = ""
        for freq in distribution:
            for user, count in freq.items():
                len_bar = int(round(count / total * scale))
                bar += f"{user.color}{BAR_CHAR*len_bar}{Fore.RESET}"
        # only add the bar if it's not empty (it's empty if the length was rounded to 0)
        if BAR_CHAR in bar: graph += f"{element:<{padding}} | {bar}\n"

    return graph


def main(df: pd.DataFrame):
    """Main function"""

    result = ""
    colors = [
        Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX,
        Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX]

    users = list()
    for i, username in enumerate(df["user"].unique()):
        color = colors[i % len(colors)]
        user = User(username, df, color)
        users.append(user)
        result += user.display()

    total_words = sum(user.num_words for user in users)
    total_emojis = sum(user.num_emojis for user in users)
    words_sent, emojis_sent = None, None
    if total_words: words_sent = "".join([f"{user.color}{BAR_CHAR*int(round((user.num_words/total_words*32)))}{Fore.RESET}" for user in users])
    if total_emojis: emojis_sent = "".join([f"{user.color}{BAR_CHAR*int(round((user.num_emojis/total_emojis*32)))}{Fore.RESET}" for user in users])
    day_freq = Counter()
    for user in users: day_freq += user.day_freq

    result += (f"""
{" vs ".join(f"{user.color}{user.username.upper()}{Fore.RESET}" for user in users)} CHAT STATISTICS\n{DIVIDER}\n
Words sent  | {words_sent}
Emojis sent | {emojis_sent}\n
TIMELINE:\n{stacked_graph({user: user.month_freq for user in users}, padding=1)}
{print(day_freq.most_common())}
Most active day = {day_freq.most_common(1)[0][0]}\n
AVTIVITY BY WEEKDAY:\n{stacked_graph({user: user.weekday_freq for user in users}, padding=1)}
ACTIVITY BY HOUR:\n{stacked_graph({user: user.hour_freq for user in users}, padding=1)}
Avg msg sentiment: {sum(user.sentiment_polarity for user in users)/len(users):.3f}
(Positive > 0 > Negative)
""") # color most active day by user that sent most messages during that day

    return result


if __name__ == "__main__":
    import itertools
    import threading
    import time

    colorama.init(autoreset=True)
    chat_path = input("Enter path to chat file: ").strip().lower()
    
    done = False
    def progress_loop():
        """Progress loop"""
        animation = itertools.cycle([".  ", ".. ", "..."])
        for char in animation:
            if done: break
            print(f"\rLoading {char}", end="", flush=True)
            time.sleep(0.2)
        print(f"\rDone!{' '*10}")
    thread = threading.Thread(target=progress_loop)
    thread.start()

    df = frame_data(chat_path)
    done = True
    time.sleep(0.5)
    print(main(df))