from constants import HACKER_NEWS_URL
from utils import HNRecord, logger
from cohere import Cohere

from bs4 import BeautifulSoup
import numpy as np
import requests

from datetime import datetime
from typing import Optional, List
import re

cohere = Cohere()


def load_embeddings() -> np.array:
    ai_news = cohere.embedding([
        "OpenAI Unveils GPT-5: The Future of Conversational AI: OpenAI has released its latest language model, GPT-5, "
        "promising groundbreaking improvements in natural language understanding and generation.",
        "Hugging Face Releases New Transformer Models for Multilingual NLP: Hugging Face has launched new transformer "
        "models specifically designed for multilingual natural language processing, enhancing global communication "
        "and accessibility.",
        "AI Breakthrough in Computer Vision: New Model Achieves Human-Level Accuracy: Researchers have developed an "
        "AI model that matches human-level accuracy in image recognition tasks, revolutionizing the field of computer "
        "vision.",
        "Large Language Models Revolutionize Content Creation: The rise of large language models (LLMs) is "
        "transforming content creation, enabling automated writing, translation, and more.",
        "Advances in NLP Enable Real-Time Sentiment Analysis: Recent advancements in natural language processing are "
        "now allowing businesses to perform real-time sentiment analysis, improving customer feedback and engagement "
        "strategies.",
        "AI-Powered Predictive Analytics Transform Healthcare: AI and machine learning are making significant strides "
        "in healthcare, particularly in predictive analytics for disease prevention and patient care optimization.",
        "Hugging Face Introduces New Tools for AI Model Deployment: Hugging Face has unveiled a suite of new tools "
        "designed to simplify the deployment of AI models, making it easier for developers to integrate advanced AI "
        "into their applications.",
        "OpenAI's DALL-E 3 Generates Stunning, Realistic Images from Text: OpenAI's latest iteration of DALL-E "
        "continues to push the boundaries of AI-generated art, producing highly realistic images from textual "
        "descriptions.",
        "Transformers in NLP: New Developments and Applications: The transformer architecture continues to dominate "
        "NLP research, with new developments expanding its applications in various fields, from translation to "
        "sentiment analysis.",
        "AI Ethics and Fairness: Addressing Bias in Machine Learning: Ongoing research and initiatives are focused on "
        "tackling biases in machine learning algorithms, ensuring fairer and more equitable AI systems."
    ])

    linux_news = cohere.embedding([
        "Linux Kernel 6.0 Released: What’s New and Improved: The latest version of the Linux kernel, 6.0, "
        "has been released, featuring numerous enhancements and new features aimed at improving performance and "
        "security.",
        "GNU Project Celebrates 40 Years of Free Software: The GNU Project marks its 40th anniversary, reflecting on "
        "its journey and impact on the free software movement and the open-source community.",
        "Unix-Based Systems See Surge in Adoption for Enterprise Solutions: Unix-based systems are experiencing a "
        "resurgence in popularity within enterprise environments due to their robustness, security, and scalability.",
        "Major Linux Distributions Announce Collaboration for Unified Desktop Environment: Leading Linux "
        "distributions have announced a collaborative effort to create a unified and user-friendly desktop "
        "environment, aiming to streamline the Linux experience for new users.",
        "Open Source Initiative: Enhancing Security in Linux and GNU Systems: A new initiative focuses on bolstering "
        "security measures within Linux and GNU systems, addressing vulnerabilities, and ensuring safer open-source "
        "software development.",
        "Red Hat Enterprise Linux 9 Released: What to Expect: Red Hat has officially launched Enterprise Linux 9, "
        "packed with new features and improvements aimed at providing a more secure and efficient enterprise "
        "environment.",
        "Debian 12 'Bookworm' Release Candidate Announced: The Debian Project has announced the release candidate for "
        "Debian 12 'Bookworm', bringing a host of new features and updates for users.",
        "KDE Plasma 6.0: A Sneak Peek at Upcoming Features: KDE developers have given a sneak peek into the features "
        "of the upcoming KDE Plasma 6.0, promising a more polished and user-friendly experience.",
        "Ubuntu 22.04 LTS 'Jammy Jellyfish' Now Available: Canonical has released Ubuntu 22.04 LTS 'Jammy Jellyfish', "
        "offering long-term support and a range of improvements for stability and performance.",
        "Linux Foundation Launches New Open Source Security Project: The Linux Foundation has announced a new project "
        "aimed at improving the security of open-source software, addressing critical vulnerabilities, and enhancing "
        "the overall security landscape."
    ])

    return ai_news, linux_news


def cosine_similarity(vector, matrix) -> float:
    vector_norm = vector / np.linalg.norm(vector)

    matrix_norm = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)

    cosine_similarities = np.max(np.dot(matrix_norm, vector_norm))

    return cosine_similarities


def cosine_similarity_matrix(matrix1, matrix2):
    # Normalize the matrices
    matrix1_norm = matrix1 / np.linalg.norm(matrix1, axis=1, keepdims=True)
    matrix2_norm = matrix2 / np.linalg.norm(matrix2, axis=1, keepdims=True)

    # Compute the cosine similarity
    return np.dot(matrix1_norm, matrix2_norm.T)


def dot_product_similarity_matrix(matrix1, matrix2):
    # Compute the dot product similarity
    return np.dot(matrix1, matrix2.T)


def classification(list_news: List[str], threshold: float = 0.4) -> List[str]:
    list_news_embedding = cohere.embedding(list_news)

    ai_router_embedding, linux_router_embedding = load_embeddings()

    similarity_A_B = cosine_similarity_matrix(list_news_embedding, ai_router_embedding)
    similarity_A_C = cosine_similarity_matrix(list_news_embedding, linux_router_embedding)

    max_similarity_B = np.max(similarity_A_B, axis=1)
    max_similarity_C = np.max(similarity_A_C, axis=1)

    all_similarities = np.vstack((max_similarity_B, max_similarity_C)).T

    mask = np.max(all_similarities, axis=1) >= threshold

    most_similar_indices = np.full(all_similarities.shape[0], -1, dtype=int)
    most_similar_indices[mask] = np.argmax(all_similarities[mask], axis=1)
    matrix_labels = np.array(['AI', 'Linux', None])
    most_similar_matrix = matrix_labels[most_similar_indices]

    return most_similar_matrix.tolist()


def remove_urls(text):
    pattern = r'\([^()]*\)'
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
