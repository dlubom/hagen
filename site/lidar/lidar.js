const $ = id => document.getElementById(id);
const canvas = $('canvas');
const status = $('status');
const cloudVisible = $('cloud-visible');
const surveyVisible = $('survey-visible');
const coloring = $('coloring');
const formatNumber = new Intl.NumberFormat('pl-PL');

let viewer, survey, potree, cloud;
let view = 'above';

function fail(message) {
  status.dataset.state = 'error';
  status.hidden = true;
  $('error').textContent = message;
  $('error').hidden = false;
  $('alternate').hidden = false;
}

window.addEventListener('error', event => fail(event.message));
window.addEventListener('unhandledrejection', event => fail(event.reason?.message || String(event.reason)));

window.hagenLidar = {
  getState: () => ({
    ready: status.dataset.state === 'ready',
    view,
    coloring: potree?.settings.attribute,
    camera: viewer?.camera.getWorldPosition().toArray().map((value, i) => value + survey.origin[i]),
    cloudVisible: cloud?.visible,
    surveyVisible: surveyVisible.checked,
    points: potree?.state.numVisiblePoints ?? 0,
    totalPoints: cloud?.loader.metadata.points,
    legs: survey?.legs.length,
    provisional: survey?.legs.filter(leg => leg.type === 'provisional').length,
    entrances: survey?.entrances.length,
  }),
};

function setHeightColors(pointCloud, originZ) {
  const position = pointCloud.loader.metadata.attributes.find(attribute => attribute.name === 'position');
  const min = position?.min?.[2];
  const span = position?.max?.[2] - min;
  if (!Number.isFinite(min) || !Number.isFinite(span) || span <= 0) {
    throw new Error('Metadane chmury nie zawierają zakresu wysokości.');
  }
  // The default elevation mapping in this loader is scalar. Use the actual
  // position extent because the octree's cube may extend above the data.
  const hue = {
    name: 'height-gradient',
    condition: attribute => attribute.name === 'elevation',
    inputs: [],
    wgsl: `fn mapping(pointID : u32, attrib : AttributeDescriptor, node : Node, position : vec4f) -> vec4f {
      let z = (uniforms.world * position).z;
      let t = clamp((z - (${(min - originZ).toFixed(6)})) / ${span.toFixed(6)}, 0.0, 1.0);
      let low = vec3f(0.145, 0.455, 0.616);
      let mid = vec3f(0.675, 0.839, 0.475);
      let high = vec3f(0.941, 0.643, 0.349);
      let color = select(mix(low, mid, 2.0 * t), mix(mid, high, 2.0 * t - 1.0), t > 0.5);
      return vec4f(color, 1.0);
    }`,
  };
  pointCloud.material.registerMapping(hue);
  pointCloud.material.selectedMappings.set('elevation', hue);
  $('lowest').textContent = `${formatNumber.format(Math.round(min))} m`;
  $('highest').textContent = `${formatNumber.format(Math.round(min + span))} m`;
}

async function init() {
  if (!isSecureContext || !navigator.gpu || !(await navigator.gpu.requestAdapter())) {
    throw new Error('Widok LiDAR wymaga przeglądarki z WebGPU oraz HTTPS lub localhost.');
  }

  const response = await fetch('./survey.json');
  if (!response.ok) throw new Error(`Nie udało się pobrać poligonu (HTTP ${response.status}).`);
  survey = await response.json();
  if (survey.crs !== 'EPSG:32633' || !survey.legs.length) throw new Error('Nieprawidłowe współrzędne poligonu.');

  const {Potree, PotreeLoader, Vector3, SplatType} = await import('potree');
  potree = Potree;
  // Some Potree renderer modules read the upstream browser global.
  window.Potree = Potree;
  viewer = await Potree.init(canvas);
  const device = viewer.renderer.device;
  device.addEventListener('uncapturederror', event => fail(`WebGPU: ${event.error.message}`));
  device.lost.then(info => fail(`Utracono dostęp do WebGPU. ${info.message}`));

  Object.assign(Potree.settings, {
    edlEnabled: true,
    hqsEnabled: false,
    dilateEnabled: false,
    pointBudget: 1_000_000,
    pointSize: 2.5,
    minNodeSize: 60,
    attribute: coloring.value,
    splatType: SplatType.POINTS,
    showBoundingBox: false,
  });

  const local = point => point.map((value, i) => value - survey.origin[i]);
  const colors = {
    underground: new Vector3(100, 219, 255),
    surface: new Vector3(255, 189, 87),
    provisional: new Vector3(255, 92, 167),
  };
  const lines = survey.legs.flatMap(({from, to, type}) => {
    const start = local(from);
    const end = local(to);
    const color = colors[type];
    if (type !== 'provisional') return [[new Vector3(...start), new Vector3(...end), color]];

    const delta = end.map((value, i) => value - start[i]);
    const length = Math.hypot(...delta);
    const pointAt = meters => new Vector3(...start.map((value, i) => value + meters * delta[i] / length));
    return Array.from({length: Math.ceil(length / 3.5)}, (_, i) => {
      const offset = 3.5 * i;
      return [pointAt(offset), pointAt(Math.min(offset + 1, length)), color];
    });
  });

  const markers = survey.entrances.map(({name, position}) => {
    const label = document.createElement('span');
    label.textContent = name;
    label.className = 'entrance';
    label.hidden = true;
    $('entrances').append(label);
    return {position: new Vector3(...local(position)), label};
  });

  viewer.onUpdate(() => {
    const showSurvey = surveyVisible.checked;
    if (showSurvey) {
      for (const line of lines) viewer.renderer.drawLine(...line);
    }
    for (const {position, label} of markers) {
      const {camera} = viewer;
      const point = position.clone().applyMatrix4(camera.view).applyMatrix4(camera.proj);
      label.hidden = !showSurvey || point.z <= 0 || point.z > 1 || Math.abs(point.x) > 1 || Math.abs(point.y) > 1;
      if (label.hidden) continue;
      label.style.left = `${50 * (1 + point.x)}%`;
      label.style.top = `${50 * (1 - point.y)}%`;
      label.classList.toggle('left-of-point', point.x > 0.53);
    }
  });

  const endpoints = survey.legs.flatMap(({from, to}) => [local(from), local(to)]);
  const minima = [0, 1, 2].map(i => Math.min(...endpoints.map(point => point[i])));
  const maxima = [0, 1, 2].map(i => Math.max(...endpoints.map(point => point[i])));
  const pivot = minima.map((min, i) => (min + maxima[i]) / 2);

  function setView(kind) {
    view = kind;
    const span = Math.hypot(...maxima.map((max, i) => max - minima[i]));
    const distance = span * Math.max(1, 0.95 * canvas.clientHeight / Math.max(1, canvas.clientWidth));
    const position = [pivot[0] + 0.32 * distance, pivot[1] - 0.62 * distance,
      pivot[2] + (kind === 'below' ? -0.48 : 0.74) * distance];
    viewer.controls.set({position, pivot});
    $('above').setAttribute('aria-pressed', kind === 'above');
    $('below').setAttribute('aria-pressed', kind === 'below');
  }

  setView('above');
  $('above').onclick = () => setView('above');
  $('below').onclick = () => setView('below');
  surveyVisible.onchange = () => { $('legend').hidden = !surveyVisible.checked; };
  coloring.onchange = () => {
    Potree.settings.attribute = coloring.value;
    $('height-scale').hidden = coloring.value !== 'elevation';
  };

  status.textContent = 'Ładowanie punktów terenu…';
  cloud = await PotreeLoader.load(new URL('./cloud/metadata.json', location.href).href);
  cloud.position.sub(new Vector3(...survey.origin));
  cloud.updateWorld();
  setHeightColors(cloud, survey.origin[2]);
  viewer.scene.root.children.push(cloud);
  cloudVisible.onchange = () => { cloud.visible = cloudVisible.checked; };
  cloud.visible = cloudVisible.checked;
  coloring.onchange();
  surveyVisible.onchange();
  $('controls').disabled = false;

  let lastTextUpdate = 0;
  Potree.events.onFrameEnd(() => {
    if (status.dataset.state === 'error' || performance.now() - lastTextUpdate < 350) return;
    lastTextUpdate = performance.now();
    if (cloud.loader.error) {
      fail(cloud.loader.error);
    } else if (cloud.root.loaded && Potree.state.numVisiblePoints > 0) {
      status.dataset.state = 'ready';
      status.textContent = `${formatNumber.format(cloud.loader.metadata.points)} punktów gruntu w kaflu`;
    }
  });
}

init().catch(error => fail(error.message || String(error)));
