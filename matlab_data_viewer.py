#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MATLAB .mat文件可视化工具
用于载入和查看MATLAB数据集的keys和内容
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import scipy.io as scio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import ListedColormap
import matplotlib
matplotlib.use('TkAgg')


class MATFileViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("MATLAB .mat文件可视化工具")
        self.root.geometry("1200x800")
        
        # 设置DPI感知和字体大小
        self.setup_dpi_scaling()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.mat_data = None
        self.current_file = None
        self.current_key = None
        self.colorbar = None
        
        # 多通道可视化变量
        self.channel_vars = {}
        self.overlay_mode = tk.BooleanVar()
        
        self.setup_ui()
    
    def setup_dpi_scaling(self):
        """设置DPI缩放"""
        try:
            # Windows DPI感知设置
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        # 获取系统DPI缩放比例
        dpi = self.root.winfo_fpixels('1i')
        scale_factor = dpi / 96.0  # 96 DPI是标准
        
        # 设置字体大小
        self.font_size = int(10 * scale_factor)
        self.title_font_size = int(12 * scale_factor)
        
        # 配置默认字体
        default_font = ("Arial", self.font_size)
        title_font = ("Arial", self.title_font_size, "bold")
        mono_font = ("Consolas", self.font_size)
        
        self.root.option_add("*Font", default_font)
        
        # 存储字体配置供后续使用
        self.fonts = {
            'default': default_font,
            'title': title_font,
            'mono': mono_font
        }
    
    def on_closing(self):
        """窗口关闭事件处理"""
        try:
            plt.close('all')  # 关闭所有matplotlib图形
            self.root.quit()  # 退出主循环
            self.root.destroy()  # 销毁窗口
        except:
            pass
        finally:
            sys.exit(0)  # 确保进程完全退出
        
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 文件选择按钮
        ttk.Button(control_frame, text="选择.mat文件", command=self.load_file).pack(side=tk.LEFT, padx=(0, 10))
        
        # 当前文件标签
        self.file_label = ttk.Label(control_frame, text="未选择文件", foreground="gray", font=self.fonts['default'])
        self.file_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # 主内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧面板 - 数据结构树
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(left_frame, text="数据结构", font=self.fonts['title']).pack(anchor=tk.W)
        
        # 树形视图
        tree_frame = ttk.Frame(left_frame, width=int(300 * (self.font_size / 10)))
        tree_frame.pack(fill=tk.BOTH, expand=True)
        tree_frame.pack_propagate(False)  # 保持固定宽度
        
        self.tree = ttk.Treeview(tree_frame)
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定树形视图选择事件
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        
        # 右侧面板 - 数据详情和可视化
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 可视化控制面板
        viz_control_frame = ttk.Frame(right_frame)
        viz_control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 多通道叠加选项
        self.overlay_checkbox = ttk.Checkbutton(
            viz_control_frame, 
            text="多通道叠加显示", 
            variable=self.overlay_mode,
            command=self.update_visualization
        )
        self.overlay_checkbox.pack(side=tk.LEFT, padx=(0, 10))
        
        # 通道选择框架
        self.channel_frame = ttk.LabelFrame(viz_control_frame, text="选择通道")
        self.channel_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 创建笔记本标签页
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 数据信息标签页
        self.info_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.info_frame, text="数据信息")
        
        self.info_text = tk.Text(self.info_frame, wrap=tk.WORD, font=self.fonts['mono'])
        info_scrollbar = ttk.Scrollbar(self.info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scrollbar.set)
        
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 可视化标签页
        self.plot_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.plot_frame, text="数据可视化")
        
        # 创建matplotlib图形
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def load_file(self):
        """加载.mat文件"""
        file_path = filedialog.askopenfilename(
            title="选择MATLAB .mat文件",
            filetypes=[("MAT files", "*.mat"), ("All files", "*.*")]
        )
        
        if file_path:
            self.load_mat_file(file_path)
    
    def load_mat_file(self, file_path):
        """载入MATLAB文件"""
        try:
            self.mat_data = scio.loadmat(file_path)
            self.current_file = file_path
            self.file_label.config(text=f"当前文件: {os.path.basename(file_path)}", foreground="black")
            
            self.populate_tree()
            self.show_file_info()
            
            messagebox.showinfo("成功", f"成功载入文件: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("错误", f"载入文件失败: {str(e)}")
    
    def populate_tree(self):
        """填充树形视图"""
        # 清空树
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if self.mat_data is None:
            return
        
        # 添加根节点
        root_item = self.tree.insert("", "end", text="MAT文件内容", open=True)
        
        # 遍历所有键
        for key, value in self.mat_data.items():
            if not key.startswith('__'):  # 跳过元数据
                self.add_tree_item(root_item, key, value)
    
    def add_tree_item(self, parent, key, value):
        """递归添加树项"""
        if isinstance(value, np.ndarray):
            shape_str = f"shape: {value.shape}, dtype: {value.dtype}"
            item = self.tree.insert(parent, "end", text=f"{key} [{shape_str}]", 
                                  values=(key, "array"))
            
            # 如果是小数组，显示一些内容
            if value.size <= 10:
                self.tree.insert(item, "end", text=f"数据: {value.flatten()}")
            
        elif isinstance(value, (list, tuple)):
            item = self.tree.insert(parent, "end", text=f"{key} [list, len: {len(value)}]",
                                  values=(key, "list"))
            for i, item_value in enumerate(value[:5]):  # 只显示前5个元素
                self.add_tree_item(item, f"[{i}]", item_value)
            
        elif isinstance(value, dict):
            item = self.tree.insert(parent, "end", text=f"{key} [dict]",
                                  values=(key, "dict"))
            for sub_key, sub_value in value.items():
                self.add_tree_item(item, sub_key, sub_value)
                
        else:
            self.tree.insert(parent, "end", text=f"{key}: {type(value).__name__}",
                           values=(key, "other"))
    
    def on_tree_select(self, event):
        """树形视图选择事件"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item, "values")
        
        if len(values) >= 1:
            key = values[0]
            self.current_key = key
            self.show_data_info(key)
            self.setup_channel_controls(key)
            self.plot_data(key)
    
    def setup_channel_controls(self, key):
        """设置通道控制"""
        # 清空之前的通道控件
        for widget in self.channel_frame.winfo_children():
            widget.destroy()
        
        self.channel_vars.clear()
        
        if self.mat_data is None or key not in self.mat_data:
            return
        
        data = self.mat_data[key]
        
        # 只对3D数据显示通道选择
        if isinstance(data, np.ndarray) and data.ndim == 3:
            # 显示通道选择框架
            self.channel_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # 创建滚动框架 - 使用更好的布局
            # 主容器
            scroll_container = ttk.Frame(self.channel_frame)
            scroll_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 创建Canvas和Scrollbar
            canvas = tk.Canvas(scroll_container, height=80, highlightthickness=0)
            v_scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
            h_scrollbar = ttk.Scrollbar(scroll_container, orient="horizontal", command=canvas.xview)
            scrollable_frame = ttk.Frame(canvas)
            
            # 配置滚动
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            # 添加鼠标滚轮支持
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
            def _on_shift_mousewheel(event):
                canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
            
            canvas.bind("<MouseWheel>", _on_mousewheel)
            canvas.bind("<Shift-MouseWheel>", _on_shift_mousewheel)
            
            # 添加所有通道的复选框 - 不再限制数量
            num_channels = data.shape[2]
            
            # 创建网格布局来更好地组织复选框
            cols = 8  # 每行显示8个通道
            rows = (num_channels + cols - 1) // cols
            
            for i in range(num_channels):
                var = tk.BooleanVar()
                # 默认选中前3个通道
                if i < 3:
                    var.set(True)
                
                self.channel_vars[i] = var
                
                row = i // cols
                col = i % cols
                
                checkbox = ttk.Checkbutton(
                    scrollable_frame,
                    text=f"Ch{i+1}",
                    variable=var,
                    command=self.update_visualization
                )
                checkbox.grid(row=row, column=col, padx=3, pady=2, sticky="w")
            
            # 添加"全选"和"清除"按钮
            control_frame = ttk.Frame(scrollable_frame)
            control_frame.grid(row=rows, column=0, columnspan=cols, pady=(10, 0), sticky="w")
            
            def select_all():
                for var in self.channel_vars.values():
                    var.set(True)
                self.update_visualization()
            
            def clear_all():
                for var in self.channel_vars.values():
                    var.set(False)
                self.update_visualization()
            
            def select_first_n(n):
                clear_all()
                for i in range(min(n, len(self.channel_vars))):
                    self.channel_vars[i].set(True)
                self.update_visualization()
            
            ttk.Button(control_frame, text="全选", command=select_all, width=8).pack(side=tk.LEFT, padx=2)
            ttk.Button(control_frame, text="清除", command=clear_all, width=8).pack(side=tk.LEFT, padx=2)
            ttk.Button(control_frame, text="前3个", command=lambda: select_first_n(3), width=8).pack(side=tk.LEFT, padx=2)
            ttk.Button(control_frame, text="前10个", command=lambda: select_first_n(10), width=8).pack(side=tk.LEFT, padx=2)
            
            # 显示通道总数信息
            info_label = ttk.Label(control_frame, text=f"总计: {num_channels} 个通道")
            info_label.pack(side=tk.RIGHT, padx=10)
            
            # 布局滚动组件
            canvas.grid(row=0, column=0, sticky="nsew")
            v_scrollbar.grid(row=0, column=1, sticky="ns")
            h_scrollbar.grid(row=1, column=0, sticky="ew")
            
            # 配置权重
            scroll_container.grid_rowconfigure(0, weight=1)
            scroll_container.grid_columnconfigure(0, weight=1)
            
        else:
            # 隐藏通道选择框架
            self.channel_frame.pack_forget()
    
    def update_visualization(self):
        """更新可视化"""
        if self.current_key:
            self.plot_data(self.current_key)
    
    def show_file_info(self):
        """显示文件整体信息"""
        if self.mat_data is None:
            return
        
        info = f"文件: {os.path.basename(self.current_file)}\n"
        info += f"路径: {self.current_file}\n"
        info += f"文件大小: {os.path.getsize(self.current_file)} 字节\n\n"
        info += "所有键 (keys):\n"
        info += "=" * 40 + "\n"
        
        for key, value in self.mat_data.items():
            if not key.startswith('__'):
                if isinstance(value, np.ndarray):
                    info += f"  {key:<20} | shape: {str(value.shape):<15} | dtype: {value.dtype}\n"
                else:
                    info += f"  {key:<20} | type: {type(value).__name__}\n"
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
    
    def show_data_info(self, key):
        """显示特定数据的详细信息"""
        if self.mat_data is None or key not in self.mat_data:
            return
        
        data = self.mat_data[key]
        
        info = f"键: {key}\n"
        info += "=" * 40 + "\n"
        info += f"类型: {type(data).__name__}\n"
        
        if isinstance(data, np.ndarray):
            info += f"形状: {data.shape}\n"
            info += f"数据类型: {data.dtype}\n"
            info += f"元素数量: {data.size}\n"
            info += f"维度: {data.ndim}\n"
            
            if data.size > 0:
                info += f"最小值: {np.min(data)}\n"
                info += f"最大值: {np.max(data)}\n"
                info += f"平均值: {np.mean(data)}\n"
                info += f"标准差: {np.std(data)}\n"
            
            info += "\n数据预览:\n"
            info += "-" * 20 + "\n"
            
            if data.size <= 50:
                info += str(data)
            else:
                info += f"数据太大，只显示部分内容:\n"
                if data.ndim == 1:
                    info += f"前10个元素: {data[:10]}\n"
                    info += f"后10个元素: {data[-10:]}"
                elif data.ndim == 2:
                    info += f"前5行:\n{data[:5]}\n"
                    if data.shape[0] > 10:
                        info += f"后5行:\n{data[-5:]}"
                else:
                    info += f"形状: {data.shape}\n"
                    info += f"部分数据: {data.flatten()[:20]}..."
        
        else:
            info += f"内容: {str(data)[:500]}"
            if len(str(data)) > 500:
                info += "..."
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
    
    def get_colormap_for_dtype(self, data):
        """根据数据类型选择合适的颜色映射"""
        dtype_str = str(data.dtype)
        
        if 'int' in dtype_str:
            # 整数类型 - 使用离散颜色映射
            unique_values = np.unique(data)
            num_unique = len(unique_values)
            
            if num_unique <= 2:
                # 二值数据
                return 'gray', True
            elif num_unique <= 10:
                # 少量离散值 - 使用定性颜色
                return 'tab10', True
            elif num_unique <= 20:
                # 中等离散值
                return 'tab20', True
            else:
                # 大量离散值 - 使用连续映射
                return 'viridis', False
        else:
            # 浮点类型 - 使用连续颜色映射
            return 'viridis', False
    
    def create_discrete_colormap(self, data, base_cmap):
        """为离散数据创建颜色映射"""
        unique_values = np.unique(data)
        num_unique = len(unique_values)
        
        if num_unique <= 20:
            # 使用matplotlib的定性颜色映射
            if base_cmap == 'tab10':
                colors = plt.cm.tab10(np.linspace(0, 1, min(num_unique, 10)))
            elif base_cmap == 'tab20':
                colors = plt.cm.tab20(np.linspace(0, 1, min(num_unique, 20)))
            else:
                colors = plt.cm.Set3(np.linspace(0, 1, num_unique))
            
            return ListedColormap(colors), unique_values
        else:
            return plt.cm.get_cmap('viridis'), unique_values

    def plot_data(self, key):
        """绘制数据"""
        if self.mat_data is None or key not in self.mat_data:
            return
        
        data = self.mat_data[key]
        
        # 清空之前的图和颜色条
        self.ax.clear()
        # 完全重新创建figure来避免colorbar问题
        if hasattr(self, 'colorbar') and self.colorbar is not None:
            try:
                # 先尝试移除colorbar
                self.colorbar.remove()
            except:
                # 如果移除失败，重新创建整个figure
                self.fig.clear()
                self.ax = self.fig.add_subplot(111)
            finally:
                self.colorbar = None
        
        try:
            if isinstance(data, np.ndarray) and data.size > 0:
                if data.ndim == 1:
                    # 一维数组 - 线图
                    self.ax.plot(data, linewidth=2)
                    self.ax.set_title(f"1D Data: {key}", fontsize=self.title_font_size)
                    self.ax.set_xlabel("Index", fontsize=self.font_size)
                    self.ax.set_ylabel("Value", fontsize=self.font_size)
                    
                elif data.ndim == 2:
                    # 二维数组
                    if min(data.shape) == 1:
                        # 实际上是一维数据
                        flat_data = data.flatten()
                        self.ax.plot(flat_data, linewidth=2)
                        self.ax.set_title(f"2D Data (Flattened): {key}", fontsize=self.title_font_size)
                        self.ax.set_xlabel("Index", fontsize=self.font_size)
                        self.ax.set_ylabel("Value", fontsize=self.font_size)
                    else:
                        # 显示为热图
                        cmap_name, is_discrete = self.get_colormap_for_dtype(data)
                        
                        if is_discrete:
                            cmap, unique_vals = self.create_discrete_colormap(data, cmap_name)
                            im = self.ax.imshow(data, cmap=cmap, aspect='auto', interpolation='nearest')
                            
                            # 为离散数据创建特殊的颜色条
                            try:
                                if len(unique_vals) <= 20:
                                    self.colorbar = self.fig.colorbar(im, ax=self.ax, shrink=0.8)
                                    self.colorbar.set_ticks(unique_vals)
                                    self.colorbar.set_label('Discrete Values', fontsize=self.font_size)
                                else:
                                    self.colorbar = self.fig.colorbar(im, ax=self.ax, shrink=0.8)
                                    self.colorbar.set_label('Values', fontsize=self.font_size)
                            except Exception:
                                # 如果colorbar创建失败，继续绘制但不显示colorbar
                                pass
                        else:
                            im = self.ax.imshow(data, cmap=cmap_name, aspect='auto', interpolation='bilinear')
                            try:
                                self.colorbar = self.fig.colorbar(im, ax=self.ax, shrink=0.8)
                                self.colorbar.set_label('Values', fontsize=self.font_size)
                            except Exception:
                                # 如果colorbar创建失败，继续绘制但不显示colorbar
                                pass
                        
                        self.ax.set_title(f"2D Heatmap: {key}", fontsize=self.title_font_size)
                        self.ax.set_xlabel("X", fontsize=self.font_size)
                        self.ax.set_ylabel("Y", fontsize=self.font_size)
                        
                elif data.ndim >= 3:
                    # 三维或高维数组
                    if self.overlay_mode.get() and self.channel_vars:
                        # 多通道叠加模式
                        self.plot_multichannel_overlay(data, key)
                    else:
                        # 单通道模式 - 显示第一个切片
                        slice_data = data[:, :, 0] if data.shape[2] > 0 else data[:, :, 0]
                        
                        cmap_name, is_discrete = self.get_colormap_for_dtype(slice_data)
                        
                        if is_discrete:
                            cmap, unique_vals = self.create_discrete_colormap(slice_data, cmap_name)
                            im = self.ax.imshow(slice_data, cmap=cmap, aspect='auto', interpolation='nearest')
                        else:
                            im = self.ax.imshow(slice_data, cmap=cmap_name, aspect='auto', interpolation='bilinear')
                        
                        try:
                            self.colorbar = self.fig.colorbar(im, ax=self.ax, shrink=0.8)
                            self.colorbar.set_label('Values', fontsize=self.font_size)
                        except Exception:
                            # 如果colorbar创建失败，继续绘制但不显示colorbar
                            pass
                        self.colorbar.set_label('Values', fontsize=self.font_size)
                        self.ax.set_title(f"3D Data - Channel 1: {key}", fontsize=self.title_font_size)
                        self.ax.set_xlabel("X", fontsize=self.font_size)
                        self.ax.set_ylabel("Y", fontsize=self.font_size)
                
                # 设置网格和字体大小
                self.ax.grid(True, alpha=0.3)
                self.ax.tick_params(labelsize=self.font_size-1)
                
            else:
                # 非数值数据
                self.ax.text(0.5, 0.5, f"Cannot visualize:\n{type(data).__name__}", 
                           horizontalalignment='center', verticalalignment='center',
                           transform=self.ax.transAxes, fontsize=self.font_size)
                self.ax.set_title(f"Data: {key}", fontsize=self.title_font_size)
                
        except Exception as e:
            self.ax.text(0.5, 0.5, f"Visualization Error:\n{str(e)}", 
                       horizontalalignment='center', verticalalignment='center',
                       transform=self.ax.transAxes, fontsize=self.font_size)
            self.ax.set_title(f"Error: {key}", fontsize=self.title_font_size)
        
        # 调整布局
        self.fig.tight_layout()
        self.canvas.draw()
    
    def plot_multichannel_overlay(self, data, key):
        """在一张图上叠加显示多个通道"""
        selected_channels = [ch for ch, var in self.channel_vars.items() if var.get()]
        
        if not selected_channels:
            # 如果没有选择通道，显示第一个通道
            selected_channels = [0]
        
        # 确保选择的通道都在有效范围内
        valid_channels = [ch for ch in selected_channels if ch < data.shape[2]]
        
        if not valid_channels:
            self.ax.text(0.5, 0.5, "No valid channels selected", 
                       horizontalalignment='center', verticalalignment='center',
                       transform=self.ax.transAxes, fontsize=self.font_size)
            return
        
        if len(valid_channels) == 1:
            # 单通道显示
            ch = valid_channels[0]
            slice_data = data[:, :, ch]
            cmap_name, is_discrete = self.get_colormap_for_dtype(slice_data)
            
            if is_discrete:
                cmap, unique_vals = self.create_discrete_colormap(slice_data, cmap_name)
                im = self.ax.imshow(slice_data, cmap=cmap, aspect='auto', interpolation='nearest')
            else:
                im = self.ax.imshow(slice_data, cmap=cmap_name, aspect='auto', interpolation='bilinear')
            
            try:
                self.colorbar = self.fig.colorbar(im, ax=self.ax, shrink=0.8)
                self.colorbar.set_label(f'Channel {ch+1} Values', fontsize=self.font_size)
            except Exception:
                pass
            
            self.ax.set_title(f"Channel {ch+1}: {key}", fontsize=self.title_font_size)
            
        else:
            # 多通道叠加 - 创建加权叠加图像
            # 方法1: 如果通道数量少，使用RGB叠加
            if len(valid_channels) <= 3:
                # RGB叠加
                overlay_image = np.zeros((*data.shape[:2], 3), dtype=np.float32)
                colors = ['red', 'green', 'blue']
                color_values = [(1,0,0), (0,1,0), (0,0,1)]
                
                max_values = []
                min_values = []
                
                for i, ch in enumerate(valid_channels):
                    channel_data = data[:, :, ch].astype(np.float32)
                    max_val = np.max(channel_data)
                    min_val = np.min(channel_data)
                    max_values.append(max_val)
                    min_values.append(min_val)
                    
                    # 归一化到0-1
                    if max_val > min_val:
                        normalized = (channel_data - min_val) / (max_val - min_val)
                    else:
                        normalized = np.zeros_like(channel_data)
                    
                    # 应用到对应的RGB通道
                    for j in range(3):
                        overlay_image[:, :, j] += normalized * color_values[i][j]
                
                # 限制RGB值到0-1范围
                overlay_image = np.clip(overlay_image, 0, 1)
                
                self.ax.imshow(overlay_image, aspect='auto')
                self.ax.set_title(f"RGB Overlay - Channels {[ch+1 for ch in valid_channels]}: {key}", 
                                fontsize=self.title_font_size)
                
                # 创建图例显示通道信息
                from matplotlib.patches import Patch
                legend_elements = []
                for i, ch in enumerate(valid_channels):
                    range_str = f"[{min_values[i]:.2f}, {max_values[i]:.2f}]"
                    legend_elements.append(
                        Patch(facecolor=colors[i], label=f'Ch{ch+1}: {range_str}')
                    )
                
                self.ax.legend(handles=legend_elements, loc='upper right', 
                             bbox_to_anchor=(1, 1), fontsize=self.font_size-2)
                
            else:
                # 方法2: 大量通道使用加权平均或者最大值投影
                overlay_method = "average"  # 可以是 "average", "max", "sum"
                
                if overlay_method == "average":
                    # 加权平均
                    overlay_data = np.zeros(data.shape[:2], dtype=np.float32)
                    total_weight = 0
                    
                    for ch in valid_channels:
                        channel_data = data[:, :, ch].astype(np.float32)
                        # 使用通道的标准差作为权重
                        weight = np.std(channel_data) + 1e-8
                        overlay_data += channel_data * weight
                        total_weight += weight
                    
                    overlay_data /= total_weight
                    title_prefix = "Weighted Average"
                    
                elif overlay_method == "max":
                    # 最大值投影
                    selected_data = data[:, :, valid_channels]
                    overlay_data = np.max(selected_data, axis=2)
                    title_prefix = "Max Projection"
                    
                else:  # sum
                    # 求和
                    selected_data = data[:, :, valid_channels]
                    overlay_data = np.sum(selected_data, axis=2)
                    title_prefix = "Sum"
                
                # 显示叠加结果
                cmap_name, is_discrete = self.get_colormap_for_dtype(overlay_data)
                
                if is_discrete:
                    cmap, unique_vals = self.create_discrete_colormap(overlay_data, cmap_name)
                    im = self.ax.imshow(overlay_data, cmap=cmap, aspect='auto', interpolation='nearest')
                else:
                    im = self.ax.imshow(overlay_data, cmap=cmap_name, aspect='auto', interpolation='bilinear')
                
                try:
                    self.colorbar = self.fig.colorbar(im, ax=self.ax, shrink=0.8)
                    self.colorbar.set_label(f'{title_prefix} Values', fontsize=self.font_size)
                except Exception:
                    pass
                
                self.ax.set_title(f"{title_prefix} of {len(valid_channels)} Channels: {key}", 
                                fontsize=self.title_font_size)
                
                # 添加文本显示选中的通道
                channel_text = f"Channels: {', '.join([str(ch+1) for ch in valid_channels[:10]])}"
                if len(valid_channels) > 10:
                    channel_text += f" ... (+{len(valid_channels)-10} more)"
                
                self.ax.text(0.02, 0.98, channel_text, 
                           transform=self.ax.transAxes, fontsize=self.font_size-2,
                           verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", 
                           facecolor="white", alpha=0.8))
        
        self.ax.set_xlabel("X", fontsize=self.font_size)
        self.ax.set_ylabel("Y", fontsize=self.font_size)


def main():
    """主函数"""
    root = tk.Tk()
    app = MATFileViewer(root)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path) and file_path.endswith('.mat'):
            app.load_mat_file(file_path)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            plt.close('all')
            root.quit()
            root.destroy()
        except:
            pass


if __name__ == "__main__":
    main()
