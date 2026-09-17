---
layout: post
title: "Image Resize : 数字图像的整数倍缩小"
date:  2013-11-17 16:04:33 +0800
categories: 数字图像处理
tags: [图像处理, 图像重采样]
math: true
image:
  path: /assets/resource/og/Image-Resize-2.png
  alt: "Image Resize : 数字图像的整数倍缩小"
---

本文参考了貴家仁志先生在**よくわかる動画・静止画の処理技術**系列中的1-3期内容[^footnote1][^footnote2][^footnote3]。

### 理想图像缩小的理论基础

类似于数字图像的整数倍扩大法，我们首先从理想情况出发，研究理想的缩小方法。与扩大法采用相同思路，我们需要分析两个信号的特性。

信号①：当采样时间选择为$\Delta T = 1 / 2\mu_m$时，得到的信号如下图所示。左侧展示了信号①在时间域的表现形式，右侧则为其振幅谱。

![Signal_1](/assets/resource/Image-Resize-2/signal_time_domain_1.jpg){: width="450" height="450"}

信号②：当采样时间选择为$\Delta T = 1 / \mu_m$时，得到的信号如下图所示。左侧展示了信号②在时间域的表现形式，右侧则为其振幅谱。

![Signal_2](/assets/resource/Image-Resize-2/signal_time_domain_2.jpeg){: width="450" height="450"}

如上图所示，信号②的频率域中出现了明显的重叠现象，这种现象被称为混淆现象。为了避免混淆现象的发生，我们可以使用滤波器将可能产生混淆的部分削除，从而获得不会混淆的信号。这种不会发生混淆的缩小方法，即为理想的缩小法，其处理过程如下图所示。

![Frequency_Domain_Changes](/assets/resource/Image-Resize-2/freq_domain_changes.jpeg){: width="600" height="600"}

值得注意的是，在介绍数字图像的整数倍扩大法时，我们使用的滤波器振幅特性会随扩大倍数的变化而变化。然而在缩小法中，所使用的滤波器振幅始终保持为1。这是因为在降采样(Down-Sampling)过程中已经进行了振幅调整，因此无需在滤波处理阶段再次调整其振幅。

与扩大法类似，理想的缩小法同样需要理想的滤波器，而这在实际中无法实现。因此，混淆现象无法完全避免，我们只能尽量减小其影响。

### 常用缩小法分析

#### 直接降采样法
直接降采样法是指直接进行降采样处理的方法。由于这种方法相当于使用了全通滤波器，因此无法减小混淆现象，通常不推荐使用。其实现步骤如下：当缩小$D$倍时，从原信号的每$D$个信号中保留第一个，而将剩余的$D-1$个信号直接删除。

![Direct_Downsampling](/assets/resource/Image-Resize-2/direct_downsampling.jpeg){: width="600" height="600"}

#### 平均操作法
平均操作法是指先使用平均滤波器处理信号，然后再进行降采样的方法。这种方法能有效减小混淆现象，比直接降采样法效果更好。其实现步骤如下：当缩小$D$倍时，首先对原信号应用平均滤波器，然后从处理后的信号每$D$个采样点中保留第一个，删除剩余的$D-1$个点。

![Average_Method](/assets/resource/Image-Resize-2/average_method.jpeg){: width="600" height="600"}

#### 上述两种方法的比较分析
下图展示了在4倍缩小情况下，上述两种方法与理想缩小法所使用的滤波器振幅特性的对比。

![Amplitude_Characteristics](/assets/resource/Image-Resize-2/amplitude_characteristics.jpeg){: width="600" height="600"}

从上图可以看出，平均操作法的滤波器特性更接近理想滤波器的振幅特性。因此，平均操作法能在一定程度上有效减小混淆现象。

### 实验验证与结果分析

#### 实验图像准备
本次实验使用的图片如下所示，这些图片均通过Matlab生成，共计3张。

<table>
    <tr>
        <td> 
            <img src="/assets/resource/Image-Resize-2/test_image_1.jpeg" alt="测试图像1" width="600" height="600">
        </td>
        <td> 
            <img src="/assets/resource/Image-Resize-2/test_image_2.jpeg" alt="测试图像2" width="600" height="600">
        </td>
        <td> 
            <img src="/assets/resource/Image-Resize-2/test_image_3.jpeg" alt="测试图像3" width="600" height="600">
        </td>
    </tr>
</table> 

#### 实验结果
使用上述两种方法进行4倍缩小处理，得到的结果如下图所示。左侧为直接降采样法的处理结果，右侧为平均操作法的处理结果。

![Resize_Results](/assets/resource/Image-Resize-2/resize_results.jpeg){: width="600" height="600"}

从结果可以明显观察到，直接降采样法处理后的图像出现了明显的混淆现象，而平均操作法处理后的图像则有效改善了这一问题。

#### Matlab实现代码
```matlab
close all;
clear all;
clc;

f = imread('./cheer/maru_360(cheer).tif');
f = mat2gray(f,[0 255]);

D = 4;  %縮小率

[M,N] = size(f);
g_down = zeros(ceil(M/D),ceil(N/D));
[P,Q] = size(g_down);

for x = 0:1:(P-1)     
   for y = 0:1:(Q-1)
       g_down(x+1,y+1) = f((x*D)+1,(y*D)+1); 
   end
end

figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image');

subplot(1,2,2);
imshow(g_down,[0 1]);
xlabel('b).Ruselt of downsampled');
f = imread('./cheer/maru_360(cheer).tif');
f = mat2gray(f,[0 255]);

D = 4;  %縮小率

[M,N] = size(f);
g_aver = zeros(ceil(M/D),ceil(N/D));
[P,Q] = size(g_aver);

H_aver = ones(D)/(D*D);  %%%%%
f_aver = imfilter(f,H_aver,'conv','symmetric','same');

for x = 0:1:(P-1)     
   for y = 0:1:(Q-1)
       g_aver(x+1,y+1) = f_aver((x*D)+1,(y*D)+1); 
   end
end

figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image');

subplot(1,2,2);
imshow(g_aver,[0 1]);
xlabel('a).Ruselt of average filter + downsampled');
```

### 参考文献
[^footnote1]: [貴家 仁志，"ディジタル画像の表現と階調変換，色間引きの原理，" インターフェース，CQ出版，1998年2月]
[^footnote2]: [貴家 仁志，"ディジタル画像の解像度変換 — 画像の拡大，" インターフェース，CQ出版，1998年4月]
[^footnote3]: [貴家 仁志，"ディジタル画像の解像度変換 — 任意サイズへの画像の変換，" インターフェース，CQ出版，1998年6月]

[貴家 仁志，"ディジタル画像の表現と階調変換，色間引きの原理，" インターフェース，CQ出版，1998年2月]: https://cir.nii.ac.jp/crid/1520854805825943040

[貴家 仁志，"ディジタル画像の解像度変換 — 画像の拡大，" インターフェース，CQ出版，1998年4月]: https://cir.nii.ac.jp/crid/1523669555437398400

[貴家 仁志，"ディジタル画像の解像度変換 — 任意サイズへの画像の変換，" インターフェース，CQ出版，1998年6月]: https://cir.nii.ac.jp/crid/1520010380206841600

