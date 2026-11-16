'use strict';
const burger = document.querySelector('.burger');
const navigation = document.querySelector('#main-nav');
function closeMenu() {
  burger?.setAttribute('aria-expanded', 'false');
  navigation?.classList.remove('is-open');
}
burger?.addEventListener('click', () => {
  const open = burger.getAttribute('aria-expanded') !== 'true';
  burger.setAttribute('aria-expanded', String(open));
  navigation.classList.toggle('is-open', open);
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && burger?.getAttribute('aria-expanded') === 'true') {
    closeMenu(); burger.focus();
  }
});
window.matchMedia('(min-width: 1024px)').addEventListener('change', closeMenu);

document.querySelector('#print-order')?.addEventListener('click', () => window.print());

// Сервер возвращает итоговую цену. Старый ответ не может затереть новый расчёт.
const money = value => new Intl.NumberFormat('ru-RU', {style: 'currency', currency: 'RUB', maximumFractionDigits: 0}).format(Number(value));
const debounce = (callback, delay = 300) => { let timer; return (...args) => { clearTimeout(timer); timer = setTimeout(() => callback(...args), delay); }; };
const calculator = document.querySelector('#calculator');
const orderForm = document.querySelector('#order-form');
let quoteController;
async function updateEstimate(form, target, detailed = false) {
  quoteController?.abort(); quoteController = new AbortController();
  target.setAttribute('aria-busy', 'true');
  const status = document.querySelector('#estimate-error');
  if (status) status.textContent = 'Рассчитываем стоимость…';
  else target.textContent = 'Рассчитываем стоимость…';
  const params = new URLSearchParams(new FormData(form)); params.delete('csrfmiddlewaretoken');
  const endpoint = form.dataset.endpoint || form.dataset.estimateUrl;
  try {
    const response = await fetch(`${endpoint}?${params}`, {signal: quoteController.signal, headers: {Accept: 'application/json'}});
    const data = await response.json();
    if (!response.ok) {
      const errors = Object.values(data.errors || {}).flat().map(error => error.message).join(' ');
      throw new Error(errors || 'Проверьте параметры уборки.');
    }
    if (status) status.textContent = '';
    target.replaceChildren();
    if (detailed) {
      for (const item of data.items) {
        const row = document.createElement('div'); row.className = 'line';
        const label = document.createElement('span'); label.textContent = `${item.name} × ${Number(item.quantity)}`;
        const amount = document.createElement('strong'); amount.textContent = money(item.amount);
        row.append(label, amount); target.append(row);
      }
    }
    const price = document.createElement('p'); price.className = 'total'; price.textContent = money(data.price);
    const detail = document.createElement('p'); detail.className = 'small'; detail.textContent = `Длительность: ${data.duration_min} мин. Коэффициент помещения: ${data.factor}. Скидка: ${data.discount_percent}%.`;
    target.append(price, detail);
    const orderLink = document.querySelector('#choose-time');
    if (orderLink && calculator) { const url = new URL(orderLink.href); url.search = new URLSearchParams(new FormData(calculator)).toString(); orderLink.href = url.toString(); }
  } catch (error) {
    if (error.name !== 'AbortError') {
      const message = error instanceof TypeError ? 'Не удалось получить расчёт. Проверьте соединение и повторите.' : error.message;
      if (status) status.textContent = message; else target.textContent = message;
    }
  } finally { target.removeAttribute('aria-busy'); }
}
if (calculator) {
  const target = document.querySelector('#estimate');
  calculator.addEventListener('submit', event => {event.preventDefault(); updateEstimate(calculator, target, true);});
  calculator.addEventListener('input', debounce(() => {if (calculator.checkValidity()) updateEstimate(calculator, target, true);}));
  updateEstimate(calculator, target, true);
}
if (orderForm) {
  const target = document.querySelector('#order-estimate');
  orderForm.addEventListener('input', debounce(() => {
    if (orderForm.elements.area.checkValidity() && orderForm.elements.service.value && orderForm.elements.room_type.value) updateEstimate(orderForm, target);
  }));
}

// Живой поиск и фильтры получают HTML фрагмента из JSON своего представления.
const filterForm = document.querySelector('#catalog-filter');
let searchController;
async function updateCatalog(params, updateUrl = true) {
  searchController?.abort(); searchController = new AbortController();
  const status = document.querySelector('#search-status'); const results = document.querySelector('#catalog-results');
  status.textContent = 'Ищем услуги…'; results.setAttribute('aria-busy', 'true');
  try {
    const response = await fetch(`${filterForm.dataset.endpoint}?${params}`, {signal: searchController.signal, headers: {Accept: 'application/json'}});
    if (!response.ok) throw new Error('Поиск временно недоступен. Повторите попытку.');
    const data = await response.json(); results.innerHTML = data.html; status.textContent = `Найдено: ${data.count}`;
    if (updateUrl) {const url = new URL(filterForm.action); url.search = params.toString(); history.replaceState({}, '', url);}
  } catch (error) {if (error.name !== 'AbortError') status.textContent = 'Не удалось загрузить услуги. Повторите поиск.';}
  finally {results.removeAttribute('aria-busy');}
}
if (filterForm) {
  filterForm.addEventListener('submit', event => {event.preventDefault(); updateCatalog(new URLSearchParams(new FormData(filterForm)));});
  filterForm.querySelector('input[type=search]').addEventListener('input', debounce(() => updateCatalog(new URLSearchParams(new FormData(filterForm)))));
  filterForm.querySelectorAll('select').forEach(select => select.addEventListener('change', () => updateCatalog(new URLSearchParams(new FormData(filterForm)))));
  document.querySelector('#catalog-results').addEventListener('click', event => {
    const link = event.target.closest('.pagination a'); if (!link) return;
    event.preventDefault(); updateCatalog(new URL(link.href).searchParams);
  });
}

// Улучшенная клиентская проверка; сервер проверяет данные независимо от JavaScript.
for (const form of document.querySelectorAll('form[data-validate]')) {
  form.noValidate = true;
  form.addEventListener('submit', event => {
    let firstInvalid;
    for (const input of form.querySelectorAll('input:not([type=hidden]),select,textarea')) {
      const errorNode = document.getElementById(`${input.id}_client_error`);
      input.setCustomValidity('');
      if (input.name === 'phone' && input.value && !/^\+7\d{10}$/.test(input.value)) input.setCustomValidity('Введите телефон в формате +7XXXXXXXXXX.');
      if (input.maxLength > 0 && input.value.length > input.maxLength) input.setCustomValidity(`Введите не больше ${input.maxLength} символов.`);
      if (input.type === 'file' && (input.files.length > 3 || [...input.files].some(file => file.size > 5*1024*1024))) input.setCustomValidity('Выберите не больше трёх фото, до 5 МБ каждое.');
      let message = input.validationMessage;
      if (input.validity.valueMissing) message = 'Заполните это поле.';
      if (input.type === 'email' && input.validity.typeMismatch) message = 'Введите почту в формате name@example.ru.';
      if (errorNode) errorNode.textContent = message;
      if (message) {
        firstInvalid ||= input; input.setAttribute('aria-invalid', 'true');
        const descriptions = new Set((input.getAttribute('aria-describedby') || '').split(' ').filter(Boolean));
        if (errorNode) descriptions.add(errorNode.id);
        input.setAttribute('aria-describedby', [...descriptions].join(' '));
      } else input.removeAttribute('aria-invalid');
    }
    if (firstInvalid) {event.preventDefault(); firstInvalid.focus();}
  });
}
