---
layout: post
title: "Image Resize : 数字图像的有理数倍缩放"
date:  2013-11-17 17:28:25 +0800
categories: 数字图像处理
tags: [图像处理, 图像重采样]
math: true
---

本文参考了貴家仁志先生在**よくわかる動画・静止画の処理技術**系列中的1-3期内容[^footnote1][^footnote2][^footnote3]。

### 图像的有理数倍缩放
根据上两节的内容，我们已经实现了整数倍的扩大与缩小。但在实际应用中，恰好需要整数倍缩放的情况并不常见，更多时候我们需要非整数倍的变换。

当我们如下图所示，将图像的整数倍扩大与缩小操作进行串联后，就可以得到有理数倍的缩放。

![Rational Scaling Flowchart 1](/assets/resource/Image-Resize-3/rational-scaling-flowchart-1.jpeg){: width="450" height="450"}

先进行$U$倍的扩大，然后再缩小$D$倍，这样就实现了$U/D$倍的分辨率变换。这里的$U$与$D$都是整数，其中$\uparrow U$表示零值插入操作，$\downarrow D$表示降采样操作，$H_U(z)$和$H_D(z)$则代表图像的滤波器操作。显然，可以将$H_U(z)$和$H_D(z)$的操作合成为一个滤波器，如下所示：

![Rational Scaling Flowchart 2](/assets/resource/Image-Resize-3/rational-scaling-flowchart-2.jpeg){: width="450" height="450"}

这里的$H(z) = H_U(z) H_D(z)$。

### 图像的有理数倍扩大 ($U > D$)
当$U > D$时，整个流程变为图像的有理数倍扩大。我们假设$U=3$，$D=2$，此时相当于$U/D = 1.5$倍的扩大。根据前两节的内容，我们需要的理想滤波器的振幅特性如下所示。

![Amplitude Characteristics for Rational Enlargement 1](/assets/resource/Image-Resize-3/amplitude-characteristics-enlargement-1.jpeg){: width="450" height="450"}

可以看到，当$U>D$时，扩大操作所用的滤波器$H_U(z)$的通带要比缩小操作所用滤波器$H_D(z)$的通带窄。因此，我们所需的有理数倍扩大所用滤波器的振幅特性应该如下所示：

![Amplitude Characteristics for Rational Enlargement 2](/assets/resource/Image-Resize-3/amplitude-characteristics-enlargement-2.jpeg){: width="250" height="250"}

我们可以得到以下两个非常有用的结论：
- 当$U>D$时，我们可以将$H_U(z)$直接作为$H(z)$使用。
- 当$U>D$时，缩小处理可直接使用降采样法即可。（其理由是$H_U(z)$已经很大程度上减小了频谱混叠，没有必要再使用平均操作法）

#### Matlab实现代码
使用线性插值法与直接降采样法，实现图像的1.5倍变换的代码如下所示。输入图像的分辨率为512×512，输出图像的尺寸为768×768。
```matlab
f = imread('./maru/maru_512.tif');
f = mat2gray(f,[0 255]);

U = 3;  %拡大率 
D = 2;  %縮小率

[M,N] = size(f);
g_bilin = zeros((M*U)+6,(N*U)+6);

H_bilin = [1 2 3 2 1]/3;

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

g_biline_down = zeros(ceil((M*U)/D)-1,ceil((N*U)/D)-1);
[P,Q] = size(g_biline_down);

for x = 0:1:(P-1)
   for y = 0:1:(Q-1)
       g_biline_down(x+1,y+1) = g_b((x*D)+1,(y*D)+1); 
   end
end

figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image');

subplot(1,2,2);
imshow(g_biline_down,[0 1]);
xlabel('b).Result of bilinear+downsampled');
```


### 图像的有理数倍缩小 ($U < D$)
同样，当$U < D$时，整个流程变为图像的有理数倍缩小。我们假设$U=2$，$D=3$，相当于$U/D = 2/3$倍的缩小。此时，我们需要的理想滤波器的振幅特性如下所示：


![Amplitude Characteristics for Rational Reduction 1](/assets/resource/Image-Resize-3/amplitude-characteristics-reduction-1.jpeg){: width="450" height="450"}

可以看到，当$U<D$时，扩大操作所用的滤波器$H_U(z)$的通带要比缩小操作所用滤波器$H_D(z)$的通带宽。因此，我们所需的有理数倍缩小所用滤波器的振幅特性应该如下所示：

![Amplitude Characteristics for Rational Reduction 2](/assets/resource/Image-Resize-3/amplitude-characteristics-reduction-2.jpeg){: width="250" height="250"}


我们可以得到以下两个非常有用的结论：
- 当$U<D$时，我们绝对不可将$H_U(z)$直接当做$H(z)$使用。（其理由是$H_U(z)$的通带较宽，不能减小频谱混叠现象）
- 当$U<D$时，应将缩小处理所用$H_D(z)$滤波器进行$U$倍振幅调整，即$H(z)=U \cdot H_D(z)$。这个调整过的滤波器才可以作为$H(z)$使用。但是，如果处理不当，会出现棋盘失真（关于棋盘失真的条件，本文后面将会详细叙述）。

#### Matlab实现代码
使用零次保持法（最邻近插值法）与平均操作法，实现图像的2/3倍变换。输入图像的分辨率为512×512，输出图像的尺寸为341×341。
```matlab
f = imread('./maru/maru_512.tif');
f = mat2gray(f,[0 255]);

U = 2;  %拡大率
D = 3;  %縮小率

[M,N] = size(f);
g_hold_aver = zeros((M*U)+6,(N*U)+6);
H_hold_aver = [1 2 2 1]/3;

for x = 0:1:M-1 
   for y = 0:1:N-1
       g_hold_aver((U*x)+1,(U*y)+1) = f(x+1,y+1); 
   end
end

g_hold_aver(1,:) = g_hold_aver(U+1,:); 
g_hold_aver((M*U)+U+1,:) = g_hold_aver((M*U)+1,:); 
g_hold_aver(:,1) = g_hold_aver(:,U+1); 
g_hold_aver(:,(M*U)+U+1) = g_hold_aver(:,(M*U)+1); 

for x = 1:1:(U*M)+6 
    g_hold_aver(x,:) = filter(H_hold_aver,1,g_hold_aver(x,:));
end
for y = 1:1:(U*N)+6 
    g_hold_aver(:,y) = filter(H_hold_aver,1,g_hold_aver(:,y));
end

g_H_A = zeros((M*U),(N*U));
for x = 1:1:(M*U)
   for y = 1:1:(M*U)
       g_H_A(x,y) = g_hold_aver(x+3,y+3); 
   end
end

g_hold_aver = zeros(ceil((M*U)/D)-1,ceil((N*U)/D)-1);
[P,Q] = size(g_hold_aver);

for x = 0:1:(P-1)
   for y = 0:1:(Q-1)
       g_hold_aver(x+1,y+1) = g_H_A((x*D)+1,(y*D)+1); 
   end
end

figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image (512x512)');

subplot(1,2,2);
imshow(g_hold_aver,[0 1]);
xlabel('b).Result of hold+average (341x341)');
```

### 图像缩放时需要注意的问题

#### 分离式滤波处理
在实际工程应用中，图像的水平方向与垂直方向往往需要不同倍率的变化。因此，可以将处理拆分为两个一维滤波器来实现图像分辨率的变换，如下图所示：

![2D Convolution Decomposition](/assets/resource/Image-Resize-3/2d-convolution-decomposition.jpeg){: width="450" height="450"}

对于$M \times N$的图像，先在水平方向上逐列进行一维卷积，得到$P \times N$的图像。然后，在垂直方向上逐行进行一维卷积，就可以得到$P \times Q$的图像。
通过这种方式，我们可以将水平方向与垂直方向上不同倍率的变换拆分为两个方向的独立缩放操作。

作为分离式滤波处理的示例，以下代码实现了水平方向上的1.5倍扩大与垂直方向上的2/3倍缩小：
- 输入图像的分辨率：512×512
- 输出图像的分辨率：341×768

![2D Convolution Decomposition Result](/assets/resource/Image-Resize-3/2d-convolution-result.jpeg){: width="450" height="450"}

#### Matlab实现代码
```matlab
f = imread('./lena/lena_gray_512.tif');
f = mat2gray(f,[0 255]);

U_x = 2; 
U_y = 3;  
D_x = 3;
D_y = 2;

[M,N] = size(f);
g_xy = zeros((M*U_x)+6,(N*U_y)+6);
H_x = [1 2 2 1]/3;    %行(垂直)方向 U_x=2 的零次保持+平均
H_y = [1 2 3 2 1]/3;  %列(水平)方向 U_y=3 的线性插值

for x = 0:1:M-1 
   for y = 0:1:N-1
       g_xy((U_x*x)+1,(U_y*y)+1) = f(x+1,y+1); 
   end
end

g_xy(1,:) = g_xy(U_x+1,:); 
g_xy((M*U_x)+U_x+1,:) = g_xy((M*U_x)+1,:); 
g_xy(:,1) = g_xy(:,U_y+1); 
g_xy(:,(M*U_y)+U_y+1) = g_xy(:,(M*U_y)+1); 

for x = 1:1:(U_x*M)+6 
    g_xy(x,:) = filter(H_y,1,g_xy(x,:));  %沿列滤波，即水平方向
end
for y = 1:1:(U_y*N)+6 
    g_xy(:,y) = filter(H_x,1,g_xy(:,y));  %沿行滤波，即垂直方向
end

g_xy_2 = zeros((M*U_x),(N*U_y));
for x = 1:1:(M*U_x)
   for y = 1:1:(M*U_y)
       g_xy_2(x,y) = g_xy(x+3,y+3); 
   end
end

g_xy_Result= zeros(ceil((M*U_x)/D_x)-1,ceil((N*U_y)/D_y)-1);
[P,Q] = size(g_xy_Result);

for x = 0:1:(P-1)
   for y = 0:1:(Q-1)
       g_xy_Result(x+1,y+1) = g_xy_2((x*D_x)+1,(y*D_y)+1); 
   end
end


figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image (512x512)');

subplot(1,2,2);
imshow(g_xy_Result,[0 1]);
xlabel('b).Result of hold+average (341x768)');
```

#### 棋盘失真
我们将3个像素上进行平均操作，同时将振幅扩大调整两倍，并进行$2/3$倍缩小（下采样）操作。此滤波器如下所示：

$$
\begin{aligned}
H(z) = \frac{2}{3} (1 + z^{-1} + z^{-2})
\end{aligned}
$$

我们使用这个滤波器进行$2/3$倍缩小操作，图像输出结果如下所示：

![Checkerboard Artifacts Result](/assets/resource/Image-Resize-3/checkerboard-artifacts-result.jpeg){: width="450" height="450"}

如上图所示，使用此滤波器进行$2/3$倍缩小后的结果出现了周期性很强的噪声。这种噪声呈现"黑""白"相间的状态，由于形似棋盘，我们将其称为棋盘失真(Checkerboard Artifacts)。

关于棋盘失真出现的原因，我们可以将所用滤波器进行多相分解（Polyphase decomposition），如下所示：

$$
\begin{aligned}
H(z) &= \frac{2}{3} (1 + z^{-1} + z^{-2}) \\
&= \frac{2}{3} z^{-1} + (\frac{2}{3} +  \frac{2}{3} z^{-2}) \\
&= R_0(z) z^{-1} + R_1(z)
\end{aligned}
$$

根据分解结果，我们可以将图像$2/3$倍缩小的流程分解如下：

![Image Reduction Process Decomposition](/assets/resource/Image-Resize-3/reduction-process-decomposition.jpeg){: width="450" height="450"}

如图所示，将其拆分为$R_0$和$R_1$两条支路后，如果$R_0$和$R_1$在相同的$z$值下输出不一致，则滤波器的输出无法收敛，如下图所示：

![Checkerboard Artifacts Cause](/assets/resource/Image-Resize-3/checkerboard-artifacts-cause.jpeg){: width="450" height="450"}

因此，棋盘失真出现的条件是：按照多相分解的结果，若各部分的最终输出值不一致，会导致滤波器输出不收敛，最终造成棋盘失真。为避免棋盘失真，应该确保多相分解后各支路的输出一致。

### 参考文献
[^footnote1]: [貴家 仁志，"ディジタル画像の表現と階調変換，色間引きの原理，" インターフェース，CQ出版，1998年2月]
[^footnote2]: [貴家 仁志，"ディジタル画像の解像度変換 — 画像の拡大，" インターフェース，CQ出版，1998年4月]
[^footnote3]: [貴家 仁志，"ディジタル画像の解像度変換 — 任意サイズへの画像の変換，" インターフェース，CQ出版，1998年6月]

[貴家 仁志，"ディジタル画像の表現と階調変換，色間引きの原理，" インターフェース，CQ出版，1998年2月]: https://cir.nii.ac.jp/crid/1520854805825943040

[貴家 仁志，"ディジタル画像の解像度変換 — 画像の拡大，" インターフェース，CQ出版，1998年4月]: https://cir.nii.ac.jp/crid/1523669555437398400

[貴家 仁志，"ディジタル画像の解像度変換 — 任意サイズへの画像の変換，" インターフェース，CQ出版，1998年6月]: https://cir.nii.ac.jp/crid/1520010380206841600

