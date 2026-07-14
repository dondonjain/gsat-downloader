import os
import json
import urllib.parse

def generate_metadata():
    pdfs_dir = 'pdfs'
    api_dir = 'api'
    
    if not os.path.exists(api_dir):
        os.makedirs(api_dir)

    base_url = "https://dondonjain.github.io/gsat-downloader/pdfs/"
    files_metadata = []

    for filename in os.listdir(pdfs_dir):
        if not filename.endswith(('.pdf', '.url')):
            continue
            
        filepath = os.path.join(pdfs_dir, filename)
        file_size = os.path.getsize(filepath)
        
        # 檔名格式: 113-學測國文-試卷.pdf 或 113-會考全部-答案.pdf
        # 解析年份, 考試類別與科目, 文件類型
        parts = filename.replace('.pdf', '').replace('.url', '').split('-')
        
        if len(parts) >= 3:
            year = parts[0]
            # parts[1] might be "學測國文", we need to extract category and subject
            category_subject = parts[1]
            if category_subject.startswith('學測'):
                category = '學測'
                subject = category_subject[2:]
            elif category_subject.startswith('分科測驗'):
                category = '分科測驗'
                subject = category_subject[4:]
            elif category_subject.startswith('會考'):
                category = '會考'
                subject = category_subject[2:]
            else:
                category = '未知'
                subject = category_subject
                
            file_type = parts[2]
            # URL Encoding is needed if other AIs try to fetch directly
            url = base_url + urllib.parse.quote(filename)
            
            files_metadata.append({
                "year": int(year) if year.isdigit() else year,
                "examCategory": category,
                "subject": subject,
                "type": file_type,
                "filename": filename,
                "url": url,
                "size_bytes": file_size
            })

    output_data = {
        "description": "台灣歷屆大考(學測/分科/會考)試題下載 API",
        "total_files": len(files_metadata),
        "data": files_metadata
    }

    with open(os.path.join(api_dir, 'files.json'), 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"Generated api/files.json with {len(files_metadata)} files.")

if __name__ == '__main__':
    generate_metadata()
