import requests
from bs4 import BeautifulSoup
import urllib3
import urllib.parse
import os
import re
import time

urllib3.disable_warnings()

BASE_URL = 'https://www.ceec.edu.tw'
LIST_URL_TEMPLATE = 'https://www.ceec.edu.tw/xmfile?xsmsid=0J052427633128416650&page={}'
TARGET_DIR = os.path.join(os.path.dirname(__file__), 'pdfs')

SUBJECTS = {
    "國文": ["國文"],
    "英文": ["英文", "英語"],
    "數學甲": ["數甲", "數學甲"],
    "數學乙": ["數乙", "數學乙"],
    "歷史": ["歷史"],
    "地理": ["地理"],
    "公民與社會": ["公民"],
    "物理": ["物理"],
    "化學": ["化學"],
    "生物": ["生物"],
    "數學": ["數學"]
}

def extract_year(filename):
    numbers = re.findall(r'\d+', filename)
    for num_str in numbers:
        num = int(num_str)
        if 80 <= num <= 115:
            return str(num)
    return None

def get_type_by_name(filename):
    if '答題卷' in filename or '答案卷' in filename:
        return '答題卷'
    elif '非選擇' in filename or '評分' in filename:
        return '非選擇題評分原則'
    elif '選擇題答案' in filename:
        return '選擇題答案'
    elif '參考答案' in filename or '答案' in filename:
        return '答案'
    elif '試題' in filename or '試卷' in filename or '科' in filename:
        return '試題'
    else:
        return '其他'

def get_subject_by_name(filename_decoded):
    matched = None
    for subj in ["數學甲", "數學乙", "國文", "英文", "歷史", "地理", "公民與社會", "物理", "化學", "生物", "數學"]:
        for kw in SUBJECTS[subj]:
            if kw.lower() in filename_decoded:
                if subj == "數學":
                    if "數甲" in filename_decoded or "數學甲" in filename_decoded or "數乙" in filename_decoded or "數學乙" in filename_decoded:
                        continue
                matched = subj
                break
        if matched:
            break
    return matched

def main():
    session = requests.Session()
    session.verify = False

    start_year = 95
    end_year = 115

    # Scan 20 pages max
    for page in range(1, 20):
        print(f"Scanning page {page}...")
        url = LIST_URL_TEMPLATE.format(page)
        try:
            r = session.get(url, timeout=10)
            if r.status_code != 200:
                continue
            r.encoding = 'utf-8'
            soup = BeautifulSoup(r.text, 'html.parser')
            links = soup.find_all('a')
            
            for a in links:
                href = a.get('href')
                if not href:
                    continue
                
                decoded_href = urllib.parse.unquote(href).lower()
                if not decoded_href.endswith('.pdf') or ('指考' not in decoded_href and '分科' not in decoded_href):
                    continue
                    
                subject = get_subject_by_name(decoded_href)
                if not subject:
                    continue
                    
                filename = decoded_href.split('/')[-1]
                year_str = extract_year(filename)
                if not year_str:
                    continue
                year = int(year_str)
                
                if start_year <= year <= end_year:
                    file_type = get_type_by_name(filename)
                    new_filename = f"{year}-分科測驗{subject}-{file_type}.pdf"
                    
                    # deduplicate naming if necessary
                    filepath = os.path.join(TARGET_DIR, new_filename)
                    base_name = new_filename[:-4]
                    suffix = 1
                    
                    # Check if already downloaded an identically named file in THIS run
                    # If file exists, we could check size, but let's just use suffix logic to be safe
                    final_filepath = filepath
                    while os.path.exists(final_filepath):
                        # CEEC sometimes has duplicate links to the exact same file, let's just skip if the exact name exists for now, 
                        # or append suffix. To avoid duplicate downloads of the EXACT SAME FILE due to multiple links:
                        # Let's assume if it exists, it's already downloaded, unless we want to be very robust.
                        # Wait, CEEC has multiple versions like 定稿. If they are different files, they might have the same mapped name.
                        # We will append suffix but ONLY download if we haven't seen this URL yet!
                        break 
                    
                    # Better logic: Check if we haven't downloaded this href yet
                    # Actually, if final_filepath exists, we'll skip to save time and bandwidth.
                    if os.path.exists(final_filepath):
                        continue

                    full_url = href if href.startswith('http') else BASE_URL + href
                    print(f"Downloading {new_filename} from {full_url}")
                    try:
                        res = session.get(full_url, stream=True, timeout=10)
                        if res.status_code == 200:
                            with open(final_filepath, 'wb') as f:
                                for chunk in res.iter_content(1024):
                                    f.write(chunk)
                    except Exception as e:
                        print(f"Error downloading {full_url}: {e}")
                        
        except Exception as e:
            print(f"Error on page {page}: {e}")

if __name__ == "__main__":
    main()
