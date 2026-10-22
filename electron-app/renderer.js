const khmerInput = document.getElementById('khmerInput');
const charCount = document.getElementById('charCount');
const wordCount = document.getElementById('wordCount');
const btnPaste = document.getElementById('btnPaste');
const btnClear = document.getElementById('btnClear');
const btnGenerate = document.getElementById('btnGenerate');
const btnGenText = document.getElementById('btnGenText');
const btnSpinner = document.getElementById('btnSpinner');
const serverSelect = document.getElementById('serverSelect');
const statusDot = document.getElementById('statusDot');
const btnHealth = document.getElementById('btnHealth');
const msgBox = document.getElementById('msgBox');
const playerBox = document.getElementById('playerBox');
const audioEl = document.getElementById('audioEl');
const audioMeta = document.getElementById('audioMeta');
const btnSaveFile = document.getElementById('btnSaveFile');
const btnCopyAudioUrl = document.getElementById('btnCopyAudioUrl');
const copyUrlText = document.getElementById('copyUrlText');
const historyList = document.getElementById('historyList');
const accountPoolInfo = document.getElementById('accountPoolInfo');

let currentAudioUrl = '';
let currentAudioBuffer = null;
let currentFilename = '';
let historyItems = [];

// Text stats
khmerInput.addEventListener('input', updateStats);

function updateStats() {
  const text = khmerInput.value;
  charCount.textContent = text.length;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  wordCount.textContent = words;
}

// Paste button
btnPaste.addEventListener('click', async () => {
  try {
    const text = await navigator.clipboard.readText();
    if (text) {
      khmerInput.value = text;
      updateStats();
      showMessage('បានបិទភ្ជាប់អត្ថបទពី Clipboard រួចរាល់ ✓', 'info');
    }
  } catch (err) {
    showMessage('មិនអាចអាន Clipboard បានទេ សូមចុច Ctrl+V ដោយផ្ទាល់', 'error');
  }
});

// Clear button
btnClear.addEventListener('click', () => {
  khmerInput.value = '';
  updateStats();
  msgBox.style.display = 'none';
  playerBox.style.display = 'none';
  audioEl.pause();
});

// Sample buttons
document.querySelectorAll('.chip-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    khmerInput.value = btn.getAttribute('data-text');
    updateStats();
    khmerInput.focus();
  });
});

// Check health / server status
async function checkServer() {
  const baseUrl = serverSelect.value;
  try {
    const res = await fetch(`${baseUrl}/health`, { method: 'GET' });
    if (res.ok) {
      statusDot.className = 'status-dot online';
      loadAccountInfo();
    } else {
      statusDot.className = 'status-dot error';
    }
  } catch (e) {
    statusDot.className = 'status-dot error';
  }
}

async function loadAccountInfo() {
  const baseUrl = serverSelect.value;
  try {
    const res = await fetch(`${baseUrl}/api/accounts`);
    if (res.ok) {
      const data = await res.json();
      accountPoolInfo.innerHTML = `
        <div>ចំនួនគណនីក្នុង Pool: <b>${data.total_accounts}</b></div>
        <div style="font-size:0.75rem; color:#94A3B8; margin-top:4px;">
          ${data.accounts.map(a => `• ${a.email}`).join('<br>')}
        </div>
      `;
    }
  } catch {}
}

btnHealth.addEventListener('click', async () => {
  showMessage('កំពុងពិនិត្យមើលស្ថានភាព Server...', 'info');
  await checkServer();
  if (statusDot.classList.contains('online')) {
    showMessage('Server កំពុងដំណើរការយ៉ាងរលូន (Online & Healthy) ✓', 'info');
  } else {
    showMessage('មិនអាចភ្ជាប់ទៅកាន់ Server បានទេ សូមពិនិត្យមើលម្ដងទៀត', 'error');
  }
});

serverSelect.addEventListener('change', checkServer);

// Generate Speech
btnGenerate.addEventListener('click', async () => {
  const text = khmerInput.value.trim();
  if (!text) {
    showMessage('សូមបញ្ចូល ឬបិទភ្ជាប់អត្ថបទភាសាខ្មែរជាមុនសិន!', 'error');
    khmerInput.focus();
    return;
  }

  const baseUrl = serverSelect.value;
  const format = document.getElementById('formatSelect').value;

  // Reset UI
  msgBox.style.display = 'none';
  playerBox.style.display = 'none';
  btnGenerate.disabled = true;
  btnSpinner.style.display = 'inline-block';

  let seconds = 0;
  btnGenText.textContent = `កំពុងបង្កើតសំឡេង... (0s)`;
  const timer = setInterval(() => {
    seconds++;
    btnGenText.textContent = `កំពុងបង្កើតសំឡេង... (${seconds}s)`;
  }, 1000);

  try {
    const res = await fetch(`${baseUrl}/api/tts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text,
        format: format,
        stream: false,
        auto_rotate: true
      })
    });

    clearInterval(timer);

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'ការបង្កើតសំឡេងបរាជ័យ');
    }

    const data = await res.json();
    if (data.status === 'success' && data.download_url) {
      currentAudioUrl = `${baseUrl}${data.download_url}`;
      currentFilename = data.filename || `khmer_audio_${Date.now()}.mp3`;

      // Fetch buffer for native Electron file saving
      const audioFetch = await fetch(currentAudioUrl);
      currentAudioBuffer = await audioFetch.arrayBuffer();

      // Setup audio element
      audioEl.src = currentAudioUrl;
      const kbSize = data.size_bytes ? (data.size_bytes / 1024).toFixed(1) : '0';
      audioMeta.textContent = `${kbSize} KB • MP3 192kbps`;

      playerBox.style.display = 'flex';
      audioEl.play().catch(() => {});

      // Add to history
      addToHistory({
        text: text,
        filename: currentFilename,
        url: currentAudioUrl,
        size: kbSize,
        time: new Date().toLocaleTimeString()
      });

      showMessage('សំឡេងត្រូវបានបង្កើតជោគជ័យ! ✓', 'info');
    } else {
      throw new Error(data.detail || 'មិនអាចទទួលបានឯកសារសំឡេង');
    }
  } catch (err) {
    clearInterval(timer);
    showMessage(`បរាជ័យ: ${err.message}`, 'error');
  } finally {
    btnGenerate.disabled = false;
    btnSpinner.style.display = 'none';
    btnGenText.textContent = 'បង្កើតសំឡេង (Generate Speech)';
  }
});

// Save to Computer using Native Electron Dialog
btnSaveFile.addEventListener('click', async () => {
  if (!currentAudioBuffer) {
    showMessage('មិនមានឯកសារសំឡេងសម្រាប់រក្សាទុកទេ', 'error');
    return;
  }

  try {
    const result = await window.electronAPI.saveAudioFile({
      filename: currentFilename,
      arrayBuffer: currentAudioBuffer
    });

    if (result.success) {
      showMessage(`ឯកសារត្រូវបានរក្សាទុកនៅ: ${result.filePath} ✓`, 'info');
    }
  } catch (err) {
    showMessage(`មិនអាចរក្សាទុកឯកសារបានទេ: ${err.message}`, 'error');
  }
});

// Copy Audio Link
btnCopyAudioUrl.addEventListener('click', () => {
  if (!currentAudioUrl) return;
  navigator.clipboard.writeText(currentAudioUrl).then(() => {
    copyUrlText.textContent = 'បានចម្លងរួចរាល់! ✓';
    setTimeout(() => { copyUrlText.textContent = 'ចម្លង Link'; }, 2000);
  });
});

function showMessage(text, type) {
  msgBox.textContent = text;
  msgBox.className = `msg-box ${type}`;
  msgBox.style.display = 'block';
}

function addToHistory(item) {
  historyItems.unshift(item);
  renderHistory();
}

function renderHistory() {
  if (historyItems.length === 0) {
    historyList.innerHTML = '<div class="empty-state">មិនទាន់មានប្រវត្តិសំឡេងនៅឡើយទេ</div>';
    return;
  }

  historyList.innerHTML = historyItems.map((item, idx) => `
    <div class="history-item" onclick="loadHistoryItem(${idx})">
      <div class="history-snippet">${escapeHtml(item.text)}</div>
      <div class="history-meta">
        <span>${item.time}</span>
        <span>${item.size} KB</span>
      </div>
    </div>
  `).join('');
}

window.loadHistoryItem = function(idx) {
  const item = historyItems[idx];
  if (!item) return;

  currentAudioUrl = item.url;
  currentFilename = item.filename;
  audioEl.src = item.url;
  audioMeta.textContent = `${item.size} KB • MP3`;
  playerBox.style.display = 'flex';
  audioEl.play().catch(() => {});
};

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Initial check on startup
checkServer();
setInterval(checkServer, 10000);
