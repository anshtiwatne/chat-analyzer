"""Script to analyze WhatsApp chats"""

from collections import Counter
from datetime import datetime as dt
import re
import colorama
from colorama import Fore
import emoji
import pandas as pd

DIVIDER = "="*48
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
        # group1- date, group2- time, group3- sender, group4- message
        pattern = r"(\d*?/\d*?/\d*?), (\d*?:\d*? [A, P]M) - (.*?): (.*)"
        data = re.findall(pattern, file.read())

    df = pd.DataFrame(columns=["timestamp", "user", "message"])
    for element in data:
        date, time, sender, message = element
        if message in ("<Media omitted>", "Missed voice call"): message = ""
        timestamp = dt.strptime(f"{date} {time}", "%m/%d/%y %I:%M %p")
        df.loc[len(df)] = [timestamp, sender, message]

    return df


class User:
    """Class to represent a user"""

    def __init__(self, username: str, df: pd.DataFrame, color: str = Fore.RESET):
        
        self.username = username
        self.color = color
        self.longest_msg = max(df.loc[df["user"] == username]["message"], key=len)
        self.word_freq = Counter(word.strip(r".,!\?;:()[]{}").lower() for msg in df.loc[df["user"] == username]["message"] for word in msg.split() if word.lower() not in ENG_COMMON_WORDS)
        self.emoji_freq = Counter(char for msg in df.loc[df["user"] == username]["message"] for char in msg if emoji.is_emoji(char))
        self.hour_freq = Counter(dt.strftime(timestamp, "%H") for timestamp in df.loc[df["user"] == username]["timestamp"])
        self.num_messages = len(df.loc[df["user"] == username]["message"])
        self.num_words = sum(self.word_freq.values())
        self.num_emojis = sum(self.emoji_freq.values())
        self.avg_msg_len = self.num_words/self.num_messages

    def graph_freq(self, freq: Counter, padding: int = 8, scale: int = 100):
        """Returns a Unicode bar graph for a given frequency distribution"""

        graph = ""
        total = sum(freq.values())
        for element, count in freq.most_common(5):
            len_line = int(round(count / total * scale))
            graph += f"{element:<{padding}} | {self.color}{'▇'*len_line}{Fore.RESET} {count}\n"
        return graph
    
    def __repr__(self):
        
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
Most active at: {self.color}{dt.strptime(f"{top_hour}", "%H").strftime("%I:%M %p")}{Fore.RESET}
Avg msg sentiment: {self.color}{NotImplemented}{Fore.RESET}
"""


def main(df: pd.DataFrame):
    """Main function"""

    users = []
    usernames = [username for username in df["user"].unique()]
    colors = [
        Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX,
        Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX
    ]
    
    i = -1
    for user in usernames:
        i += 1
        if i >= len(colors): i = 0
        user = User(user, df, colors[i])
        users.append(user)
        print(user)

    total_msgs = sum(user.num_messages for user in users)
    msg_bar = [f"{user.color}{'▇'*int(round(user.num_messages / total_msgs * 50))}{Fore.RESET}" for user in users]
    months_active = {dt.strftime(timestamp, "%b %y"):"" for timestamp in df["timestamp"]}
    days_active = {dt.strftime(timestamp, "%a"):"" for timestamp in df["timestamp"]}

    for user in users:
        month_freq = Counter(dt.strftime(timestamp, "%b %y") for timestamp in df.loc[df["user"] == user.username]["timestamp"])
        day_freq = Counter(dt.strftime(timestamp, "%a") for timestamp in df.loc[df["user"] == user.username]["timestamp"])
        for month in month_freq:
            months_active[month] += f"{user.color}{'▇'*int(round(month_freq[month] / total_msgs * 250))}{Fore.RESET}"
        for day in day_freq:
            days_active[day] += f"{user.color}{'▇'*int(round(day_freq[day] / total_msgs * 250))}{Fore.RESET}"
    # sort days_active by weekdays
    days_active = {day: days_active[day] for day in sorted(days_active, key=lambda day: WEEKDAYS.index(day))}


    print(f"""
CHAT {" / ".join([f"{user.color}{user.username}{Fore.RESET}" for user in users])}\n{DIVIDER}\n
Total words  | {"".join(msg_bar)} {":".join([str(user.num_messages) for user in users])}
Total emojis | {"".join(msg_bar)} {":".join([str(user.num_emojis) for user in users])}
\nMost active day: {days_active[max(days_active, key=days_active.get)]}
\nTIMELINE:\n{chr(10).join([f"{month} | {''.join(bar)}" for month, bar in months_active.items() if "▇" in bar])}
\nACTIVITY BY WEEKDAY:\n{chr(10).join([f"{day} | {''.join(bar)}" for day, bar in days_active.items() if "▇" in bar])}
""")
        


if __name__ == "__main__":
    colorama.init(autoreset=True)
    df = frame_data("testchat.txt")
    main(df)