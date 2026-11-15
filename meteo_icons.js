/**
 * MeteoCenter RF - High-Definition Vector Meteorological Icon & Visualizer System
 * Replaces cartoon unicode emojis with volumetric, layered, responsive SVG icons.
 * Fully compatible with WMO codes 0..99, ECMWF IFS, and Gismeteo-style visualizations.
 */

(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    const exports = factory();
    for (const key in exports) {
      root[key] = exports[key];
    }
  }
}(typeof self !== 'undefined' ? self : this, function () {

  const WMO_DESCRIPTIONS = {
    0: 'Ясно',
    1: 'Преимущественно ясно',
    2: 'Переменная облачность',
    3: 'Пасмурно',
    45: 'Туман',
    48: 'Изморозь',
    51: 'Легкая морось',
    53: 'Умеренная морось',
    55: 'Густая морось',
    56: 'Ледяная морось',
    57: 'Плотная ледяная морось',
    61: 'Небольшой дождь',
    63: 'Умеренный дождь',
    65: 'Сильный дождь',
    66: 'Ледяной дождь',
    67: 'Сильный ледяной дождь',
    71: 'Небольшой снегопад',
    73: 'Снегопад',
    75: 'Сильный снегопад',
    77: 'Снежная крупа',
    80: 'Ливневый дождь',
    81: 'Сильный ливень',
    82: 'Шквалистый ливень',
    85: 'Снежный заряд',
    86: 'Метель',
    95: 'Гроза',
    96: 'Гроза с градом',
    99: 'Шквал с градом'
  };

  function getWmoDescription(code) {
    code = parseInt(code, 10);
    return WMO_DESCRIPTIONS[code] || 'Переменная облачность';
  }

  function getMeteoIconSvg(code, isDay, size) {
    code = parseInt(code, 10);
    if (isNaN(code)) code = 0;
    isDay = (isDay === 0 || isDay === false) ? 0 : 1;
    size = size || 32;

    // 0: Clear Sky
    if (code === 0) {
      if (isDay) {
        return `<svg width="${size}" height="${size}" viewBox="0 0 48 48" class="inline-block shrink-0 select-none overflow-visible" fill="none">
          <defs>
            <radialGradient id="mcSunGrad_${size}" cx="40%" cy="40%" r="60%">
              <stop offset="0%" stop-color="#fef08a"/>
              <stop offset="50%" stop-color="#fbbf24"/>
              <stop offset="100%" stop-color="#f59e0b"/>
            </radialGradient>
          </defs>
          <circle cx="24" cy="24" r="10" fill="url(#mcSunGrad_${size})"/>
          <g stroke="#f59e0b" stroke-width="2.2" stroke-linecap="round" opacity="0.9">
            <line x1="24" y1="4" x2="24" y2="9"/><line x1="24" y1="39" x2="24" y2="44"/>
            <line x1="4" y1="24" x2="9" y2="24"/><line x1="39" y1="24" x2="44" y2="24"/>
            <line x1="10" y1="10" x2="13.5" y2="13.5"/><line x1="34.5" y1="34.5" x2="38" y2="38"/>
            <line x1="38" y1="10" x2="34.5" y2="13.5"/><line x1="13.5" y1="34.5" x2="10" y2="38"/>
          </g>
        </svg>`;
      } else {
        return `<svg width="${size}" height="${size}" viewBox="0 0 48 48" class="inline-block shrink-0 select-none overflow-visible" fill="none">
          <defs>
            <linearGradient id="mcMoonGrad_${size}" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#fef9c3"/><stop offset="100%" stop-color="#facc15"/>
            </linearGradient>
          </defs>
          <path d="M30 11 A14 14 0 0 1 18 33 A15 15 0 1 0 30 11 Z" fill="url(#mcMoonGrad_${size})" stroke="#eab308" stroke-width="1.2"/>
          <circle cx="36" cy="14" r="1.5" fill="#fef08a"/>
          <circle cx="33" cy="23" r="1.2" fill="#bae6fd"/>
        </svg>`;
      }
    }

    // 1, 2: Partly Cloudy
    if (code === 1 || code === 2) {
      if (isDay) {
        return `<svg width="${size}" height="${size}" viewBox="0 0 48 48" class="inline-block shrink-0 select-none overflow-visible" fill="none">
          <defs>
            <radialGradient id="mcSunMini_${size}" cx="40%" cy="40%" r="60%">
              <stop offset="0%" stop-color="#fef08a"/><stop offset="100%" stop-color="#f59e0b"/>
            </radialGradient>
            <linearGradient id="mcCloudGrad_${size}" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#cbd5e1"/>
            </linearGradient>
          </defs>
          <g transform="translate(10, 6)">
            <circle cx="12" cy="12" r="8" fill="url(#mcSunMini_${size})"/>
            <g stroke="#f59e0b" stroke-width="1.8" stroke-linecap="round" opacity="0.85">
              <line x1="12" y1="0" x2="12" y2="3"/><line x1="24" y1="12" x2="21" y2="12"/>
              <line x1="3.5" y1="3.5" x2="5.5" y2="5.5"/><line x1="20.5" y1="3.5" x2="18.5" y2="5.5"/>
            </g>
          </g>
          <path d="M14 36 h22 a8 8 0 0 0 1-15.9 A11 11 0 0 0 16 17 a9 9 0 0 0 -2 19 Z" fill="url(#mcCloudGrad_${size})" stroke="#94a3b8" stroke-width="1.1"/>
        </svg>`;
      } else {
        return `<svg width="${size}" height="${size}" viewBox="0 0 48 48" class="inline-block shrink-0 select-none overflow-visible" fill="none">
          <defs>
            <linearGradient id="mcCloudNight_${size}" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stop-color="#e2e8f0"/><stop offset="100%" stop-color="#94a3b8"/>
            </linearGradient>
          </defs>
          <path d="M28 8 A10 10 0 0 1 19 24 A11 11 0 1 0 28 8 Z" fill="#fef08a" stroke="#eab308" stroke-width="1"/>
          <path d="M14 36 h22 a8 8 0 0 0 1-15.9 A11 11 0 0 0 16 17 a9 9 0 0 0 -2 19 Z" fill="url(#mcCloudNight_${size})" stroke="#64748b" stroke-width="1"/>
        </svg>`;
      }
    }

    // 3: Overcast
    if (code === 3) {
      return `<svg width="${size}" height="${size}" viewBox="0 0 48 48" class="inline-block shrink-0 select-none overflow-visible" fill="none">
        <defs>
          <linearGradient id="mcBackCloud_${size}" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#94a3b8"/><stop offset="100%" stop-color="#64748b"/>
          </linearGradient>
          <linearGradient id="mcFrontCloud_${size}" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#cbd5e1"/>
          </linearGradient>
        </defs>
        <path d="M18 29 h18 a7 7 0 0 0 1-13.9 A9.5 9.5 0 0 0 20 12 a8 8 0 0 0 -2 17 Z" fill="url(#mcBackCloud_${size})" opacity="0.8"/>
        <path d="M12 37 h22 a8 8 0 0 0 1-15.9 A11 11 0 0 0 14 18 a9 9 0 0 0 -2 19 Z" fill="url(#mcFrontCloud_${size})" stroke="#94a3b8" stroke-width="1.1"/>
      </svg>`;
    }

    // 45, 48: Fog
    if (code === 45 || code === 48) {
      return `<svg width="${size}" height="${size}" viewBox="0 0 48 48" class="inline-block shrink-0 select-none overflow-visible" fill="none">
        <path d="M16 22 h16 a6 6 0 0 0 1-11.9 A8.5 8.5 0 0 0 18 9 a7 7 0 0 0 -2 13 Z" fill="#cbd5e1" opacity="0.75"/>
        <rect x="8" y="26" width="32" height="3" rx="1.5" fill="#94a3b8"/>
        <rect x="12" y="32" width="24" height="3" rx="1.5" fill="#94a3b8"/>
        <rect x="10" y="38" width="28" height="2.5" rx="1.2" fill="#94a3b8" opacity="0.7"/>
      </svg>`;
    }

    // 51, 53, 55: Drizzle
    if (code >= 51 && code <= 55) {
      return `<svg width="${size}" height="${size}" viewBox="0 0 48 48" class="inline-block shrink-0 select-none overflow-visible" fill="none">
        <path d="M12 28 h22 a7.5 7.5 0 0 0 1-14.9 A10.5 10.5 0 0 0 14 10 a8.5 8.5 0 0 0 -2 18 Z" fill="#e2e8f0" stroke="#64748b" stroke-width="1"/>
        <g stroke="#38bdf8" stroke-width="2" stroke-linecap="round">
          <line x1="16" y1="33" x2="14" y2="38"/><line x1="24" y1="33" x2="22" y2="38"/><line x1="32" y1="33" x2="30" y2="38"/>
        </g>
      </svg>`;
    }

    // 56, 57: Freezing Drizzle
    if (code === 56 || code === 57) {
      return `<svg width="${size}" height="${size}" viewBox="0 0 48 48" class="inline-block shrink-0 select-none overflow-visible" fill="none">
        <path d="M12 28 h22 a7.5 7.5 0 0 0 1-14.9 A10.5 10.5 0 0 0 14 10 a8.5 8.5 0 0 0 -2 18 Z" fill="#e2e8f0" stroke="#0284c7" stroke-width="1.1"/>
        <g stroke="#38bdf8" stroke-width="2" stroke-linecap="round">
          <line x1="16" y1="33" x2="14" y2="38"/><line x1="32" y1="33" x2="30" y2="38"/>
        </g>
        <g transform="translate(24, 35)">
          <circle cx="0" cy="0" r="1.5" fill="#38bdf8"/>
        </g>
      </svg>`;
    }

    // 61, 63, 65, 80, 81: Rain
    if (code === 61 || code === 63 || code === 65 || code === 80 || code === 81) {
      return `<svg width="${size}" height="${size}" viewBox="0 0 48 48" class="inline-block shrink-0 select-none overflow-visible" fill="none">
        <defs>
          <linearGradient id="mcRainHeavy_${size}" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#e2e8f0"/><stop offset="100%" stop-color="#64748b"/>
          </linearGradient>
        </defs>
        <path d="M12 27 h22 a7.5 7.5 0 0 0 1-14.9 A10.5 10.5 0 0 0 14 9 a8.5 8.5 0 0 0 -2 18 Z" fill="url(#mcRainHeavy_${size})" stroke="#475569" stroke-width="1.1"/>
        <g stroke="#0284c7" stroke-width="2.4" stroke-linecap="round">
          <line x1="15" y1="32" x2="12" y2="40"/><line x1="22" y1="32" x2="19" y2="40"/><line x1="29" y1="32" x2="26" y2="40"/><line x1="35" y1="33" x2="32" y2="40"/>
        </g>
      </svg>`;
    }

    // 66, 67: Freezing Rain
    if (code === 66 || code === 67) {
      return `<svg width="${size}" height="${size}" viewBox="0 0 48 48" class="inline-block shrink-0 select-none overflow-visible" fill="none">
        <path d="M12 27 h22 a7.5 7.5 0 0 0 1-14.9 A10.5 10.5 0 0 0 14 9 a8.5 8.5 0 0 0 -2 18 Z" fill="#cbd5e1" stroke="#0284c7" stroke-width="1.1"/>
        <g stroke="#0284c7" stroke-width="2.2" stroke-linecap="round">
          <line x1="16" y1="32" x2="13" y2="40"/><line x1="32" y1="32" x2="29" y2="40"/>
        </g>
        <g transform="translate(24, 36)">
          <circle cx="0" cy="0" r="2.2" fill="#38bdf8"/>
        </g>
      </svg>`;
    }

    // 71, 73, 75, 77: Snow
    if (code >= 71 && code <= 77) {
      return `<svg width="${size}" height="${size}" viewBox="0 0 48 48" class="inline-block shrink-0 select-none overflow-visible" fill="none">
        <defs>
          <linearGradient id="mcSnow_${size}" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#cbd5e1"/>
          </linearGradient>
        </defs>
        <path d="M12 28 h22 a7.5 7.5 0 0 0 1-14.9 A10.5 10.5 0 0 0 14 10 a8.5 8.5 0 0 0 -2 18 Z" fill="url(#mcSnow_${size})" stroke="#94a3b8" stroke-width="1"/>
        <g stroke="#38bdf8" stroke-linecap="round">
          <g transform="translate(15, 35)">
            <line x1="-3" y1="0" x2="3" y2="0" stroke-width="1.2"/><line x1="0" y1="-3" x2="0" y2="3" stroke-width="1.2"/>
            <circle cx="0" cy="0" r="1.2" fill="#0284c7"/>
          </g>
          <g transform="translate(24, 38)">
            <line x1="-3.5" y1="0" x2="3.5" y2="0" stroke-width="1.3"/><line x1="0" y1="-3.5" x2="0" y2="3.5" stroke-width="1.3"/>
            <circle cx="0" cy="0" r="1.4" fill="#0284c7"/>
          </g>
          <g transform="translate(33, 35)">
            <line x1="-3" y1="0" x2="3" y2="0" stroke-width="1.2"/><line x1="0" y1="-3" x2="0" y2="3" stroke-width="1.2"/>
            <circle cx="0" cy="0" r="1.2" fill="#0284c7"/>
          </g>
        </g>
      </svg>`;
    }

    // 85, 86: Blizzard / Snowstorm (with Gismeteo-Style Hazard Triangle Badge)
    if (code === 85 || code === 86) {
      return `<svg width="${size}" height="${size}" viewBox="0 0 48 48" class="inline-block shrink-0 select-none overflow-visible" fill="none">
        <defs>
          <linearGradient id="mcBlizz_${size}" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#e2e8f0"/><stop offset="100%" stop-color="#64748b"/>
          </linearGradient>
        </defs>
        <path d="M10 27 h24 a7.5 7.5 0 0 0 1-14.9 A10.5 10.5 0 0 0 12 9 a8.5 8.5 0 0 0 -2 18 Z" fill="url(#mcBlizz_${size})" stroke="#475569" stroke-width="1.1"/>
        <path d="M6 34 q8 -3 16 0 q4 1 8 -1" stroke="#38bdf8" stroke-width="1.6" stroke-linecap="round" fill="none"/>
        <path d="M10 39 q8 -2 14 0 q5 1 10 -2" stroke="#bae6fd" stroke-width="1.4" stroke-linecap="round" fill="none"/>
        <g transform="translate(30, 8)">
          <polygon points="8,1 15,14 1,14" fill="#f59e0b" stroke="#d97706" stroke-width="1.2" stroke-linejoin="round"/>
          <circle cx="8" cy="9" r="2.5" fill="#ffffff" opacity="0.9"/>
          <path d="M7 8 q1 -1 2 0 q1 1 0 2" stroke="#b45309" stroke-width="1.2" fill="none"/>
        </g>
      </svg>`;
    }

    // 95, 96, 99, 82: Thunderstorm
    if (code >= 95 || code === 82) {
      return `<svg width="${size}" height="${size}" viewBox="0 0 48 48" class="inline-block shrink-0 select-none overflow-visible" fill="none">
        <defs>
          <linearGradient id="mcStorm_${size}" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#64748b"/><stop offset="100%" stop-color="#334155"/>
          </linearGradient>
        </defs>
        <path d="M12 26 h22 a7.5 7.5 0 0 0 1-14.9 A10.5 10.5 0 0 0 14 8 a8.5 8.5 0 0 0 -2 18 Z" fill="url(#mcStorm_${size})" stroke="#1e293b" stroke-width="1.2"/>
        <polygon points="26,24 20,33 25,33 22,43 31,31 26,31" fill="#fde047" stroke="#eab308" stroke-width="1.2" stroke-linejoin="round"/>
        <line x1="14" y1="32" x2="11" y2="39" stroke="#38bdf8" stroke-width="2" stroke-linecap="round"/>
        <line x1="33" y1="32" x2="30" y2="39" stroke="#38bdf8" stroke-width="2" stroke-linecap="round"/>
      </svg>`;
    }

    // Fallback: Neutral Cloud with Soft Sun
    return `<svg width="${size}" height="${size}" viewBox="0 0 48 48" class="inline-block shrink-0 select-none overflow-visible" fill="none">
      <circle cx="28" cy="18" r="8" fill="#fbbf24"/>
      <path d="M14 36 h22 a8 8 0 0 0 1-15.9 A11 11 0 0 0 16 17 a9 9 0 0 0 -2 19 Z" fill="#ffffff" stroke="#94a3b8" stroke-width="1"/>
    </svg>`;
  }

  return {
    WMO_DESCRIPTIONS,
    getWmoDescription,
    getMeteoIconSvg
  };

}));
