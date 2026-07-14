import requests
from bs4 import BeautifulSoup
import os
import re

base_url = "https://cap.rcpet.edu.tw/"
output_dir = "pdfs"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def get_file_id(url):
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    return None

def download_file(url, filepath):
    if os.path.exists(filepath):
        print(f"Skipping {filepath}, already exists.")
        return
        
    file_id = get_file_id(url)
    if file_id:
        direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        print(f"Downloading {filepath}...")
        try:
            res = requests.get(direct_url)
            if res.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(res.content)
            else:
                print(f"Failed to download {filepath}: HTTP {res.status_code}")
        except Exception as e:
            print(f"Error downloading {filepath}: {e}")
    else:
        print(f"Could not extract file ID from {url}")

def create_url_shortcut(url, filepath):
    # Windows .url file format
    if os.path.exists(filepath):
        print(f"Skipping {filepath}, already exists.")
        return
        
    print(f"Creating shortcut {filepath}...")
    content = f"[InternetShortcut]\nURL={url}\n"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def fetch_cap_exams():
    print("Fetching CAP exams...")
    
    # 會考是從 103 到 115
    for year in range(103, 116):
        url = f"{base_url}exam/{year}/{year}exam.html"
        try:
            res = requests.get(url)
            res.encoding = 'utf-8' # 網頁是 utf-8 編碼
            
            if res.status_code != 200:
                print(f"Failed to fetch {url}: HTTP {res.status_code}")
                continue
                
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # The structure is usually tables or a list of links
            # We'll map the text of the link to our naming convention
            links = soup.find_all('a', href=True)
            for link in links:
                text = link.get_text(strip=True)
                href = link['href']
                
                if 'drive.google.com' not in href and '.pdf' not in href and '.mp3' not in href:
                    continue
                
                # Default unknown type
                subject = "未知"
                file_type = "試卷"
                
                if '國文' in text: subject = '國文'
                elif '英語' in text or '英文' in text: subject = '英文'
                elif '數學' in text: subject = '數學'
                elif '社會' in text: subject = '社會'
                elif '自然' in text: subject = '自然'
                elif '寫作' in text: subject = '寫作測驗'
                
                # Determine file type
                if '答案' in text or '解答' in text or '參考答案' in text: file_type = '答案'
                elif '試題' in text or '題本' in text or '試卷' in text: file_type = '試卷'
                elif '聽力' in text or '音檔' in text: file_type = '聽力音檔'
                
                # Some links just say "國文", "英語", which means it's the 試題本
                if text in ['國文', '英語', '英語(閱讀)', '數學', '社會', '自然', '寫作測驗']:
                    file_type = '試卷'
                if '英語(聽力)' in text:
                    subject = '英文'
                    file_type = '聽力試卷'
                    
                # Hardcode check for the common "參考答案" link which applies to all subjects
                if text == '參考答案':
                    subject = '全部'
                    file_type = '答案'
                if text == '試題':
                    subject = '全部'
                    file_type = '試卷'
                    
                # Some items might be just "題目"
                
                # MP3 Check
                is_mp3 = '.mp3' in href or '音檔' in text or '聽力' in text
                
                if is_mp3:
                    filename = f"{year}-會考{subject}-{file_type}.url"
                    filepath = os.path.join(output_dir, filename)
                    create_url_shortcut(href, filepath)
                else:
                    filename = f"{year}-會考{subject}-{file_type}.pdf"
                    filepath = os.path.join(output_dir, filename)
                    if 'drive.google.com' in href:
                        download_file(href, filepath)
                    else:
                        # Direct PDF link
                        if not href.startswith('http'):
                            # Resolve relative URL
                            if href.startswith('../../'):
                                direct_url = base_url + href[6:]
                            else:
                                direct_url = f"{base_url}exam/{year}/{href}"
                        else:
                            direct_url = href
                        
                        if os.path.exists(filepath):
                            print(f"Skipping {filepath}")
                            continue
                        
                        print(f"Downloading direct PDF {filepath}...")
                        r = requests.get(direct_url)
                        if r.status_code == 200:
                            with open(filepath, 'wb') as f:
                                f.write(r.content)
                                
        except Exception as e:
            print(f"Error fetching {year}: {e}")

if __name__ == "__main__":
    fetch_cap_exams()
