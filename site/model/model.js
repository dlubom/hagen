"use strict";

const get = id => document.getElementById(id);
const message = get("message");
get("layers").open = window.matchMedia("(min-width: 950px)").matches;

function loadModel() {
  const viewer = new CV2.CaveViewer("viewer", {
    home: "CaveView/",
    surveyDirectory: "./",
    terrainDirectory: new URL("terrain", document.baseURI).href,
    displayCRS: "EPSG:3857",
    language: "pl",
    theme: {
      background: "#142a26",
      lighting: { azimuth: 120, inclination: 45 },
      shading: {
        single: "#ffb648",
        surface: "#9be7ff",
        duplicate: "#ff5fa1",
        contours: { base: "#ffffff", line: "#a2af96", line10: "#667b61", interval: 10 }
      }
    },
    view: {
      cameraType: CV2.CAMERA_PERSPECTIVE, box: false, HUD: false,
      shadingMode: CV2.SHADING_SINGLE, surfaceShading: CV2.SHADING_SURFACE,
      duplicateLegs: true, duplicateShading: CV2.SHADING_DUPLICATE,
      terrain: true, terrainOpacity: .60, terrainDatumShift: false,
      terrainShading: CV2.SHADING_CONTOURS, surfaceLegs: true,
      entrances: false, stationLabelOver: true, stationLabels: false, linewidth: .28
    }
  });

  const controls = viewer.getControls();
  function startView() {
    // Fit the complete survey first, then rotate immediately about its centre.
    viewer.setView({ view: CV2.VIEW_PLAN });
    controls.rotateLeft(controls.getAzimuthalAngle() + 2.85);
    controls.rotateUp(controls.getPolarAngle() - .78);
    controls.scaleDolly(1.14);
  }

  viewer.addEventListener("newCave", ({ survey }) => {
    startView();
    viewer.HUD = false;
    viewer.duplicateLegs = get("tie").checked;
    get("locate-tie").onclick = () => {
      const from = survey.surveyTree.getByPath("kgw.2");
      const to = survey.surveyTree.getByPath("local.4");
      const midpoint = survey.getWorldPosition(from.clone().lerp(to, .5));
      startView();
      const camera = controls.cameraManager.activeCamera;
      const offset = camera.position.clone().sub(controls.target).multiplyScalar(.18);
      controls.target.copy(midpoint);
      camera.position.copy(midpoint).add(offset);
      controls.update();
      get("tie").checked = true;
      viewer.duplicateLegs = true;
    };
    get("settings").disabled = false;
    message.hidden = viewer.hasTerrain;
    if (!viewer.hasTerrain) message.textContent = "Model jaskini gotowy. Nie udało się wczytać terenu.";
    get("viewer").setAttribute("aria-busy", "false");
  });
  get("opacity").oninput = event => {
    const percent = Number(event.target.value);
    viewer.terrainOpacity = percent / 100;
    get("value").value = percent + "%";
  };
  get("terrain").onchange = event => {
    viewer.terrain = event.target.checked;
    get("opacity").disabled = !event.target.checked;
  };
  get("centreline").onchange = event => { viewer.legs = event.target.checked; };
  get("surface").onchange = event => { viewer.surfaceLegs = event.target.checked; };
  get("tie").onchange = event => { viewer.duplicateLegs = event.target.checked; };
  get("labels").onchange = event => { viewer.stationLabels = event.target.checked; };
  get("viewer").onkeydown = event => {
    if (!viewer.surveyLoaded) return;
    const step = Math.PI / 18;
    switch (event.key) {
      case "ArrowLeft": controls.rotateLeft(step); break;
      case "ArrowRight": controls.rotateLeft(-step); break;
      case "ArrowUp": controls.rotateUp(step); break;
      case "ArrowDown": controls.rotateUp(-step); break;
      default: return;
    }
    event.preventDefault();
  };
  get("home").onclick = () => { if (viewer.surveyLoaded) startView(); };
  get("closer").onclick = () => { if (viewer.surveyLoaded) controls.scaleDolly(.8); };
  get("farther").onclick = () => { if (viewer.surveyLoaded) controls.scaleDolly(1.25); };
  viewer.loadCave("hagen.3d");
}

try {
  get("viewer").setAttribute("aria-busy", "true");
  loadModel();
} catch (error) {
  get("viewer").setAttribute("aria-busy", "false");
  message.replaceChildren("Do wyświetlenia modelu potrzebna jest przeglądarka z obsługą WebGL 2. ");
  const link = document.createElement("a");
  link.href = "hagen.3d";
  link.textContent = "Pobierz model do Aven.";
  message.append(link);
  console.error(error);
}
