"""Script to analyze WhatsApp chats"""
# pylint: disable=invalid-name

from collections import Counter, OrderedDict
from datetime import datetime as dt
import re
import colorama
from colorama import Fore
import emoji
import pandas as pd
from textblob import TextBlob

DT_FORMAT = "%m/%d/%y %I:%M %p"
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


def frame_data(path: str):
    """Reads a WhatsApp chat export file and creates a dataframe"""

    with open(path, "r", encoding="UTF8") as file:
        # groups: date, time,  sender, message
        pattern = r"(\d*?/\d*?/\d*?), (\d*?:\d*?) ([Aa]|[Pp][Mm]) - (.*?): (.*)"
        data = re.findall(pattern, file.read())

    df = pd.DataFrame(columns=["timestamp", "user", "message"])
    for element in data:
        date, time, meridiem, sender, message = element
        time = f"{time} {meridiem}"
        if message in AUTOMATED_MESSAGES: message = ""
        timestamp = pd.to_datetime(f"{date} {time}", format=DT_FORMAT)
        df.loc[len(df)] = [timestamp, sender, message]

    return df


class User:
    """Class to represent a user"""

    def __init__(self, username: str, df: pd.DataFrame, color: str = Fore.RESET):
        
        self.username = username
        self.color = color
        self.longest_msg = max(df.loc[df["user"] == username]["message"], key=len)
        self.word_freq = Counter(word.strip(PUNCTUATIONS+" ").lower() for msg in df.loc[df["user"] == username]["message"] for word in msg.split() if word.lower() not in ENG_COMMON_WORDS and not emoji.is_emoji(word))
        self.emoji_freq = Counter(char for msg in df.loc[df["user"] == username]["message"] for char in msg if emoji.is_emoji(char))
        self.hour_freq = Counter(dt.strftime(timestamp, "%I %p") for timestamp in df.loc[df["user"] == username]["timestamp"])
        self.weekday_freq = Counter(dt.strftime(timestamp, "%a") for timestamp in df.loc[df["user"] == username]["timestamp"])
        self.hour_freq = Counter(OrderedDict(sorted(self.hour_freq.items())))
        self.weekday_freq = Counter(OrderedDict(sorted(self.weekday_freq.items(), key=lambda x: WEEKDAYS.index(x[0]))))
        self.day_freq = Counter(dt.strftime(timestamp, "%d/%m/%y") for timestamp in df.loc[df["user"] == username]["timestamp"])
        self.month_freq = Counter(dt.strftime(timestamp, "%b %y") for timestamp in df.loc[df["user"] == username]["timestamp"])
        self.num_messages = len(df.loc[df["user"] == username]["message"])
        self.num_words = sum(self.word_freq.values())
        self.num_emojis = sum(self.emoji_freq.values())
        self.avg_msg_len = self.num_words/self.num_messages
        self.sentiment_score = sum(TextBlob(msg).sentiment.polarity for msg in df.loc[df["user"] == username]["message"])/self.num_messages

    def graph_freq(self, freq: Counter, padding: int = 8, scale: int = 100):
        """Returns a Unicode bar graph for a given frequency distribution"""

        graph = ""
        total = sum(freq.values())
        for element, count in freq.most_common(5):
            len_bar = int(round(count / total * scale))
            graph += f"{element:<{padding}} | {self.color}{BAR_CHAR*len_bar}{Fore.RESET} {count}\n"
        return graph
    
    def display(self):
        
        top_hour = self.hour_freq.most_common(1)[0][0]
        return f"""
{self.username.upper()}{self.color}\n{DIVIDER}{Fore.RESET}
Messages sent: {self.color}{self.num_messages}{Fore.RESET}
Avg msg length: {self.color}{self.avg_msg_len:.2f} {Fore.RESET}words
Longest msg: {self.color}{len(self.longest_msg)}{Fore.RESET} chars
Words sent: {self.color}{self.num_words}{Fore.RESET}
Emojis sent: {self.color}{self.num_emojis}{Fore.RESET}
\nTOP WORDS:\n{self.graph_freq(self.word_freq, scale=500)}
TOP EMOJIS:\n{self.graph_freq(self.emoji_freq, padding=1)}
Most active at: {self.color}{top_hour}{Fore.RESET}
Avg msg sentiment: {self.color}{self.sentiment_score:.3f}{Fore.RESET}
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
        if BAR_CHAR in bar: graph += f"{element:<{padding}} | {bar}\n"
    
    return graph


def main(df: pd.DataFrame):
    """Main function"""
    
    colors = [
        Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX,
        Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX]

    i = int() -1
    users = list()
    for username in df["user"].unique():
        i = 0 if i >= len(colors) else i + 1
        user = User(username, df, colors[i])
        users.append(user)
        print(user.display())
    total_words = sum(user.num_words for user in users)
    total_emojis = sum(user.num_emojis for user in users)
    words_sent, emojis_sent = None, None
    if total_words: words_sent = "".join([f"{user.color}{BAR_CHAR*int(round((user.num_words/total_words*32)))}{Fore.RESET}" for user in users])
    if total_emojis: emojis_sent = "".join([f"{user.color}{BAR_CHAR*int(round((user.num_emojis/total_emojis*32)))}{Fore.RESET}" for user in users])

    print(f"""
{" vs ".join(f"{user.color}{user.username.upper()}{Fore.RESET}" for user in users)} CHAT STATISTICS\n{DIVIDER}\n
Words sent  | {words_sent}
Emojis sent | {emojis_sent}\n
TIMELINE:\n{stacked_graph({user: user.month_freq for user in users}, padding=1)}
MOST ACTIVE DAY = {users[0].day_freq.most_common(1)[0][0]}\n
AVTIVITY BY WEEKDAY:\n{stacked_graph({user: user.weekday_freq for user in users}, padding=1)}
ACTIVITY BY HOUR:\n{stacked_graph({user: user.hour_freq for user in users}, padding=1)}
Avg msg sentiment: {sum(user.sentiment_score for user in users)/len(users):.3f}
(Positive > 0 > Negative)
""") # color most active day by user that sent most messages during that day


if __name__ == "__main__":
    colorama.init(autoreset=True)
    chat_path = input("Enter path to chat file: ").strip().lower()
    format_choice = input("Is the date formatted as day first?: ").strip().lower()
    if format_choice == "y": DT_FORMAT = "%d/%m/%y %I:%M %p"
    df = frame_data(chat_path)
    main(df)