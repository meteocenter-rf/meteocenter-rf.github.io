import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const indexHtmlPath = path.join(__dirname, 'index.html');
const indexContent = fs.readFileSync(indexHtmlPath, 'utf-8');

// Extract WMO_STATIONS_CATALOG
const catalogMatch = indexContent.match(/const\s+WMO_STATIONS_CATALOG\s*=\s*(\[[\s\S]*?\]);/);
if (!catalogMatch) {
  console.error("Could not find WMO_STATIONS_CATALOG in index.html");
  process.exit(1);
}

// Safely evaluate catalog
let catalog = [];
try {
  catalog = new Function(`return ${catalogMatch[1]};`)();
  console.log(`Loaded ${catalog.length} stations from WMO_STATIONS_CATALOG`);
} catch (e) {
  console.error("Error evaluating catalog:", e);
  process.exit(1);
}

const cityDir = path.join(__dirname, 'city');
if (!fs.existsSync(cityDir)) {
  fs.mkdirSync(cityDir, { recursive: true });
}

// Monthly climate norms helper (approximate standard norms if station norms not explicitly listed)
const monthNamesRu = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];

let generatedCount = 0;
const cityUrls = [];

for (const st of catalog) {
  if (!st.id || !st.name) continue;
  const fileName = `${st.id}.html`;
  const filePath = path.join(cityDir, fileName);
  cityUrls.push(`https://meteocenter-rf.github.io/city/${fileName}`);

  const pageTitle = `${st.name} — Погода сейчас, климатический архив ВМО #${st.wmo || ''} и нормы | МетеоПортал`;
  const metaDesc = `Фактическая погода, опорная метеостанция ВМО #${st.wmo || ''} (${st.fullName || st.name}), климатические нормы 1991–2020 и архив погоды 1890–2026 в г. ${st.name} (${st.region || ''}).`;
  const canonicalUrl = `https://meteocenter-rf.github.io/city/${fileName}`;
  const terminalUrl = `../index.html?city=${encodeURIComponent(st.name)}`;

  const html = `<!DOCTYPE html>
<html lang="ru" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${pageTitle}</title>
  <meta name="description" content="${metaDesc}">
  <link rel="canonical" href="${canonicalUrl}">
  
  <!-- OpenGraph -->
  <meta property="og:type" content="website">
  <meta property="og:title" content="${pageTitle}">
  <meta property="og:description" content="${metaDesc}">
  <meta property="og:url" content="${canonicalUrl}">
  <meta property="og:site_name" content="МетеоПортал РФ">
  
  <link rel="icon" type="image/svg+xml" href="../favicon.svg">
  <link rel="alternate icon" href="../favicon.ico">
  
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: { 500: '#38bdf8', 600: '#0284c7' }
          }
        }
      }
    };
  </script>

  <!-- Schema.org JSON-LD -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "BreadcrumbList",
        "itemListElement": [
          { "@type": "ListItem", "position": 1, "name": "Главная", "item": "https://meteocenter-rf.github.io/" },
          { "@type": "ListItem", "position": 2, "name": "Города", "item": "https://meteocenter-rf.github.io/#cities" },
          { "@type": "ListItem", "position": 3, "name": "${st.name}", "item": "${canonicalUrl}" }
        ]
      },
      {
        "@type": "Place",
        "name": "${st.fullName || st.name}",
        "address": {
          "@type": "PostalAddress",
          "addressLocality": "${st.name}",
          "addressRegion": "${st.region || 'РФ'}",
          "addressCountry": "RU"
        },
        "geo": {
          "@type": "GeoCoordinates",
          "latitude": ${st.lat},
          "longitude": ${st.lon}
        }
      }
    ]
  }
  </script>

  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    .glass { background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); }
    .glass-card { background: rgba(30, 41, 59, 0.6); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.06); }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col antialiased selection:bg-sky-500 selection:text-white">

  <!-- Header -->
  <header class="glass sticky top-0 z-50 border-b border-slate-800">
    <div class="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
      <a href="../index.html" class="flex items-center space-x-2 text-sky-400 font-black tracking-wider uppercase text-sm hover:text-sky-300 transition">
        <span>⚡ МЕТЕОПОРТАЛ</span>
      </a>
      <nav class="flex items-center space-x-3 text-xs font-medium">
        <a href="../anomalies.html" class="text-slate-300 hover:text-white transition hidden sm:inline">Аномалии</a>
        <a href="../snow.html" class="text-slate-300 hover:text-white transition hidden sm:inline">Снег</a>
        <a href="../models.html" class="text-slate-300 hover:text-white transition hidden sm:inline">Модели</a>
        <a href="../articles.html" class="text-slate-300 hover:text-white transition hidden sm:inline">Журнал</a>
        <a href="${terminalUrl}" class="px-3 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold transition">4K Терминал →</a>
      </nav>
    </div>
  </header>

  <!-- Main Content -->
  <main class="flex-grow max-w-6xl mx-auto px-4 py-8 w-full space-y-6">

    <!-- Breadcrumbs -->
    <nav class="flex items-center space-x-2 text-xs text-slate-400">
      <a href="../index.html" class="hover:text-sky-400 transition">Главная</a>
      <span>/</span>
      <a href="../index.html#catalog" class="hover:text-sky-400 transition">Метеостанции ВМО</a>
      <span>/</span>
      <span class="text-slate-200 font-medium">${st.name}</span>
    </nav>

    <!-- Hero Card -->
    <div class="glass-card rounded-2xl p-6 sm:p-8 space-y-6 relative overflow-hidden">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="inline-flex items-center space-x-2 px-2.5 py-1 rounded-md bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs font-mono mb-2">
            <span>● МС ВМО #${st.wmo || 'СЕТЬ'}</span>
            <span>·</span>
            <span>${st.lat.toFixed(4)}°N, ${st.lon.toFixed(4)}°E</span>
            ${st.icao ? `<span>·</span><span>ICAO: ${st.icao}</span>` : ''}
          </div>
          <h1 class="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">${st.fullName || st.name}</h1>
          <p class="text-sm text-slate-400 mt-1">${st.region || 'Российская Федерация'}</p>
        </div>

        <div class="flex items-center space-x-3">
          <a href="${terminalUrl}" class="px-5 py-3 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-slate-950 font-black text-sm shadow-lg shadow-sky-500/20 transition flex items-center space-x-2">
            <span>↗ Открыть 4K Терминал</span>
          </a>
        </div>
      </div>

      <!-- Live Observation Widget (Client side Open-Meteo) -->
      <div id="live-obs-box" class="p-5 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center space-x-4">
          <div id="live-temp" class="text-4xl font-black font-mono text-sky-400">--°C</div>
          <div>
            <div id="live-desc" class="text-sm font-bold text-white">Загрузка данных...</div>
            <div class="text-xs text-slate-400">Фактические параметры метеостанции</div>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-300">
          <div class="p-2 rounded bg-slate-800/60 border border-slate-700/50">
            <span class="text-slate-400">Ветер:</span> <span id="live-wind" class="font-bold text-white">-- м/с</span>
          </div>
          <div class="p-2 rounded bg-slate-800/60 border border-slate-700/50">
            <span class="text-slate-400">Давление:</span> <span id="live-press" class="font-bold text-white">-- мм</span>
          </div>
          <div class="p-2 rounded bg-slate-800/60 border border-slate-700/50">
            <span class="text-slate-400">Влажность:</span> <span id="live-hum" class="font-bold text-white">--%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Station Info & Features Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      
      <!-- Card 1: WMO Specifications -->
      <div class="glass-card rounded-2xl p-6 space-y-3">
        <h2 class="text-base font-bold text-white flex items-center space-x-2">
          <span>📋 Паспорт станции</span>
        </h2>
        <ul class="text-xs text-slate-300 space-y-2 font-mono">
          <li class="flex justify-between border-b border-slate-800 pb-1">
            <span class="text-slate-400">Индекс ВМО:</span>
            <span class="text-sky-400 font-bold">${st.wmo || 'Сетевая'}</span>
          </li>
          <li class="flex justify-between border-b border-slate-800 pb-1">
            <span class="text-slate-400">Координаты:</span>
            <span>${st.lat.toFixed(2)}°, ${st.lon.toFixed(2)}°</span>
          </li>
          <li class="flex justify-between border-b border-slate-800 pb-1">
            <span class="text-slate-400">Часовой пояс:</span>
            <span>${st.tz || 'Europe/Moscow'}</span>
          </li>
          <li class="flex justify-between border-b border-slate-800 pb-1">
            <span class="text-slate-400">Архивный ряд:</span>
            <span class="text-emerald-400 font-bold">1890–2026 гг.</span>
          </li>
        </ul>
      </div>

      <!-- Card 2: Climate Norms Intro -->
      <div class="glass-card rounded-2xl p-6 space-y-3">
        <h2 class="text-base font-bold text-white flex items-center space-x-2">
          <span>📊 Климатическая норма ВМО</span>
        </h2>
        <p class="text-xs text-slate-400 leading-relaxed">
          Расчет официального климатического базиса Всемирной метеорологической организации (период 1991–2020 гг.) для ${st.name}. Сравнение текущей фактической температуры с многолетним среднемесячным значением.
        </p>
        <a href="${terminalUrl}&tab=archive" class="inline-block text-xs font-bold text-sky-400 hover:text-sky-300 transition">
          Смотреть климатический дневник 136 лет →
        </a>
      </div>

      <!-- Card 3: Numerical Models -->
      <div class="glass-card rounded-2xl p-6 space-y-3">
        <h2 class="text-base font-bold text-white flex items-center space-x-2">
          <span>🌐 Суперкомпьютерные модели</span>
        </h2>
        <p class="text-xs text-slate-400 leading-relaxed">
          Для точки ${st.name} выполняется прямое сопоставление 5 независимых моделей высокого разрешения: ECMWF IFS (9 км), DWD ICON (13 км), NOAA GFS (13 км), JMA GSM (13 км) и GEM (15 км).
        </p>
        <a href="../models.html" class="inline-block text-xs font-bold text-sky-400 hover:text-sky-300 transition">
          Сравнить прогнозы 5 моделей →
        </a>
      </div>

    </div>

    <!-- SEO Text Block -->
    <div class="glass-card rounded-2xl p-6 sm:p-8 space-y-4">
      <h2 class="text-lg font-bold text-white">Метеорологические наблюдения и архив погоды в г. ${st.name}</h2>
      <div class="text-xs text-slate-300 leading-relaxed space-y-2">
        <p>
          Опорная метеорологическая станция <strong>${st.fullName || st.name}</strong> (индекс Всемирной метеорологической организации #${st.wmo || ''}) обеспечивает непрерывный инструментальный мониторинг атмосферных процессов в регионе ${st.region || ''}.
        </p>
        <p>
          В метеорологическом терминале «МетеоПортал» доступны исторические верифицированные ряды наблюдений с 1890 по 2026 год, расчет температурных аномалий, детектор снежного покрова и прогноз осадков высокой точности.
        </p>
      </div>

      <div class="pt-4 border-t border-slate-800 flex flex-wrap gap-3">
        <a href="${terminalUrl}" class="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs transition">
          Перейти к полному графику погоды ${st.name}
        </a>
        <a href="../snow.html" class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs transition">
          Карта снежного покрова РФ
        </a>
        <a href="../anomalies.html" class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs transition">
          Карта температурных аномалий
        </a>
      </div>
    </div>

  </main>

  <!-- Footer -->
  <footer class="glass border-t border-slate-800 py-6 text-center text-xs text-slate-500">
    <div class="max-w-6xl mx-auto px-4 space-y-2">
      <p>© 2026 МетеоПортал РФ · Независимый гидрометеорологический агрегатор открытых данных</p>
      <p class="text-[11px]">Метеостанция #${st.wmo || ''} · Координаты: ${st.lat.toFixed(4)}°N, ${st.lon.toFixed(4)}°E</p>
    </div>
  </footer>

  <script>
    // Live weather fetch on static page load
    (async function() {
      try {
        const url = 'https://api.open-meteo.com/v1/forecast?latitude=${st.lat}&longitude=${st.lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,surface_pressure';
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        const c = data.current || {};
        if (c.temperature_2m != null) {
          const t = Math.round(c.temperature_2m * 10) / 10;
          document.getElementById('live-temp').textContent = (t > 0 ? '+' : '') + t + '°C';
        }
        if (c.wind_speed_10m != null) {
          document.getElementById('live-wind').textContent = Math.round(c.wind_speed_10m * 10) / 10 + ' м/с';
        }
        if (c.surface_pressure != null) {
          document.getElementById('live-press').textContent = Math.round(c.surface_pressure * 0.750062) + ' мм';
        }
        if (c.relative_humidity_2m != null) {
          document.getElementById('live-hum').textContent = c.relative_humidity_2m + '%';
        }
        document.getElementById('live-desc').textContent = 'Погода сейчас (Open-Meteo / WMO)';
      } catch(e) {
        console.error("Live fetch error:", e);
      }
    })();
  </script>
</body>
</html>`;

  fs.writeFileSync(filePath, html, 'utf-8');
  generatedCount++;
}

console.log(`Successfully generated ${generatedCount} static city pages in /city/`);

// Update sitemap.xml
const sitemapPath = path.join(__dirname, 'sitemap.xml');
const todayStr = new Date().toISOString().split('T')[0];

const corePages = [
  { url: 'https://meteocenter-rf.github.io/', priority: '1.0', changefreq: 'hourly' },
  { url: 'https://meteocenter-rf.github.io/index.html', priority: '1.0', changefreq: 'hourly' },
  { url: 'https://meteocenter-rf.github.io/anomalies.html', priority: '0.9', changefreq: 'hourly' },
  { url: 'https://meteocenter-rf.github.io/snow.html', priority: '0.9', changefreq: 'hourly' },
  { url: 'https://meteocenter-rf.github.io/models.html', priority: '0.9', changefreq: 'daily' },
  { url: 'https://meteocenter-rf.github.io/articles.html', priority: '0.8', changefreq: 'weekly' },
  { url: 'https://meteocenter-rf.github.io/card.html', priority: '0.7', changefreq: 'daily' }
];

let xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
`;

for (const p of corePages) {
  xml += `  <url>
    <loc>${p.url}</loc>
    <lastmod>${todayStr}</lastmod>
    <changefreq>${p.changefreq}</changefreq>
    <priority>${p.priority}</priority>
  </url>
`;
}

for (const u of cityUrls) {
  xml += `  <url>
    <loc>${u}</loc>
    <lastmod>${todayStr}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>
`;
}

xml += `</urlset>\n`;

fs.writeFileSync(sitemapPath, xml, 'utf-8');
console.log(`Successfully updated sitemap.xml with ${corePages.length + cityUrls.length} clean URLs!`);
