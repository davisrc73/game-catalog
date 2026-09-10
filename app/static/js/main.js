// Pesquisa: redireciona para a consola atual ou pesquisa global na 1.ª consola.
function doSearch(e){
  e.preventDefault();
  const q = document.getElementById('globalSearch').value.trim();
  const m = location.pathname.match(/\/console\/([^/]+)/);
  if (m){
    location.href = `/console/${m[1]}` + (q ? `?q=${encodeURIComponent(q)}` : '');
  } else if (q){
    // fora de uma consola: vai para a página inicial filtrada não existe,
    // por isso reencaminha para a primeira consola disponível, se houver.
    location.href = `/?` ; // a pesquisa global por consola faz-se dentro da consola
  }
  return false;
}

function toast(msg){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._t);
  t._t = setTimeout(()=>t.classList.remove('show'), 3500);
}

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

// Ao abrir a página, se já houver um scan a decorrer, mostra o estado.
document.addEventListener('DOMContentLoaded', ()=>{
  fetch('/api/status').then(r=>r.json()).then(s=>{
    if (s.scanning){ document.body.dataset.wasScanning='1'; setBusy(true); pollStatus(); }
  }).catch(()=>{});
});
