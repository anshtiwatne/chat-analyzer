"""Script to analyze WhatsApp chats"""

import datetime
import re


def get_data(path: str):
    """
    Reads in a file and returns a dataframe
    """

    with open(path, 'r', encoding="utf8") as file:
        pattern = r"(\d*?/\d*?/\d*?), (\d*?:\d*? [A, P]M) - (.*?): (.*)"
        data = re.findall(pattern, file.read())

    df = {"dt": [], "sender": [], "msg": []}

    for element in data:
        date, time, sender, message = element
        dt = datetime.datetime.strptime(f"{date} {time}", "%m/%d/%y %I:%M %p")

        df["dt"].append(dt)
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

        messages = []
        for i, sender in enumerate(df["sender"]):
            if sender != self.name: continue
            messages.append(df["msg"][i])

        self.messages = messages
        self.average_msg_length = sum(len(msg) for msg in self.messages) / len(self.messages)
        self.longest_msg = max(self.messages, key=len)
        self.words_typed = sum(len(msg.split()) for msg in self.messages)
        self.top_words = sorted(set(word for msg in self.messages for word in msg.split()), key=lambda x: x.lower())
        # we could add a few more of these, like time of day most texted, etc.

    @property
    def get_name(self):
        """
        Returns the user's name
        """

        return self.name