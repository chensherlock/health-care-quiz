"""
從 all.docx 提取有圖片的題目
並更新 questions.js

此腳本會:
1. 分析 docx 中哪些題目有關聯圖片
2. 將圖片路徑加入題目資料
3. 更新 questions.js
"""

from docx import Document
from docx.oxml.ns import qn
import re
import json
import os

def extract_questions_with_images(docx_path):
    """分析 docx 並找出有圖片的題目"""
    doc = Document(docx_path)
    
    # 章節標題模式
    chapter_section_pattern = re.compile(
        r'第([一二三四五六七八九十]+)章.*第([一二三四五六七八九十]+)節\s*(.+)'
    )
    
    # 題目模式
    tf_answer_pattern = re.compile(r'[（(]\s*([○╳OX])\s*[）)]\s*(\d+)\.')
    mc_answer_pattern = re.compile(r'[（(]\s*([ＡＢＣＤABCD])\s*[）)]\s*(\d+)\.')
    
    # 中文數字轉換
    chinese_nums = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
    
    def convert_chinese_num(s):
        if s == '十':
            return 10
        elif s.startswith('十'):
            return 10 + chinese_nums.get(s[1], 0)
        elif s.endswith('十'):
            return chinese_nums.get(s[0], 0) * 10
        else:
            return chinese_nums.get(s, 0)
    
    current_chapter_id = 'ch1-1'
    current_question_type = None
    image_index = 1
    
    # 儲存有圖片的題目資訊
    questions_with_images = []
    
    for para in doc.paragraphs:
        text = para.text.strip()
        
        # 檢查是否包含圖片
        has_image = False
        for run in para.runs:
            drawing_elements = run._element.findall('.//' + qn('w:drawing'))
            if drawing_elements:
                has_image = True
                break
        
        if not text:
            if has_image:
                # 純圖片段落，記錄圖片索引
                print(f"Image {image_index}: (standalone image)")
                image_index += 1
            continue
        
        # 偵測章節
        ch_sec_match = chapter_section_pattern.search(text)
        if ch_sec_match:
            ch_num = convert_chinese_num(ch_sec_match.group(1))
            sec_num = convert_chinese_num(ch_sec_match.group(2))
            current_chapter_id = f"ch{ch_num}-{sec_num}"
            continue
        
        # 偵測題型
        type_headers = {
            '是非題': 'tf',
            '單選題': 'mc',
            '多選題': 'mc_multi',
            '問答題': 'essay'
        }
        for type_name, type_code in type_headers.items():
            if type_name in text and (':' in text or '：' in text):
                current_question_type = type_code
                break
        
        # 檢查是否為題目
        is_question = False
        question_num = None
        answer = None
        
        tf_match = tf_answer_pattern.search(text)
        mc_match = mc_answer_pattern.search(text)
        
        if tf_match and current_question_type == 'tf':
            is_question = True
            question_num = tf_match.group(2)
            answer_symbol = tf_match.group(1)
            answer = answer_symbol in ('○', 'O')
            question_text = text[tf_match.end():].strip()
        elif mc_match and current_question_type in ('mc', 'mc_multi'):
            is_question = True
            question_num = mc_match.group(2)
            answer_letter = mc_match.group(1)
            answer_letter = answer_letter.replace('Ａ','A').replace('Ｂ','B').replace('Ｃ','C').replace('Ｄ','D')
            answer_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
            answer = answer_map.get(answer_letter, 0)
            question_text = text[mc_match.end():].strip()
        
        if has_image:
            print(f"Image {image_index}: Chapter={current_chapter_id}, Type={current_question_type}, "
                  f"Question={question_num if question_num else 'N/A'}, Text preview: {text[:50]}...")
            
            if is_question:
                questions_with_images.append({
                    'chapter_id': current_chapter_id,
                    'type': current_question_type,
                    'question_num': question_num,
                    'image': f"images/image{image_index}.png",
                    'text_preview': text[:100]
                })
            
            image_index += 1
    
    return questions_with_images

def print_image_question_summary(questions):
    """印出有圖片題目的摘要"""
    print("\n" + "=" * 60)
    print("有圖片的題目摘要")
    print("=" * 60)
    
    by_chapter = {}
    for q in questions:
        ch = q['chapter_id']
        if ch not in by_chapter:
            by_chapter[ch] = []
        by_chapter[ch].append(q)
    
    for ch in sorted(by_chapter.keys()):
        print(f"\n{ch}:")
        for q in by_chapter[ch]:
            print(f"  - {q['type']} #{q['question_num']}: {q['image']}")
            print(f"    {q['text_preview'][:60]}...")

if __name__ == '__main__':
    docx_file = 'all.docx'
    
    if not os.path.exists(docx_file):
        print(f"Error: {docx_file} not found")
        exit(1)
    
    print("分析有圖片的題目...")
    questions = extract_questions_with_images(docx_file)
    
    print_image_question_summary(questions)
    
    print(f"\n共找到 {len(questions)} 個有圖片的題目")
    print("\n注意: 要將這些題目加入題庫，需要手動檢查圖片與題目的對應關係")
    print("因為圖片可能是選項說明而非題目本身")
