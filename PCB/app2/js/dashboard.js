/* ===========================================
   å·¥å·å½æ°
=========================================== */

// ç®æ fetch åè£
async function api(url, method = 'GET', body = null) {
    const opt = { method };
    if (body) opt.body = body;

    const res = await fetch(`/dashboard${url}`, opt);

    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

// æ¾ç¤ºæ¶æ¯
function showMessage(id, msg, isError = false) {
    const box = document.getElementById(id);
    box.innerHTML = msg;
    box.style.color = isError ? 'red' : 'green';
}


/* ===========================================
   1. å è½½æä»¶æ 
=========================================== */

async function loadFiles() {
    try {
        const list = await api('/list');
        renderFileTree(list, document.getElementById('fileList'));
        loadStats();
        loadRecent();
    } catch (err) {
        showMessage('uploadMsg', 'Failed to load file list: ' + err, true);
    }
}

function renderFileTree(files, parentUL) {
    parentUL.innerHTML = '';

    if (!files.length) {
        parentUL.innerHTML = '<li class="empty">No files</li>';
        return;
    }

    files.forEach(item => {
        const li = document.createElement('li');
        li.classList.add('file-item');
        li.dataset.path = item.path;

        // æä»¶å¾æ 
        const icon = item.isDir ? "ð" : "ð";
        li.innerHTML = `${icon} ${item.name}`;

        // æä»¶ç¹å»äºä»¶
        if (!item.isDir) {
            li.addEventListener('click', () => previewFile(item));
        }

        // ç®å½éå½
        if (item.isDir) {
            const subUL = document.createElement('ul');
            subUL.style.display = 'none';
            li.appendChild(subUL);

            // ç¹å»å±å¼/æ¶èµ·
            li.addEventListener('click', () => {
                subUL.style.display = subUL.style.display === 'none' ? 'block' : 'none';
            });

            renderFileTree(item.children, subUL);
        }

        parentUL.appendChild(li);
    });
}


/* ===========================================
   2. æä»¶é¢è§
=========================================== */

async function previewFile(file) {
    const box = document.getElementById('previewBox');
    box.innerHTML = '<i>Loading...</i>';

    const ext = file.name.split('.').pop().toLowerCase();

    if (['png','jpg','jpeg','gif','webp'].includes(ext)) {
        // å¾çé¢è§
        box.innerHTML = `<img src="/dashboard/download?path=${file.path}" style="max-width:100%;">`;
    } else {
        // ææ¬æä»¶é¢è§
        const res = await fetch(`/dashboard/download?path=${file.path}`);
        const text = await res.text();
        box.textContent = text;
    }
}


/* ===========================================
   3. ä¸ä¼ æä»¶ï¼å¢å¼ºï¼è¿åº¦æ¡ï¼
=========================================== */

document.getElementById('uploadForm').addEventListener('submit', async function(e){
    e.preventDefault();

    const box = document.getElementById('uploadMsg');
    box.innerText = 'Uploading...';

    const formData = new FormData(this);

    try {
        const res = await fetch('/dashboard/upload', {
            method: 'POST',
            body: formData
        });

        const json = await res.json();
        showMessage('uploadMsg', 'Upload OK: ' + json.filename);

        await loadFiles(); // å·æ°åè¡¨
    } catch (err) {
        showMessage('uploadMsg', 'Upload Failed: ' + err, true);
    }
});


/* ===========================================
   4. å é¤æä»¶
=========================================== */

async function deleteFile(path) {
    if (!confirm('Delete: ' + path + ' ?')) return;

    const form = new FormData();
    form.append('path', path);

    try {
        await api('/delete', 'POST', form);
        await loadFiles();
    } catch (err) {
        alert('Delete failed: ' + err);
    }
}


/* ===========================================
   5. éå½å
=========================================== */

async function renameFile(oldPath) {
    const newName = prompt('New name:');
    if (!newName) return;

    const form = new FormData();
    form.append('oldPath', oldPath);
    form.append('newName', newName);

    try {
        await api('/rename', 'POST', form);
        await loadFiles();
    } catch (err) {
        alert('Rename failed: ' + err);
    }
}


/* ===========================================
   6. åå»ºç®å½
=========================================== */

async function createFolder() {
    const name = prompt('Folder name:');
    if (!name) return;

    const form = new FormData();
    form.append('path', name);

    try {
        await api('/mkdir', 'POST', form);
        await loadFiles();
    } catch (err) {
        alert('Create folder failed: ' + err);
    }
}


/* ===========================================
   7. è·åç»è®¡æ°æ®
=========================================== */

async function loadStats() {
    const stat = await api('/stats');

    document.getElementById('stat-total-files').textContent = stat.files;
    document.getElementById('stat-total-folders').textContent = stat.folders;
    document.getElementById('stat-storage').textContent = (stat.size / 1024 / 1024).toFixed(2) + ' MB';
}


/* ===========================================
   8. æè¿æ´æ°
=========================================== */

async function loadRecent() {
    const recent = await api('/recent');
    const ul = document.getElementById('recentList');

    ul.innerHTML = '';

    if (!recent.length) {
        ul.innerHTML = '<li class="empty">No recent files</li>';
        return;
    }

    recent.forEach(f => {
        const li = document.createElement('li');
        const date = new Date(f.lastModified).toLocaleString();
        li.textContent = `${f.name} â ${date}`;
        ul.appendChild(li);
    });
}


/* ===========================================
   åå§å
=========================================== */

document.addEventListener('DOMContentLoaded', () => {
    loadFiles();

    document.querySelector('.refresh-btn').addEventListener('click', loadFiles);
});
