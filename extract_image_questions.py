"""
從 chapters 目錄的各章節 docx 提取有圖片的題目
並更新 questions.js
"""

from docx import Document
from docx.oxml.ns import qn
import re
import json
import os
import zipfile
from pathlib import Path

def convert_chinese_num(s):
    """轉換中文數字"""
    chinese_nums = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
    if s == '十':
        return 10
    elif len(s) == 2 and s.startswith('十'):
        return 10 + chinese_nums.get(s[1], 0)
    elif len(s) == 2 and s.endswith('十'):
        return chinese_nums.get(s[0], 0) * 10
    else:
        return chinese_nums.get(s, 0)

def extract_images_from_docx(docx_path, output_dir):
    """從單個 docx 提取圖片"""
    images = []
    with zipfile.ZipFile(docx_path, 'r') as zip_ref:
        for file in zip_ref.namelist():
            if file.startswith('word/media/'):
                # 取得圖片資料
                img_data = zip_ref.read(file)
                ext = os.path.splitext(file)[1]
                images.append((file, img_data, ext))
    return images

def analyze_chapter_file(docx_path, chapter_id):
    """分析單個章節檔案，找出有圖片的題目"""
    doc = Document(docx_path)
    
    # 題目模式
    tf_answer_pattern = re.compile(r'[（(]\s*([○╳OX])\s*[）)]\s*(\d+)\.')
    mc_answer_pattern = re.compile(r'[（(]\s*([ＡＢＣＤABCD])\s*[）)]\s*(\d+)\.')
    source_pattern = re.compile(r'出處[：:]\s*([^\s　]+)')
    
    current_question_type = None
    
    # 題型標記
    type_headers = {
        '是非題': 'tf',
        '單選題': 'mc',
        '多選題': 'mc',
        '問答題': 'essay'
    }
    
    questions_with_images = []
    image_counter = 0
    
    paragraphs = list(doc.paragraphs)
    
    for i, para in enumerate(paragraphs):
        text = para.text.strip()
        
        # 檢查是否包含圖片
        has_image = False
        for run in para.runs:
            drawing = run._element.findall('.//' + qn('w:drawing'))
            pict = run._element.findall('.//' + qn('w:pict'))
            if drawing or pict:
                has_image = True
                image_counter += 1
                break
        
        if not text and has_image:
            continue
            
        if not text:
            continue
        
        # 偵測題型
        for type_name, type_code in type_headers.items():
            if type_name in text and (':' in text or '：' in text):
                current_question_type = type_code
                break
        
        # 解析是非題
        if current_question_type == 'tf':
            tf_match = tf_answer_pattern.search(text)
            if tf_match:
                answer_symbol = tf_match.group(1)
                question_num = int(tf_match.group(2))
                question_text = text[tf_match.end():].strip()
                
                # 取得出處
                source = ""
                if i > 0:
                    prev_text = paragraphs[i-1].text
                    source_match = source_pattern.search(prev_text)
                    if source_match:
                        source = source_match.group(1)
                
                # 檢查解析
                explanation = ""
                if i + 1 < len(paragraphs):
                    next_text = paragraphs[i+1].text.strip()
                    if next_text.startswith('解析'):
                        explanation = next_text.replace('解析', '').strip().lstrip('　 ：:')
                
                question_data = {
                    'type': 'tf',
                    'chapterId': chapter_id,
                    'question': question_text,
                    'answer': answer_symbol in ('○', 'O'),
                    'source': source,
                    'has_image': has_image,
                    'local_question_num': question_num
                }
                if explanation:
                    question_data['explanation'] = explanation
                    
                if has_image:
                    questions_with_images.append(question_data)
        
        # 解析選擇題
        elif current_question_type == 'mc':
            mc_match = mc_answer_pattern.search(text)
            if mc_match:
                answer_letter = mc_match.group(1)
                question_num = int(mc_match.group(2))
                question_text = text[mc_match.end():].strip()
                
                # 標準化答案
                answer_letter = answer_letter.replace('Ａ','A').replace('Ｂ','B').replace('Ｃ','C').replace('Ｄ','D')
                answer_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
                
                # 取得出處
                source = ""
                if i > 0:
                    prev_text = paragraphs[i-1].text
                    source_match = source_pattern.search(prev_text)
                    if source_match:
                        source = source_match.group(1)
                
                question_data = {
                    'type': 'mc',
                    'chapterId': chapter_id,
                    'question': question_text,
                    'answer': answer_map.get(answer_letter, 0),
                    'source': source,
                    'has_image': has_image,
                    'local_question_num': question_num
                }
                
                if has_image:
                    questions_with_images.append(question_data)
    
    return questions_with_images, image_counter

def main():
    chapters_dir = Path('chapters')
    
    if not chapters_dir.exists():
        print(f"Error: chapters directory not found")
        return
    
    # 章節ID映射 (根據檔案順序)
    chapter_mapping = {
        '00': 'ch1-1',
        '01': 'ch1-2',
        '02': 'ch1-3',
        '03': 'ch1-4',
        '04': 'ch1-5',
        '05': 'ch2-1',
        '06': 'ch2-2',
        '07': 'ch2-3',
        '08': 'ch3-1',
        '09': 'ch3-2',
        '10': 'ch3-3'
    }
    
    all_image_questions = []
    total_images = 0
    
    for docx_file in sorted(chapters_dir.glob('*.docx')):
        prefix = docx_file.name[:2]
        chapter_id = chapter_mapping.get(prefix, 'unknown')
        
        print(f"\n處理: {docx_file.name}")
        print(f"  章節ID: {chapter_id}")
        
        questions, img_count = analyze_chapter_file(docx_file, chapter_id)
        total_images += img_count
        
        print(f"  找到 {len(questions)} 個有圖片的題目")
        print(f"  共有 {img_count} 張圖片")
        
        for q in questions:
            print(f"    - {q['type']} #{q['local_question_num']}: {q['question'][:50]}...")
        
        all_image_questions.extend(questions)
    
    print("\n" + "=" * 60)
    print(f"總計: {len(all_image_questions)} 個有圖片的題目")
    print(f"總計: {total_images} 張圖片")
    print("=" * 60)
    
    # 輸出 JSON 供參考
    with open('image_questions.json', 'w', encoding='utf-8') as f:
        json.dump(all_image_questions, f, ensure_ascii=False, indent=2)
    print("\n已輸出到 image_questions.json")

if __name__ == '__main__':
    main()
