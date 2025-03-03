@echo off
echo 正在启动币安USDT合约涨跌幅排行榜...
echo 首次运行可能需要安装依赖，请耐心等待

echo 安装基本依赖...
pip install python-binance==1.0.16 PyQt5==5.15.7 pandas==1.5.3 requests==2.28.2

echo.
echo 是否安装matplotlib以支持自定义图标功能？(Y/N)
set /p install_matplotlib=

if /i "%install_matplotlib%"=="Y" (
    echo 正在安装matplotlib...
    pip install matplotlib==3.7.1
    echo matplotlib安装完成
) else (
    echo 跳过matplotlib安装，将使用默认图标
)

echo.
echo 启动应用程序...
python main.py

pause 