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
