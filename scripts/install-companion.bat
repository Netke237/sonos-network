@echo off
setlocal

set "PATH=%LOCALAPPDATA%\Android\Sdk\platform-tools;%PATH%"
set "APK_PATH=%~dp0..\android\app\build\outputs\apk\debug\app-debug.apk"

if not exist "%APK_PATH%" (
    echo [ERROR] APK not found at %APK_PATH%
    echo Please build the project or check the path.
    pause
    exit /b 1
)

echo ============================================================
echo Sonos Network Companion Installer
echo ============================================================
echo Checking connected Android devices...
echo.

adb devices -l
echo.

adb get-state >nul 2>&1
if errorlevel 1 (
    echo [WARNING] No authorized Android device detected via ADB!
    echo.
    echo Please verify:
    echo  1. USB cable is firmly connected to PC and phone (not charge-only).
    echo  2. Phone screen is unlocked.
    echo  3. Developer Options are enabled:
    echo     - USB Debugging: ON
    echo     - Install via USB: ON (required for Xiaomi / MIUI / HyperOS)
    echo  4. If a prompt appeared on your phone, tap "Allow USB debugging".
    echo.
    echo Alternative: Open http://192.168.55.60:8001/install on your phone
    echo to download and install the APK directly over Wi-Fi.
    echo ============================================================
    pause
    exit /b 1
)

echo [OK] Device detected! Installing Companion APK...
echo APK: %APK_PATH%
echo.

adb install -r -d "%APK_PATH%"
if errorlevel 1 (
    echo.
    echo [ERROR] adb install failed.
    echo On Xiaomi devices, make sure "Install via USB" is toggled ON
    echo in Settings -> Additional settings -> Developer options.
) else (
    echo.
    echo [SUCCESS] App successfully installed!
    echo Launching Sonos Network Companion...
    adb shell monkey -p de.wutanglan.sonosnetwork 1 >nul 2>&1
)

echo.
pause
