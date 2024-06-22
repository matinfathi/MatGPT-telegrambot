from embedding import classification
from constants import HACKER_NEWS_URL
from utils import HNRecord, logger

from bs4 import BeautifulSoup
import requests

from datetime import datetime
from typing import Optional, List
import re


def remove_urls(text):
    # Define a regex pattern to match URLs inside parentheses
    pattern = r'\([^()]*\)'

    # Use re.sub() to replace matched URLs with an empty string
    cleaned_text = re.sub(pattern, '', text)

    return cleaned_text


def parse_time(entry: BeautifulSoup) -> datetime.fromtimestamp:
    time_tag = entry.find("a", class_="hn span3 story")
    if time_tag and time_tag.has_attr("data-date"):
        timestamp = int(time_tag["data-date"])
        time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    else:
        time = None

    return time


def get_today_news(
        total_list: List[HNRecord],
        target_date: Optional[datetime] = datetime.today().strftime('%Y-%m-%d'),
        num_return: int = 10,
) -> List[HNRecord]:
    today_news = []
    for item in total_list:
        date_date = datetime.strptime(item.date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')

        if date_date == target_date:
            today_news.append(item)

    return sorted(today_news, key=lambda x: x.points, reverse=True)[:num_return]


def get_high_point_news(
        total_list: List[HNRecord],
        num_return: int = 10,
) -> List[HNRecord]:
    return sorted(total_list, key=lambda x: x.points, reverse=True)[:num_return]


def get_high_comment_news(
        total_list: List[HNRecord],
        num_return: int = 10,
) -> List[HNRecord]:
    return sorted(total_list, key=lambda x: x.comments, reverse=True)[:num_return]


def get_ai_news(
        total_list: List[HNRecord],
        num_return: int = 10,
) -> List[HNRecord]:
    texts = [item.title for item in total_list]
    labels = classification(texts, threshold=0.4)
    ai_list = [total_list[idx] for idx in range(len(total_list)) if labels[idx] == "AI"]
    max_lim = max(len(ai_list), num_return)
    return sorted(ai_list, key=lambda x: x.comments, reverse=True)[:max_lim]


def get_linux_news(
        total_list: List[HNRecord],
        num_return: int = 10,
) -> List[HNRecord]:
    texts = [item.title for item in total_list]
    labels = classification(texts, threshold=0.35)
    ai_list = [total_list[idx] for idx in range(len(total_list)) if labels[idx] == "Linux"]
    max_lim = max(len(ai_list), num_return)
    return sorted(ai_list, key=lambda x: x.comments, reverse=True)[:max_lim]


def get_news(
        url: Optional[str] = HACKER_NEWS_URL,
) -> List[HNRecord]:
    total_news = []
    response = requests.get(url)
    logger.info(f"The status code for scraping is {response}")
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
    else:
        raise Exception(f"Error in getting website content with status code: {response.status_code}")

    entries = soup.find_all("li", class_="entry row")
    logger.info(f"The length of scraped list is {len(entries)}")

    for entry in entries:
        story_link_tag = entry.find("a", class_="link span15 story")
        if story_link_tag:
            link = story_link_tag.get("href")
            title = remove_urls(story_link_tag.get_text(strip=True))
            short_link = link.split('/')[2] if link else None
        else:
            link = None
            title = None
            short_link = None

        comments_tag = entry.find("span", class_="comments span2")
        comments = int(comments_tag.get_text(strip=True)) if comments_tag and comments_tag.get_text(strip=True) else 0

        points_tag = entry.find("span", class_="points span1")
        points = int(points_tag.get_text(strip=True)) if points_tag and points_tag.get_text(strip=True) else 0

        time = parse_time(entry)

        if title and link and time:
            total_news.append(
                HNRecord(title=title, url=link, points=points, comments=comments, date=time, short_url=short_link))

    logger.info(f"Length returned data is {len(total_news)}")

    return sorted(total_news, key=lambda x: x.date, reverse=True)


#
#
# scrape = get_news(url=HACKER_NEWS_URL)
# aa = get_ai_news(scrape)
#
# for a in aa:
#     print(a)
# print(scrape[0])
