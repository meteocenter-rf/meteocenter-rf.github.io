[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$host.UI.RawUI.WindowTitle = "Обновление МетеоПортала на GitHub Pages"

Clear-Host
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       ОБНОВЛЕНИЕ МЕТЕОПОРТАЛА НА GITHUB PAGES          " -ForegroundColor White -BackgroundColor DarkCyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$sourceDir = "C:\Users\danil\Desktop\САЙТ_ДЛЯ_GITHUB_PAGES"
if (-not (Test-Path $sourceDir)) {
    $sourceDir = "C:\Users\danil\OneDrive\Рабочий стол\САЙТ_ДЛЯ_GITHUB_PAGES"
}

$uploadFolder = "C:\Users\danil\Desktop\ГОТОВО_ДЛЯ_GITHUB_PAGES"
if (-not (Test-Path "C:\Users\danil\Desktop")) {
    $uploadFolder = "C:\Users\danil\OneDrive\Рабочий стол\ГОТОВО_ДЛЯ_GITHUB_PAGES"
}
New-Item -ItemType Directory -Path $uploadFolder -Force | Out-Null

$files = @(
    "index.html",
    "card.html",
    "snow.html",
    "anomalies.html",
    "models.html",
    "articles.html",
    "sitemap.xml",
    "favicon.svg",
    "manifest.json",
    ".nojekyll",
    "robots.txt"
)

# Sync latest files to upload folder
foreach ($f in $files) {
    $src = Join-Path $sourceDir $f
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination (Join-Path $uploadFolder $f) -Force
    }
}

Write-Host " [OK] Все 10 файлов подготовлены в папке:" -ForegroundColor Green
Write-Host "      $uploadFolder" -ForegroundColor DarkGray
Write-Host ""
Write-Host " [1/2] Открываю папку с готовыми файлами..." -ForegroundColor Yellow
Start-Process explorer.exe -ArgumentList $uploadFolder

Start-Sleep -Milliseconds 600

Write-Host " [2/2] Открываю страницу загрузки на GitHub в браузере..." -ForegroundColor Yellow
$githubUrl = "https://github.com/meteocenter-rf/meteocenter-rf.github.io/upload/main"
Start-Process $githubUrl

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  КАК ЗАВЕРШИТЬ ОБНОВЛЕНИЕ (ЗАЙМЕТ 20 СЕКУНД):          " -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " 1. В открывшейся папке выделите все файлы (Ctrl + A)" -ForegroundColor White
Write-Host " 2. Перетащите их мышкой в окно браузера на страницу GitHub" -ForegroundColor White
Write-Host " 3. Внизу страницы нажмите зеленую кнопку:" -ForegroundColor White
Write-Host "    [ Commit changes ]" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " Через 1-2 минуты сайт обновится по адресу:" -ForegroundColor White
Write-Host " https://meteocenter-rf.github.io/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Нажмите Enter для завершения..." -ForegroundColor DarkGray
Read-Host
