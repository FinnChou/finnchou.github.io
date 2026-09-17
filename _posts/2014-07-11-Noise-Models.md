---
layout: post
title: "Image Denoise : 噪声模型"
date: 2014-07-11 16:45:12 +0800
categories: 数字图像处理
tags: [图像处理, 噪声模型]
math: true
---

### 图像退化模型
在数字图像处理领域中，图像退化是一个普遍存在的现象。现实世界中的图像退化过程可以通过下图所示的数学模型来描述和分析。

![频率域信号示例](/assets/resource/Image-Denoise-1/frequency_domain_signal.jpeg){: width="450" height="450"}

这个退化模型可以用如下数学表达式来描述：

$$
\begin{aligned}
g(x,y) = h(x,y) \star f(x,y) + \eta (x,y)
\end{aligned}
$$

在这里，$f(x,y)$ 表示原图数据， $h(x,y)$ 表示退化滤波器，$\eta (x,y)$ 代表了加性噪声，$g(x,y)$ 则表示退化后的图像结果。

在频域中，该模型可以表示为：

$$
\begin{aligned}
G(u,v) = H(u,v) F(u,v) + N(u,v)
\end{aligned}
$$

其中，$F(u,v)$ 为原始图像的傅里叶变换，$H(u,v)$ 为退化滤波器的频域传达函数，$N(u,v)$ 为噪声的频谱，$G(u,v)$ 为退化图像的频谱。

基于上述模型，图像复原的目标是将退化图像 $g(x,y)$ 或其频谱 $G(u,v)$ 恢复为原始图像 $f(x,y)$ 或其频谱 $F(u,v)$。这个过程主要包含两个关键步骤：
- 噪声抑制：消除 $\eta (x,y)$ 或其频谱 $N(u,v)$ 的影响
- 逆滤波：补偿 $h(x,y)$ 或其频谱 $H(u,v)$ 导致的退化

理想的图像复原结果应当使重建图像 $\hat{f}(x,y)$ 与原始图像 $f(x,y)$ 尽可能接近。

本文将重点介绍图像复原中的噪声模型，详细讨论几种常见的噪声类型及其特征。

### 评价用图像与其直方图

![噪声评价用图像与其直方图](/assets/resource/Image-Denoise-1/noise_evaluation_histogram.jpeg){: width="450" height="450"}


### 均匀噪声 (Uniform noise)
均匀噪声是最基本的噪声类型之一，其概率密度函数在定义区间内保持恒定。可以通过线性变换将标准均匀分布映射到任意区间：

$$
\begin{aligned}
z = a + (b-a) U(0, 1)
\end{aligned}
$$

MATLAB实现非常直观：

```matlab
a = 0;      % 下界
b = 0.3;    % 上界
n_Uniform = a + (b-a)*rand(M,N);
```

![均匀噪声](/assets/resource/Image-Denoise-1/uniform_noise.jpeg){: width="450" height="450"}

### 高斯噪声 (Gaussian noise) 
高斯噪声（Gaussian noise），也称为正态噪声（Normal noise），是图像处理中最常见的噪声类型之一。其概率密度函数服从正态分布，具有良好的数学特性，在实际应用中具有广泛的适用性。

在MATLAB中，我们可以使用内置函数randn(M,N)生成符合标准正态分布（均值为0，方差为1）的噪声矩阵。通过简单的线性变换，可以得到任意均值和方差的高斯噪声：

```matlab
a = 0;      % 期望均值
b = 0.08;   % 标准差
n_gaussian = a + b .* randn(M,N);
```

![高斯噪声](/assets/resource/Image-Denoise-1/gaussian_noise.jpeg){: width="450" height="450"}

### 瑞利噪声 (Rayleigh noise)
瑞利噪声是一种具有右偏特性的概率分布，其概率密度函数呈现不对称性，这使其特别适合于模拟某些具有偏态分布特征的图像噪声。瑞利噪声可以通过对均匀分布进行非线性变换来生成，其数学表达式为：

$$
\begin{aligned}
z = a + \sqrt{-b \log{[1 - U(0, 1)]}}
\end{aligned}
$$

其中，$U(0, 1)$ 表示区间[0,1]上的均匀分布。在MATLAB中，可以使用rand(M,N)函数生成均匀分布的随机数，然后通过变换得到瑞利噪声：

```matlab
a = -0.2;   % 位置参数
b = 0.03;   % 尺度参数
n_rayleigh = a + (-b .* log(1 - rand(M,N))).^0.5;
```

![瑞利噪声](/assets/resource/Image-Denoise-1/rayleigh_noise.jpeg){: width="450" height="450"}

### 伽马噪声 (Gamma noise)
伽马噪声是通过叠加多个独立的指数分布随机变量而得到的。其中，每个指数分布的随机变量可以通过对均匀分布进行变换获得：

$$
\begin{aligned}
E_i = \frac{1}{a} \log{[1 - U(0, 1)]}
\end{aligned}
$$

最终的伽马噪声是这些指数分布随机变量的叠加：

$$
\begin{aligned}
z = E_1 + E_2 + \dotsc + E_b
\end{aligned}
$$

其中，$b$ 是形状参数，当 $b=1$ 时，退化为指数分布。MATLAB实现如下：

```matlab
a = 25;     % 尺度参数
b = 3;      % 形状参数
n_Erlang = zeros(M,N); 

for j=1:b
    n_Erlang = n_Erlang + (-1/a)*log(1 - rand(M,N));
end
```

![伽马噪声](/assets/resource/Image-Denoise-1/gamma_noise.jpeg){: width="450" height="450"}

### 椒盐噪声 (Salt-and-pepper noise)
椒盐噪声，也称为脉冲噪声（Impulse noise），是一种典型的数字图像噪声。它在图像中表现为随机分布的黑白像素点。这种噪声在早期的电影胶片中尤为常见，主要由胶片材料的化学不稳定性和机械损伤导致。

实现椒盐噪声的关键是通过阈值判断来随机将部分像素设置为最大值（盐噪声）或最小值（椒噪声）。实现方法如下：

```matlab
a = 0.05;   % 椒噪声比例
b = 0.05;   % 盐噪声比例
x = rand(M,N);

g_sp = zeros(M,N);
g_sp = f;

g_sp(find(x<=a)) = 0;          % 添加椒噪声
g_sp(find(x > a & x<(a+b))) = 1;  % 添加盐噪声
```

![椒盐噪声](/assets/resource/Image-Denoise-1/salt_pepper_noise.jpeg){: width="450" height="450"}

### 总结
本文详细介绍了数字图像处理中最常见的几种噪声模型，包括高斯噪声、瑞利噪声、伽马噪声、均匀噪声和椒盐噪声。每种噪声都具有其特定的概率分布特征和应用场景。理解这些噪声模型的特性对于选择合适的图像去噪方法具有重要的指导意义。完整的代码实现如下：

```matlab
close all;
clear all;
clc;

f = imread('./original_pattern.tif');
f = mat2gray(f,[0 255]);
[M,N] = size(f);

figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original image');

subplot(1,2,2);
x = linspace(-0.2,1.2,358);
h = hist(f,x)/(M*N);
Histogram = zeros(358,1);
for y = 1:256
    Histogram = Histogram + h(:,y);
end
bar(-0.2:1/255:1.2,Histogram);
axis([-0.2 1.2 0 0.014]),grid;
xlabel('b).The Histogram of a');
ylabel('Number of pixels');

%% ---------------gaussian-------------------
a = 0;
b = 0.08;
n_gaussian = a + b .* randn(M,N);

g_gaussian = f + n_gaussian; 

figure();
subplot(1,2,1);
imshow(g_gaussian,[0 1]);
xlabel('a).Ruselt of Gaussian noise');

subplot(1,2,2);
x = linspace(-0.2,1.2,358);
h = hist(g_gaussian,x)/(M*N);
Histogram = zeros(358,1);
for y = 1:256
    Histogram = Histogram + h(:,y);
end
bar(-0.2:1/255:1.2,Histogram);
axis([-0.2 1.2 0 0.014]),grid;
xlabel('b).The Histogram of a');
ylabel('Number of pixels');

%% ---------------rayleigh-------------------
a = -0.2;
b = 0.03;
n_rayleigh = a + (-b .* log(1 - rand(M,N))).^0.5;

g_rayleigh = f + n_rayleigh; 

figure();
subplot(1,2,1);
imshow(g_rayleigh,[0 1]);
xlabel('a).Ruselt of Rayleigh noise');

subplot(1,2,2);
x = linspace(-0.2,1.2,358);
h = hist(g_rayleigh,x)/(M*N);
Histogram = zeros(358,1);
for y = 1:256
    Histogram = Histogram + h(:,y);
end
bar(-0.2:1/255:1.2,Histogram);
axis([-0.2 1.2 0 0.014]),grid;
xlabel('b).The Histogram of a');
ylabel('Number of pixels');
%% ---------------Erlang-------------------
a = 25;
b = 3;
n_Erlang = zeros(M,N); 

for j=1:b
    n_Erlang = n_Erlang + (-1/a)*log(1 - rand(M,N));
end

g_Erlang = f + n_Erlang; 

figure();
subplot(1,2,1);
imshow(g_Erlang,[0 1]);
xlabel('a).Ruselt of Erlang noise');

subplot(1,2,2);
x = linspace(-0.2,1.2,358);
h = hist(g_Erlang,x)/(M*N);
Histogram = zeros(358,1);
for y = 1:256
    Histogram = Histogram + h(:,y);
end
bar(-0.2:1/255:1.2,Histogram);
axis([-0.2 1.2 0 0.014]),grid;
xlabel('b).The Histogram of a');
ylabel('Number of pixels');

%% ---------------Exponential-------------------
a = 9;
n_Ex = (-1/a)*log(1 - rand(M,N)); 

g_Ex = f + n_Ex;

figure();
subplot(1,2,1);
imshow(g_Ex,[0 1]);
xlabel('a).Ruselt of Exponential noise');

subplot(1,2,2);
x = linspace(-0.2,1.2,358);
h = hist(g_Ex,x)/(M*N);
Histogram = zeros(358,1);
for y = 1:256
    Histogram = Histogram + h(:,y);
end
bar(-0.2:1/255:1.2,Histogram);
axis([-0.2 1.2 0 0.014]),grid;
xlabel('b).The Histogram of a');
ylabel('Number of pixels');

%% ---------------Uniform-------------------
a = 0;
b = 0.3;
n_Uniform = a + (b-a)*rand(M,N);

g_Uniform = f + n_Uniform;

figure();
subplot(1,2,1);
imshow(g_Uniform,[0 1]);
xlabel('a).Ruselt of Uniform noise');

subplot(1,2,2);
x = linspace(-0.2,1.2,358);
h = hist(g_Uniform,x)/(M*N);
Histogram = zeros(358,1);
for y = 1:256
    Histogram = Histogram + h(:,y);
end
bar(-0.2:1/255:1.2,Histogram);
axis([-0.2 1.2 0 0.014]),grid;
xlabel('b).The Histogram of a');
ylabel('Number of pixels');

%% ---------------Salt & pepper-------------------
a = 0.05;
b = 0.05;
x = rand(M,N);

g_sp = zeros(M,N);
g_sp = f;

g_sp(find(x<=a)) = 0;
g_sp(find(x > a & x<(a+b))) = 1;

figure();
subplot(1,2,1);
imshow(g_sp,[0 1]);
xlabel('a).Ruselt of Salt & pepper noise');

subplot(1,2,2);
x = linspace(-0.2,1.2,358);
h = hist(g_sp,x)/(M*N);
Histogram = zeros(358,1);
for y = 1:256
    Histogram = Histogram + h(:,y);
end
bar(-0.2:1/255:1.2,Histogram);
axis([-0.2 1.2 0 0.3]),grid;
xlabel('b).The Histogram of a');
ylabel('Number of pixels');
```
