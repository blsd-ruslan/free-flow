import './app.scss';
import Cell from './components/Cell';
import Colour from './lib/Colour';
import Grid from './components/Grid';
import LevelProvider from './lib/LevelProvider';
import Point from './components/Point';
import TouchHighlight from './components/TouchHighlight';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';

const levelProvider = new LevelProvider(location);
const hashLevelData = levelProvider.fromURL();
const [height, width, levelData] = hashLevelData ?? levelProvider.generate();

// Initialize TouchHighlight and Grid
const touchHighlight = new TouchHighlight(height, width);
const grid = new Grid(
  height,
  width,
  levelData.map((pointColour, index) =>
    pointColour === Colour.NONE
      ? new Cell(index)
      : new Point(index, pointColour)
  ),
  touchHighlight
);

// Append elements to the app container
const appContainer = document.getElementById('app');
// Create the controls container
const controlsContainer = document.createElement('div');
controlsContainer.classList.add('controls', 'mb-4');

// Create an alert for instructions
const alert = document.createElement('div');
alert.classList.add('alert', 'alert-primary');
alert.role = 'alert';
alert.textContent = 'Select a mode to play';

// Add a mode selector to the UI
const modeSelector = document.createElement('select');
modeSelector.classList.add('form-select', 'mb-4');
modeSelector.innerHTML = `
  <option value="manual">Play Manually</option>
  <option value="bot">Solve with Bot</option>
`;

// Add a level selector to the UI (1-10)
const levelSelector = document.createElement('select');
levelSelector.classList.add('form-select', 'mb-4');
let levelOptions = '';
for (let i = 1; i <= 10; i++) {
  levelOptions += `<option value="${i}">Level ${i}</option>`;
}
levelSelector.innerHTML = levelOptions;

// Create a container for the selectors that will use flexbox to align them horizontally
const selectorContainer = document.createElement('div');
selectorContainer.classList.add('d-flex', 'justify-content-start', 'gap-3'); // d-flex for flex layout, gap-3 for spacing

// Append the selectors into the container
selectorContainer.appendChild(modeSelector);
selectorContainer.appendChild(levelSelector);

// Append the alert and the selector container to the controls container
controlsContainer.appendChild(alert);
controlsContainer.appendChild(selectorContainer);

appContainer.append(
  controlsContainer,
  grid.element(),
  touchHighlight.element()
);

// Handle mode changes
let currentMode = 'manual';

modeSelector.addEventListener('change', (event) => {
  const selectTarget = event.target as HTMLSelectElement;
  currentMode = selectTarget.value;
  if (currentMode === 'bot') {
    startBotMode();
  }
});

// Function to fetch and execute bot moves
async function startBotMode() {
  try {
    while (currentMode === 'bot') {
      const response = await fetch('/api/get-next-move', { method: 'GET' });
      if (!response.ok) {
        throw new Error('Failed to fetch bot move');
      }

      const { from, to } = await response.json();
      executeBotMove(from, to);

      // Simulate a delay to show the bot's moves step-by-step
      await new Promise((resolve) => setTimeout(resolve, 499));
    }
  } catch (error) {
    console.error('Bot mode error:', error);
  }
}

// Function to execute a bot move
function executeBotMove(fromIndex, toIndex) {
  return;
}
