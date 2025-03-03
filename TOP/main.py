#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import pandas as pd
import os.path
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
                            QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton,
                            QHeaderView, QTabWidget, QGridLayout, QFrame, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QIcon, QPalette
import requests

# 检查图标是否存在，如果不存在则尝试生成
def ensure_icon_exists():
    if not os.path.exists('icon.png'):
        try:
            # 尝试导入matplotlib
            try:
                import matplotlib
                import icon
                icon.create_icon()
                print("图标已成功生成")
            except ImportError:
                print("警告: 未安装matplotlib，将使用默认图标")
                print("如需自定义图标，请运行: pip install matplotlib")
                # 无法生成图标时不影响程序运行
                pass
        except Exception as e:
            print(f"警告: 无法生成图标: {e}")
            print("程序将继续运行，但没有自定义图标")

class DataFetcher(QThread):
    """数据获取线程，避免UI卡顿"""
    data_fetched = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, single_run=False):
        super().__init__()
        # 存储有效的交易对列表
        self.valid_pairs = []
        # 是否只运行一次
        self.single_run = single_run
        
    def run(self):
        # 如果是连续运行模式，则循环执行
        while True:
            try:
                # 首先获取所有可用的合约交易对信息
                exchange_info_url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
                exchange_info_response = requests.get(exchange_info_url, timeout=10)
                
                if exchange_info_response.status_code != 200:
                    self.error_occurred.emit(f"获取交易对信息失败: 状态码 {exchange_info_response.status_code}")
                    if self.single_run:
                        break
                    time.sleep(5)
                    continue
                
                exchange_info = exchange_info_response.json()
                
                # 提取所有状态为TRADING的USDT永续合约
                self.valid_pairs = []
                for symbol_info in exchange_info.get('symbols', []):
                    if (symbol_info.get('status') == 'TRADING' and 
                        symbol_info.get('symbol', '').endswith('USDT') and
                        symbol_info.get('contractType') == 'PERPETUAL'):
                        self.valid_pairs.append(symbol_info.get('symbol'))
                
                if not self.valid_pairs:
                    self.error_occurred.emit("未找到有效的USDT永续合约交易对")
                    if self.single_run:
                        break
                    time.sleep(5)
                    continue
                
                # 获取所有USDT合约交易对的24小时行情数据
                ticker_url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
                ticker_response = requests.get(ticker_url, timeout=10)
                
                if ticker_response.status_code != 200:
                    self.error_occurred.emit(f"获取行情数据失败: 状态码 {ticker_response.status_code}")
                    if self.single_run:
                        break
                    time.sleep(5)
                    continue
                    
                ticker_data = ticker_response.json()
                
                # 过滤出有效的USDT永续合约交易对
                valid_tickers = [item for item in ticker_data if item['symbol'] in self.valid_pairs]
                
                if not valid_tickers:
                    self.error_occurred.emit("未找到有效的USDT永续合约行情数据")
                    if self.single_run:
                        break
                    time.sleep(5)
                    continue
                
                # 创建DataFrame并计算涨跌幅
                df = pd.DataFrame(valid_tickers)
                
                # 确保数据类型正确
                df['priceChangePercent'] = df['priceChangePercent'].astype(float)
                df['price'] = df['lastPrice'].astype(float)
                df['volume'] = df['volume'].astype(float)
                df['highPrice'] = df['highPrice'].astype(float)
                df['lowPrice'] = df['lowPrice'].astype(float)
                
                # 过滤掉成交量为0的交易对
                df = df[df['volume'] > 0]
                
                # 选择需要的列
                df = df[['symbol', 'price', 'priceChangePercent', 'volume', 'highPrice', 'lowPrice']]
                
                # 发送数据到主线程
                self.data_fetched.emit(df)
                
                # 如果是单次运行模式，则退出循环
                if self.single_run:
                    break
                
                # 休眠30秒
                time.sleep(30)
            except Exception as e:
                self.error_occurred.emit(f"获取数据出错: {e}")
                if self.single_run:
                    break
                time.sleep(5)

class BinanceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.startDataFetcher()
        # 存储临时线程的引用
        self.temp_fetcher = None
        
    def initUI(self):
        # 设置窗口属性
        self.setWindowTitle('币安USDT合约涨跌幅排行榜')
        self.setGeometry(100, 100, 1000, 600)
        
        # 设置图标
        if os.path.exists('icon.png'):
            self.setWindowIcon(QIcon('icon.png'))
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E2130;
                color: #FFFFFF;
            }
            QTableWidget {
                background-color: #2D3446;
                color: #FFFFFF;
                gridline-color: #3D4663;
                border: none;
                font-size: 14px;
            }
            QTableWidget::item:alternate {
                background-color: #252A3A;
            }
            QHeaderView::section {
                background-color: #252A3A;
                color: #FFFFFF;
                padding: 5px;
                border: 1px solid #3D4663;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 1px solid #3D4663;
                background-color: #2D3446;
            }
            QTabBar::tab {
                background-color: #252A3A;
                color: #FFFFFF;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3D4663;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
            }
            QPushButton {
                background-color: #3D4663;
                color: #FFFFFF;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4D5683;
            }
            QPushButton:disabled {
                background-color: #2D3446;
                color: #AAAAAA;
            }
        """)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标题和时间标签
        header_layout = QHBoxLayout()
        title_label = QLabel('币安USDT合约涨跌幅排行榜')
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
        header_layout.addWidget(title_label)
        
        self.time_label = QLabel()
        self.time_label.setStyleSheet("font-size: 14px; color: #AAAAAA; alignment: right;")
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_layout.addWidget(self.time_label)
        
        main_layout.addLayout(header_layout)
        
        # 创建交易对信息标签
        self.pairs_info_label = QLabel('正在获取交易对信息...')
        self.pairs_info_label.setStyleSheet("font-size: 14px; color: #AAAAAA; margin-bottom: 5px;")
        main_layout.addWidget(self.pairs_info_label)
        
        # 创建单一页面显示所有数据
        self.main_tab = QWidget()
        main_tab_layout = QVBoxLayout(self.main_tab)
        
        # 创建涨幅榜标签
        gainers_label = QLabel('涨幅榜 Top 10')
        gainers_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00C853; margin-top: 10px;")
        main_tab_layout.addWidget(gainers_label)
        
        # 创建涨幅榜表格
        self.gainers_table = QTableWidget()
        self.gainers_table.setColumnCount(6)
        self.gainers_table.setHorizontalHeaderLabels(['交易对', '价格', '涨跌幅(%)', '24h成交量', '24h最高', '24h最低'])
        self.gainers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.gainers_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.gainers_table.setAlternatingRowColors(True)
        self.gainers_table.setShowGrid(True)
        main_tab_layout.addWidget(self.gainers_table)
        
        # 创建分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #3D4663; margin: 10px 0;")
        main_tab_layout.addWidget(separator)
        
        # 创建跌幅榜标签
        losers_label = QLabel('跌幅榜 Top 10')
        losers_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FF5252; margin-top: 10px;")
        main_tab_layout.addWidget(losers_label)
        
        # 创建跌幅榜表格
        self.losers_table = QTableWidget()
        self.losers_table.setColumnCount(6)
        self.losers_table.setHorizontalHeaderLabels(['交易对', '价格', '涨跌幅(%)', '24h成交量', '24h最高', '24h最低'])
        self.losers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.losers_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.losers_table.setAlternatingRowColors(True)
        self.losers_table.setShowGrid(True)
        main_tab_layout.addWidget(self.losers_table)
        
        main_layout.addWidget(self.main_tab)
        
        # 创建底部状态栏
        status_layout = QHBoxLayout()
        self.status_label = QLabel('正在获取数据...')
        status_layout.addWidget(self.status_label)
        
        self.refresh_button = QPushButton('刷新数据')
        self.refresh_button.clicked.connect(self.manualRefresh)
        status_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(status_layout)
        
        # 设置定时器更新时间显示
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTimeLabel)
        self.timer.start(1000)
        self.updateTimeLabel()
    
    def startDataFetcher(self):
        """启动数据获取线程"""
        self.data_fetcher = DataFetcher(single_run=False)  # 连续运行模式
        self.data_fetcher.data_fetched.connect(self.updateTables)
        self.data_fetcher.error_occurred.connect(self.handleError)
        self.data_fetcher.start()
    
    def handleError(self, error_msg):
        """处理错误信息"""
        self.status_label.setText(f'错误: {error_msg}')
    
    def updateTables(self, df):
        """更新表格数据"""
        try:
            # 更新交易对信息标签
            self.pairs_info_label.setText(f'当前显示 {len(df)} 个有效USDT永续合约交易对')
            
            # 按涨跌幅排序
            df_sorted = df.sort_values(by='priceChangePercent', ascending=False)
            
            # 获取涨幅前10和跌幅前10
            gainers = df_sorted.head(10)
            losers = df_sorted.tail(10).sort_values(by='priceChangePercent', ascending=True)
            
            # 更新涨幅榜
            self.updateTable(self.gainers_table, gainers)
            
            # 更新跌幅榜
            self.updateTable(self.losers_table, losers)
            
            # 更新状态
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.status_label.setText(f'最后更新: {current_time}')
        except Exception as e:
            self.status_label.setText(f'更新数据出错: {e}')
    
    def updateTable(self, table, data):
        """更新指定表格的数据"""
        table.setRowCount(len(data))
        
        for i, (_, row) in enumerate(data.iterrows()):
            # 交易对
            symbol_item = QTableWidgetItem(row['symbol'])
            table.setItem(i, 0, symbol_item)
            
            # 价格
            price_item = QTableWidgetItem(f"{float(row['price']):.4f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(i, 1, price_item)
            
            # 涨跌幅
            percent_change = float(row['priceChangePercent'])
            percent_item = QTableWidgetItem(f"{percent_change:.2f}%")
            percent_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # 根据涨跌设置颜色
            if percent_change > 0:
                percent_item.setForeground(QColor('#00C853'))  # 绿色
            elif percent_change < 0:
                percent_item.setForeground(QColor('#FF5252'))  # 红色
            
            table.setItem(i, 2, percent_item)
            
            # 成交量
            volume = float(row['volume'])
            volume_str = f"{volume:.2f}" if volume < 1000000 else f"{volume/1000000:.2f}M"
            volume_item = QTableWidgetItem(volume_str)
            volume_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(i, 3, volume_item)
            
            # 最高价
            high_item = QTableWidgetItem(f"{float(row['highPrice']):.4f}")
            high_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(i, 4, high_item)
            
            # 最低价
            low_item = QTableWidgetItem(f"{float(row['lowPrice']):.4f}")
            low_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(i, 5, low_item)
    
    def updateTimeLabel(self):
        """更新时间标签"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.time_label.setText(f'当前时间: {current_time}')
    
    def manualRefresh(self):
        """手动刷新数据"""
        try:
            self.status_label.setText('正在刷新数据...')
            
            # 如果已经有一个临时线程在运行，先停止它
            if self.temp_fetcher is not None and self.temp_fetcher.isRunning():
                self.temp_fetcher.quit()
                self.temp_fetcher.wait()
            
            # 创建一个临时线程获取数据
            self.temp_fetcher = DataFetcher(single_run=True)
            self.temp_fetcher.data_fetched.connect(self.updateTables)
            self.temp_fetcher.error_occurred.connect(self.handleError)
            
            # 连接线程完成信号
            self.temp_fetcher.finished.connect(self.onRefreshFinished)
            
            # 启动线程
            self.temp_fetcher.start()
            
            # 设置按钮暂时不可用，防止频繁点击
            self.refresh_button.setEnabled(False)
        except Exception as e:
            self.status_label.setText(f'刷新数据出错: {e}')
            self.refresh_button.setEnabled(True)
    
    def onRefreshFinished(self):
        """刷新完成后的处理"""
        # 重新启用刷新按钮
        self.refresh_button.setEnabled(True)
        
        # 清理临时线程引用
        if self.temp_fetcher is not None:
            self.temp_fetcher.deleteLater()
            self.temp_fetcher = None
    
    def closeEvent(self, event):
        """关闭窗口时的确认对话框"""
        reply = QMessageBox.question(self, '确认退出',
                                     "确定要退出程序吗?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            # 停止所有线程
            if hasattr(self, 'data_fetcher') and self.data_fetcher.isRunning():
                self.data_fetcher.quit()
                self.data_fetcher.wait()
            
            if hasattr(self, 'temp_fetcher') and self.temp_fetcher is not None and self.temp_fetcher.isRunning():
                self.temp_fetcher.quit()
                self.temp_fetcher.wait()
            
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    # 确保图标存在
    ensure_icon_exists()
    
    app = QApplication(sys.argv)
    window = BinanceApp()
    window.show()
    sys.exit(app.exec_()) 