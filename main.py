"""Script to analyze WhatsApp chats"""

from datetime import datetime as dt
import re
import emoji
import pandas as pd


def frame_data(path: str):
    """Reads a WhatsApp chat export file and creates a dataframe"""

    with open(path, "r", encoding="UTF8") as file:
        # group1- date, group2- time, group3- sender, group4- message
        pattern = r"(\d*?/\d*?/\d*?), (\d*?:\d*? [A, P]M) - (.*?): (.*)"
        data = re.findall(pattern, file.read())

    df = pd.DataFrame(columns=["timestamp", "user", "message"])
    for element in data:
        date, time, sender, message = element
        timestamp = dt.strptime(f"{date} {time}", "%m/%d/%y %I:%M %p")
        df.loc[len(df)] = [timestamp, sender, message]

    return df


class User:
    """Class to represent a user"""

    def __init__(self, username: str, df: pd.DataFrame):

        self.username = username
        self.longest_msg = ""
        self.num_messages, self.num_words, self.num_emojis = 0, 0, 0
        self.word_freq, self.emoji_freq = {}, {}
        self.hour_freq = {h: 0 for h in range(24)}

        for i, row in df.loc[df["user"] == username].iterrows():
            timestamp, msg = row["timestamp"], row["message"]
            self.num_messages += 1
            if len(msg) > len(self.longest_msg): self.longest_msg = msg

            for word in msg.split():
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
        self.word_freq = dict(
            sorted(self.word_freq.items(), key=lambda x: x[1], reverse=True))
        self.emoji_freq = dict(
            sorted(self.emoji_freq.items(), key=lambda x: x[1], reverse=True))
        self.hour_freq = dict(
            sorted(self.hour_freq.items(), key=lambda x: x))


if __name__ == "__main__":
    print(User("Ansh", frame_data("testchat.txt")).hour_freq)