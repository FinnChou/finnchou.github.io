---
layout: post
title: "Frequency Domain Filter : 高通滤波器"
date: 2013-12-08 18:02:49 +0800
categories: 数字图像处理
tags: [图像处理, 频域滤波]
math: true
image:
  path: /assets/resource/og/Frequency-Domain-Filter-2.png
  alt: "Frequency Domain Filter : 高通滤波器"
---

首先，我们对图像进行二维傅里叶变换，其表达式为：

$$
\begin{aligned}
F(u,v) = \sum_{x=0}^{M-1} \sum_{y=0}^{N-1} f(x,y) e^{-j2\pi \big( \frac{u}{M}x + \frac{v}{N}y \big)}
\end{aligned}
$$

当 $u=0$ 和 $v=0$ 时，上式简化为：

$$
\begin{aligned}
F(0,0) &= MN \cdot \frac{1}{MN} \sum_{x=0}^{M-1} \sum_{y=0}^{N-1} f(x,y) \\
       &= MN \cdot \overline{f}(x,y) 
\end{aligned}
$$

可以看出，$F(0,0)$的值通常非常大，我们称之为直流分量。这个直流分量比其他频率成分大几个数量级，这也是为什么傅里叶谱通常需要使用对数变换才能清晰显示的原因。

对于高通滤波器来说，由于它会衰减直流分量，导致处理后的图像动态范围变窄，使图像整体偏灰暗。相反，如果保留直流分量并增强高频部分，就能增强图像细节，这种滤波器被称为锐化滤波器。本文将重点介绍高通滤波器与锐化滤波器的原理和应用。

### 理想高通滤波器
类似于理想低通滤波器，理想高通滤波器的数学表达式如下：

$$
\begin{equation}
H(u,v) = \left \{
\begin{array}{l}
0　, D(u, v) \le D_0 \\
1　, D(u, v) > D_0 \\ 
\end{array}
\right.
\end{equation}
$$

其中$D_0$表示滤波器的截止频率（阻带半径），$D(u,v)$是频域点到频谱中心的距离。理想高通滤波器的振幅特性如下图所示：

![理想高通滤波器振幅特性](/assets/resource/Frequency-Domain-Filter-2/ideal_highpass_amplitude.jpeg){: width="600" height="600"}

使用该滤波器处理图像，得到如下结果。可以观察到，与理想低通滤波器类似，处理后的图像存在明显的振铃现象。从视觉效果来看，图像整体偏暗，这是因为图像的直流分量被滤除所导致的。

![理想高通滤波器结果](/assets/resource/Frequency-Domain-Filter-2/ideal_highpass_result.jpeg){: width="600" height="600"}

### 巴特沃斯高通滤波器
巴特沃斯高通滤波器的表达式为：

$$
\begin{aligned}
H(u, v) = \frac{1}{1 + (D_0 / D(u,v))^{2n}}
\end{aligned}
$$

与低通滤波器类似，巴特沃斯高通滤波器可以通过调整阶数n来改变过渡特性。阶数过高会导致振铃现象的产生。

![巴特沃斯高通滤波器振幅特性](/assets/resource/Frequency-Domain-Filter-2/butterworth_highpass_amplitude.jpeg){: width="600" height="600"}

![巴特沃斯高通滤波器结果](/assets/resource/Frequency-Domain-Filter-2/butterworth_highpass_result.jpeg){: width="600" height="600"}

### 高斯高通滤波器
高斯高通滤波器的表达式为：

$$
\begin{aligned}
H(u, v) = 1 - e^{\frac{-D^2(u,v)}{2D_0^2}}
\end{aligned}
$$

高斯滤波器的过渡特性非常平滑，因此不会产生振铃现象。

![高斯高通滤波器振幅特性](/assets/resource/Frequency-Domain-Filter-2/gaussian_highpass_amplitude.jpeg){: width="600" height="600"}

![高斯高通滤波器结果](/assets/resource/Frequency-Domain-Filter-2/gaussian_highpass_result.jpeg){: width="600" height="600"}

### 高通滤波器 Matlab 代码
```matlab
close all;
clear all;

%% ---------Ideal Highpass Filters (Fre. Domain)------------
f = imread('characters_test_pattern.tif');
f = mat2gray(f,[0 255]);

[M,N] = size(f);
P = 2*M;
Q = 2*N;
fc = zeros(M,N);

for x = 1:1:M
    for y = 1:1:N
        fc(x,y) = f(x,y) * (-1)^(x+y);
    end
end

F = fft2(fc,P,Q);

H_1 = ones(P,Q);
H_2 = ones(P,Q);

for x = (-P/2):1:(P/2)-1
     for y = (-Q/2):1:(Q/2)-1
        D = (x^2 + y^2)^(0.5);
        if(D <= 60)  H_1(x+(P/2)+1,y+(Q/2)+1) = 0; end    
        if(D <= 160) H_2(x+(P/2)+1,y+(Q/2)+1) = 0; end
     end
end

G_1 = H_1 .* F;
G_2 = H_2 .* F;

g_1 = real(ifft2(G_1));
g_1 = g_1(1:1:M,1:1:N);

g_2 = real(ifft2(G_2));
g_2 = g_2(1:1:M,1:1:N);         

for x = 1:1:M
    for y = 1:1:N
        g_1(x,y) = g_1(x,y) * (-1)^(x+y);
        g_2(x,y) = g_2(x,y) * (-1)^(x+y);
    end
end
%% -----show-------
figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image');

subplot(1,2,2);
imshow(log(1 + abs(F)),[ ]);
xlabel('b).Fourier spectrum of a');

figure();
subplot(1,2,1);
imshow(H_1,[0 1]);
xlabel('c).Ideal Highpass filter(D=60)');

subplot(1,2,2);
h = mesh(1:20:P,1:20:Q,H_1(1:20:P,1:20:Q));
set(h,'EdgeColor','k');
axis([0 P 0 Q 0 1]);
xlabel('u');ylabel('v');
zlabel('|H(u,v)|');

figure();
subplot(1,2,1);
imshow(log(1 + abs(G_1)),[ ]);
xlabel('d).Result of filtering using c');

subplot(1,2,2);
imshow(g_1,[0 1]);
xlabel('e).Result image');

figure();
subplot(1,2,1);
imshow(H_2,[0 1]);
xlabel('f).Ideal Highpass filter(D=160)');

subplot(1,2,2);
h = mesh(1:20:P,1:20:Q,H_2(1:20:P,1:20:Q));
set(h,'EdgeColor','k');
axis([0 P 0 Q 0 1]);
xlabel('u');ylabel('v');
zlabel('|H(u,v)|');

figure();
subplot(1,2,1);
imshow(log(1 + abs(G_2)),[ ]);
xlabel('g).Result of filtering using e');

subplot(1,2,2);
imshow(g_2,[0 1]);
xlabel('h).Result image');
close all;
clear all;

%% ---------Butterworth Highpass Filters (Fre. Domain)------------
f = imread('characters_test_pattern.tif');
f = mat2gray(f,[0 255]);

[M,N] = size(f);
P = 2*M;
Q = 2*N;
fc = zeros(M,N);

for x = 1:1:M
    for y = 1:1:N
        fc(x,y) = f(x,y) * (-1)^(x+y);
    end
end

F = fft2(fc,P,Q);

H_1 = zeros(P,Q);
H_2 = zeros(P,Q);

for x = (-P/2):1:(P/2)-1
     for y = (-Q/2):1:(Q/2)-1
        D = (x^2 + y^2)^(0.5);
        D_0 = 100;
        H_1(x+(P/2)+1,y+(Q/2)+1) = 1/(1+(D_0/D)^2);   
        H_2(x+(P/2)+1,y+(Q/2)+1) = 1/(1+(D_0/D)^6);
     end
end


G_1 = H_1 .* F;
G_2 = H_2 .* F;

g_1 = real(ifft2(G_1));
g_1 = g_1(1:1:M,1:1:N);

g_2 = real(ifft2(G_2));
g_2 = g_2(1:1:M,1:1:N);         

for x = 1:1:M
    for y = 1:1:N
        g_1(x,y) = g_1(x,y) * (-1)^(x+y);
        g_2(x,y) = g_2(x,y) * (-1)^(x+y);
    end
end

%% -----show-------
figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image');

subplot(1,2,2);
imshow(log(1 + abs(F)),[ ]);
xlabel('b).Fourier spectrum of a');

figure();
subplot(1,2,1);
imshow(H_1,[0 1]);
xlabel('c)Butterworth Lowpass (D_{0}=100,n=1)');

subplot(1,2,2);
h = mesh(1:20:P,1:20:Q,H_1(1:20:P,1:20:Q));
set(h,'EdgeColor','k');
axis([0 P 0 Q 0 1]);
xlabel('u');ylabel('v');
zlabel('|H(u,v)|');

figure();
subplot(1,2,1);
imshow(log(1 + abs(G_1)),[ ]);
xlabel('d).Result of filtering using c');

subplot(1,2,2);
imshow(g_1,[0 1]);
xlabel('e).Result image');

figure();
subplot(1,2,1);
imshow(H_2,[0 1]);
xlabel('f).Butterworth Lowpass (D_{0}=100,n=3)');

subplot(1,2,2);
h = mesh(1:20:P,1:20:Q,H_2(1:20:P,1:20:Q));
set(h,'EdgeColor','k');
axis([0 P 0 Q 0 1]);
xlabel('u');ylabel('v');
zlabel('|H(u,v)|');

figure();
subplot(1,2,1);
imshow(log(1 + abs(G_2)),[ ]);
xlabel('g).Result of filtering using e');

subplot(1,2,2);
imshow(g_2,[0 1]);
xlabel('h).Result image');
close all;
clear all;

%% ---------Gaussian Highpass Filters (Fre. Domain)------------
f = imread('characters_test_pattern.tif');
f = mat2gray(f,[0 255]);

[M,N] = size(f);
P = 2*M;
Q = 2*N;
fc = zeros(M,N);

for x = 1:1:M
    for y = 1:1:N
        fc(x,y) = f(x,y) * (-1)^(x+y);
    end
end

F = fft2(fc,P,Q);

H_1 = zeros(P,Q);
H_2 = zeros(P,Q);

for x = (-P/2):1:(P/2)-1
     for y = (-Q/2):1:(Q/2)-1
        D = (x^2 + y^2)^(0.5);
        D_0 = 60;
        H_1(x+(P/2)+1,y+(Q/2)+1) = 1 - exp(-(D*D)/(2*D_0*D_0));   
        D_0 = 160;
        H_2(x+(P/2)+1,y+(Q/2)+1) = 1 - exp(-(D*D)/(2*D_0*D_0));
     end
end

G_1 = H_1 .* F;
G_2 = H_2 .* F;

g_1 = real(ifft2(G_1));
g_1 = g_1(1:1:M,1:1:N);

g_2 = real(ifft2(G_2));
g_2 = g_2(1:1:M,1:1:N);         

for x = 1:1:M
    for y = 1:1:N
        g_1(x,y) = g_1(x,y) * (-1)^(x+y);
        g_2(x,y) = g_2(x,y) * (-1)^(x+y);
    end
end


%% -----show-------
figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image');

subplot(1,2,2);
imshow(log(1 + abs(F)),[ ]);
xlabel('b).Fourier spectrum of a');

figure();
subplot(1,2,1);
imshow(H_1,[0 1]);
xlabel('c)Gaussian Highpass (D_{0}=60)');

subplot(1,2,2);
h = mesh(1:20:P,1:20:Q,H_1(1:20:P,1:20:Q));
set(h,'EdgeColor','k');
axis([0 P 0 Q 0 1]);
xlabel('u');ylabel('v');
zlabel('|H(u,v)|');

figure();
subplot(1,2,1);
imshow(log(1 + abs(G_1)),[ ]);
xlabel('d).Result of filtering using c');

subplot(1,2,2);
imshow(g_1,[0 1]);
xlabel('e).Result image');

figure();
subplot(1,2,1);
imshow(H_2,[0 1]);
xlabel('f).Gaussian Highpass (D_{0}=160)');

subplot(1,2,2);
h = mesh(1:20:P,1:20:Q,H_2(1:20:P,1:20:Q));
set(h,'EdgeColor','k');
axis([0 P 0 Q 0 1]);
xlabel('u');ylabel('v');
zlabel('|H(u,v)|');

figure();
subplot(1,2,1);
imshow(log(1 + abs(G_2)),[ ]);
xlabel('g).Result of filtering using e');

subplot(1,2,2);
imshow(g_2,[0 1]);
xlabel('h).Result image');
```

### 锐化滤波器
锐化滤波器的核心思想是保留傅里叶谱的直流分量，同时增强其他频率成分。通过这种方式，可以有效增强图像细节，使图像更加清晰。锐化滤波器的数学表达式如下：

$$
\begin{aligned}
g(x,y) &= \Im^{-1} \Big[ k_1 F(u,v) + k_2  \Big( 1-H_{LP}(u,v) \Big) F(u,v) \Big] \\
       &= \Im^{-1} \Big[ k_1 F(u,v) + k_2 H_{HP}(u,v) F(u,v) \Big] \\
       &= \Im^{-1} \Big[ \big( k_1 + k_2 H_{HP}(u,v) \big) \cdot F(u,v) \Big] \\
\end{aligned}
$$

这个表达式的原理很直观：首先保留原始图像的傅里叶谱$F(u,v)$，然后叠加高通滤波器的结果$H_{HP}(u,v) \cdot F(u,v)$，最终得到锐化后的图像。为了灵活控制锐化效果，引入了两个参数$k_1$和$k_2$：$k_1$控制原图像的保留程度，$k_2$控制高频分量的增强程度。

下图展示了锐化滤波器的应用效果：

![锐化滤波器-原始图像与频谱](/assets/resource/Frequency-Domain-Filter-2/sharpening_original.jpeg){: width="600" height="600"}
![锐化滤波器-锐化图像与频谱](/assets/resource/Frequency-Domain-Filter-2/sharpening_result.jpeg){: width="600" height="600"}

#### Matlab 代码
```matlab
close all;
clear all;
clc;

%% ---------The High-Fre-Emphasis Filters (Fre. Domain)------------
f = imread('blurry_moon.tif');
f = mat2gray(f,[0 255]);

[M,N] = size(f); 
P = 2*M;
Q = 2*N;
fc = zeros(M,N);

for x = 1:1:M
    for y = 1:1:N
        fc(x,y) = f(x,y) * (-1)^(x+y);
    end
end

F = fft2(fc,P,Q);

H_HP = zeros(P,Q);

for x = (-P/2):1:(P/2)-1
     for y = (-Q/2):1:(Q/2)-1
        D = (x^2 + y^2)^(0.5);
        D_0 = 80;
        H_HP(x+(P/2)+1,y+(Q/2)+1) = 1 - exp(-(D*D)/(2*D_0*D_0));   
     end
end

G_HP = H_HP .* F;

G_HFE = (1 + 1.1 * H_HP) .* F;

g_1 = real(ifft2(G_HP));
g_1 = g_1(1:1:M,1:1:N);

g_2 = real(ifft2(G_HFE));
g_2 = g_2(1:1:M,1:1:N);

for x = 1:1:M
    for y = 1:1:N
        g_1(x,y) = g_1(x,y) * (-1)^(x+y);
        g_2(x,y) = g_2(x,y) * (-1)^(x+y);
    end
end

g = histeq(g_2);

%g_1 = mat2gray(g_1);
%% -----show-------
figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image');

subplot(1,2,2);
imshow(log(1 + abs(F)),[ ]);
xlabel('b).Fourier spectrum of a');

figure();
subplot(1,2,1);
imshow(g_1,[0 1]);
xlabel('c).Result image of High-pass Filter');

subplot(1,2,2);
imshow(log(1 + abs(G_HP)),[ ]);
xlabel('d).Result of filtering using e');

figure();
subplot(1,2,1);
imshow(g_2,[0 1]);
xlabel('e).Result image of High-Fre-Emphasis Filter');

subplot(1,2,2);
imshow(log(1 + abs(G_HFE)),[ ]);
xlabel('f).Result of filtering using e');
```