import requests

from utils import logger
from cohere import Cohere

from youtube_transcript_api import YouTubeTranscriptApi


def get_video_transcript(youtube_url: str) -> str:
    video_id = youtube_url.split("v=")[-1]

    proxies = {
        'http': 'socks5://bfwdtqgb:4syygf6nic68@167.160.180.203:6754',
        'https': 'socks5://bfwdtqgb:4syygf6nic68@167.160.180.203:6754'
    }

    result = YouTubeTranscriptApi.get_transcript(video_id, proxies=proxies)

    text = ""
    for item in result:
        text += item["text"] + " "

    return text


def get_video_transcript_2(youtube_url: str) -> str:
    video_id = youtube_url.split("v=")[-1]

    import requests

    url = "https://youtube-transcriptor.p.rapidapi.com/transcript"

    querystring = {"video_id": video_id, "lang": "en"}

    headers = {
        "x-rapidapi-key": "1d1c5c600emsh6b90065391de81ap145c20jsn2e17abd1bfaa",
        "x-rapidapi-host": "youtube-transcriptor.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    return response.json()[0]["transcriptionAsText"]


def video_summarize(youtube_url: str) -> str:
    cohere = Cohere()
    try:
        transcript = get_video_transcript(youtube_url)
        logger.info(f"Got the video transcript with length {len(transcript.split())}")
    except Exception as e:
        logger.info(f"Not able to get transcript. {e}")
        return "I'm not able to get the transcript of this video."
    if len(transcript.split()) > 10000:
        return "The video is too long."

    prompt = f"""\
{transcript}

This is a transcript for a video, I want you to provide for me a nice bullet point list of the most important points \
in the video. Make the list explicit and understandable. for each point about a paragraph. like this: 
- **sub topic**: description
- **sub topic**: description
..."""

    answer = cohere.query(prompt=prompt)

    logger.info(f"Got the answer with length {len(answer.split())}")

    return answer



def video_summarize_short(youtube_url: str) -> str:
    cohere = Cohere()
    try:
        transcript = get_video_transcript(youtube_url)
        logger.info(f"Got the video transcript with length {len(transcript.split())}")
    except Exception as e:
        logger.info(f"Not able to get transcript. {e}")
        return "I'm not able to get the transcript of this video."
    if len(transcript.split()) > 10000:
        return "The video is too long."

    prompt = f"""\
{transcript}

This is a transcript for a video, I want you to provide for me a simple summary of the video, Generate a paragraph \
that summarizes the video in a few sentences. Make sure to include the main points of the video. like this:
- **summary**: description"""

    answer = cohere.query(prompt=prompt)

    logger.info(f"Got the answer with length {len(answer.split())}")

    return answer


# print(get_video_transcript("https://www.youtube.com/watch?v=GFE8qfwN23U"))
