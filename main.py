from typing import TypedDict, Literal
from tinytag import TinyTag
from pathlib import Path

import requests, time, os

ENDPOINT = "https://lrclib.net/api"


def yes_or_no(msg: str) -> bool:
    choice = input(f"{msg} [Y/n] ")
    if choice.lower() in ["yes", "y", ""]:
        return True
    elif choice.lower() in ["no", "n"]:
        return False
    else:
        return True


def color(text: str, code: str):
    return f"\033[{code}m{text}\033[0m"


def red(text: str):
    return color(text, "31")


def green(text: str):
    return color(text, "32")


def magenta(text: str):
    return color(text, "35")


class LrcResponse(TypedDict):
    id: str
    trackName: str
    artistName: str
    albumName: str
    duration: float
    plainLyrics: str | None
    syncedLyrics: str | None
    instrumental: bool


def search_lyrics(track: str, artist: str, album: str) -> list[LrcResponse] | None:
    """Returns a maximum of 20 results for the given parametres"""

    params = {
        "track_name": track,
        "artist_name": artist,
        "album_name": album,
    }

    res = requests.get(f"{ENDPOINT}/search", params=params, timeout=60)

    if res.status_code != 200:
        print(f"API error: {res.status_code}")
        return None

    return res.json()


def main():

    def save_to_lrc_file(
        filename: str, content: str | None, lyrics_type: Literal["Synced", "Plain"]
    ):
        with open(f"{filename}.lrc", "w") as f:
            f.write(content or "")
            print(
                f"✅ Saved to {green(f.name)} -> {red(lyrics_type) if lyrics_type == 'Plain' else lyrics_type}"
            )

    print("Powered by https://lrclib.net")
    auto_mode_enabled = yes_or_no("Save lyrics automatically?")

    for file in Path(".").iterdir():
        if file.suffix in [".flac", ".mp3", ".ogg", ".wav"]:

            time.sleep(0.7)

            print("\n--------------------------------------------")
            print(f"Searching for {magenta(file.name)}...")

            # Lyrics file already exists
            if os.path.exists(f"{file.stem}.lrc"):
                if auto_mode_enabled:
                    print("Lyrics file already exists, skipping")
                    continue

                if yes_or_no("Lyrics file already exists, overwrite?"):
                    pass
                else:
                    continue

            # Fetch
            tag = TinyTag.get(file.name)
            results = search_lyrics(
                tag.title or file.stem, tag.artist or "", tag.album or ""
            )

            if not results:
                print(red(f"No results for {file.name}"))
                continue

            for index, song in enumerate(results):

                if song["instrumental"]:
                    print("Song is instrumental, skipping")
                    break

                # Automatic saving
                if auto_mode_enabled:
                    if song["syncedLyrics"]:
                        save_to_lrc_file(file.stem, song["syncedLyrics"], "Synced")
                        break

                    # Settle for the last plain result if there are no synced lyrics at all
                    if index + 1 == len(results):
                        save_to_lrc_file(file.stem, song["plainLyrics"], "Plain")
                        break

                    continue  # Continue looking until synced lyrics are found

                # Manual info check and saving
                if song["syncedLyrics"]:
                    print(f"\n{song['syncedLyrics']}")
                else:
                    print(f"\n{song['plainLyrics']}")

                print("\n--------------------------------------------")
                print(
                    f"Lyrics type: {green('Synced') if song['syncedLyrics'] else red('Plain')}"
                )
                print(f"Track: {green(song['trackName'])}")
                print(f"Album: {green(song['albumName'])}")
                print(f"Artist: {green(song['artistName'])}")
                print(f"Duration: {green(song['duration'])}")
                print(f"ID: {green(song['id'])}")
                print(f"Index: {green(index + 1)}/{green(len(results))}")

                if index + 1 < len(results) and len(results) > 1:
                    if yes_or_no("\nSkip?"):
                        continue

                if yes_or_no("Save to file?"):
                    save_to_lrc_file(
                        file.stem,
                        song["syncedLyrics"] or song["plainLyrics"],
                        "Synced" if song["syncedLyrics"] else "Plain",
                    )

                    break
                else:
                    break


if __name__ == "__main__":
    main()
