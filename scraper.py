import requests
from bs4 import BeautifulSoup
import urllib3
import urllib.parse
import os
import re
import tempfile
import zipfile

urllib3.disable_warnings()

BASE_URL = 'https://www.ceec.edu.tw'
# CEEC list url for general past papers
LIST_URL_TEMPLATE = 'https://www.ceec.edu.tw/xmfile?xsmsid=0J052424829869345634&page={}'

def extract_year(filename):
    numbers = re.findall(r'\d+', filename)
    for num_str in numbers:
        num = int(num_str)
        if 80 <= num <= 115:
            return str(num)
    return None

def get_type_by_name(filename):
    if '答題卷' in filename:
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

def download_and_zip(subject: str, start_year: int, end_year: int):
    """
    Scrape, download and zip the requested files.
    Returns the path to the zip file.
    """
    session = requests.Session()
    session.verify = False

    temp_dir = tempfile.mkdtemp()
    downloaded_files = []

    # Map the user subject input to what appears in the filenames
    subject_map = {
        "國文": ["國文", "國語文", "國綜", "國寫"],
        "英文": ["英文"],
        "數學A": ["數學a", "數學 A"],
        "數學B": ["數學b", "數學 B"],
        "數學": ["數學"],  # Older ones
        "社會": ["社會"],
        "自然": ["自然"]
    }
    
    keywords = subject_map.get(subject, [subject])
    if subject in ["數學A", "數學B"]:
        keywords.append("數學") # might need to catch general 數學 for older years if desired, but let's stick to exact if possible. Actually older ones just have "數學"

    # We will search up to 20 pages
    for page in range(1, 20):
        url = LIST_URL_TEMPLATE.format(page)
        r = session.get(url)
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
            
            if not decoded_href.endswith('.pdf'):
                continue
            if '學測' not in decoded_href:
                continue
                
            # Check subject
            matched_subject = False
            for kw in keywords:
                if kw.lower() in decoded_href:
                    matched_subject = True
                    break
                    
            if not matched_subject:
                # for older papers, they might just be e.g. 89年學測自然科.pdf
                pass
            
            if matched_subject:
                filename = decoded_href.split('/')[-1]
                year_str = extract_year(filename)
                if not year_str:
                    continue
                year = int(year_str)
                
                if start_year <= year <= end_year:
                    # Determine new name
                    file_type = get_type_by_name(filename)
                    new_filename = f"{year}-學測{subject}-{file_type}.pdf"
                    
                    filepath = os.path.join(temp_dir, new_filename)
                    
                    # Handle duplicates
                    base_name = new_filename[:-4]
                    suffix = 1
                    while os.path.exists(filepath):
                        filepath = os.path.join(temp_dir, f"{base_name}_{suffix}.pdf")
                        suffix += 1
                    
                    # Download
                    full_url = href if href.startswith('http') else BASE_URL + href
                    res = session.get(full_url, stream=True)
                    if res.status_code == 200:
                        with open(filepath, 'wb') as f:
                            for chunk in res.iter_content(1024):
                                f.write(chunk)
                        downloaded_files.append(filepath)

    # Create ZIP
    zip_path = os.path.join(tempfile.gettempdir(), f"GSAT_{subject}_{start_year}_{end_year}.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f in downloaded_files:
            zipf.write(f, os.path.basename(f))
            
    # Cleanup temp files
    for f in downloaded_files:
        try:
            os.remove(f)
        except:
            pass
    try:
        os.rmdir(temp_dir)
    except:
        pass

    return zip_path
