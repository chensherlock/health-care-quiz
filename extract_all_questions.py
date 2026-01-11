"""
健康與護理 題庫提取腳本 v2
從 all.docx 提取所有題目並輸出為 questions.js
題型: 是非題、單選題、多選題、配合題、填充題、題組題、問答題
"""

from docx import Document
import re
import json
import os
import zipfile
import shutil


def convert_chinese_num(chinese):
    """轉換中文數字"""
    mapping = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
    }
    if len(chinese) == 1:
        return mapping.get(chinese, 1)
    elif chinese.startswith('十'):
        return 10 + mapping.get(chinese[1:], 0) if len(chinese) > 1 else 10
    elif chinese.endswith('十'):
        return mapping.get(chinese[0], 1) * 10
    return 1


def extract_options_from_text(text):
    """從選擇題文字中提取選項"""
    # 尋找選項 (A)...(B)...(C)...(D)... 或 A.B.C.D. 格式
    # 全形或半形括號
    patterns = [
        r'[（(]\s*([AaBbCcDd])\s*[）)]\s*([^（(]+?)(?=[（(][AaBbCcDd]|$)',
        r'\s([A-D])\s*[\.。]\s*([^A-D]+?)(?=\s[A-D]\s*[\.。]|$)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if len(matches) >= 2:
            options = []
            question = text
            for letter, content in matches:
                opt_text = content.strip()
                if opt_text:
                    options.append(opt_text)
                    # 移除選項部分以獲得純題目
                    question = question.split(f'({letter.upper()})')[0]
                    question = question.split(f'（{letter.upper()}）')[0]
            if options:
                return {'question': question.strip(), 'options': options}
    
    return None


def extract_questions(docx_path):
    """從 docx 提取所有題目"""
    doc = Document(docx_path)
    
    data = {
        'chapters': [],
        'trueFalseQuestions': [],
        'multipleChoiceQuestions': [],
        'matchingQuestions': [],
        'essayQuestions': []
    }
    
    current_chapter_id = 'ch1-1'
    current_question_type = None
    
    tf_id = mc_id = essay_id = 0
    
    # 章節標題模式
    chapter_section_pattern = re.compile(
        r'第([一二三四五六七八九十]+)章.*第([一二三四五六七八九十]+)節\s*(.+)'
    )
    
    # 題型標記
    type_headers = {
        '是非題': 'tf',
        '單選題': 'mc',
        '多選題': 'mc_multi',  # 視為選擇題處理
        '配合題': 'match',
        '填充題': 'fill',
        '題組題': 'group',
        '問答題': 'essay'
    }
    
    # 答案模式
    tf_answer_pattern = re.compile(r'[（(]\s*([○╳OX])\s*[）)]\s*(\d+)\.')
    mc_answer_pattern = re.compile(r'[（(]\s*([ＡＢＣＤABCD])\s*[）)]\s*(\d+)\.')
    source_pattern = re.compile(r'出處[：:]\s*([^\s　]+)')
    
    paragraphs = list(doc.paragraphs)
    
    for i, para in enumerate(paragraphs):
        text = para.text.strip()
        if not text:
            continue
        
        # 偵測章節標題
        ch_sec_match = chapter_section_pattern.search(text)
        if ch_sec_match:
            ch_num = convert_chinese_num(ch_sec_match.group(1))
            sec_num = convert_chinese_num(ch_sec_match.group(2))
            sec_name = ch_sec_match.group(3).strip()
            
            current_chapter_id = f"ch{ch_num}-{sec_num}"
            
            # 避免重複
            if not any(c['id'] == current_chapter_id for c in data['chapters']):
                data['chapters'].append({
                    'id': current_chapter_id,
                    'chapter': f"第{ch_sec_match.group(1)}章",
                    'section': f"第{ch_sec_match.group(2)}節 {sec_name}",
                    'shortName': f"{ch_num}-{sec_num} {sec_name}"
                })
            continue
        
        # 偵測題型標記
        for type_name, type_code in type_headers.items():
            if type_name in text and (':' in text or '：' in text):
                current_question_type = type_code
                break
        
        # 解析是非題
        if current_question_type == 'tf':
            tf_match = tf_answer_pattern.search(text)
            if tf_match:
                answer_symbol = tf_match.group(1)
                question_text = text[tf_match.end():].strip()
                
                # 清理題目文字
                question_text = re.sub(r'\s+', ' ', question_text)
                
                # 取得出處 (從前一段)
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
                        explanation = next_text.replace('解析', '').strip().lstrip('　 ')
                
                tf_id += 1
                q = {
                    'id': tf_id,
                    'chapterId': current_chapter_id,
                    'question': question_text,
                    'answer': answer_symbol in ('○', 'O'),
                    'source': source
                }
                if explanation:
                    q['explanation'] = explanation
                data['trueFalseQuestions'].append(q)
        
        # 解析單選題/多選題
        elif current_question_type in ('mc', 'mc_multi'):
            mc_match = mc_answer_pattern.search(text)
            if mc_match:
                answer_letter = mc_match.group(1)
                question_text = text[mc_match.end():].strip()
                
                # 標準化答案字母
                answer_letter = answer_letter.replace('Ａ', 'A').replace('Ｂ', 'B')
                answer_letter = answer_letter.replace('Ｃ', 'C').replace('Ｄ', 'D')
                
                # 嘗試提取選項
                parsed = extract_options_from_text(question_text)
                
                # 取得出處
                source = ""
                if i > 0:
                    prev_text = paragraphs[i-1].text
                    source_match = source_pattern.search(prev_text)
                    if source_match:
                        source = source_match.group(1)
                
                answer_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
                
                mc_id += 1
                data['multipleChoiceQuestions'].append({
                    'id': mc_id,
                    'chapterId': current_chapter_id,
                    'question': parsed['question'] if parsed else question_text,
                    'options': parsed['options'] if parsed else [],
                    'answer': answer_map.get(answer_letter, 0),
                    'source': source
                })
        
        # 解析問答題
        elif current_question_type == 'essay':
            essay_match = re.match(r'(\d+)\.\s*(.+)', text)
            if essay_match and not text.startswith('編碼'):
                question_text = essay_match.group(2).strip()
                
                # 取得出處
                source = ""
                if i > 0:
                    prev_text = paragraphs[i-1].text
                    source_match = source_pattern.search(prev_text)
                    if source_match:
                        source = source_match.group(1)
                
                # 找答案
                answer_text = ""
                if i + 1 < len(paragraphs):
                    next_text = paragraphs[i+1].text.strip()
                    if next_text.startswith('解答'):
                        answer_text = next_text.replace('解答', '').strip().lstrip('　 ')
                
                essay_id += 1
                data['essayQuestions'].append({
                    'id': essay_id,
                    'chapterId': current_chapter_id,
                    'question': question_text,
                    'answer': answer_text,
                    'source': source
                })
    
    return data


def extract_images(docx_path, output_dir='images'):
    """從 docx 提取圖片"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    extracted = 0
    with zipfile.ZipFile(docx_path, 'r') as z:
        for name in z.namelist():
            if 'media' in name:
                filename = os.path.basename(name)
                data = z.read(name)
                with open(os.path.join(output_dir, filename), 'wb') as f:
                    f.write(data)
                extracted += 1
    
    return extracted


def generate_js(data, output_path='questions.js'):
    """生成 JavaScript 檔案"""
    from datetime import datetime
    
    js_content = f'''// 健康與護理Ⅰ 題庫 - 自動生成
// 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}
// 統計: {len(data['chapters'])} 章節, {len(data['trueFalseQuestions'])} 是非題, {len(data['multipleChoiceQuestions'])} 選擇題, {len(data['essayQuestions'])} 問答題

const quizData = {{
  title: "健康與護理Ⅰ",
  
  chapters: {json.dumps(data['chapters'], ensure_ascii=False, indent=4)},
  
  trueFalseQuestions: {json.dumps(data['trueFalseQuestions'], ensure_ascii=False, indent=4)},
  
  multipleChoiceQuestions: {json.dumps(data['multipleChoiceQuestions'], ensure_ascii=False, indent=4)},
  
  matchingQuestions: {json.dumps(data['matchingQuestions'], ensure_ascii=False, indent=4)},
  
  essayQuestions: {json.dumps(data['essayQuestions'], ensure_ascii=False, indent=4)}
}};
'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(js_content)


if __name__ == '__main__':
    print("=" * 50)
    print("健康與護理 題庫提取 v2")
    print("=" * 50)
    
    docx_file = 'all.docx'
    
    if not os.path.exists(docx_file):
        print(f"錯誤: 找不到 {docx_file}")
        exit(1)
    
    print(f"\n正在解析 {docx_file}...")
    data = extract_questions(docx_file)
    
    print(f"\n提取結果:")
    print(f"  章節數: {len(data['chapters'])}")
    print(f"  是非題: {len(data['trueFalseQuestions'])}")
    print(f"  選擇題: {len(data['multipleChoiceQuestions'])}")
    print(f"  配合題: {len(data['matchingQuestions'])}")
    print(f"  問答題: {len(data['essayQuestions'])}")
    
    print(f"\n章節列表:")
    for ch in data['chapters']:
        tf = len([q for q in data['trueFalseQuestions'] if q['chapterId'] == ch['id']])
        mc = len([q for q in data['multipleChoiceQuestions'] if q['chapterId'] == ch['id']])
        es = len([q for q in data['essayQuestions'] if q['chapterId'] == ch['id']])
        print(f"  {ch['shortName']}: TF={tf}, MC={mc}, Essay={es}")
    
    print(f"\n正在提取圖片...")
    img_count = extract_images(docx_file)
    print(f"  提取 {img_count} 張圖片")
    
    print(f"\n正在生成 questions.js...")
    generate_js(data)
    
    print(f"\n完成!")
