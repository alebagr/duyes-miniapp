const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }

const app = document.getElementById('app');
let currentPage = 'home';
let me = null;
let activeChatUserId = null;

function headers() {
  return { 'X-Telegram-Init-Data': tg?.initData || '' };
}

async function api(path, options={}) {
  const res = await fetch(path, { 
    ...options, 
    headers: { 'Content-Type': 'application/json', ...headers(), ...(options.headers||{}) } 
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function nav(page) {
  currentPage = page;
  activeChatUserId = null;
  document.querySelectorAll('.nav-item').forEach(x => x.classList.toggle('active', x.dataset.page === page));
  render();
}

function updateNavVisibility() {
  const navEl = document.querySelector('.nav') || document.querySelector('nav') || document.getElementById('bottomNav');
  const isRegistered = me && me.registered;
  if (navEl) {
    navEl.style.display = isRegistered ? 'flex' : 'none';
  }
}

async function render() {
  try {
    const r = await api('/api/me');
    me = r;
    
    updateNavVisibility();

    // Если не зарегистрирован — форсируем показ экрана 'home' (стартового)
    if (!me.registered) {
      return home();
    }

    if (currentPage === 'home') return home();
    if (currentPage === 'search') return search();
    if (currentPage === 'favorites') return favorites();
    if (currentPage === 'chats') return chats();
    if (currentPage === 'profile') return profile();
    if (currentPage === 'chat_detail') return openChat(activeChatUserId);
  } catch (e) {
    app.innerHTML = `<div class="empty"><div style="font-size:42px">⚠️</div><p>Ошибка загрузки.</p><small>${escapeHtml(e.message)}</small></div>`;
  }
}

function home() {
  const isRegistered = me && me.registered;

  if (!isRegistered) {
    // Стартовая страница до регистрации (Нижнее меню скрыто)
    app.innerHTML = `
      <section class="hero">
        <h1>Du&Yes ❤️</h1>
        <p>Добро пожаловать в сервис знакомств для создания армянской семьи.</p>
        <div class="actions" style="margin-top:16px;">
          <button class="btn" onclick="openRegistration()">📝 Регистрация</button>
        </div>
      </section>

      <div class="section-title"><h2>Информация</h2></div>
      <div style="display:flex; flex-direction:column; gap:10px;">
        <button class="btn secondary" style="width:100%; text-align:left;" onclick="showInfo('about')">📖 Описание сервиса</button>
        <button class="btn secondary" style="width:100%; text-align:left;" onclick="showInfo('rules')">📜 Правила ресурса</button>
        <button class="btn secondary" style="width:100%; text-align:left;" onclick="showInfo('privacy')">🔒 Политика конфиденциальности</button>
      </div>`;
    return;
  }

  // Главная страница после успешной регистрации
  app.innerHTML = `
    <section class="hero">
      <h1>Du&Yes ❤️</h1>
      <p>Серьёзные отношения с целью создания армянской семьи.</p>
      <div class="actions">
        <button class="btn" onclick="nav('search')">Найти пару</button>
        <button class="btn secondary" onclick="showGifts()">🎁 Подарки</button>
      </div>
    </section>
    <div class="section-title"><h2>Добро пожаловать</h2></div>
    <div class="card">
      <div class="card-body">
        <div class="card-title">Безопасность и проверка</div>
        <div class="card-sub">Все профили проходят проверку. Для подтверждения анкеты отправьте заявку на верификацию в профиле.</div>
      </div>
    </div>`;
}

function showInfo(type) {
  let title = '';
  let content = '';

  if (type === 'about') {
    title = 'Описание сервиса';
    content = 'Du&Yes — это специализированная платформа для знакомств, созданная с целью поиска спутника жизни и построения крепкой армянской семьи.';
  } else if (type === 'rules') {
    title = 'Правила ресурса';
    content = '1. Будьте вежливы и уважительны к собеседникам.<br>2. Запрещено размещать недостоверные данные или чужие фотографии.<br>3. Запрещены спам, коммерческая реклама и оскорбления.';
  } else if (type === 'privacy') {
    title = 'Политика конфиденциальности';
    content = 'Мы бережно относимся к вашим персональным данным. Информация используется исключительно для обеспечения работы сервиса и не передается третьим лицам.';
  }

  app.innerHTML = `
    <div class="section-title">
      <button class="btn secondary" style="flex:none; padding:5px 10px;" onclick="nav('home')">← Назад</button>
      <h2>${title}</h2>
    </div>
    <div class="card" style="padding:16px; line-height:1.6; color:var(--muted);">
      ${content}
    </div>`;
}

function openRegistration() {
  app.innerHTML = `
    <div class="section-title">
      <button class="btn secondary" style="flex:none; padding:5px 10px;" onclick="nav('home')">← Назад</button>
      <h2>Регистрация</h2>
    </div>
    <div class="card" style="padding:16px; display:flex; flex-direction:column; gap:12px;">
      <label>Ваше имя:
        <input type="text" id="regName" placeholder="Имя" style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--line); background:#121b3c; color:#fff; margin-top:4px;" />
      </label>
      <label>Пол:
        <select id="regGender" style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--line); background:#121b3c; color:#fff; margin-top:4px;">
          <option value="male">Мужской</option>
          <option value="female">Женский</option>
        </select>
      </label>
      <label>Дата рождения:
        <input type="date" id="regBirth" style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--line); background:#121b3c; color:#fff; margin-top:4px;" />
      </label>
      <label>Город:
        <input type="text" id="regCity" placeholder="Например, Ереван" style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--line); background:#121b3c; color:#fff; margin-top:4px;" />
      </label>
      <label>О себе:
        <textarea id="regAbout" placeholder="Расскажите о себе..." style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--line); background:#121b3c; color:#fff; margin-top:4px;"></textarea>
      </label>
      <button class="btn" style="margin-top:8px;" onclick="submitRegistration()">Завершить регистрацию</button>
    </div>`;
}

async function submitRegistration() {
  const name = document.getElementById('regName').value.trim();
  const gender = document.getElementById('regGender').value;
  const birth_date = document.getElementById('regBirth').value;
  const city = document.getElementById('regCity').value.trim();
  const about = document.getElementById('regAbout').value.trim();

  if (!name || !birth_date) {
    if (tg?.showPopup) tg.showPopup({ title: 'Ошибка', message: 'Пожалуйста, укажите имя и дату рождения.', buttons: [{ type: 'ok' }] });
    return;
  }

  await api('/api/me', {
    method: 'POST',
    body: JSON.stringify({ name, gender, birth_date, city, about })
  });

  if (tg?.showPopup) tg.showPopup({ title: 'Du&Yes', message: 'Регистрация успешно завершена!', buttons: [{ type: 'ok' }] });
  render();
}

async function search() {
  app.innerHTML = '<div class="empty">Загружаем анкеты…</div>';
  const r = await api('/api/profiles');
  const items = r.profiles || [];
  app.innerHTML = `<div class="section-title"><h2>Анкеты</h2></div>${items.length ? `<div class="grid">${items.map(profileCard).join('')}</div>` : '<div class="empty">Подходящих профилей пока не найдено.</div>'}`;
}

function profileCard(p) {
  const loc = [p.city, p.country].filter(Boolean).join(', ');
  return `
    <article class="card">
      <div class="photo">👤</div>
      <div class="card-body">
        <div class="card-title">${escapeHtml(p.name||'Пользователь')}, ${p.age||'—'} ${p.verified ? '<span class="verified">✓</span>' : ''}</div>
        <div class="card-sub">${escapeHtml(loc||'')}</div>
        <div class="actions">
          <button class="btn secondary" onclick="fav(${p.user_id})">♡</button>
          <button class="btn" onclick="startChat(${p.user_id})">Написать</button>
        </div>
      </div>
    </article>`;
}

async function favorites() {
  const r = await api('/api/favorites');
  app.innerHTML = `<div class="section-title"><h2>Избранное</h2></div>${r.profiles.length ? `<div class="grid">${r.profiles.map(profileCard).join('')}</div>` : '<div class="empty">В избранном пока никого нет.</div>'}`;
}

async function chats() {
  app.innerHTML = '<div class="empty">Загружаем сообщения…</div>';
  const r = await api('/api/chats');
  const list = r.chats || [];
  
  if (!list.length) {
    app.innerHTML = '<div class="section-title"><h2>Сообщения</h2></div><div class="empty">У вас пока нет активных диалогов.</div>';
    return;
  }

  app.innerHTML = `
    <div class="section-title"><h2>Сообщения</h2></div>
    <div style="display:flex; flex-direction:column; gap:10px;">
      ${list.map(c => `
        <div class="card" onclick="startChat(${c.user_id})" style="padding:12px; cursor:pointer;">
          <div style="font-weight:bold;">${escapeHtml(c.name)}${c.verified ? '✓' : ''}</div>
          <div class="card-sub">${escapeHtml(c.last_message || 'Нажмите, чтобы открыть диалог')}</div>
        </div>
      `).join('')}
    </div>`;
}

async function startChat(userId) {
  activeChatUserId = userId;
  currentPage = 'chat_detail';
  openChat(userId);
}

async function openChat(userId) {
  app.innerHTML = '<div class="empty">Загружаем чат…</div>';
  const r = await api('/api/messages/' + userId);
  const msgs = r.messages || [];

  app.innerHTML = `
    <div class="section-title">
      <button class="btn secondary" style="flex:none; padding:5px 10px;" onclick="nav('chats')">← Назад</button>
      <h2>Чат</h2>
    </div>
    <div id="msgContainer" style="display:flex; flex-direction:column; gap:8px; max-height:50vh; overflow-y:auto; margin-bottom:12px;">
      ${msgs.length ? msgs.map(m => `
        <div style="align-self: ${m.sender_id === me.user?.user_id ? 'flex-end' : 'flex-start'}; background: ${m.sender_id === me.user?.user_id ? 'var(--gold2)' : 'var(--panel2)'}; color: ${m.sender_id === me.user?.user_id ? '#000' : '#fff'}; padding:8px 12px; border-radius:12px; max-width:80%;">
          ${escapeHtml(m.text)}
        </div>
      `).join('') : '<div class="empty">Напишите первое сообщение!</div>'}
    </div>
    <div style="display:flex; gap:8px;">
      <input type="text" id="msgText" placeholder="Введите сообщение..." style="flex:1; padding:10px; border-radius:10px; border:1px solid var(--line); background:#121b3c; color:#fff;" />
      <button class="btn" style="flex:none;" onclick="sendMsg(${userId})">Отправить</button>
    </div>`;
}

async function sendMsg(userId) {
  const input = document.getElementById('msgText');
  const text = input.value.trim();
  if (!text) return;
  await api('/api/messages/send', { method: 'POST', body: JSON.stringify({ receiver_id: userId, text: text }) });
  input.value = '';
  openChat(userId);
}

function profile() {
  const u = me.user || {};
  app.innerHTML = `
    <section class="hero">
      <div style="font-size:48px">👤</div>
      <h1>${escapeHtml(u.name || 'Моя анкета')}</h1>
      <p>${u.city || 'Город не указан'}</p>
      <p class="gold" style="margin-top:6px;">Монеты: 🪙 ${me.coins || 0}</p>
    </section>

    <div class="section-title"><h2>Редактировать анкету</h2></div>
    <div class="card" style="padding:14px; display:flex; flex-direction:column; gap:10px;">
      <input type="text" id="editName" value="${escapeHtml(u.name||'')}" placeholder="Ваше имя" style="padding:10px; border-radius:8px; border:1px solid var(--line); background:#121b3c; color:#fff;" />
      <input type="date" id="editBirth" value="${u.birth_date||''}" style="padding:10px; border-radius:8px; border:1px solid var(--line); background:#121b3c; color:#fff;" />
      <input type="text" id="editCity" value="${escapeHtml(u.city||'')}" placeholder="Город" style="padding:10px; border-radius:8px; border:1px solid var(--line); background:#121b3c; color:#fff;" />
      <textarea id="editAbout" placeholder="О себе" style="padding:10px; border-radius:8px; border:1px solid var(--line); background:#121b3c; color:#fff;">${escapeHtml(u.about||'')}</textarea>
      <button class="btn" onclick="saveProfile()">Сохранить изменения</button>
    </div>

    <div style="margin-top:15px;">
      <button class="btn secondary" style="width:100%;" onclick="requestVerify()">Запросить синюю галочку (Верификация)</button>
    </div>`;
}

async function saveProfile() {
  const body = {
    name: document.getElementById('editName').value,
    birth_date: document.getElementById('editBirth').value,
    city: document.getElementById('editCity').value,
    about: document.getElementById('editAbout').value
  };
  await api('/api/me', { method: 'POST', body: JSON.stringify(body) });
  if (tg?.showPopup) tg.showPopup({ title: 'Du&Yes', message: 'Анкета успешно сохранена!', buttons: [{ type: 'ok' }] });
  render();
}

async function requestVerify() {
  await api('/api/verification/request', { method: 'POST' });
  if (tg?.showPopup) tg.showPopup({ title: 'Du&Yes', message: 'Заявка на верификацию отправлена модераторам.', buttons: [{ type: 'ok' }] });
}

async function showGifts() {
  app.innerHTML = '<div class="empty">Загружаем подарки…</div>';
  const r = await api('/api/gifts');
  app.innerHTML = `
    <div class="section-title"><h2>🎁 Подарки</h2></div>
    <div class="gift-grid">
      ${r.gifts.map(g => `
        <div class="gift">
          <div class="gift-art">${g.emoji || '🎁'}</div>
          <div>${escapeHtml(g.name_ru || 'Подарок')}</div>
          <div class="coin">🪙 ${g.price_coins || 0}</div>
        </div>
      `).join('')}
    </div>`;
}

async function fav(id) {
  await api('/api/favorites/' + id, { method: 'POST' });
  if (tg?.showPopup) tg.showPopup({ title: 'Du&Yes', message: 'Добавлено в Избранное!', buttons: [{ type: 'ok' }] });
}

function escapeHtml(s) {
  return String(s || '').replace(/[&<>'"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[c]));
}

const settingsBtn = document.getElementById('settingsBtn');
if (settingsBtn) {
  settingsBtn.addEventListener('click', () => nav('profile'));
}

document.querySelectorAll('.nav-item').forEach(b => b.addEventListener('click', () => nav(b.dataset.page)));

render();
