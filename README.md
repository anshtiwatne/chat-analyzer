# WhatsApp Chat Analyzer

Get interesting statistics on WhatsApp chats

## Installation & Usage

Clone the repository and run the script or download the executable if on Windows

```powershell
python wordlesolver.py

Enter path to chat file: .\chats\testchat.txt
Is the date formatted as day first?: n
```

## Example

coming soon

## How it Works

Given a chat file, the script scrapes the chat to create a dataframe based on which and statistics on the chat are generated.

```python
def frame_data(path: str):
    """Scrapes Whatsapp chat export file and creates a dataframe"""

    with open(path, "r", encoding="UTF8") as file:
        # groups: date, time, meridiem, sender, message
        pattern = r"(\d*?/\d*?/\d*?), (\d*?:\d*?) ([Aa]|[Pp][Mm]) - (.*?): (.*)"
        data = pd.Series(file.read()).str.findall(pattern)[0]
    
    df = pd.DataFrame(columns=["timestamp", "user", "message"])
    for element in data:
        date, time, meridiem, sender, message = element
        time = f"{time} {meridiem}"
        if message in AUTOMATED_MESSAGES: message = ""
        timestamp = pd.to_datetime(f"{date} {time}", format=DT_FORMAT)
        df.loc[len(df)] = [timestamp, sender, message]

    return df
```

## License

[MIT](https://github.com/anshunderscore/chat_analyzer/blob/main/LICENSE)
