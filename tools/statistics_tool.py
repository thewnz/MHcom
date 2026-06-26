# -*- coding: utf-8 -*-
"""数据统计工具 - 数值序列的数学统计分析"""
import math
from collections import Counter
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QGroupBox
)


class StatisticsTool(QWidget):
    """数据统计工具 - 单例模式"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, parent=None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        super().__init__(parent)
        self._initialized = True
        self.setWindowTitle('数据统计分析 - MHcom')
        self.resize(680, 600)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel('数据统计分析工具')
        title.setStyleSheet('font-size:18px; font-weight:700; color:#0F172A;')
        layout.addWidget(title)

        cfg = QGroupBox('  输入数据')
        cfg_lay = QVBoxLayout(cfg)
        cfg_lay.setContentsMargins(12, 10, 12, 12)
        cfg_lay.setSpacing(8)

        self.txt_in = QPlainTextEdit()
        self.txt_in.setPlaceholderText(
            '输入数字序列，支持空格、逗号、换行分隔\n'
            '示例: 12.5 14.2 11.8 15.0 13.6'
        )
        self.txt_in.setMaximumHeight(120)
        self.txt_in.setStyleSheet(
            'QPlainTextEdit { border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px; }'
        )
        cfg_lay.addWidget(self.txt_in)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_clear = QPushButton('清空')
        btn_clear.setStyleSheet(
            'padding:6px 16px; border-radius:4px;'
            'background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1;'
        )
        btn_clear.clicked.connect(lambda: self.txt_in.clear())
        btn_row.addWidget(btn_clear)

        btn_calc = QPushButton('统计分析')
        btn_calc.setStyleSheet(
            'padding:6px 20px; border-radius:4px;'
            'background:#3B82F6; color:white; font-weight:600; border:none;'
        )
        btn_calc.clicked.connect(self._compute)
        btn_row.addWidget(btn_calc)

        cfg_lay.addLayout(btn_row)
        layout.addWidget(cfg)

        out = QGroupBox('  统计结果')
        out_lay = QVBoxLayout(out)
        out_lay.setContentsMargins(12, 10, 12, 12)
        self.txt_out = QPlainTextEdit()
        self.txt_out.setReadOnly(True)
        self.txt_out.setStyleSheet(
            'QPlainTextEdit { background:#F8FAFC; font-family: Consolas; font-size:13px;'
            'border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px; }'
        )
        out_lay.addWidget(self.txt_out)
        layout.addWidget(out, 1)

        tip = QLabel('支持描述性统计：均值、中位数、众数、方差、标准差、极值、分位数等。')
        tip.setStyleSheet('color:#64748B; font-size:12px; padding:8px;')
        tip.setWordWrap(True)
        layout.addWidget(tip)

    def _compute(self):
        text = self.txt_in.toPlainText().strip()
        if not text:
            self.txt_out.setPlainText('请输入数据')
            return
        try:
            cleaned = text.replace(',', ' ').replace('\n', ' ').replace('\t', ' ')
            nums = [float(x) for x in cleaned.split() if x]
        except ValueError as e:
            self.txt_out.setPlainText(f'数据解析错误: {e}\n请确保输入的是数字')
            return

        if not nums:
            self.txt_out.setPlainText('未找到有效数据')
            return

        try:
            result = self._calc_stats(nums)
            self._display_result(result, nums)
        except Exception as e:
            self.txt_out.setPlainText(f'计算错误: {e}')

    def _calc_stats(self, nums):
        n = len(nums)
        sorted_nums = sorted(nums)
        total = sum(nums)
        mean = total / n

        if n % 2 == 1:
            median = sorted_nums[n // 2]
        else:
            median = (sorted_nums[n // 2 - 1] + sorted_nums[n // 2]) / 2

        counts = Counter(nums)
        max_count = max(counts.values())
        if max_count > 1:
            modes = [k for k, v in counts.items() if v == max_count]
        else:
            modes = []

        variance = sum((x - mean) ** 2 for x in nums) / n
        std_dev = math.sqrt(variance)

        sample_var = sum((x - mean) ** 2 for x in nums) / (n - 1) if n > 1 else 0
        sample_std = math.sqrt(sample_var)

        min_val = sorted_nums[0]
        max_val = sorted_nums[-1]
        range_val = max_val - min_val

        def percentile(p):
            k = (n - 1) * p / 100.0
            f = int(k)
            c = f + 1 if f + 1 < n else f
            d = k - f
            return sorted_nums[f] * (1 - d) + sorted_nums[c] * d

        q1 = percentile(25)
        q3 = percentile(75)
        iqr = q3 - q1

        cv = (std_dev / mean * 100) if mean != 0 else float('inf')

        return {
            'n': n,
            'sum': total,
            'mean': mean,
            'median': median,
            'modes': modes,
            'variance': variance,
            'std_dev': std_dev,
            'sample_var': sample_var,
            'sample_std': sample_std,
            'min': min_val,
            'max': max_val,
            'range': range_val,
            'q1': q1,
            'q3': q3,
            'iqr': iqr,
            'cv': cv,
        }

    def _display_result(self, r, nums):
        lines = []
        lines.append('=' * 55)
        lines.append('  描述性统计分析报告')
        lines.append('=' * 55)
        lines.append('')
        lines.append(f'  样本数量 (N):    {r["n"]}')
        lines.append(f'  求和 (Sum):      {r["sum"]:.6f}')
        lines.append('')
        lines.append('  --- 集中趋势 ---')
        lines.append(f'  均值 (Mean):     {r["mean"]:.6f}')
        lines.append(f'  中位数 (Median): {r["median"]:.6f}')
        if r['modes']:
            modes_str = ', '.join(f'{m}' for m in r['modes'][:5])
            if len(r['modes']) > 5:
                modes_str += ' ...'
            lines.append(f'  众数 (Mode):     {modes_str}')
        else:
            lines.append(f'  众数 (Mode):     无重复值')
        lines.append('')
        lines.append('  --- 离散程度 ---')
        lines.append(f'  最小值 (Min):    {r["min"]:.6f}')
        lines.append(f'  最大值 (Max):    {r["max"]:.6f}')
        lines.append(f'  极差 (Range):    {r["range"]:.6f}')
        lines.append(f'  方差 (σ²):       {r["variance"]:.6f}')
        lines.append(f'  标准差 (σ):      {r["std_dev"]:.6f}')
        lines.append(f'  样本方差 (s²):   {r["sample_var"]:.6f}')
        lines.append(f'  样本标准差 (s):  {r["sample_std"]:.6f}')
        lines.append(f'  变异系数 (CV):   {r["cv"]:.2f}%')
        lines.append('')
        lines.append('  --- 分位数 ---')
        lines.append(f'  Q1 (25%):        {r["q1"]:.6f}')
        lines.append(f'  Q2 (50%/中位):   {r["median"]:.6f}')
        lines.append(f'  Q3 (75%):        {r["q3"]:.6f}')
        lines.append(f'  IQR (四分位距):  {r["iqr"]:.6f}')
        lines.append('')
        lines.append('=' * 55)

        self.txt_out.setPlainText('\n'.join(lines))

    def closeEvent(self, event):
        super().closeEvent(event)

