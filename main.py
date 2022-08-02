"""Script to analyze WhatsApp chats"""

import datetime
import emoji
import re


def get_data(path: str):
    """
    Reads in a file and returns a dataframe
    """

    with open(path, 'r', encoding="utf8") as file:
        pattern = r"(\d*?/\d*?/\d*?), (\d*?:\d*? [A, P]M) - (.*?): (.*)"
        data = re.findall(pattern, file.read())

    df = {"timestamp": [], "sender": [], "msg": []}

    for element in data:
        date, time, sender, message = element
        dt = datetime.datetime.strptime(f"{date} {time}", "%m/%d/%y %I:%M %p")

        df["timestamp"].append(dt)
        df["sender"].append(sender)
        df["msg"].append(message)

    return df


df = get_data("testchat.txt")


class User:
    """
    Class to represent a user
    """

    def __init__(self, name: str):

        self.name = name
        self.messages = []  # list of all of the user's messages in the chat
        for i, sender in enumerate(df["sender"]):
            if sender != self.name: continue
            self.messages.append(df["msg"][i])

        self.num_messages, self.num_words, self.num_emojis = 0, 0, 0
        self.word_freq, self.emoji_freq = {}, {}
        self.longest_msg = ""
        max_len = 0

        for msg in self.messages:
            self.num_messages += 1
            if len(msg) > max_len:
                max_len = len(msg)
                self.longest_msg = msg

            for word in msg.split():
                self.num_words += 1
                if word not in self.word_freq: self.word_freq[word] = 1
                else: self.word_freq[word] += 1

                for char in word:
                    if not emoji.is_emoji(char): continue
                    self.num_emojis += 1
                    if char not in self.emoji_freq: self.emoji_freq[char] = 1
                    else: self.emoji_freq[char] += 1

        self.word_emoji_ratio = self.num_emojis / self.num_words
        self.avg_msg_len = self.num_words / self.num_messages  # words per message
        self.word_freq = dict(
            sorted(self.word_freq.items(), key=lambda x: x[1], reverse=True))
        self.emoji_freq = dict(
            sorted(self.emoji_freq.items(), key=lambda x: x[1], reverse=True))

        hours = {hour:0 for hour in range(0, 24)}
        for timestamp in df["timestamp"]:
            print(timestamp)

ansh = User("Ansh")