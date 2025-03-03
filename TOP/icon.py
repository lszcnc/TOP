#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
生成应用程序图标
运行此脚本将创建一个简单的应用程序图标
"""

import os

def create_icon():
    """
    创建应用程序图标
    需要安装matplotlib库
    """
    try:
        # 在函数内部导入matplotlib，这样在导入icon模块时不会立即尝试导入matplotlib
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        from matplotlib.path import Path
        import numpy as np
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(5, 5))
        
        # 设置背景色
        ax.set_facecolor('#1E2130')
        
        # 绘制圆形背景
        circle = plt.Circle((0.5, 0.5), 0.4, color='#3D4663')
        ax.add_patch(circle)
        
        # 绘制上升箭头（绿色）
        up_arrow_verts = [
            (0.3, 0.4),  # 起点
            (0.5, 0.7),  # 箭头尖
            (0.7, 0.4),  # 右下
            (0.6, 0.4),  # 右下内
            (0.6, 0.2),  # 右下延伸
            (0.4, 0.2),  # 左下延伸
            (0.4, 0.4),  # 左下内
            (0.3, 0.4),  # 回到起点
        ]
        
        up_arrow_codes = [
            Path.MOVETO,
            Path.LINETO,
            Path.LINETO,
            Path.LINETO,
            Path.LINETO,
            Path.LINETO,
            Path.LINETO,
            Path.CLOSEPOLY,
        ]
        
        up_arrow_path = Path(up_arrow_verts, up_arrow_codes)
        up_arrow_patch = patches.PathPatch(up_arrow_path, facecolor='#00C853', edgecolor='none')
        ax.add_patch(up_arrow_patch)
        
        # 绘制下降箭头（红色）
        down_arrow_verts = [
            (0.3, 0.6),  # 起点
            (0.5, 0.3),  # 箭头尖
            (0.7, 0.6),  # 右上
            (0.6, 0.6),  # 右上内
            (0.6, 0.8),  # 右上延伸
            (0.4, 0.8),  # 左上延伸
            (0.4, 0.6),  # 左上内
            (0.3, 0.6),  # 回到起点
        ]
        
        down_arrow_codes = [
            Path.MOVETO,
            Path.LINETO,
            Path.LINETO,
            Path.LINETO,
            Path.LINETO,
            Path.LINETO,
            Path.LINETO,
            Path.CLOSEPOLY,
        ]
        
        down_arrow_path = Path(down_arrow_verts, down_arrow_codes)
        down_arrow_patch = patches.PathPatch(down_arrow_path, facecolor='#FF5252', alpha=0.5, edgecolor='none')
        ax.add_patch(down_arrow_patch)
        
        # 设置坐标轴范围
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        # 隐藏坐标轴
        ax.axis('off')
        
        # 保存图标
        plt.savefig('icon.png', dpi=100, bbox_inches='tight', pad_inches=0)
        plt.close()
        
        print("图标已生成: icon.png")
        return True
    except ImportError:
        print("无法生成图标: 缺少matplotlib库")
        print("如需生成自定义图标，请安装matplotlib: pip install matplotlib")
        return False
    except Exception as e:
        print(f"生成图标时出错: {e}")
        return False

if __name__ == "__main__":
    create_icon() 