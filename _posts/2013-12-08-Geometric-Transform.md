---
layout: post
title: "Geometric Transform : 几何学变换与图像配准"
date: 2013-12-08 21:30:24 +0800
categories: 数字图像处理
tags: [图像处理, 几何变换, 图像配准]
math: true
image:
  path: /assets/resource/og/Geometric-Transform.png
  alt: "Geometric Transform : 几何学变换与图像配准"
---

## 1.图像的几何学变换

之前的博文里，我简单介绍了图像的放大与缩小（📎 <a href="{{ site.baseurl }}/posts/Image-Resize-1/">Image Resize 系列</a>）。放大与缩小也属于图像的几何学变换，本文介绍其余的几种几何学变换，包括旋转、水平倾斜与垂直倾斜。（水平移动与垂直移动同样属于几何学变换，但它们不需要插值，实现起来相当简单，这里就不展开了。）

假设输入图像为 $g(u,v)$，其变换后的图像为 $f(x,y)$，几种变换的对应关系如下表所示。

| 变换 | 对应关系 |
|:---|:---|
| 旋转 | $x = u\cos\theta - v\sin\theta$ ，$y = u\sin\theta + v\cos\theta$ |
| 倾斜（$x$ 轴方向） | $x = u + s_v v$ ，$y = v$ |
| 倾斜（$y$ 轴方向） | $x = u$ ，$y = s_u u + v$ |

图像的几何学变换主要有两种做法：向前映射与向后映射。

### 1.1 向前映射

所谓向前映射，就是从输入图像 $g(u,v)$ 的 $(0,0)$ 点开始，把 $g(u,v)$ 遍历一遍，依次计算每个点变换之后的坐标。当然，算出来的坐标绝大多数时候不会是整数，就像下图所示那样。

![向前映射：g 的格点经变换后落在 f 的格子之间](/assets/resource/Geometric-Transform/forward-mapping.png){: width="760" }
_变换之后的 $A'$ 并不落在 $f$ 的格点上_

借由上图，我们再来理解一下向前映射。假设图像的一部分是 $A_1 \sim A_5$ 这 5 个点，经过变换，我们得到了右边的 $A'_1 \sim A'_5$。其实，这 5 个点经过变换之后，计算出来的坐标并不是整数。假设现在遍历到 $A_2$（图中以蓝色表示），通过计算得到的点是 $A'_2$；我们将 $A'_2$ 的坐标进行四舍五入，再把 $A'_2$ 的值赋给 $B_2$（这种处理相当于选择最近的点，属于最初级的插值方法）。

使用上述向前映射的思想将图像旋转，我们能得到如下效果。

![向前映射得到的旋转结果，布满空穴](/assets/resource/Geometric-Transform/rotation-forward-mapping.jpeg){: width="560" }
_$\theta = -\pi/8$，四舍五入取最近格点_

可以看出来，所得到的结果非常「斑驳」。其原因是：我们将 $g(u,v)$ 进行变换，所得到的坐标四舍五入之后，有的点没有被赋值，而有的点被赋值了多次。没有被赋值的点就成了「空穴」，所以变换后的图像非常斑驳。

我看过一些文章，讲到这里基本都会说「由于向前映射会产生空穴，所以向前映射一般不使用」。诸如此类的话，其实这样理解并不准确——产生空穴的根本原因在于插值方法不恰当，而不在向前映射本身。使用向前映射，同样可以不产生空穴，所使用的方法如下图所示。

![由最接近的四个 A' 共同确定 B2](/assets/resource/Geometric-Transform/forward-mapping-spread.png){: width="600" }
_把一个 $A'$ 的值摊给周围的格点，反过来看，就是每个 $B$ 由最近的几个 $A'$ 共同确定_

我们可以通过最接近 $B_2$ 的四个点，去确定 $B_2$ 的值，这样就不会产生空穴。但是，这个方法实现起来很困难，所以向前映射才一般不被使用。

### 1.2 向后映射

向后映射，就是将输出图像 $f(x,y)$ 遍历一遍，然后在计算输出点 $(x,y)$ 的时候，反算出它所需要的 $g(u,v)$ 的坐标。当然，这个坐标同样不一定是整数。为了方便理解，还是看下图。

![向后映射：从 f 的格点反算它在 g 上的来源](/assets/resource/Geometric-Transform/inverse-mapping.png){: width="760" }
_$B_1$ 的来源 $B'_1$ 落在 $g$ 的四个格点之间_

假设我们遍历到 $B_1$，通过计算，我们得到 $B'_1$ 这样一个点。也就意味着，如果需要确定 $B_1$ 的灰度值，那么我们需要 $B'_1$ 点处的灰度值。这样，几何变换的问题又归结到了插值问题。最方便的办法就是选择最近的点，如上图的例子，$B_1$ 的灰度值等于 $A_1$ 的灰度值。当然，还有精度更好一些的办法，$B'_1$ 的灰度值的确定方法如下图所示。

![双线性插值：先沿 u 插两次，再沿 v 插一次](/assets/resource/Geometric-Transform/bilinear-interpolation.png){: width="660" }
_把灰度值看成高度，$B'_1$ 的高度由四个邻点的高度决定_

如上图，我们使用 $A_1 \sim A_4$ 这四个点，去确定 $B'_1$ 的值。首先 $A_1$ 与 $A_2$ 之间使用线性插值，确定出 $R_1$ 的值；同样的方法，确定出 $R_2$ 的值。$R_1$ 与 $R_2$ 之间再进行一次线性插值，就可以得到 $B'_1$ 的值了。这就是双线性插值。

使用向后映射将图像旋转，我们可以得到如下结果。

![向后映射得到的旋转结果](/assets/resource/Geometric-Transform/rotation-inverse-mapping.jpeg){: width="560" }
_同样是 $\theta = -\pi/8$，改用向后映射 + 双线性插值_

### 1.3 上述两部分的MATLAB代码

下面的代码中，输入图像的坐标写作 `v`、`w`，对应前文的 $u$ 与 $v$。

```matlab
close all;
clear all;
clc;

%% -----------Geometric_spatial_transform------------------
f = imread('./letter_T.tif');
f = mat2gray(f,[0 255]);
[M,N] = size(f);

%-----by forward mapping-----%
g_fm = zeros(M,N);
seta = -pi/8;
for v = (-M/2):1:(M/2)-1
    for w = (-N/2):1:(N/2)-1
        x = round(v*cos(seta) - w*sin(seta));
        y = round(v*sin(seta) + w*cos(seta));
        if (((y>=(-N/2))&&(y<=(N/2)))&&((x>=(-M/2))&&(x<=(M/2))))
            g_fm(x+(M/2)+1,y+(N/2)+1) = f(v+(M/2)+1,w+(N/2)+1);
        end
    end
end

figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image');
subplot(1,2,2);
imshow(g_fm,[0 1]);
xlabel('b).Ruselt of Geometric spatial transform');

%-----by inverse mapping-----%
g_im = zeros(M,N);
seta = -pi/8;
for x = (-M/2):1:(M/2)-1
    for y = (-N/2):1:(N/2)-1
        v = x*cos(-seta) - y*sin(-seta);
        w = x*sin(-seta) + y*cos(-seta);
        if (((w>=(-N/2)+1)&&(w<=(N/2)-1))&&((v>=(-M/2)+1)&&(v<=(M/2)-1)))
            Q_11 = f(floor(v)+(M/2)+1,floor(w)+(N/2)+1);
            Q_21 = f(floor(v)+(M/2)+1, ceil(w)+(N/2)+1);
            Q_12 = f( ceil(v)+(M/2)+1,floor(w)+(N/2)+1);
            Q_22 = f( ceil(v)+(M/2)+1, ceil(w)+(N/2)+1);
            R1 = (Q_21 - Q_11)*(w-floor(w)) + Q_11;
            R2 = (Q_22 - Q_12)*(w-floor(w)) + Q_12;
            g_im(x+(M/2)+1,y+(N/2)+1) = (R2-R1)*(v-floor(v)) + R1;
        end
    end
end

figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image');
subplot(1,2,2);
imshow(g_im,[0 1]);
xlabel('b).Ruselt of Geometric spatial transform');
```

## 2.图像的配准

图像的配准常常用于超分辨率等领域。作为基础学习，这里不做太深入的讨论；本节尝试还原被倾斜变换过的图像。首先，将图像沿两个方向做倾斜。

![沿两个方向倾斜后的图像，红圈为选定的控制点](/assets/resource/Geometric-Transform/shear-with-tie-points.jpeg){: width="580" }
_先沿 $x$ 轴方向倾斜，再沿 $y$ 轴方向倾斜；红圈标出的是用于求解的四个控制点_

我们这次的目的是，将图像 b) 还原为 a)。这次变换相对简单，我们使用如下模型去拟合变换关系。

$$
\begin{aligned}
x &= c_1u + c_2v + c_3uv + c_4 \\
y &= c_5u + c_6v + c_7uv + c_8
\end{aligned}
$$

我们在原图与变换后的图像上，各选出四个控制点（tie points），然后代入方程，求出系数 $c_1 \sim c_8$。使用这个方程，就可以将图像 b) 还原为 a)。这个过程比较简单，所选择的控制点已经在上图中用红圈标定出来了，还原的结果如下。

![配准还原的结果与差分图像](/assets/resource/Geometric-Transform/registration-result.jpeg){: width="580" }
_c) 为还原结果，d) 为它与原图的差分_

可以看到，还原的效果非常好——当然，这也是因为畸变本身比较简单的缘故。为了看出与原图的区别，我们做出了差分图像；由此可见，还原并不是完美的。

最后，以下面这段代码作为本文的结尾。需要说明的是，这里控制点的选择是手工完成的，所以这段代码的实用价值有限。一般来说，在使用特征点做图像配准的时候，会在实际的物体上放置某种实体标志，再通过检测这些标志去确定变换关系——这部分内容可以参考 Gonzalez 与 Woods 的📎 [《Digital Image Processing》] 第二章，书中有相关的叙述。

[《Digital Image Processing》]: https://www.imageprocessingplace.com/

```matlab
close all;
clear all;
clc;

%% --------------image registration---------------------------
f_Original = imread('./characters_test_pattern.tif');
f_Original = mat2gray(f_Original,[0 255]);
[M,N] = size(f_Original);

f = zeros(M+4,N+4);
for x = 1:M
    f(x+2,:) = [0 0 f_Original(x,:) 0 0];
end
[M,N] = size(f);

s_v = 0.3;
s_w = 0.02;
P = round(M+s_v*N);
Q = round(N+s_w*M);

%-----shear along x-----%
g_1 = zeros(P,N);
for x = (-P/2):1:(P/2)-1
    for y = (-N/2):1:(N/2)-1
        v = x - s_v * y;
        w = y;
        if (((w>=(-N/2))&&(w<=(N/2)-1))&&((v>=(-M/2))&&(v<=(M/2)-1)))
            Q_11 = f(floor(v)+(M/2)+1,floor(w)+(N/2)+1);
            Q_21 = f(floor(v)+(M/2)+1, ceil(w)+(N/2)+1);
            Q_12 = f( ceil(v)+(M/2)+1,floor(w)+(N/2)+1);
            Q_22 = f( ceil(v)+(M/2)+1, ceil(w)+(N/2)+1);
            R1 = (Q_21 - Q_11)*(w-floor(w)) + Q_11;
            R2 = (Q_22 - Q_12)*(w-floor(w)) + Q_12;
            g_1(x+(P/2)+1,y+(N/2)+1) = (R2-R1)*(v-floor(v)) + R1;
        end
    end
end

%-----shear along y-----%
g = zeros(P,Q);
for x = (-P/2):1:(P/2)-1
    for y = (-Q/2):1:(Q/2)-1
        v = x;
        w = y - s_w * x;
        if (((w>=(-N/2))&&(w<=(N/2)-1))&&((v>=(-P/2))&&(v<=(P/2)-1)))
            Q_11 = g_1(floor(v)+(P/2)+1,floor(w)+(N/2)+1);
            Q_21 = g_1(floor(v)+(P/2)+1, ceil(w)+(N/2)+1);
            Q_12 = g_1( ceil(v)+(P/2)+1,floor(w)+(N/2)+1);
            Q_22 = g_1( ceil(v)+(P/2)+1, ceil(w)+(N/2)+1);
            R1 = (Q_21 - Q_11)*(w-floor(w)) + Q_11;
            R2 = (Q_22 - Q_12)*(w-floor(w)) + Q_12;
            g(x+(P/2)+1,y+(Q/2)+1) = (R2-R1)*(v-floor(v)) + R1;
        end
    end
end

figure();
subplot(1,2,1);
imshow(f,[0 1]);
xlabel('a).Original Image');
hold on;
plot(621, 78,'ro','MarkerSize',7);
plot(116,113,'ro','MarkerSize',7);
plot( 85,649,'ro','MarkerSize',7);
plot(624,641,'ro','MarkerSize',7);
subplot(1,2,2);
imshow(g,[0 1]);
xlabel('b).Ruselt of Geometric spatial transform');
hold on;
plot(625,264,'ro','MarkerSize',7);
plot(116,147,'ro','MarkerSize',7);
plot( 96,674,'ro','MarkerSize',7);
plot(638,828,'ro','MarkerSize',7);

%% -----solve the coefficients & restore-----
f_reg = zeros(M,N);
Original = [621-(N/2)  78-(M/2) (621-(N/2))*( 78-(M/2)) 1;
            116-(N/2) 113-(M/2) (116-(N/2))*(113-(M/2)) 1;
             85-(N/2) 649-(M/2) ( 85-(N/2))*(649-(M/2)) 1;
            624-(N/2) 641-(M/2) (624-(N/2))*(641-(M/2)) 1];

Ruselt = [625-(Q/2);116-(Q/2);96-(Q/2);638-(Q/2)];
c = (Original)\Ruselt;                  %C1~C4
Ruselt = [264-(P/2);147-(P/2);674-(P/2);828-(P/2)];
c = [c (Original)\Ruselt];              %C5~C8

for y = (-M/2):1:(M/2)-1
    for x = (-N/2):1:(N/2)-1
        w = c(1,1)*y + c(2,1)*x + c(3,1)*x*y + c(4,1);
        v = c(1,2)*y + c(2,2)*x + c(3,2)*x*y + c(4,2);
        if (((w>=(-Q/2))&&(w<=(Q/2)-1))&&((v>=(-P/2))&&(v<=(P/2)-1)))
            Q_11 = g(floor(v)+(P/2)+1,floor(w)+(Q/2)+1);
            Q_21 = g(floor(v)+(P/2)+1, ceil(w)+(Q/2)+1);
            Q_12 = g( ceil(v)+(P/2)+1,floor(w)+(Q/2)+1);
            Q_22 = g( ceil(v)+(P/2)+1, ceil(w)+(Q/2)+1);
            R1 = (Q_21 - Q_11)*(w-floor(w)) + Q_11;
            R2 = (Q_22 - Q_12)*(w-floor(w)) + Q_12;
            f_reg(x+(N/2)+1,y+(M/2)+1) = (R2-R1)*(v-floor(v)) + R1;
        end
    end
end

g_diff = abs(f - f_reg);

figure();
subplot(1,2,1);
imshow(f_reg,[0 1]);
xlabel('c).Ruselt of image registration');
subplot(1,2,2);
imshow(g_diff,[0 1]);
xlabel('d).Difference image');
```
