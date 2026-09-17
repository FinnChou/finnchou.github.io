---
layout: post
title: "Image Restoration : 逆滤波"
date: 2014-07-23 20:15:28 +0800
categories: 数字图像处理
tags: [图像处理, 图像复原, 逆滤波]
math: true
---

### 逆滤波的问题点
图像的退化，可以视为这样的一个过程：一个是退化函数的影响（致使图像模糊、褪色等），另一个是可加性噪声的影响。

![图像退化模型](/assets/resource/Image-Denoise-1/frequency_domain_signal.jpeg){: width="450" height="450"}

用算式表示为：

$$
\begin{aligned}
g(x,y) = h(x,y) \star f(x,y) + \eta (x,y)
\end{aligned}
$$

前几篇博文主要介绍的是可加性噪声 $\eta (x,y)$ 的去除，本文则主要介绍图像的逆滤波，即退化函数 $h(x,y)$ 的去除。然而，逆滤波在空间域内的处理是很不方便的。

简单地考虑，加法的逆运算是减法，乘法的逆运算是除法，微分的逆运算是积分。那么要去除卷积，就需要用到卷积的逆运算，也就是反卷积。但反卷积在空间域内究竟是一种什么样的运算形式，其实不必考虑得这么复杂。在之前的博文 📎 <a href="{{ site.baseurl }}/posts/Frequency-Domain-Filter-1/"> >> Frequency Domain Filter : 低通滤波 << </a> 中，我们已经得到了一个重要的结论：空间域内的卷积，就是频率域内的乘积。这样一来问题就简单了——频率域内的逆滤波运算，其实就是做除法。

通过傅里叶变换，可以得到频率域内的退化模型：

$$
\begin{aligned}
G(u,v) = H(u,v)F(u,v) + N(u,v)
\end{aligned}
$$

这个表达式中已经没有了卷积运算，只是简单的四则运算。所谓的去卷积或者逆滤波，就是将退化函数 $H(u,v)$ 去除的过程。这样看来，直接做除法就可以了：

$$
\begin{aligned}
\hat{F}(u,v) &= \frac{G(u,v)}{H(u,v)} \\
             &= F(u,v) + \frac{N(u,v)}{H(u,v)}
\end{aligned}
$$

这个表达式很有意思。首先，必须知道精确的退化函数 $H(u,v)$；其次，从展开式的第二项可以看出，如果退化函数 $H(u,v)$ 含有0值或者极小值，会使得噪声项 $N(u,v)/H(u,v)$ 变得极大。

综上所述，逆滤波的问题点有两个：

1. 退化函数 $H(u,v)$ 的推测。
2. 尽可能不让噪声项 $N(u,v)$ 影响画质。


### 两个退化函数的模型

#### 大气湍流模型
大气湍流模型的表达式如下所示。

$$
\begin{aligned}
H(u,v) = e^{-k(u^2+v^2)^{5/6}}
\end{aligned}
$$

这个模型很简单，与高斯低通滤波器非常相似。伴随着 $k$ 值的增大，得到的图像会越来越模糊。以下是这个模型的执行结果。

![大气湍流模型的执行结果](/assets/resource/Image-Restoration-1/atmospheric_turbulence_model.jpeg){: width="450" height="450"}

从表达式上可以看出，这个模型不会出现0值。不过，由于它与低通滤波器很相似，阻带部分的值都是极小的，这可能会使得图像的直接逆滤波失败，这一点在后文中还会提到。

#### 运动模糊模型
这个模型在Photoshop中也有一个同名的滤镜。详细的推导这里就不做了，模型的表达式如下所示。

$$
\begin{aligned}
H(u,v) = \frac{T \sin \left[ \pi (ua+vb) \right]}{\pi (ua+vb)} e^{-j\pi (ua+vb)}
\end{aligned}
$$

这里对几个参数说明一下：$T$ 表示曝光时间，$a$ 与 $b$ 分别表示水平移动量与垂直移动量。值得一提的是，不要忘记下面这样一个重要的极限。

$$
\begin{aligned}
\lim_{x \to 0} \frac{\sin x}{x} = 1
\end{aligned}
$$

在实现时需要对 $ua+vb=0$ 的点做特殊处理，直接取 $H=T$。

另外需要注意的是，运动模糊后的图像尺寸会发生变化。如果仍然按照原图的尺寸去截取，会造成图像成分的损失，复原时效果不会太好，而且难以判断效果不佳的原因究竟是成分的缺失还是噪声的干扰。因此这里适当扩展了图像的尺寸，以保留图像的全部成分。

此模型的执行结果如下所示。

![运动模糊模型](/assets/resource/Image-Restoration-1/motion_blur_model.jpeg){: width="450" height="450"}

![运动模糊模型的执行结果](/assets/resource/Image-Restoration-1/motion_blur_result.jpeg){: width="450" height="450"}


### 图像的逆滤波

#### 实验步骤与实验用图像
实验步骤是这样的：首先使用退化函数 $H(u,v)$ 处理图像，然后加上适当的可加性噪声 $N(u,v)$，再使用这样的图像进行逆滤波实验。

下面是实验用图像。噪声选用高斯噪声，均值为0、方差为0.08；退化函数则选用前面叙述的两种，一个是大气湍流模型，一个是运动模糊模型。

![大气湍流退化的实验用图像](/assets/resource/Image-Restoration-1/test_image_turbulence.jpeg){: width="450" height="450"}

![运动模糊退化的实验用图像](/assets/resource/Image-Restoration-1/test_image_motion_blur.jpeg){: width="450" height="450"}

#### 直接逆滤波
所谓直接逆滤波，就是不考虑噪声的影响，直接按下式进行逆滤波的方法。

$$
\begin{aligned}
\hat{F}(u,v) &= \frac{G(u,v)}{H(u,v)} \\
             &= F(u,v) + \frac{N(u,v)}{H(u,v)}
\end{aligned}
$$

对于大气湍流模型而言，直接逆滤波会得到很不理想的结果。下面是直接逆滤波的实验结果。

![直接逆滤波的结果](/assets/resource/Image-Restoration-1/direct_inverse_filter_failure.jpeg){: width="450" height="450"}

实验结果完全没有任何价值。观察其频谱可以发现，频谱的四角很亮，而原本应该最亮的直流分量反而看不到了——这正是前面分析的 $N(u,v)/H(u,v)$ 在 $H$ 极小处被放大所致。

因此，这里做一个限制处理：仅处理靠近直流分量的部分，其余部分不做处理，然后将处理完的结果通过一个10阶巴特沃斯低通滤波器，可以得到如下结果。

![加入限制处理后的直接逆滤波结果](/assets/resource/Image-Restoration-1/direct_inverse_filter_limited.jpeg){: width="450" height="450"}

这样一来，只需调整限制半径，就可以得到一个比之前好得多的结果。当然，这一招在运动模糊的图像面前就显得无力了。

#### 维纳滤波器
维纳滤波器的推导是一个相当复杂的过程，这里不作推导，直接来看结果，从中可以得到一些有用的结论。

$$
\begin{aligned}
\hat{F}(u,v) = \left[ \frac{1}{H(u,v)} \frac{\left| H(u,v) \right|^2}{\left| H(u,v) \right|^2 + K} \right] G(u,v)
\end{aligned}
$$

观察这个式子，对于选取得当的常数 $K$，有如下两个结论：

1. 对于退化函数很小的点，相对而言常数 $K$ 的值很大，此时修正项 $\frac{|H|^2}{|H|^2+K}$ 趋近于0，从而抑制了 $1/H(u,v)$ 的放大作用，使其不会变得过大。
2. 对于退化函数较大的点，相对而言常数 $K$ 的值很小，此时修正项趋近于1，$1/H(u,v)$ 基本保持不变。

也就是说，维纳滤波器相当于在直接逆滤波 $1/H(u,v)$ 的基础上乘了一个修正因子，在 $H$ 很小的地方主动压低增益，从而避免噪声被放大。下面是维纳滤波器的实验结果。

![维纳滤波器与直接逆滤波的比较](/assets/resource/Image-Restoration-1/wiener_filter_result.jpeg){: width="450" height="450"}

![维纳滤波器的频谱](/assets/resource/Image-Restoration-1/wiener_filter_spectrum.jpeg){: width="450" height="450"}

#### 约束最小二乘方滤波
这个方法的思路很好：将图像的能量作为评价图像平滑程度的度量，尽可能地将其平滑。设噪声的能量为一个定值，使用拉格朗日乘数法进行迭代求解。这种方法有很多变种，其中包括很著名的TV（Total Variation，全变分）模型。

在这里，使用本方法的目的是减少噪声对逆滤波的影响，其表达式如下所示。

$$
\begin{aligned}
\hat{F}(u,v) = \left[ \frac{1}{H(u,v)} \frac{\left| H(u,v) \right|^2}{\left| H(u,v) \right|^2 + \gamma \left| P(u,v) \right|^2} \right] G(u,v)
\end{aligned}
$$

将它与维纳滤波器的表达式对照可以发现，两者的形式是一致的，区别只在于维纳滤波器中的常数 $K$ 被替换为了 $\gamma |P(u,v)|^2$。这里的 $P(u,v)$ 是拉普拉斯算子的傅里叶变换，也就是说，修正项不再是一个与频率无关的常数，而是随频率变化的——这正是"尽可能平滑"这一约束在频率域中的体现。

这个滤波器可以在消除很严重的噪声的同时复原图像。将实验用图像的噪声方差提升到0.2，再进行滤波，可以得到如下结果。

![强噪声下维纳滤波与约束最小二乘方滤波的比较](/assets/resource/Image-Restoration-1/wiener_vs_clsf_high_noise.jpeg){: width="450" height="450"}

在噪声方差为0.2这样的强噪声条件下，维纳滤波器的结果（图a）中噪声依然比较明显，而约束最小二乘方滤波的结果（图c）则明显平滑许多，复原的效果更好。


### 示例代码

```matlab
close all;
clear all;
clc;

%% ----------init-----------------------------
f = imread('./original_DIP.tif');
f = mat2gray(f,[0 255]);

f_original = f;

[M,N] = size(f);

P = 2*M;
Q = 2*N;
fc = zeros(M,N);

for x = 1:1:M
    for y = 1:1:N
        fc(x,y) = f(x,y) * (-1)^(x+y);
    end
end

F_I = fft2(fc,P,Q);

figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image');

subplot(1,2,2);
imshow(log(1 + abs(F_I)),[ ]);
xlabel('b).Fourier spectrum of a).');

%% ------motion blur------------------
H = zeros(P,Q);
a = 0.02;
b = 0.02;
T = 1;
for x = (-P/2):1:(P/2)-1
     for y = (-Q/2):1:(Q/2)-1
        R = (x*a + y*b)*pi;
        if(R == 0)
            H(x+(P/2)+1,y+(Q/2)+1) = T;
        else H(x+(P/2)+1,y+(Q/2)+1) = (T/R)*(sin(R))*exp(-1i*R);
        end
     end
end

%% ------the atmospheric turbulence modle------------------
H_1 = zeros(P,Q);
k = 0.0025;
for x = (-P/2):1:(P/2)-1
     for y = (-Q/2):1:(Q/2)-1
        D = (x^2 + y^2)^(5/6);
        H_1(x+(P/2)+1,y+(Q/2)+1) = exp(-k*D);
     end
end

%% -----------noise------------------
a = 0;
b = 0.2;
n_gaussian = a + b .* randn(M,N);

Noise = fft2(n_gaussian,P,Q);

figure();
subplot(1,2,1);
imshow(n_gaussian,[-1 1]);
xlabel('a).Gaussian noise');

subplot(1,2,2);
imshow(log(1 + abs(Noise)),[ ]);
xlabel('b).Fourier spectrum of a).');

%% -----------degradation------------------
G = H .* F_I + Noise;
% G = H_1 .* F_I + Noise;
gc = ifft2(G);

gc = gc(1:1:M,1:1:N);
for x = 1:1:(M)
    for y = 1:1:(N)
        g(x,y) = gc(x,y) .* (-1)^(x+y);
    end
end

figure();
subplot(1,2,1);
imshow(abs(H),[ ]);
xlabel('c).The motion modle H(u,v)(a=0.02,b=0.02,T=1)');

subplot(1,2,2);
n = 1:1:P;
plot(n,abs(H(400,:)));
axis([0 P 0 1]);grid;
xlabel('H(n,400)');
ylabel('|H(u,v)|');

figure();
subplot(1,2,1);
imshow(real(g),[0 1]);
xlabel('d).Result image');

subplot(1,2,2);
imshow(log(1 + abs(G)),[ ]);
xlabel('e).Fourier spectrum of d). ');

%% --------------inverse filtering---------------------
%F = G ./ H;
%F = G ./ H_1;

for x = (-P/2):1:(P/2)-1
     for y = (-Q/2):1:(Q/2)-1
        D = (x^2 + y^2)^(0.5);
        if(D < 258)
            F(x+(P/2)+1,y+(Q/2)+1) = G(x+(P/2)+1,y+(Q/2)+1) ./ H_1(x+(P/2)+1,y+(Q/2)+1);
        % no noise D < 188
        % noise    D < 56
        else F(x+(P/2)+1,y+(Q/2)+1) = G(x+(P/2)+1,y+(Q/2)+1);
        end
     end
end

% Butterworth Lowpass Filter
H_B = zeros(P,Q);
D_0 = 70;
for x = (-P/2):1:(P/2)-1
     for y = (-Q/2):1:(Q/2)-1
        D = (x^2 + y^2)^(0.5);
        H_B(x+(P/2)+1,y+(Q/2)+1) = 1/(1+(D/D_0)^20);
     end
end

F = F .* H_B;

f = real(ifft2(F));
f = f(1:1:M,1:1:N);

for x = 1:1:(M)
    for y = 1:1:(N)
        f(x,y) = f(x,y) * (-1)^(x+y);
    end
end

%% ------show Result------------------
figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Result image');

subplot(1,2,2);
imshow(log(1 + abs(F)),[ ]);
xlabel('b).Fourier spectrum of a).');

%% ----------Wiener filters-----------
% K = 0.000014;
K = 0.02;
%H_Wiener = ((abs(H_1).^2)./((abs(H_1).^2)+K)).*(1./H_1);
H_Wiener = ((abs(H).^2)./((abs(H).^2)+K)).*(1./H);

F_Wiener = H_Wiener .*  G;
f_Wiener = real(ifft2(F_Wiener));
f_Wiener = f_Wiener(1:1:M,1:1:N);

for x = 1:1:(M)
    for y = 1:1:(N)
        f_Wiener(x,y) = f_Wiener(x,y) * (-1)^(x+y);
    end
end

[SSIM_Wiener mssim] = ssim_index(f_Wiener,f_original,[0.01 0.03],ones(8),1);
SSIM_Wiener

figure();
subplot(1,2,1);
imshow(f_Wiener,[0 1]);
xlabel('d).Result image by Wiener filter');

subplot(1,2,2);
imshow(log(1+abs(F_Wiener)),[ ]);
xlabel('c).Fourier spectrum of c).');

figure();
n = 1:1:P;
plot(n,abs(F(400,:)),'r-',n,abs(F_Wiener(400,:)),'b-');
axis([0 P 0 500]);grid;
xlabel('Number of rows(400th column)');
ylabel('Fourier amplitude spectrum');
legend('F(u,v)','F_{Wiener}(u,v)');

figure();
subplot(1,2,1);
imshow(log(1 + abs(H_Wiener)),[ ]);
xlabel('a).F_{Wiener}(u,v).');

subplot(1,2,2);
n = 1:1:P;
plot(n,abs(H_Wiener(400,:)));
axis([0 P 0 80]);grid;
xlabel('Number of rows(400th column)');
ylabel('Amplitude spectrum');

%% ------------Constrained least squares filtering---------
p_laplacian = zeros(M,N);
Laplacian = [ 0 -1  0;
             -1  4 -1;
              0 -1  0];
p_laplacian(1:3,1:3) = Laplacian;

for x = 1:1:M
    for y = 1:1:N
        p_laplacian(x,y) = p_laplacian(x,y) * (-1)^(x+y);
    end
end
P_laplacian = fft2(p_laplacian,P,Q);

F_C = zeros(P,Q);
r = 0.2;
H_clsf = ((H')./((abs(H).^2)+r.*P_laplacian));

F_C = H_clsf .* G;

f_c = real(ifft2(F_C));
f_c = f_c(1:1:M,1:1:N);

for x = 1:1:(M)
   for y = 1:1:(N)
       f_c(x,y) = f_c(x,y) * (-1)^(x+y);
    end
end

figure();
subplot(1,2,1);
imshow(f_c,[0 1]);
xlabel('e).Result image by constrained least squares filter (r = 0.2)');

subplot(1,2,2);
imshow(log(1 + abs(F_C)),[ ]);
xlabel('f).Fourier spectrum of c).');

[SSIM_CLSF mssim] = ssim_index(f_c,f_original,[0.01 0.03],ones(8),1);

figure();
subplot(1,2,1);
imshow(log(1 + abs(H_clsf)),[ ]);
xlabel('a).F_{clsf}(u,v).');

subplot(1,2,2);
n = 1:1:P;
plot(n,abs(H_clsf(400,:)));
axis([0 P 0 80]);grid;
xlabel('Number of rows(400th column)');
ylabel('Amplitude spectrum');
```


### 总结
本文讨论了图像复原中退化函数的去除，也就是逆滤波的问题。

逆滤波的核心困难在于，直接做除法 $\hat{F} = G/H$ 会把噪声项放大为 $N(u,v)/H(u,v)$，在退化函数 $H$ 取值极小的频率处，这一项会变得极大，从而彻底淹没图像本身的信息。本文介绍的几种方法，本质上都是在处理这一问题：直接逆滤波通过限制处理半径，回避了 $H$ 过小的区域；维纳滤波器引入常数 $K$，在 $H$ 较小处主动压低增益；约束最小二乘方滤波则进一步将这个常数替换为与频率相关的 $\gamma |P(u,v)|^2$，以图像的平滑程度作为约束，在强噪声条件下取得了更好的复原效果。
