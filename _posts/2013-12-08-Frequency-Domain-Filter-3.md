---
layout: post
title: "Frequency Domain Filter : 带阻滤波器与陷波滤波器"
date: 2013-12-08 18:02:49 +0800
categories: 数字图像处理
tags: [图像处理, 频域滤波]
math: true
image:
  path: /assets/resource/og/Frequency-Domain-Filter-3.png
  alt: "Frequency Domain Filter : 带阻滤波器与陷波滤波器"
---

### 带阻滤波器
与低通和高通滤波器类似，带阻滤波器也具有三种特性类型：高斯型、巴特沃斯型和理想型。它们的数学表达式如下：

| 理想带阻滤波器     | $$ H_{BR}(u,v) = \left \{ \begin{array}{l} 0　, D_0 - \frac{W}{2} \le D < D_0 + \frac{W}{2}\\ 1　, other \\ \end{array} \right.$$ |
| 巴特沃斯带阻滤波器  | $$ H_{BR}(u,v) = \frac{1}{1 + \Big( \frac{DW}{D^2 - D_0^2} \Big)^{2n}} $$ |
| 高斯带阻滤波器     | $$ H_{BR}(u, v) = 1 - e^{-\Big[ \frac{D^2 - D_0^2}{DW} \Big]^2} $$ |

而带通滤波器则可以通过将带阻滤波器的通带和阻带取反获得：

$$
\begin{aligned}
H_{BP}(u, v) = 1 - H_{BR}(u, v)
\end{aligned}
$$

带阻滤波器常用于去除周期性噪声。为了展示其特性，我们首先在一幅图像的频率域内添加几个孤立的亮点，然后对被污染的频谱图执行IDFT操作，得到的空间域图像会被严重的周期噪声污染。

![带阻滤波器-原始图像与频谱](/assets/resource/Frequency-Domain-Filter-2/bandstop_original.jpeg){: width="600" height="600"}
![带阻滤波器-加噪图像与频谱](/assets/resource/Frequency-Domain-Filter-2/bandstop_noisy.jpeg){: width="600" height="600"}

可以看到，图像的原始内容完全被严重的周期性噪声淹没。如果仅通过观察图像本身，在空间域内执行滤波操作去除噪声时，很难确定合适的滤波器参数。但在频率域内考虑去噪问题，我们只需将频率域中孤立的亮点抹除即可。此时，使用带阻滤波器能够获得很好的去噪效果。为避免振铃现象，我们选择使用3次的巴特沃斯带阻滤波器。下图展示了所使用的滤波器及实际去噪效果：

![带阻滤波器振幅特性](/assets/resource/Frequency-Domain-Filter-2/bandstop_filter_amplitude.jpeg){: width="600" height="600"}
![带阻滤波器滤波效果](/assets/resource/Frequency-Domain-Filter-2/bandstop_filter_result.jpeg){: width="600" height="600"}

#### Matlab 代码
```matlab
close all;
clear all;
clc;
%% ---------------------Add Noise-------------------------
f = imread('left.tif');
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

H_NP = ones(P,Q);

for x = (-P/2):1:(P/2)-1
     for y = (-Q/2):1:(Q/2)-1
        D = 2;
        
        v_k = -200; u_k = 150;
        D_k = ((x+u_k)^2 + (y+v_k)^2)^(0.5);
        H_NP(x+(P/2)+1,y+(Q/2)+1) = H_NP(x+(P/2)+1,y+(Q/2)+1) * 1/(1+(D/D_k)^4);
        D_k = ((x-u_k)^2 + (y-v_k)^2)^(0.5);
        H_NP(x+(P/2)+1,y+(Q/2)+1) = H_NP(x+(P/2)+1,y+(Q/2)+1) * 1/(1+(D/D_k)^4);
        
        v_k = 200; u_k = 150;
        D_k = ((x+u_k)^2 + (y+v_k)^2)^(0.5);
        H_NP(x+(P/2)+1,y+(Q/2)+1) = H_NP(x+(P/2)+1,y+(Q/2)+1) * 1/(1+(D/D_k)^4);
        D_k = ((x-u_k)^2 + (y-v_k)^2)^(0.5);
        H_NP(x+(P/2)+1,y+(Q/2)+1) = H_NP(x+(P/2)+1,y+(Q/2)+1) * 1/(1+(D/D_k)^4);
        
        v_k = 0; u_k = 250;
        D_k = ((x+u_k)^2 + (y+v_k)^2)^(0.5);
        H_NP(x+(P/2)+1,y+(Q/2)+1) = H_NP(x+(P/2)+1,y+(Q/2)+1) * 1/(1+(D/D_k)^4);
        D_k = ((x-u_k)^2 + (y-v_k)^2)^(0.5);
        H_NP(x+(P/2)+1,y+(Q/2)+1) = H_NP(x+(P/2)+1,y+(Q/2)+1) * 1/(1+(D/D_k)^4);
        
        v_k = 250; u_k = 0;
        D_k = ((x+u_k)^2 + (y+v_k)^2)^(0.5);
        H_NP(x+(P/2)+1,y+(Q/2)+1) = H_NP(x+(P/2)+1,y+(Q/2)+1) * 1/(1+(D/D_k)^4);
        D_k = ((x-u_k)^2 + (y-v_k)^2)^(0.5);
        H_NP(x+(P/2)+1,y+(Q/2)+1) = H_NP(x+(P/2)+1,y+(Q/2)+1) * 1/(1+(D/D_k)^4);
        
        
        H_NP(x+(P/2)+1,y+(Q/2)+1) = 1 + 700*(1 - H_NP(x+(P/2)+1,y+(Q/2)+1));
     end
end

G_Noise = F .* H_NP;

g_noise = real(ifft2(G_Noise));
g_noise = g_noise(1:1:M,1:1:N);     

for x = 1:1:M
    for y = 1:1:N
        g_noise(x,y) = g_noise(x,y) * (-1)^(x+y);
    end
end


%% ---------Bandreject Filters (Fre. Domain)------------
H_1 = ones(P,Q);

for x = (-P/2):1:(P/2)-1
     for y = (-Q/2):1:(Q/2)-1
        D = (x^2 + y^2)^(0.5);
        D_0 = 250;
        W = 30;
        H_1(x+(P/2)+1,y+(Q/2)+1) = 1/(1+((D*W)/((D*D) - (D_0*D_0)))^6);   
     end
end

G_1 = H_1 .* G_Noise;

g_1 = real(ifft2(G_1));
g_1 = g_1(1:1:M,1:1:N);     

for x = 1:1:M
    for y = 1:1:N
        g_1(x,y) = g_1(x,y) * (-1)^(x+y);
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
subplot(1,2,2);
imshow(log(1 + abs(G_Noise)),[ ]);
xlabel('c).Fourier spectrum of b');

subplot(1,2,1);
imshow(g_noise,[0 1]);
xlabel('b).Result of add noise');


figure();
subplot(1,2,1);
imshow(H_1,[0 1]);
xlabel('d).Butterworth Notch filter(D=355 W=40 n =2)');

subplot(1,2,2);
h = mesh(1:20:Q,1:20:P,H_1(1:20:P,1:20:Q));
set(h,'EdgeColor','k');
axis([0 Q 0 P 0 1]);
xlabel('u');ylabel('v');
zlabel('|H(u,v)|');


figure();
subplot(1,2,2);
imshow(log(1 + abs(G_1)),[ ]);
xlabel('e).Fourier spectrum of f');

subplot(1,2,1);
imshow(g_1,[0 1]);
xlabel('f).Result of denoise');
```

### 陷波滤波器(Notch Filter)
陷波滤波器同样用于去除周期噪声。虽然带阻滤波器也能去除周期噪声，但它会对噪声以外的频率成分也产生衰减。而陷波滤波器的优势在于它只对特定点进行衰减，对其余频率成分几乎不造成损失。下图有助于理解这一特性：

![带有周期噪声的原始图像与频谱](/assets/resource/Frequency-Domain-Filter-2/notch_original.jpeg){: width="600" height="600"}

从空间域来看，图像存在明显的周期性噪声。在其傅里叶频谱中，我们可以清晰地看到噪声所在位置（图中用红圈标注，这些红圈不是数据的一部分）。使用带阻滤波器难以精确地去除这些噪声，因为可能会导致图像损失较大。而我们只需要精确地衰减频谱中那些孤立的亮点，就能获得很好的效果。陷波滤波器正是为此目的而设计的，其表达式如下：

$$
\begin{aligned}
H_{NR}(u, v) = \prod_{k=1}^{K} H_k(u,v) H_{-k}(u,v)
\end{aligned}
$$

由于傅里叶变换的对称性，傅里叶频谱上不可能只存在单个孤立的噪声亮点。对于每个孤立噪点$k$，必然存在一个关于原点对称的另一个孤立噪点$-k$。将巴特沃斯带阻滤波器的表达式代入，陷波滤波器可以表示为：

$$
\begin{aligned}
H_{NR}(u, v) = \prod_{k=1}^{K} \Biggl[  \frac{1}{1 + \Big( D_{0k} / D_{k}(u,v) \Big)^{2n}} \Biggl] \Biggl[  \frac{1}{1 + \Big( D_{0k} / D_{-k}(u,v) \Big)^{2n}} \Biggl] 
\end{aligned}
$$

其中$D_{-k}(u,v)$与$D_{k}(u,v)$表示需要去除的噪声点到当前点的距离，计算方式如下：

$$
\begin{aligned}
D_{k}(u,v) &= \sqrt{ \Bigg( u - \frac{P}{2} - u_k \Bigg)^2 + \Bigg( v - \frac{Q}{2} - v_k \Bigg)^2 } \\
D_{-k}(u,v) &= \sqrt{ \Bigg( u - \frac{P}{2} + u_k \Bigg)^2 + \Bigg( v - \frac{Q}{2} + v_k \Bigg)^2 } \\ 
\end{aligned}
$$

针对图像中的周期性噪声，我们只需要确定孤立亮点的坐标值即可。在本例中，我们手动确定这些值，并设计如下滤波器进行去噪：

![陷波滤波器振幅特性](/assets/resource/Frequency-Domain-Filter-2/notch_filter_amplitude.jpeg){: width="600" height="600"}

处理结果如下所示。可以看到，噪声已被有效去除，图像质量得到显著改善：

![陷波滤波器去噪结果](/assets/resource/Frequency-Domain-Filter-2/notch_filter_result.jpeg){: width="600" height="600"}

#### Matlab 代码
```matlab
close all;
clear all;
clc;

%% ---------Butterworth Notch filter (Fre. Domain)------------
f = imread('car_75DPI_Moire.tif');
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

H_NF = ones(P,Q);

for x = (-P/2):1:(P/2)-1
     for y = (-Q/2):1:(Q/2)-1
        D = 30;
        
        v_k = 59; u_k = 77;
        D_k = ((x+u_k)^2 + (y+v_k)^2)^(0.5);
        H_NF(x+(P/2)+1,y+(Q/2)+1) = H_NF(x+(P/2)+1,y+(Q/2)+1) * 1/(1+(D/D_k)^4);
        D_k = ((x-u_k)^2 + (y-v_k)^2)^(0.5);
        H_NF(x+(P/2)+1,y+(Q/2)+1) = H_NF(x+(P/2)+1,y+(Q/2)+1) * 1/(1+(D/D_k)^4);
        
        v_k = 59; u_k = 159;
        D_k = ((x+u_k)^2 + (y+v_k)^2)^(0.5);
        H_NF(x+(P/2)+1,y+(Q/2)+1) = H_NF(x+(P/2)+1,y+(Q/2)+1) * 1/(1+(D/D_k)^4);
        D_k = ((x-u_k)^2 + (y-v_k)^2)^(0.5);
        H_NF(x+(P/2)+1,y+(Q/2)+1) = H_NF(x+(P/2)+1,y+(Q/2)+1) * 1/(1+(D/D_k)^4);
        
        v_k = -54; u_k = 84;
        D_k = ((x+u_k)^2 + (y+v_k)^2)^(0.5);
        H_NF(x+(P/2)+1,y+(Q/2)+1) = H_NF(x+(P/2)+1,y+(Q/2)+1) * 1/(1+(D/D_k)^4);
        D_k = ((x-u_k)^2 + (y-v_k)^2)^(0.5);
        H_NF(x+(P/2)+1,y+(Q/2)+1) = H_NF(x+(P/2)+1,y+(Q/2)+1) * 1/(1+(D/D_k)^4);
        
        v_k = -54; u_k = 167;
        D_k = ((x+u_k)^2 + (y+v_k)^2)^(0.5);
        H_NF(x+(P/2)+1,y+(Q/2)+1) = H_NF(x+(P/2)+1,y+(Q/2)+1) * 1/(1+(D/D_k)^4);
        D_k = ((x-u_k)^2 + (y-v_k)^2)^(0.5);
        H_NF(x+(P/2)+1,y+(Q/2)+1) = H_NF(x+(P/2)+1,y+(Q/2)+1) * 1/(1+(D/D_k)^4);
     end
end

G_1 = H_NF .* F;

g_1 = real(ifft2(G_1));
g_1 = g_1(1:1:M,1:1:N);     

for x = 1:1:M
    for y = 1:1:N
        g_1(x,y) = g_1(x,y) * (-1)^(x+y);
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
imshow(H_NF,[0 1]);
xlabel('c).Butterworth Notch filter(D=30 n=2)');

subplot(1,2,2);
h = mesh(1:10:Q,1:10:P,H_NF(1:10:P,1:10:Q));
set(h,'EdgeColor','k');
axis([0 Q 0 P 0 1]);
xlabel('u');ylabel('v');
zlabel('|H(u,v)|');

figure();
subplot(1,2,2);
imshow(log(1 + abs(G_1)),[ ]);
xlabel('e).Fourier spectrum of d');

subplot(1,2,1);
imshow(g_1,[0 1]);
xlabel('d).Result image');
```
