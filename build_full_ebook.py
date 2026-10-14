import os
import re
import html
import zipfile
import xml.etree.ElementTree as ET

odt_path = "憂國_評論集_自由時報與民報__一校中.odt"

with zipfile.ZipFile(odt_path, 'r') as z:
    content_xml = z.read('content.xml')

root = ET.fromstring(content_xml)

NS = {
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
    'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
    'xlink': 'http://www.w3.org/1999/xlink',
    'style': 'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
    'fo': 'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0'
}

# Extract style information (bold/italic)
bold_styles = set()
italic_styles = set()

for s in root.iter('{urn:oasis:names:tc:opendocument:xmlns:style:1.0}style'):
    name = s.attrib.get('{urn:oasis:names:tc:opendocument:xmlns:style:1.0}name')
    tp = s.find('{urn:oasis:names:tc:opendocument:xmlns:style:1.0}text-properties')
    if tp is not None:
        weight = tp.attrib.get('{urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0}font-weight', '') or tp.attrib.get('{http://www.w3.org/1999/xlink}font-weight', '')
        posture = tp.attrib.get('{urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0}font-style', '')
        if weight == 'bold':
            bold_styles.add(name)
        if posture == 'italic':
            italic_styles.add(name)

# Map headings to internal section IDs
heading_to_id = {}

def extract_node_html(node):
    """Recursively converts an XML node to HTML formatted string."""
    res = []
    if node.text:
        res.append(html.escape(node.text))
        
    for child in node:
        tag = child.tag.split('}')[-1]
        
        if tag == 'span':
            style_name = child.attrib.get('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}style-name', '')
            inner = extract_node_html(child)
            if style_name in bold_styles and style_name in italic_styles:
                res.append(f"<strong><em>{inner}</em></strong>")
            elif style_name in bold_styles:
                res.append(f"<strong>{inner}</strong>")
            elif style_name in italic_styles:
                res.append(f"<em>{inner}</em>")
            else:
                res.append(inner)
                
        elif tag == 'a':
            href = child.attrib.get('{http://www.w3.org/1999/xlink}href', '')
            inner = extract_node_html(child)
            if href.startswith('http'):
                # Check if it's youtube or audio
                is_audio = 'youtube.com' in href or 'youtu.be' in href or 'soundcloud' in href or 'mp3' in href
                icon = ' <span class="ext-icon">🎧</span>' if is_audio else ' <span class="ext-icon">↗</span>'
                res.append(f'<a href="{html.escape(href)}" target="_blank" rel="noopener noreferrer" class="link-external{" link-audio" if is_audio else ""}">{inner}{icon}</a>')
            else:
                # Internal bookmark link
                res.append(f'<span class="internal-link" data-href="{html.escape(href)}">{inner}</span>')
                
        elif tag == 'line-break':
            res.append('<br/>')
            
        elif tag == 'tab':
            res.append('&emsp;')
            
        elif tag == 's':
            c = int(child.attrib.get('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}c', 1))
            res.append(' ' * c)
            
        elif tag == 'frame':
            img = child.find('{urn:oasis:names:tc:opendocument:xmlns:drawing:1.0}image')
            if img is not None:
                img_href = img.attrib.get('{http://www.w3.org/1999/xlink}href', '')
                basename = os.path.basename(img_href)
                res.append(f'<div class="book-img-wrap"><img src="images/{basename}" alt="插圖" class="book-image" loading="lazy" /></div>')
                
        elif tag == 'image':
            img_href = child.attrib.get('{http://www.w3.org/1999/xlink}href', '')
            basename = os.path.basename(img_href)
            res.append(f'<div class="book-img-wrap"><img src="images/{basename}" alt="插圖" class="book-image" loading="lazy" /></div>')
            
        else:
            res.append(extract_node_html(child))
            
        if child.tail:
            res.append(html.escape(child.tail))
            
    return "".join(res)

def extract_table_html(table_node):
    rows_html = []
    is_first = True
    for row in table_node.findall('.//{urn:oasis:names:tc:opendocument:xmlns:table:1.0}table-row'):
        cells_html = []
        cell_tag = 'th' if is_first else 'td'
        for cell in row.findall('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}table-cell'):
            cell_parts = []
            for p in cell.findall('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p'):
                p_text = extract_node_html(p).strip()
                if p_text:
                    cell_parts.append(p_text)
            inner_cell = "<br>".join(cell_parts)
            cells_html.append(f"<{cell_tag}>{inner_cell}</{cell_tag}>")
        if cells_html:
            rows_html.append("<tr>" + "".join(cells_html) + "</tr>")
        is_first = False
    return "<div class='table-container'><table class='book-table'><tbody>" + "".join(rows_html) + "</tbody></table></div>"

body = root.find('.//office:text', NS)
elements = list(body)

# First pass: Collect all articles and map their clean titles to section IDs
all_articles = []
idx = 0

# Skip to preface
while idx < len(elements):
    elem = elements[idx]
    tag = elem.tag.split('}')[-1]
    txt = "".join(elem.itertext()).strip()
    if tag == 'h' and '【序】守護咱台灣--lah' in txt:
        idx += 1
        break
    idx += 1

# Skip preface elements
while idx < len(elements):
    elem = elements[idx]
    tag = elem.tag.split('}')[-1]
    txt = "".join(elem.itertext()).strip()
    if tag == 'h' and '【國家安全】' in txt:
        break
    idx += 1

current_cat = "國家安全"
sec_id_counter = 2

while idx < len(elements):
    elem = elements[idx]
    tag = elem.tag.split('}')[-1]
    txt = "".join(elem.itertext()).strip()
    
    if tag == 'h':
        level = elem.attrib.get('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}outline-level', '1')
        if level == '1':
            if '【國家安全】' in txt: current_cat = '國家安全'
            elif '【社會議題】' in txt: current_cat = '社會議題'
            elif '【母語議題】' in txt: current_cat = '母語議題'
            elif '【台語相關雜文】' in txt: current_cat = '台語相關雜文'
            elif '分類文章表格' in txt or '索引' in txt:
                break
        elif level == '2':
            clean_title = txt.replace('\u200b', '').strip()
            heading_to_id[clean_title] = f"section-{sec_id_counter}"
            # Also register substring without prefix like 自由廣場》
            if '》' in clean_title:
                heading_to_id[clean_title.split('》', 1)[-1].strip()] = f"section-{sec_id_counter}"
            sec_id_counter += 1
    idx += 1

print(f"Mapped {len(heading_to_id)} heading keys to section IDs")

# Second pass: Build sections
sections = []

# Section 0: Cover
sections.append({
    'id': 'section-0',
    'title': '封面導讀',
    'short_title': '封面導讀',
    'category': '封面導讀',
    'type': 'cover',
    'content_html': '''
    <div class="cover-hero">
        <div class="cover-image-box">
            <img src="images/cover.jpg" alt="護國 封面" class="cover-image-main" />
        </div>
        <div class="cover-intro-card">
            <div class="badge badge-primary">政經國安 × 社會改革 × 母語復振</div>
            <h1 class="book-main-title">護國</h1>
            <h2 class="book-sub-title">評論集（台-華）</h2>
            <div class="author-line">
                <span class="author-name">杜信龍 (Tō͘ Sìn-Liông) 著</span>
            </div>
            
            <div class="meta-details-pill">
                <span>史秀里冊房 出版</span>
                <span>•</span>
                <span>2026年10月初版一刷</span>
                <span>•</span>
                <span>全書 240 篇評論</span>
            </div>

            <p class="book-quote">
                「原底beh kā冊名號做『憂國』，che名kap過去日本文學家三島由紀夫ê冊來--ê，後來台灣文學曾貴海mā捌出過以chit-ê冊名……<br><br>
                阮落尾想想leh，『憂』字一般tek khah負面，總是無koh進一步行動ê概念，chŏaⁿ改做<strong>『護』國</strong>。<br><br>
                <strong>Taⁿ，無人是外人；做伙手牽手護國！</strong>」
            </p>

            <div class="cover-actions">
                <button class="btn btn-primary" onclick="activateSection('section-1')">開始閱讀【序言】 →</button>
                <button class="btn btn-outline" onclick="activateSection('section-2')">閱讀首篇評論</button>
                <button class="btn btn-secondary" onclick="activateSection('section-242')">全書索引目錄</button>
            </div>

            <div class="stats-row">
                <div class="stat-item">
                    <div class="stat-number">100</div>
                    <div class="stat-desc">國家安全篇</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">62</div>
                    <div class="stat-desc">社會議題篇</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">55</div>
                    <div class="stat-desc">母語議題篇</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">23</div>
                    <div class="stat-desc">台語雜文篇</div>
                </div>
            </div>
        </div>
    </div>
    '''
})

# Section 1: Preface
idx = 0
while idx < len(elements):
    elem = elements[idx]
    tag = elem.tag.split('}')[-1]
    txt = "".join(elem.itertext()).strip()
    if tag == 'h' and '【序】守護咱台灣--lah' in txt:
        idx += 1
        break
    idx += 1

preface_html = []
while idx < len(elements):
    elem = elements[idx]
    tag = elem.tag.split('}')[-1]
    txt = "".join(elem.itertext()).strip()
    if tag == 'h' and '【國家安全】' in txt:
        break
    if tag == 'table-of-content':
        idx += 1
        continue
    if tag == 'p':
        p_html = extract_node_html(elem).strip()
        if p_html:
            if '2026 nî' in p_html:
                preface_html.append(f'<p class="date-signature">{p_html}</p>')
            else:
                preface_html.append(f'<p>{p_html}</p>')
    idx += 1

sections.append({
    'id': 'section-1',
    'title': '【序】守護咱台灣--lah',
    'short_title': '【序】守護咱台灣--lah',
    'category': '序言',
    'type': 'preface',
    'date': '2026-08-22',
    'content_html': f'''
    <div class="article-header">
        <span class="category-badge cat-preface">序言</span>
        <h1 class="article-title">【序】守護咱台灣--lah</h1>
        <div class="article-meta-bar">
            <span class="meta-item">✍️ 杜信龍</span>
            <span class="meta-item">📅 2026 nî 8 goe̍h 22 ji̍t</span>
            <span class="meta-item">📍 史秀里冊房</span>
        </div>
    </div>
    <div class="article-body">
        {"".join(preface_html)}
    </div>
    <div class="article-footer-nav">
        <button class="nav-btn prev-btn" onclick="activateSection('section-0')">← 回到封面導讀</button>
        <button class="nav-btn next-btn" onclick="activateSection('section-2')">下一篇：消失ê中國白蟻？ →</button>
    </div>
    '''
})

# Collect Articles
current_cat = '國家安全'
current_sec_num = 2
article_elements = []
current_title = ""
current_date = ""

def finish_article(art_num, cat, title, elems):
    body_parts = []
    art_date = ""
    for el in elems:
        t = el.tag.split('}')[-1]
        if t == 'p':
            p_content = extract_node_html(el).strip()
            if not p_content:
                continue
            # Check if this paragraph is date line
            if not art_date and ('日期：' in p_content or '日期:' in p_content):
                art_date = p_content
                continue
            body_parts.append(f"<p>{p_content}</p>")
        elif t == 'table':
            body_parts.append(extract_table_html(el))
            
    cat_class_map = {
        '國家安全': 'cat-security',
        '社會議題': 'cat-society',
        '母語議題': 'cat-mother-tongue',
        '台語相關雜文': 'cat-taiwanese'
    }
    cat_class = cat_class_map.get(cat, 'cat-default')
    
    clean_t = title.replace('\u200b', '').strip()
    
    prev_id = f"section-{art_num - 1}"
    next_id = f"section-{art_num + 1}"
    
    # Detect if article is Taiwanese / Han-lo
    is_taiwanese = (cat in ['母語議題', '台語相關雜文', '序言']) or ('ê' in clean_t) or ('--lah' in clean_t)
    if not is_taiwanese:
        sample_body = " ".join(body_parts[:4])
        tw_markers = ['ê', 'm̄', 'bē', 'bōe', 'kā', 'chit ', 'lóng', 'tio̍h', 'thang', 'hō͘', 'siáⁿ', 'án-chóaⁿ', 'chiah ', 'chhan-chhiūⁿ']
        if sum(1 for m in tw_markers if m in sample_body.lower()) >= 2:
            is_taiwanese = True

    tw_badge_html = f'''
    <div class="taiwanese-toolbar-strip">
        <span class="tw-strip-tag">🇹🇼 漢羅／全羅台語篇章</span>
        <button class="tw-strip-btn" onclick="openDictModeWithSelection('{clean_t}')">📚 查台語字典模式</button>
    </div>
    ''' if is_taiwanese else ''

    content = f'''
    <div class="article-header">
        <span class="category-badge {cat_class}">【{cat}】</span>
        {f'<span class="lang-pill">漢羅台文</span>' if is_taiwanese else ''}
        <h1 class="article-title">{clean_t}</h1>
        <div class="article-meta-bar">
            {f'<span class="meta-item meta-date">📅 {art_date}</span>' if art_date else ''}
            <span class="meta-item meta-cat">📂 {cat}</span>
            <span class="meta-item meta-num"># {art_num - 1} / 240</span>
        </div>
        {tw_badge_html}
    </div>
    <div class="article-body">
        {"".join(body_parts)}
    </div>
    <div class="article-footer-nav">
        <button class="nav-btn prev-btn" onclick="activateSection('{prev_id}')">← 上一篇</button>
        <button class="nav-btn toc-btn" onclick="activateSection('section-242')">📑 索引目錄</button>
        <button class="nav-btn next-btn" onclick="activateSection('{next_id}')">下一篇 →</button>
    </div>
    '''
    return {
        'id': f'section-{art_num}',
        'title': clean_t,
        'short_title': clean_t,
        'category': cat,
        'date': art_date,
        'type': 'article',
        'is_taiwanese': is_taiwanese,
        'content_html': content
    }

while idx < len(elements):
    elem = elements[idx]
    tag = elem.tag.split('}')[-1]
    txt = "".join(elem.itertext()).strip()
    
    if tag == 'h':
        level = elem.attrib.get('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}outline-level', '1')
        if level == '1':
            if '【國家安全】' in txt: current_cat = '國家安全'
            elif '【社會議題】' in txt: current_cat = '社會議題'
            elif '【母語議題】' in txt: current_cat = '母語議題'
            elif '【台語相關雜文】' in txt: current_cat = '台語相關雜文'
            elif '分類文章表格' in txt or '索引' in txt:
                # Finish previous article if any
                if current_title:
                    sections.append(finish_article(current_sec_num, current_cat, current_title, article_elements))
                    current_sec_num += 1
                    current_title = ""
                    article_elements = []
                idx += 1
                break
            idx += 1
            continue
        elif level == '2':
            # Finish previous article
            if current_title:
                sections.append(finish_article(current_sec_num, current_cat, current_title, article_elements))
                current_sec_num += 1
                article_elements = []
            current_title = txt
            idx += 1
            continue
            
    if current_title:
        article_elements.append(elem)
    idx += 1

print(f"Articles built. Last article section: section-{current_sec_num - 1}")

# Now build Section 242: Classified Article Index
index_elements = []
postscript_elements = []
in_postscript = False

while idx < len(elements):
    elem = elements[idx]
    tag = elem.tag.split('}')[-1]
    txt = "".join(elem.itertext()).strip()
    
    if '*後記' in txt or '國家圖書館出版品預行編目' in txt:
        in_postscript = True
        
    if in_postscript:
        postscript_elements.append(elem)
    else:
        index_elements.append(elem)
    idx += 1

# Process Index Section
index_body = []
for el in index_elements:
    t = el.tag.split('}')[-1]
    if t == 'p':
        p_str = extract_node_html(el).strip()
        if p_str: index_body.append(f"<p>{p_str}</p>")
    elif t == 'table':
        # Custom process table to add click links
        table_html = []
        is_first = True
        for row in el.findall('.//{urn:oasis:names:tc:opendocument:xmlns:table:1.0}table-row'):
            cells = []
            cell_tag = 'th' if is_first else 'td'
            for cell in row.findall('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}table-cell'):
                cell_txt = "".join(cell.itertext()).strip()
                cell_p_html = []
                for p in cell.findall('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p'):
                    p_content = extract_node_html(p).strip()
                    if p_content: cell_p_html.append(p_content)
                combined = "<br>".join(cell_p_html)
                
                # Check if this cell matches any article title
                clean_lookup = cell_txt.replace('\u200b', '').strip()
                target_id = heading_to_id.get(clean_lookup)
                if not target_id and '》' in clean_lookup:
                    target_id = heading_to_id.get(clean_lookup.split('》', 1)[-1].strip())
                    
                if target_id and not is_first:
                    cells.append(f'<{cell_tag} class="table-link-cell" onclick="activateSection(\'{target_id}\')"><a href="#{target_id}" class="table-jump-link">{combined}</a></{cell_tag}>')
                else:
                    cells.append(f'<{cell_tag}>{combined}</{cell_tag}>')
                    
            if cells:
                table_html.append("<tr>" + "".join(cells) + "</tr>")
            is_first = False
        index_body.append("<div class='table-container index-table-wrap'><table class='book-table index-table'><tbody>" + "".join(table_html) + "</tbody></table></div>")

sections.append({
    'id': 'section-242',
    'title': '分類文章表格 (索引)',
    'short_title': '分類文章表格 (索引)',
    'category': '分類文章索引',
    'type': 'index',
    'content_html': f'''
    <div class="article-header">
        <span class="category-badge cat-index">分類索引</span>
        <h1 class="article-title">分類文章表格 (索引)</h1>
        <p class="index-subtitle">點擊任一文章標題可立即跳轉至該篇閱讀</p>
    </div>
    <div class="article-body">
        {"".join(index_body)}
    </div>
    <div class="article-footer-nav">
        <button class="nav-btn prev-btn" onclick="activateSection('section-241')">← 上一篇</button>
        <button class="nav-btn next-btn" onclick="activateSection('section-243')">後記與版權頁 →</button>
    </div>
    '''
})

# Process Postscript & Copyright
ps_body = []
for el in postscript_elements:
    t = el.tag.split('}')[-1]
    if t == 'p':
        p_str = extract_node_html(el).strip()
        if p_str:
            if '國家圖書館出版品預行編目' in p_str:
                ps_body.append(f'<h3 class="cip-title">{p_str}</h3>')
            elif p_str.startswith('*後記：') or p_str.startswith('*後記'):
                ps_body.append(f'<h2 class="postscript-title">{p_str}</h2>')
            elif '書名：' in p_str or '作者：' in p_str:
                ps_body.append(f'<p class="copyright-item">{p_str}</p>')
            else:
                ps_body.append(f'<p>{p_str}</p>')
    elif t == 'table':
        ps_body.append(extract_table_html(el))

sections.append({
    'id': 'section-243',
    'title': '後記與版權頁',
    'short_title': '後記與版權頁',
    'category': '後記與版權',
    'type': 'copyright',
    'content_html': f'''
    <div class="article-header">
        <span class="category-badge cat-copyright">版權聲明</span>
        <h1 class="article-title">後記與版權頁</h1>
    </div>
    <div class="article-body copyright-body">
        {"".join(ps_body)}
    </div>
    <div class="article-footer-nav">
        <button class="nav-btn prev-btn" onclick="activateSection('section-242')">← 分類文章索引</button>
        <button class="nav-btn next-btn" onclick="activateSection('section-0')">回到封面 ⌂</button>
    </div>
    '''
})

print(f"Total sections constructed: {len(sections)}")

# Build Sidebar Navigation HTML
nav_items_html = []
for s in sections:
    sec_id = s['id']
    title = s['title']
    cat = s['category']
    date = s.get('date', '')
    is_tw = s.get('is_taiwanese', False)
    if date:
        date_clean = re.sub(r'^[^\d]*', '', date)
    else:
        date_clean = ''
        
    badge_type = 'preface' if cat == '序言' else (
        'security' if cat == '國家安全' else (
            'society' if cat == '社會議題' else (
                'mother' if cat == '母語議題' else (
                    'taiwanese' if cat == '台語相關雜文' else (
                        'cover' if cat == '封面導讀' else 'other'
                    )
                )
            )
        )
    )
    
    tw_indicator = '<span class="nav-tw-indicator" title="台語漢羅篇章">台</span>' if is_tw else ''

    nav_items_html.append(f'''
    <li class="nav-item" data-target="{sec_id}" data-category="{cat}" data-search="{html.escape(title.lower())} {html.escape(date_clean)}{' 台語 漢羅' if is_tw else ''}">
        <div class="nav-item-header">
            <span class="nav-cat-dot dot-{badge_type}"></span>
            <span class="nav-item-title">{title}</span>
            {tw_indicator}
        </div>
        {f'<div class="nav-item-sub">{html.escape(date_clean[:10])}</div>' if date_clean else ''}
    </li>
    ''')

# Build Main Content Sections HTML
content_sections_html = []
for i, s in enumerate(sections):
    is_active = " active" if i == 0 else ""
    content_sections_html.append(f'''
    <section id="{s['id']}" class="book-section{is_active}" data-category="{s['category']}">
        {s['content_html']}
    </section>
    ''')

# Assemble index.html with Reading Mode and Dictionary Mode
index_html = f'''<!DOCTYPE html>
<html lang="zh-Hant-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>護國 - 評論集（台-華）| 杜信龍</title>
    <meta name="description" content="《護國 評論集（台-華）》杜信龍 (Tō͘ Sìn-Liông) 著。收錄 2014-2026 年於民報、自由時報發表之 240 篇政經國安、社會改革、母語復振評論。支援台語詞典模式。">
    <meta name="author" content="杜信龍 (Tō͘ Sìn-Liông)">
    
    <!-- Open Graph for sharing on Social Media -->
    <meta property="og:title" content="護國 - 評論集（台-華）| 杜信龍">
    <meta property="og:description" content="《護國 評論集（台-華）》杜信龍 著。收錄 2014-2026 年 240 篇深度時論，內建 8,139 條台語詞典模式。">
    <meta property="og:type" content="book">
    <meta property="og:image" content="images/cover.jpg">

    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600;700&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    
    <!-- Stylesheet -->
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <!-- Top Progress Bar -->
    <div id="read-progress-bar" class="progress-bar"></div>

    <div class="app-container">
        <!-- Sidebar Navigation -->
        <aside id="sidebar" class="sidebar">
            <div class="sidebar-header">
                <div class="app-mode-switch">
                    <button id="btn-mode-read" class="mode-btn active" onclick="switchAppMode('read')">📖 閱讀模式</button>
                    <button id="btn-mode-dict" class="mode-btn" onclick="switchAppMode('dict')">📚 台語字典</button>
                </div>

                <div class="header-brand">
                    <span class="brand-badge">EBOOK</span>
                    <h2 class="book-logo">護國 評論集</h2>
                    <p class="book-author">杜信龍 (Tō͘ Sìn-Liông) 著</p>
                </div>

                <!-- Reading Mode Sidebar Controls -->
                <div id="sidebar-read-controls">
                    <!-- Search Input -->
                    <div class="search-box-wrap">
                        <input type="text" id="search-input" placeholder="🔍 搜尋 240 篇標題/日期/台語..." autocomplete="off" />
                        <button id="search-clear-btn" class="search-clear-btn" title="清除搜尋">✕</button>
                    </div>

                    <!-- Filter Category Tabs -->
                    <div class="category-tabs" id="category-tabs">
                        <button class="cat-tab active" data-cat="all">全部 <span class="tab-count">244</span></button>
                        <button class="cat-tab" data-cat="國家安全">國安 <span class="tab-count">100</span></button>
                        <button class="cat-tab" data-cat="社會議題">社會 <span class="tab-count">62</span></button>
                        <button class="cat-tab" data-cat="母語議題">母語 <span class="tab-count">55</span></button>
                        <button class="cat-tab" data-cat="台語相關雜文">雜文 <span class="tab-count">23</span></button>
                    </div>
                </div>

                <!-- Dictionary Mode Sidebar Quick Stats -->
                <div id="sidebar-dict-controls" style="display: none;">
                    <div class="dict-quick-guide">
                        <p class="dict-quick-title">📚 台語文辭典快速導覽</p>
                        <p class="dict-quick-text">涵蓋杜信龍老師作品 8,139+ 條詞目，專為<strong>全羅、漢羅、白話字 (POJ) 與教育部台羅 (Tâi-lô)</strong> 研製。</p>
                        <button class="btn btn-primary btn-dict-all" onclick="resetDictSearch()">顯示全部詞條 A-Z</button>
                    </div>
                </div>
            </div>

            <!-- Scrollable Nav List (for Reading Mode) -->
            <ul id="nav-list" class="nav-list">
                {"".join(nav_items_html)}
            </ul>
            
            <div class="sidebar-footer">
                <span class="sidebar-copy">史秀里冊房 © 2026 · 杜信龍</span>
            </div>
        </aside>

        <!-- Sidebar Backdrop Overlay (Mobile) -->
        <div id="sidebar-overlay" class="overlay"></div>

        <!-- Main Content Area -->
        <main id="main-content" class="content">
            <!-- Mobile Header Bar -->
            <header class="mobile-header">
                <button id="menu-toggle" class="menu-toggle" aria-label="打開目錄">
                    <span class="hamburger-icon">☰</span> 目錄
                </button>
                <div class="mobile-mode-pills">
                    <button class="mobile-mode-btn active" id="m-btn-read" onclick="switchAppMode('read')">📖 閱讀</button>
                    <button class="mobile-mode-btn" id="m-btn-dict" onclick="switchAppMode('dict')">📚 字典</button>
                </div>
            </header>

            <!-- VIEW 1: Reading Mode (Book Articles) -->
            <div id="read-view" class="main-view active">
                <div class="sections-container">
                    {"".join(content_sections_html)}
                </div>
            </div>

            <!-- VIEW 2: Dictionary Mode (Tâi-gí Sû-tián) -->
            <div id="dict-view" class="main-view" style="display: none;">
                <div class="dict-container">
                    <header class="dict-header-banner">
                        <div class="dict-banner-content">
                            <span class="badge badge-primary">Tâi-gí Sû-tián</span>
                            <h2 class="dict-view-title">台語詞典 · 全羅／漢羅模式</h2>
                            <p class="dict-view-desc">專為本書《護國 評論集》台語文、全羅與漢羅篇章量身研製 · 支援台語漢字、白話字 (POJ)、台羅 (Tâi-lô) 與數字調</p>
                        </div>
                        <div class="dict-banner-actions">
                            <button class="btn btn-outline" onclick="switchAppMode('read')">← 返回閱讀文章</button>
                        </div>
                    </header>

                    <div class="dict-search-panel">
                        <div class="dict-mode-subtabs">
                            <button id="tab-dict" class="dict-subtab active">📖 詞典查詞</button>
                            <button id="tab-help" class="dict-subtab">ℹ️ 台羅/白話字音標說明</button>
                        </div>

                        <div id="dict-search-controls">
                            <div class="dict-input-wrap">
                                <input type="text" id="dict-search" class="dict-search-box" placeholder="🔍 輸入台語漢字 (如 食、代誌、作穡) 或 拼音 (如 chiah8, taigi, seng-te)..." autocomplete="off" />
                                <button id="dict-clear-btn" class="dict-clear-btn" title="清除">✕</button>
                            </div>
                            <div class="dict-search-tips">
                                💡 支援多種輸入：漢字（<span class="tip-pill">食</span>、<span class="tip-pill">作穡</span>、<span class="tip-pill">好朋友</span>）、白話字（<span class="tip-pill">chia̍h</span>）、台羅（<span class="tip-pill">tsia̍h</span>）、數字調（<span class="tip-pill">tai5-gi2</span>）或無調號（<span class="tip-pill">chiah</span>）
                            </div>

                            <div class="dict-meta-row">
                                <div id="stat-line" class="dict-stat-line">載入字典資料庫中...</div>
                                <div class="dict-sort-box">
                                    <span class="sort-label">排序方式：</span>
                                    <button id="sort-toggle-btn" class="sort-toggle-btn">出現頻率 ▾</button>
                                </div>
                            </div>

                            <div id="letter-grid" class="letter-grid"></div>
                        </div>
                    </div>

                    <!-- Dynamic Dictionary Results / Detail Area -->
                    <div id="content-inner" class="dict-content-inner">
                        <div class="dict-loading-box">
                            <div class="dict-spinner"></div>
                            <p>正在載入台語詞典資料庫 (8,139 條詞目)...</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Back to top button -->
            <button id="back-to-top" class="back-to-top-btn" title="回到頁首">↑</button>
        </main>
    </div>

    <!-- Floating Tools Control (Theme & Font Adjust & Mode Switch) -->
    <div class="floating-controls">
        <button id="floating-dict-toggle" class="control-btn dict-toggle-btn" title="切換台語字典模式" onclick="toggleAppMode()">📚 字典</button>
        <button id="font-decrease-btn" class="control-btn" title="縮小字體">A-</button>
        <button id="font-increase-btn" class="control-btn" title="放大字體">A+</button>
        <button id="theme-toggle-btn" class="control-btn theme-toggle" title="切換深淺模式">🌙</button>
    </div>

    <!-- Reader & Dictionary Script -->
    <script src="script.js"></script>
</body>
</html>
'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(index_html)

print("Generated index.html with Dictionary Mode successfully")

