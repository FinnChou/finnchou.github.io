---
layout: post
title: "色差公式的演进：从 CIELAB 到 CIEDE2000"
description: "CIELAB 的欧氏距离并不能准确反映色差。本篇梳理 CMC、CIE94 到 CIEDE2000 的演进，看每项修正对应椭圆的哪种变形；最后指出 L1、L2 损失也是一种色差，同样带着偏向。"
date: 2026-10-21 22:45:18 +0800
categories: 色彩科学
tags: [色彩科学, 色差, CIEDE2000, 均匀色空间]
math: true
image:
  path: /assets/resource/og/Color-Difference-Formulas.png
  alt: "色差公式的演进：从 CIELAB 到 CIEDE2000"
---

色差，就是两个颜色看起来差多少。[《色差与均匀色空间：CIELUV 与 CIELAB》](/posts/Uniform-Color-Space/)一文从 MacAdam 的颜色辨别椭圆讲到 1976 年的 CIELAB：在这个色空间里，色差 $\Delta E^{\ast}\_{ab}$ 就是两点之间的欧氏距离。

这个定义很朴素，用处却不止于色彩管理。训练图像网络时最常用的 L1、L2 损失，比较的也是两个像素的颜色差多少，只是空间换成了 RGB。可是 CIELAB 并不均匀，RGB 更不均匀。本篇先讲色差公式的演进：CIELAB 还剩下哪些不均匀，CMC(l:c)、CIE94、CIEDE2000 各修正了什么；再回到损失函数，看这些不均匀让它偏向哪里。

## 一、CIELAB 里的椭圆

### 椭圆还在

先把 MacAdam 的 25 个椭圆搬到 CIELAB 的 $a^{\ast}b^{\ast}$ 平面上。如果 CIELAB 是理想的均匀色空间，它们应该变成大小相同的圆。

![CIELAB a*b* 平面上的 25 个 MacAdam 椭圆，中性色附近最小，高彩度处较长，蓝紫一侧的椭圆细长](/assets/resource/Color-Difference-Formulas/macadam-ab.png){: width="820" }
_MacAdam 椭圆（1942）在 $a^{\ast}b^{\ast}$ 平面上的样子（放大 10 倍），换算方法见注释_

结果并不是圆[^macab]：

- 大小仍不一致。面积最大的椭圆约为最小的 9 倍；作为对照，$xy$ 图上约 71 倍，$u'v'$ 图上约 7.6 倍。
- 彩度越高，椭圆越长；中性色附近的椭圆最小。
- 形状也不一致。蓝～紫一侧的椭圆被拉得很长，长短轴之比可达 10 倍以上。

同样是 $\Delta E^{\ast}\_{ab} = 1$，放在灰色上与放在鲜艳的颜色上、沿彩度方向与沿色相方向，看起来都不一样大。

这不只是 MacAdam 一组数据的问题。MacAdam 的椭圆是**阈值**一级的数据，前文说成「分辨不出」的界限，严格地说是同一名观察者反复配色的标准差（MacAdam，1942）。工业上更关心**超阈值**的小色差：看得出的差别有多大，能不能接受。1980 年前后起，纺织、涂料等行业做了多组这样的目视实验，比如 BFD 数据（Luo & Rigg，1986）与 RIT-DuPont 数据（Berns et al.，1991）。在 $a^{\ast}b^{\ast}$ 平面上，两组数据的椭圆规律相当一致：中性色的椭圆很小，彩度越高椭圆越大；大多数椭圆的长轴指向中性点，唯独蓝色区域的长轴偏离中性点（Luo，2002）。

### 两条路

[《色差与均匀色空间》](/posts/Uniform-Color-Space/)一文的译者注说过，让一个数描述色差，有两条路：一是改空间，让色空间里的欧氏距离能够描述色差；二是改公式，不再用简单的欧氏距离。

CIE 推荐的 $uv$、$u'v'$ 与 CIELAB，走的都是第一条路，想通过换坐标让椭圆接近圆。但上面的对照也说明，就 MacAdam 这组数据而言，CIELAB 的椭圆并不比 $u'v'$ 图上更整齐。CIELAB 本身也只是阶段性的结果：它与 CIELUV 是从几个效果相近的方案中选出来的，为的是在更好的公式出现之前，先统一业界的做法（Robertson，1977；Robertson，1990）。

此后，CIE 推荐的色差公式改走第二条路：坐标仍用 CIELAB，但不再要求椭圆是圆，而是直接按椭圆来量距离。

## 二、改公式：按椭圆量距离

### 拆成明度、彩度、色相

大多数椭圆的轴大致沿彩度方向和色相方向，所以先把 $a^{\ast}b^{\ast}$ 换成极坐标：

$$ C^{\ast} = \sqrt{a^{\ast 2} + b^{\ast 2}}, \qquad h = \arctan\frac{b^{\ast}}{a^{\ast}} $$

$C^{\ast}$ 是**彩度**，即到中性轴的距离；$h$ 是**色相角**，从 $a^{\ast}$ 轴正方向逆时针量起。两个颜色记作 1、2，有参考色时，1 为参考色。色差随之拆成三个分量，平方和不变：

$$ \Delta E^{\ast}_{ab} = \sqrt{(\Delta L^{\ast})^2 + (\Delta C^{\ast})^2 + (\Delta H^{\ast})^2}, \qquad \Delta H^{\ast} = 2\sqrt{C^{\ast}_1 C^{\ast}_2}\,\sin\frac{\Delta h}{2} $$

$\Delta L^{\ast}$、$\Delta C^{\ast}$ 分别是明度差与彩度差。$\Delta H^{\ast}$ 是**色相差**，沿切向，即与径向垂直。它不是色相角之差 $\Delta h$，而是把 $\Delta h$ 折算成与 $a^{\ast}$、$b^{\ast}$ 同单位的长度：同样转过 10°，彩度越高，$\Delta H^{\ast}$ 越大。

![a*b* 平面上参考色 P 与 Q 的色差，分解为沿径向的彩度差 ΔC* 与沿切向的色相差 ΔH*](/assets/resource/Color-Difference-Formulas/lch-decomposition.png){: width="640" }
_模式图：$a^{\ast}b^{\ast}$ 平面上的色差拆成彩度差与色相差_

然后三个分量各除以一个权重：

$$ \Delta E = \sqrt{\left(\frac{\Delta L^{\ast}}{k_L S_L}\right)^2 + \left(\frac{\Delta C^{\ast}}{k_C S_C}\right)^2 + \left(\frac{\Delta H^{\ast}}{k_H S_H}\right)^2} $$

$S_L$、$S_C$、$S_H$ 称为**权重函数**，随颜色所在的位置变化；$k_L$、$k_C$、$k_H$ 称为**参数因子**，随观察条件与行业习惯而定。$\Delta E = 1$ 的点构成一个椭球，三个半轴分别是 $k_L S_L$、$k_C S_C$、$k_H S_H$。权重函数的任务，就是让这个椭球在各处与实验的椭圆相符。下面三个公式的区别，主要在权重函数怎么取。

### CMC(l:c)

CMC(l:c) 出自英国染色家协会（SDC）的颜色测量委员会，由 Clarke、McDonald 与 Rigg 在 1984 年发表，主要用于纺织业（Clarke et al.，1984）。它取 $k_L = l$、$k_C = c$、$k_H = 1$，三个权重都由参考色的 $L^{\ast}$、$C^{\ast}$、$h$ 算出：

$$ S_L = \begin{cases} 0.511, & L^{\ast} < 16 \\ \dfrac{0.040975\,L^{\ast}}{1 + 0.01765\,L^{\ast}}, & L^{\ast} \ge 16 \end{cases} \qquad S_C = \frac{0.0638\,C^{\ast}}{1 + 0.0131\,C^{\ast}} + 0.638 $$

$$ S_H = S_C\,(F\,T + 1 - F), \qquad F = \sqrt{\frac{(C^{\ast})^4}{(C^{\ast})^4 + 1900}}, \qquad T = \begin{cases} 0.56 + \lvert 0.2\cos(h + 168^\circ) \rvert, & 164^\circ < h < 345^\circ \\ 0.36 + \lvert 0.4\cos(h + 35^\circ) \rvert, & \text{其他} \end{cases} $$

$S_L$ 随明度增大，越亮的颜色，同样的 $\Delta L^{\ast}$ 折算出的色差越小。$S_C$ 随彩度增大并逐渐饱和，对应「彩度越高，椭圆越大」。$S_H$ 是 $S_C$ 再乘 $FT + 1 - F$：$T$ 随色相变化；$F$ 在低彩度时接近 0，乘数随之接近 1，$T$ 只在彩色上起作用。判断能否接受时常取 CMC(2:1)，允许明度差大一些；判断能否看出时取 CMC(1:1)。

因为权重只按参考色计算，CMC 是**不对称**的：把参考色与试样对调，结果会变。不过 CMC 本来只用于小色差，差得小时这个问题并不明显（Luo，2002）。

### CIE94

CIE94 由 CIE 在 1994 年推荐试用，1995 年发布在技术报告 CIE 116-1995 中。它沿用 CMC 的结构，权重主要依据 RIT-DuPont 数据重新拟合（Luo，2002），并简化为：

$$ S_L = 1, \qquad S_C = 1 + 0.045\,C^{\ast}, \qquad S_H = 1 + 0.015\,C^{\ast} $$

式中 $C^{\ast}$ 取参考色的彩度。明度权重成了常数，与色相有关的因子也去掉了；$S_H$ 比 $S_C$ 增得慢，椭圆因此沿径向较长。

CIE94 还引入了**参考条件**（Luo，2002）：照明、背景、样品的大小与排列、色差的大小都有规定，在这些条件下参数因子取 1，条件不同时再调整。以 CIEDE2000 的现行标准为例，规定的样品是两块直接相邻、颜色均匀的色块，色差在 5 个 CIELAB 单位以内[^ref]。色差公式给出的数，只有在这样的条件下才有确定的含义。

### CIEDE2000

CMC 与 CIE94 的椭圆都严格指向中性点，所以在蓝色区域与实验不符；两者在灰色附近也有误差，对明度差的预测则互相矛盾（Luo，2002）。CIE 的技术委员会 TC 1-47 综合四组超阈值数据，在 2001 年提出 CIEDE2000（CIE 142-2001），Luo、Cui 与 Rigg 同年发表了它的推导（Luo et al.，2001）。它记作 $\Delta E_{00}$，现行标准为 ISO/CIE 11664-6:2022。

计算分三步。

第一步，修正 $a^{\ast}$。按两个颜色彩度的平均 $\bar{C}^{\ast}$ 求出 $G$，把 $a^{\ast}$ 放大 $1 + G$ 倍，再用新的 $a'$ 重算彩度与色相角：

$$ G = 0.5\left(1 - \sqrt{\frac{\bar{C}^{\ast 7}}{\bar{C}^{\ast 7} + 25^7}}\right), \qquad a'_i = (1 + G)\,a^{\ast}_i, \qquad C'_i = \sqrt{a'^2_i + b^{\ast 2}_i}, \qquad h'_i = \arctan\frac{b^{\ast}_i}{a'_i} $$

第二步，求三个分量的差：

$$ \Delta L' = L^{\ast}_2 - L^{\ast}_1, \qquad \Delta C' = C'_2 - C'_1, \qquad \Delta H' = 2\sqrt{C'_1 C'_2}\,\sin\frac{\Delta h'}{2} $$

式中 $\Delta h' = h'_2 - h'_1$，换算到 $-180^\circ$～$180^\circ$ 之间。

第三步，求权重，合成色差。权重都按两个颜色的平均值 $\bar{L}'$、$\bar{C}'$、$\bar{h}'$ 计算。其中平均色相 $\bar{h}'$ 取两个色相角在圆周上的平均：两者相差不超过 180° 时直接平均；超过 180° 时，先给较小的一个加上 360° 再平均，结果超过 360° 时减去 360°。

$$ S_L = 1 + \frac{0.015\,(\bar{L}' - 50)^2}{\sqrt{20 + (\bar{L}' - 50)^2}}, \qquad S_C = 1 + 0.045\,\bar{C}', \qquad S_H = 1 + 0.015\,\bar{C}'\,T $$

$$ T = 1 - 0.17\cos(\bar{h}' - 30^\circ) + 0.24\cos(2\bar{h}') + 0.32\cos(3\bar{h}' + 6^\circ) - 0.20\cos(4\bar{h}' - 63^\circ) $$

$$ R_T = -2\sqrt{\frac{\bar{C}'^7}{\bar{C}'^7 + 25^7}}\;\sin\left[60^\circ \exp\left(-\left(\frac{\bar{h}' - 275^\circ}{25^\circ}\right)^2\right)\right] $$

$$ \Delta E_{00} = \sqrt{\left(\frac{\Delta L'}{k_L S_L}\right)^2 + \left(\frac{\Delta C'}{k_C S_C}\right)^2 + \left(\frac{\Delta H'}{k_H S_H}\right)^2 + R_T\,\frac{\Delta C'}{k_C S_C}\,\frac{\Delta H'}{k_H S_H}} $$

相对 CIELAB，CIEDE2000 有五项修正（Luo，2002），前三项 CMC 与 CIE94 已有类似的形式，后两项是新加的：

1. $S_L$：改为以 $L^{\ast} = 50$ 为最低点的 V 字形，两端约为 1.75。CMC 的明度权重随明度单调增大，CIE94 取常数，两者矛盾；补做的实验显示，明度权重只在 $L^{\ast} > 50$ 时随明度增大（Luo，2002）[^sl]。
2. $S_C$：形式同 CIE94，只是彩度改用修正后的 $C'$。
3. $S_H$：重新带上与色相有关的因子 $T$，它在 0.36～1.57 之间变化。
4. $R_T$：只在 $\bar{h}'$ 约 275° 的蓝色区域起作用，乘在彩度差与色相差的交叉项上，使那里的椭圆偏转并被拉长。蓝色区域的椭圆偏离中性点，在七项独立研究中都能看到（Luo，2002）。
5. $G$：彩度接近 0 时 $G \approx 0.5$，$a^{\ast}$ 放大到 1.5 倍，灰色附近同样的红－绿差折算出更大的色差，用来改善对灰色的预测（Luo et al.，2001）；彩度高时 $G \to 0$，不再修正。

权重改按两个颜色的平均值计算，CIEDE2000 因此是对称的，对调两个颜色，结果不变。

平均色相这一步也带来一个问题。两个颜色的色相角相差约 180° 时，比如分处中性点两侧的两个近灰色，相差略小于与略大于 180°，算出的 $\bar{h}'$ 会差半个圆周，$T$ 与 $R_T$ 随之跳变。这个不连续对色差评价影响很小，却不利于要求函数连续可导的优化方法（Sharma et al.，2005）。

### 三个公式放在一起

![三个公式的权重函数：左为明度权重随 L* 变化，中为彩度权重随 C* 变化，右为 C*=40 时色相权重随色相角变化](/assets/resource/Color-Difference-Formulas/weighting-functions.png){: width="820" }
_CMC(l:c)、CIE94、CIEDE2000 的权重函数，由公式算出_

权重函数的演进一目了然：明度权重从「越亮越宽容」到常数，再到以中灰为中心的 V 字形；彩度权重从分式简化为线性；色相权重里与色相有关的因子，先被去掉，又以新的形式加回来。

把 CIEDE2000 在 $a^{\ast}b^{\ast}$ 平面上画成等色差轮廓，各项修正的效果就更直观：

![CIEDE2000 在 L*=50 的 a*b* 平面上 ΔE00=1 的等色差轮廓，彩度越高轮廓越大，蓝色区域的轮廓斜着拉长，中性色的轮廓沿 a* 方向被压扁](/assets/resource/Color-Difference-Formulas/ciede2000-contours.png){: width="820" }
_CIEDE2000 的等色差轮廓（实线，$\Delta E\_{00} = 1$）与 $\Delta E^{\ast}\_{ab} = 1$ 的圆（虚线），均放大 3 倍_

图中三处标注，分别对应 $S_C$、$G$ 与 $R_T$。$C^{\ast} = 50$ 时，径向半轴约 3.3，切向只有 1.4～2.0；$h = 270^\circ$ 处长短轴之比约为 5 倍，去掉 $R_T$ 只有约 2 倍。

## 三、回到色空间

改公式这条路有个代价：从 CMC 起，这些公式都只回答两个颜色差多少，不对应一个色空间（Luo，2002）。插值、求平均、做色域映射，需要的恰恰是坐标。此后也有研究回到第一条路，在色貌模型（描述颜色在不同观察条件下看起来如何）的基础上构造均匀色空间，比如 CAM16-UCS（Li et al.，2017），它也只是近似均匀。

从 1942 年的椭圆算起，色差研究在「改空间」与「改公式」之间走了一个来回，绕不开的始终是同一件事：要在一个色空间里取欧氏距离，前提是这个空间足够均匀。

## 四、损失函数里的色差

### L1、L2 也是色差

这个前提，在今天最常见的一种「色差」里同样绕不开。训练图像复原、增强一类的网络时，最常用的损失函数是逐像素的 L1 与 L2：

$$ \mathcal{L}_1 = \frac{1}{N}\sum_{p} \lVert \hat{\mathbf{y}}_p - \mathbf{y}_p \rVert_1, \qquad \mathcal{L}_2 = \frac{1}{N}\sum_{p} \lVert \hat{\mathbf{y}}_p - \mathbf{y}_p \rVert_2^2 $$

式中 $\hat{\mathbf{y}}_p$、$\mathbf{y}_p$ 分别是网络输出与目标在像素 $p$ 处的 RGB 向量，$N$ 是像素数。这里的 RGB 可以是**线性 sRGB**，即与光的强度成正比的值；也可以是经过伽马编码的 **sRGB 编码值**，8 位图像文件里存的是后者（传递函数见[《白点切换》](/posts/Chromatic-Adaptation/)一文）。

单看一个像素，$\lVert \hat{\mathbf{y}}_p - \mathbf{y}_p \rVert_2$ 就是两个颜色在 RGB 空间里的欧氏距离，与 $\Delta E^{\ast}\_{ab}$ 的形式完全相同，只是 CIELAB 换成了 RGB；L2 损失取它的平方，L1 则换成三个分量之差的绝对值之和。训练网络时，我们其实一直在用色差，只是用的是「RGB 里的 $\Delta E$」。有的工作训练时用 RGB 上的均方误差，评价时却报告 CIELAB 里的 $\Delta E$（Zeng et al.，2022）。

以 L2 为例，在 RGB 上取距离，等于假定同样大小的数值差，不论落在哪个颜色上、朝哪个方向，都是同样大的色差，也就是假定 RGB 是均匀色空间。前三节已经说明，这个假定连 CIELAB 都只能近似做到。

### 偏在哪里

偏多少，可以直接量。在基准色周围沿随机方向把 RGB 值偏移同样的长度 0.004（向量长度，约为 8 位图像的 1 个灰阶），再用 CIEDE2000 换算成色差，当作人眼感受的近似；这样小的偏移，色差基本落在 CIEDE2000 适用的 0～5 以内：

![三幅图：RGB 偏移 0.004 折算成的 ΔE00 随灰色明度、随彩度、随色相角的变化；左右两图比较 sRGB 编码值与线性 sRGB，中图为 sRGB 编码值上绿、紫两种色相](/assets/resource/Color-Difference-Formulas/rgb-error-vs-de2000.png){: width="820" }
_RGB 上同样长度的误差，按 CIEDE2000 折算成的色差。中图取绿、紫两种色相_

- 线性 sRGB：主要差在明度。同样的误差放在暗处，比放在亮处显眼得多，灰色 $L^{\ast} = 20$ 与 $L^{\ast} = 95$ 相差约 9 倍。
- sRGB 编码值：伽马编码大体抹平了明度上的差别，但灰色上的误差比 $C^{\ast} = 60$ 的鲜艳颜色上显眼约 3 倍；只换色相，约差 1.4 倍[^hue]；同一个颜色朝不同方向偏移，5%～95% 分位之间也差 3 倍多。

这里假定误差朝各个方向的机会均等。如果误差是三个通道同增同减、只改变亮度，sRGB 编码值上灰色与鲜艳颜色的差别几乎消失；而彩度上的差别，大半来自 CIELAB 本身的不均匀，由 CIEDE2000 的彩度权重显现出来[^iso]。

L1、L2 只看 RGB 上的误差，不看这份误差在人眼看来有多大。网络总有拟合不了的误差，损失函数决定这些误差留在哪里：在线性 sRGB 上，L2 眼里一样大的误差，留在暗部比留在亮部显眼得多；在 sRGB 编码值上，留在灰色与低彩度颜色上，比留在鲜艳颜色上显眼。这就是 L1、L2 损失的偏向。

### 两种改法

要减小这种偏向，办法也是色差研究的那两条路：改空间，或者改公式。

改空间，就是不在原始的 RGB 上处理颜色，这早有先例。Reinhard 等人做图像之间的颜色迁移时，先换到对视锥响应取对数、再旋转得到的 $l\alpha\beta$ 空间，为的是三个通道几乎不相关，可以分开处理（Reinhard et al.，2001）。对 RAW 与 HDR 数据，Ke 等人的结论是先用感知上更均匀的传递函数编码，让网络的输入、输出都在编码后的空间里，只在算损失时编码效果并不明显（Ke et al.，2025）。Chen 等人则用照片数据学出一个特征空间，在其中取欧氏距离作为色差（Chen et al.，2023）。

改公式，就是不再取简单的欧氏距离，而用更接近人眼的色差。损失函数只需要一个距离，不需要坐标，第三节说的那个代价在这里不成问题。Zhao 等人研究对抗扰动时认为，RGB 上的距离与人眼的感受相去甚远，于是直接用 CIEDE2000 来衡量扰动的大小（Zhao et al.，2020）。

两种改法也各有局限。换到 CIELAB，偏向会缩小但不会消失：比较各基准色上 $\Delta E\_{00}$ 的中位数，最大与最小之比，线性 sRGB 约 15 倍，sRGB 编码值约 4.4 倍，CIELAB 仍有约 2.5 倍[^lab]。CIEDE2000 更接近人眼，却有第二节说的不连续点，而且是为两块相邻的均匀色块标定的，照片并不满足这个条件，这也是 Chen 等人另起炉灶的原因。

回头看，逐像素的 L2 就是 1976 年那个最朴素的色差公式，只是放进了一个更不均匀的空间，L1 则是它的近亲。色差研究几十年来处理的问题，在损失函数里并没有消失。

## 五、小结

- MacAdam 椭圆在 CIELAB 里仍然大小不一、形状各异，工业上的超阈值数据也是如此。
- CMC(l:c)、CIE94、CIEDE2000 改走「改公式」的路：把色差拆成明度、彩度、色相三个分量，各除以一个权重，按椭圆量距离。
- 改公式不再对应色空间，CAM16-UCS 等又回到「改空间」的路上。
- 逐像素的 L2 与 $\Delta E^{\ast}\_{ab}$ 同形，只是空间换成了 RGB，同样大小的误差看起来可以相差数倍。改空间、改公式都能减小这种偏向，但都不彻底。

## 参考文献

1. D. L. MacAdam. *Visual Sensitivities to Color Differences in Daylight*. Journal of the Optical Society of America, 32(5): 247–274, 1942. [DOI](https://doi.org/10.1364/JOSA.32.000247)
2. M. R. Luo, B. Rigg. *Chromaticity-Discrimination Ellipses for Surface Colours*. Color Research & Application, 11(1): 25–42, 1986. [DOI](https://doi.org/10.1002/col.5080110107)
3. R. S. Berns, D. H. Alman, L. Reniff, et al. *Visual Determination of Suprathreshold Color-Difference Tolerances Using Probit Analysis*. Color Research & Application, 16(5): 297–316, 1991. [DOI](https://doi.org/10.1002/col.5080160505)
4. M. R. Luo. *Development of Colour-Difference Formulae*. Review of Progress in Coloration and Related Topics, 32: 28–39, 2002. [DOI](https://doi.org/10.1111/j.1478-4408.2002.tb00248.x)
5. A. R. Robertson. *The CIE 1976 Color-Difference Formulae*. Color Research & Application, 2(1): 7–11, 1977. [DOI](https://doi.org/10.1002/j.1520-6378.1977.tb00104.x)
6. A. R. Robertson. *Historical Development of CIE Recommended Color Difference Equations*. Color Research & Application, 15(3): 167–170, 1990. [DOI](https://doi.org/10.1002/col.5080150308)
7. F. J. J. Clarke, R. McDonald, B. Rigg. *Modification to the JPC79 Colour-Difference Formula*. Journal of the Society of Dyers and Colourists, 100(4): 128–132, 1984. [DOI](https://doi.org/10.1111/j.1478-4408.1984.tb00969.x)
8. CIE 116-1995. *Industrial Colour-Difference Evaluation*. [DOI](https://doi.org/10.25039/TR.116.1995)
9. CIE 142-2001. *Improvement to Industrial Colour-Difference Evaluation*. [DOI](https://doi.org/10.25039/TR.142.2001)
10. M. R. Luo, G. Cui, B. Rigg. *The Development of the CIE 2000 Colour-Difference Formula: CIEDE2000*. Color Research & Application, 26(5): 340–350, 2001. [DOI](https://doi.org/10.1002/col.1049)
11. ISO/CIE 11664-6:2022. *Colorimetry — Part 6: CIEDE2000 Colour-Difference Formula*.
12. G. Sharma, W. Wu, E. N. Dalal. *The CIEDE2000 Color-Difference Formula: Implementation Notes, Supplementary Test Data, and Mathematical Observations*. Color Research & Application, 30(1): 21–30, 2005. [DOI](https://doi.org/10.1002/col.20070)
13. C. Li, Z. Li, Z. Wang, et al. *Comprehensive Color Solutions: CAM16, CAT16, and CAM16-UCS*. Color Research & Application, 42(6): 703–718, 2017. [DOI](https://doi.org/10.1002/col.22131)
14. H. Zeng, J. Cai, L. Li, Z. Cao, L. Zhang. *Learning Image-Adaptive 3D Lookup Tables for High Performance Photo Enhancement in Real-Time*. IEEE Transactions on Pattern Analysis and Machine Intelligence, 44(4): 2058–2073, 2022. [DOI](https://doi.org/10.1109/TPAMI.2020.3026740)
15. E. Reinhard, M. Ashikhmin, B. Gooch, P. Shirley. *Color Transfer between Images*. IEEE Computer Graphics and Applications, 21(5): 34–41, 2001. [DOI](https://doi.org/10.1109/38.946629)
16. A. Y. Ke, L. Luo, X. Xiang, et al. *Training Neural Networks on RAW and HDR Images for Restoration Tasks*. CVPR Workshops, 2025: 801–810. [DOI](https://doi.org/10.1109/CVPRW67362.2025.00085)
17. H. Chen, Z. Wang, Y. Yang, Q. Sun, K. Ma. *Learning a Deep Color Difference Metric for Photographic Images*. CVPR, 2023: 22242–22251.
18. Z. Zhao, Z. Liu, M. Larson. *Towards Large yet Imperceptible Adversarial Image Perturbations with Perceptual Color Distance*. CVPR, 2020: 1036–1045. [DOI](https://doi.org/10.1109/CVPR42600.2020.00112)

> **数据来源**：MacAdam 椭圆同[《色差与均匀色空间》](/posts/Uniform-Color-Space/)一文，取 Wyszecki & Stiles《Color Science》第 2 版表 2(5.4.1) 的拟合值。CIEDE2000 的实现用 Sharma 等人公布的 34 组测试数据校验，最大偏差 $5 \times 10^{-5}$。RGB 误差的统计中，sRGB 按 IEC 61966-2-1 换算，白点取 D65，每个基准色取 4000 个均匀分布的随机方向。
{: .prompt-info }

## 注释

[^macab]: **把 MacAdam 椭圆换到 $a^{\ast}b^{\ast}$。** 把每个椭圆的边界逐点换算到 $a^{\ast}b^{\ast}$，白点取 D65，$Y$ 取 $L^{\ast} = 50$ 对应的值。MacAdam 的实验亮度恒定，色度不变时 $a^{\ast}$、$b^{\ast}$ 都与 $Y$ 的立方根成正比，$Y$ 取别的值只会把整张图等比缩放（$L^{\ast}$ 不低于约 24 时成立）。

[^ref]: **参考条件。** ISO/CIE 11664-6:2022 为 CIEDE2000 规定的参考条件是：D65 模拟光源，照度 1000 lx，背景为 $L^{\ast} = 50$ 的均匀中灰，物体色模式，一对样品的视角大于 4° 且直接相邻，色差在 0～5 个 CIELAB 单位以内，颜色均匀、看不出纹理。

[^sl]: **明度权重的争议。** CMC 的明度权重来自缝纫线的可接受性评定，涂料样品的实验也得到过同样的趋势，新实验却得出 V 字形，Luo 称这是一个谜。他推测最低点落在 $L^{\ast} = 50$ 附近，可能是因为明度与背景相近时差别显得格外大，即 crispening 效应（Luo，2002）。CIEDE2000 参考条件规定的背景，也正是 $L^{\ast} = 50$ 的中灰。

[^hue]: **绿与紫。** 1.4 倍是 $L^{\ast} = 50$、$C^{\ast} = 25$ 时绕色相一圈的最大与最小之比，最大在黄橙色，最小在绿色。单比绿（$h = 140^\circ$）与紫（$h = 305^\circ$），sRGB 编码值上紫色略显眼（0.37 对 0.34），线性 sRGB 上反而是绿色（0.46 对 0.41）。

[^iso]: **误差方向的前提。** sRGB 编码值上，$L^{\ast} = 50$ 的灰色与 $C^{\ast} = 60$ 的绿色或紫色相比：误差方向各向同性时，$\Delta E\_{00}$ 差约 3 倍；误差沿 (1, 1, 1) 方向时只差 1.03～1.06 倍；方向各向同性但改用 $\Delta E^{\ast}\_{ab}$ 衡量时，差 1.1～1.3 倍。

[^lab]: **三种空间的比较。** 基准色取 sRGB 色域内的 88 个（$L^{\ast}$ 为 30～90，$C^{\ast}$ 为 0～60，色相每隔 30°，灰色每种明度只取一个），在 RGB 上偏移 0.004，或在 CIELAB 上偏移 1 个单位。
