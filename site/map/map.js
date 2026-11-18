'use strict';

const el = (id) => document.getElementById(id);
const map = L.map('map', { zoomControl: false, trackResize: false, minZoom: 5, maxZoom: 23, preferCanvas: true });
const dataRoot = new URL('./data/', document.baseURI);
const layersButton = el('layers-button');
const panel = el('layers');
const colors = { underground: '#964159', surface: '#c77a15', synthetic: '#c11265', regional: '#286466', gps: '#166994', entrances: '#edba63' };
const baseSpecs = { topo: ['bmapgrau', 'png'], ortho: ['bmaporthofoto30cm', 'jpeg'] };
let basemap, caveBounds, massifBounds;

L.control.zoom({ position: 'bottomright', zoomInTitle: 'Przybliż', zoomOutTitle: 'Oddal' }).addTo(map);
L.control.scale({ imperial: false, maxWidth: 120 }).addTo(map);
map.attributionControl.setPrefix('<a href="https://leafletjs.com/">Leaflet</a>');
map.createPane('plans').style.zIndex = 350;

function element(tag, text) {
  const result = document.createElement(tag);
  result.textContent = text;
  return result;
}

function panelOpen(open) {
  layersButton.setAttribute('aria-expanded', String(open));
  panel.hidden = !open;
}
panelOpen(window.matchMedia('(min-width: 800px) and (min-height: 480px)').matches);
layersButton.addEventListener('click', () => panelOpen(panel.hidden));

function changeBasemap() {
  if (basemap) map.removeLayer(basemap);
  basemap = null;
  el('tile-status').hidden = true;
  const selected = el('basemap').value;
  el('geology-info').hidden = selected !== 'geology';
  if (selected === 'none') return;
  const options = { minZoom: 5, maxZoom: 23, noWrap: true };
  let tiles;
  if (selected === 'geology') {
    const attribution = '© <a href="https://www.geosphere.at/">GeoSphere Austria</a> · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>';
    tiles = [['karte_geofast_50', 16], ['karte_50', 15]].map(([series, maxNativeZoom]) =>
      L.tileLayer('https://gis.geosphere.at/images/rest/services/geologie/' + series + '/ImageServer/tile/{z}/{y}/{x}',
        { ...options, maxNativeZoom, attribution }));
  } else {
    const [id, format] = baseSpecs[selected];
    tiles = [L.tileLayer('https://mapsneu.wien.gv.at/basemap/' + id + '/normal/google3857/{z}/{y}/{x}.' + format, {
      ...options, maxNativeZoom: 19,
      attribution: 'Data source: <a href="https://basemap.at/">basemap.at</a> · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>'
    })];
  }
  const group = L.layerGroup(tiles);
  const failures = new Set();
  function tileStatus() {
    if (group !== basemap) return;
    el('tile-status').hidden = failures.size === 0;
    el('tile-status').textContent = 'Nie udało się wczytać części podkładu.';
  }
  for (const tileLayer of tiles) {
    tileLayer.on('tileerror', (e) => { failures.add(e.tile); tileStatus(); });
    tileLayer.on('tileunload', (e) => { failures.delete(e.tile); tileStatus(); });
  }
  basemap = group;
  group.addTo(map);
}
el('basemap').addEventListener('change', changeBasemap);
changeBasemap();

function frame(bounds, maxZoom = 19) {
  if (!bounds?.isValid() || !map.getSize().x || !map.getSize().y) return;
  map.closePopup();
  const panelWidth = !panel.hidden && map.getSize().x >= 800 ? panel.offsetWidth + 30 : 20;
  map.fitBounds(bounds, {
    paddingTopLeft: [panelWidth, 56],
    paddingBottomRight: [25, 34],
    maxZoom,
    animate: false
  });
}
el('cave').addEventListener('click', () => {
  if (map.getSize().x < 800) panelOpen(false);
  frame(caveBounds);
});
el('massif').addEventListener('click', () => {
  if (map.getSize().x < 800) panelOpen(false);
  frame(massifBounds, 15);
});
new ResizeObserver(() => {
  const container = map.getContainer();
  if (!container.clientWidth || !container.clientHeight) return;
  map.invalidateSize({ animate: false });
  if (map.getZoom() === undefined) frame(caveBounds);
}).observe(el('map'));

const number = (n, digits = 0) => n.toLocaleString('pl-PL', { maximumFractionDigits: digits });
const coord = ([lon, lat]) => lat.toFixed(6) + '° N, ' + lon.toFixed(6) + '° E';
const popupOptions = { maxWidth: 340, minWidth: 160 };

function setMeasurement() {
  const button = el('measure');
  const section = el('measurement');
  const hint = el('measure-hint');
  const result = el('measure-result');
  const clear = el('measure-clear');
  const container = map.getContainer();
  const pane = map.createPane('measurement');
  pane.style.zIndex = 625;
  pane.style.pointerEvents = 'none';
  const style = { pane: 'measurement', color: '#007481', interactive: false };
  const line = L.polyline([], { ...style, weight: 4 }).addTo(map);
  const points = L.layerGroup().addTo(map);
  let active = false;
  let lastPoint = null;
  let distance = 0;

  function render() {
    section.hidden = !active && distance === 0;
    hint.hidden = !active;
    result.hidden = distance === 0;
    result.textContent = distance === 0 ? '' : 'Długość w rzucie · ' + (distance < 1000
      ? number(distance, 1) + ' m' : number(distance / 1000, 2) + ' km');
    clear.disabled = !lastPoint;
  }

  function reset() {
    lastPoint = null;
    distance = 0;
    line.setLatLngs([]);
    points.clearLayers();
  }

  function setActive(measuring) {
    active = measuring;
    button.textContent = active ? 'Zakończ pomiar' : 'Miarka';
    container.classList.toggle('is-measuring', active);
    if (active) {
      reset();
      if (map.getSize().x < 800) panelOpen(false);
      map.closePopup();
      map.doubleClickZoom.disable();
    } else {
      if (distance === 0) reset();
      map.doubleClickZoom.enable();
    }
    render();
  }

  map.on('click', ({ latlng }) => {
    if (!active || lastPoint?.equals(latlng)) return;
    if (lastPoint) distance += map.distance(lastPoint, latlng);
    lastPoint = latlng;
    line.addLatLng(latlng);
    points.addLayer(L.circleMarker(latlng, { ...style, radius: 4, weight: 2, fillColor: '#fff', fillOpacity: 1 }));
    render();
  });
  button.addEventListener('click', () => setActive(!active));
  clear.addEventListener('click', () => {
    reset();
    render();
    button.focus();
  });
  window.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    if (active) {
      setActive(false);
      button.focus();
    } else if (!panel.hidden) {
      panelOpen(false);
      layersButton.focus();
    }
  });
}
setMeasurement();

function gpsPopup(feature) {
  const p = feature.properties;
  const popup = element('div', '');
  popup.append(element('h2', p.name), element('p', 'Punkt GPX'));
  if (p.desc) popup.append(element('p', p.desc));
  if (p.cmt && p.cmt !== p.desc) popup.append(element('p', p.cmt));
  if (Number.isFinite(p.ele)) popup.append(element('p', number(p.ele, 2) + ' m'));
  popup.append(element('small', coord(feature.geometry.coordinates)));
  return popup;
}
function entrancePopup(control, model, gps) {
  const popup = element('div', '');
  popup.append(element('h2', control.properties.name + ' · ' + control.properties.station.toUpperCase().split('.').pop()));
  const values = element('dl', '');
  for (const [title, feature] of [['Podana pozycja', control], ['Punkt GPX', gps], ['Wynik Survex', model]]) {
    if (!feature) continue;
    values.append(element('dt', title), element('dd', coord(feature.geometry.coordinates) + ' · ' + number(feature.properties.ele, 2) + ' m'));
  }
  popup.append(values);
  return popup;
}

function addToggle(label, key, layer) {
  const row = document.createElement('label');
  row.className = 'check';
  const input = document.createElement('input');
  input.type = 'checkbox';
  input.checked = true;
  input.id = 'show-' + key;
  input.addEventListener('change', () => input.checked ? layer.addTo(map) : map.removeLayer(layer));
  const sample = document.createElement('i');
  sample.className = key;
  sample.style.setProperty('--c', colors[key]);
  sample.setAttribute('aria-hidden', 'true');
  row.append(input, sample, document.createTextNode(label));
  el('overlays').append(row);
  layer.addTo(map);
  return input;
}

function setPlans(plans) {
  const select = el('plan');
  const opacity = el('opacity');
  const info = el('plan-info');
  const sources = el('plan-sources');
  const status = el('plan-status');
  const layers = L.layerGroup().addTo(map);
  const layersOpacity = () => Number(opacity.value) / 100;
  // The 1963 detail is an alternate view of Kälbergruben-Windloch.
  const both = ['plan-1985', 'plan-tantal-1979'].map((id) => plans.find((plan) => plan.id === id));
  plans.forEach((plan) => select.add(new Option(plan.title, plan.id)));
  if (both.every(Boolean)) select.add(new Option('Obie jaskinie', 'both'));
  if (plans.length) select.value = plans[0].id;

  function update() {
    const selected = select.value === 'both' ? both : plans.filter((plan) => plan.id === select.value);
    layers.clearLayers();
    sources.replaceChildren();
    status.hidden = true;
    opacity.disabled = selected.length === 0;
    info.hidden = selected.length === 0;
    const bounds = L.latLngBounds([]);
    const failed = new Set();
    for (const plan of selected) {
      const layer = L.imageOverlay(new URL(plan.image, dataRoot).href, plan.bounds, {
        pane: 'plans', opacity: layersOpacity(), alt: plan.title, interactive: false
      }).on('error', () => {
        if (!layers.hasLayer(layer)) return;
        failed.add(plan.title);
        status.textContent = 'Nie udało się wczytać planów · ' + [...failed].join(', ');
        status.hidden = false;
      });
      layers.addLayer(layer);
      bounds.extend(layer.getBounds());
      if (selected.length > 1) sources.append(element('h3', plan.title));
      sources.append(element('p', plan.note), element('p', plan.attribution));
    }
    return bounds;
  }
  select.addEventListener('change', () => {
    const bounds = update();
    if (!bounds.isValid()) return;
    caveBounds = bounds;
    el('survey-cave').value = '';
    if (map.getSize().x < 800) panelOpen(false);
    frame(caveBounds);
  });
  opacity.addEventListener('input', () => {
    el('opacity-value').textContent = opacity.value + '%';
    layers.eachLayer((layer) => layer.setOpacity(layersOpacity()));
  });
  update();
}

function setSearch(markers, gpsLayer, toggle) {
  const search = el('search');
  const list = el('matches');
  const normalize = (s) => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const index = markers.map((marker) => ({ marker, name: normalize(marker.feature.properties.name || '') }));
  search.addEventListener('input', () => {
    list.replaceChildren();
    const key = normalize(search.value.trim());
    list.hidden = !key;
    if (!key) return;
    const matches = index.filter((entry) => entry.name.includes(key)).slice(0, 10);
    if (!matches.length) {
      const empty = element('li', 'Brak pasujących punktów');
      empty.className = 'empty';
      list.append(empty);
    }
    for (const { marker } of matches) {
      const item = document.createElement('li');
      const button = element('button', marker.feature.properties.name);
      button.type = 'button';
      button.addEventListener('click', () => {
        toggle.checked = true;
        gpsLayer.addTo(map);
        if (map.getSize().x < 800) panelOpen(false);
        map.setView(marker.getLatLng(), 18, { animate: false });
        marker.openPopup();
        list.hidden = true;
        search.value = '';
        map.getContainer().focus();
      });
      item.append(button);
      list.append(item);
    }
  });
}

async function readJson(path) {
  const response = await fetch(new URL(path, dataRoot));
  if (!response.ok) throw Error(path + ' (' + response.status + ')');
  return response.json();
}

async function load() {
  const manifest = await readJson('map.json');
  const [gps, regional, surveys, controls] = await Promise.all(
    [manifest.gps, manifest.regional, manifest.surveys, manifest.controls].map(readJson)
  );
  const surveyOptions = (surface) => ({
    filter: (feature) => feature.properties.surface === surface && !feature.properties.synthetic,
    style: { color: surface ? colors.surface : colors.underground, weight: 3, dashArray: surface ? '6 5' : undefined },
    onEachFeature: (f, l) => l.bindPopup(() => element('p', (surface ? 'Powierzchnia' : 'Pod ziemią') + ' · ' + f.properties.from + ' — ' + f.properties.to))
  });
  const regionalLayer = L.geoJSON(regional, {
    style: { color: colors.regional, weight: 3 },
    onEachFeature: (f, l) => l.bindPopup(() => {
      const popup = element('div', '');
      popup.append(element('h2', f.properties.name), element('p', 'Podziemne odcinki pomiarowe · ' + number(f.properties.legs)));
      return popup;
    }, popupOptions)
  }).on('add', () => regionalLayer.bringToBack());
  const gpsLayer = L.geoJSON(gps, {
    pointToLayer: (f, ll) => L.circleMarker(ll, {
      radius: f.properties.station ? 6 : 4, color: '#fff', weight: 1.4, fillColor: colors.gps, fillOpacity: 0.95
    }),
    onEachFeature: (f, l) => l.bindPopup(() => gpsPopup(f), popupOptions)
  });
  const underground = L.geoJSON(surveys, surveyOptions(false));
  const surface = L.geoJSON(surveys, surveyOptions(true));
  const synthetic = L.geoJSON(surveys, {
    filter: (feature) => feature.properties.synthetic,
    style: { color: colors.synthetic, weight: 4, dashArray: '4 4', lineCap: 'butt' },
    onEachFeature: (feature, line) => line.bindPopup(() => {
      const popup = element('div', '');
      popup.append(element('h2', 'Sztuczny łącznik · do weryfikacji w terenie'),
        element('p', feature.properties.from + ' — ' + feature.properties.to),
        element('p', 'Z dopasowania do planu wynika 12,71 m w rzucie. Obu końcom przypisano tę samą wysokość (ΔH = 0 m).'));
      return popup;
    }, popupOptions)
  });
  const entranceLayer = L.layerGroup();
  for (const control of controls.features.filter((f) => f.properties.kind === 'control')) {
    const { station, name } = control.properties;
    const model = controls.features.find((f) => f.properties.kind === 'model' && f.properties.station === station);
    const gpx = gps.features.find((f) => f.properties.station === station);
    const short = station.toUpperCase().split('.').pop();
    const marker = L.marker(L.GeoJSON.coordsToLatLng(control.geometry.coordinates), {
      icon: L.divIcon({ className: 'entrance', iconSize: [13, 13], iconAnchor: [6.5, 6.5] }), title: name, alt: name
    });
    marker.bindTooltip(short, { permanent: true, direction: station === 'kgw.e1' ? 'right' : 'left', className: 'entrance-label', offset: [0, -9] });
    marker.bindPopup(() => entrancePopup(control, model, gpx), popupOptions);
    entranceLayer.addLayer(marker);
  }
  caveBounds = underground.getBounds().extend(surface.getBounds());
  massifBounds = gpsLayer.getBounds().extend(regionalLayer.getBounds()).extend(caveBounds);
  for (const plan of manifest.plans) massifBounds.extend(plan.bounds);
  frame(caveBounds);
  setPlans(manifest.plans);
  addToggle('Otwory 1335/70', 'entrances', entranceLayer);
  addToggle('Poligon podziemny 1335/70', 'underground', underground);
  addToggle('Poligon powierzchniowy 1335/70', 'surface', surface);
  addToggle('Sztuczny łącznik · do weryfikacji w terenie', 'synthetic', synthetic);
  const gpsToggle = addToggle('Punkty GPX', 'gps', gpsLayer);
  const regionalToggle = addToggle('Ciągi jaskiń · h2026', 'regional', regionalLayer);
  const caves = regionalLayer.getLayers().sort((a, b) => a.feature.properties.name.localeCompare(b.feature.properties.name, 'pl', { numeric: true }));
  const select = el('survey-cave');
  caves.forEach((layer, i) => select.add(new Option(layer.feature.properties.name, String(i))));
  select.addEventListener('change', () => {
    if (!select.value) return;
    regionalToggle.checked = true;
    regionalLayer.addTo(map);
    caveBounds = caves[Number(select.value)].getBounds();
    if (map.getSize().x < 800) panelOpen(false);
    frame(caveBounds);
  });
  setSearch(gpsLayer.getLayers(), gpsLayer, gpsToggle);
  el('measure').disabled = false;
  el('status').hidden = true;
}

load().catch((error) => {
  el('status').textContent = 'Nie udało się wczytać danych mapy. Odśwież stronę, aby ponowić próbę.';
  el('status').hidden = false;
  console.error(error);
});
