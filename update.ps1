# =====================================================================
#  Bale Chat Mosharket — نصب / به‌روزرسانی مستقیم از گیت‌هاب
#
#  اجرا: روی فایل راست‌کلیک کنید و «Run with PowerShell» را بزنید
#  یا در PowerShell:
#      powershell -ExecutionPolicy Bypass -File .\update.ps1
#
#  این اسکریپت:
#     ۱) آخرین نسخه را از گیت‌هاب می‌گیرد (اگر پوشه با git کلون شده
#        باشد با git pull وگرنه با فایل ZIP)
#     ۲) فایل‌های برنامه را جایگزین می‌کند — پیام‌های ذخیره‌شده
#        (messages.json)، تنظیمات و عکس‌ها (media) حفظ می‌شوند
#     ۳) پیش‌نیازها را نصب می‌کند و برنامه را اجرا می‌کند
# =====================================================================

$ErrorActionPreference = "Stop"
$ZipUrl = "https://github.com/sjalilvand/bale_chat_mosharket/archive/refs/heads/main.zip"

try {

    # 0) پایتون موجود است؟
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Host ""
        Write-Host "[X] Python نصب نیست!" -ForegroundColor Red
        Write-Host "    اگر winget دارید بزنید:  winget install -e --id Python.Python.3.12"
        Write-Host "    یا از python.org نصب کنید (تیک Add to PATH را بزنید)."
        Write-Host "    بعد از نصب PowerShell را ببندید و دوباره باز کنید و اسکریپت را دوباره اجرا کنید."
        pause
        exit 1
    }

    $dest = $PSScriptRoot
    if (-not $dest) { $dest = (Get-Location).Path }

    Write-Host ""
    Write-Host "=== Bale Chat Mosharket | update from GitHub ==="
    Write-Host "پوشه برنامه: $dest"
    Write-Host ""

    # 1) دریافت آخرین نسخه
    if (Test-Path (Join-Path $dest ".git")) {
        Write-Host "[1/3] به‌روزرسانی با git pull ..."
        git -C $dest pull
    } else {
        Write-Host "[1/3] دانلود آخرین نسخه از گیت‌هاب ..."
        $zip = Join-Path $env:TEMP "bale_mosharket.zip"
        $tmp = Join-Path $env:TEMP "bale_mosharket_extract"
        Invoke-WebRequest -Uri $ZipUrl -OutFile $zip -UseBasicParsing
        if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
        Expand-Archive -Path $zip -DestinationPath $tmp -Force
        Write-Host "      جایگزینی فایل‌های برنامه ... (پیام‌ها و تنظیمات شما حفظ می‌شوند)"
        Copy-Item (Join-Path $tmp "*") $dest -Recurse -Force
        Remove-Item $tmp -Recurse -Force
        Remove-Item $zip -Force -ErrorAction SilentlyContinue
    }

    # 2) نصب پیش‌نیازها
    Write-Host "[2/3] نصب پیش‌نیازها ..."
    python -m pip install -r (Join-Path $dest "requirements.txt") --disable-pip-version-check -q

    # 3) اجرای برنامه
    Write-Host "[3/3] اجرای برنامه ... (برای بستن برنامه این پنجره را ببندید یا Ctrl+C بزنید)"
    python (Join-Path $dest "main.py")

} catch {
    Write-Host ""
    Write-Host "[X] خطا: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "    اگر پیام مربوط به permissions/Policy است، PowerShell را Run as Administrator باز کنید و دوباره تلاش کنید."
    pause
}
