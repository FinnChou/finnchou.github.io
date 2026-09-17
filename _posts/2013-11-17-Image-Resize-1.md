---
layout: post
title: "Image Resize : 数字图像的整数倍扩大"
date:  2013-11-17 14:59:52 +0800
categories: 数字图像处理
tags: [图像处理, 图像重采样]
math: true
image:
  path: /assets/resource/og/Image-Resize-1.png
  alt: "Image Resize : 数字图像的整数倍扩大"
---

### 引言
在数字图像处理领域，我们经常需要处理不同平台或仪器获取的图像。这些图像在大小（分辨率）和数据类型上往往存在显著差异。分辨率是数字图像质量的重要指标，它表示图像中像素的数量。像素数量越多，图像就能表现出更丰富的细节。

本文主要探讨数字图像的整数倍扩大问题，即如何提高图像的分辨率。本质上，图像扩大处理的核心在于如何确定新增像素的值，这实际上是一个插值问题。我们将首先理解理想插值的概念，然后分析几种常用的插值方法，并对其性能进行全面评估。

本文参考了貴家仁志先生在**よくわかる動画・静止画の処理技術**系列中的1-3期内容[^footnote1][^footnote2][^footnote3]。

### 理想插值处理的理论基础
为了深入理解插值处理，我们先从模拟信号的角度进行分析。假设我们有一个模拟信号 $f(t)$，如下图所示：

![Example Analog Signal](/assets/resource/Image-Resize-1/example_analog_signal.jpeg){: width="450" height="450"}

左图展示了模拟信号在时域的表现，右图则是其频谱。虽然图像略显粗糙，但这不影响我们的分析。对这个信号进行采样，可以得到：

$$
\begin{aligned}
\stackrel{\sim}{f}(t) &= f(t)S_{\Delta T}(t) \\ 
&= f(t) \sum_{n=-\infty}^{\infty} \delta(t - n \Delta T)
\end{aligned}
$$

其中，$ \sum_{n=-\infty}^{\infty} \delta(t - n \Delta T)$ 表示以 $\Delta T$ 为时间间隔的冲击串信号。对采样后的信号 $\stackrel{\sim}{f}(t)$ 进行连续时间傅立叶变换，可得：

$$
\begin{aligned}
\stackrel{\sim}{F_{\Delta T}}(u) &= F(\mu) \star S(\mu) \\ 
&= \frac{1}{\Delta T} \sum_{n=-\infty}^{\infty} F(\mu - \frac{n}{\Delta T})
\end{aligned}
$$

观察上式，我们可以发现离散信号的振幅谱呈现周期性变化，如下图所示：

![Example Digital Signal](/assets/resource/Image-Resize-1/example_digital_signal.jpeg){: width="450" height="450"}

这里，我们使用 $\Delta T$ 作为采样时间间隔。通常，我们会将振幅谱归一化，使横轴变为归一化频率。归一化后的振幅谱中，相邻波峰之间的频率差为 $2\pi$。

为了说明理想插值的概念，我们考虑两个不同的采样信号。首先，当采样间隔为 $\Delta T = \frac{1}{2\mu_{m}}$ 时，得到信号①：

![Digital Signal Sample 1](/assets/resource/Image-Resize-1/digital_signal_sample_1.jpeg){: width="450" height="450"}

然后，将采样间隔减小一半（即采样频率提高一倍），即 $\Delta T = \frac{1}{4\mu_{m}}$，得到信号②：

![Digital Signal Sample 2](/assets/resource/Image-Resize-1/digital_signal_sample_2.jpeg){: width="450" height="450"}

对比这两个信号，我们可以发现：
- 两个信号的波峰之间的归一化频率差都是 $2\pi$
- 信号②的振幅是信号①的两倍

因此，理想插值处理的定义是：如果能够通过某种处理将信号①转换为信号②，这种处理就称为理想插值。如下图所示：

![Ideal Interpolation](/assets/resource/Image-Resize-1/ideal_interpolation.jpeg){: width="450" height="450"}

从频域角度观察理想插值处理，如下图所示：

![Frequency Domain Analysis](/assets/resource/Image-Resize-1/frequency_domain_analysis.jpeg){: width="600" height="600"}

左图是信号①的频谱，右图是信号②的频谱。理想插值操作的目标是将左侧频谱转换为右侧频谱。

实现这一目标的关键步骤是：在信号①的相邻采样点之间插入一个数值为零的采样点。这个操作相当于在频率轴上进行了2倍的缩放，得到的新信号频谱如中间图所示。

> 推论： 在信号的相邻采样点之间插入 $U$ 个数值为零的采样点，相当于在频率轴上进行了 $U+1$ 倍的缩放。
{: .prompt-tip }

插入零值采样点后，新信号在频率轴上已经与目标信号对齐。如果能够将中间信号频谱中 $\pi$ 处的成分完全衰减，并将剩余部分放大2倍，就能得到目标信号。这种在频域中同时进行衰减和放大的操作，正是滤波器的作用。因此，实现理想插值需要如下所示的滤波器：

![Ideal Interpolation Filter](/assets/resource/Image-Resize-1/ideal_interpolation_filter.jpeg){: width="450" height="450"}

根据上图滤波器的振幅特性，我们可以看出实现理想插值需要理想滤波器。然而，正如我们在数字信号处理中所知，由于理想滤波器的单位冲击响应是无限的，因此理想滤波器是无法实现的。这意味着理想插值处理也是无法实现的，我们只能通过接近理想滤波器的方法来实现。因此，插值方法的好坏可以通过其等效滤波器的振幅特性与理想滤波器的接近程度来判断。

### 常用插值方法分析

#### 零次保持法
零次保持法，也称为最近邻插值法，是最简单的插值方法。

![Zero-Order Hold](/assets/resource/Image-Resize-1/zero_order_hold.jpeg){: width="450" height="450"}

左图是输入信号$f(t)$，右图是输出信号$g(t)$。这种方法相当于如下的一维滤波器：

$$
\begin{aligned}
h(t) = \underbrace{[1, 1, 1, ..., 1]}_{\text{U个}}
\end{aligned}
$$

#### 线性插值法
线性插值法通过将相邻信号点用直线连接，并取直线上的值作为内插值。

![Linear Interpolation](/assets/resource/Image-Resize-1/linear_interpolation.jpeg){: width="450" height="450"}

左图是输入信号$f(t)$，右图是输出信号$g(t)$。这种方法相当于如下的一维滤波器：

$$
\begin{equation}
h(t) = \left \{
\begin{array}{l}
1 - |t|, 0 \le |t| < 1 \\
0, 1 \le |t| \\ 
\end{array}
\right.
\end{equation}
$$

当扩大倍数为$U$时，$t \in [-1, 1]$，步进值为$1/U$，得到所需的滤波器单位冲击响应。例如，当$U=2$时，$h(t) = [0.5 1 0.5]$。

#### Cubic Convolution插值法
三次卷积插值法使用如下的一维滤波器：

$$
\begin{equation}
h(t) = \left \{
\begin{array}{l}
(a + 2)|t|^3 - (a+3)|t|^2 + 1, & 0 \le |t| < 1 \\
a|t|^3 - 5a|t|^2 + 8a|t| - 4a, & 1 \le |t| < 2 \\
0, & 2 \le |t| \\ 
\end{array}
\right.
\end{equation}
$$

与线性插值法类似，当扩大倍数为$U$时，$t \in [-2, 2]$，步进值为$1/U$，得到所需的滤波器单位冲击响应。参数a用于调整插值性能，如下图所示：

![Cubic Convolution Interpolation](/assets/resource/Image-Resize-1/cubic_convolution_interpolation.jpeg){: width="450" height="450"}

#### B-Spline插值法
B-Spline插值法使用如下的一维滤波器：

$$
\begin{equation}
h(t) = \left \{
\begin{array}{l}
\frac{1}{2}|t|^3 - |t|^2 + \frac{2}{3}, & 0 \le |t| < 1 \\
-\frac{1}{6}|t|^3 + |t|^2 - 2|t| + \frac{4}{3}, & 1 \le |t| < 2 \\
0, & 2 \le |t| \\ 
\end{array}
\right.
\end{equation}
$$

### 插值方法性能对比
将上述四种方法的等效滤波器和理想滤波器的振幅特性绘制如下：

![Amplitude Characteristics](/assets/resource/Image-Resize-1/amplitude_characteristics.jpeg){: width="450" height="450"}

通过分析上图，我们可以得出以下结论：
1. 零次保持法（最邻近插值法）的效果最差，其滤波器与理想滤波器差异最大
2. 线性插值法比零次保持法更接近理想滤波器，因此效果更好
3. 三次卷积插值法更接近理想滤波器，性能优于线性插值法。但其单位冲击响应存在负值，可能导致"振铃"现象，需要谨慎调整参数a
4. B-spline插值法在高频特性上最接近理想滤波器，阻带的抑制效果最好，但其低频特性与理想滤波器差异最大，通带内的衰减会使结果偏模糊

### 实验验证与结果分析

#### 实验图像准备
为了验证不同插值方法的性能，我们需要准备实验用的图像。参考第二节中通过不同采样频率获得信号①和②的方法，我们制作了两张测试图像。其中图像②是图像①的理想插值结果。图像制作方法如下：

![Test Image Generation](/assets/resource/Image-Resize-1/test_image_generation.jpeg){: width="600" height="600"}

通过上述方法，我们得到了两张分辨率分别为256×256和512×512的测试图像：

![Test Images](/assets/resource/Image-Resize-1/test_images.jpeg){: width="450" height="450"}

#### 实验流程
本次实验主要实现图像2倍放大。为了评估插值效果，我们将放大后的图像与目标图像进行差分运算，得到差分图像。

![Experimental Process](/assets/resource/Image-Resize-1/experimental_process.jpeg){: width="450" height="450"}

我们使用SAD（Sum of Absolute Difference，绝对差值和）作为评价指标。SAD值越大，表示插值效果越差。

$$
\begin{aligned}
R_{SAD} = \sum_{j=0}^{N-1} \sum_{i=0}^{M-1} (|g(x,y) - \stackrel{\sim}{f}(x,y)|)
\end{aligned}
$$

#### 实验结果
不同插值方法的实验结果如下：

![Experimental Results](/assets/resource/Image-Resize-1/experimental_results.jpeg){: width="450" height="450"}

#### Matlab实现代码
```matlab
close all;
clear all;
clc;

f = imread('./cheer/maru_256(cheer).tif');
f_Goal = imread('./cheer/maru_512(cheer).tif');
f = mat2gray(f,[0 255]);
f_Goal = mat2gray(f_Goal,[0 255]);

U = 2;  %拡大率　

[M,N] = size(f);
g_hold = zeros((M*U),(N*U));
H_hold = ones(1,U);

for x = 0:1:M-1     
   for y = 0:1:N-1
       g_hold((U*x)+1,(U*y)+1) = f(x+1,y+1); 
   end
end

for x = 1:1:U*M 
    g_hold(x,:) = filter(H_hold,1,g_hold(x,:));
end
for y = 1:1:U*N 
    g_hold(:,y) = filter(H_hold,1,g_hold(:,y));
end

g_hold_diff = zeros((M*U),(N*U));
for x = 1:1:(M*U)     
   for y = 1:1:(N*U)
       g_hold_diff(x,y) = abs(f_Goal(x,y) - g_hold(x,y)); 
   end
end

SAD_hold = sum(sum(g_hold_diff))
%SSD_hold = sum(sum(g_hold_diff .^2))
%MSE_hold = sum(sum(g_hold_diff .^2))/((M*U)*(M*U));
%PSNR_hold = 10*log10((1*1)/MSE_hold)

figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image (256x256)');

figure();
subplot(1,2,1);
imshow(g_hold,[0 1]);
xlabel('a).Ruselt of hold (512x512)');

subplot(1,2,2);
imshow(g_hold_diff,[0 1]);
xlabel('b).Difference image (512x512)');

figure();
w = 0:0.01:pi;
Xejw_1 = freqz(H_hold,1,w);
plot(w,abs(Xejw_1));
axis([0,pi,0,2]);grid;
xlabel('\omega [rad]');
ylabel('|H(e^{j\omega_1})|');
f = imread('./cheer/maru_256(cheer).tif');
f_Goal = imread('./cheer/maru_512(cheer).tif');
f = mat2gray(f,[0 255]);
f_Goal = mat2gray(f_Goal,[0 255]);

U = 2;   %拡大率　

[M,N] = size(f);
g_bilin = zeros((M*U)+6,(N*U)+6);

H_bilin = [1 2 1]/2;

for x = 1:1:M    
   for y = 1:1:N
       g_bilin((U*x)+1,(U*y)+1) = f(x,y); 
   end
end

g_bilin(1,:) = g_bilin(U+1,:); 
g_bilin((M*U)+U+1,:) = g_bilin((M*U)+1,:); 
g_bilin(:,1) = g_bilin(:,U+1); 
g_bilin(:,(M*U)+U+1) = g_bilin(:,(M*U)+1); 

for x = 1:1:(U*M)+6 
    g_bilin(x,:) = filter(H_bilin,1,g_bilin(x,:));
end
for y = 1:1:(U*N)+6 
    g_bilin(:,y) = filter(H_bilin,1,g_bilin(:,y));
end

g_b = zeros((M*U),(N*U));
for x = 1:1:(M*U)
   for y = 1:1:(M*U)
       g_b(x,y) = g_bilin(x+3,y+3); 
   end
end

g_b_diff = zeros((M*U),(N*U));
for x = 1:1:(M*U)    
   for y = 1:1:(N*U)
       g_b_diff(x,y) = abs(f_Goal(x,y) - g_b(x,y)); 
   end
end

SAD_b = sum(sum(g_b_diff))
%SSD_b = sum(sum(g_b_diff .^2))
%MSE_b = sum(sum(g_b_diff .^2))/((M*U)*(M*U));
%PSNR_b = 10*log10((1*1)/MSE_b)

figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image (256x256)');

figure();
subplot(1,2,1);
imshow(g_b,[0 1]);
xlabel('a).Ruselt of bilinear interpolation (512x512)');

subplot(1,2,2);
imshow(g_b_diff,[0 1]);
xlabel('b).Difference image (512x512)');

figure();
w = 0:0.01:pi;
Xejw_2 = freqz(H_bilin,1,w);
plot(w,abs(Xejw_2));
axis([0,pi,0,2]);grid;
xlabel('\omega [rad]');
ylabel('|H(e^{j\omega_1}|');
f = imread('./cheer/maru_256(cheer).tif');
f_Goal = imread('./cheer/maru_512(cheer).tif');
f = mat2gray(f,[0 255]);
f_Goal = mat2gray(f_Goal,[0 255]);

U = 2;   %拡大率　

[M,N] = size(f);
g_cubic = zeros((M*U)+16,(N*U)+16);

a = -0.5;
t = -1+(1/U):(1/U):1-(1/U);
H_cubic = (a+2)*(abs(t).^(3))-(a+3)*(abs(t).^(2)) + 1;  
t = -2+(1/U):(1/U):-1;
H_cubic = [0 (a)*(abs(t).^(3))-(a*5)*(abs(t).^(2))+(a*8)*abs(t)-4*a H_cubic];  
t = 1:(1/U):2-(1/U);
H_cubic = [H_cubic (a)*(abs(t).^(3))-(a*5)*(abs(t).^(2))+(a*8)*abs(t)-4*a 0];

for x = 1:1:M 
   for y = 1:1:N
       g_cubic((U*x)+1,(U*y)+1) = f(x,y); 
   end
end

g_cubic(1,:) = g_cubic(U+1,:); 
g_cubic((M*U)+U+1,:) = g_cubic((M*U)+1,:); 
g_cubic(:,1) = g_cubic(:,U+1); 
g_cubic(:,(M*U)+U+1) = g_cubic(:,(M*U)+1); 

for x = 1:1:(U*M+16) 
    g_cubic(x,:) = filter(H_cubic,1,g_cubic(x,:));
end
for y = 1:1:(U*N+16) 
    g_cubic(:,y) = filter(H_cubic,1,g_cubic(:,y));
end

g_c = zeros((M*U),(N*U));
for x = 1:1:(M*U)
   for y = 1:1:(M*U)
       g_c(x,y) = g_cubic(x+6,y+6); 
   end
end

g_c_diff = zeros((M*U),(N*U));
for x = 1:1:(M*U) 
   for y = 1:1:(N*U)
       g_c_diff(x,y) = abs(f_Goal(x,y) - g_c(x,y)); 
   end
end

SAD_c = sum(sum(g_c_diff))
%SSD_c = sum(sum(g_c_diff .^2))
%MSE_c = sum(sum(g_c_diff .^2))/((M*U)*(M*U));
%PSNR_c = 10*log10((1*1)/MSE_c)

figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image (256x256)');

figure();
subplot(1,2,1);
imshow(g_c,[0 1]);
xlabel('a).Ruselt of Cubic convolution (a=-0.5)(512x512)');

subplot(1,2,2);
imshow(g_c_diff,[0 1]);
xlabel('b).Difference image (512x512)');

figure();
w = 0:0.01:pi;
Xejw_3 = freqz(H_cubic,1,w);
plot(w,abs(Xejw_3));
axis([0,pi,0,5]);grid;
xlabel('\omega [rad] (a = -0.5)');
ylabel('|H(e^{j\omega_1}|');
f = imread('./cheer/maru_256(cheer).tif');
f_Goal = imread('./cheer/maru_512(cheer).tif');
f = mat2gray(f,[0 255]);
f_Goal = mat2gray(f_Goal,[0 255]);

U = 2;   %拡大率　

[M,N] = size(f);
g_B_sp = zeros((M*U)+16,(N*U)+16);

t = -1+(1/U):(1/U):1-(1/U);
H_B_sp = (1/2)*(abs(t).^(3))-(abs(t).^(2)) + (2/3);  
t = -2+(1/U):(1/U):-1;
H_B_sp = [0 (-1/6)*(abs(t).^(3))+(abs(t).^(2))-(2)*abs(t)+(4/3) H_B_sp];  
t = 1:(1/U):2-(1/U);
H_B_sp = [ H_B_sp (-1/6)*(abs(t).^(3))+(abs(t).^(2))-(2)*abs(t)+(4/3) 0];  

for x = 1:1:M  
   for y = 1:1:N
       g_B_sp((U*x)+1,(U*y)+1) = f(x,y); 
   end
end

g_B_sp(1,:) = g_B_sp(U+1,:); 
g_B_sp((M*U)+U+1,:) = g_B_sp((M*U)+1,:); 
g_B_sp(:,1) = g_B_sp(:,U+1); 
g_B_sp(:,(M*U)+U+1) = g_B_sp(:,(M*U)+1); 

for x = 1:1:(M*U)+16 
    g_B_sp(x,:) = filter(H_B_sp,1,g_B_sp(x,:));
end
for y = 1:1:(N*U)+16
    g_B_sp(:,y) = filter(H_B_sp,1,g_B_sp(:,y));
end

g_B = zeros((M*U),(N*U));
for x = 1:1:(M*U)
   for y = 1:1:(M*U)
       g_B(x,y) = g_B_sp(x+6,y+6); 
   end
end

g_B_diff = zeros((M*U),(N*U));
for x = 1:1:(M*U) 
   for y = 1:1:(N*U)
       g_B_diff(x,y) = abs(f_Goal(x,y) - g_B(x,y)); 
   end
end

SAD_B = sum(sum(g_B_diff))
%SSD_B = sum(sum(g_B_diff .^2))
%MSE_B = sum(sum(g_B_diff .^2))/((M*U)*(M*U));
%PSNR_B = 10*log10((1*1)/MSE_B)


figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image (512x512)');

figure();
subplot(1,2,1);
imshow(g_B,[0 1]);
xlabel('b).Ruselt of B-spline (512x512)');

subplot(1,2,2);
imshow(g_B_diff,[0 1]);
xlabel('b).Difference image (512x512)');

figure();
w = 0:0.01:pi;
Xejw_4 = freqz(H_B_sp,1,w);
plot(w,abs(Xejw_4));
axis([0,pi,0,5]);grid;
xlabel('\omega [rad] (a = -1)');
ylabel('|H(e^{j\omega_1}|');
```

### 参考文献
[^footnote1]: [貴家 仁志，"ディジタル画像の表現と階調変換，色間引きの原理，" インターフェース，CQ出版，1998年2月]
[^footnote2]: [貴家 仁志，"ディジタル画像の解像度変換 — 画像の拡大，" インターフェース，CQ出版，1998年4月]
[^footnote3]: [貴家 仁志，"ディジタル画像の解像度変換 — 任意サイズへの画像の変換，" インターフェース，CQ出版，1998年6月]

[貴家 仁志，"ディジタル画像の表現と階調変換，色間引きの原理，" インターフェース，CQ出版，1998年2月]: https://cir.nii.ac.jp/crid/1520854805825943040

[貴家 仁志，"ディジタル画像の解像度変換 — 画像の拡大，" インターフェース，CQ出版，1998年4月]: https://cir.nii.ac.jp/crid/1523669555437398400

[貴家 仁志，"ディジタル画像の解像度変換 — 任意サイズへの画像の変換，" インターフェース，CQ出版，1998年6月]: https://cir.nii.ac.jp/crid/1520010380206841600


