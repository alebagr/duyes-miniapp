const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }

const app = document.getElementById('app');
let currentPage = 'home';
let me = null;

function headers() {
  return { 'X-Telegram-Init-Data': tg?.initData || '' };
}
async function api(path, options={}) {
  const res = await fetch(path, { ...options, headers: { ...headers(), ...(options.headers||{}) } });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
function nav(page) {
  currentPage = page;
  document.querySelectorAll('.nav-item').forEach(x => x.classList.toggle('active', x.dataset.page === page));
  render();
}
async function render() {
  try {
    if (!me) { const r = await api('/api/me'); me = r; }
    if (currentPage === 'home') return home();
    if (currentPage === 'search') return search();
    if (currentPage === 'favorites') return favorites();
    if (currentPage === 'chats') return chats();
    if (currentPage === 'profile') return profile();
  } catch (e) {
    app.innerHTML = `<div class="empty"><div style="font-size:42px">⚠️</div><p>Не удалось загрузить Du&Yes.</p><small>${escapeHtml(e.message)}</small></div>`;
  }
}
function home() {
  app.innerHTML = `<section class="hero"><h1>Du&Yes ❤️</h1><p>Серьёзные отношения с целью создания армянской семьи.</p><div class="actions"><button class="btn" onclick="nav('search')">Найти человека</button><button class="btn secondary" onclick="showGifts()">🎁 Подарки</button></div></section><div class="section-title"><h2>Добро пожаловать</h2></div><div class="card"><div class="card-body"><div class="card-title">Безопасность и доверие</div><div class="card-sub">Модерация профилей и фотографий, защита переписки и добровольная верификация личности.</div></div></div>`;
}
async function search() {
  app.innerHTML = '<div class="empty">Загружаем анкеты…</div>';
  const r = await api('/api/profiles');
  const items = r.profiles || [];
  app.innerHTML = `<div class="section-title"><h2>Подходящие анкеты</h2></div>${items.length ? `<div class="grid">${items.map(profileCard).join('')}</div>` : '<div class="empty">Подходящих профилей пока не найдено.</div>'}`;
}
function profileCard(p) {
  const loc = [p.city, p.region, p.country].filter(Boolean).join(', ');
  return `<article class="card"><div class="photo">${p.photo_1_file_id ? '👤' : '♡'}</div><div class="card-body"><div class="card-title">${escapeHtml(p.name||'Пользователь')}, ${p.age||'—'} ${p.verified ? '<span class="verified">✓</span>' : ''}</div><div class="card-sub">${escapeHtml(loc||'')}</div><div class="actions"><button class="btn secondary" onclick="fav(${p.user_id})">♡</button><button class="btn" onclick="openProfile(${p.user_id})">Открыть</button></div></div></article>`;
}
async function favorites() {
  const r = await api('/api/favorites');
  app.innerHTML = `<div class="section-title"><h2>Избранное</h2></div>${r.profiles.length ? `<div class="grid">${r.profiles.map(profileCard).join('')}</div>` : '<div class="empty">В избранном пока никого нет.</div>'}`;
}
function chats() { app.innerHTML = '<div class="section-title"><h2>Сообщения</h2></div><div class="empty">Здесь появятся ваши диалоги.</div>'; }
function profile() {
  const u = me.user;
  if (!u) { app.innerHTML='<div class="empty">Профиль ещё не зарегистрирован.</div>'; return; }
  app.innerHTML = `<section class="hero"><div style="font-size:52px">👤</div><h1>${escapeHtml(u.name||'')}</h1><p>${u.age||''} · ${escapeHtml(u.city||'')}</p><p class="gold" style="margin-top:10px">${u.verification_status === 'verified' ? '✓ Личность подтверждена' : 'Верификация личности доступна добровольно'}</p></section><div class="actions"><button class="btn" onclick="showGifts()">🎁 Подарки</button><button class="btn secondary">Настройки</button></div>`;
}
async function showGifts() {
  app.innerHTML='<div class="empty">Загружаем подарки…</div>';
  const r = await api('/api/gifts');
  if (!r.enabled) { app.innerHTML='<div class="empty"><div style="font-size:48px">🎁</div><p>Подарки пока отключены.</p></div>'; return; }
  app.innerHTML = `<div class="section-title"><h2>🎁 Подарки</h2></div><div class="gift-grid">${r.gifts.map(g=>`<div class="gift"><div class="gift-art">${g.emoji||'🎁'}</div><div>${escapeHtml(g.name_ru||g.name||'Подарок')}</div><div class="coin">🪙 ${g.price_coins||0}</div></div>`).join('')}</div>`;
}
async function fav(id) { await api('/api/favorites/'+id, {method:'POST'}); if (tg?.showPopup) tg.showPopup({title:'Du&Yes', message:'Добавлено в избранное', buttons:[{type:'ok'}]}); }
function openProfile(id) { if (tg?.showPopup) tg.showPopup({title:'Du&Yes', message:'Полный профиль подключим на следующем этапе.', buttons:[{type:'ok'}]}); }
function escapeHtml(s) { return String(s).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
document.querySelectorAll('.nav-item').forEach(b => b.addEventListener('click', ()=>nav(b.dataset.page)));
document.getElementById('settingsBtn').addEventListener('click', ()=>profile());
render();
