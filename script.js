/**
 * 護國 評論集 - Interactive EBook Web Reader & Tâi-gí Sû-tián (台語詞典)
 * Author: 杜信龍 (Tō͘ Sìn-Liông)
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements - Reader Mode
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.book-section');
    const content = document.getElementById('main-content');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const menuToggle = document.getElementById('menu-toggle');
    const searchInput = document.getElementById('search-input');
    const searchClearBtn = document.getElementById('search-clear-btn');
    const catTabs = document.querySelectorAll('.cat-tab');
    const progressBar = document.getElementById('read-progress-bar');
    const backToTopBtn = document.getElementById('back-to-top');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const fontIncBtn = document.getElementById('font-increase-btn');
    const fontDecBtn = document.getElementById('font-decrease-btn');

    // DOM Elements - Mode Switcher & Views
    const readView = document.getElementById('read-view');
    const dictView = document.getElementById('dict-view');
    const btnModeRead = document.getElementById('btn-mode-read');
    const btnModeDict = document.getElementById('btn-mode-dict');
    const mBtnRead = document.getElementById('m-btn-read');
    const mBtnDict = document.getElementById('m-btn-dict');
    const floatingDictToggle = document.getElementById('floating-dict-toggle');
    const sidebarReadControls = document.getElementById('sidebar-read-controls');
    const sidebarDictControls = document.getElementById('sidebar-dict-controls');

    // DOM Elements - Dictionary Mode
    const dictSearchInput = document.getElementById('dict-search');
    const dictClearBtn = document.getElementById('dict-clear-btn');
    const dictStatLine = document.getElementById('stat-line');
    const dictLetterGrid = document.getElementById('letter-grid');
    const dictSortBtn = document.getElementById('sort-toggle-btn');
    const dictContentInner = document.getElementById('content-inner');
    const tabDict = document.getElementById('tab-dict');
    const tabHelp = document.getElementById('tab-help');
    const dictSearchControls = document.getElementById('dict-search-controls');

    let currentAppMode = 'read'; // 'read' or 'dict'
    let currentCategory = 'all';
    let currentSearchTerm = '';
    let currentSectionId = 'section-0';

    // Dictionary State
    let DICT_DATA = null;
    let DICT_META = null;
    let headwords = [];
    let SEARCH_INDEX = [];
    let letterMap = {};
    let letters = [];
    let dictSortMode = 'freq'; // 'freq' or 'alpha'
    let dictCurrentLetter = 'A';
    let dictCurrentQuery = '';
    let dictSubMode = 'dict'; // 'dict' or 'help'
    let isDictLoading = false;
    const PREVIEW_EXAMPLES = 3;

    // -------------------------------------------------------------
    // App Mode Switching (Reading vs Dictionary)
    // -------------------------------------------------------------
    window.switchAppMode = function(mode) {
        if (mode === currentAppMode && mode !== 'dict') return;
        currentAppMode = mode;

        if (mode === 'dict') {
            if (readView) readView.style.display = 'none';
            if (dictView) dictView.style.display = 'block';

            if (btnModeRead) btnModeRead.classList.remove('active');
            if (btnModeDict) btnModeDict.classList.add('active');
            if (mBtnRead) mBtnRead.classList.remove('active');
            if (mBtnDict) mBtnDict.classList.add('active');
            if (floatingDictToggle) {
                floatingDictToggle.textContent = '📖 閱讀';
                floatingDictToggle.title = '切換回文章閱讀模式';
            }

            if (sidebarReadControls) sidebarReadControls.style.display = 'none';
            if (sidebarDictControls) sidebarDictControls.style.display = 'block';

            // Ensure dictionary data is loaded
            initDictionaryMode();

            if (content) content.scrollTop = 0;
            if (window.innerWidth <= 768) closeSidebar();

            if (!window.location.hash.startsWith('#dict')) {
                history.pushState(null, null, '#dict');
            }
        } else {
            // Reading mode
            if (readView) readView.style.display = 'block';
            if (dictView) dictView.style.display = 'none';

            if (btnModeRead) btnModeRead.classList.add('active');
            if (btnModeDict) btnModeDict.classList.remove('active');
            if (mBtnRead) mBtnRead.classList.add('active');
            if (mBtnDict) mBtnDict.classList.remove('active');
            if (floatingDictToggle) {
                floatingDictToggle.textContent = '📚 字典';
                floatingDictToggle.title = '開啟台語字典模式';
            }

            if (sidebarReadControls) sidebarReadControls.style.display = 'block';
            if (sidebarDictControls) sidebarDictControls.style.display = 'none';

            if (content) content.scrollTop = 0;
            if (window.innerWidth <= 768) closeSidebar();

            if (window.location.hash.startsWith('#dict')) {
                history.pushState(null, null, `#${currentSectionId}`);
            }
        }
    };

    window.toggleAppMode = function() {
        switchAppMode(currentAppMode === 'read' ? 'dict' : 'read');
    };

    window.openDictModeWithSelection = function(query) {
        switchAppMode('dict');
        if (query) {
            setTimeout(() => {
                if (dictSearchInput) {
                    dictSearchInput.value = query;
                    dictCurrentQuery = query.trim();
                    if (dictClearBtn) dictClearBtn.style.display = 'block';
                    if (DICT_DATA) renderDictSearch(dictCurrentQuery);
                }
            }, 100);
        }
    };

    window.resetDictSearch = function() {
        switchAppMode('dict');
        if (dictSearchInput) dictSearchInput.value = '';
        dictCurrentQuery = '';
        if (dictClearBtn) dictClearBtn.style.display = 'none';
        if (DICT_DATA) {
            renderDictLetterGrid();
            renderDictLetterView();
        }
    };

    // -------------------------------------------------------------
    // Section Activation Logic (Reading Mode)
    // -------------------------------------------------------------
    window.activateSection = function(targetId) {
        if (!targetId) return;

        // If in dict mode, switch to read mode
        if (currentAppMode !== 'read') {
            switchAppMode('read');
        }

        const targetSection = document.getElementById(targetId);
        if (!targetSection) return;

        // Update active section
        sections.forEach(sec => sec.classList.remove('active'));
        targetSection.classList.add('active');
        currentSectionId = targetId;

        // Update active nav item
        navItems.forEach(item => item.classList.remove('active'));
        const targetNav = document.querySelector(`.nav-item[data-target="${targetId}"]`);
        if (targetNav) {
            targetNav.classList.add('active');
            targetNav.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }

        // Scroll content container to top
        if (content) {
            content.scrollTop = 0;
        }

        // Update URL hash safely without reload
        if (window.location.hash !== `#${targetId}`) {
            history.pushState(null, null, `#${targetId}`);
        }

        // Close sidebar on mobile
        if (window.innerWidth <= 768) {
            closeSidebar();
        }
    };

    // Nav Item Click Listeners
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetId = item.getAttribute('data-target');
            activateSection(targetId);
        });
    });

    // -------------------------------------------------------------
    // Mobile Sidebar Drawer
    // -------------------------------------------------------------
    function openSidebar() {
        sidebar.classList.add('open');
        overlay.classList.add('open');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        overlay.classList.remove('open');
        document.body.style.overflow = '';
    }

    if (menuToggle) menuToggle.addEventListener('click', openSidebar);
    if (overlay) overlay.addEventListener('click', closeSidebar);

    // -------------------------------------------------------------
    // Search & Category Filtering (Reading Mode)
    // -------------------------------------------------------------
    function filterNavItems() {
        const term = currentSearchTerm.trim().toLowerCase();

        navItems.forEach(item => {
            const itemCat = item.getAttribute('data-category');
            const searchData = item.getAttribute('data-search') || '';

            const matchesCat = (currentCategory === 'all') || (itemCat === currentCategory);
            const matchesSearch = (term === '') || (searchData.includes(term));

            if (matchesCat && matchesSearch) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            currentSearchTerm = e.target.value;
            if (searchClearBtn) {
                searchClearBtn.style.display = currentSearchTerm ? 'block' : 'none';
            }
            filterNavItems();
        });
    }

    if (searchClearBtn) {
        searchClearBtn.addEventListener('click', () => {
            searchInput.value = '';
            currentSearchTerm = '';
            searchClearBtn.style.display = 'none';
            filterNavItems();
            searchInput.focus();
        });
    }

    catTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            catTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentCategory = tab.getAttribute('data-cat');
            filterNavItems();
        });
    });

    // -------------------------------------------------------------
    // Reading Progress & Back to Top
    // -------------------------------------------------------------
    if (content) {
        content.addEventListener('scroll', () => {
            const scrollTop = content.scrollTop;
            const scrollHeight = content.scrollHeight - content.clientHeight;
            const progress = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
            
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }

            if (backToTopBtn) {
                if (scrollTop > 350) {
                    backToTopBtn.style.display = 'flex';
                } else {
                    backToTopBtn.style.display = 'none';
                }
            }
        });
    }

    if (backToTopBtn) {
        backToTopBtn.addEventListener('click', () => {
            if (content) {
                content.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
    }

    // -------------------------------------------------------------
    // Dark / Light Mode Toggle
    // -------------------------------------------------------------
    const savedTheme = localStorage.getItem('ebook_hok_kok_theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.body.classList.add('dark-mode');
        if (themeToggleBtn) themeToggleBtn.textContent = '☀️';
    } else {
        document.body.classList.remove('dark-mode');
        if (themeToggleBtn) themeToggleBtn.textContent = '🌙';
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const isDark = document.body.classList.toggle('dark-mode');
            themeToggleBtn.textContent = isDark ? '☀️' : '🌙';
            localStorage.setItem('ebook_hok_kok_theme', isDark ? 'dark' : 'light');
        });
    }

    // -------------------------------------------------------------
    // Font Size Adjuster
    // -------------------------------------------------------------
    let currentFontSize = parseFloat(localStorage.getItem('ebook_font_size')) || 1.125;
    document.documentElement.style.setProperty('--reader-font-size', `${currentFontSize}rem`);

    if (fontIncBtn) {
        fontIncBtn.addEventListener('click', () => {
            if (currentFontSize < 1.45) {
                currentFontSize += 0.05;
                document.documentElement.style.setProperty('--reader-font-size', `${currentFontSize}rem`);
                localStorage.setItem('ebook_font_size', currentFontSize);
            }
        });
    }

    if (fontDecBtn) {
        fontDecBtn.addEventListener('click', () => {
            if (currentFontSize > 0.95) {
                currentFontSize -= 0.05;
                document.documentElement.style.setProperty('--reader-font-size', `${currentFontSize}rem`);
                localStorage.setItem('ebook_font_size', currentFontSize);
            }
        });
    }

    // -------------------------------------------------------------
    // DICTIONARY MODE ENGINE (Tâi-gí Sû-tián)
    // -------------------------------------------------------------
    function stripDiacritics(s) {
        return s.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    }

    function baseLetter(rom) {
        const s = stripDiacritics(rom.toLowerCase());
        for (const ch of s) {
            if (/[a-z]/.test(ch)) return ch.toUpperCase();
        }
        return '#';
    }

    function extractVariants(rom) {
        const syls = rom.trim().split(/[-\s]+/);
        const cleanSyls = [];
        
        for (const syl of syls) {
            let s = syl.toLowerCase().replace(/[^a-z0-9\u00a0-\u024f\u0300-\u036f\u0358\u2070-\u209f]/g, '');
            if (!s) continue;
            
            const hasNasal = s.includes('ⁿ') || s.includes('\u207f');
            s = s.replace(/ⁿ|\u207f/g, '');
            
            const nfd = s.normalize('NFD');
            let tone = 0;
            if (nfd.includes('\u0301')) tone = 2;
            else if (nfd.includes('\u0300')) tone = 3;
            else if (nfd.includes('\u0302')) tone = 5;
            else if (nfd.includes('\u030c')) tone = 6;
            else if (nfd.includes('\u0304')) tone = 7;
            else if (nfd.includes('\u030d') || nfd.includes('\u030a')) tone = 8;
            else if (nfd.includes('\u030b')) tone = 9;
            
            let cleanNfd = nfd.replace(/[\u0300-\u036f]/g, '');
            let isOo = false;
            if (cleanNfd.includes('\u0358') || cleanNfd.includes('o͘') || cleanNfd.includes('o·')) {
                isOo = true;
                cleanNfd = cleanNfd.replace(/\u0358|·/g, '');
            }
            
            let base = cleanNfd.normalize('NFC');
            if (isOo) base = base.replace(/o+/g, 'oo');
            
            let basePoj = base + (hasNasal ? 'nn' : '');
            
            if (tone === 0) {
                if (/[ptkh]$/.test(basePoj)) tone = 4;
                else tone = 1;
            } else if (tone === 7 && /[ptkh]$/.test(basePoj)) {
                tone = 8;
            }
            
            let baseTl = basePoj
                .replace(/chh/g, 'tsh')
                .replace(/ch/g, 'ts')
                .replace(/oa/g, 'ua')
                .replace(/oe/g, 'ue')
                .replace(/eng/g, 'ing')
                .replace(/ek/g, 'ik');
                
            cleanSyls.push({
                basePoj,
                baseTl,
                tone: String(tone)
            });
        }
        
        if (cleanSyls.length === 0) return [rom.toLowerCase()];
        
        const pojNoToneHyphen = cleanSyls.map(x => x.basePoj).join('-');
        const pojNoToneFlat = cleanSyls.map(x => x.basePoj).join('');
        const tlNoToneHyphen = cleanSyls.map(x => x.baseTl).join('-');
        const tlNoToneFlat = cleanSyls.map(x => x.baseTl).join('');
        
        const pojNumHyphen = cleanSyls.map(x => x.basePoj + x.tone).join('-');
        const pojNumFlat = cleanSyls.map(x => x.basePoj + x.tone).join('');
        const tlNumHyphen = cleanSyls.map(x => x.baseTl + x.tone).join('-');
        const tlNumFlat = cleanSyls.map(x => x.baseTl + x.tone).join('');
        
        const rawLower = rom.toLowerCase();
        const rawFlat = rawLower.replace(/[^a-z0-9]/g, '');
        
        return [
            pojNoToneHyphen, pojNoToneFlat,
            tlNoToneHyphen, tlNoToneFlat,
            pojNumHyphen, pojNumFlat,
            tlNumHyphen, tlNumFlat,
            rawLower, rawFlat
        ];
    }

    async function initDictionaryMode() {
        if (DICT_DATA) {
            if (!dictCurrentQuery) {
                renderDictLetterGrid();
                renderDictLetterView();
            }
            return;
        }

        if (isDictLoading) return;
        isDictLoading = true;

        try {
            if (dictStatLine) dictStatLine.textContent = '載入字典資料庫中 (約 4 MB)...';
            
            const [dataRes, metaRes] = await Promise.all([
                fetch('dict_data.json'),
                fetch('dict_meta.json').catch(() => null)
            ]);

            DICT_DATA = await dataRes.json();
            DICT_META = metaRes ? await metaRes.json() : { word_headwords: 8060, phrase_headwords: 79 };
            headwords = Object.keys(DICT_DATA);

            // Build search index and letter index
            SEARCH_INDEX = [];
            letterMap = {};

            headwords.forEach(h => {
                const primaryRom = DICT_DATA[h].readings[0].rom;
                const l = baseLetter(primaryRom);
                (letterMap[l] = letterMap[l] || []).push(h);

                const variants = new Set();
                DICT_DATA[h].readings.forEach(r => {
                    extractVariants(r.rom).forEach(v => variants.add(v));
                });
                SEARCH_INDEX.push({ han: h, variants: Array.from(variants) });
            });

            letters = Object.keys(letterMap).sort();
            dictCurrentLetter = letters[0] || 'A';

            if (dictStatLine) {
                dictStatLine.textContent = `${headwords.length.toLocaleString()} 條台語詞目，涵蓋漢字、白話字與台羅拼音`;
            }

            renderDictLetterGrid();
            if (dictCurrentQuery) {
                renderDictSearch(dictCurrentQuery);
            } else {
                renderDictLetterView();
            }
        } catch (err) {
            console.error('Error loading dictionary:', err);
            if (dictContentInner) {
                dictContentInner.innerHTML = `<div class="empty-state">載入詞典資料失敗，請確認網路連線或稍後重試。<br><small>${err.message}</small></div>`;
            }
        } finally {
            isDictLoading = false;
        }
    }

    function renderDictLetterGrid() {
        if (!dictLetterGrid) return;
        dictLetterGrid.innerHTML = '';
        letters.forEach(l => {
            const btn = document.createElement('div');
            btn.className = 'letter-btn' + (l === dictCurrentLetter && !dictCurrentQuery ? ' active' : '');
            btn.textContent = l;
            btn.addEventListener('click', () => {
                dictCurrentQuery = '';
                if (dictSearchInput) dictSearchInput.value = '';
                if (dictClearBtn) dictClearBtn.style.display = 'none';
                dictCurrentLetter = l;
                renderDictLetterGrid();
                renderDictLetterView();
            });
            dictLetterGrid.appendChild(btn);
        });
    }

    function sortedDictWords(list) {
        const arr = [...list];
        if (dictSortMode === 'freq') {
            arr.sort((a, b) => DICT_DATA[b].total - DICT_DATA[a].total);
        } else {
            arr.sort((a, b) => DICT_DATA[a].readings[0].rom.localeCompare(DICT_DATA[b].readings[0].rom));
        }
        return arr;
    }

    function entryCardHTML(h) {
        const d = DICT_DATA[h];
        if (!d) return '';
        const r = d.readings[0];
        return `<div class="entry-card${d.phrase ? ' phrase' : ''}" data-han="${h}">
            ${d.phrase ? '<div class="phrase-badge">整句補遺</div>' : ''}
            <div class="han">${h}</div>
            <div class="rom">${r.rom}</div>
            <div class="freq">出現 ${d.total} 次</div>
        </div>`;
    }

    function attachDictCardHandlers() {
        if (!dictContentInner) return;
        dictContentInner.querySelectorAll('.entry-card').forEach(card => {
            card.addEventListener('click', () => renderDictDetail(card.dataset.han));
        });
    }

    function renderDictLetterView() {
        if (!dictContentInner) return;
        const words = sortedDictWords(letterMap[dictCurrentLetter] || []);
        dictContentInner.innerHTML = `
            <div class="dict-section-title">
                <span>字母 ${dictCurrentLetter} — 共 ${words.length} 條詞目</span>
            </div>
            <div class="entry-grid">${words.slice(0, 400).map(entryCardHTML).join('')}</div>
        `;
        attachDictCardHandlers();
    }

    function renderDictSearch(q) {
        if (!dictContentInner || !DICT_DATA) return;
        const rawQ = q.trim().toLowerCase();
        if (!rawQ) {
            renderDictLetterView();
            return;
        }

        // Direct Han character search
        if (/[\u4e00-\u9fff]/.test(rawQ)) {
            const matches = headwords.filter(h => h.includes(rawQ));
            const words = sortedDictWords(matches);
            if (words.length === 0) {
                dictContentInner.innerHTML = `<div class="empty-state">找無相關台語詞目 · 查無「${q}」<br><small style="color:var(--text-secondary); margin-top:8px; display:inline-block;">可嘗試縮短關鍵字、改用白話字或台羅拼音搜尋</small></div>`;
                return;
            }
            dictContentInner.innerHTML = `
                <div class="dict-section-title">搜尋漢字「${q}」— 找到 ${words.length} 條詞目</div>
                <div class="entry-grid">${words.slice(0, 300).map(entryCardHTML).join('')}</div>
            `;
            attachDictCardHandlers();
            return;
        }

        // Romanization search
        const qNfd = rawQ.normalize('NFD');
        const qStripped = qNfd.replace(/[\u0300-\u036f]/g, '');
        const qClean = qStripped.normalize('NFC').replace(/ⁿ|\u207f/g, 'nn');

        const qTl = qClean
            .replace(/chh/g, 'tsh')
            .replace(/ch/g, 'ts')
            .replace(/oa/g, 'ua')
            .replace(/oe/g, 'ue')
            .replace(/eng/g, 'ing')
            .replace(/ek/g, 'ik');

        const qPoj = qClean
            .replace(/tsh/g, 'chh')
            .replace(/ts/g, 'ch')
            .replace(/ua/g, 'oa')
            .replace(/ue/g, 'oe')
            .replace(/ing/g, 'eng')
            .replace(/ik/g, 'ek');

        const qTargets = new Set([
            rawQ,
            qClean,
            qClean.replace(/[-\s]/g, ''),
            qTl,
            qTl.replace(/[-\s]/g, ''),
            qPoj,
            qPoj.replace(/[-\s]/g, '')
        ]);

        const targetArr = Array.from(qTargets).filter(t => t.length > 0);

        const matches = [];
        for (const item of SEARCH_INDEX) {
            let matched = false;
            for (const v of item.variants) {
                for (const target of targetArr) {
                    if (v.includes(target)) {
                        matched = true;
                        break;
                    }
                }
                if (matched) break;
            }
            if (matched) matches.push(item.han);
        }

        const words = sortedDictWords(matches);
        if (words.length === 0) {
            dictContentInner.innerHTML = `<div class="empty-state">找無相關詞目 · No matches for "${q}"<br><small style="color:var(--text-secondary); margin-top:8px; display:inline-block;">可嘗試省略聲調（如 taigi）、數字調（如 tai5-gi2）、或使用台羅 (tsiah8) / 白話字 (chiah8)</small></div>`;
            return;
        }
        dictContentInner.innerHTML = `
            <div class="dict-section-title">搜尋拼音「${q}」— 找到 ${words.length} 條詞目</div>
            <div class="entry-grid">${words.slice(0, 300).map(entryCardHTML).join('')}</div>
        `;
        attachDictCardHandlers();
    }

    function exampleHTML(ex, extra) {
        return `<div class="example${extra ? ' extra' : ''}">
            <div class="ex-han">${ex.han}</div>
            <div class="ex-rom">${ex.rom}</div>
            <div class="ex-title">— 《${ex.title}》</div>
        </div>`;
    }

    function readingBlockHTML(r, isPhrase, idx, hanWord) {
        const shown = r.examples.slice(0, PREVIEW_EXAMPLES);
        const rest = r.examples.slice(PREVIEW_EXAMPLES);
        const blockId = `reading-${idx}`;
        return `<div class="reading-block">
            <div class="reading-header">
                <span class="reading-rom">${r.rom}</span>
                <span class="reading-count">${r.count} 次</span>
                <button class="audio-speak-btn" onclick="speakTaiwanese('${r.rom.replace(/'/g, "\\'")}', '${hanWord.replace(/'/g, "\\'")}')">🔊 發音</button>
            </div>
            ${isPhrase ? '<div style="font-size:0.75rem; color:#f59e0b; margin-bottom:8px;">⚠️ 整句層級對應，非逐字切詞，讀音僅供參考。</div>' : ''}
            <div id="${blockId}">
                ${shown.map(ex => exampleHTML(ex, false)).join('')}
                ${rest.map(ex => exampleHTML(ex, true)).join('')}
            </div>
            ${rest.length > 0 ? `<button class="expand-btn" data-target="${blockId}">+ 展開看全部例句（共 ${r.examples.length} 句）</button>` : ''}
        </div>`;
    }

    function renderDictDetail(h) {
        if (!dictContentInner || !DICT_DATA) return;
        const d = DICT_DATA[h];
        if (!d) return;

        const encodedHan = encodeURIComponent(h);
        const moeUrl = `https://sutian.moe.edu.tw/zh-hant/su/?k=${encodedHan}`;
        const chhoeUrl = `https://chhoetaigi.edict.tw/?q=${encodedHan}`;
        const itaigiUrl = `https://itaigi.tw/k/${encodedHan}`;

        dictContentInner.innerHTML = `
            <button class="detail-back" id="dict-back-btn">← 返回詞條列表</button>
            <div class="detail-card">
                <div class="detail-han${d.phrase ? ' phrase' : ''}">${h}</div>
                <div class="detail-count">作品內共出現 ${d.total} 次${d.phrase ? ' · <span class="phrase-badge" style="position:static; vertical-align:2px;">整句補遺</span>' : ''}</div>
                
                <div class="detail-external-links">
                    <a href="${moeUrl}" target="_blank" rel="noopener noreferrer" class="ext-dict-btn">📖 教育部臺灣台語辭典 ↗</a>
                    <a href="${chhoeUrl}" target="_blank" rel="noopener noreferrer" class="ext-dict-btn">🔍 ChhoeTaigi 台語辭典 ↗</a>
                    <a href="${itaigiUrl}" target="_blank" rel="noopener noreferrer" class="ext-dict-btn">🌐 iTaigi 華台對照 ↗</a>
                </div>

                ${d.readings.map((r, idx) => readingBlockHTML(r, d.phrase, idx, h)).join('')}
            </div>
        `;

        const backBtn = document.getElementById('dict-back-btn');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                if (dictCurrentQuery) renderDictSearch(dictCurrentQuery);
                else renderDictLetterView();
            });
        }

        dictContentInner.querySelectorAll('.expand-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const target = document.getElementById(btn.dataset.target);
                if (target) {
                    target.querySelectorAll('.example.extra').forEach(el => el.style.display = 'block');
                    btn.remove();
                }
            });
        });

        if (content) content.scrollTop = 0;
    }

    function renderDictHelp() {
        if (!dictContentInner) return;
        dictContentInner.innerHTML = `
        <div class="help-page">
            <h2>台語詞典與拼音說明 · Tâi-gí Sû-tián Guide</h2>
            <div class="help-card">
                <p>本詞典為<strong>台語文漢羅與全羅對照辭典模式</strong>，語料彙整自杜信龍老師之台語文作品。
                詞條涵蓋台語漢字、白話字（POJ）與教育部臺灣閩南語羅馬字拼音（台羅 Tâi-lô），提供即時例句、出現頻率與發音對照。</p>
            </div>

            <h2>搜尋功能與多格式支援 · How to Search</h2>
            <div class="help-card">
                <ul>
                    <li><strong>漢字搜尋</strong>：輸入漢字（例如 <span class="code-pill">食</span>、<span class="code-pill">作穡</span>、<span class="code-pill">代誌</span>、<span class="code-pill">好朋友</span>），即時列出所有收錄詞目。</li>
                    <li><strong>白話字 (POJ) 搜尋</strong>：輸入含調號白話字（例如 <span class="code-pill">Tâi-gí</span>、<span class="code-pill">chia̍h</span>、<span class="code-pill">lâm-pak</span>）。</li>
                    <li><strong>教育部台羅 (Tâi-lô) 搜尋</strong>：輸入台羅拼音（例如 <span class="code-pill">tsia̍h</span>、<span class="code-pill">tshuì</span>、<span class="code-pill">uē</span>），系統自動轉換對照。</li>
                    <li><strong>聲調數字搜尋 (Numbered Tones)</strong>：可輸入數字調號（例如 <span class="code-pill">tai5-gi2</span>、<span class="code-pill">tsiah8</span>、<span class="code-pill">chiah8</span>、<span class="code-pill">lam5-pak4</span>）。</li>
                    <li><strong>無聲調模糊搜尋 (Tone-free)</strong>：直接輸入純英文字母（例如 <span class="code-pill">taigi</span>、<span class="code-pill">chiah</span>、<span class="code-pill">lampak</span>），連字符與空白皆可省略。</li>
                </ul>
            </div>

            <h2>白話字 (POJ) ↔ 臺灣閩南語羅馬字 (台羅 Tâi-lô) 對照表</h2>
            <div class="help-card">
                <table class="help-table">
                    <thead>
                        <tr><th>項目</th><th>白話字 (POJ)</th><th>台羅拼音 (Tâi-lô)</th><th>範例</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>聲母 (不送氣/送氣)</td><td>ch / chh</td><td>ts / tsh</td><td>chhiú ↔ tshiu2 (手)</td></tr>
                        <tr><td>母音 (開口/圓唇)</td><td>oa / oe</td><td>ua / ue</td><td>oan ↔ uan (冤)</td></tr>
                        <tr><td>閉口韻尾 / 舌根韻尾</td><td>eng / ek</td><td>ing / ik</td><td>seng ↔ sing (生)</td></tr>
                        <tr><td>烏韻母 (O͘)</td><td>o͘ / o·</td><td>oo</td><td>o͘-káu ↔ oo-kau2 (烏狗)</td></tr>
                        <tr><td>鼻化母音 (Nasal)</td><td>aⁿ / iⁿ / oⁿ (ⁿ)</td><td>ann / inn / onn (nn)</td><td>piàⁿ ↔ piann3 (拚)</td></tr>
                    </tbody>
                </table>
            </div>

            <h2>台語聲調與數字調號對照表 · Tone Table</h2>
            <div class="help-card">
                <table class="help-table">
                    <thead>
                        <tr><th>調類</th><th>調名</th><th>調符 (POJ / 台羅)</th><th>數字調號</th><th>範例</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>第 1 調</td><td>陰平</td><td>無調符 (a)</td><td><span class="code-pill">1</span></td><td>tai1 (東 / 衫)</td></tr>
                        <tr><td>第 2 調</td><td>陰上</td><td>尖音符 (á / í / ú)</td><td><span class="code-pill">2</span></td><td>gí2 (語 / 狗)</td></tr>
                        <tr><td>第 3 調</td><td>陰去</td><td>重音符 (à / è / ì)</td><td><span class="code-pill">3</span></td><td>kòe3 (過 / 豹)</td></tr>
                        <tr><td>第 4 調</td><td>陰入</td><td>無調符 + 塞音 (p, t, k, h)</td><td><span class="code-pill">4</span></td><td>pak4 (北 / 鴨)</td></tr>
                        <tr><td>第 5 調</td><td>陽平</td><td>揚抑符 (â / ê / î)</td><td><span class="code-pill">5</span></td><td>tâi5 (台 / 猴)</td></tr>
                        <tr><td>第 7 調</td><td>陽去</td><td>長音符 (ā / ē / ī / ū)</td><td><span class="code-pill">7</span></td><td>nn̄g7 (二 / 象)</td></tr>
                        <tr><td>第 8 調</td><td>陽入</td><td>直標符 (a̍ / e̍ / i̍) + 塞音</td><td><span class="code-pill">8</span></td><td>lia̍p8 (粒 / 鹿)</td></tr>
                    </tbody>
                </table>
            </div>
        </div>`;
    }

    // Web Speech API / TTS
    window.speakTaiwanese = function(rom, han) {
        if (!('speechSynthesis' in window)) {
            alert(`發音：${rom}`);
            return;
        }
        window.speechSynthesis.cancel();
        const textToSpeak = han || rom;
        const ut = new SpeechSynthesisUtterance(textToSpeak);
        ut.lang = 'zh-TW';
        ut.rate = 0.9;
        window.speechSynthesis.speak(ut);
    };

    // Dictionary Controls Listeners
    if (dictSearchInput) {
        dictSearchInput.addEventListener('input', (e) => {
            dictCurrentQuery = e.target.value.trim();
            if (dictClearBtn) dictClearBtn.style.display = dictCurrentQuery ? 'block' : 'none';
            renderDictLetterGrid();
            if (dictCurrentQuery) {
                renderDictSearch(dictCurrentQuery);
            } else {
                renderDictLetterView();
            }
        });
    }

    if (dictClearBtn) {
        dictClearBtn.addEventListener('click', () => {
            dictSearchInput.value = '';
            dictCurrentQuery = '';
            dictClearBtn.style.display = 'none';
            renderDictLetterGrid();
            renderDictLetterView();
            dictSearchInput.focus();
        });
    }

    if (dictSortBtn) {
        dictSortBtn.addEventListener('click', () => {
            dictSortMode = dictSortMode === 'freq' ? 'alpha' : 'freq';
            dictSortBtn.textContent = dictSortMode === 'freq' ? '出現頻率 ▾' : '字母順序 ▾';
            if (dictCurrentQuery) renderDictSearch(dictCurrentQuery);
            else renderDictLetterView();
        });
    }

    if (tabDict && tabHelp) {
        tabDict.addEventListener('click', () => {
            dictSubMode = 'dict';
            tabDict.classList.add('active');
            tabHelp.classList.remove('active');
            if (dictSearchControls) dictSearchControls.style.display = 'block';
            if (dictCurrentQuery) renderDictSearch(dictCurrentQuery);
            else renderDictLetterView();
        });

        tabHelp.addEventListener('click', () => {
            dictSubMode = 'help';
            tabHelp.classList.add('active');
            tabDict.classList.remove('active');
            if (dictSearchControls) dictSearchControls.style.display = 'none';
            renderDictHelp();
        });
    }

    // -------------------------------------------------------------
    // Text Selection Quick Lookup in Articles
    // -------------------------------------------------------------
    let lookupTooltip = null;
    function showQuickLookupTooltip(text, x, y) {
        if (!lookupTooltip) {
            lookupTooltip = document.createElement('div');
            lookupTooltip.className = 'quick-lookup-bubble';
            Object.assign(lookupTooltip.style, {
                position: 'fixed',
                background: '#0284c7',
                color: '#ffffff',
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '0.82rem',
                fontWeight: '600',
                cursor: 'pointer',
                boxShadow: '0 4px 12px rgba(0,0,0,0.25)',
                zIndex: 2000,
                fontFamily: 'sans-serif',
                transition: 'opacity 0.15s, transform 0.15s',
                display: 'none'
            });
            document.body.appendChild(lookupTooltip);
        }

        lookupTooltip.textContent = `🔍 查台語字典「${text.slice(0, 10)}${text.length > 10 ? '...' : ''}」`;
        lookupTooltip.style.left = `${Math.min(window.innerWidth - 180, Math.max(10, x - 50))}px`;
        lookupTooltip.style.top = `${Math.max(10, y - 45)}px`;
        lookupTooltip.style.display = 'block';

        lookupTooltip.onclick = () => {
            lookupTooltip.style.display = 'none';
            openDictModeWithSelection(text);
        };
    }

    document.addEventListener('mouseup', (e) => {
        if (currentAppMode !== 'read') return;
        const sel = window.getSelection();
        const selectedText = sel ? sel.toString().trim() : '';

        if (selectedText && selectedText.length >= 1 && selectedText.length <= 25) {
            showQuickLookupTooltip(selectedText, e.clientX, e.clientY);
        } else if (lookupTooltip && e.target !== lookupTooltip) {
            lookupTooltip.style.display = 'none';
        }
    });

    // -------------------------------------------------------------
    // Keyboard Navigation
    // -------------------------------------------------------------
    document.addEventListener('keydown', (e) => {
        if (document.activeElement === searchInput || document.activeElement === dictSearchInput) return;

        if (e.key === 'Escape') {
            closeSidebar();
            if (lookupTooltip) lookupTooltip.style.display = 'none';
        } else if (e.key === 'ArrowRight' && currentAppMode === 'read') {
            const activeSec = document.querySelector('.book-section.active');
            if (activeSec) {
                const nextBtn = activeSec.querySelector('.next-btn');
                if (nextBtn) nextBtn.click();
            }
        } else if (e.key === 'ArrowLeft' && currentAppMode === 'read') {
            const activeSec = document.querySelector('.book-section.active');
            if (activeSec) {
                const prevBtn = activeSec.querySelector('.prev-btn');
                if (prevBtn) prevBtn.click();
            }
        }
    });

    // -------------------------------------------------------------
    // Hash Routing & Initialization
    // -------------------------------------------------------------
    window.addEventListener('hashchange', () => {
        handleHashRoute();
    });

    function handleHashRoute() {
        const hash = window.location.hash.replace('#', '');
        if (hash === 'dict' || hash.startsWith('dict?')) {
            switchAppMode('dict');
            if (hash.includes('?q=')) {
                const q = decodeURIComponent(hash.split('?q=')[1]);
                openDictModeWithSelection(q);
            }
        } else if (hash && document.getElementById(hash)) {
            activateSection(hash);
        }
    }

    const initHash = window.location.hash.replace('#', '');
    if (initHash === 'dict' || initHash.startsWith('dict?')) {
        handleHashRoute();
    } else if (initHash && document.getElementById(initHash)) {
        activateSection(initHash);
    } else {
        activateSection('section-0');
    }
});
