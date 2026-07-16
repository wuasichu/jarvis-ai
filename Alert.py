from pathlib import Path
from winotify import Notification, audio

_ICON = Path(__file__).parent / "logo.png"

def Alert(Text):
    icon_path = str(_ICON) if _ICON.exists() else ""

    toast = Notification(
        app_id="🟢 J.A.R.V.I.S.",
        title=Text,
        duration="long",
        icon=icon_path
    )

    toast.set_audio(audio.Default, loop=False)


    toast.add_actions(label="Click me", launch="https://www.google.com")
    toast.add_actions(label="Dismiss", launch="https://www.google.com")


    toast.show()

