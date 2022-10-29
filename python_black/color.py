#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author:    thepoy
# @Email:     thepoy@163.com
# @File Name: color.py
# @Created:   2022-10-29 16:24:07
# @Modified:  2022-10-29 17:24:53

Style = int


class _Mode:
    """模式"""

    @property
    def normal(self) -> Style:
        """终端默认样式"""
        return 0

    @property
    def bold(self) -> Style:
        """高亮或加粗"""
        return 1

    @property
    def underline(self) -> Style:
        """下划线"""
        return 4

    @property
    def blink(self) -> Style:
        """闪烁"""
        return 5

    @property
    def invert(self) -> Style:
        """反白"""
        return 7

    @property
    def hide(self) -> Style:
        """隐藏"""
        return 8


class _ForegroundColor:
    """前景色 / 文字颜色"""

    @property
    def black(self) -> Style:
        """黑色"""
        return 30

    @property
    def red(self) -> Style:
        """红色"""
        return 31

    @property
    def green(self) -> Style:
        """绿色"""
        return 32

    @property
    def yellow(self) -> Style:
        """黄色"""
        return 33

    @property
    def blue(self) -> Style:
        """蓝色"""
        return 34

    @property
    def purple(self) -> Style:
        """紫色"""
        return 35

    @property
    def cyan(self) -> Style:
        """青色"""
        return 36

    @property
    def light_gray(self) -> Style:
        """亮灰色"""
        return 37

    @property
    def dark_gray(self) -> Style:
        """暗灰色"""
        return 90

    @property
    def light_red(self) -> Style:
        """亮红色"""
        return 91

    @property
    def light_green(self) -> Style:
        """亮绿色"""
        return 92

    @property
    def light_yellow(self) -> Style:
        """亮黄色"""
        return 93

    @property
    def light_blue(self) -> Style:
        """暗灰色"""
        return 94

    @property
    def light_purple(self) -> Style:
        """亮紫色"""
        return 95

    @property
    def light_cyan(self) -> Style:
        """亮青色"""
        return 96

    @property
    def white(self) -> Style:
        """白色"""
        return 97


class _BackgroudColor:
    """背景色"""

    @property
    def black(self) -> Style:
        """黑色"""
        return 40

    @property
    def red(self) -> Style:
        """红色"""
        return 41

    @property
    def green(self) -> Style:
        """绿色"""
        return 42

    @property
    def yellow(self) -> Style:
        """黄色"""
        return 43

    @property
    def blue(self) -> Style:
        """蓝色"""
        return 44

    @property
    def purple(self) -> Style:
        """紫色"""
        return 45

    @property
    def cyan(self) -> Style:
        """青色"""
        return 46

    @property
    def light_gray(self) -> Style:
        """亮灰色"""
        return 47

    @property
    def dark_gray(self) -> Style:
        """暗灰色"""
        return 100

    @property
    def light_red(self) -> Style:
        """亮红色"""
        return 101

    @property
    def light_green(self) -> Style:
        """亮绿色"""
        return 102

    @property
    def light_yellow(self) -> Style:
        """亮黄色"""
        return 103

    @property
    def light_blue(self) -> Style:
        """亮蓝色"""
        return 104

    @property
    def light_purple(self) -> Style:
        """亮紫色"""
        return 105

    @property
    def light_cyan(self) -> Style:
        """亮青色"""
        return 106

    @property
    def white(self) -> Style:
        """白色"""
        return 107


class DisplayStyle:
    fc = foreground_color = _ForegroundColor()
    bc = backgorud_color = _BackgroudColor()
    mode = _Mode()

    @property
    def end(self) -> Style:
        return 0

    def format_with_one_style(self, src: str, style: Style) -> str:
        """用一种样式格式化输出的文字

        Parameters
        ----------
        src : {str}
            待格式化的源文字
        style : {Style}
            要使用的样式

        Returns
        -------
        str
            格式化后的文字

        Raises
        ------
        TypeError
            源文字或样式不是要求的类型时抛异常
        """
        if type(style) != Style and type(style) != int:
            raise TypeError(f"type of `style` is {type(style)}, not Style or int")

        fmt = "\033[%dm%s\033[%dm"
        return fmt % (style, src, self.end)

    def format_with_multiple_styles(self, src: str, *styles: Style) -> str:
        """用多种样式格式化输出的文字

        Parameters
        ----------
        src : {str}
            待格式化的源文字
        *styles : {[Style]}
            要使用的样式，需要输入两种或以上的样式

        Returns
        -------
        str
            格式化后的文字

        Raises
        ------
        TypeError
            源文字或某一个样式不是要求的类型时抛异常
        """
        if len(styles) < 2:
            raise ValueError("at least 2 styles")

        styles_str = []

        for style in styles:
            if type(style) != Style and type(style) != int:
                raise TypeError(f"type of `style` is {type(style)}, not Style or int")
            styles_str.append(str(style))

        style = ";".join(styles_str)
        return f"\033[{style}m{src}\033[{self.end}m"
