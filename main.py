"""Script to analyze WhatsApp chats"""

from collections import Counter
from datetime import datetime as dt
import re
from colorama import Fore
import colorama
import emoji
import pandas as pd
import termgraph.termgraph as tg


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
        self.longest_msg = ""
        self.num_messages, self.num_words, self.num_emojis = 0, 0, 0
        self.word_freq, self.emoji_freq = {}, {}
        self.hour_freq = {h: 0 for h in range(24)}

        for i, row in df.loc[df["user"] == username].iterrows():
            timestamp, msg = row["timestamp"], row["message"]
            self.num_messages += 1
            if len(msg) > len(self.longest_msg): self.longest_msg = msg

            for word in msg.split():
                word = word.strip(r"\.\,\!\?\;\:\(\)\[\]\{\}").lower()
                self.num_words += 1
                if not emoji.is_emoji(word):
                    if word in self.word_freq: self.word_freq[word] += 1
                    else: self.word_freq[word] = 1

                    for char in word:
                        if not emoji.is_emoji(char): continue
                        self.num_emojis += 1
                        if char in self.emoji_freq: self.emoji_freq[char] += 1
                        else: self.emoji_freq[char] = 1

            hour = timestamp.hour
            self.hour_freq[hour] += 1

        if self.num_messages:
            self.avg_msg_len = self.num_words / self.num_messages
        self.hour_freq = dict(sorted(self.hour_freq.items(), key=lambda x: x))

    def graph_freq(self, freq: dict, total: int, padding: int = 8, scale: int = 100):
        """Draws a ascii graph for frequencies"""

        freq = dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))
        graph = ""
        for key in list(freq)[:5]:
            len_line = int(round(freq[key] / total * scale))
            graph += f"{key:<{padding}} | {self.color}{'▇'*len_line}{Fore.RESET} {freq[key]}\n"
        return graph

    def __repr__(self):
        top_emojis = ""
        for emoji in list(self.emoji_freq.keys())[:5]:
            top_emojis += f"{emoji}:{self.color}{self.emoji_freq[emoji]}{Fore.RESET} "

        top_hour = max(self.hour_freq.keys(), key=(lambda freq: self.hour_freq[freq]))
        top_hour = dt.strptime(f"{top_hour}", "%H").strftime("%I:%M %p")

        return (f"""{self.username.upper()}{self.color}\n{'='*32}{Fore.RESET}
Messages sent: {self.color}{self.num_messages}{Fore.RESET}
Avg msg length: {self.color}{self.avg_msg_len:.2f} words{Fore.RESET}
Longest message: {self.color}{len(self.longest_msg)} chars{Fore.RESET}
Words sent: {self.color}{self.num_words}{Fore.RESET}
Emojis sent: {self.color}{self.num_emojis}{Fore.RESET}
\nTOP WORDS:\n{self.graph_freq(self.word_freq, self.num_words, scale=100)}
\nTOP EMOJIS:\n{self.graph_freq(self.emoji_freq, self.num_emojis, padding=1)}
Most active at: {self.color}{top_hour}{Fore.RESET}
Avg msg sentiment: to do""")


def draw(df: pd.DataFrame):
    """Draws a graph of the data"""

    users = [user for user in df["user"].unique()]
    colors = [
        Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX,
        Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX
    ]

    i = -1
    for user in users:
        i += 1
        if i > len(colors): i = 0
        color = colors[i]
        print(f"\n{User(user, df, color)}")
    print(end=None)


if __name__ == "__main__":
    colorama.init(autoreset=True)
    df = frame_data("testchat.txt")
    draw(df)