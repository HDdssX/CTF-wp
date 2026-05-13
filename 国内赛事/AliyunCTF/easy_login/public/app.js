const $ = (id) => document.getElementById(id);

const terminalBody = $('terminalBody');
const currentUser = $('currentUser');

function appendLine(className, text) {
  const line = document.createElement('div');
  line.className = `line ${className}`;
  line.textContent = text;
  terminalBody.appendChild(line);
  terminalBody.scrollTop = terminalBody.scrollHeight;
}

function logRequest(method, path, body) {
  const payload = body ? ` ${JSON.stringify(body)}` : '';
  appendLine('request-line', `$ fetch ${method.toUpperCase()} ${path}${payload}`);
}

function logResponse(status, json) {
  appendLine('meta-line', `< status ${status} >`);
  appendLine('response-line', JSON.stringify(json));
}

function logError(err) {
  appendLine('error-line', `! error: ${err}`);
}

function updateUserLabel(username) {
  if (!username) {
    currentUser.textContent = 'guest';
    currentUser.classList.add('pill-muted');
    return;
  }
  currentUser.textContent = username;
  currentUser.classList.remove('pill-muted');
}

async function callApi(method, path, body) {
  try {
    logRequest(method, path, body);

    const res = await fetch(path, {
      method,
      headers: {
        'Content-Type': 'application/json'
      },
      body: body ? JSON.stringify(body) : undefined,
      credentials: 'same-origin'
    });

    const text = await res.text();
    let json;
    try {
      json = JSON.parse(text);
    } catch {
      json = { raw: text };
    }

    logResponse(res.status, json);
    return { res, json };
  } catch (err) {
    logError(err);
    throw err;
  }
}

window.addEventListener('DOMContentLoaded', () => {
  $('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = $('username').value.trim();
    const password = $('password').value;

    if (!username || !password) {
      logError('username and password required');
      return;
    }

    try {
      const { res, json } = await callApi('post', '/login', { username, password });
      if (res.ok) {
        updateUserLabel(json.username || username);
      }
    } catch (err) {
      console.error(err);
    }
  });

  $('btnLogout').addEventListener('click', async () => {
    try {
      await callApi('post', '/logout');
      updateUserLabel(null);
    } catch (err) {
      console.error(err);
    }
  });

  $('btnMe').addEventListener('click', async () => {
    try {
      const { json } = await callApi('get', '/me');
      if (json && json.loggedIn && json.username) {
        updateUserLabel(json.username);
      } else {
        updateUserLabel(null);
      }
    } catch (err) {
      console.error(err);
    }
  });

  $('btnAdmin').addEventListener('click', async () => {
    try {
      await callApi('get', '/admin');
    } catch (err) {
      console.error(err);
    }
  });

  $('btnVisit').addEventListener('click', async () => {
    const urlInput = $('visitUrl');
    const url = urlInput.value.trim();

    if (!url) {
      logError('url is required for /visit');
      return;
    }

    try {
      await callApi('post', '/visit', { url });
    } catch (err) {
      console.error(err);
    }
  });
});
