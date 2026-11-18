const tabs = Array.from(document.querySelectorAll('[role="tab"]'));

function showTab() {
  const active = tabs.find(tab => tab.hash === location.hash) || tabs[0];
  for (const tab of tabs) {
    const selected = tab === active;
    const panel = document.getElementById(tab.getAttribute('aria-controls'));
    tab.setAttribute('aria-selected', selected);
    tab.tabIndex = selected ? 0 : -1;
    panel.hidden = !selected;
    if (selected && !panel.firstElementChild) {
      const frame = document.createElement('iframe');
      frame.title = panel.dataset.title;
      frame.src = panel.dataset.page;
      frame.allowFullscreen = true;
      panel.append(frame);
    }
  }
  const isMap = active.id === 'tab-mapa';
  document.getElementById('cave-number').hidden = isMap;
  document.querySelector('h1').textContent = isMap ? 'Jaskinie masywu' : 'Kälbergruben-Windloch';
  document.title = active.textContent + (isMap ? ' · Hagengebirge' : ' · Kälbergruben-Windloch');
}

document.querySelector('[role="tablist"]').addEventListener('keydown', event => {
  const index = tabs.indexOf(event.target);
  if (index < 0) return;
  const positions = {
    ArrowRight: (index + 1) % tabs.length,
    ArrowLeft: (index - 1 + tabs.length) % tabs.length,
    Home: 0,
    End: tabs.length - 1,
  };
  const next = tabs[positions[event.key]];
  if (!next) return;
  event.preventDefault();
  next.focus();
  next.click();
});
window.addEventListener('hashchange', showTab);
showTab();
