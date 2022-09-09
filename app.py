import flet
from flet import *
from flet import icons, FilePicker, FilePickerResultEvent
import whatstats


def main(page: Page):
    page.title = "WhatStats"
    page.scroll = "always"

    def pick_files_result(e: FilePickerResultEvent):
        filename.value = " ,".join(map(lambda f: f.name, e.files)) if e.files else "Cancelled!"
        path.value = " ,".join(map(lambda f: f.path, e.files)) if e.files else None
        filename.update()
        analyze_chat()

    pick_files_dialog = FilePicker(on_result=pick_files_result)
    filename = Text()
    path = Text()
    page.overlay.append(pick_files_dialog)

    page.add(
        Row([
            ElevatedButton(
                "Pick files",
                icon=icons.UPLOAD_FILE,
                on_click=lambda _: pick_files_dialog.pick_files(),
            ), filename
        ]))

    def analyze_chat():
        df = whatstats.frame_data(path.value)
        result = whatstats.main(df)
        page.add(Text(result))


flet.app(target=main)