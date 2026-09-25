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
  const navEl = document.querySelector('nav') || document.querySelector('.nav') || document.getElementById('bottomNav');
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

    if (!me.registered) {
      return home();
    }

    if (currentPage === 'home') return home();
    if (currentPage === 'search') return search();
    if (currentPage === 'favorites') return favorites();
    if (currentPage === 'chats') return chats();
    if (currentPage === 'profile') return profile();
    if (currentPage === 'settings') return settingsPage();
    if (currentPage === 'chat_detail') return openChat(activeChatUserId);
  } catch (e) {
    app.innerHTML = `<div class="empty"><div style="font-size:42px">⚠️</div><p>Ошибка загрузки.</p><small>${escapeHtml(e.message)}</small></div>`;
  }
}

function home() {
  const isRegistered = me && me.registered;

  if (!isRegistered) {
    app.innerHTML = `
      <section class="hero">
        <h1>Du&Yes ❤️</h1>
        <p>Ты и Я — к счастью вместе. Сервис знакомств для создания армянской семьи.</p>
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

  app.innerHTML = `
    <section class="hero">
      <h1>Du&Yes ❤️</h1>
      <p>Ты и Я — к счастью вместе. Серьёзные отношения с целью создания армянской семьи.</p>
      <div class="actions">
        <button class="btn" onclick="nav('search')">Найти пару</button>
        <button class="btn secondary" onclick="showGifts()">🎁 Подарки</button>
      </div>
    </section>
    <div class="section-title"><h2>Добро пожаловать</h2></div>
    <div class="card">
      <div class="card-body">
        <div class="card-title">Безопасность и проверка</div>
        <div class="card-sub">Все профили проходят проверку модерацией. Для получения синей галочки отправьте заявку на верификацию в профиле.</div>
      </div>
    </div>`;
}

function showInfo(type) {
  let title = '';
  let content = '';

  if (type === 'about') {
    title = 'Описание сервиса';
    content = `
      Платформа <b>Du&Yes</b> («Ты и Я») создана для поиска спутника жизни и создания крепкой семьи в армянских традициях.<br><br>
      Приложение предоставляет возможность знакомиться с проверенными анкетами, обмениваться сообщениями, виртуальными подарками и добавлять понравившихся кандидатов в Избранное.`;
  } else if (type === 'rules') {
    title = 'Правила ресурса';
    content = `
      <b>Правила использования сервиса Du&Yes:</b><br><br>
      1. Указывайте достоверную информацию о себе при регистрации.<br>
      2. Запрещено использовать чужие фотографии или материалы ненадлежащего содержания.<br>
      3. Соблюдайте уважительный тон при общении с другими пользователями.<br>
      4. Любая реклама, спам, мошенничество или оскорбления приведут к блокировке анкеты без возможности восстановления.`;
  } else if (type === 'privacy') {
    title = 'Политика конфиденциальности';
    content = `
      <b>Политика конфиденциальности персональных данных:</b><br><br>
      Администрация сервиса Du&Yes обеспечивает полную защиту ваших персональных данных.<br><br>
      • Вся личная информация используется исключительно для идентификации профиля в приложении.<br>
      • Мы не передаем ваши личные данные третьим лицам.<br>
      • Вы в любой момент можете изменить или обновить свои данные в разделе «Профиль».`;
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
      <label>Дата рождения (вам должно быть 18+):
        <input type="date" id="regBirth" style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--line); background:#121b3c; color:#fff; margin-top:4px;" />
      </label>
      <label>Страна:
        <input type="text" id="regCountry" placeholder="Армения, Россия..." style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--line); background:#121b3c; color:#fff; margin-top:4px;" />
      </label>
      <label>Город:
        <input type="text" id="regCity" placeholder="Ереван, Москва..." style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--line); background:#121b3c; color:#fff; margin-top:4px;" />
      </label>
      <label>Семейное положение:
        <select id="regMarried" style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--line); background:#121b3c; color:#fff; margin-top:4px;">
          <option value="0">Не состоял(а) в браке</option>
          <option value="1">Состоял(а) в браке</option>
        </select>
      </label>
      <label>Дети:
        <select id="regChildren" style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--line); background:#121b3c; color:#fff; margin-top:4px;">
          <option value="0">Нет детей</option>
          <option value="1">Есть дети</option>
        </select>
      </label>
      <label>О себе:
        <textarea id="regAbout" placeholder="Расскажите о себе, ваших ценностях и целях..." style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--line); background:#121b3c; color:#fff; margin-top:4px;"></textarea>
      </label>
      <button class="btn" style="margin-top:8px;" onclick="submitRegistration()">Завершить регистрацию</button>
    </div>`;
}

async function submitRegistration() {
  const first_name = document.getElementById('regName').value.trim();
  const gender = document.getElementById('regGender').value;
  const birth_date = document.getElementById('regBirth').value;
  const country = document.getElementById('regCountry').value.trim();
  const city = document.getElementById('regCity').value.trim();
  const previously_married = document.getElementById('regMarried').value;
  const has_children = document.getElementById('regChildren').value;
  const about = document.getElementById('regAbout').value.trim();

  if (!first_name || !birth_date) {
    if (tg?.showPopup) tg.showPopup({ title: 'Ошибка', message: 'Пожалуйста, укажите имя и дату рождения.', buttons: [{ type: 'ok' }] });
    return;
  }

  const bDate = new Date(birth_date);
  const today = new Date();
  let age = today.getFullYear() - bDate.getFullYear();
  const m = today.getMonth() - bDate.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < bDate.getDate())) age--;

  if (age < 18) {
    if (tg?.showPopup) tg.showPopup({ title: 'Ограничение по возрасту', message: 'Регистрация разрешена только лицам старше 18 лет.', buttons: [{ type: 'ok' }] });
    return;
  }

  await api('/api/me', {
    method: 'POST',
    body: JSON.stringify({ first_name, gender, birth_date, country, city, previously_married, has_children, about })
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
  const marriedStr = p.previously_married ? 'Был(а) в браке' : 'В браке не состоял(а)';
  const childrenStr = p.has_children ? 'Есть дети' : 'Детей нет';

  return `
    <article class="card">
      <div class="photo">${p.photo_1 ? `<img src="${p.photo_1}" style="width:100%; height:100%; object-fit:cover; border-radius:12px;" />` : '👤'}</div>
      <div class="card-body">
        <div class="card-title">${escapeHtml(p.first_name||'Пользователь')}, ${p.age||'—'} ${p.verified ? '<span class="verified">✓</span>' : ''}</div>
        <div class="card-sub">${escapeHtml(loc||'')}</div>
        <div class="card-sub" style="font-size:12px; opacity:0.8; margin-top:4px;">${marriedStr} • ${childrenStr}</div>
        <div class="actions" style="margin-top:10px;">
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
          <div style="font-weight:bold;">${escapeHtml(c.first_name)}${c.verified ? '✓' : ''}</div>
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
  const isVerified = u.verification_status === 'verified';
  const isPending = u.verification_status === 'pending';
  const marriedStr = u.previously_married ? 'Ранее состоял(а) в браке' : 'Ранее в браке не состоял(а)';
  const childrenStr = u.has_children ? 'Есть дети' : 'Детей нет';

  app.innerHTML = `
    <section class="hero">
      <div style="font-size:48px">👤</div>
      <h1>${escapeHtml(u.first_name || 'Моя анкета')} ${isVerified ? '✓' : ''}</h1>
      <p>🎂 ${u.age || '—'} лет • 📍 ${u.city || ''}, ${u.country || ''}</p>
      <p class="gold" style="margin-top:6px;">Монеты: 🪙 ${me.coins || 0}</p>
    </section>

    <!-- Вывод неизменяемых данных -->
    <div class="card" style="padding:14px; margin-bottom:12px; opacity:0.9; background:#121b3c;">
      <div style="font-size:12px; color:var(--muted); margin-bottom:6px;">🔒 Неизменяемые данные анкеты:</div>
      <div>💍 ${marriedStr}</div>
      <div>👶 ${childrenStr}</div>
    </div>

    <div class="section-title"><h2>Редактировать анкету</h2></div>
    <div class="card" style="padding:14px; display:flex; flex-direction:column; gap:10px;">
      <label>О себе (разрешено к изменению):
        <textarea id="editAbout" placeholder="О себе" style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--line); background:#121b3c; color:#fff; margin-top:4px;">${escapeHtml(u.about||'')}</textarea>
      </label>
      <button class="btn" onclick="saveProfile()">Сохранить описание</button>
    </div>

    <div style="margin-top:12px;">
      <button class="btn secondary" style="width:100%;" onclick="nav('settings')">⚙️ Настройки приватности</button>
    </div>

    <div style="margin-top:12px;">
      ${isVerified ? '<div style="color:#4caf50; font-weight:bold; text-align:center;">✓ Ваш профиль верифицирован</div>' : 
        isPending ? '<div style="color:#ff9800; font-weight:bold; text-align:center;">⏳ Заявка на верификацию рассматривается</div>' :
        '<button class="btn secondary" style="width:100%;" onclick="requestVerify()">Запросить синюю галочку (Верификация)</button>'
      }
    </div>`;
}

function settingsPage() {
  const u = me.user || {};
  app.innerHTML = `
    <div class="section-title">
      <button class="btn secondary" style="flex:none; padding:5px 10px;" onclick="nav('profile')">← Назад</button>
      <h2>⚙️ Настройки</h2>
    </div>
    <div class="card" style="padding:16px; display:flex; flex-direction:column; gap:14px;">
      <label style="display:flex; justify-content:space-between; align-items:center;">
        <span>📷 Скрыть фотографии</span>
        <input type="checkbox" id="setPhotos" ${u.photos_hidden ? 'checked' : ''} />
      </label>
      <label style="display:flex; justify-content:space-between; align-items:center;">
        <span>🟢 Показывать онлайн-статус</span>
        <input type="checkbox" id="setOnline" ${u.show_online_status !== 0 ? 'checked' : ''} />
      </label>
      <label style="display:flex; justify-content:space-between; align-items:center;">
        <span>🕐 Показывать время последнего визита</span>
        <input type="checkbox" id="setLastSeen" ${u.show_last_seen !== 0 ? 'checked' : ''} />
      </label>
      <label style="display:flex; justify-content:space-between; align-items:center;">
        <span>🔔 Включить уведомления</span>
        <input type="checkbox" id="setNotif" ${u.notifications_enabled !== 0 ? 'checked' : ''} />
      </label>
      <button class="btn" onclick="saveSettings()">Сохранить настройки</button>
    </div>`;
}

async function saveSettings() {
  const body = {
    photos_hidden: document.getElementById('setPhotos').checked,
    show_online_status: document.getElementById('setOnline').checked,
    show_last_seen: document.getElementById('setLastSeen').checked,
    notifications_enabled: document.getElementById('setNotif').checked
  };
  await api('/api/settings', { method: 'POST', body: JSON.stringify(body) });
  if (tg?.showPopup) tg.showPopup({ title: 'Du&Yes', message: 'Настройки сохранены!', buttons: [{ type: 'ok' }] });
  nav('profile');
}

async function saveProfile() {
  const body = {
    about: document.getElementById('editAbout').value
  };
  await api('/api/me', { method: 'POST', body: JSON.stringify(body) });
  if (tg?.showPopup) tg.showPopup({ title: 'Du&Yes', message: 'Описание обновлено!', buttons: [{ type: 'ok' }] });
  render();
}

async function requestVerify() {
  await api('/api/verification/request', { method: 'POST' });
  if (tg?.showPopup) tg.showPopup({ title: 'Du&Yes', message: 'Заявка на верификацию отправлена модераторам.', buttons: [{ type: 'ok' }] });
  render();
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
