// Toast de notificações
function toast(msg){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._t);
  t._t = setTimeout(()=>t.classList.remove('show'), 3500);
}

// Controlo do botão de scan
let pollTimer = null;

async function startScan(){
  const btn = document.getElementById('scanBtn');
  try{
    const r = await fetch('/api/scan', {method:'POST'});
    const data = await r.json();
    if (data.started){
      toast('Scan iniciado…');
      setBusy(true);
      pollStatus();
    } else {
      toast('Já existe um scan em curso.');
      setBusy(true);
      pollStatus();
    }
  }catch(err){
    toast('Erro ao iniciar o scan.');
  }
}

function setBusy(busy){
  const btn = document.getElementById('scanBtn');
  if (!btn) return;
  btn.classList.toggle('busy', busy);
  btn.querySelector('.dot').nextSibling.textContent = busy ? ' A analisar…' : ' Fazer scan';
}

async function pollStatus(){
  clearTimeout(pollTimer);
  try{
    const r = await fetch('/api/status');
    const s = await r.json();
    if (s.scanning){
      setBusy(true);
      pollTimer = setTimeout(pollStatus, 2000);
    } else {
      setBusy(false);
      if (document.body.dataset.wasScanning === '1'){
        toast('Scan concluído.');
        setTimeout(()=>location.reload(), 800);
      }
    }
    document.body.dataset.wasScanning = s.scanning ? '1' : document.body.dataset.wasScanning;
  }catch(err){
    setBusy(false);
  }
}

// ----------------------------------------------------------------------------
// Favoritos (Toggle)
// ----------------------------------------------------------------------------
async function toggleFavorite(gameId, btn, e){
  if (e) {
    e.preventDefault();
    e.stopPropagation();
  }
  if (!gameId || !btn) return;

  btn.disabled = true;
  try {
    const res = await fetch(`/api/game/${encodeURIComponent(gameId)}/favorite`, {
      method: 'POST',
      headers: { 'Accept': 'application/json' }
    });
    const data = await res.json();
    if (data.success) {
      const isFav = data.favorite;
      btn.classList.toggle('active', isFav);

      const btnText = btn.querySelector('.btn-text');
      if (btnText) {
        btnText.textContent = isFav ? 'Favorito' : 'Marcar Favorito';
      }
      btn.title = isFav ? 'Remover dos favoritos' : 'Adicionar aos favoritos';

      document.querySelectorAll(`button[onclick*="'${gameId}'"]`).forEach(other => {
        if (other !== btn) {
          other.classList.toggle('active', isFav);
          const otherText = other.querySelector('.btn-text');
          if (otherText) otherText.textContent = isFav ? 'Favorito' : 'Marcar Favorito';
          other.title = isFav ? 'Remover dos favoritos' : 'Adicionar aos favoritos';
        }
      });

      toast(isFav ? '⭐ Adicionado aos favoritos!' : 'Removido dos favoritos.');
    } else {
      toast('Não foi possível alterar o estado de favorito.');
    }
  } catch (err) {
    toast('Erro de ligação ao atualizar favorito.');
  } finally {
    btn.disabled = false;
  }
}

// ----------------------------------------------------------------------------
// Pesquisa Instantânea ao digitar (Live Search Dropdown)
// ----------------------------------------------------------------------------
let liveSearchTimer = null;

function setupLiveSearch(){
  const input = document.getElementById('globalSearch');
  const dropdown = document.getElementById('searchResultsDropdown');
  if (!input || !dropdown) return;

  input.addEventListener('input', () => {
    clearTimeout(liveSearchTimer);
    const q = input.value.trim();
    if (!q) {
      dropdown.hidden = true;
      dropdown.innerHTML = '';
      return;
    }
    liveSearchTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        renderDropdown(data, q, dropdown);
      } catch (err) {
        dropdown.hidden = true;
      }
    }, 150);
  });

  // Fechar ao clicar fora
  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target) && e.target !== input) {
      dropdown.hidden = true;
    }
  });

  // Reabrir ao focar se tiver texto
  input.addEventListener('focus', () => {
    if (input.value.trim() && dropdown.children.length > 0) {
      dropdown.hidden = false;
    }
  });

  // Fechar com tecla Escape
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      dropdown.hidden = true;
    }
  });
}

function renderDropdown(data, query, dropdown){
  if (!data || !data.results || data.results.length === 0) {
    dropdown.innerHTML = `
      <div style="padding:14px;text-align:center;color:var(--muted);font-size:0.88rem;">
        Nenhum jogo encontrado para “${escapeHtml(query)}”
      </div>
    `;
    dropdown.hidden = false;
    return;
  }

  let html = '';
  data.results.forEach(g => {
    const thumb = g.cover_url
      ? `<img src="${g.cover_url}" alt="${escapeHtml(g.title)}">`
      : `<span>${escapeHtml(g.title[0] || '?').toUpperCase()}</span>`;
    const meta = [g.console, g.year].filter(Boolean).join(' · ');

    html += `
      <a class="search-item" href="${g.url}">
        <div class="search-item-thumb">${thumb}</div>
        <div class="search-item-info">
          <span class="search-item-title">${escapeHtml(g.title)}</span>
          <span class="search-item-meta">${escapeHtml(meta)}</span>
        </div>
      </a>
    `;
  });

  if (data.total > data.results.length) {
    html += `
      <a class="search-item-all" href="/?q=${encodeURIComponent(query)}">
        Ver todos os ${data.total} resultados ➔
      </a>
    `;
  }

  dropdown.innerHTML = html;
  dropdown.hidden = false;
}

function escapeHtml(str){
  if (!str) return '';
  return String(str).replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[m]);
}

// ----------------------------------------------------------------------------
// Definições do Sistema & Testes de API
// ----------------------------------------------------------------------------
async function testSteamGrid(e){
  if (e) e.preventDefault();
  const input = document.getElementById('steamgriddb_api_key');
  const resBox = document.getElementById('sgResult');
  const btn = e ? e.target : null;
  if (!input || !resBox) return;

  const key = input.value.trim();
  resBox.hidden = false;
  resBox.className = 'test-result';
  resBox.textContent = 'A testar ligação à SteamGridDB…';
  if (btn) btn.disabled = true;

  try {
    const res = await fetch('/api/settings/test-steamgrid', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({api_key: key})
    });
    const data = await res.json();
    resBox.className = 'test-result ' + (data.success ? 'success' : 'error');
    resBox.textContent = (data.success ? '✓ ' : '✕ ') + data.message;
  } catch (err) {
    resBox.className = 'test-result error';
    resBox.textContent = '✕ Erro de ligação ao testar a API.';
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function testIgdb(e){
  if (e) e.preventDefault();
  const idInput = document.getElementById('twitch_client_id');
  const secInput = document.getElementById('twitch_client_secret');
  const resBox = document.getElementById('igdbResult');
  const btn = e ? e.target : null;
  if (!idInput || !secInput || !resBox) return;

  const cid = idInput.value.trim();
  const csec = secInput.value.trim();
  resBox.hidden = false;
  resBox.className = 'test-result';
  resBox.textContent = 'A autenticar na Twitch / IGDB…';
  if (btn) btn.disabled = true;

  try {
    const res = await fetch('/api/settings/test-igdb', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({client_id: cid, client_secret: csec})
    });
    const data = await res.json();
    resBox.className = 'test-result ' + (data.success ? 'success' : 'error');
    resBox.textContent = (data.success ? '✓ ' : '✕ ') + data.message;
  } catch (err) {
    resBox.className = 'test-result error';
    resBox.textContent = '✕ Erro de ligação ao autenticar na Twitch.';
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function triggerMissingCovers(e){
  if (e) e.preventDefault();
  const btn = document.getElementById('btnEnrich');
  if (btn) {
    btn.disabled = true;
    btn.textContent = '⏳ A procurar capas…';
  }
  try {
    const res = await fetch('/api/maintenance/fetch-covers', {method: 'POST'});
    const data = await res.json();
    toast(data.message);
    if (data.started) {
      setBusy(true);
      pollStatus();
    }
  } catch (err) {
    toast('Erro ao iniciar a procura de capas.');
  } finally {
    setTimeout(()=>{
      if (btn) btn.disabled = false;
    }, 4000);
  }
}

// Inicialização
document.addEventListener('DOMContentLoaded', ()=>{
  setupLiveSearch();

  fetch('/api/status').then(r=>r.json()).then(s=>{
    if (s.scanning){ document.body.dataset.wasScanning='1'; setBusy(true); pollStatus(); }
  }).catch(()=>{});
});
