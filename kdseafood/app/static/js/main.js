// ================= KDSeaFood – tương tác phía trình duyệt =================
(function () {
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content;
  const toastEl = document.getElementById('appToast');
  const toast = toastEl ? new bootstrap.Toast(toastEl, { delay: 2500 }) : null;

  function notify(msg, ok = true) {
    if (!toast) return alert(msg);
    toastEl.classList.toggle('text-bg-dark', ok);
    toastEl.classList.toggle('text-bg-danger', !ok);
    toastEl.querySelector('.toast-body').textContent = msg;
    toast.show();
  }

  async function postForm(url, data) {
    const res = await fetch(url, {
      method: 'POST', body: data,
      headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrf },
    });
    const json = await res.json().catch(() => ({}));
    if (res.status === 401 && json.login) { window.location = json.login; return null; }
    return { ok: res.ok, ...json };
  }

  // ---- Thêm vào giỏ bằng AJAX (thẻ sản phẩm & trang chi tiết) ----
  document.addEventListener('submit', async (e) => {
    const form = e.target.closest('.js-add-cart');
    if (!form || e.submitter?.name === 'buy_now') return;
    e.preventDefault();
    const btn = form.querySelector('button');
    btn.disabled = true;
    const r = await postForm(form.action, new FormData(form));
    btn.disabled = false;
    if (!r) return;
    notify(r.message || 'Có lỗi xảy ra', r.ok);
    if (r.ok && r.count !== undefined) {
      const badge = document.getElementById('cartCount');
      if (badge) badge.textContent = r.count;
    }
  });

  // ---- Yêu thích ----
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.js-wish');
    if (!btn) return;
    e.preventDefault();
    const r = await postForm(btn.dataset.url, new FormData());
    if (!r || !r.ok) return;
    btn.querySelector('i').className = 'bi ' + (r.liked ? 'bi-heart-fill' : 'bi-heart');
    notify(r.liked ? 'Đã thêm vào danh sách yêu thích' : 'Đã bỏ khỏi danh sách yêu thích');
  });

  // ---- Gợi ý tìm kiếm ----
  const input = document.getElementById('searchInput');
  const box = document.getElementById('suggestBox');
  let timer;
  if (input && box) {
    input.addEventListener('input', () => {
      clearTimeout(timer);
      const q = input.value.trim();
      if (q.length < 2) { box.style.display = 'none'; return; }
      timer = setTimeout(async () => {
        const res = await fetch('/api/search-suggest?q=' + encodeURIComponent(q));
        const items = await res.json();
        box.innerHTML = '';
        items.forEach((it) => {
          const a = document.createElement('a');
          a.href = it.url;
          const img = document.createElement('img'); img.src = it.image; img.alt = '';
          const div = document.createElement('div');
          const name = document.createElement('div'); name.className = 'fw-semibold small'; name.textContent = it.name;
          const price = document.createElement('div'); price.className = 'small text-coral'; price.textContent = it.price;
          div.append(name, price); a.append(img, div); box.append(a);
        });
        box.style.display = items.length ? 'block' : 'none';
      }, 250);
    });
    document.addEventListener('click', (e) => { if (!box.contains(e.target) && e.target !== input) box.style.display = 'none'; });
  }

  // ---- Nút +/- số lượng ----
  document.addEventListener('click', (e) => {
    const b = e.target.closest('[data-step]');
    if (!b) return;
    const inp = b.closest('.qty-input').querySelector('input');
    const step = parseFloat(inp.step) || 1;
    const min = parseFloat(inp.min) || step;
    let v = (parseFloat(inp.value) || 0) + step * parseFloat(b.dataset.step);
    if (inp.max) v = Math.min(v, parseFloat(inp.max));
    inp.value = Math.max(min, Math.round(v * 100) / 100);
    if (inp.dataset.autosubmit !== undefined) inp.form.submit();
  });

  // ---- Ảnh sản phẩm ----
  document.querySelectorAll('.gallery-thumbs img').forEach((t) => t.addEventListener('click', () => {
    document.getElementById('mainImage').src = t.src;
    document.querySelectorAll('.gallery-thumbs img').forEach((x) => x.classList.remove('active'));
    t.classList.add('active');
  }));

  // ---- Xác nhận trước khi xóa ----
  document.addEventListener('submit', (e) => {
    const msg = e.target.dataset.confirm;
    if (msg && !confirm(msg)) e.preventDefault();
  });
})();
