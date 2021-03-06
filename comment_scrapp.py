import time

import pandas as pd
from bs4 import BeautifulSoup 
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from googleapiclient.discovery import build
from tqdm import tqdm

from utils import load_json


def get_param(url):
    url, params = url.split('?')
    params = [
        value.split('=')
        for value in params.split("&")
    ]
    params = {
        k: v
        for k, v in params
    }
    return params


def get_video_ids(playlist_urls):
    result = []
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
    
    for playlist_url in tqdm(playlist_urls):
        driver.get(playlist_url)
        
        latest_cnt = 0
        elements = []
        
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            elements = driver.find_elements_by_css_selector("#video-title")
            
            if len(elements) == latest_cnt:
                break
            
            latest_cnt = len(elements)
        
        result += [get_param(element.get_attribute('href'))['v'] for element in elements]

    driver.close()
    
    return result


def scrap_comments(video_ids, token):
    api_obj = build('youtube', 'v3', developerKey=token)
    
    comments = list()

    for video_id in tqdm(video_ids):
        result = []

        video = api_obj.videos().list(part='snippet', id=video_id).execute()
        title = video['items'][0]['snippet']['title']
        desc = video['items'][0]['snippet']['description']
        channel_title = video['items'][0]['snippet']['channelTitle']

        try:
            response = api_obj.commentThreads().list(part='snippet,replies', videoId=video_id, maxResults=100).execute()
        except Exception as e:
            print(e)

        while response:
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                result.append([comment['authorDisplayName'], comment['publishedAt'], comment['textOriginal']])

                if item['snippet']['totalReplyCount'] > 0:
                    for reply_item in item['replies']['comments']:
                        reply = reply_item['snippet']
                        result.append([reply['authorDisplayName'], reply['publishedAt'], reply['textOriginal']])

            if 'nextPageToken' in response:
                response = api_obj.commentThreads().list(part='snippet,replies', videoId=video_id, pageToken=response['nextPageToken'], maxResults=100).execute()
            else:
                break

        result = [
            [title, desc, channel_title] + [BeautifulSoup(col, 'html.parser').text for col in row]
            for row in result
        ]
        comments.append(result)

    return sum(comments, [])


def main(cfg):
    video_ids = get_video_ids(cfg['playlist_urls'])
    comments = scrap_comments(video_ids, cfg['youtube_token'])
    
    df = pd.DataFrame(comments, columns=['title', 'desc', 'channel', 'name', 'time', 'original_comment'])
    df['desc'] = df['desc'].apply(lambda x: x.replace("\n", " ").strip())
    df['original_comment'] = df['original_comment'].apply(lambda x: x.replace("\n", " ").strip())
    df['time'] = df['time'].apply(lambda x: x.replace("T", " ").replace("Z", ""))
    
    print(df.shape)
    print(df.head())
    
    df.to_excel("resource/ine_coment.xlsx", index=None)


if __name__ == "__main__":
    cfg = load_json("config.json")
    main(cfg)
    