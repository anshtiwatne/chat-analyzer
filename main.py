"""Script to analyze WhatsApp chats"""

import dataclasses
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

    def __init__(self, username: str, messages: list[str] = []):

        self.username = username
        self.messages = messages

        self.longest_msg = ""
        self.num_messages = self.num_words = self.num_emojis = 0
        self.word_freq = self.emoji_freq = {}

        for msg in self.messages:
            self.num_messages += 1
            if not len(msg) > len(self.longest_msg): continue
            self.longest_msg = msg

            for word in msg.split():
                self.num_words += 1
                if word in self.word_freq: self.word_freq[word] += 1
                else: self.word_freq[word] = 1

                for char in word:
                    if not emoji.is_emoji(char): continue
                    self.num_emojis += 1
                    if char in self.emoji_freq: self.emoji_freq[char] += 1
                    else: self.emoji_freq[char] = 1

        if self.num_messages:
            self.avg_msg_len = self.num_words / self.num_messages
        self.word_freq = dict(
            sorted(self.word_freq.items(), key=lambda x: x[1], reverse=True))
        self.emoji_freq = dict(
            sorted(self.emoji_freq.items(), key=lambda x: x[1], reverse=True))


def populate_user_data():
    """Populates the user data"""

    df = frame_data("testchat.txt")
    users = [User(user) for user in df["user"].unique()]

    for i, row in df.iterrows():
        for user in users:
            if user.username != row["user"]: continue
            user.messages.append(row["message"])
            break
    print(users[0].messages)


if __name__ == "__main__":
    ...