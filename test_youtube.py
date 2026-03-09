import yt_dlp

ydl_opts = {
    "quiet": True,
    "extract_flat": True
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info("https://www.youtube.com/@TwoMinutePapers/videos", download=False)

    for video in info["entries"][:5]:
        print(video["title"])