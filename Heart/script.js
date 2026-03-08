// script.js
const canvas = document.getElementById('heartCanvas');
const ctx = canvas.getContext('2d', { alpha: true });

let w = canvas.width = innerWidth;
let h = canvas.height = innerHeight;

window.addEventListener('resize', () => {
  w = canvas.width = innerWidth;
  h = canvas.height = innerHeight;
  resetPoints();
});

// Heart parametric function (classic heart curve)
function heartPoint(t) {
  // t in [0, 2π]
  // Using a scaled version of the cardioid-like heart polynomial parametric formula
  const x = 16 * Math.pow(Math.sin(t), 3);
  const y = 13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t);
  return { x, y };
}

// Convert heart coordinate to canvas
function toCanvas(p, scale=15) {
  // center horizontally, move a little up for aesthetic
  return {
    x: w/2 + p.x * scale,
    y: h/2 - p.y * scale - 30
  };
}

// Particle system
let particles = [];
let points = [];
let animationId = null;
let running = true;

// UI
const toggleBtn = document.getElementById('toggleBtn');
const countRange = document.getElementById('countRange');
const sizeRange = document.getElementById('sizeRange');
const colorPicker = document.getElementById('colorPicker');

toggleBtn.onclick = () => {
  running = !running;
  toggleBtn.textContent = running ? 'Pause' : 'Play';
  if (running) animate();
  else cancelAnimationFrame(animationId);
};

countRange.oninput = () => { resetPoints(); };
sizeRange.oninput = () => { particles.forEach(p => p.baseSize = parseFloat(sizeRange.value)); };
colorPicker.oninput = () => { particles.forEach(p => p.color = colorPicker.value); };

// Create points along the heart outline
function buildHeartPoints(resolution = 800) {
  points = [];
  for (let i = 0; i < resolution; i++) {
    const t = (i / resolution) * Math.PI * 2;
    const raw = heartPoint(t);
    const c = toCanvas(raw, Math.min(w, h) / 60); // scale depends on screen
    points.push({ x: c.x, y: c.y });
  }
}

// Create particle objects that sit near the heart points
function resetPoints() {
  buildHeartPoints(1000); // many points for smoothness
  const count = parseInt(countRange.value, 10);
  particles = [];
  for (let i = 0; i < count; i++) {
    const pi = points[Math.floor(Math.random() * points.length)];
    const angle = Math.random() * Math.PI * 2;
    const r = Math.random() * 10; // small offset radius
    particles.push({
      // position around the heart path with a tiny random offset
      x: pi.x + Math.cos(angle) * r,
      y: pi.y + Math.sin(angle) * r,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      jitter: Math.random() * 0.6 + 0.2,
      baseSize: parseFloat(sizeRange.value),
      color: colorPicker.value,
      life: Math.random() * 1000
    });
  }
}

// Render frame
function draw() {
  // fade with slight alpha to create trailing glow
  ctx.fillStyle = 'rgba(0,0,0,0.12)';
  ctx.fillRect(0, 0, w, h);

  // Draw each particle as a filled circle with blur
  for (const p of particles) {
    // subtle attraction to nearest heart point so particles stick to outline
    const nearest = points[Math.floor(Math.random() * points.length)];
    const ax = (nearest.x - p.x) * 0.02 * p.jitter;
    const ay = (nearest.y - p.y) * 0.02 * p.jitter;

    p.vx += ax + (Math.random() - 0.5) * 0.05;
    p.vy += ay + (Math.random() - 0.5) * 0.05;

    p.x += p.vx;
    p.y += p.vy;

    // simple pulsing size
    const size = p.baseSize * (0.75 + 0.25 * Math.sin(Date.now() / 200 + p.life));

    ctx.beginPath();
    ctx.globalCompositeOperation = 'lighter';
    ctx.shadowColor = p.color;
    ctx.shadowBlur = 22; // glow
    ctx.fillStyle = p.color;
    ctx.arc(p.x, p.y, size, 0, Math.PI * 2);
    ctx.fill();

    // small chance of respawn to keep the scatter lively
    if (Math.random() < 0.001) {
      const pi = points[Math.floor(Math.random() * points.length)];
      p.x = pi.x + (Math.random() - 0.5) * 10;
      p.y = pi.y + (Math.random() - 0.5) * 10;
      p.vx = (Math.random() - 0.5) * 0.4;
      p.vy = (Math.random() - 0.5) * 0.4;
    }
  }
}

// animation loop
function animate() {
  draw();
  animationId = requestAnimationFrame(animate);
}

// initial setup
resetPoints();
ctx.fillStyle = '#000';
ctx.fillRect(0,0,w,h);
animate();
