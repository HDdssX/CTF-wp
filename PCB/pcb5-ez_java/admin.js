/* ===========================================
   å·¥å·å½æ°
=========================================== */

// ç®æ fetch åè£
async function api(url, method = 'GET', body = null) {
    const opt = { method };
    if (body) opt.body = body;

    const res = await fetch(`/admin${url}`, opt);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function api2(url, method = 'GET', body = null) {
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

// HTML è½¬ä¹ï¼ç¨äºé¢è§ææ¬æä»¶ï¼
function escapeHtml(s){
    return s.replace(/[&<>"']/g, c => ({
        '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
    }[c]));
}


/* ===========================================
   1. å è½½æä»¶æ 
=========================================== */

async function loadFiles() {
    try {
        const list = await api2('/list');
        renderFileTree(list, document.getElementById('fileList'));
        loadStats();
        loadRecent();
    } catch (err) {
        showMessage('uploadMsg', 'Failed to load file list: ' + err, true);
    }
}


// æ¸²ææä»¶æ ï¼å å¥æä½æé® + å³é®èåï¼
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

        /* ========= æä»¶ / ç®å½åç§° ========= */
        const nameSpan = document.createElement('span');
        nameSpan.classList.add('file-name');
        const icon = item.isDir ? "ð" : "ð";
        nameSpan.textContent = `${icon} ${item.name}`;
        li.appendChild(nameSpan);


        /* ========= æä»¶æä½æé® ========= */
        const ops = document.createElement('span');
        ops.classList.add('file-ops');

        if (!item.isDir) {
            // ä¸è½½
            const btnDownload = document.createElement('button');
            btnDownload.textContent = "â¬";
            btnDownload.title = "Download";
            btnDownload.onclick = (e) => {
                e.stopPropagation();
                window.open(`/dashboard/download?path=${item.path}`);
            };
            ops.appendChild(btnDownload);
        }

        // éå½å
        const btnRename = document.createElement('button');
        btnRename.textContent = "âï¸";
        btnRename.title = "Rename";
        btnRename.onclick = (e) => {
            e.stopPropagation();
            renameFile(item.path);
        };
        ops.appendChild(btnRename);

        // å é¤
        const btnDelete = document.createElement('button');
        btnDelete.textContent = "ðï¸";
        btnDelete.title = "Delete";
        btnDelete.onclick = (e) => {
            e.stopPropagation();
            deleteFile(item.path);
        };
        ops.appendChild(btnDelete);

        li.appendChild(ops);


        /* ========= æä»¶ç¹å»ï¼é¢è§ ========= */
        if (!item.isDir) {
            nameSpan.addEventListener('click', () => previewFile(item));
        }


        /* ========= ç®å½éå½ ========= */
        if (item.isDir) {

            // å­ç®å½åºå
            const subUL = document.createElement('ul');
            subUL.style.display = 'none';
            li.appendChild(subUL);

            // ç¹å»å±å¼ / æ¶èµ·
            nameSpan.addEventListener('click', (e) => {
                e.stopPropagation();
                subUL.style.display = subUL.style.display === 'none' ? 'block' : 'none';
            });

            // éå½æ¸²æ
            renderFileTree(item.children, subUL);

            // å³é®èåï¼ç®å½ï¼
            li.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                showMenu(e.pageX, e.pageY, [
                    { label: "New Folder", action: () => createFolderAt(item.path) },
                    { label: "Upload to this folder", action: () => uploadToFolder(item.path) },
                    { label: "Rename", action: () => renameFile(item.path) },
                    { label: "Delete", action: () => deleteFile(item.path) }
                ]);
            });

        } else {

            // å³é®èåï¼æä»¶ï¼
            li.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                showMenu(e.pageX, e.pageY, [
                    { label: "Download", action: () => window.open(`/dashboard/download?path=${item.path}`) },
                    { label: "Rename", action: () => renameFile(item.path) },
                    { label: "Delete", action: () => deleteFile(item.path) },
                ]);
            });
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
        box.innerHTML = `<img src="/dashboard/download?path=${file.path}" style="max-width:100%;">`;
        return;
    }

    // ææ¬æä»¶é¢è§
    const res = await fetch(`/dashboard/download?path=${file.path}`);
    const text = await res.text();
    box.innerHTML = `<pre style="white-space: pre-wrap;">${escapeHtml(text)}</pre>`;
}


/* ===========================================
   3. ä¸ä¼ æä»¶
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

        await loadFiles();
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
   6. æ°å»ºç®å½ï¼å¨æå®ç®å½ä¸ï¼
=========================================== */

async function createFolderAt(parentPath) {
    const name = prompt('Folder name:');
    if (!name) return;

    const full = parentPath + "/" + name;
    const form = new FormData();
    form.append('path', full);

    try {
        await api('/mkdir', 'POST', form);
        await loadFiles();
    } catch (err) {
        alert('Create folder failed: ' + err);
    }
}


/* ===========================================
   7. ä¸ä¼ å°æå®ç®å½
=========================================== */

function uploadToFolder(path) {
    const input = document.createElement('input');
    input.type = "file";

    input.onchange = async () => {
        const form = new FormData();
        form.append("file", input.files[0]);
        form.append("path", path);

        try {
            await fetch('/dashboard/upload', {
                method: 'POST',
                body: form
            });
            await loadFiles();
        } catch (err) {
            alert("Upload failed: " + err);
        }
    };

    input.click();
}


/* ===========================================
   8. ç»è®¡
=========================================== */

async function loadStats() {
    const stat = await api2('/stats');
    document.getElementById('stat-total-files').textContent = stat.files;
    document.getElementById('stat-total-folders').textContent = stat.folders;
    document.getElementById('stat-storage').textContent =
        (stat.size / 1024 / 1024).toFixed(2) + ' MB';
}


/* ===========================================
   9. æè¿ä¿®æ¹
=========================================== */

async function loadRecent() {
    const recent = await api2('/recent');
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
   10. æ°å»ºæä»¶ç®å½
=========================================== */

document.querySelector(".new-folder-btn").addEventListener("click", async () => {
    const folderName = prompt("Enter new folder name:");
    if (!folderName) return;

    const form = new FormData();
    form.append("path", folderName);

    try {
        const res = await fetch("/admin/mkdir", {
            method: "POST",
            body: form
        });
        const result = await res.json();

        if (result.error) {
            alert("Create folder failed: " + result.error);
        } else if (result.mkdir) {
            alert("Folder created!");
            loadFiles(); // å·æ°åè¡¨
        }
    } catch (err) {
        alert("Create folder failed: " + err);
    }
});

document.querySelector(".change-res-dir-btn").addEventListener("click", () => {
    const newPath = prompt("Enter new static resource directory:");

    if (!newPath) {
        alert("Canceled");
        return;
    }

    fetch("/admin/challengeResourceDir", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: "new-path=" + encodeURIComponent(newPath)
    })
        .then(r => r.json())
        .then(data => {
            alert("Resource directory updated to:\n" + data.challengeResourceDir);
        })
        .catch(err => {
            alert("Failed to update resourceDir: " + err);
        });
});
/* ===========================================
   åå§å
=========================================== */

document.addEventListener('DOMContentLoaded', () => {
    loadFiles();
    document.querySelector('.refresh-btn').addEventListener('click', loadFiles);
});
