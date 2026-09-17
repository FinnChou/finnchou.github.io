---
layout: post
title: "Frequency Domain Filter : 低通滤波"
date: 2013-12-08 12:42:43 +0800
categories: 数字图像处理
tags: [图像处理, 低通滤波, 频域滤波]
math: true
image:
  path: /assets/resource/og/Frequency-Domain-Filter-1.png
  alt: "Frequency Domain Filter : 低通滤波"
---

本文从频率域角度对之前文章中介绍的空间域滤波器进行分析。主要利用傅里叶变换将空间域图像转换到频域，在频域中进行数字图像处理。这部分内容极其重要，因为频域处理能够解决空间域无法完成的图像增强任务。文章首先从数学角度分析图像在频域中的特性，然后重点介绍滤波器在频域中的性质。

### 傅里叶变换与频域

在之前的文章中，我们已经进行过一些基本的图像处理。例如，使用低通滤波可以模糊图像，也具有一定的降噪作用。这些都是在空间域内进行的滤波处理，主要依靠卷积计算实现。首先，从连续的一维卷积入手：

$$
\begin{aligned}
f(t) \star h(t) = \int_{-\infty}^{+\infty} f(\tau) h(t - \tau) d\tau
\end{aligned}
$$

这里使用 $\star$ 表示卷积操作。将上式进行傅里叶变换，可得：

$$
\begin{aligned}
\Im[f(t) \star h(t)] &= \Im \Big[ {\int_{-\infty}^{+\infty} f(\tau) h(\tau - t) d\tau} \Big] \\
                 &= \int_{-\infty}^{+\infty} \Big[ {\int_{-\infty}^{+\infty} f(\tau) h(t - \tau) d\tau} \Big] e^{-j 2\pi \mu t} dt \\
                 &= \int_{-\infty}^{+\infty} \Big[ H(\mu ) e^{-j 2\pi \mu \tau}  \Big] f(\tau) d\tau = H(\mu) F(\mu)
\end{aligned}
$$

从这个推导中，我们得到一个重要结论：函数$f(t)$与$h(t)$的卷积结果，等于它们傅里叶变换$F(\mu)$与$H(\mu)$的乘积。简洁表述如下：

$$
\begin{aligned}
f(t) \star h(t) \xrightarrow{DFT} H(\mu)F(\mu) \\
f(t) \star h(t) \xleftarrow{IDFT} H(\mu)F(\mu) \\
\end{aligned}
$$

将其扩展到二维情况，同样关系依然成立：

$$
\begin{aligned}
f(x,y) \star h(x,y) \xrightarrow{DFT} H(u,v)F(u,v) \\
f(x,y) \star h(x,y) \xleftarrow{IDFT} H(u,v)F(u,v) \\
\end{aligned}
$$

至此，基本原理已经明确。我们看到的图像都是空间域的表现形式，无法直接辨识频域中的图像。要进行频域滤波处理，首先需要进行傅里叶变换，然后在频域中直接进行滤波处理，最后通过反傅里叶变换转回空间域。

在开始频域滤波之前，还有一点需要注意。以一维信号为例，其傅里叶变换是以$2\pi$为周期的函数。我们通常使用$[-\pi,\pi]$范围来表示某个信号的傅里叶变换，如下图所示：

![频率域信号示例](/assets/resource/Frequency-Domain-Filter-1/frequency_domain_signal_example.jpeg){: width="300" height="300"}

越靠近0点的成分频率越低，越靠近$-\pi$与$\pi$的成分频率越高。对于图像而言，在Matlab中使用fft2()函数计算傅里叶变换：

```matlab
g = fft2(f)
```

这段代码计算出的是$[0,2\pi)$范围内、共$M \times N$个点的傅里叶变换，且直流分量位于左上角。为便于理解，下图展示了该代码计算的图像傅里叶变换范围（右）以及与之等效的一维傅里叶变换范围（左）：

![fft变换示例1](/assets/resource/Frequency-Domain-Filter-1/fft_transform_example1.jpeg){: width="600" height="600"}

在频域做滤波时，DFT隐含的是圆周卷积，图像一侧的内容会绕回到另一侧，造成所谓的缠绕误差(wraparound error)。为避免这一问题，需要把图像补零延拓到$P \ge 2M-1$、$Q \ge 2N-1$，通常直接取$P=2M$、$Q=2N$。补零并不改变频率的取值范围，只是让频率采样更密。实现代码如下：

```matlab
P = 2*M;
Q = 2*N;
F = fft2(f,P,Q);
```

下图展示了这段代码计算的傅里叶变换范围（右）和相应的一维傅里叶变换范围（左）。得到的图像$F(u,v)$尺寸为$P \times Q$：

![fft变换示例2](/assets/resource/Frequency-Domain-Filter-1/fft_transform_example2.jpeg){: width="600" height="600"}

我们需要对其进行平移，如下图所示，目标是获取粉色区域的频谱：

![fft变换示例3](/assets/resource/Frequency-Domain-Filter-1/fft_transform_example3.jpeg){: width="600" height="600"}

接下来从数学上分析如何获取这部分频谱。对于傅里叶变换，存在以下性质：

$$
\begin{aligned}
\Im \Big[ f(x,y) e^{j2\pi (\frac{u_0}{M}x + \frac{v_0}{N}y)} \Big] = F(u-u_0, v-v_0)
\end{aligned}
$$

这一特性称为平移特性。针对粉色部分的频谱，我们可以得到：

$$
\begin{aligned}
\Im \Big[ f(x,y) e^{j2\pi (\frac{u_0}{M}x + \frac{v_0}{N}y)} \Big] = \Im \Big[ f(x,y) e^{j\pi (x+y)} \Big] = \Im \Big[ f(x,y) (-1)^{x+y} \Big] 
\end{aligned}
$$

由此，我们获得了粉色区域的频谱。在傅里叶频谱图像中，越靠近中间的部分代表低频成分。实现这一变换的Matlab代码如下：

```matlab
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
```

代码执行结果如下图所示：

![fft变换示例4](/assets/resource/Frequency-Domain-Filter-1/fft_transform_example4.jpeg){: width="600" height="600"}

总结频域滤波的步骤：
1. 先对图像进行频域中心化平移，然后计算原图像$f(x,y)$的DFT，得到傅里叶谱$F(u,v)$
2. 与频域滤波器相乘
3. 计算$G(u,v)$的IDFT，然后进行频域逆平移（移回原位置），结果可能存在微小虚部，可直接忽略
4. 使用ifft2函数进行IDFT变换，得到尺寸为$P \times Q$的图像，取左上角$M \times N$区域作为最终结果

### 理想低通滤波器
在频率域中，通带半径为$D_0$的理想低通滤波器表达式为：

$$
\begin{equation}
H(u,v) = \left \{
\begin{array}{l}
1　, D(u, v) \le D_0 \\
0　, D(u, v) > D_0 \\ 
\end{array}
\right.
\end{equation}
$$

其中$D(u,v)$是两点间的欧式距离：

$$
\begin{aligned}
D(u, v) = \sqrt{\Big(u - \frac{P}{2}\Big)^2 + \Big(v - \frac{Q}{2}\Big)^2}
\end{aligned}
$$

使用理想低通滤波器的效果如下。由于滤除了高频成分，图像变得模糊。同时，因为理想滤波器的频率响应过渡特性过于陡峭，会产生明显的振铃现象：

![理想滤波器效果1](/assets/resource/Frequency-Domain-Filter-1/ideal_filter_result1.jpeg){: width="600" height="600"}
![理想滤波器效果2](/assets/resource/Frequency-Domain-Filter-1/ideal_filter_result2.jpeg){: width="600" height="600"}

### 巴特沃斯低通滤波器
巴特沃斯低通滤波器的表达式为：

$$
\begin{aligned}
H(u, v) = \frac{1}{1 + (D(u,v) / D_0)^{2n}}
\end{aligned}
$$

同样，$D_0$表示通带半径，$n$表示巴特沃斯滤波器的阶数。从表达式可以看出，随着阶数$n$的增加，巴特沃斯滤波器的特性越来越接近理想滤波器：

![巴特沃斯低通滤波器效果1](/assets/resource/Frequency-Domain-Filter-1/butterworth_filter_result1.jpeg){: width="600" height="600"}
![巴特沃斯低通滤波器效果2](/assets/resource/Frequency-Domain-Filter-1/butterworth_filter_result2.jpeg){: width="600" height="600"}


### 高斯低通滤波器

高斯低通滤波器的表达式为：

$$
\begin{aligned}
H(u, v) = e^{\frac{-D^2(u,v)}{2D_0^2}}
\end{aligned}
$$

同样，$D_0$表示通带半径。高斯滤波器的频率响应过渡特性非常平滑，因此不会产生振铃现象：

![高斯低通滤波器效果1](/assets/resource/Frequency-Domain-Filter-1/gaussian_filter_result1.jpeg){: width="600" height="600"}
![高斯低通滤波器效果2](/assets/resource/Frequency-Domain-Filter-1/gaussian_filter_result2.jpeg){: width="600" height="600"}


### Matlab 代码
```matlab
close all;
clear all;

%% ---------Ideal Lowpass Filters (Fre. Domain)------------
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
        if(D <= 60)  H_1(x+(P/2)+1,y+(Q/2)+1) = 1; end    
        if(D <= 160)  H_2(x+(P/2)+1,y+(Q/2)+1) = 1; end
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
xlabel('c).Ideal Lowpass filter(D=60)');

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
xlabel('f).Ideal Lowpass filter(D=160)');

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

%% ---------Butterworth Lowpass Filters (Fre. Domain)------------
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
        H_1(x+(P/2)+1,y+(Q/2)+1) = 1/(1+(D/D_0)^2);   
        H_2(x+(P/2)+1,y+(Q/2)+1) = 1/(1+(D/D_0)^6);
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
clc;
%% ---------Gaussian Lowpass Filters (Fre. Domain)------------
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
        H_1(x+(P/2)+1,y+(Q/2)+1) = exp(-(D*D)/(2*D_0*D_0));   
        D_0 = 160;
        H_2(x+(P/2)+1,y+(Q/2)+1) = exp(-(D*D)/(2*D_0*D_0));
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
close all;

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
xlabel('c)Gaussian Lowpass (D_{0}=60)');

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
xlabel('f).Gaussian Lowpass (D_{0}=160)');

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

