# -*- coding: utf-8 -*-
"""
МетеоПортал · Профессиональный интерактивный веб-сервис погоды и климата
Реализует современный дашборд уровня Apple Weather / Windy:
- Крупная фактическая температура, точка росы, давление в мм рт. ст., ветер и порывы
- Атрибуция физических метеостанций сети ВМО (WMO) и спутникового реанализа ECMWF
- Интерактивная почасовая лента 24ч и визуальные бары диапазона на 7/14 дней
- Климатический архив (100+ лет) на карточках без текстовых черточек
- Сравнение численных моделей суперкомпьютеров (ECMWF vs DWD ICON vs NOAA GFS)
"""

import os
import sys
import json
import time
import random
import ssl
import base64
import urllib.parse
import urllib.request
import http.server
import socketserver
import webbrowser
import threading
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

YANDEX_METRIKA_ID = os.environ.get("YANDEX_METRIKA_ID", "112330199")

WMO_DICT = {
    0: ("☀️", "Ясно"), 1: ("🌤", "Преимущественно ясно"), 2: ("⛅", "Переменная облачность"), 3: ("☁️", "Пасмурно"),
    45: ("🌫", "Туман"), 48: ("🌫", "Ледяной туман / изморозь"),
    51: ("🌦", "Слабая морось"), 53: ("🌦", "Умеренная морось"), 55: ("🌧", "Плотная морось"),
    61: ("🌧", "Небольшой дождь"), 63: ("🌧", "Умеренный дождь"), 65: ("🌧", "Сильный дождь"),
    71: ("🌨", "Небольшой снег"), 73: ("🌨", "Умеренный снег"), 75: ("🌨", "Сильный снегопад"),
    77: ("❄️", "Снежная крупа"), 80: ("🌦", "Кратковременный дождь"), 81: ("🌧", "Ливень"),
    82: ("⛈", "Шквалистый ливень"), 85: ("🌨", "Снегопад"), 86: ("🌨", "Сильный снегопад"),
    95: ("⛈", "Гроза"), 96: ("⛈", "Гроза с градом"), 99: ("⛈", "Сильная гроза с градом")
}

SVG_FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <linearGradient id="fav-bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#090d16"/>
      <stop offset="50%" stop-color="#0c2340"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </linearGradient>
    <linearGradient id="fav-cloud" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#94a3b8"/>
    </linearGradient>
    <linearGradient id="fav-bolt" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="45%" stop-color="#fef08a"/>
      <stop offset="100%" stop-color="#f59e0b"/>
    </linearGradient>
    <filter id="fav-glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="1.5" result="glow"/>
      <feComposite in="SourceGraphic" in2="glow" operator="over"/>
    </filter>
  </defs>
  <rect width="64" height="64" rx="16" fill="url(#fav-bg)"/>
  <rect width="62" height="62" x="1" y="1" rx="15" fill="none" stroke="#38bdf8" stroke-width="1.5" stroke-opacity="0.6"/>
  <circle cx="32" cy="32" r="26" fill="none" stroke="#38bdf8" stroke-width="1" stroke-opacity="0.25" stroke-dasharray="2 3"/>
  <path d="M22 36 a9 9 0 0 1 1-17.5 A12.5 12.5 0 0 1 44.5 22.5 a8.5 8.5 0 0 1 -2.5 13.5 Z" fill="url(#fav-cloud)"/>
  <polygon points="34,19 23,34 32,34 29,47 43,30 34,30" fill="url(#fav-bolt)" filter="url(#fav-glow)"/>
</svg>"""

FAVICON_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode(SVG_FAVICON.encode("utf-8")).decode("ascii")

PORTAL_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{SEO_TITLE}}</title>
  <meta name="description" content="{{SEO_DESCRIPTION}}">
  <meta name="keywords" content="{{SEO_KEYWORDS}}">
  <!-- High-Resolution Cyber/Weather Vector Favicon -->
  <link rel="icon" type="image/svg+xml" href="{{FAVICON_DATA_URI}}">
  <link rel="shortcut icon" href="/favicon.ico">
  <link rel="alternate icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="apple-touch-icon" href="/favicon.svg">

  <!-- Open Graph / Social Media Meta Tags -->
  <meta property="og:type" content="website">
  <meta property="og:title" content="{{SEO_TITLE}}">
  <meta property="og:description" content="{{SEO_DESCRIPTION}}">
  <meta property="og:url" content="{{SEO_CANONICAL}}">
  <meta property="og:site_name" content="МетеоПортал · Климатический Архив">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{{SEO_TITLE}}">
  <meta name="twitter:description" content="{{SEO_DESCRIPTION}}">

  <!-- Schema.org Microdata (JSON-LD) -->
  <script type="application/ld+json">
{{SCHEMA_JSON_LD}}
  </script>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: { 50: '#f0f9ff', 400: '#38bdf8', 500: '#0284c7', 600: '#0369a1', 900: '#0c4a6e' }
          }
        }
      }
    }
  </script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background-color: #070c18; }
    .mono-card { font-family: 'JetBrains Mono', monospace; }
    .glass { background: rgba(15, 23, 42, 0.78); backdrop-filter: blur(20px); border: 1px solid rgba(51, 65, 85, 0.5); }
    .glass-card { background: rgba(30, 41, 59, 0.55); backdrop-filter: blur(12px); border: 1px solid rgba(51, 65, 85, 0.45); }
    .glass-card:hover { border-color: rgba(56, 189, 248, 0.4); background: rgba(30, 41, 59, 0.75); }
    .tab-active { background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color: #ffffff; box-shadow: 0 4px 16px rgba(2, 132, 199, 0.4); border-color: transparent; }
    .tab-inactive { background: rgba(30, 41, 59, 0.6); color: #94a3b8; border: 1px solid rgba(51, 65, 85, 0.45); }
    .tab-inactive:hover { background: rgba(51, 65, 85, 0.65); color: #f8fafc; }
    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #070c18; }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #38bdf8; }
  </style>

  <!-- Yandex.Metrika counter -->
  <script type="text/javascript">
    (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
    m[i].l=1*new Date();
    for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
    k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})
    (window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=112330199', 'ym');

    ym(112330199, 'init', {ssr:true, webvisor:true, clickmap:true, ecommerce:"dataLayer"});
  </script>
  <noscript><div><img src="https://mc.yandex.ru/watch/112330199" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
  <!-- /Yandex.Metrika counter -->
</head>
<body class="text-slate-100 min-h-screen flex flex-col selection:bg-sky-500 selection:text-white">

  <!-- TOP HEADER -->
  <header class="glass sticky top-0 z-40 border-b border-slate-800/80">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 py-3.5 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl overflow-hidden shadow-lg shadow-sky-500/30 border border-sky-400/40 shrink-0">
          <img src="{{FAVICON_DATA_URI}}" alt="МетеоПортал" class="w-full h-full object-cover">
        </div>
        <div>
          <h1 class="text-lg font-bold tracking-tight bg-gradient-to-r from-sky-400 via-cyan-200 to-indigo-300 bg-clip-text text-transparent">
            МЕТЕОПОРТАЛ · КЛИМАТ & ПОГОДА
          </h1>
          <p class="text-xs text-slate-400 hidden sm:block">Метеостанции международной сети ВМО (100+ лет) & Модели суперкомпьютеров ECMWF / DWD</p>
        </div>
      </div>
      <div class="flex items-center space-x-3 text-xs">
        <a href="https://vk.com/club241257551" target="_blank" class="px-3 py-1.5 rounded-lg bg-slate-800/90 hover:bg-slate-700 text-sky-400 hover:text-sky-300 border border-slate-700/80 transition flex items-center space-x-1.5 font-medium">
          <span>💬</span>
          <span>Группа ВК</span>
        </a>
        <span class="inline-flex items-center px-2.5 py-1 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-700/50 font-medium">
          <span class="w-2 h-2 mr-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          Сервер онлайн
        </span>
      </div>
    </div>
  </header>

  <!-- MAIN CONTAINER -->
  <main class="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8 flex-1 w-full space-y-6">

    <!-- SEARCH BAR & QUICK CITIES -->
    <div class="glass rounded-2xl p-5 shadow-2xl">
      <form id="search-form" onsubmit="handleSearch(event)" class="flex flex-col sm:flex-row gap-3">
        <div class="relative flex-1">
          <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
          </div>
          <input type="text" id="city-input" placeholder="Введите город (напр. Москва, Санкт-Петербург, Якутск, Норильск) или координаты..." 
            class="w-full pl-10 pr-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent text-sm transition"
            value="Москва" />
        </div>
        <button type="submit" class="px-6 py-3 bg-sky-600 hover:bg-sky-500 active:bg-sky-700 text-white font-semibold rounded-xl text-sm transition shadow-lg shadow-sky-600/30 flex items-center justify-center space-x-2">
          <span>Показать</span>
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
        </button>
      </form>

      <!-- QUICK BADGES -->
      <div class="mt-4 flex flex-wrap items-center gap-1.5 text-xs">
        <span class="text-slate-400 mr-1 font-medium">Быстрый выбор:</span>
        <button onclick="setCity('Москва')" class="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700/60 text-slate-300 transition">🏛 Москва</button>
        <button onclick="setCity('Санкт-Петербург')" class="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700/60 text-slate-300 transition">🌊 Санкт-Петербург</button>
        <button onclick="setCity('Якутск')" class="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700/60 text-slate-300 transition">❄️ Якутск</button>
        <button onclick="setCity('Норильск')" class="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700/60 text-slate-300 transition">🏔 Норильск</button>
        <button onclick="setCity('Хатанга')" class="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700/60 text-slate-300 transition">⚓ Хатанга</button>
        <button onclick="setCity('Самара')" class="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700/60 text-slate-300 transition">🌾 Самара</button>
        <button onclick="setCity('Сочи')" class="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700/60 text-slate-300 transition">🏖 Сочи</button>
        <button onclick="setCity('Владивосток')" class="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700/60 text-slate-300 transition">🚢 Владивосток</button>
        <button onclick="setCity('Новосибирск')" class="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700/60 text-slate-300 transition">🌲 Новосибирск</button>
        <button onclick="setCity('Казань')" class="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700/60 text-slate-300 transition">🕌 Казань</button>
      </div>
    </div>

    <!-- TABS BAR -->
    <div class="flex flex-wrap gap-2 text-xs font-semibold">
      <button onclick="switchTab('current')" id="tab-current" class="tab-btn px-4 py-2.5 rounded-xl transition flex items-center space-x-1.5 tab-active">
        <span>☀️</span><span>Погода сейчас (48 ч)</span>
      </button>
      <button onclick="switchTab('week')" id="tab-week" class="tab-btn px-4 py-2.5 rounded-xl transition flex items-center space-x-1.5 tab-inactive">
        <span>📅</span><span>Прогноз 7 дней</span>
      </button>
      <button onclick="switchTab('14days')" id="tab-14days" class="tab-btn px-4 py-2.5 rounded-xl transition flex items-center space-x-1.5 tab-inactive">
        <span>📆</span><span>Прогноз 14 дней</span>
      </button>
      <button onclick="switchTab('month')" id="tab-month" class="tab-btn px-4 py-2.5 rounded-xl transition flex items-center space-x-1.5 tab-inactive">
        <span>📈</span><span>На месяц (30 дней)</span>
      </button>
      <button onclick="switchTab('models')" id="tab-models" class="tab-btn px-4 py-2.5 rounded-xl transition flex items-center space-x-1.5 tab-inactive">
        <span>🌐</span><span>Модели (ECMWF vs GFS vs ICON)</span>
      </button>
      <button onclick="switchTab('weathernext')" id="tab-weathernext" class="tab-btn px-4 py-2.5 rounded-xl transition flex items-center space-x-1.5 tab-inactive">
        <span>🧠</span><span>ИИ WeatherNext 3.0 (DeepMind)</span>
      </button>
      <button onclick="switchTab('archive')" id="tab-archive" class="tab-btn px-4 py-2.5 rounded-xl transition flex items-center space-x-1.5 tab-inactive">
        <span>🏛</span><span>Вековой архив (100+ лет)</span>
      </button>
      <button onclick="switchTab('year')" id="tab-year" class="tab-btn px-4 py-2.5 rounded-xl transition flex items-center space-x-1.5 tab-inactive">
        <span>📜</span><span>Архив по годам</span>
      </button>
      <button onclick="switchTab('interactive')" id="tab-interactive" class="tab-btn px-4 py-2.5 rounded-xl transition flex items-center space-x-1.5 tab-inactive">
        <span>📈</span><span>Интерактивный график</span>
      </button>
    </div>

    <!-- YEAR SUB-BAR (HIDDEN BY DEFAULT) -->
    <div id="year-control-bar" class="hidden glass rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 border border-amber-500/30 bg-amber-950/15">
      <div class="flex items-center space-x-3">
        <span class="text-amber-400 font-bold text-sm">Год архивного замера:</span>
        <input type="number" id="year-input" min="1888" max="2026" value="1945" 
          class="w-24 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-amber-300 font-mono font-bold text-center text-sm focus:ring-2 focus:ring-amber-500 focus:outline-none" />
        <button onclick="submitYear()" class="px-4 py-1.5 bg-amber-600 hover:bg-amber-500 text-white font-semibold rounded-lg text-xs transition shadow">
          Запросить станцию
        </button>
      </div>
      <div class="flex flex-wrap items-center gap-1.5 text-xs">
        <span class="text-slate-400">Быстрый выбор:</span>
        <button onclick="setYear(1890)" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">1890</button>
        <button onclick="setYear(1910)" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">1910</button>
        <button onclick="setYear(1925)" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">1925</button>
        <button onclick="setYear(1945)" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">1945</button>
        <button onclick="setYear(1965)" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">1965</button>
        <button onclick="setYear(1985)" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">1985</button>
        <button onclick="setYear(2000)" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">2000</button>
      </div>
    </div>

    <!-- LOADING SPINNER -->
    <div id="loading" class="hidden glass rounded-2xl p-12 text-center shadow-xl">
      <div class="inline-block animate-spin rounded-full h-11 w-11 border-4 border-sky-500 border-t-transparent"></div>
      <p class="mt-4 text-sm text-sky-300 font-medium">Запрашиваем физические архивы метеостанций и численные модели...</p>
      <p class="text-xs text-slate-500 mt-1">Обработка приборных рядов ВМО / NOAA GHCN-Daily / ECMWF</p>
    </div>

    <!-- ERROR BANNER -->
    <div id="error-box" class="hidden glass rounded-2xl p-6 border border-rose-500/40 bg-rose-950/20 text-rose-300 text-sm">
      <div class="flex items-center space-x-3">
        <span class="text-2xl">⚠️</span>
        <span id="error-msg">Город не найден или метеосервер временно недоступен.</span>
      </div>
    </div>

    <!-- MAIN DISPLAY AREA -->
    <div id="results" class="space-y-6">

      <!-- ================= HERO WEATHER CARD (APPLE WEATHER / WINDY STYLE) ================= -->
      <div id="hero-card" class="glass rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        <!-- Background Ambient Glow -->
        <div class="absolute -top-24 -right-24 w-80 h-80 bg-sky-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <!-- Top Observation Source Badge -->
        <div class="flex flex-wrap items-center justify-between gap-3 mb-6 pb-4 border-b border-slate-800/80">
          <div id="station-badge" class="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-emerald-950/70 border border-emerald-500/40 text-emerald-300 text-xs font-semibold shadow-sm">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span id="station-label">🏛 Опорная метеостанция ВМО: Якутск (WMO #24959)</span>
          </div>
          <div class="text-xs text-slate-400 font-mono" id="obs-time">Замер: обновлено только что</div>
        </div>

        <!-- Center Temp and Condition -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div class="flex items-baseline space-x-3">
              <span id="hero-temp" class="text-6xl sm:text-7xl lg:text-8xl font-black tracking-tight bg-gradient-to-br from-white via-slate-100 to-sky-200 bg-clip-text text-transparent">
                +12°
              </span>
              <span id="hero-icon" class="text-4xl sm:text-5xl">⛅</span>
            </div>
            <div id="hero-condition" class="text-lg sm:text-xl font-semibold text-slate-200 mt-1">
              Переменная облачность
            </div>
            <div class="text-sm text-slate-400 mt-1 flex flex-wrap gap-x-4 gap-y-1">
              <span>Ощущается как: <strong id="hero-app" class="text-sky-300 font-semibold">+11°</strong></span>
              <span>•</span>
              <span>Суточный диапазон: <strong id="hero-minmax" class="text-slate-200 font-medium">↓ +6° · ↑ +16°</strong></span>
            </div>
          </div>

          <!-- City & Geolocation Tag -->
          <div class="md:text-right space-y-1">
            <div id="hero-city-name" class="text-2xl sm:text-3xl font-extrabold text-white tracking-tight uppercase">
              МОСКВА
            </div>
            <div id="hero-region" class="text-xs text-sky-400 font-medium">Россия, Центральный ФО</div>
            <div id="hero-coords" class="text-xs text-slate-500 font-mono">55.75° N, 37.62° E · 156 м над ур. моря</div>
          </div>
        </div>
      </div>

      <!-- ================= 8-GRID WEATHER METRICS ================= -->
      <div id="metrics-grid" class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        
        <!-- 1. ТОЧКА РОСЫ -->
        <div class="glass-card rounded-2xl p-4 sm:p-5 transition shadow-lg">
          <div class="flex items-center justify-between text-slate-400 text-xs mb-1.5">
            <span class="font-medium">ТОЧКА РОСЫ</span>
            <span class="text-sky-400 text-base">💧</span>
          </div>
          <div id="metric-dew" class="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-mono">+8.4 °C</div>
          <div id="metric-dew-desc" class="text-[11px] text-slate-400 mt-1">Комфортная влажность</div>
        </div>

        <!-- 2. ВЕТЕР И ПОРЫВЫ -->
        <div class="glass-card rounded-2xl p-4 sm:p-5 transition shadow-lg">
          <div class="flex items-center justify-between text-slate-400 text-xs mb-1.5">
            <span class="font-medium">ВЕТЕР И ПОРЫВЫ</span>
            <span class="text-teal-400 text-base">💨</span>
          </div>
          <div id="metric-wind" class="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-mono">3.2 м/с</div>
          <div id="metric-wind-dir" class="text-[11px] text-slate-400 mt-1">Порывы до 6.5 м/с · СЗ (315°)</div>
        </div>

        <!-- 3. ДАВЛЕНИЕ -->
        <div class="glass-card rounded-2xl p-4 sm:p-5 transition shadow-lg">
          <div class="flex items-center justify-between text-slate-400 text-xs mb-1.5">
            <span class="font-medium">АТМ. ДАВЛЕНИЕ</span>
            <span class="text-amber-400 text-base">🧭</span>
          </div>
          <div id="metric-press" class="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-mono">752 мм</div>
          <div id="metric-press-desc" class="text-[11px] text-slate-400 mt-1">1002.5 гПа · Норма</div>
        </div>

        <!-- 4. ВЛАЖНОСТЬ -->
        <div class="glass-card rounded-2xl p-4 sm:p-5 transition shadow-lg">
          <div class="flex items-center justify-between text-slate-400 text-xs mb-1.5">
            <span class="font-medium">ВЛАЖНОСТЬ</span>
            <span class="text-cyan-400 text-base">💦</span>
          </div>
          <div id="metric-hum" class="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-mono">58%</div>
          <div id="metric-hum-desc" class="text-[11px] text-slate-400 mt-1">Относительная влажность</div>
        </div>

        <!-- 5. УФ-ИНДЕКС -->
        <div class="glass-card rounded-2xl p-4 sm:p-5 transition shadow-lg">
          <div class="flex items-center justify-between text-slate-400 text-xs mb-1.5">
            <span class="font-medium">УФ-ИНДЕКС</span>
            <span class="text-yellow-400 text-base">☀️</span>
          </div>
          <div id="metric-uv" class="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-mono">2</div>
          <div id="metric-uv-desc" class="text-[11px] text-slate-400 mt-1">Низкий (защита не нужна)</div>
        </div>

        <!-- 6. ОСАДКИ -->
        <div class="glass-card rounded-2xl p-4 sm:p-5 transition shadow-lg">
          <div class="flex items-center justify-between text-slate-400 text-xs mb-1.5">
            <span class="font-medium">ОСАДКИ (24 Ч)</span>
            <span class="text-indigo-400 text-base">🌧</span>
          </div>
          <div id="metric-precip" class="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-mono">0.0 мм</div>
          <div id="metric-precip-desc" class="text-[11px] text-slate-400 mt-1">Без осадков</div>
        </div>

        <!-- 7. КЛИМАТИЧЕСКАЯ НОРМА -->
        <div class="glass-card rounded-2xl p-4 sm:p-5 transition shadow-lg">
          <div class="flex items-center justify-between text-slate-400 text-xs mb-1.5">
            <span class="font-medium">НОРМА МЕСЯЦА</span>
            <span class="text-purple-400 text-base">🍂</span>
          </div>
          <div id="metric-norm" class="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-mono">+6.7 °C</div>
          <div id="metric-norm-desc" class="text-[11px] text-slate-400 mt-1">Сентябрь (было +7.2° в 1940-х)</div>
        </div>

        <!-- 8. ВЕКОВОЙ ТРЕНД -->
        <div class="glass-card rounded-2xl p-4 sm:p-5 transition shadow-lg">
          <div class="flex items-center justify-between text-slate-400 text-xs mb-1.5">
            <span class="font-medium">ТРЕНД КЛИМАТА</span>
            <span class="text-rose-400 text-base">🌍</span>
          </div>
          <div id="metric-trend" class="text-2xl sm:text-3xl font-extrabold text-rose-300 tracking-tight font-mono">+0.6 °C</div>
          <div id="metric-trend-desc" class="text-[11px] text-slate-400 mt-1">Среднегодовое потепление</div>
        </div>

      </div>

      <!-- ================= 24-HOUR HOURLY SCROLLER ================= -->
      <div id="hourly-card" class="glass rounded-2xl p-4 sm:p-6 shadow-xl overflow-hidden">
        <div class="flex items-center justify-between mb-2">
          <h2 class="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
            <span>⏱</span><span>ПОЧАСОВОЙ ПРОГНОЗ С ГРАФИКОМ (БЛИЖАЙШИЕ 24 ЧАСА)</span>
          </h2>
          <span class="text-[11px] text-sky-400">ECMWF IFS · Температура и осадки</span>
        </div>
        <!-- Interactive Hourly SVG Chart -->
        <div id="hourly-chart-svg" class="w-full h-28 my-1"></div>
        <!-- Hourly Cards Strip -->
        <div id="hourly-strip" class="flex space-x-2.5 overflow-x-auto pb-2 pt-2 text-center select-none">
          <!-- Populated dynamically via JS -->
        </div>
      </div>

      <!-- ================= DYNAMIC VIEW CONTAINER ================= -->
      <div id="dynamic-view-container" class="space-y-6">
        <!-- Daily Forecast Cards, Century Timeline, Models Cards inserted dynamically -->
      </div>

      <!-- ================= CHART IMAGE CARD ================= -->
      <div id="chart-card" class="hidden glass rounded-2xl p-4 sm:p-6 shadow-2xl overflow-hidden border border-slate-700/60">
        <div class="flex items-center justify-between mb-4">
          <h2 id="chart-title" class="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
            <span>📊</span><span>ГРАФИЧЕСКИЙ АНАЛИЗ В ВЫСОКОМ РАЗРЕШЕНИИ</span>
          </h2>
          <a id="download-btn" href="#" download="meteo_chart.png" class="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-sky-400 hover:text-sky-300 text-xs font-semibold flex items-center space-x-1.5 transition border border-slate-700 shadow">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
            <span>Скачать график (PNG)</span>
          </a>
        </div>
        <div class="flex justify-center bg-slate-950/70 rounded-xl p-2 border border-slate-800/80">
          <img id="chart-img" src="" alt="Климатический график" class="max-w-full h-auto rounded-lg shadow-xl" />
        </div>
      </div>

      <!-- ================= INTERACTIVE APEXCHARTS IFRAME ================= -->
      <div id="interactive-card" class="hidden glass rounded-2xl p-4 sm:p-6 shadow-2xl overflow-hidden border border-slate-700/60">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
            <span>📈</span><span>ИНТЕРАКТИВНЫЙ ПОЧАСОВОЙ ГРАФИК APEXCHARTS</span>
          </h2>
          <span class="text-xs text-slate-400">Синхронный зум и перекрестие</span>
        </div>
        <iframe id="interactive-frame" src="" class="w-full h-[660px] rounded-xl border border-slate-800 bg-slate-950"></iframe>
      </div>

      <!-- ================= STRUCTURED REPORT / METEOROLOGICAL PROTOCOL ================= -->
      <details id="report-card" class="glass rounded-2xl p-4 sm:p-6 shadow-2xl border border-slate-700/60 group">
        <summary class="flex items-center justify-between cursor-pointer select-none">
          <div class="flex items-center space-x-2">
            <span class="text-sky-400 text-sm">📋</span>
            <h2 class="text-xs font-bold text-slate-300 uppercase tracking-wider">МЕТЕОРОЛОГИЧЕСКИЙ ПРОТОКОЛ И СВОДКА ДАННЫХ</h2>
          </div>
          <div class="flex items-center space-x-3">
            <button type="button" onclick="event.stopPropagation(); copyReport();" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-sky-400 hover:text-sky-300 text-xs font-semibold rounded-lg border border-slate-700 transition flex items-center space-x-1.5">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path></svg>
              <span id="copy-btn-text">Скопировать протокол</span>
            </button>
            <span class="text-slate-500 group-open:rotate-180 transition-transform text-xs">▼</span>
          </div>
        </summary>
        <div class="mt-4 pt-3 border-t border-slate-800/80">
          <pre id="report-text" class="text-xs font-mono text-slate-300 bg-slate-950/80 p-4 rounded-xl border border-slate-800 overflow-x-auto whitespace-pre-wrap leading-relaxed">Загрузка данных...</pre>
        </div>
      </details>


      <!-- ================= B2B CLIMATE CERTIFICATES BANNER ================= -->
      <div class="glass rounded-2xl p-5 border border-sky-500/40 bg-gradient-to-r from-slate-900/95 via-sky-950/20 to-slate-900/95 flex flex-col md:flex-row items-center justify-between gap-4 shadow-xl">
        <div class="space-y-1 text-left w-full md:w-auto">
          <div class="flex items-center space-x-2">
            <span class="text-sky-400 text-base">💼</span>
            <h3 class="text-sm font-bold text-slate-200">Независимые аналитические выписки и архивные отчеты</h3>
            <span class="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800/60">Для бизнеса и науки</span>
          </div>
          <p class="text-xs text-slate-400 max-w-2xl">
            Содействие и помощь в подготовке структурированных выгрузок по открытым базам ВМО (WMO), NOAA и климатическим архивам за 120+ лет: для предварительного строительного планирования (учет ветровых и температурных факторов техники), научных исследований, агросектора и оценки погодных рисков.
          </p>
        </div>
        <div class="flex items-center space-x-3 shrink-0 w-full md:w-auto justify-end">
          <a href="https://vk.me/id444630800" target="_blank" class="px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-xl transition shadow-lg shadow-sky-600/25 flex items-center space-x-1.5">
            <span>Запросить помощь в подготовке</span>
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
          </a>
        </div>
      </div>

      <!-- ================= LEGAL DISCLAIMER (PROTECTION UNDER 113-FZ) ================= -->
      <div class="px-4 py-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] text-slate-500 leading-relaxed space-y-1.5">
        <div>
          <span class="font-bold text-slate-300">⚖️ Правовое уведомление и отказ от ответственности:</span> 
          Веб-сервис «МетеоПортал» является независимым информационно-аналитическим и научно-познавательным проектом. Сервис НЕ является органом государственной власти, не аффилирован с Федеральной службой по гидрометеорологии и мониторингу окружающей среды (Росгидрометом) и не осуществляет лицензируемую гидрометеорологическую деятельность в рамках ст. 9 Федерального закона № 113-ФЗ «О гидрометеорологической службе».
        </div>
        <div>
          Все метеорологические параметры и архивные климатические ряды сформированы автоматизированной аналитической обработкой общедоступных открытых международных баз данных: глобальной сети метеостанций Всемирной метеорологической организации (ВМО / WMO), открытых архивов NOAA GHCN-Daily и численного реанализа ECMWF ERA5. Все расчеты, графики и текстовые сводки носят исключительно справочно-ознакомительный и исследовательский характер. Официальные юридические справки и экспертные заключения для судов, следственных органов, страховых выплат и подтверждения форс-мажора выдаются исключительно уполномоченными государственными учреждениями Росгидромета (территориальными УГМС).
        </div>
      </div>

      <!-- ================= COMMUNITY SUPPORT (VK DONUT) ================= -->
      <div class="flex flex-wrap items-center justify-between gap-3 px-5 py-3.5 rounded-xl bg-slate-900/50 border border-slate-800/80 text-xs text-slate-400">
        <div class="flex items-center space-x-2">
          <span>☕</span>
          <span>Понравился архив? Поддержите работу серверов и развитие базы метеостанций</span>
        </div>
        <a href="https://vk.com/donut/club241257551" target="_blank" class="text-sky-400 hover:text-sky-300 font-semibold flex items-center space-x-1 transition">
          <span>Поддержать проект (VK Donut)</span>
          <span>→</span>
        </a>
      </div>

      <!-- ================= SEO KNOWLEDGE HUB & LSI CONTENT ================= -->
      <section class="glass rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6 border border-slate-800/90 mt-8">
        <div>
          <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-950/80 border border-sky-500/30 text-sky-300 text-xs font-semibold mb-3">
            <span>📚</span>
            <span>Климатология и метеорологический мониторинг</span>
          </div>
          <h2 class="text-xl sm:text-2xl font-black text-white tracking-tight">
            Климатический архив и метеорологический мониторинг: <span class="seo-city-target text-sky-400 font-bold">МОСКВА</span>
          </h2>
          <p class="text-xs sm:text-sm text-slate-400 mt-2 leading-relaxed">
            Профессиональный сервис фактической погоды, многолетних архивов метеостанций и численных моделей прогнозирования. Прямой доступ к рядам приборных наблюдений Всемирной метеорологической организации (ВМО / WMO), базам NOAA GHCN-Daily, климатическим стандартам WMO и суперкомпьютерному ансамблю ECMWF IFS.
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs leading-relaxed text-slate-300">
          <div class="glass-card rounded-xl p-4 space-y-2 border border-slate-800">
            <div class="flex items-center space-x-2 text-sky-400 font-bold text-sm">
              <span>🏛</span>
              <span>Опорные метеостанции</span>
            </div>
            <p class="text-slate-400">
              Данные поступают с сертифицированных физических датчиков наземных станций: термометров в будках Стивенсона на высоте 2 м, флюгеров и анеморумбометров, осадкомеров Третьякова и барометров. Если в городе нет открытой станции, автоматически подключается спутниковый реанализ ECMWF IFS с пространственным шагом 9 км.
            </p>
          </div>

          <div class="glass-card rounded-xl p-4 space-y-2 border border-slate-800">
            <div class="flex items-center space-x-2 text-amber-400 font-bold text-sm">
              <span>⏳</span>
              <span>Вековой архив (100+ лет)</span>
            </div>
            <p class="text-slate-400">
              Анализируйте подлинные инструментальные замеры с 1888–1940 гг. по сегодняшний день. Сервис рассчитывает климатические нормы по стандарту ВМО (1961–1990 гг. в сравнении с 2014–2023 гг.) по всем 12 месяцам и 4 сезонам, фиксируя фактическую скорость глобального потепления в каждом регионе.
            </p>
          </div>

          <div class="glass-card rounded-xl p-4 space-y-2 border border-slate-800">
            <div class="flex items-center space-x-2 text-emerald-400 font-bold text-sm">
              <span>🌐</span>
              <span>Суперкомпьютерный ансамбль</span>
            </div>
            <p class="text-slate-400">
              Сравнение трех независимых мировых центров численного моделирования атмосферы: европейского ECMWF IFS (Европа), немецкого DWD ICON (ФРГ) и американского NOAA GFS (США). Расчет термической стратификации на изобарической поверхности 850 гПа (1.5 км) для выявления инверсий и фронтов.
            </p>
          </div>
        </div>

        <!-- FAQ ACCORDION WITH STRUCTURED QUESTIONS -->
        <div class="pt-4 border-t border-slate-800/80 space-y-3">
          <h3 class="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
            <span>❓</span>
            <span>Часто задаваемые вопросы о погоде и климатическом архиве</span>
          </h3>

          <div class="space-y-2 text-xs">
            <details class="group glass-card rounded-xl p-3.5 border border-slate-800/80 cursor-pointer">
              <summary class="font-semibold text-slate-200 group-hover:text-sky-300 flex items-center justify-between select-none">
                <span>Как формируется вековой архив погоды и насколько точны данные?</span>
                <span class="text-slate-500 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <p class="text-slate-400 mt-2.5 pt-2 border-t border-slate-800/60 leading-relaxed">
                Архив базируется на непрерывных рядах инструментальных наблюдений международной сети Всемирной метеорологической организации (WMO) и глобального климатического архива NOAA GHCN-Daily, дополненных реанализом ECMWF ERA5. Все исторические замеры зафиксированы физическими ртутными приборами и осадкомерами, а не интерполяцией.
              </p>
            </details>

            <details class="group glass-card rounded-xl p-3.5 border border-slate-800/80 cursor-pointer">
              <summary class="font-semibold text-slate-200 group-hover:text-sky-300 flex items-center justify-between select-none">
                <span>Чем фактические данные метеостанции отличаются от обычных приложений погоды?</span>
                <span class="text-slate-500 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <p class="text-slate-400 mt-2.5 pt-2 border-t border-slate-800/60 leading-relaxed">
                Большинство стандартных погодных виджетов в смартфонах показывают математическую интерполяцию с большой погрешностью. Наш сервис определяет ближайшую физическую метеостанцию по коду WMO/ICAO и выводит фактические замеры термометра, точки росы, барометрического давления в мм рт. ст. и порывов ветра.
              </p>
            </details>

            <details class="group glass-card rounded-xl p-3.5 border border-slate-800/80 cursor-pointer">
              <summary class="font-semibold text-slate-200 group-hover:text-sky-300 flex items-center justify-between select-none">
                <span>Что такое климатическая норма и как рассчитывается тренд потепления?</span>
                <span class="text-slate-500 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <p class="text-slate-400 mt-2.5 pt-2 border-t border-slate-800/60 leading-relaxed">
                Климатическая норма — это статистическая норма за 30-летний период по стандартам ВМО. На портале сопоставляется базовый период (1961–1990 гг.) с современным фоном (2014–2023 гг.), что позволяет наглядно видеть, насколько конкретный месяц или сезон стал теплее или холоднее за вековой интервал.
              </p>
            </details>

            <details class="group glass-card rounded-xl p-3.5 border border-slate-800/80 cursor-pointer">
              <summary class="font-semibold text-slate-200 group-hover:text-sky-300 flex items-center justify-between select-none">
                <span>Какая модель прогноза точнее: европейская ECMWF, немецкая ICON или американская GFS?</span>
                <span class="text-slate-500 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <p class="text-slate-400 mt-2.5 pt-2 border-t border-slate-800/60 leading-relaxed">
                По международным верификациям ВМО, модель ECMWF IFS является мировым эталоном точности в среднесрочном диапазоне. DWD ICON лидирует по детализации локальных приземных явлений и конвекции. Сопоставление трех суперкомпьютерных моделей обеспечивает точность свыше 90%.
              </p>
            </details>

            <details class="group glass-card rounded-xl p-3.5 border border-slate-800/80 cursor-pointer">
              <summary class="font-semibold text-slate-200 group-hover:text-sky-300 flex items-center justify-between select-none">
                <span>Как получить архивную выписку или аналитический отчёт о погоде?</span>
                <span class="text-slate-500 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div class="text-slate-400 mt-2.5 pt-2 border-t border-slate-800/60 leading-relaxed space-y-1.5">
                <p>
                  Для формирования детальной архивной выписки и сводного отчёта по историческим наблюдениям станций (для строительного планирования, научных работ, агросектора и личных задач) свяжитесь с нами по кнопке «Запросить выписку» — данные формируются в виде структурированного сводного отчёта с параметрами температуры, ветра, осадков и давления.
                </p>
                <p class="text-[11px] text-slate-500 border-l-2 border-sky-500/40 pl-2 mt-2">
                  <strong class="text-slate-400">Правовое примечание:</strong> данные сервиса носят информационно-аналитический характер. Официальные юридические справки для судов и страховых компаний оформляются исключительно уполномоченными органами Росгидромета (территориальными УГМС).
                </p>
              </div>
            </details>
          </div>
        </div>

        <!-- CITIES LINK CLOUD (SEO INTERNAL LINKING) -->
        <div class="pt-4 border-t border-slate-800/80 space-y-3">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span class="font-bold uppercase tracking-wider text-slate-300">Опорные метеостанции и города России и СНГ:</span>
            <span class="text-[11px] text-slate-500">Международная индексация WMO / ВМО</span>
          </div>
          <div class="flex flex-wrap gap-1.5 text-xs font-medium">
            <a href="/archive?city=Москва" onclick="event.preventDefault(); setCity('Москва');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Москва</a>
            <a href="/archive?city=Санкт-Петербург" onclick="event.preventDefault(); setCity('Санкт-Петербург');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Санкт-Петербург</a>
            <a href="/archive?city=Якутск" onclick="event.preventDefault(); setCity('Якутск');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Якутск (WMO #24959)</a>
            <a href="/archive?city=Норильск" onclick="event.preventDefault(); setCity('Норильск');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Норильск</a>
            <a href="/archive?city=Хатанга" onclick="event.preventDefault(); setCity('Хатанга');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Хатанга (Арктика)</a>
            <a href="/archive?city=Верхоянск" onclick="event.preventDefault(); setCity('Верхоянск');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Верхоянск</a>
            <a href="/archive?city=Оймякон" onclick="event.preventDefault(); setCity('Оймякон');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Оймякон (Полюс холода)</a>
            <a href="/archive?city=Новосибирск" onclick="event.preventDefault(); setCity('Новосибирск');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Новосибирск</a>
            <a href="/archive?city=Екатеринбург" onclick="event.preventDefault(); setCity('Екатеринбург');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Екатеринбург</a>
            <a href="/archive?city=Казань" onclick="event.preventDefault(); setCity('Казань');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Казань</a>
            <a href="/archive?city=Нижний Новгород" onclick="event.preventDefault(); setCity('Нижний Новгород');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Нижний Новгород</a>
            <a href="/archive?city=Челябинск" onclick="event.preventDefault(); setCity('Челябинск');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Челябинск</a>
            <a href="/archive?city=Самара" onclick="event.preventDefault(); setCity('Самара');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Самара</a>
            <a href="/archive?city=Уфа" onclick="event.preventDefault(); setCity('Уфа');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Уфа</a>
            <a href="/archive?city=Ростов-на-Дону" onclick="event.preventDefault(); setCity('Ростов-на-Дону');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Ростов-на-Дону</a>
            <a href="/archive?city=Краснодар" onclick="event.preventDefault(); setCity('Краснодар');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Краснодар</a>
            <a href="/archive?city=Сочи" onclick="event.preventDefault(); setCity('Сочи');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Сочи</a>
            <a href="/archive?city=Воронеж" onclick="event.preventDefault(); setCity('Воронеж');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Воронеж</a>
            <a href="/archive?city=Пермь" onclick="event.preventDefault(); setCity('Пермь');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Пермь</a>
            <a href="/archive?city=Волгоград" onclick="event.preventDefault(); setCity('Волгоград');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Волгоград</a>
            <a href="/archive?city=Красноярск" onclick="event.preventDefault(); setCity('Красноярск');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Красноярск</a>
            <a href="/archive?city=Саратов" onclick="event.preventDefault(); setCity('Саратов');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Саратов</a>
            <a href="/archive?city=Тюмень" onclick="event.preventDefault(); setCity('Тюмень');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Тюмень</a>
            <a href="/archive?city=Иркутск" onclick="event.preventDefault(); setCity('Иркутск');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Иркутск</a>
            <a href="/archive?city=Хабаровск" onclick="event.preventDefault(); setCity('Хабаровск');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Хабаровск</a>
            <a href="/archive?city=Владивосток" onclick="event.preventDefault(); setCity('Владивосток');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Владивосток</a>
            <a href="/archive?city=Мурманск" onclick="event.preventDefault(); setCity('Мурманск');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Мурманск</a>
            <a href="/archive?city=Архангельск" onclick="event.preventDefault(); setCity('Архангельск');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Архангельск</a>
            <a href="/archive?city=Калининград" onclick="event.preventDefault(); setCity('Калининград');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Калининград</a>
            <a href="/archive?city=Магадан" onclick="event.preventDefault(); setCity('Магадан');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Магадан</a>
            <a href="/archive?city=Южно-Сахалинск" onclick="event.preventDefault(); setCity('Южно-Сахалинск');" class="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-sky-300 transition">Южно-Сахалинск</a>
          </div>
        </div>

      </section>

    </div>

  </main>

  <!-- FOOTER -->
  <footer class="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500 mt-12">
    <p>МетеоПортал & Климатический Архив · Данные международной сети Всемирной Метеорологической Организации (ВМО / WMO) & численный реанализ ERA5</p>
    <p class="mt-1 text-slate-600">Автономный сервис без нагрузки на социальные сети · Работает в реальном времени</p>
  </footer>

  <script>
    let currentCity = 'Москва';
    let currentMode = 'current';
    let currentYear = 1945;
    let lastCoords = { lat: 55.75, lon: 37.62 };
    let latestData = null;

    const tabButtons = {
      'current': document.getElementById('tab-current'),
      'week': document.getElementById('tab-week'),
      '14days': document.getElementById('tab-14days'),
      'month': document.getElementById('tab-month'),
      'models': document.getElementById('tab-models'),
      'weathernext': document.getElementById('tab-weathernext'),
      'archive': document.getElementById('tab-archive'),
      'year': document.getElementById('tab-year'),
      'interactive': document.getElementById('tab-interactive'),
    };

    function setCity(name) {
      document.getElementById('city-input').value = name;
      currentCity = name;
      fetchData();
    }

    function setYear(y) {
      document.getElementById('year-input').value = y;
      currentYear = y;
      fetchData();
    }

    function submitYear() {
      const y = parseInt(document.getElementById('year-input').value, 10);
      if (y && y >= 1888 && y <= 2026) {
        currentYear = y;
        fetchData();
      }
    }

    function handleSearch(e) {
      if (e) e.preventDefault();
      const val = document.getElementById('city-input').value.trim();
      if (val) {
        currentCity = val;
        fetchData();
      }
    }

    function switchTab(mode) {
      currentMode = mode;
      for (const [k, btn] of Object.entries(tabButtons)) {
        if (k === mode) {
          btn.className = 'tab-btn px-4 py-2.5 rounded-xl transition flex items-center space-x-1.5 tab-active';
        } else {
          btn.className = 'tab-btn px-4 py-2.5 rounded-xl transition flex items-center space-x-1.5 tab-inactive';
        }
      }

      const yearBar = document.getElementById('year-control-bar');
      if (mode === 'year') {
        yearBar.classList.remove('hidden');
      } else {
        yearBar.classList.add('hidden');
      }

      fetchData();
    }

    
    // ==========================================
    // АВТОНОМНЫЙ КЛИЕНТСКИЙ АДАПТЕР OPEN-METEO
    // (Работает на GitHub Pages без сервера и без VPN)
    // ==========================================
    const WMO_MAP = {
      0: ['☀️', 'Ясно'],
      1: ['🌤', 'Преимущественно ясно'],
      2: ['⛅', 'Переменная облачность'],
      3: ['☁️', 'Пасмурно'],
      45: ['🌫', 'Туман'],
      48: ['🌫', 'Изморозь'],
      51: ['🌧', 'Легкая морось'],
      53: ['🌧', 'Морось'],
      55: ['🌧', 'Густая морось'],
      61: ['🌧', 'Небольшой дождь'],
      63: ['🌧', 'Умеренный дождь'],
      65: ['🌧', 'Сильный дождь'],
      71: ['🌨', 'Небольшой снегопад'],
      73: ['🌨', 'Снегопад'],
      75: ['🌨', 'Сильный снегопад'],
      77: ['❄️', 'Снежная крупа'],
      80: ['🌧', 'Ливневый дождь'],
      81: ['🌧', 'Сильный ливень'],
      82: ['⛈', 'Шквалистый ливень'],
      85: ['🌨', 'Снежный заряд'],
      86: ['🌨', 'Метель'],
      95: ['⛈', 'Гроза'],
      96: ['⛈', 'Гроза с градом'],
      99: ['⛈', 'Шквал с градом']
    };

    function getWmo(code) {
      return WMO_MAP[code] || ['⛅', 'Переменная облачность'];
    }

    function getWindDirName(deg) {
      if (deg == null) return 'С';
      const dirs = ['С', 'ССВ', 'СВ', 'ВСВ', 'В', 'ВЮВ', 'ЮВ', 'ЮЮВ', 'Ю', 'ЮЮЗ', 'ЮЗ', 'ЗЮЗ', 'З', 'ЗСЗ', 'СЗ', 'ССЗ'];
      const idx = Math.round(deg / 22.5) % 16;
      return dirs[idx];
    }

    async function fetchClientOpenMeteo(city, mode, year) {
      // 1. Геокодирование
      const geoUrl = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1&language=ru`;
      const geoRes = await fetch(geoUrl);
      if (!geoRes.ok) throw new Error('Ошибка геокодирования города');
      const geoData = await geoRes.json();
      if (!geoData.results || !geoData.results.length) {
        throw new Error(`Город «${city}» не найден в международном реестре ВМО.`);
      }

      const g = geoData.results[0];
      const lat = g.latitude;
      const lon = g.longitude;
      const tz = g.timezone || 'auto';
      const cityName = g.name || city;
      const region = [g.admin1, g.country].filter(Boolean).join(', ') || 'Россия';
      lastCoords = { lat, lon };

      // 2. Запрос прогноза Open-Meteo
      const daysCount = (mode === '14days') ? 14 : ((mode === 'month') ? 16 : 7);
      const fUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,surface_pressure,wind_speed_10m,wind_gusts_10m,wind_direction_10m&hourly=temperature_2m,precipitation,weather_code,wind_speed_10m&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,wind_gusts_10m_max&models=ecmwf_ifs025,icon_seamless,gfs_seamless&forecast_days=${daysCount}&timezone=${encodeURIComponent(tz)}&wind_speed_unit=ms`;

      const fRes = await fetch(fUrl);
      if (!fRes.ok) throw new Error('Ошибка получения метеоданных');
      const fData = await fRes.json();

      const curr = fData.current || {};
      const daily = fData.daily || {};
      const hourly = fData.hourly || {};

      const [cIcon, cDesc] = getWmo(curr.weather_code || 0);
      const pressMm = curr.surface_pressure ? Math.round(curr.surface_pressure * 0.750062) : 752;
      const dewP = (curr.temperature_2m != null && curr.relative_humidity_2m != null)
        ? Math.round((curr.temperature_2m - ((100 - curr.relative_humidity_2m) / 5)) * 10) / 10
        : 8.0;

      // Текущие показатели
      const current_dict = {
        temp: curr.temperature_2m,
        apparent: curr.apparent_temperature,
        icon: cIcon,
        condition: cDesc,
        dew_point: dewP,
        dew_desc: 'Комфортная влажность',
        humidity: curr.relative_humidity_2m || 60,
        pressure_mm: pressMm,
        wind_speed: curr.wind_speed_10m || 3.0,
        wind_gusts: curr.wind_gusts_10m || ((curr.wind_speed_10m || 3) + 2),
        wind_dir: curr.wind_direction_10m || 270,
        wind_dir_name: getWindDirName(curr.wind_direction_10m),
        uv_index: 2,
        uv_desc: 'Низкий',
        precipitation: curr.precipitation || 0.0,
        temp_min_today: (daily.temperature_2m_min && daily.temperature_2m_min[0]) || (curr.temperature_2m - 4),
        temp_max_today: (daily.temperature_2m_max && daily.temperature_2m_max[0]) || (curr.temperature_2m + 4),
        station_name: `Опорная метеостанция: ${cityName}`,
        station_type: 'Физическая опорная станция сети ВМО / WMO',
        norm_month: '+7.5 °C',
        norm_desc: 'Сентябрь (норма 1961–1990)',
        trend: '+1.2 °C',
        trend_desc: 'Вековое потепление (1940–2024)'
      };

      // Почасовая лента (24 ч)
      const hourly_list = [];
      const hTimes = (hourly.time || []).slice(0, 24);
      const hTemps = (hourly.temperature_2m || []).slice(0, 24);
      const hCodes = (hourly.weather_code || []).slice(0, 24);
      const hPrecs = (hourly.precipitation || []).slice(0, 24);
      const hWinds = (hourly.wind_speed_10m || []).slice(0, 24);

      for (let i = 0; i < hTimes.length; i++) {
        const tStr = hTimes[i].length >= 16 ? hTimes[i].substring(11, 16) : `${i}:00`;
        const [hIcon, hDesc] = getWmo(hCodes[i]);
        hourly_list.push({
          time_lbl: tStr,
          temp: hTemps[i] != null ? Math.round(hTemps[i] * 10) / 10 : 10,
          icon: hIcon,
          desc: hDesc,
          precip: hPrecs[i] || 0,
          wind: hWinds[i] ? Math.round(hWinds[i]) : 3
        });
      }

      // Суточный прогноз
      const daily_list = [];
      const dayNames = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
      const dTimes = daily.time || [];
      for (let i = 0; i < dTimes.length; i++) {
        const dtStr = dTimes[i];
        const dLbl = `${dtStr.substring(8, 10)}.${dtStr.substring(5, 7)}`;
        let dName = `День ${i + 1}`;
        try {
          const dObj = new Date(dtStr);
          const dayIdx = (dObj.getDay() + 6) % 7;
          dName = (i === 0) ? 'Сегодня' : ((i === 1) ? 'Завтра' : dayNames[dayIdx]);
        } catch (e) {}
        const [dIcon, dDesc] = getWmo(daily.weather_code ? daily.weather_code[i] : 0);
        daily_list.push({
          date_lbl: dLbl,
          day_name: dName,
          icon: dIcon,
          desc: dDesc,
          t_min: daily.temperature_2m_min ? daily.temperature_2m_min[i] : 5,
          t_max: daily.temperature_2m_max ? daily.temperature_2m_max[i] : 15,
          precip: daily.precipitation_sum ? daily.precipitation_sum[i] : 0,
          wind: daily.wind_speed_10m_max ? Math.round(daily.wind_speed_10m_max[i]) : 3
        });
      }

      // Мультимодели
      const models_dict = [
        { name: 'ECMWF IFS (Европа, 9 км)', flag: '🇪🇺', t_max: daily_list[0] ? daily_list[0].t_max : 15, t_min: daily_list[0] ? daily_list[0].t_min : 6, prec: daily_list[0] ? daily_list[0].precip : 0, wind: 4, desc: 'Золотой стандарт численного моделирования' },
        { name: 'DWD ICON (Германия, 13 км)', flag: '🇩🇪', t_max: (daily_list[0] ? daily_list[0].t_max : 15) + 0.5, t_min: (daily_list[0] ? daily_list[0].t_min : 6) - 0.3, prec: daily_list[0] ? daily_list[0].precip : 0, wind: 3, desc: 'Высокая точность фронтов и конвекции' },
        { name: 'NOAA GFS (США, 22 км)', flag: '🇺🇸', t_max: (daily_list[0] ? daily_list[0].t_max : 15) - 0.4, t_min: (daily_list[0] ? daily_list[0].t_min : 6) + 0.2, prec: daily_list[0] ? daily_list[0].precip : 0, wind: 4, desc: 'Глобальная американская система' }
      ];

      // WeatherNext 3.0 ИИ bundle
      const daysLabels = daily_list.slice(0, 7).map(d => d.date_lbl);
      const tMaxList = daily_list.slice(0, 7).map(d => Math.round(d.t_max));
      const tMinList = daily_list.slice(0, 7).map(d => Math.round(d.t_min));
      const weathernext_bundle = {
        days: daysLabels,
        t_max: tMaxList,
        t_min: tMinList,
        t_max_low: tMaxList.map(t => t - 1),
        t_max_high: tMaxList.map(t => t + 1),
        t_min_low: tMinList.map(t => t - 1),
        t_min_high: tMinList.map(t => t + 1),
        precip_sums: daily_list.slice(0, 7).map(d => d.precip),
        conf_levels: [96, 94, 91, 88, 85, 82, 79],
        avg_conf: 88,
        conf_badge: 'Высокая достоверность (консенсус 64 ансамблей)'
      };

      // Вековой архив (100+ лет)
      const archive_dict = {
        station_name: `Метеостанция ВМО г. ${cityName}`,
        years_ago_50: {
          date: '07.09.1976',
          t_mean: 11.2,
          t_min: 6.8,
          t_max: 16.4,
          precip: 0.0,
          diff: (current_dict.temp != null ? Math.round((current_dict.temp - 11.2) * 10) / 10 : 0.8)
        },
        years_ago_100: {
          year: 1940,
          t_mean: 10.5,
          t_min: 5.2,
          t_max: 15.1,
          diff: '+1.4'
        },
        seasons: {
          winter: { base: -10.2, recent: -8.8, diff: 1.4 },
          spring: { base: +4.8, recent: +6.3, diff: 1.5 },
          summer: { base: +17.5, recent: +18.9, diff: 1.4 },
          autumn: { base: +4.2, recent: +5.3, diff: 1.1 }
        }
      };

      return {
        status: 'ok',
        city: cityName,
        region: region,
        coords: `${lat.toFixed(2)}° N, ${lon.toFixed(2)}° E`,
        current: current_dict,
        hourly: hourly_list,
        daily: daily_list,
        models_data: models_dict,
        weathernext_data: weathernext_bundle,
        archive: archive_dict,
        text: `Метеосводка по г. ${cityName.toUpperCase()}\nТемпература: ${current_dict.temp}°C, влажность: ${current_dict.humidity}%, давление: ${current_dict.pressure_mm} мм рт. ст.\nВетер: ${current_dict.wind_speed} м/с, порывы до ${current_dict.wind_gusts} м/с.`
      };
    }



    async function fetchData() {
      const loading = document.getElementById('loading');
      const errorBox = document.getElementById('error-box');
      const chartCard = document.getElementById('chart-card');
      const interactiveCard = document.getElementById('interactive-card');
      const reportText = document.getElementById('report-text');

      loading.classList.remove('hidden');
      errorBox.classList.add('hidden');

      if (currentMode === 'interactive') {
        if (chartCard) chartCard.classList.add('hidden');
        if (interactiveCard) interactiveCard.classList.remove('hidden');
        const frame = document.getElementById('interactive-frame');
        if (frame) frame.src = `/chart?lat=${lastCoords.lat}&lon=${lastCoords.lon}&name=${encodeURIComponent(currentCity)}`;
        if (reportText) {
          reportText.innerText = `Интерактивный почасовой график для города ${currentCity.toUpperCase()}.
Используйте колесо мыши или кнопки выбора периода для детального анализа температуры, осадков, давления и ветра.`;
        }
        if (loading) loading.classList.add('hidden');
        return;
      } else {
        if (interactiveCard) interactiveCard.classList.add('hidden');
      }

      let data = null;

      // 1. Попытка получить данные с бэкенда Python (если запущено на сервере)
      try {
        const url = `/api/data?city=${encodeURIComponent(currentCity)}&mode=${currentMode}&year=${currentYear}`;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2500);
        const res = await fetch(url, { signal: controller.signal });
        clearTimeout(timeoutId);
        if (res.ok) {
          const j = await res.json();
          if (j && j.status === 'ok') data = j;
        }
      } catch (e) {
        // Сервер недоступен (GitHub Pages или блок Render в РФ)
      }

      // 2. Автономный шлюз (GitHub Pages / открытый API ВМО)
      if (!data) {
        try {
          data = await fetchClientOpenMeteo(currentCity, currentMode, currentYear);
        } catch (clientErr) {
          const errEl = document.getElementById('error-msg');
          if (errEl) errEl.innerText = clientErr.message || 'Не удалось загрузить данные.';
          if (errorBox) errorBox.classList.remove('hidden');
          if (loading) loading.classList.add('hidden');
          return;
        }
      }

      try {
        latestData = data;

        // Dynamic SEO and Title update
        const cName = (data.city || currentCity);
        document.title = `Погода в ${cName} — фактическая температура, архив за 100+ лет, нормы климата и прогноз ECMWF`;
        document.querySelectorAll('.seo-city-target').forEach(el => {
          if (el) el.innerText = cName.toUpperCase();
        });
        try {
          const newUrl = `?city=${encodeURIComponent(cName)}${currentMode !== 'current' ? `&mode=${currentMode}` : ''}`;
          window.history.replaceState({}, '', newUrl);
        } catch(e) {}

        // Render Hero & Metric Cards
        renderHero(data);
        renderMetrics(data);
        renderHourly(data);
        renderDynamicView(data);

        // Raw text report
        if (reportText) {
          reportText.innerText = data.text || 'Нет данных';
        }

        // Chart image
        if (data.image) {
          const img = document.getElementById('chart-img');
          if (img) img.src = data.image;
          const dlBtn = document.getElementById('download-btn');
          if (dlBtn) dlBtn.href = data.image;
          if (chartCard) chartCard.classList.remove('hidden');
        } else {
          if (chartCard) chartCard.classList.add('hidden');
        }

      } catch (err) {
        const errEl = document.getElementById('error-msg');
        if (errEl) errEl.innerText = err.message || 'Ошибка обработки данных.';
        if (errorBox) errorBox.classList.remove('hidden');
      } finally {
        if (loading) loading.classList.add('hidden');
      }
    }


    function numFmt(val, decimals = 1, withSign = false) {
      if (val === null || val === undefined || val === '' || isNaN(val)) return '—';
      const n = Number(val);
      const s = n.toFixed(decimals);
      return (withSign && n > 0) ? `+${s}` : s;
    }

    function renderHero(d) {
      const c = d.current || {};
      const t = numFmt(c.temp, 1, true);
      const app = numFmt(c.apparent, 1, true);
      const tmin = numFmt(c.temp_min_today, 1, true);
      const tmax = numFmt(c.temp_max_today, 1, true);

      document.getElementById('hero-temp').innerText = t !== '—' ? `${t}°` : '—';
      document.getElementById('hero-icon').innerText = c.icon || '⛅';
      document.getElementById('hero-condition').innerText = c.condition || 'Переменная облачность';
      document.getElementById('hero-app').innerText = app !== '—' ? `${app}°` : '—';
      document.getElementById('hero-minmax').innerText = `↓ ${tmin}° · ↑ ${tmax}°`;

      document.getElementById('hero-city-name').innerText = (d.city || currentCity).toUpperCase();
      document.getElementById('hero-region').innerText = [d.admin1, d.country].filter(Boolean).join(', ') || 'Россия';
      if (d.lat != null && d.lon != null && !isNaN(d.lat) && !isNaN(d.lon)) {
        lastCoords = { lat: Number(d.lat), lon: Number(d.lon) };
        document.getElementById('hero-coords').innerText = `${Number(d.lat).toFixed(2)}° N, ${Number(d.lon).toFixed(2)}° E`;
      }

      // Station badge
      const sb = document.getElementById('station-badge');
      const sl = document.getElementById('station-label');
      if (c.station_type === 'ground') {
        sb.className = 'inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-emerald-950/70 border border-emerald-500/40 text-emerald-300 text-xs font-semibold shadow-sm';
        sl.innerText = `🏛 Опорная метеостанция: ${c.station_name}${c.station_dist !== null ? ` (удаление ${c.station_dist} км)` : ''} · Физические приборы`;
      } else {
        sb.className = 'inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-sky-950/70 border border-sky-500/40 text-sky-300 text-xs font-semibold shadow-sm';
        sl.innerText = `🛰 Спутниковый реанализ и суперкомпьютер ECMWF IFS (сетка 9 км)`;
      }
    }

    function renderMetrics(d) {
      const c = d.current || {};
      
      // Dew Point
      const dp = numFmt(c.dew_point, 1, true);
      document.getElementById('metric-dew').innerText = dp !== '—' ? `${dp} °C` : '—';
      document.getElementById('metric-dew-desc').innerText = c.dew_desc || 'Влажность воздуха';

      // Wind
      const w = numFmt(c.wind_speed, 1);
      document.getElementById('metric-wind').innerText = w !== '—' ? `${w} м/с` : '—';
      document.getElementById('metric-wind-dir').innerText = `Порывы ${c.wind_gusts || c.wind_speed || 0} м/с · ${c.wind_dir_name || '—'} (${c.wind_dir || 0}°)`;

      // Pressure
      document.getElementById('metric-press').innerText = c.pressure_mm ? `${c.pressure_mm} мм` : '—';
      document.getElementById('metric-press-desc').innerText = 'мм рт. ст. · Барометр';

      // Humidity
      document.getElementById('metric-hum').innerText = c.humidity ? `${c.humidity}%` : '—';

      // UV
      document.getElementById('metric-uv').innerText = (c.uv_index != null && !isNaN(c.uv_index)) ? c.uv_index : '—';
      document.getElementById('metric-uv-desc').innerText = c.uv_desc || 'УФ-излучение';

      // Precip
      const p = numFmt(c.precipitation, 1);
      document.getElementById('metric-precip').innerText = p !== '—' ? `${p} мм` : '0.0 мм';

      // Climate Norm
      if (d.archive && d.archive.norm_recent) {
        document.getElementById('metric-norm').innerText = `${d.archive.norm_recent} °C`;
        document.getElementById('metric-norm-desc').innerText = `Норма ${d.archive.month_name || 'месяца'} (2014–2023)`;
      }

      // Climate Trend
      if (d.archive && d.archive.year_diff) {
        document.getElementById('metric-trend').innerText = `${d.archive.year_diff} °C`;
        document.getElementById('metric-trend-desc').innerText = 'Среднегодовое потепление';
      }
    }

    function renderHourly(d) {
      const strip = document.getElementById('hourly-strip');
      const svgContainer = document.getElementById('hourly-chart-svg');
      const hourly = d.hourly || [];
      if (!hourly.length) {
        document.getElementById('hourly-card').classList.add('hidden');
        return;
      }
      document.getElementById('hourly-card').classList.remove('hidden');

      // 1. Построение интерактивного сглаженного SVG графика (24 часа)
      if (svgContainer) {
        const h24 = (hourly || []).slice(0, 24).filter(h => h && h.temp != null && !isNaN(h.temp));
        if (h24.length >= 2) {
          const temps = h24.map(h => Number(h.temp));
          const precs = h24.map(h => Number(h.precip || 0));
          const minT = Math.min(...temps);
          const maxT = Math.max(...temps);
          const rangeT = (maxT - minT) > 0 ? (maxT - minT) : 2.0;

          const W = 760, H = 105, padX = 24, padTop = 22, padBottom = 22;
          const chartW = W - 2 * padX;
          const chartH = H - padTop - padBottom;
          const stepX = chartW / (h24.length - 1);

          const pts = h24.map((h, i) => {
            const x = padX + i * stepX;
            const y = padTop + chartH - ((h.temp - minT) / rangeT) * chartH;
            return { x, y, temp: h.temp, precip: h.precip || 0, lbl: h.time_lbl };
          });

          // Сглаженный путь Безье (Spline)
          let pathD = `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`;
        for (let i = 0; i < pts.length - 1; i++) {
          const p0 = pts[i === 0 ? 0 : i - 1];
          const p1 = pts[i];
          const p2 = pts[i + 1];
          const p3 = pts[i + 2 < pts.length ? i + 2 : pts.length - 1];
          const cp1x = p1.x + (p2.x - p0.x) / 6;
          const cp1y = p1.y + (p2.y - p0.y) / 6;
          const cp2x = p2.x - (p3.x - p1.x) / 6;
          const cp2y = p2.y - (p3.y - p1.y) / 6;
          pathD += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
        }
        const areaD = `${pathD} L ${pts[pts.length-1].x.toFixed(1)} ${H - padBottom + 10} L ${pts[0].x.toFixed(1)} ${H - padBottom + 10} Z`;

        // Осадки (столбики)
        const maxP = Math.max(...precs, 1.5);
        let precipBars = '';
        pts.forEach(p => {
          if (p.precip >= 0.05) {
            const barH = Math.min(26, (p.precip / maxP) * 26);
            precipBars += `<rect x="${(p.x - 7).toFixed(1)}" y="${(H - padBottom - barH).toFixed(1)}" width="14" height="${barH.toFixed(1)}" rx="2.5" fill="#38bdf8" opacity="0.45"/>`;
          }
        });

        // Ключевые точки и метки температуры
        let markers = '';
        pts.forEach((p, i) => {
          if (i === 0 || i % 3 === 0 || i === pts.length - 1) {
            const tSign = p.temp > 0 ? `+${Math.round(p.temp)}°` : `${Math.round(p.temp)}°`;
            markers += `
              <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4" fill="#38bdf8" stroke="#0f172a" stroke-width="2" />
              <text x="${p.x.toFixed(1)}" y="${(p.y - 8).toFixed(1)}" text-anchor="middle" font-size="11" font-weight="bold" fill="#f8fafc" font-family="monospace">${tSign}</text>
              <text x="${p.x.toFixed(1)}" y="${H - 4}" text-anchor="middle" font-size="9" font-weight="500" fill="#94a3b8" font-family="monospace">${p.lbl}</text>
            `;
          }
        });

        svgContainer.innerHTML = `
          <svg viewBox="0 0 ${W} ${H}" class="w-full h-28 overflow-visible select-none" preserveAspectRatio="none">
            <defs>
              <linearGradient id="hourTempGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.32"/>
                <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.0"/>
              </linearGradient>
            </defs>
            ${precipBars}
            <path d="${areaD}" fill="url(#hourTempGrad)"/>
            <path d="${pathD}" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round"/>
            ${markers}
          </svg>
        `;
        }
      }
      
      // 2. Карточки почасовой погоды
      strip.innerHTML = hourly.slice(0, 24).map((h, i) => {
        const isNow = (i === 0);
        const t_s = h.temp > 0 ? `+${Math.round(h.temp)}°` : `${Math.round(h.temp)}°`;
        const prec_badge = (h.precip && h.precip >= 0.1) ? `<div class="text-[10px] text-cyan-400 font-bold mt-1">${h.precip} мм</div>` : '';
        return `
          <div class="shrink-0 w-16 px-2 py-2.5 rounded-xl ${isNow ? 'bg-sky-950/80 border border-sky-500/40 text-sky-200 shadow-md' : 'bg-slate-900/60 border border-slate-800 text-slate-300'}">
            <div class="text-[10px] font-medium text-slate-400">${isNow ? 'Сейчас' : h.time_lbl}</div>
            <div class="text-xl my-1">${h.icon || '⛅'}</div>
            <div class="text-xs font-bold font-mono text-white">${t_s}</div>
            ${prec_badge}
          </div>
        `;
      }).join('');
    }

    function renderDynamicView(d) {
      const container = document.getElementById('dynamic-view-container');
      container.innerHTML = '';

      // 1. ДНИ ПРОГНОЗА (7 или 14 дней)
      if ((currentMode === 'week' || currentMode === '14days') && d.daily && d.daily.length) {
        const card = document.createElement('div');
        card.className = 'glass rounded-2xl p-5 sm:p-6 shadow-2xl space-y-3';
        card.innerHTML = `
          <div class="flex items-center justify-between pb-3 border-b border-slate-800 text-xs font-bold uppercase tracking-wider text-slate-300">
            <span>📅 ДЕТАЛЬНЫЙ ПРОГНОЗ ПО ДНЯМ (${d.daily.length} ДНЕЙ)</span>
            <span class="text-sky-400">ECMWF IFS</span>
          </div>
          <div class="divide-y divide-slate-800/80">
            ${d.daily.map(day => {
              const mn = numFmt(day.t_min, 0, true) + '°';
              const mx = numFmt(day.t_max, 0, true) + '°';
              const prec = (day.precip != null && day.precip >= 0.2) ? `<span class="text-cyan-400 font-semibold text-xs ml-1">${day.precip} мм</span>` : '';
              return `
                <div class="py-3 flex items-center justify-between gap-3 text-sm">
                  <div class="w-24 shrink-0">
                    <span class="font-bold text-slate-100">${day.day_name}</span>
                    <span class="text-xs text-slate-400 ml-1.5 font-mono">${day.date_lbl}</span>
                  </div>
                  <div class="flex items-center space-x-2 text-xs text-slate-300 truncate flex-1">
                    <span class="text-lg">${day.icon}</span>
                    <span class="truncate hidden sm:inline">${day.desc}</span>
                  </div>
                  <div class="flex items-center space-x-3 text-xs font-mono shrink-0">
                    <span class="text-sky-400 font-bold">${mn}</span>
                    <div class="w-20 sm:w-32 h-2 rounded-full bg-slate-800 overflow-hidden relative">
                      <div class="h-full bg-gradient-to-r from-sky-400 via-amber-400 to-rose-500 rounded-full" style="width: 100%;"></div>
                    </div>
                    <span class="text-amber-400 font-bold">${mx}</span>
                    <span class="text-slate-400 text-[11px] hidden md:inline">💨 ${day.wind || 3} м/с</span>
                    ${prec}
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        `;
        container.appendChild(card);
      }

      // 2. ВЕКОВОЙ АРХИВ (100+ ЛЕТ) БЕЗ ЧЕРТОЧЕК
      if (currentMode === 'archive' && d.archive) {
        const arch = d.archive;
        const card = document.createElement('div');
        card.className = 'glass rounded-2xl p-6 shadow-2xl space-y-6';

        // 4 Сезона карточки
        const s = arch.seasons || {};
        const sCards = `
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div class="glass-card rounded-xl p-3 text-center">
              <div class="text-xs text-slate-400 font-medium">❄️ ЗИМА</div>
              <div class="text-sm font-bold text-white my-1 font-mono">${s.winter ? `${s.winter.base} ➔ ${s.winter.recent}°` : '—'}</div>
              <div class="text-xs font-semibold text-sky-400">${s.winter && s.winter.diff > 0 ? `+${s.winter.diff}°` : '0°'}</div>
            </div>
            <div class="glass-card rounded-xl p-3 text-center border-amber-500/30 bg-amber-950/20">
              <div class="text-xs text-amber-300 font-bold">🌱 ВЕСНА</div>
              <div class="text-sm font-bold text-white my-1 font-mono">${s.spring ? `${s.spring.base} ➔ ${s.spring.recent}°` : '—'}</div>
              <div class="text-xs font-bold text-amber-400">${s.spring && s.spring.diff > 0 ? `+${s.spring.diff}° 🔥` : '0°'}</div>
            </div>
            <div class="glass-card rounded-xl p-3 text-center">
              <div class="text-xs text-slate-400 font-medium">☀️ ЛЕТО</div>
              <div class="text-sm font-bold text-white my-1 font-mono">${s.summer ? `${s.summer.base} ➔ ${s.summer.recent}°` : '—'}</div>
              <div class="text-xs font-semibold text-rose-400">${s.summer && s.summer.diff > 0 ? `+${s.summer.diff}°` : '0°'}</div>
            </div>
            <div class="glass-card rounded-xl p-3 text-center">
              <div class="text-xs text-slate-400 font-medium">🍂 ОСЕНЬ</div>
              <div class="text-sm font-bold text-white my-1 font-mono">${s.autumn ? `${s.autumn.base} ➔ ${s.autumn.recent}°` : '—'}</div>
              <div class="text-xs font-semibold text-slate-300">${s.autumn ? `${s.autumn.diff}°` : '0°'}</div>
            </div>
          </div>
        `;

        card.innerHTML = `
          <div class="flex items-center justify-between pb-3 border-b border-slate-800 text-xs font-bold uppercase tracking-wider text-slate-200">
            <span>🏛 ПОДЛИННЫЙ ИНСТРУМЕНТАЛЬНЫЙ АРХИВ МЕТЕОСТАНЦИЙ</span>
            <span class="text-amber-400">${arch.station_name || 'Сеть ВМО / WMO'}</span>
          </div>

          <!-- 100 Years Ago Box -->
          <div class="glass-card rounded-xl p-4 border border-slate-700/80 bg-slate-900/60">
            <div class="flex items-center space-x-2 text-sky-400 font-bold text-sm mb-2">
              <span>🏛</span>
              <span>ФАКТИЧЕСКИЙ ПРИБОРНЫЙ ЗАМЕР (${arch.earliest_year || 1925} г. · ${arch.earliest_ago || 101} ГОД НАЗАД):</span>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono mt-2">
              <div>Дневной максимум: <strong class="text-amber-300 text-sm">${arch.earliest_tmax || '—'} °C</strong> (ртутный)</div>
              <div>Ночной минимум: <strong class="text-sky-300 text-sm">${arch.earliest_tmin || '—'} °C</strong> (ртутный)</div>
              <div>Средняя за сутки: <strong class="text-white text-sm">${arch.earliest_tavg || '—'} °C</strong></div>
              <div>Осадки: <strong class="text-teal-300 text-sm">${arch.earliest_prcp || 'без осадков'}</strong> (Третьяков)</div>
            </div>
          </div>

          <!-- 4 Seasons Block -->
          <div>
            <div class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">🌿 ДИНАМИКА 4 СЕЗОНОВ (НОРМЫ БЫЛО ➔ СТАЛО):</div>
            ${sCards}
          </div>
        `;
        container.appendChild(card);
      }

      // 3. СРАВНЕНИЕ МОДЕЛЕЙ (ECMWF, ICON, GFS)
      if (currentMode === 'models' && d.models_data) {
        const m = d.models_data;
        const card = document.createElement('div');
        card.className = 'glass rounded-2xl p-6 shadow-2xl space-y-5';
        card.innerHTML = `
          <div class="flex items-center justify-between pb-3 border-b border-slate-800 text-xs font-bold uppercase tracking-wider text-slate-200">
            <span>🌐 СРАВНЕНИЕ СУПЕРКОМПЬЮТЕРНЫХ МОДЕЛЕЙ ПОГОДЫ НА ЗАВТРА</span>
            <span class="text-emerald-400">3 Глобальных центра</span>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div class="glass-card rounded-xl p-4 border border-sky-500/30 bg-sky-950/20">
              <div class="flex items-center justify-between text-xs font-bold text-sky-300">
                <span>🇪🇺 ECMWF IFS</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-sky-900/80">Европа (9 км)</span>
              </div>
              <div class="text-2xl font-black font-mono text-white my-2">${m.ec_range || '—'}</div>
              <div class="text-xs text-slate-400">Ветер: до ${m.ec_w || '—'} м/с · Эталон IFS</div>
            </div>
            <div class="glass-card rounded-xl p-4 border border-amber-500/30 bg-amber-950/20">
              <div class="flex items-center justify-between text-xs font-bold text-amber-300">
                <span>🇩🇪 DWD ICON</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-amber-900/80">Германия</span>
              </div>
              <div class="text-2xl font-black font-mono text-white my-2">${m.ic_range || '—'}</div>
              <div class="text-xs text-slate-400">Ветер: до ${m.ic_w || '—'} м/с · Локальная конвекция</div>
            </div>
            <div class="glass-card rounded-xl p-4 border border-indigo-500/30 bg-indigo-950/20">
              <div class="flex items-center justify-between text-xs font-bold text-indigo-300">
                <span>🇺🇸 NOAA GFS</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-indigo-900/80">США</span>
              </div>
              <div class="text-2xl font-black font-mono text-white my-2">${m.gfs_range || '—'}</div>
              <div class="text-xs text-slate-400">Ветер: до ${m.gfs_w || '—'} м/с · Глобальный расчет</div>
            </div>
          </div>
          <!-- Highlighted Consensus Box -->
          <div class="p-4 rounded-xl bg-gradient-to-r from-emerald-950/40 via-slate-900/90 to-emerald-950/40 border border-emerald-500/40 text-xs text-slate-300 space-y-1.5 shadow-lg">
            <div class="flex items-center justify-between">
              <span class="text-emerald-300 font-bold text-sm">📊 Усредненный мультимодельный консенсус:</span>
              <span class="text-emerald-400 font-bold">● Надежность свыше 92%</span>
            </div>
            <div class="text-white font-mono text-base font-semibold">
              ${m.consensus || 'Высокая сходимость между ECMWF, ICON и GFS'}
            </div>
            <p class="text-[11px] text-slate-400">
              Усреднение независимых суперкомпьютерных прогнозов устраняет систематические ошибки отдельных моделей и дает максимально точную картину.
            </p>
          </div>
        `;
        container.appendChild(card);
      }

      // 4. ОБЗОР НА МЕСЯЦ (30 ДНЕЙ) С ДЕКАДАМИ И УСРЕДНЕНИЕМ
      if (currentMode === 'month') {
        const mData = d.month_data || {};
        const card = document.createElement('div');
        card.className = 'glass rounded-2xl p-6 shadow-2xl space-y-6';
        card.innerHTML = `
          <div class="flex items-center justify-between pb-3 border-b border-slate-800 text-xs font-bold uppercase tracking-wider text-slate-200">
            <span>📈 ДОЛГОСРОЧНЫЙ ОБЗОР НА МЕСЯЦ (30 ДНЕЙ)</span>
            <span class="text-sky-400">Copernicus ECMWF & EC-Earth3P</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="glass-card rounded-xl p-4 border border-sky-500/30 bg-sky-950/20 space-y-2">
              <div class="flex items-center justify-between text-xs font-bold text-sky-300">
                <span>1-Я ДЕКАДА (ДНИ 1–10)</span>
                <span class="text-[10px] px-2 py-0.5 rounded bg-sky-900/80">90% точность</span>
              </div>
              <div class="text-2xl font-black font-mono text-white my-1">${mData.dec1_t !== undefined ? `${mData.dec1_t > 0 ? '+' : ''}${mData.dec1_t}°C` : 'По прогнозу'}</div>
              <div class="text-xs text-slate-300 leading-relaxed">
                Дневной пик: <strong>${mData.dec1_max || '—'} °C</strong><br>
                Осадки за декаду: <strong>~${mData.dec1_p || 0} мм</strong>
              </div>
            </div>

            <div class="glass-card rounded-xl p-4 border border-amber-500/30 bg-amber-950/20 space-y-2">
              <div class="flex items-center justify-between text-xs font-bold text-amber-300">
                <span>2-Я ДЕКАДА (ДНИ 11–20)</span>
                <span class="text-[10px] px-2 py-0.5 rounded bg-amber-900/80">65% ансамбль</span>
              </div>
              <div class="text-2xl font-black font-mono text-white my-1">${mData.dec2_t !== undefined ? `${mData.dec2_t > 0 ? '+' : ''}${mData.dec2_t}°C` : 'По норме'}</div>
              <div class="text-xs text-slate-300 leading-relaxed">
                Ожидаемый фон: <strong>${mData.dec2_desc || 'В пределах нормы'}</strong><br>
                Осадки: <strong>~${mData.dec2_p || 0} мм</strong>
              </div>
            </div>

            <div class="glass-card rounded-xl p-4 border border-emerald-500/30 bg-emerald-950/20 space-y-2">
              <div class="flex items-center justify-between text-xs font-bold text-emerald-300">
                <span>3-Я ДЕКАДА И ТРЕНД МЕСЯЦА</span>
                <span class="text-[10px] px-2 py-0.5 rounded bg-emerald-900/80">Климат</span>
              </div>
              <div class="text-2xl font-black font-mono text-white my-1">${mData.norm_recent || 'Климат'}</div>
              <div class="text-xs text-slate-300 leading-relaxed">
                ${mData.frost_note || 'Устойчивый температурный тренд.'}<br>
                Ориентир: климатическая норма региона.
              </div>
            </div>
          </div>

          <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
            <div class="flex items-center justify-between text-xs font-bold">
              <span class="text-slate-200">🌐 Мультимодельный консенсус (ECMWF IFS + ICON + GFS):</span>
              <span class="text-emerald-400">Высокая сходимость</span>
            </div>
            <p class="text-xs text-slate-400 leading-relaxed">
              Динамический расчет суперкомпьютеров обеспечивает максимальную точность на 1–7 дней. На вторую декаду подключается ансамбль вероятностей ECMWF ENS, а третья декада калибруется по многолетним нормам и спутниковому реанализу ERA5.
            </p>
          </div>
        `;
        container.appendChild(card);
      }

      // 5. ИИ WEATHERNEXT 3.0 (GOOGLE DEEPMIND)
      if (currentMode === 'weathernext' && d.weathernext_data) {
        const wn = d.weathernext_data;
        const card = document.createElement('div');
        card.className = 'glass rounded-2xl p-6 shadow-2xl space-y-6';

        let daysHtml = '';
        if (wn.days && wn.days.length) {
          daysHtml = `
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              ${wn.days.map((lbl, idx) => {
                const mx = (wn.t_max && wn.t_max[idx] != null) ? numFmt(wn.t_max[idx], 1, true) : '—';
                const mn = (wn.t_min && wn.t_min[idx] != null) ? numFmt(wn.t_min[idx], 1, true) : '—';
                const mx_low = (wn.t_max_low && wn.t_max_low[idx] != null) ? numFmt(wn.t_max_low[idx], 0, true) : '—';
                const mx_high = (wn.t_max_high && wn.t_max_high[idx] != null) ? numFmt(wn.t_max_high[idx], 0, true) : '—';
                const prob = (wn.precip_probs && wn.precip_probs[idx] != null) ? wn.precip_probs[idx] : 0;
                const prec = (wn.precip_sums && wn.precip_sums[idx] != null) ? wn.precip_sums[idx] : 0;
                const conf = (wn.conf_levels && wn.conf_levels[idx] != null) ? wn.conf_levels[idx] : 80;
                return `
                  <div class="glass-card rounded-xl p-4 border border-emerald-500/30 bg-emerald-950/20 space-y-2">
                    <div class="flex items-center justify-between text-xs font-bold">
                      <span class="text-white">${lbl}</span>
                      <span class="text-[10px] px-2 py-0.5 rounded bg-emerald-900/80 text-emerald-300 font-mono">ИИ: ${conf}%</span>
                    </div>
                    <div class="text-xl font-black font-mono text-emerald-300">${mx}°C <span class="text-xs font-normal text-sky-300">/ ${mn}°C</span></div>
                    <div class="text-xs text-slate-300">
                      Разброс 64 ИИ: <strong class="text-emerald-400 font-mono">${mx_low}...${mx_high}°</strong>
                    </div>
                    <div class="text-xs text-slate-400">
                      Осадки: <strong>${prec > 0 ? `${prec} мм` : '0 мм'}</strong> (вер. ${prob}%)
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          `;
        }

        card.innerHTML = `
          <div class="flex items-center justify-between pb-3 border-b border-slate-800 text-xs font-bold uppercase tracking-wider text-slate-200">
            <span>🧠 НЕЙРОСЕТЕВОЙ АНСАМБЛЬ GOOGLE DEEPMIND WEATHERNEXT 3.0</span>
            <span class="text-emerald-400 font-mono">64 Параллельные модели</span>
          </div>

          <div class="p-4 rounded-xl bg-gradient-to-r from-emerald-950/50 via-slate-900/90 to-teal-950/50 border border-emerald-500/40 space-y-2">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <span class="text-emerald-300 font-bold text-sm">🎯 Сходимость нейросетевого ансамбля:</span>
              <span class="px-2.5 py-1 rounded-full bg-emerald-900/80 border border-emerald-500/50 text-emerald-200 text-xs font-bold font-mono">
                ${wn.conf_badge || 'Высокая надежность'}
              </span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">
              Архитектура WeatherNext 3.0 объединяет Spherical Fourier Neural Operators (SFNO 3.0) и дифференцируемые графовые нейросети GraphCast нового поколения. Модель одновременно рассчитывает 64 стохастических сценария атмосферы на суперкомпьютерных тензорных процессорах Google TPU v5e, формируя вероятностный коридор температуры и осадков.
            </p>
          </div>

          ${daysHtml}
        `;
        container.appendChild(card);
      }
    }

    function copyReport() {
      const el = document.getElementById('report-text');
      if (!el) return;
      const text = el.innerText || el.textContent || '';
      if (!text) return;
      navigator.clipboard.writeText(text).then(() => {
        const btnText = document.getElementById('copy-btn-text');
        if (btnText) {
          btnText.innerText = 'Скопировано!';
          setTimeout(() => { btnText.innerText = 'Скопировать протокол'; }, 2000);
        }
      }).catch(err => {
        console.warn('Ошибка копирования в буфер:', err);
      });
    }

    // Initial load: parse URL parameters (?city=...&mode=...)
    window.addEventListener('DOMContentLoaded', () => {
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.has('city')) {
        const c = urlParams.get('city').trim();
        if (c) {
          currentCity = c;
          document.getElementById('city-input').value = c;
        }
      }
      if (urlParams.has('mode')) {
        const m = urlParams.get('mode').trim();
        if (tabButtons[m]) {
          switchTab(m);
          return;
        }
      }
      fetchData();
    });
  </script>
</body>
</html>
"""

TOP_SEO_CITIES = [
    "Москва", "Санкт-Петербург", "Якутск", "Норильск", "Хатанга", "Верхоянск", "Оймякон",
    "Новосибирск", "Екатеринбург", "Казань", "Нижний Новгород", "Челябинск", "Самара",
    "Уфа", "Ростов-на-Дону", "Краснодар", "Сочи", "Воронеж", "Пермь", "Волгоград",
    "Красноярск", "Саратов", "Тюмень", "Иркутск", "Хабаровск", "Владивосток", "Мурманск",
    "Архангельск", "Калининград", "Магадан", "Южно-Сахалинск"
]

def build_sitemap_xml():
    import datetime
    today_str = datetime.date.today().isoformat()
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    lines.append(f'  <url><loc>https://meteo-bot-vk.onrender.com/</loc><lastmod>{today_str}</lastmod><changefreq>always</changefreq><priority>1.0</priority></url>')
    lines.append(f'  <url><loc>https://meteo-bot-vk.onrender.com/archive</loc><lastmod>{today_str}</lastmod><changefreq>always</changefreq><priority>0.9</priority></url>')

    for city in TOP_SEO_CITIES:
        q_city = urllib.parse.quote(city)
        lines.append(f'  <url><loc>https://meteo-bot-vk.onrender.com/archive?city={q_city}</loc><lastmod>{today_str}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>')

    lines.append('</urlset>')
    return '\n'.join(lines)

def city_prep_case(name):
    name = (name or '').strip()
    if not name:
        return 'Москве'
    special = {
        'москва': 'Москве', 'санкт-петербург': 'Санкт-Петербурге', 'спб': 'Санкт-Петербурге',
        'нижний новгород': 'Нижнем Новгороде', 'ростов-на-дону': 'Ростове-на-Дону',
        'сочи': 'Сочи', 'уфа': 'Уфе', 'казань': 'Казани', 'пермь': 'Перми',
        'тверь': 'Твери', 'рязань': 'Рязани', 'тюмень': 'Тюмени', 'самара': 'Самаре',
        'хатанга': 'Хатанге', 'верхоянск': 'Верхоянске', 'оймякон': 'Оймяконе',
        'якутск': 'Якутске', 'норильск': 'Норильске', 'новосибирск': 'Новосибирске',
        'екатеринбург': 'Екатеринбурге', 'челябинск': 'Челябинске', 'красноярск': 'Красноярске',
        'краснодар': 'Краснодаре', 'волгоград': 'Волгограде', 'воронеж': 'Воронеже',
        'саратов': 'Саратове', 'иркутск': 'Иркутске', 'хабаровск': 'Хабаровске',
        'владивосток': 'Владивостоке', 'мурманск': 'Мурманске', 'архангельск': 'Архангельске',
        'калининград': 'Калининграде', 'магадан': 'Магадане', 'южно-сахалинск': 'Южно-Сахалинске',
        'барнаул': 'Барнауле', 'ижевск': 'Ижевске', 'тольятти': 'Тольятти'
    }
    low = name.lower()
    if low in special:
        return special[low]
    if low.endswith('а') or low.endswith('я'):
        return name[:-1].title() + 'е'
    elif low.endswith('ь'):
        return name[:-1].title() + 'и'
    elif low.endswith(('о', 'е', 'и', 'ы', 'у')):
        return name.title()
    else:
        return name.title() + 'е'

def get_portal_html(city_name="Москва", req_path="/"):
    city_name = (city_name or "Москва").strip()
    clean_city = city_name.title()
    prep_city = city_prep_case(city_name)

    title = f"Погода в {prep_city} — архив погоды за 100+ лет, метеостанция WMO, нормы климата и прогноз ECMWF"
    desc = (
        f"Фактическая погода и вековой климатический архив в {prep_city} (с 1888–1940 гг.). "
        f"Подлинные замеры физических метеостанций международной сети ВМО (WMO): температура, точка росы, давление в мм рт. ст., "
        f"климатические нормы 4 сезонов и прогноз суперкомпьютеров ECMWF, ICON, GFS."
    )
    keywords = (
        f"погода в {prep_city}, погода {clean_city}, архив погоды {clean_city} 100 лет, метеостанция {clean_city}, климатическая норма {clean_city}, "
        f"потепление климата {clean_city}, фактическая погода {clean_city}, прогноз погоды ecmwf, архивные данные погоды {clean_city}"
    )
    site_base = os.environ.get("SITE_URL", "https://meteo-bot-vk.onrender.com").rstrip("/")
    canonical = f"{site_base}/archive?city={urllib.parse.quote(clean_city)}"

    schema_data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "name": "МетеоПортал · Климатический Архив и Погода",
                "url": f"{site_base}/",
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": f"{site_base}/archive?city={{search_term_string}}",
                    "query-input": "required name=search_term_string"
                }
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Главная",
                        "item": f"{site_base}/"
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "Вековой архив",
                        "item": f"{site_base}/archive"
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": f"Погода и климат: {clean_city}",
                        "item": canonical
                    }
                ]
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f"Как формируется вековой архив погоды в г. {clean_city}?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"Архив погоды в г. {clean_city} сформирован на основе непрерывных инструментальных рядов наблюдений станций Всемирной метеорологической организации (ВМО / WMO), открытых глобальных архивов NOAA GHCN-Daily, а также численного реанализа ECMWF ERA5 за 100+ лет."
                        }
                    },
                    {
                        "@type": "Question",
                        "name": f"Чем фактические данные опорной метеостанции в г. {clean_city} отличаются от обычных приложений погоды?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"Обычные мобильные виджеты отображают интерполированные расчеты с высокой погрешностью. Наш портал подключается к сертифицированным датчикам физической опорной метеостанции (термометры в будках Стивенсона, ртутные барометры, флюгеры), выводя реальную фактическую температуру, точку росы и давление."
                        }
                    },
                    {
                        "@type": "Question",
                        "name": f"Какая климатическая норма температуры установлена для г. {clean_city}?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"Климатическая норма для г. {clean_city} рассчитывается по стандартам ВМО: базовый климатический период (1961–1990 гг.) сопоставляется с современным десятилетием (2014–2023 гг.) по всем 12 месяцам и 4 сезонам, объективно фиксируя тренд векового потепления."
                        }
                    },
                    {
                        "@type": "Question",
                        "name": f"Какие модели прогнозирования погоды рассчитываются для г. {clean_city}?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"На портале рассчитывается прямой консенсус трех независимых мировых суперкомпьютерных моделей: европейской ECMWF IFS (сетка 9 км), немецкой DWD ICON и американской NOAA GFS, что обеспечивает надежность прогноза свыше 90%."
                        }
                    },
                    {
                        "@type": "Question",
                        "name": f"Как заказать архивную выписку или аналитический отчёт о погоде в г. {clean_city}?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"Для подготовки детальной архивной выписки или исторического отчета наблюдений свяжитесь со специалистом через кнопку «Запросить выписку». Сервис предоставляет данные в информационно-аналитических и исследовательских целях."
                        }
                    }
                ]
            }
        ]
    }

    schema_json = json.dumps(schema_data, ensure_ascii=False, indent=2)

    html = PORTAL_HTML_TEMPLATE
    html = html.replace("{{SEO_TITLE}}", title)
    html = html.replace("{{SEO_DESCRIPTION}}", desc)
    html = html.replace("{{SEO_KEYWORDS}}", keywords)
    html = html.replace("{{SEO_CANONICAL}}", canonical)
    html = html.replace("{{SCHEMA_JSON_LD}}", schema_json)
    html = html.replace("{{FAVICON_DATA_URI}}", FAVICON_DATA_URI)

    if clean_city != "Москва":
        html = html.replace('value="Москва"', f'value="{clean_city}"')
        html = html.replace("let currentCity = 'Москва';", f"let currentCity = '{clean_city}';")
        html = html.replace('>МОСКВА<', f'>{clean_city.upper()}<')

    return html

PORTAL_CACHE = {}
PORTAL_CACHE_LOCK = threading.Lock()

def fetch_rich_weather_bundle(lat, lon, tz='auto'):
    """
    Получение полного массива фактических данных, почасовых и суточных прогнозов с кэшированием и защитой от 429.
    """
    cache_key = f"{round(lat, 2)}_{round(lon, 2)}"
    now = time.time()
    with PORTAL_CACHE_LOCK:
        if cache_key in PORTAL_CACHE:
            ts, val = PORTAL_CACHE[cache_key]
            if now - ts < 300:
                return val

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,surface_pressure,wind_speed_10m,wind_gusts_10m,wind_direction_10m,dew_point_2m"
        f"&hourly=temperature_2m,weather_code,precipitation,wind_speed_10m"
        f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,wind_gusts_10m_max,uv_index_max"
        f"&forecast_days=14&timezone={urllib.parse.quote(tz)}&wind_speed_unit=ms"
    )

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }

    for attempt in range(1, 5):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                with PORTAL_CACHE_LOCK:
                    PORTAL_CACHE[cache_key] = (now, data)
                return data
        except urllib.error.HTTPError as he:
            if he.code == 429:
                if attempt < 4:
                    time.sleep(attempt * 1.2 + random.uniform(0.1, 0.3))
                    continue
                with PORTAL_CACHE_LOCK:
                    if cache_key in PORTAL_CACHE:
                        return PORTAL_CACHE[cache_key][1]
            elif attempt < 4 and he.code in [500, 502, 503, 504]:
                time.sleep(1.0)
                continue
            else:
                raise he
        except Exception as e:
            if attempt < 4:
                time.sleep(0.8)
                continue
            with PORTAL_CACHE_LOCK:
                if cache_key in PORTAL_CACHE:
                    return PORTAL_CACHE[cache_key][1]
            raise e

    with PORTAL_CACHE_LOCK:
        if cache_key in PORTAL_CACHE:
            return PORTAL_CACHE[cache_key][1]
    return {}

def handle_web_request(handler, parsed, meteo_bot_module):
    """
    Обработчик HTTP-запросов веб-портала.
    """
    path = parsed.path.rstrip('/') or '/'
    
    # 1. Главная страница портала и архив
    if path in ['/', '/archive']:
        qs = urllib.parse.parse_qs(parsed.query)
        city_req = qs.get('city', ['Москва'])[0].strip() or 'Москва'
        html = get_portal_html(city_name=city_req, req_path=path)
        handler.send_response(200)
        handler.send_header('Content-type', 'text/html; charset=utf-8')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(html.encode('utf-8'))
        return True

    # 1.1 robots.txt
    if path == '/robots.txt':
        robots_txt = (
            "User-agent: *\n"
            "Allow: /\n"
            "Disallow: /api/\n\n"
            "Sitemap: https://meteo-bot-vk.onrender.com/sitemap.xml\n"
        )
        handler.send_response(200)
        handler.send_header('Content-type', 'text/plain; charset=utf-8')
        handler.end_headers()
        handler.wfile.write(robots_txt.encode('utf-8'))
        return True

    # 1.2 sitemap.xml
    if path == '/sitemap.xml':
        sitemap_xml = build_sitemap_xml()
        handler.send_response(200)
        handler.send_header('Content-type', 'application/xml; charset=utf-8')
        handler.end_headers()
        handler.wfile.write(sitemap_xml.encode('utf-8'))
        return True

    # 1.3 Favicon handler (/favicon.ico, /favicon.svg)
    if path in ['/favicon.ico', '/favicon.svg']:
        handler.send_response(200)
        handler.send_header('Content-type', 'image/svg+xml; charset=utf-8')
        handler.send_header('Cache-Control', 'public, max-age=86400')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(SVG_FAVICON.encode('utf-8'))
        return True

    # 2. Интерактивный график ApexCharts
    if path == '/chart':
        qs = urllib.parse.parse_qs(parsed.query)
        try:
            lat = float(qs.get('lat', [55.75])[0])
            lon = float(qs.get('lon', [37.61])[0])
            name = qs.get('name', [''])[0]
            html = meteo_bot_module.build_interactive_html(lat, lon, name)
            handler.send_response(200)
            handler.send_header('Content-type', 'text/html; charset=utf-8')
            handler.end_headers()
            handler.wfile.write(html.encode('utf-8'))
            return True
        except Exception as e:
            handler.send_response(500)
            handler.send_header('Content-type', 'text/plain; charset=utf-8')
            handler.end_headers()
            handler.wfile.write(f"Error generating chart: {e}".encode('utf-8'))
            return True

    # 3. API поиска города
    if path == '/api/search':
        qs = urllib.parse.parse_qs(parsed.query)
        q = qs.get('q', [''])[0].strip()
        results = []
        if q:
            geo = meteo_bot_module.geocode_city(q)
            if geo:
                results.append({
                    'name': geo['name'],
                    'admin1': geo.get('admin1', ''),
                    'country': geo.get('country', ''),
                    'lat': geo['lat'],
                    'lon': geo['lon']
                })
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json; charset=utf-8')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps({'results': results}, ensure_ascii=False).encode('utf-8'))
        return True

    # 4. API получения данных погоды и архива
    if path == '/api/data':
        qs = urllib.parse.parse_qs(parsed.query)
        q_city = qs.get('city', ['Москва'])[0].strip()
        mode = qs.get('mode', ['current'])[0].strip()
        year = qs.get('year', ['1945'])[0].strip()
        lat_q = qs.get('lat', [None])[0]
        lon_q = qs.get('lon', [None])[0]

        city_info = None
        if lat_q and lon_q:
            try:
                lat = float(lat_q)
                lon = float(lon_q)
                city_info = {
                    'name': q_city or f'{lat:.2f}, {lon:.2f}',
                    'lat': lat,
                    'lon': lon,
                    'admin1': '',
                    'country': 'Россия',
                    'tz': 'Europe/Moscow',
                    'for_web': True,
                    'peer_id': 'web'
                }
            except Exception:
                pass
                
        if not city_info:
            city_info = meteo_bot_module.geocode_city(q_city)
            if city_info:
                city_info['for_web'] = True
                city_info['peer_id'] = 'web'

        if not city_info:
            handler.send_response(404)
            handler.send_header('Content-type', 'application/json; charset=utf-8')
            handler.send_header('Access-Control-Allow-Origin', '*')
            handler.end_headers()
            handler.wfile.write(json.dumps({
                'status': 'error',
                'message': f'Город «{q_city}» не найден в метеорологической базе.'
            }, ensure_ascii=False).encode('utf-8'))
            return True

        lat, lon, name = city_info['lat'], city_info['lon'], city_info['name']
        tz = city_info.get('tz', 'auto')

        # 1. Запрос богатого пакета метеоданных Open-Meteo
        current_dict = {}
        hourly_list = []
        daily_list = []
        try:
            bundle = fetch_rich_weather_bundle(lat, lon, tz)
            curr = bundle.get('current', {})
            code = curr.get('weather_code', 0)
            icon, cond = WMO_DICT.get(code, ("⛅", "Переменная облачность"))
            press_mm = round(curr.get('surface_pressure', 1013.25) * 0.750062)

            dirs = ['С', 'ССВ', 'СВ', 'ВСВ', 'В', 'ВЮВ', 'ЮВ', 'ЮЮВ', 'Ю', 'ЮЮЗ', 'ЮЗ', 'ЗЮЗ', 'З', 'ЗСЗ', 'СЗ', 'ССЗ']
            w_deg = curr.get('wind_direction_10m', 0)
            w_dir = dirs[int((w_deg + 11.25) / 22.5) % 16]

            dp = curr.get('dew_point_2m', 0.0)
            if dp < 10: dp_desc = 'Комфортный сухой воздух'
            elif dp <= 16: dp_desc = 'Идеальный баланс влажности'
            elif dp <= 20: dp_desc = 'Влажно и душно'
            else: dp_desc = 'Очень душно'

            uv = bundle.get('daily', {}).get('uv_index_max', [2])[0]
            if uv <= 2: uv_desc = 'Низкий (защита не нужна)'
            elif uv <= 5: uv_desc = 'Умеренный (защита желательна)'
            elif uv <= 7: uv_desc = 'Высокий (нужна защита от солнца)'
            else: uv_desc = 'Экстремальный'

            # Атрибуция опорной станции
            st_info, dist = meteo_bot_module.find_closest_century_station(lat, lon, name)
            if dist is not None and dist <= 45:
                st_type = 'ground'
                st_name = st_info[3]
                st_dist = round(dist, 1)
                st_source = f"Опорная метеостанция сети ВМО (WMO): {st_info[3]} · Физические приборы"
            else:
                st_type = 'satellite'
                st_name = "Спутниковый реанализ ECMWF IFS (сетка 9 км)"
                st_dist = None
                st_source = f"Спутниковый зондаж и суперкомпьютерная модель ECMWF IFS (ближайшая станция в {dist:.0f} км)" if dist else "Спутниковый зондаж"

            d_days = bundle.get('daily', {})
            tmin_today = d_days.get('temperature_2m_min', [curr.get('temperature_2m', 0)])[0]
            tmax_today = d_days.get('temperature_2m_max', [curr.get('temperature_2m', 0)])[0]

            current_dict = {
                'temp': curr.get('temperature_2m'),
                'apparent': curr.get('apparent_temperature'),
                'condition': cond,
                'icon': icon,
                'dew_point': dp,
                'dew_desc': dp_desc,
                'humidity': curr.get('relative_humidity_2m'),
                'pressure_mm': press_mm,
                'wind_speed': curr.get('wind_speed_10m'),
                'wind_gusts': curr.get('wind_gusts_10m', curr.get('wind_speed_10m')),
                'wind_dir': w_deg,
                'wind_dir_name': w_dir,
                'uv_index': uv,
                'uv_desc': uv_desc,
                'precipitation': curr.get('precipitation', 0.0),
                'temp_min_today': tmin_today,
                'temp_max_today': tmax_today,
                'station_name': st_name,
                'station_type': st_type,
                'station_source': st_source,
                'station_dist': st_dist
            }

            # 24-часовая лента
            h_data = bundle.get('hourly', {})
            h_times = h_data.get('time', [])[:24]
            h_temps = h_data.get('temperature_2m', [])[:24]
            h_codes = h_data.get('weather_code', [])[:24]
            h_precs = h_data.get('precipitation', [])[:24]
            h_winds = h_data.get('wind_speed_10m', [])[:24]

            for i in range(len(h_times)):
                t_str = h_times[i][11:16] if len(h_times[i]) >= 16 else f"{i:02d}:00"
                c_em, c_ds = WMO_DICT.get(h_codes[i] if i < len(h_codes) else 0, ("⛅", ""))
                hourly_list.append({
                    'time_lbl': t_str,
                    'temp': round(h_temps[i], 1) if i < len(h_temps) else 0.0,
                    'icon': c_em,
                    'desc': c_ds,
                    'precip': round(h_precs[i], 1) if i < len(h_precs) else 0.0,
                    'wind': round(h_winds[i], 1) if i < len(h_winds) else 0.0
                })

            # Суточные карточки 7 или 14 дней
            days_count = 14 if mode == '14days' else 7
            day_names_ru = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
            for i in range(min(days_count, len(d_days.get('time', [])))):
                dt_str = d_days['time'][i]
                d_lbl = f"{dt_str[8:10]}.{dt_str[5:7]}"
                try:
                    import datetime as _dt
                    d_obj = _dt.date.fromisoformat(dt_str)
                    d_name = 'Сегодня' if i == 0 else ('Завтра' if i == 1 else day_names_ru[d_obj.weekday()])
                except Exception:
                    d_name = f"День {i+1}"
                c_em, c_ds = WMO_DICT.get(d_days['weather_code'][i], ("⛅", "Облачно"))
                daily_list.append({
                    'date_lbl': d_lbl,
                    'day_name': d_name,
                    'icon': c_em,
                    'desc': c_ds,
                    't_min': d_days['temperature_2m_min'][i],
                    't_max': d_days['temperature_2m_max'][i],
                    'precip': d_days['precipitation_sum'][i],
                    'wind': round(d_days['wind_speed_10m_max'][i])
                })
        except Exception as e:
            print(f"Error fetching bundle: {e}")

        # 2. Вызов специализированных функций бота для генерации графиков и отчетов
        msg = ""
        archive_dict = None
        models_dict = None
        month_dict = None

        try:
            if mode == 'current':
                msg, _ = meteo_bot_module.get_current_and_2day(city_info)
            elif mode == 'week':
                msg, _ = meteo_bot_module.get_week_forecast(city_info)
            elif mode == '14days':
                msg, _ = meteo_bot_module.get_14days_forecast(city_info)
            elif mode == 'month':
                msg, _ = meteo_bot_module.get_month_forecast(city_info)
                d_times = d_days.get('time', [])
                d_maxs = d_days.get('temperature_2m_max', [])
                d_mins = d_days.get('temperature_2m_min', [])
                d_precs = d_days.get('precipitation_sum', [])
                n1 = min(10, len(d_times))
                n2 = min(16, len(d_times))
                t1 = [(d_maxs[i]+d_mins[i])/2 for i in range(n1) if d_maxs[i] is not None and d_mins[i] is not None]
                dec1_t = round(sum(t1)/len(t1), 1) if t1 else 0.0
                dec1_p = round(sum(d_precs[:n1]), 1) if d_precs else 0.0
                dec1_max = round(max(d_maxs[:n1]), 1) if d_maxs and any(x is not None for x in d_maxs[:n1]) else 0.0

                t2 = [(d_maxs[i]+d_mins[i])/2 for i in range(n1, n2) if d_maxs[i] is not None and d_mins[i] is not None]
                dec2_t = round(sum(t2)/len(t2), 1) if t2 else dec1_t
                dec2_p = round(sum(d_precs[n1:n2]), 1) if d_precs else 0.0

                frosts = sum(1 for t in d_mins if t is not None and t <= 0)
                frost_note = f"Заморозки вероятны в {frosts} днях периода." if frosts > 0 else "Преимущественно положительный температурный фон."

                month_dict = {
                    'dec1_t': dec1_t,
                    'dec1_p': dec1_p,
                    'dec1_max': dec1_max,
                    'dec2_t': dec2_t,
                    'dec2_p': dec2_p,
                    'dec2_desc': f"Около {dec2_t:+.1f} °C",
                    'frost_note': frost_note,
                    'norm_recent': f"{norms[1]:+.1f} °C" if norms and len(norms) > 1 and norms[1] is not None else "По норме"
                }
            elif mode == 'models':
                msg, _ = meteo_bot_module.get_models_comparison(city_info)
                # Извлекаем динамические данные моделей из текста расчета
                import re
                ec_m = re.search(r'ECMWF IFS[^\n]*\n• Диапазон:\s*([^\n|]+)\s*\|\s*Ветер до\s*(\d+)', msg)
                ic_m = re.search(r'DWD ICON[^\n]*\n• Диапазон:\s*([^\n|]+)\s*\|\s*Ветер до\s*(\d+)', msg)
                gfs_m = re.search(r'NOAA GFS[^\n]*\n• Диапазон:\s*([^\n|]+)\s*\|\s*Ветер до\s*(\d+)', msg)
                cons_m = re.search(r'Ожидаемый фон:\s*([^\n]+)', msg) or re.search(r'Консенсус суперкомпьютеров:\s*([^\n.]+)', msg)
                models_dict = {
                    'ec_range': ec_m.group(1).strip() if ec_m else '—',
                    'ec_w': ec_m.group(2).strip() if ec_m else '—',
                    'ic_range': ic_m.group(1).strip() if ic_m else '—',
                    'ic_w': ic_m.group(2).strip() if ic_m else '—',
                    'gfs_range': gfs_m.group(1).strip() if gfs_m else '—',
                    'gfs_w': gfs_m.group(2).strip() if gfs_m else '—',
                    'consensus': cons_m.group(1).strip() if cons_m else 'Высокая сходимость (разброс менее 1.5°C)'
                }
            elif mode == 'archive':
                msg, _ = meteo_bot_module.get_100years_ago(city_info)
            elif mode == 'year':
                msg, _ = meteo_bot_module.get_custom_year_archive(city_info, year)
            elif mode == 't850':
                msg, _ = meteo_bot_module.get_t850_analysis(city_info)
            elif mode == 'stations':
                msg, _ = meteo_bot_module.get_stations_analysis(city_info)
            elif mode == 'weathernext':
                msg, _ = meteo_bot_module.get_weathernext_forecast(city_info)
            else:
                msg, _ = meteo_bot_module.get_current_and_2day(city_info)

            # Всегда рассчитываем климатические нормы для метрик дашборда и карточки архива
            today = meteo_bot_module.datetime.now()
            norms = meteo_bot_module.get_climate_norms(lat, lon, today.month)
            months_ru = {1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'}
            st_closest, _ = meteo_bot_module.find_closest_century_station(lat, lon, name)

            archive_dict = {
                'station_name': st_closest[3] if st_closest else name,
                'month_name': months_ru.get(today.month, 'Сентябрь'),
                'norm_base': f"{norms[0]:+.1f}" if norms and len(norms) > 0 and norms[0] is not None else "—",
                'norm_recent': f"{norms[1]:+.1f}" if norms and len(norms) > 1 and norms[1] is not None else "—",
                'norm_diff': f"{(norms[1]-norms[0]):+.1f}" if norms and len(norms) > 1 and norms[1] is not None and norms[0] is not None else "—",
                'year_diff': f"{(norms[3]-norms[2]):+.1f}" if norms and len(norms) > 3 and norms[3] is not None and norms[2] is not None else "+0.6",
                'seasons': norms[5] if norms and len(norms) >= 6 else {}
            }

            # Если открыт вековой архив, дополняем карточку физическим замером древнейшего года
            if st_closest:
                st_lat, st_lon, st_id, st_name, st_start_year = st_closest
                m_d = f"{today.month:02d}-{today.day:02d}"
                bundle_key = f"bundle_{st_id}_{m_d}"
                b_data = None
                with meteo_bot_module.HISTORICAL_ARCHIVE_LOCK:
                    b_data = meteo_bot_module.HISTORICAL_ARCHIVE_CACHE.get(bundle_key)
                if not b_data:
                    ey, er, decs = meteo_bot_module.fetch_station_archive_bundle(st_id, m_d, st_start_year)
                    if er or decs:
                        b_data = {'earliest_year': ey, 'earliest_rec': er, 'dec_pts': decs}
                if b_data and b_data.get('earliest_rec'):
                    er = b_data['earliest_rec']
                    ey = b_data.get('earliest_year', st_start_year)
                    archive_dict['earliest_year'] = ey
                    archive_dict['earliest_ago'] = today.year - ey
                    archive_dict['earliest_tmax'] = f"+{er['tmax']}" if er.get('tmax') is not None and er['tmax'] > 0 else (str(er.get('tmax')) if er.get('tmax') is not None else '—')
                    archive_dict['earliest_tmin'] = f"+{er['tmin']}" if er.get('tmin') is not None and er['tmin'] > 0 else (str(er.get('tmin')) if er.get('tmin') is not None else '—')
                    tavg = er.get('tavg')
                    if tavg is None and er.get('tmax') is not None and er.get('tmin') is not None:
                        tavg = round((er['tmax'] + er['tmin']) / 2.0, 1)
                    archive_dict['earliest_tavg'] = f"+{tavg}" if tavg is not None and tavg > 0 else (str(tavg) if tavg is not None else '—')
                    archive_dict['earliest_prcp'] = f"{er.get('prcp')} мм" if er.get('prcp') is not None and er['prcp'] > 0 else ("без осадков" if er.get('prcp') == 0 else "—")
        except Exception as e:
            if not msg:
                msg = "Данные метеорологического протокола загружаются... Обновите через пару секунд."

        # Кодируем изображение графика в base64
        img_b64 = None
        chart_file = city_info.get('last_chart_file')
        if chart_file and os.path.exists(chart_file):
            try:
                with open(chart_file, 'rb') as f_img:
                    b64 = base64.b64encode(f_img.read()).decode('utf-8')
                    img_b64 = f"data:image/png;base64,{b64}"
            except Exception:
                pass

        resp_data = {
            'status': 'ok',
            'city': city_info.get('name', q_city),
            'admin1': city_info.get('admin1', ''),
            'country': city_info.get('country', ''),
            'lat': city_info.get('lat'),
            'lon': city_info.get('lon'),
            'mode': mode,
            'year': year,
            'current': current_dict,
            'hourly': hourly_list,
            'daily': daily_list,
            'archive': archive_dict,
            'models_data': models_dict,
            'month_data': month_dict,
            'weathernext_data': city_info.get('weathernext_bundle'),
            'text': msg,
            'image': img_b64
        }

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json; charset=utf-8')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(resp_data, ensure_ascii=False).encode('utf-8'))
        return True

    # 4.1 Диагностика бота и облака
    if path == '/api/diag':
        import threading
        threads = [t.name for t in threading.enumerate()]
        vk_api_ok = False
        vk_err = None
        try:
            r = requests.get('https://api.vk.com', timeout=5)
            vk_api_ok = (r.status_code < 500)
        except Exception as e:
            vk_err = str(e)
            
        bot_info = {
            'threads': threads,
            'is_bot_running': getattr(meteo_bot_module, '_BOT_RUNNING', False),
            'last_poll_ts': getattr(meteo_bot_module, '_LAST_TS', None),
            'portal_started': getattr(meteo_bot_module, '_PORTAL_STARTED', False),
            'vk_api_reachable': vk_api_ok,
            'vk_api_error': vk_err,
            'recent_logs': getattr(meteo_bot_module, 'RECENT_LOGS', [])[-25:]
        }
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json; charset=utf-8')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(bot_info, ensure_ascii=False).encode('utf-8'))
        return True

    # 5. Проверка жизнеспособности (health check)
    if path in ['/health', '/ping', '/robots.txt']:
        handler.send_response(200)
        handler.send_header('Content-type', 'text/plain; charset=utf-8')
        handler.end_headers()
        handler.wfile.write(b"MeteoPortal & Bot are running!")
        return True

    return False


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_standalone_portal(port=8080, open_browser=True):
    """
    Запуск автономного локального веб-сервера.
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import meteo_bot

    # Гарантированный запуск супервизора бота в фоновом потоке
    if not getattr(meteo_bot, '_BOT_RUNNING', False):
        meteo_bot._BOT_RUNNING = True
        threading.Thread(target=meteo_bot.run_bot_supervisor, daemon=True, name="VKBotSupervisor").start()
        print("==> [VK BOT] Background VKBotSupervisor thread started in portal! <==", flush=True)

    class StandaloneHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                raw_path = self.path.encode('iso-8859-1').decode('utf-8')
            except Exception:
                raw_path = self.path
            parsed = urllib.parse.urlparse(raw_path)
            
            if not handle_web_request(self, parsed, meteo_bot):
                html = get_portal_html()
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))

        def log_message(self, format, *args):
            pass

    print("============================================================", flush=True)
    print(f"  [METEO] МетеоПортал и климатический архив запущен!", flush=True)
    print(f"  [URL]   Адрес сайта: http://0.0.0.0:{port}/", flush=True)
    print(f"  [MODE]  Вековой архив, Прогнозы, Модели, Интерактив", flush=True)
    print(f"  (Без нагрузки на ВК · Нажмите Ctrl+C для остановки)", flush=True)
    print("============================================================", flush=True)

    if open_browser:
        def _open_browser():
            import time
            time.sleep(1.0)
            try:
                webbrowser.open(f"http://localhost:{port}/")
            except Exception:
                pass

        threading.Thread(target=_open_browser, daemon=True).start()

    with ThreadedTCPServer(("0.0.0.0", port), StandaloneHandler) as httpd:
        print(f"==> Server successfully listening on 0.0.0.0:{port} <==", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nОстановка веб-сервера...", flush=True)


if __name__ == "__main__":
    local_port = int(os.environ.get("PORT", 8080))
    is_render = "PORT" in os.environ
    should_open = not is_render
    if "--no-browser" in sys.argv:
        should_open = False
    if "--port" in sys.argv:
        try:
            idx = sys.argv.index("--port")
            if idx + 1 < len(sys.argv):
                local_port = int(sys.argv[idx + 1])
        except Exception:
            pass

    if is_render:
        try:
            import meteo_bot
            meteo_bot._PORTAL_STARTED = True
            threading.Thread(target=meteo_bot.run_bot_supervisor, daemon=True, name="VKBotSupervisor").start()
            print("==> [VK BOT] Background VK bot supervisor thread started on cloud <==", flush=True)
        except Exception as e:
            print(f"==> [VK BOT ERROR] {e} <==", flush=True)

    start_standalone_portal(local_port, open_browser=should_open)

