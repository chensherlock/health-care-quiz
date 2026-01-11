"""
分析 all.docx 中有圖片的題目並提取完整資訊
"""

from docx import Document
from docx.oxml.ns import qn
import re
import json

def convert_chinese_num(s):
    chinese_nums = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
    if s == '十':
        return 10
    elif len(s) == 2 and s.startswith('十'):
        return 10 + chinese_nums.get(s[1], 0)
    elif len(s) == 2 and s.endswith('十'):
        return chinese_nums.get(s[0], 0) * 10
    else:
        return chinese_nums.get(s, 0)

def has_image_in_paragraph(para):
    """檢查段落中是否有圖片"""
    for run in para.runs:
        # 檢查 drawing 元素
        drawing = run._element.findall('.//' + qn('w:drawing'))
        if drawing:
            return True
        # 檢查 pict 元素 (舊版 Word)
        pict = run._element.findall('.//' + qn('w:pict'))
        if pict:
            return True
        # 檢查 object 元素
        obj = run._element.findall('.//' + qn('w:object'))
        if obj:
            return True
    return False

def extract_options_from_text(text):
    """從題目文字提取選項"""
    # 清理題目文字
    text = re.sub(r'\s+', ' ', text)
    
    # 嘗試匹配選項格式
    option_pattern = re.compile(r'[（(]([ABCD])[）)]\s*([^（(ABCD]+?)(?=[（(][ABCD][）)]|$)')
    matches = option_pattern.findall(text)
    
    if len(matches) >= 2:
        options = {m[0]: m[1].strip() for m in matches}
        # 找到主題文字 (選項之前的部分)
        first_option_pos = text.find('(A)')
        if first_option_pos == -1:
            first_option_pos = text.find('（A）')
        if first_option_pos > 0:
            main_question = text[:first_option_pos].strip()
        else:
            main_question = text
        return main_question, options
    
    return text, None

def main():
    doc = Document('all.docx')
    
    # 模式
    chapter_pattern = re.compile(r'第([一二三四五六七八九十]+)章.*第([一二三四五六七八九十]+)節\s*(.+)')
    tf_pattern = re.compile(r'[（(]\s*([○╳OX])\s*[）)]\s*(\d+)\.')
    mc_pattern = re.compile(r'[（(]\s*([ＡＢＣＤABCD])\s*[）)]\s*(\d+)\.')
    source_pattern = re.compile(r'出處[：:]\s*([^\s　]+)')
    
    current_chapter_id = 'ch1-1'
    current_type = None
    
    type_headers = {
        '是非題': 'tf',
        '單選題': 'mc',
        '多選題': 'mc',
        '問答題': 'essay'
    }
    
    paragraphs = list(doc.paragraphs)
    image_questions = []
    image_context = []
    
    print("分析 all.docx 中的圖片...\n")
    
    for i, para in enumerate(paragraphs):
        text = para.text.strip()
        has_img = has_image_in_paragraph(para)
        
        # 偵測章節
        ch_match = chapter_pattern.search(text)
        if ch_match:
            ch_num = convert_chinese_num(ch_match.group(1))
            sec_num = convert_chinese_num(ch_match.group(2))
            current_chapter_id = f"ch{ch_num}-{sec_num}"
            if has_img:
                print(f"圖片在章節標題: {current_chapter_id}")
            continue
        
        # 偵測題型
        for type_name, type_code in type_headers.items():
            if type_name in text and (':' in text or '：' in text):
                current_type = type_code
                break
        
        # 記錄有圖片的段落
        if has_img:
            # 取得前後文
            prev_text = paragraphs[i-1].text.strip() if i > 0 else ""
            next_text = paragraphs[i+1].text.strip() if i < len(paragraphs)-1 else ""
            
            context = {
                'index': i,
                'chapter': current_chapter_id,
                'type': current_type,
                'text': text,
                'prev_text': prev_text[:100] if prev_text else "",
                'next_text': next_text[:100] if next_text else ""
            }
            
            # 檢查是否為題目行
            tf_match = tf_pattern.search(text)
            mc_match = mc_pattern.search(text)
            
            if tf_match:
                context['is_question'] = True
                context['question_type'] = 'tf'
                context['question_num'] = tf_match.group(2)
                context['answer'] = tf_match.group(1) in ('○', 'O')
                context['question_text'] = text[tf_match.end():].strip()
            elif mc_match:
                context['is_question'] = True
                context['question_type'] = 'mc'
                context['question_num'] = mc_match.group(2)
                ans = mc_match.group(1).replace('Ａ','A').replace('Ｂ','B').replace('Ｃ','C').replace('Ｄ','D')
                context['answer'] = {'A':0,'B':1,'C':2,'D':3}.get(ans, 0)
                context['question_text'] = text[mc_match.end():].strip()
            else:
                context['is_question'] = False
                # 可能是題目的圖片部分
                if prev_text:
                    tf_prev = tf_pattern.search(prev_text)
                    mc_prev = mc_pattern.search(prev_text)
                    if tf_prev or mc_prev:
                        context['related_to_prev_question'] = True
            
            image_context.append(context)
    
    print(f"\n找到 {len(image_context)} 個包含圖片的段落")
    print("\n" + "=" * 70)
    
    for ctx in image_context:
        print(f"\n段落 {ctx['index']} [{ctx['chapter']}] ({ctx['type']}):")
        if ctx.get('is_question'):
            print(f"  ★ 這是題目: {ctx['question_type']} #{ctx['question_num']}")
            print(f"  答案: {ctx['answer']}")
            print(f"  題目: {ctx['question_text'][:80]}...")
        else:
            print(f"  內容: {ctx['text'][:80] if ctx['text'] else '[純圖片]'}...")
            if ctx.get('related_to_prev_question'):
                print(f"  可能關聯到前一題")
        print(f"  前文: {ctx['prev_text'][:60]}...")
    
    # 輸出 JSON
    with open('image_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(image_context, f, ensure_ascii=False, indent=2)
    
    print(f"\n詳細資訊已輸出到 image_analysis.json")

if __name__ == '__main__':
    main()
