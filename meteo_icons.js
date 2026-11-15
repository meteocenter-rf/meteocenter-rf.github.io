/**
 * MeteoCenter RF - High-Definition Vector Meteorological Icon & Visualizer System
 * Replaces cartoon unicode emojis with volumetric, layered, responsive SVG icons.
 * Features:
 *  - 100% mathematical continuous stepped temperature ribbon (Gismeteo-standard, 0 seams, 0 gaps).
 *  - Volumetric 3D sun, moon, and multi-layered clouds with atmospheric depth.
 *  - Crystalline snow asterisks (1, 2, 4 stars with solid cores).
 *  - Teardrop rain droplets (1, 2, 4 drops) and mixed precipitation (* •).
 *  - Blizzard warning hazard badge (orange triangle with cyclone swirl on gusts >= 13 m/s).
 *  - Dual-tier wind speed & gust hazard matrix.
 */

(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    const exports = factory();
    root.renderDetailedMeteoIcon = exports.renderDetailedMeteoIcon;
    root.getMeteoIconSvg = exports.getMeteoIconSvg;
    root.buildGismeteoDays = exports.buildGismeteoDays;
    root.buildGismeteoFlawlessDays = exports.buildGismeteoDays;
    root.renderGismeteoFlawless = exports.renderGismeteoFlawless;
    root.renderGismeteoVisualizer = exports.renderGismeteoFlawless; // 100% backward-compatible replacement
  }
}(typeof self !== 'undefined' ? self : this, function () {

  const WMO_DESCRIPTIONS = {
    0: 'Ясно',
    1: 'Преимущественно ясно',
    2: 'Переменная облачность',
    3: 'Пасмурно',
    45: 'Туман',
    48: 'Изморозь',
    51: 'Слабая морось',
    53: 'Умеренная морось',
    55: 'Плотная морось',
    56: 'Ледяная морось',
    57: 'Плотная ледяная морось',
    61: 'Небольшой дождь',
    63: 'Умеренный дождь',
    65: 'Сильный дождь',
    66: 'Ледяной дождь',
    67: 'Сильный ледяной дождь',
    71: 'Небольшой снег',
    73: 'Снегопад',
    75: 'Сильный снегопад',
    77: 'Снежные зерна',
    80: 'Слабый ливень',
    81: 'Умеренный ливень',
    82: 'Сильный ливень',
    85: 'Слабый снегопад',
    86: 'Сильная метель',
    95: 'Гроза',
    96: 'Гроза с градом',
    99: 'Сильная гроза с градом'
  };

  function getWmoDescription(code) {
    return WMO_DESCRIPTIONS[code] || 'Погодные условия';
  }

  /**
   * Generates a hyper-detailed SVG weather icon for a specific meteorological slot.
   * Includes 3D cloud layering, crisp crystalline snowflakes, droplets, and blizzard badges.
   */
  function renderDetailedMeteoIcon(slot, size = 48) {
    const code = parseInt(slot.code, 10) || 0;
    const isDay = (slot.isDay === 0 || slot.isDay === false) ? 0 : 1;
    const isBlizz = slot.isBlizzard || (slot.gust >= 13 && (code >= 71 && code <= 86));
    const stars = slot.stars || 0;
    const drops = slot.drops || 0;
    const uid = 'ic_' + Math.random().toString(36).substr(2, 6);

    // 1. Base Sun / Moon / Cloud Geometry
    let base = '';
    if (code === 0) {
      if (isDay) {
        // Radiant Golden Sun with Corona Rays
        base = `
          <defs>
            <radialGradient id="sunG_${uid}" cx="35%" cy="35%" r="65%">
              <stop offset="0%" stop-color="#fffbeb"/>
              <stop offset="40%" stop-color="#fbbf24"/>
              <stop offset="100%" stop-color="#f59e0b"/>
            </radialGradient>
            <filter id="sunGlow_${uid}" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="2" flood-color="#f59e0b" flood-opacity="0.4"/>
            </filter>
          </defs>
          <circle cx="27" cy="20" r="10" fill="url(#sunG_${uid})" filter="url(#sunGlow_${uid})"/>
          <g stroke="#f59e0b" stroke-width="2" stroke-linecap="round" opacity="0.9">
            <line x1="27" y1="4" x2="27" y2="7"/><line x1="27" y1="33" x2="27" y2="36"/>
            <line x1="11" y1="20" x2="14" y2="20"/><line x1="40" y1="20" x2="43" y2="20"/>
            <line x1="15.5" y1="8.5" x2="18" y2="11"/><line x1="36" y1="29" x2="38.5" y2="31.5"/>
            <line x1="38.5" y1="8.5" x2="36" y2="11"/><line x1="18" y1="29" x2="15.5" y2="31.5"/>
          </g>
        `;
      } else {
        // Night Crescent Moon + Twinkling Stars
        base = `
          <defs>
            <linearGradient id="moonG_${uid}" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#fef08a"/>
              <stop offset="100%" stop-color="#facc15"/>
            </linearGradient>
          </defs>
          <path d="M33 10 A11 11 0 0 1 21 27 A12 12 0 1 0 33 10 Z" fill="url(#moonG_${uid})" stroke="#eab308" stroke-width="1.2"/>
          <path d="M37 9 l1 1 l-1 1 l-1 -1 Z" fill="#38bdf8"/>
          <path d="M15 15 l1.2 1.2 l-1.2 1.2 l-1.2 -1.2 Z" fill="#93c5fd"/>
          <path d="M36 24 l0.8 0.8 l-0.8 0.8 l-0.8 -0.8 Z" fill="#bae6fd"/>
        `;
      }
    } else if (code === 1 || code === 2) {
      // Partly Cloudy: Sun/Moon behind Volumetric Cloud
      const astro = isDay ? `
        <g transform="translate(14, 3)">
          <circle cx="11" cy="11" r="8" fill="#f59e0b"/>
          <g stroke="#f59e0b" stroke-width="1.8" stroke-linecap="round" opacity="0.85">
            <line x1="11" y1="-1" x2="11" y2="1.5"/><line x1="23" y1="11" x2="20.5" y2="11"/>
            <line x1="2.5" y1="2.5" x2="4.5" y2="4.5"/><line x1="19.5" y1="2.5" x2="17.5" y2="4.5"/>
          </g>
        </g>
      ` : `
        <g transform="translate(14, 3)">
          <path d="M20 5 A8 8 0 0 1 12 17 A9 9 0 1 0 20 5 Z" fill="#fde047" stroke="#eab308" stroke-width="1"/>
        </g>
      `;
      base = `
        <defs>
          <linearGradient id="cloudPart_${uid}" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#ffffff"/>
            <stop offset="65%" stop-color="#f1f5f9"/>
            <stop offset="100%" stop-color="#cbd5e1"/>
          </linearGradient>
          <filter id="cShadow_${uid}" x="-10%" y="-10%" width="120%" height="125%">
            <feDropShadow dx="0" dy="2" stdDeviation="1.8" flood-color="#64748b" flood-opacity="0.2"/>
          </filter>
        </defs>
        ${astro}
        <path d="M11 29 h26 a8 8 0 0 0 1.2-15.9 A12 12 0 0 0 14 11 a9 9 0 0 0 -3 18 Z" fill="url(#cloudPart_${uid})" stroke="#94a3b8" stroke-width="1.3" filter="url(#cShadow_${uid})"/>
      `;
    } else if (code >= 95) {
      // Thunderstorm: Dark Volumetric Cloud + Electric Lightning Bolt
      base = `
        <defs>
          <linearGradient id="cStorm_${uid}" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#64748b"/>
            <stop offset="100%" stop-color="#334155"/>
          </linearGradient>
          <filter id="cShadow_${uid}" x="-10%" y="-10%" width="120%" height="125%">
            <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#1e293b" flood-opacity="0.35"/>
          </filter>
        </defs>
        <path d="M10 28 h26 a8 8 0 0 0 1.2-15.9 A12 12 0 0 0 13 10 a9.5 9.5 0 0 0 -3 18 Z" fill="url(#cStorm_${uid})" stroke="#475569" stroke-width="1.3" filter="url(#cShadow_${uid})"/>
        <polygon points="27,24 21,34 26,34 23,42 32,31 27,31" fill="#facc15" stroke="#eab308" stroke-width="0.8"/>
      `;
    } else {
      // Overcast 3D Dual-Layer Cloud
      base = `
        <defs>
          <linearGradient id="cBack_${uid}" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#cbd5e1"/>
            <stop offset="100%" stop-color="#94a3b8"/>
          </linearGradient>
          <linearGradient id="cFront_${uid}" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#ffffff"/>
            <stop offset="60%" stop-color="#f1f5f9"/>
            <stop offset="100%" stop-color="#cbd5e1"/>
          </linearGradient>
          <filter id="cShadow_${uid}" x="-10%" y="-10%" width="120%" height="125%">
            <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#475569" flood-opacity="0.22"/>
          </filter>
        </defs>
        <path d="M16 23 h20 a7.5 7.5 0 0 0 1-14.9 A10.5 10.5 0 0 0 18 6 a8.5 8.5 0 0 0 -2 17 Z" fill="url(#cBack_${uid})" opacity="0.9"/>
        <path d="M10 29 h26 a8 8 0 0 0 1.2-15.9 A12 12 0 0 0 13 11 a9.5 9.5 0 0 0 -3 18 Z" fill="url(#cFront_${uid})" stroke="#94a3b8" stroke-width="1.3" filter="url(#cShadow_${uid})"/>
      `;
    }

    // 2. Crisp Asterisk Snowflake Generator (6-point with solid center core)
    function mkSnowflake(cx, cy, r = 3.8) {
      return `
        <g transform="translate(${cx}, ${cy})">
          <line x1="-${r}" y1="0" x2="${r}" y2="0" stroke="#38bdf8" stroke-width="1.6" stroke-linecap="round"/>
          <line x1="0" y1="-${r}" x2="0" y2="${r}" stroke="#38bdf8" stroke-width="1.6" stroke-linecap="round"/>
          <line x1="-${r*0.7}" y1="-${r*0.7}" x2="${r*0.7}" y2="${r*0.7}" stroke="#38bdf8" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="-${r*0.7}" y1="${r*0.7}" x2="${r*0.7}" y2="-${r*0.7}" stroke="#38bdf8" stroke-width="1.5" stroke-linecap="round"/>
          <circle cx="0" cy="0" r="1.2" fill="#0284c7"/>
          <circle cx="0" cy="0" r="0.6" fill="#f0f9ff"/>
        </g>
      `;
    }

    // 3. Rain Droplet Generator (smooth teardrop)
    function mkDroplet(cx, cy) {
      return `
        <path d="M${cx} ${cy-3.5} C${cx+2} ${cy} ${cx+2.2} ${cy+2.2} ${cx} ${cy+3.6} C${cx-2.2} ${cy+2.2} ${cx-2} ${cy} ${cx} ${cy-3.5} Z" fill="#0284c7"/>
      `;
    }

    // 4. Precipitation Indicators Layer
    let precip = '';
    if (stars === 1 && drops === 1) {
      // Mixed: 1 snowflake + 1 droplet
      precip = mkSnowflake(18, 34, 3.5) + mkDroplet(31, 34);
    } else if (stars === 4) {
      // 4 Asterisks in 2 rows
      precip = mkSnowflake(16, 33, 3.4) + mkSnowflake(26, 33, 3.4) +
               mkSnowflake(21, 39, 3.4) + mkSnowflake(31, 39, 3.4);
    } else if (stars === 2) {
      // 2 Asterisks side by side
      precip = mkSnowflake(18, 35, 3.5) + mkSnowflake(30, 35, 3.5);
    } else if (stars === 1) {
      // 1 Asterisk centered
      precip = mkSnowflake(24, 35, 3.8);
    } else if (drops === 4) {
      // 4 Droplets in 2 rows
      precip = mkDroplet(16, 33) + mkDroplet(26, 33) +
               mkDroplet(21, 39) + mkDroplet(31, 39);
    } else if (drops === 2) {
      // 2 Droplets
      precip = mkDroplet(19, 35) + mkDroplet(29, 35);
    } else if (drops === 1) {
      // 1 Droplet
      precip = mkDroplet(24, 35);
    }

    // 5. Blizzard Warning Triangle Badge (Gismeteo hazard indicator)
    let badge = '';
    if (isBlizz) {
      badge = `
        <g transform="translate(3, 4)">
          <path d="M10 1.5 C10.8 1.5 11.6 2 12 2.8 L19.2 15.5 C19.6 16.3 19.6 17.2 19.2 18 C18.8 18.7 18 19.2 17.2 19.2 L2.8 19.2 C2 19.2 1.2 18.7 0.8 18 C0.4 17.2 0.4 16.3 0.8 15.5 L8 2.8 C8.4 2 9.2 1.5 10 1.5 Z" fill="#f59e0b" stroke="#d97706" stroke-width="1.2"/>
          <circle cx="10" cy="12.5" r="3.6" fill="#ffffff"/>
          <path d="M8.2 12 A 1.8 1.8 0 0 1 11.8 12.5 A 1.4 1.4 0 0 1 10 14.2" fill="none" stroke="#b45309" stroke-width="1.3" stroke-linecap="round"/>
        </g>
      `;
    }

    return `
      <svg width="${size}" height="${Math.round(size * 0.85)}" viewBox="0 0 52 44" fill="none" xmlns="http://www.w3.org/2000/svg" class="inline-block select-none overflow-visible">
        ${base}
        ${precip}
        ${badge}
      </svg>
    `;
  }

  /**
   * Standard WMO code icon resolver.
   */
  function getMeteoIconSvg(code, isDay, size = 32) {
    const c = parseInt(code, 10) || 0;
    const d = (isDay === 0 || isDay === false) ? 0 : 1;
    let stars = 0, drops = 0;
    if (c === 71 || c === 77) stars = 1;
    else if (c === 73 || c === 85) stars = 2;
    else if (c === 75 || c === 86) stars = 4;
    else if (c === 51 || c === 61) drops = 1;
    else if (c === 53 || c === 63) drops = 2;
    else if (c === 55 || c === 65 || (c >= 80 && c <= 82)) drops = 4;
    else if (c === 68 || c === 69) { stars = 1; drops = 1; }

    const mockSlot = {
      code: c,
      isDay: d,
      stars,
      drops,
      isBlizzard: (c === 86)
    };
    return renderDetailedMeteoIcon(mockSlot, size);
  }

  /**
   * Transforms raw API hourly data into 3 days x 4 synoptic periods with meteorological indicators.
   */
  function buildGismeteoDays(d, maxDays) {
    if (!d) return [];
    const limit = (typeof maxDays === 'number' && maxDays > 0) 
      ? maxDays 
      : ((typeof window !== 'undefined' && window.gismeteoDaysCount) ? window.gismeteoDaysCount : 3);
    const raw = d.hourly_raw || {};
    const hTimes = raw.time || [];
    const hTemps = raw.temperature_2m || [];
    const hCodes = raw.weather_code || [];
    const hWinds = raw.wind_speed_10m || [];
    const hGusts = raw.wind_gusts_10m || [];
    const hDirs = raw.wind_direction_10m || [];
    const hPrecips = raw.precipitation || [];
    const hIsDay = raw.is_day || [];

    if (!hTimes.length) return [];

    const daysMap = {};
    const periods = [
      { name: "Ночь", targetH: 3, label: "03:00" },
      { name: "Утро", targetH: 9, label: "09:00" },
      { name: "День", targetH: 15, label: "15:00" },
      { name: "Вечер", targetH: 21, label: "21:00" }
    ];

    for (let i = 0; i < hTimes.length; i++) {
      const tStr = hTimes[i];
      const datePart = tStr.split('T')[0];
      const hourPart = parseInt(tStr.split('T')[1].split(':')[0], 10);

      if (!daysMap[datePart]) {
        if (Object.keys(daysMap).length >= limit) break;
        const dt = new Date(datePart + 'T12:00:00');
        const dayOfWeek = dt.getDay(); // 0 is Sun, 6 is Sat
        const isWeekend = (dayOfWeek === 0 || dayOfWeek === 6);
        const dayNames = ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];
        const monthNames = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"];
        const dateStr = `${dayNames[dayOfWeek]}, ${dt.getDate()} ${monthNames[dt.getMonth()]}`;

        daysMap[datePart] = {
          dateStr,
          isWeekend,
          slots: {}
        };
      }

      for (const p of periods) {
        if (hourPart === p.targetH) {
          const temp = Math.round(hTemps[i] != null ? hTemps[i] : 0);
          const wind = Math.round(hWinds[i] != null ? hWinds[i] : 0);
          const gust = Math.round(hGusts[i] != null ? hGusts[i] : (wind * 1.3));
          const code = hCodes[i] != null ? hCodes[i] : 0;
          const wDir = hDirs[i] != null ? hDirs[i] : 0;
          const isDaySlot = (hIsDay[i] != null) ? hIsDay[i] : (p.targetH >= 6 && p.targetH <= 18 ? 1 : 0);
          const precip = hPrecips[i] != null ? hPrecips[i] : 0;

          const dirs = ["С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"];
          const dirName = dirs[Math.round(wDir / 45) % 8];

          // Compute meteorological indicators
          const isBlizzard = (gust >= 13 && ((code >= 71 && code <= 86) || (temp <= 0 && precip >= 0.2)));
          let stars = 0, drops = 0;
          if (isBlizzard || code === 75 || code === 86) {
            stars = 4;
          } else if (code === 73 || code === 85) {
            stars = 2;
          } else if (code === 71 || code === 77) {
            stars = 1;
          } else if (code === 56 || code === 57 || code === 66 || code === 67 || code === 68 || code === 69) {
            stars = 1; drops = 1;
          } else if (code === 65 || code === 82) {
            drops = 4;
          } else if (code === 63 || code === 81) {
            drops = 2;
          } else if (code === 51 || code === 53 || code === 55 || code === 61 || code === 80) {
            drops = 1;
          }

          daysMap[datePart].slots[p.name] = {
            name: p.name,
            hour: p.label,
            temp,
            code,
            isDay: isDaySlot,
            wind,
            gust,
            dir: wDir,
            dirName,
            isBlizzard,
            stars,
            drops
          };
        }
      }
    }

    const resultDays = [];
    for (const [dKey, dObj] of Object.entries(daysMap)) {
      const ordered = [];
      for (const sName of ["Ночь", "Утро", "День", "Вечер"]) {
        if (dObj.slots[sName]) {
          ordered.push(dObj.slots[sName]);
        }
      }
      if (ordered.length === 4) {
        resultDays.push({
          dateStr: dObj.dateStr,
          isWeekend: dObj.isWeekend,
          slots: ordered
        });
      }
    }

    return resultDays;
  }

  /**
   * 100% Mathematical Continuous Stepped SVG Ribbon Visualizer.
   * Renders a flawless, gap-free, seam-free temperature band across 12 synoptic slots.
   */
  function renderGismeteoFlawless(city, region, days) {
    if (!days || !days.length) return '';

    // Flatten all slots across days (12 slots for 3 days)
    const allSlots = [];
    days.forEach(d => d.slots.forEach(s => allSlots.push(s)));
    const N = allSlots.length;
    const slotWidth = 72; // Fixed width per slot in px
    const totalW = N * slotWidth; // Exactly 864px for 12 slots
    const ribbonH = 76;
    const bandH = 34;

    const allTemps = allSlots.map(s => s.temp);
    const minT = Math.min(...allTemps);
    const maxT = Math.max(...allTemps);
    const rangeT = Math.max(1, maxT - minT);
    const availH = ribbonH - bandH - 10;

    // Compute topY and bottomY for each slot
    const steps = allSlots.map(s => {
      const norm = (s.temp - minT) / rangeT; // 0 (coldest) to 1 (warmest)
      const topY = Math.round((1 - norm) * availH + 5);
      const bottomY = topY + bandH;
      const midY = topY + bandH / 2;
      return { temp: s.temp, topY, bottomY, midY };
    });

    // Build solid continuous stepped SVG polygon path (ZERO SEAMS, ZERO GAPS)
    let pathD = `M 0 ${steps[0].topY}`;
    for (let i = 0; i < N; i++) {
      const xEnd = (i + 1) * slotWidth;
      pathD += ` L ${xEnd} ${steps[i].topY}`;
      if (i < N - 1) {
        pathD += ` L ${xEnd} ${steps[i + 1].topY}`;
      }
    }
    pathD += ` L ${totalW} ${steps[N - 1].bottomY}`;
    for (let i = N - 1; i >= 0; i--) {
      const xStart = i * slotWidth;
      pathD += ` L ${xStart} ${steps[i].bottomY}`;
      if (i > 0) {
        pathD += ` L ${xStart} ${steps[i - 1].bottomY}`;
      }
    }
    pathD += ` Z`;

    // Temperature text labels rendered centered on the ribbon
    const tempTexts = steps.map((st, i) => {
      const cx = i * slotWidth + slotWidth / 2;
      const sign = st.temp > 0 ? `+${st.temp}` : `${st.temp}`;
      return `
        <text x="${cx}" y="${st.midY}" text-anchor="middle" dominant-baseline="central" font-family="'JetBrains Mono', 'Inter', system-ui, sans-serif" font-weight="800" font-size="14.5" fill="#0369a1" class="dark:fill-[#f0f9ff] select-none pointer-events-none">
          ${sign}
        </text>
      `;
    }).join('');

    // Row 1: Day Columns Header & Weather Icons
    const daysColumnsHtml = days.map((d, dIdx) => {
      const dayHeaderColor = d.isWeekend ? 'text-rose-500 dark:text-rose-400' : 'text-sky-600 dark:text-sky-400';
      const dayBorder = (dIdx > 0) ? 'border-l border-slate-200/80 dark:border-slate-800' : '';

      const slotsHtml = d.slots.map(s => `
        <div style="width: ${slotWidth}px;" class="shrink-0 flex flex-col items-center">
          <div class="py-1 text-center text-[11px] font-semibold text-slate-500 dark:text-slate-400 select-none">
            ${s.name}
          </div>
          <div class="py-1 flex items-center justify-center h-12" title="${s.name}: ${s.hour}, ${s.temp}°C, WMO ${s.code}">
            ${renderDetailedMeteoIcon(s, 46)}
          </div>
        </div>
      `).join('');

      return `
        <div style="width: ${d.slots.length * slotWidth}px;" class="shrink-0 ${dayBorder} px-0 flex flex-col">
          <div class="px-3 py-2 text-sm font-extrabold tracking-tight ${dayHeaderColor} border-b border-slate-200/60 dark:border-slate-800/80">
            ${d.dateStr}
          </div>
          <div class="flex">
            ${slotsHtml}
          </div>
        </div>
      `;
    }).join('');

    // Row 3: Wind & Gusts Cards (matching the 72px slot width)
    const windsHtml = allSlots.map(s => {
      let gustBg = 'bg-slate-200/60 dark:bg-slate-700/60 text-slate-600 dark:text-slate-300';
      if (s.gust >= 15) {
        gustBg = 'bg-rose-500/25 dark:bg-rose-950/80 text-rose-700 dark:text-rose-300 font-extrabold border-t border-rose-300/40 dark:border-rose-700/50';
      } else if (s.gust >= 10) {
        gustBg = 'bg-amber-500/25 dark:bg-amber-950/80 text-amber-700 dark:text-amber-300 font-bold border-t border-amber-300/40 dark:border-amber-700/50';
      }

      return `
        <div style="width: ${slotWidth}px;" class="shrink-0 px-1 py-1">
          <div class="wind-pill text-center rounded-lg bg-slate-50/80 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60 overflow-hidden shadow-xs">
            <div class="pt-2 pb-1.5 px-0.5">
              <div class="font-mono font-bold text-xs sm:text-sm text-slate-800 dark:text-slate-100 leading-none">${s.wind}</div>
              <div class="flex items-center justify-center gap-1 text-[10px] mt-1 text-slate-500 dark:text-slate-400">
                <svg style="transform: rotate(${s.dir}deg)" class="w-2.5 h-2.5 text-sky-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 19V5m0 0l-4 4m4-4l4 4"/>
                </svg>
                <span class="font-medium">${s.dirName}</span>
              </div>
            </div>
            <div class="py-1 px-0.5 font-mono text-[11px] ${gustBg} tracking-tight">
              ${s.gust}
            </div>
          </div>
        </div>
      `;
    }).join('');

    const randId = 'gismeteo_scroll_' + Math.random().toString(36).substr(2, 6);

    return `
      <div class="w-full bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm p-4 overflow-hidden mb-6">
        <!-- Header: Breadcrumbs & Title & Day Selector & Nav -->
        <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800/80">
          <div>
            <div class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 tracking-tight truncate">
              Россия / ${region || 'Регион РФ'}
            </div>
            <h3 class="text-base sm:text-lg font-bold text-slate-800 dark:text-slate-100 tracking-tight">
              Погода в ${city ? (city.startsWith('г. ') ? city : 'г. ' + city) : 'городе'} на ${days.length} дня
            </h3>
          </div>
          <div class="flex items-center gap-2">
            <!-- Day Selector Toggle: 3 дня / 5 дней / 7 дней -->
            <div class="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-0.5 rounded-lg border border-slate-200/60 dark:border-slate-700/60 text-[11px] font-bold">
              <button type="button" onclick="if(window.setGismeteoDays)window.setGismeteoDays(3)" class="px-2 py-0.5 rounded ${days.length === 3 ? 'bg-white dark:bg-slate-700 text-sky-600 dark:text-sky-300 shadow-xs' : 'text-slate-500 hover:text-slate-800 dark:hover:text-white'} transition-colors cursor-pointer">3 дня</button>
              <button type="button" onclick="if(window.setGismeteoDays)window.setGismeteoDays(5)" class="px-2 py-0.5 rounded ${days.length === 5 ? 'bg-white dark:bg-slate-700 text-sky-600 dark:text-sky-300 shadow-xs' : 'text-slate-500 hover:text-slate-800 dark:hover:text-white'} transition-colors cursor-pointer">5 дней</button>
              <button type="button" onclick="if(window.setGismeteoDays)window.setGismeteoDays(7)" class="px-2 py-0.5 rounded ${days.length === 7 ? 'bg-white dark:bg-slate-700 text-sky-600 dark:text-sky-300 shadow-xs' : 'text-slate-500 hover:text-slate-800 dark:hover:text-white'} transition-colors cursor-pointer">7 дней</button>
            </div>
            <!-- Scroll Navigation Buttons -->
            <div class="flex items-center gap-1">
              <button onclick="document.getElementById('${randId}').scrollBy({left: -288, behavior: 'smooth'})" class="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors cursor-pointer" title="Назад">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/></svg>
              </button>
              <button onclick="document.getElementById('${randId}').scrollBy({left: 288, behavior: 'smooth'})" class="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors cursor-pointer" title="Вперед">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/></svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Scrollable Table -->
        <div id="${randId}" class="overflow-x-auto scrollbar-thin pt-2">
          <div style="min-width: ${totalW}px;" class="flex flex-col select-none">
            <!-- Row 1: Day Columns with Periods and Weather Icons -->
            <div class="flex w-full">
              ${daysColumnsHtml}
            </div>

            <!-- Row 2: Section Label for Temperature -->
            <div class="px-2 pt-2.5 pb-1 text-xs font-bold text-slate-600 dark:text-slate-400">
              Температура воздуха, °C
            </div>

            <!-- Row 3: CONTINUOUS STEPPED SVG RIBBON (ZERO CUTS, ZERO GAPS) -->
            <div class="w-full relative" style="height: ${ribbonH}px;">
              <svg width="${totalW}" height="${ribbonH}" viewBox="0 0 ${totalW} ${ribbonH}" fill="none" xmlns="http://www.w3.org/2000/svg" class="overflow-visible block">
                <defs>
                  <linearGradient id="frostGrad_${randId}" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="#cbe8fe"/>
                    <stop offset="100%" stop-color="#90cdf4"/>
                  </linearGradient>
                  <filter id="ribbonShadow_${randId}" x="-2%" y="-5%" width="104%" height="115%">
                    <feDropShadow dx="0" dy="1.5" stdDeviation="1.5" flood-color="#0284c7" flood-opacity="0.15"/>
                  </filter>
                </defs>
                <path d="${pathD}" fill="url(#frostGrad_${randId})" stroke="#7ec3f5" stroke-width="1.2" stroke-linejoin="miter" filter="url(#ribbonShadow_${randId})"/>
                ${tempTexts}
              </svg>
            </div>

            <!-- Row 4: Section Label for Wind -->
            <div class="px-2 pt-3 pb-1 flex items-center gap-1.5 text-xs font-bold text-slate-600 dark:text-slate-400">
              <svg class="w-3.5 h-3.5 text-sky-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" stroke-width="2"/>
                <path stroke-linecap="round" stroke-width="2" d="M12 16v-4m0-4h.01"/>
              </svg>
              <span>Ветер и порывы, м/с</span>
            </div>

            <!-- Row 5: Wind & Gusts Modular Cards -->
            <div class="flex w-full">
              ${windsHtml}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  return {
    getWmoDescription,
    renderDetailedMeteoIcon,
    getMeteoIconSvg,
    buildGismeteoDays,
    renderGismeteoFlawless
  };

}));
