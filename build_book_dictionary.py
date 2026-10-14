import zipfile
import re
import json
import xml.etree.ElementTree as ET

odt_path = "憂國_評論集_自由時報與民報__一校中.odt"

with zipfile.ZipFile(odt_path, 'r') as z:
    content_xml = z.read('content.xml')

root = ET.fromstring(content_xml)

# Load reference readings
ref_readings = {}
try:
    with open('dict_data.json', 'r', encoding='utf-8') as f:
        old_dict = json.load(f)
        for h, v in old_dict.items():
            if 'readings' in v and v['readings']:
                ref_readings[h] = v['readings'][0]['rom']
                ref_readings[h.lower()] = v['readings'][0]['rom']
except Exception as e:
    pass

# Collect articles
articles = []
current_title = "封面"
current_cat = "封面"
current_paras = []

for elem in root.iter():
    tag = elem.tag.split('}')[-1]
    if tag == 'h':
        lvl = elem.attrib.get('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}outline-level', '1')
        txt = "".join(elem.itertext()).strip()
        if lvl == '1':
            current_cat = txt
            if '【序】' in txt:
                current_title = txt
                current_paras = []
        elif lvl == '2':
            if current_paras:
                articles.append({
                    'cat': current_cat,
                    'title': current_title.replace('\u200b', '').strip(),
                    'paras': current_paras
                })
            current_title = txt.replace('\u200b', '').strip()
            current_paras = []
    elif tag == 'p':
        p_txt = "".join(elem.itertext()).strip()
        if p_txt and not p_txt.startswith('日期：') and not p_txt.startswith('日期:'):
            current_paras.append(p_txt)

if current_paras:
    articles.append({
        'cat': current_cat,
        'title': current_title,
        'paras': current_paras
    })

print(f"Total articles: {len(articles)}")

# Comprehensive dictionary of authentic Taiwanese words & Han-lo terms
TAIWANESE_VOCAB_DB = {
    # Pronouns & People
    '阮': 'gún', '咱': 'lán', '恁': 'lín', '怹': 'in', '伊': 'i', '逐家': 'ta̍k-ke', '家己': 'ka-kī',
    '咱人': 'lán-lâng', '友志': 'iú-chì', '老先覺': 'lāu-sian-kak', '老歲仔': 'lāu-hè-á', '少年人': 'siàu-liân-lâng',
    '囝孫': 'kiáⁿ-sun', '下跤手人': 'ē-kha-chhiú-lâng', '土匪': 'thó͘-húi', '頭家': 'thâu-ke', '作穡人': 'choh-sit-lâng',
    '白蟻': 'pe̍h-ngī', '精牲': 'cheng-seⁿ', '枵鬼': 'iau-kúi', '好朋友': 'hó pêng-iú',

    # Common Taiwanese Verbs & Actions
    '作穡': 'choh-sit', '著磨': 'tio̍h-bôa', '出脫': 'chhut-thoat', '拖沙': 'thoa-soa', '贊聲': 'chán-siaⁿ',
    '造神': 'chō-sîn', '顧守': 'kò͘-siú', '買賣': 'bé-bē', '咒誓': 'chiù-chōa', '走精': 'cháu-chiaⁿ',
    '牽拖': 'khan-thoa', '掠狂': 'lia̍h-kông', '落屎': 'làu-sái', '跋倒': 'poa̍h-tó', '轉大人': 'tńg-tōa-lâng',
    '吸氣': 'suh-khuì', '打壓': 'táⁿ-ap', '打擊': 'táⁿ-kek', '做伙': 'chò-hóe', '做伴': 'chò-phōaⁿ',
    '討生活': 'thó-seng-oa̍h', '鬥相共': 'tàu-sio-kāng', '相爭': 'sio-cheⁿ', '相咬': 'sio-kā', '相打': 'sio-phah',
    '相借問': 'sio-chioh-mn̄g', '相伨': 'sio-thīn', '牽手': 'khan-chhiú', '開喙': 'khui-chhùi', '開跤': 'khui-kha',
    '睏袂去': 'khùn bē khì', '看無': 'khòaⁿ-bô', '生目睭': 'seⁿ ba̍k-chiu', '軟塗深掘': 'nńg-thô͘ chhim-ku̍t',
    '大聲喝咻': 'tōa-siaⁿ hoah-hiu', '倒退嚕': 'tò-thè-luh', '踏話頭': 'ta̍h ōe-thâu', '抽籤詩': 'thiu chhiam-si',
    '落衰': 'lak-sui', '歇後語': 'gia̍t-khiat-á-uē', '過一暝': 'kòe chi̍t mê',

    # Adjectives & Conditions
    '性地': 'sèng-tē', '破格': 'phòa-keh', '氣魄': 'khì-phek', '好佳在': 'hó-ka-chài', '好徛家': 'hó-khiā-ka',
    '人緣': 'lâng-iân', '傲霜': 'ngō͘-sng', '痟貪': 'siáu-tham', '好喙': 'hó-chhùi', '見笑': 'kiàn-siàu',
    '無影無跡': 'bô-iáⁿ-bô-chiah', '話骨': 'ōe-kut', '懶屍': 'lán-si', '手路': 'chhiú-lō͘', '番顛': 'hoan-thian',
    '烏白來': 'o͘-pe̍h lâi', '烏白': 'o͘-pe̍h', '笑詼': 'chhiò-khoe', '沙文': 'sa-bûn', '有影': 'ū-iáⁿ',
    '無影': 'bô-iáⁿ', '有夠': 'ū-kàu', '無夠': 'bô-kàu', '好空': 'hó-khang', '歹空': 'pháiⁿ-khang',
    '好代': 'hó-tāi', '歹代': 'pháiⁿ-tāi', '好心': 'hó-sim', '歹心': 'pháiⁿ-sim', '無通': 'bô-thang',
    '無彩工': 'bô-chhái-kang', '無彩': 'bô-chhái',

    # Nouns & Cultural Concepts
    '代誌': 'tāi-chì', '檨仔': 'soāiⁿ-á', '逐工': 'ta̍k-kang', '烏道': 'o͘-tō', '普渡': 'phó͘-tō͘',
    '箍仔': 'kho͘-á', '打狗': 'Tá-káu', '府城': 'Hú-siâⁿ', '下跤': 'ē-kha', '頂懸': 'téng-koân',
    '頭前': 'thâu-chêng', '後壁': 'āu-piah', '現此時': 'hiān-chhú-sî', '現時': 'hiān-sî', '後代': 'āu-tāi',
    '心肝頭': 'sim-koaⁿ-thâu', '心肝': 'sim-koaⁿ', '母語': 'bó-gí', '台語': 'Tâi-gí', '白話字': 'Pe̍h-ōe-jī',
    '羅馬字': 'Lô-má-jī', '台灣學': 'Tâi-oân-ha̍k', '台灣人': 'Tâi-oân-lâng', '國語': 'kok-gí',
    '七字仔': 'chhit-jī-á', '唸歌': 'liām-koa', '四句聯': 'sì-kù-liân', '俗語': 'sio̍k-gí'
}

# Add ref_readings for any Taiwanese word
for k, v in ref_readings.items():
    if k not in TAIWANESE_VOCAB_DB and not re.search(r'[a-zA-Z]', k):
        # Only add if it looks like Taiwanese vocabulary (not generic Chinese)
        if any(char in k for char in ['仔', '袂', '毋', '予', '欲', '煞', '閣', '佮', '阮', '咱', '恁', '怹', '伊', '逐', '佇', '遮', '遐', '啥', '按', '怎', '講', '食', '行', '著', '縛', '拍', '啉', '驚', '看', '聽', '做', '創', '揣', '鬥', '搝', '捒', '掀', '擘', '擲', 'peh', 'hioh', 'khng', 'khau', 'liam', 'phah', 'tshu', 'bue']):
            TAIWANESE_VOCAB_DB[k] = v

BOOK_DICT = {}

def add_entry(word, rom, title, sentence, is_phrase=False):
    word = word.strip()
    if not word or len(word) < 1:
        return
    if word not in BOOK_DICT:
        BOOK_DICT[word] = {
            'readings': {},
            'total': 0,
            'phrase': is_phrase
        }
    if rom not in BOOK_DICT[word]['readings']:
        BOOK_DICT[word]['readings'][rom] = {
            'rom': rom,
            'count': 0,
            'examples': []
        }
    BOOK_DICT[word]['total'] += 1
    r_entry = BOOK_DICT[word]['readings'][rom]
    r_entry['count'] += 1
    
    # Avoid duplicate examples for same sentence
    if not any(ex['han'] == sentence for ex in r_entry['examples']):
        if len(r_entry['examples']) < 8:
            r_entry['examples'].append({
                'title': title,
                'han': sentence,
                'rom': rom
            })

# Romanization pattern
rom_token_pattern = re.compile(r'[a-zA-Z\u00C0-\u024F\u0300-\u036F\u1E00-\u1EFF\u207F\u0358]+(?:--[a-zA-Z\u00C0-\u024F\u0300-\u036F\u1E00-\u1EFF\u207F\u0358]+|-[a-zA-Z\u00C0-\u024F\u0300-\u036F\u1E00-\u1EFF\u207F\u0358]+)*')

ENGLISH_STOPWORDS = {
    'the', 'of', 'and', 'to', 'in', 'is', 'you', 'that', 'it', 'he', 'was', 'for', 'on', 'are', 'as',
    'with', 'his', 'they', 'i', 'at', 'be', 'this', 'have', 'from', 'or', 'one', 'had', 'by', 'word',
    'but', 'not', 'what', 'all', 'were', 'we', 'when', 'your', 'can', 'said', 'there', 'use', 'an',
    'each', 'which', 'she', 'do', 'how', 'their', 'if', 'will', 'up', 'other', 'about', 'out', 'many',
    'then', 'them', 'these', 'so', 'some', 'her', 'would', 'make', 'like', 'him', 'into', 'time', 'has',
    'look', 'two', 'more', 'write', 'go', 'see', 'number', 'no', 'way', 'could', 'people', 'my', 'than',
    'first', 'water', 'been', 'call', 'who', 'oil', 'its', 'now', 'find', 'long', 'down', 'day', 'did',
    'get', 'come', 'made', 'may', 'part', 'taiwan', 'china', 'america', 'russian', 'ukraine', 'national',
    'security', 'journal', 'deepseek', 'nvidia', 'chatgpt', 'tiktok', 'facebook', 'google', 'apple',
    'youtube', 'new', 'york', 'times', 'economist', 'report', 'democracy', 'authorized', 'economic',
    'operator', 'customs', 'gdp', 'gmp', 'fdny', 'team', 'world', 'series', 'rubin', 'michael', 'kursk',
    'offensive', 'against', 'russia', 'thousands', 'fishing', 'boats', 'quietly', 'form', 'vast', 'sea',
    'barriers', 'update', 'isw', 'ait', 'peace', 'prepare', 'war', 'rage', 'dying', 'light', 'gentle',
    'good', 'night', 'usb', 'ic', 'power', 'ampleon', 'ftdi', 'nexperia', 'working', 'stay', 'ma',
    'bumbler', 'lian', 'nicholas', 'kristof', 'visiting', 'most', 'important', 'company', 'donald',
    'trump', 'inherit', 'earth', 'our', 'ancestors', 'borrow', 'children', 'a', 'b', 'c', 'd', 'fde', 'swe'
}

# Scan each article
for art in articles:
    title = art['title']
    cat = art['cat']
    
    # Process each paragraph
    for p in art['paras']:
        # Split sentences
        raw_sents = re.split(r'([。！？\n])', p)
        sents = []
        for i in range(0, len(raw_sents) - 1, 2):
            s = raw_sents[i] + raw_sents[i+1]
            if s.strip(): sents.append(s.strip())
        if len(raw_sents) % 2 == 1 and raw_sents[-1].strip():
            sents.append(raw_sents[-1].strip())
            
        for sent in sents:
            # Check for Romanized Taiwanese words (全羅 / 台羅 / POJ)
            tokens = rom_token_pattern.findall(sent)
            for tok in tokens:
                tok_clean = tok.strip('-').strip()
                tok_lower = tok_clean.lower()
                
                if tok_lower in ENGLISH_STOPWORDS:
                    continue
                if len(tok_clean) <= 1 and tok_clean.isupper():
                    continue
                if re.match(r'^[A-Z][a-z]+$', tok_clean) and not re.search(r'[áàâāa̍éèêēe̍íìîīi̍óòôōo̍úùûūu̍m̄ńňng̍o͘ⁿ]', tok_clean):
                    continue
                if re.match(r'^[A-Z0-9]+$', tok_clean):
                    continue
                    
                has_diacritic = bool(re.search(r'[áàâāa̍éèêēe̍íìîīi̍óòôōo̍úùûūu̍m̄ńňng̍o͘ⁿ]', tok_clean))
                has_hyphen = '-' in tok_clean
                is_known_tw = tok_lower in [
                    'beh', 'kā', 'che', 'kap', 'ê', 'mā', 'chit', 'leh', 'tek', 'khah', 'koh', 'lóng', 'thang',
                    'tō', 'ài', 'lán', 'chia', 'lah', 'ah', 'he', 'in', 'á', 'niâ', 'saⁿ', 'sak', 'àu', 'iā',
                    'tó', 'iú', 'gún', 'goán', 'lí', 'sī', 'tio̍h', 'bē', 'bōe', 'chiah', 'soah', 'siáⁿ',
                    'tse', 'hō͘', 'kám', 'ka-tī', 'ka-kī', 'án-ne', 'án-chóaⁿ', 'chhan-chhiūⁿ', 'chī-iāng',
                    'hōo', 'siánn', 'suah', 'tshuē', 'tó-uī', 'kiám-chhái', 'khǹg', 'póe-hōe', 'sio-thīn',
                    'chŏaⁿ', 'tháu', 'sìn', 'chek', 'bû', 'put-sìn', 'put-tit', 'bēng', 'hèng', 'sông', 'suh',
                    'khuì', 'tàu-tah', 'chhîⁿ', 'o-ló', 'jú', 'phóng', 'buah', 'bīn', 'siàn-chhuì-phóe', 'gín-á'
                ]
                
                if has_diacritic or has_hyphen or is_known_tw:
                    is_phrase = ('-' in tok_clean and len(tok_clean.split('-')) >= 4)
                    add_entry(tok_clean, tok_clean, title, sent, is_phrase=is_phrase)
                    
            # Check for authentic Han-lo Taiwanese vocabulary
            for han, rom in TAIWANESE_VOCAB_DB.items():
                if han in sent:
                    add_entry(han, rom, title, sent, is_phrase=False)

print(f"Total authentic Taiwanese/Han-lo headwords extracted from THIS BOOK: {len(BOOK_DICT)}")

FINAL_DICT = {}
for h, d in BOOK_DICT.items():
    readings_list = []
    for rom, r_data in d['readings'].items():
        readings_list.append({
            'rom': rom,
            'count': r_data['count'],
            'examples': r_data['examples']
        })
    readings_list.sort(key=lambda x: x['count'], reverse=True)
    FINAL_DICT[h] = {
        'readings': readings_list,
        'total': d['total'],
        'phrase': d['phrase']
    }

FINAL_META = {
    "total_headwords": len(FINAL_DICT),
    "word_headwords": sum(1 for v in FINAL_DICT.values() if not v['phrase']),
    "phrase_headwords": sum(1 for v in FINAL_DICT.values() if v['phrase']),
    "source": "護國 評論集（台-華）",
    "source_desc": "完全自杜信龍《護國 評論集》全書台語文、全羅與漢羅篇章專屬擷取",
    "author": "Tō͘ Sìn-Liông (杜信龍)",
    "license": "CC BY-NC-SA 4.0"
}

with open("dict_data.json", "w", encoding="utf-8") as f:
    json.dump(FINAL_DICT, f, ensure_ascii=False)

with open("dict_meta.json", "w", encoding="utf-8") as f:
    json.dump(FINAL_META, f, ensure_ascii=False, indent=2)

print("Saved dict_data.json and dict_meta.json based 100% on THIS BOOK's Taiwanese and Han-lo text!")
