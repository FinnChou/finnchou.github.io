---
layout: post
title: "Spatial Filtering : 空间滤波"
date: 2013-10-20 17:28:04 +0800
categories: 数字图像处理
tags: [图像处理, 空间滤波]
math: true
image:
  path: /assets/resource/og/Spatial-Filtering.png
  alt: "Spatial Filtering : 空间滤波"
---

## 引言

滤波(Filtering)一词源于频域处理，表示对特定频率成分的滤除。空间滤波(Spatial-Filtering)则是在图像的像素邻域内进行二维滤波操作。线性空间滤波器（如均值滤波器）在空间域上进行灰度值运算，与频域滤波器存在一一对应关系（例如均值滤波器本质上就是低通滤波器），这种对应关系有助于理解滤波器的特性。相比之下，非线性滤波器（如最大值、最小值和中值滤波器）则没有这种对应关系。

## 空间滤波的基本原理

线性空间滤波的核心运算是卷积，其数学表达式如下：

$$
g(x,y) = \sum^{a}_{s=-a}\sum^{b}_{t=-b} w(s,t)f(x-s, y-t)
$$

在卷积运算中，滤波器 $w(s,t)$ 与原始图像区域 $f(x-s, y-t)$ 的运算并非简单的乘加，而是涉及坐标旋转。值得注意的是，现代主流神经网络框架中的卷积层实际上并不进行坐标反转操作，而是直接进行对应位置的相乘相加。从严格意义上讲，这种操作应该称为互相关(cross-correlation)而非卷积。不过，在实际训练过程中，坐标旋转与否并不会影响网络的收敛结果。

上式所示的滤波器是非因果的。根据数字信号处理理论，零相位特性要求单位冲击响应关于原点对称，这样的系统必然是非因果的，由于需要未来的输入，在实际中是不可实现的。然而在图像处理中，我们通常逐帧处理图像，因此非因果性不会造成问题。更重要的是，零相位特性可以保证图像不会发生形变，这一点在图像处理中至关重要。

另一个需要考虑的问题是边界处理。当滤波器中心靠近图像边缘时，滤波器的一部分会超出图像范围。常见的处理方法包括：
1. 零填充
2. 最近邻填充
3. 镜像填充
4. 周期填充

直接使用零填充可能会导致处理后图像出现黑边，因此在实际应用中常采用其他填充方式。

## 平滑滤波器(Smoothing Spatial Filter)

平滑滤波器通过计算邻域内像素的平均值（或加权平均值）来实现图像平滑。从频域角度来看，这是一个典型的低通滤波器。

![Smoothing Filter Kernel](/assets/resource/Spatial-Filtering/smoothing-filter-kernel.jpeg){: width="600" height="600"}

该滤波器通过滤除高频成分实现图像平滑，其频率响应如下：

![Frequency Response of 3X3 Average Filter](/assets/resource/Spatial-Filtering/3x3-average-filter-frequency-response.jpeg){: width="600" height="600"}

![Frequency Response of 3X3 Weighted Average Filter](/assets/resource/Spatial-Filtering/3x3-weighted-average-filter-frequency-response.jpeg){: width="600" height="600"}

平均滤波器的通带比加权平均滤波器窄，因此使用平均滤波器处理的图像会比加权平均滤波器处理的图像更加模糊。

值得注意的是，平均滤波器的相位特性并非平面，某些位置的相位值为$\pi$。这是因为平均滤波器是一个偶实函数，其频率响应为实函数，但部分频率响应为负值，导致Matlab的angle()函数计算结果为$\pi$。本质上，该滤波器仍具有零相位特性。

实际图像处理结果如下：

![Average Filter Results](/assets/resource/Spatial-Filtering/average-filter-results.jpeg){: width="600" height="600"}

从处理结果来看，两种滤波器的差异并不明显。因此，通过观察频率响应更容易理解它们的区别。本文仅对均值滤波器进行简要介绍，更详细的说明请参考 📎 <a href="{{ site.baseurl }}/posts/Denoise-1/"> >> Image Denoise : 均值滤波器 << </a> 。

#### Matlab 代码
```matlab
close all;
clear all;

%% -------------Smoothing Linear Filters-----------------
f = imread('test_pattern_blurring_orig.tif');
f = mat2gray(f,[0 255]);

w_1 = ones(3)/9;  %%%%%
g_1 = imfilter(f,w_1,'conv','symmetric','same');

w_2 = ones(5)/25;  %%%%%
g_2 = imfilter(f,w_2,'conv','symmetric','same');

w_3 = [1 2 1;
       2 4 2;
       1 2 1]/16;  %%%%%
g_3 = imfilter(f,w_3,'conv','symmetric','same');

figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image');

subplot(1,2,2);
imshow(g_1,[0 1]);
xlabel('b).Average Filter(size 3x3)');

figure();
subplot(1,2,1);
imshow(g_2,[0 1]);
xlabel('c).Average Filter(size 5x5)');

subplot(1,2,2);
imshow(g_3,[0 1]);
xlabel('d).Weighted Average Filter(size 3x3)');

%% ------------------------
M = 64;
N = 64;
[H_1,w1,w2] = freqz2(w_1,M,N);
figure();
subplot(1,2,1);
mesh(w1(1:M)*pi,w2(1:N)*pi,abs(H_1(1:M,1:N)));
axis([-pi pi -pi pi 0 1]);
xlabel('\omega_1 [rad]');ylabel('\omega_2 [rad]');
zlabel('|H(e^{j\omega_1},e^{j\omega_2})|');


%figure();
subplot(1,2,2);
mesh(w1(1:M)*pi,w2(1:N)*pi,unwrap(angle(H_1(1:M,1:N))));
axis([-pi pi -pi pi -pi pi]);
xlabel('\omega_1 [rad]');ylabel('\omega_2 [rad]');
zlabel('\theta [rad]');
```

## 统计排序滤波器(Order-Statistic Filter)

统计排序滤波器是一类典型的非线性滤波器，包括最大值滤波器、最小值滤波器和中值滤波器等。从图像形态学的角度来看，最大值滤波对应图像的膨胀操作，最小值滤波对应图像的腐蚀操作。

而中值滤波器在去除椒盐噪声方面特别有效。其工作原理是将滤波器窗口内的像素灰度值排序，选择中间值作为输出像素的灰度值。同样，最大值滤波器和最小值滤波器分别选择排序后的最大值和最小值。

以下展示了添加椒盐噪声后的图像及其中值滤波处理结果：

![Median Filter Results P1](/assets/resource/Spatial-Filtering/median-filter-results-p1.jpeg){: width="600" height="600"}
![Median Filter Results P2](/assets/resource/Spatial-Filtering/median-filter-results-p2.jpeg){: width="600" height="600"}

#### Matlab 代码
```matlab
close all;
clear all;

%% ----------------Noise type--------------------
f = imread('original_pattern.tif');
f = mat2gray(f,[0 255]);
[M,N] = size(f);

g_gaussian = imnoise(f,'gaussian',0,0.015);
g_salt_pepper = imnoise(f,'salt & pepper',0.15);

figure(1);
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image');

subplot(1,2,2);
h = imhist(f)/(M*N);
bar(0:1/255:1,h);
axis([-0.1 1.1 0 0.55]),grid;
axis square;
xlabel('b).The histogram of original image');
ylabel('Number of pixels');

figure(2);
subplot(1,2,1);
imshow(g_gaussian,[0 1]);
xlabel('c).gaussian noise image');

subplot(1,2,2);
h = imhist(g_gaussian)/(M*N);
bar(0:1/255:1,h);
axis([-.1 1.1 0 0.05]),grid;
axis square;
xlabel('d).The histogram of c)');
ylabel('Number of pixels');

figure(5);
subplot(1,2,1);
imshow(g_salt_pepper,[0 1]);
xlabel('i).salt & pepper noise image');

subplot(1,2,2);
h = imhist(g_salt_pepper)/(M*N);
bar(0:1/255:1,h);
axis([-.1 1.1 0 0.55]),grid;
axis square;
xlabel('j).The histogram of g)');
ylabel('Number of pixels');

%% -------------Nonlinear Filters-----------------
g_med_wg = medfilt2(g_gaussian,'symmetric',[3 3]);
g_med_sp = medfilt2(g_salt_pepper,'symmetric',[3 3]);

figure(3);
subplot(1,2,1);
imshow(g_med_wg,[0 1]);
xlabel('e).Result of median filter');

subplot(1,2,2);
h = imhist(g_med_wg)/(M*N);
bar(0:1/255:1,h);
axis([-.1 1.1 0 0.05]),grid;
axis square;
xlabel('f).The histogram of e)');
ylabel('Number of pixels');


figure(6);
subplot(1,2,1);
imshow(g_med_sp,[0 1]);
xlabel('k).Result of median filter');

subplot(1,2,2);
h = imhist(g_med_sp)/(M*N);
bar(0:1/255:1,h);
axis([-.1 1.1 0 0.55]),grid;
axis square;
xlabel('l).The histogram of i)');
ylabel('Number of pixels');


%% -------------Linear Filters-----------------
w_1 = [1 2 1;
       2 4 2;
       1 2 1]/16;  %%%%%
g_ave_wg = imfilter(g_gaussian,w_1,'conv','symmetric','same');
g_ave_sp = imfilter(g_salt_pepper,w_1,'conv','symmetric','same');

figure(4);
subplot(1,2,1);
imshow(g_ave_wg,[0 1]);
xlabel('g).Result of weighted average filter');

subplot(1,2,2);
h = imhist(g_ave_wg)/(M*N);
bar(0:1/255:1,h);
axis([-.1 1.1 0 0.05]),grid;
axis square;
xlabel('h).The histogram of k)');
ylabel('Number of pixels');


figure(7);
subplot(1,2,1);
imshow(g_ave_sp,[0 1]);
xlabel('m).Result of weighted average filter');

subplot(1,2,2);
h = imhist(g_ave_sp)/(M*N);
bar(0:1/255:1,h);
axis([-.1 1.1 0 0.55]),grid;
axis square;
xlabel('n).The histogram of m)');
ylabel('Number of pixels');
```

## 锐化滤波器(Sharpening Spatial Filter)

锐化滤波器用于增强图像的细节信息。其基本原理是假设图像的细节部分对应高频成分，因此锐化滤波与平滑滤波是相反的操作。

对于一维函数，其一阶微分表示为：

$$
\frac{\partial f}{\partial x}=f(x+1)-f(x)
$$

从图像处理的角度来看，这种微分操作会导致像素差值的坐标偏移，称为前向差分。同样存在后向差分。为避免这种偏移，通常将前向差分和后向差分结合使用，得到：

$$
\begin{aligned}
\frac{\partial^2 f}{\partial x^2} &= \big(f(x+1)-f(x)\big) + \big(f(x-1)-f(x)\big) \\
&= f(x-1) - 2f(x) + f(x+1)
\end{aligned}
$$

将二阶微分扩展到二维图像，得到：

$$
\begin{aligned}
\frac{\partial^2 f}{\partial x^2} &= f(x-1, y) - 2f(x, y) + f(x+1, y) \\
\frac{\partial^2 f}{\partial y^2} &= f(x, y-1) - 2f(x, y) + f(x, y+1) \\
{\nabla^2} f &= \frac{\partial^2 f}{\partial x^2} + \frac{\partial^2 f}{\partial y^2} \\
\end{aligned}
$$

这就是四方向拉普拉斯滤波器。为增强微分效果，可以在斜方向添加微分分量，得到八方向拉普拉斯滤波器。两种滤波器的频率响应如下：

![四方向的拉普拉斯滤波器频响](/assets/resource/Spatial-Filtering/4-direction-laplacian-filter-frequency-response.jpeg){: width="600" height="600"}
![八方向的拉普拉斯滤波器频响](/assets/resource/Spatial-Filtering/8-direction-laplacian-filter-frequency-response.jpeg){: width="600" height="600"}

八方向拉普拉斯滤波器对高频成分的增强效果更强。其低频部分最小值为0，意味着滤波后仅保留图像的高频成分（即边缘信息）。因此，用于图像锐化时，需要把滤波结果与原图像合成。注意这里拉普拉斯核的中心系数为负（$-4$），所以应当用原图减去滤波结果，即$g = f - \nabla^2 f$，其等效的幅频特性为$1 - H(\omega)$，在保持低频成分不变的同时增强高频成分。

![拉普拉斯滤波器结果](/assets/resource/Spatial-Filtering/laplacian-filter-results.jpeg){: width="600" height="600"}

#### Matlab 代码
```matlab
close all;
clear all;

%% -------------Sharpening Spatial Filters-----------------
f = imread('blurry_moon.tif');
f = mat2gray(f,[0 255]);

w_L = [0  1 0
       1 -4 1
       0  1 0];
g_L_without  = imfilter(f,w_L,'conv','symmetric','same');
g_L = mat2gray(g_L_without);
g = f - g_L_without;
g = mat2gray(g ,[0 1]);

figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image');

subplot(1,2,2);
imshow(g_L_without,[0 1]);
xlabel('b).The Laplacian');

figure();
subplot(1,2,1);
imshow(g_L,[0 1]);
xlabel('c).The Laplacian with scaling');

subplot(1,2,2);
imshow(g,[0 1]);
xlabel('d).Result Image');

%% ------------------------
[M,N] = size(f);
[H,w1,w2] = freqz2(w_L,N,M);
figure();
subplot(1,2,1);
mesh(w1(1:10:N)*pi,w2(1:10:M)*pi,abs(H(1:10:M,1:10:N)));
axis([-pi pi -pi pi 0 12]);
xlabel('\omega_1 [rad]');ylabel('\omega_2 [rad]');
zlabel('|H(e^{j\omega_1},e^{j\omega_2})|');


%figure();
subplot(1,2,2);
mesh(w1(1:10:N)*pi,w2(1:10:M)*pi,unwrap(angle(H(1:10:M,1:10:N))));
axis([-pi pi -pi pi -pi pi]);
xlabel('\omega_1 [rad]');ylabel('\omega_2 [rad]');
zlabel('\theta [rad]');
```

## 高提升滤波(Highboost Filter)

高提升滤波用于增强图像清晰度。其处理步骤为：首先对图像进行模糊处理，然后从原图中减去模糊结果，得到反锐化掩模，最后将掩模叠加回原图。

数学表达式如下：

$$
\begin{aligned}
g_{mask}(x, y) = f(x,y) - \overline{f}(x,y)
\end{aligned}
$$

$$
\begin{aligned}
g(x, y) = f(x,y) + k \cdot g_{mask}(x,y)
\end{aligned}
$$

当$k=1$时，称为反锐化掩模；当$k>1$时，称为高提升滤波。本质上，高提升滤波也是一种锐化滤波，通过增强图像的边缘和跳变部分来提高清晰度。

以下实验结果展示了高提升滤波的效果：

![高提升滤波结果](/assets/resource/Spatial-Filtering/image-77th-row-high-boost-results.jpeg){: width="300" height="300"}

为深入理解高提升滤波的原理，我们分析图像第77行的灰度值分布：

![图像77行灰度曲线](/assets/resource/Spatial-Filtering/image-77th-row-intensity-curve.jpeg){: width="600" height="600"}

原图与模糊图像的差值如下：

![图像77行灰度差曲线](/assets/resource/Spatial-Filtering/image-77th-row-intensity-difference-curve.jpeg){: width="300" height="300"}

可以看出，边缘部分被显著增强。将差值乘以特定系数后叠加回原图，得到高提升滤波结果：

![图像77行高提升结果](/assets/resource/Spatial-Filtering/image-77th-row-high-boost-results.jpeg){: width="300" height="300"}

从曲线可以看出，在灰度变化剧烈的边缘处，高提升滤波增强了灰度过渡，使文字在视觉上更加清晰。

#### Matlab 代码
```matlab
close all;
clear all;

%% -------------Unsharp Masking and Highboost Filtering-----------------
close all;
clear all;

f = imread('dipxe_text.tif');
f = mat2gray(f,[0 255]);

w_Gaussian = fspecial('gaussian',[3,3],1);
g_Gaussian = imfilter(f,w_Gaussian,'conv','symmetric','same');

g_mask = f - g_Gaussian;

g_Unsharp = f + g_mask;
g_hb = f + (4.5 * g_mask);
f = mat2gray(f,[0 1]);

figure();
subplot(2,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image');

subplot(2,2,2);
imshow(g_Gaussian,[0 1]);
xlabel('b).Result of Gaussian Filter');

subplot(2,2,3);
imshow(mat2gray(g_mask),[0 1]);
xlabel('a).Unsharp Mask');

subplot(2,2,4);
imshow(g_hb,[0 1]);
xlabel('b).Result of Highboost Filter');


%%
[M,N] = size(f);

figure();
%subplot(1,2,1);
plot(1:N,f(77,1:N),'r');
axis([1,N,0,1]),grid;
axis square;
xlabel('a).Original Image(77th row)');
ylabel('intensity level');

figure();
%subplot(1,2,2);
plot(1:N,f(77,1:N),'r',1:N,g_Gaussian(77,1:N),'--b');
legend('Original','Result');
axis([1,N,0,1]),grid;
axis square;
xlabel('b).Result of gaussian filter(77th row)');
ylabel('intensity level');

figure();
%subplot(1,2,1);
plot(1:N,g_mask(77,1:N));
axis([1,N,-.1,.1]),grid;
axis square;
xlabel('c).Result of gaussian filter (77th row)');
ylabel('intensity level');

figure();
%subplot(1,2,2);
plot(1:N,g_hb(77,1:N));
axis([1,N,0,1.1]),grid;
axis square;
xlabel('d).Result of Highboost Filtering(77th row)');
ylabel('intensity level');
```

## 索贝尔滤波器(Sobel Filter)

索贝尔滤波器是另一种常用的边缘检测滤波器。其原理与锐化滤波器类似，通过一阶微分保留边缘信息，同时滤除平滑区域。

从纵向来看，该滤波器是一个中心一阶差分运算，具有高通滤波特性，因此能够提取图像边缘。从横向来看，它又是一个加权平均滤波器，具有一定的平滑作用。索贝尔滤波器由以下两个滤波器组合而成：

![索贝尔滤波核](/assets/resource/Spatial-Filtering/sobel-filter-kernel.jpeg){: width="600" height="600"}

索贝尔滤波器有两个方向的频率响应，能够有效提取图像边缘信息。从频域角度来看，它保留了图像的中频段信息：

![索贝尔滤波频响1](/assets/resource/Spatial-Filtering/sobel-filter-frequency-response-1.jpeg){: width="600" height="600"}
![索贝尔滤波频响2](/assets/resource/Spatial-Filtering/sobel-filter-frequency-response-2.jpeg){: width="600" height="600"}

#### Matlab 代码
```matlab
close all;
clear all;

%% -------------The Gradient-----------------
f = imread('contact_lens_original.tif');
f = mat2gray(f,[0 255]);

sobel_x = [-1 -2 -1;
            0  0  0;
            1  2  1];
sobel_y = [-1  0  1;
           -2  0  2;
           -1  0  1];

g_x = abs(imfilter(f,sobel_x,'conv','symmetric','same'));        
g_y = abs(imfilter(f,sobel_y,'conv','symmetric','same'));   
g_sobel = g_x + g_y;

figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image');

subplot(1,2,2);
imshow(g_sobel,[0 1]);
xlabel('b).Result of Sobel Operators');

figure();
subplot(1,2,1);
imshow(g_x,[0 1]);
xlabel('c).Result of Sx');

subplot(1,2,2);
imshow(g_y,[0 1]);
xlabel('d).Result of Sy');


%% ------------------------
M = 64;
N = 64;
[H,w1,w2] = freqz2(sobel_x,N,M);
figure();
subplot(1,2,1);
mesh(w1(1:N)*pi,w2(1:M)*pi,abs(H(1:M,1:N)));
axis([-pi pi -pi pi 0 12]);
xlabel('\omega_1 [rad]');ylabel('\omega_2 [rad]');
zlabel('|H(e^{j\omega_1},e^{j\omega_2})|');


%figure();
subplot(1,2,2);
mesh(w1(1:N)*pi,w2(1:M)*pi,unwrap(angle(H(1:M,1:N))));
axis([-pi pi -pi pi -pi pi]);
xlabel('\omega_1 [rad]');ylabel('\omega_2 [rad]');
zlabel('\theta [rad]');


[H,w1,w2] = freqz2(sobel_y,N,M);
figure();
subplot(1,2,1);
mesh(w1(1:N)*pi,w2(1:M)*pi,abs(H(1:M,1:N)));
axis([-pi pi -pi pi -12 12]);
xlabel('\omega_1 [rad]');ylabel('\omega_2 [rad]');
zlabel('|H(e^{j\omega_1},e^{j\omega_2})|');

%figure();
subplot(1,2,2);
mesh(w1(1:N)*pi,w2(1:M)*pi,unwrap(angle(H(1:M,1:N))));
axis([-pi pi -pi pi -pi pi]);
xlabel('\omega_1 [rad]');ylabel('\omega_2 [rad]');
zlabel('\theta [rad]');
```



