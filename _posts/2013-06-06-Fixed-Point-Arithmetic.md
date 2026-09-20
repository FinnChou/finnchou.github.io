---
layout: post
title: "[番外2]定点计算与浮点计算"
date: 2013-06-06 14:12:31 +0800
categories: 数字信号处理
tags: [定点运算, Q格式, FIR滤波器]
math: true
image:
  path: /assets/resource/og/Fixed-Point-Arithmetic.png
  alt: "[番外2]定点计算与浮点计算"
---

到目前为止，我们实现FIR与IIR滤波器时，系数与信号均以`double`存放，乘加也直接交由浮点运算完成。这在PC上自然没有问题，但若要把滤波器移植到定点DSP这类不具备浮点运算单元的平台，整套运算就必须改写为整数运算。本篇作为番外，讨论定点计算的原理与做法，并以前文的FIR滤波器为例，给出一个完整的Q15实现。

## 1.定点计算的必要性

定点计算，简单来说就是把小数的计算转换为整数的计算。这里的「点」指的是小数点，所谓定点，即小数点位置固定的运算：对于一个整数，将假定的小数点固定在某个位置，便可把这个整数视为小数。小数点定在哪里原本无所谓，一旦决定下来，它就固定在某一位上不再移动，定点运算之名即由此而来。那么，为什么要多做这一层转换？

① 在实际的C语言程序中，小数通常用`double`与`float`来表达，也就是浮点数。而在实际的信号处理中，处理之前必定要先经A/D采集模拟信号并将其转换为数字信号，所得到的数字信号显然并不是小数；某些场合下，为了计算还得先把它转换为浮点数。

② DSP分为定点DSP与浮点DSP两类。浮点DSP是为浮点运算量身定做的，其内部有硬件可以直接完成浮点运算；但受限于结构复杂、功耗与价格等因素，它的适用场合并不像定点DSP那样广泛。而在定点DSP上做浮点运算，只能依靠软件模拟，耗时相当可观。

③ 可以限制运算结果的位宽。

综上所述，为了获得足够的运算速度，定点计算是必须掌握的。

## 2.负数的表达与三大规则

① **规则一：最高位(MSB)是符号位。** 下面以4-bit的数为例进行说明。最高位作为符号位，其值为1时表示负数，为0时表示正数；此时最高位的权重为$-8$(4-bit)。$+6$与$-6$的表示如下。

![4-bit有符号数中最高位作为符号位，其权重为负](/assets/resource/Fixed-Point-Arithmetic/sign-bit-weights.png){: width="720" }
_符号位的权重是负的，正负数便能用同一套加权求和来解释_

不难验证，$+6 = 4 + 2$与$-6 = -8 + 2$均成立，这样理解相当直观。换个角度看，$1010$正是$0110$的补码，两种理解是等价的。

② **规则二：负数的符号位扩展不影响数的大小。** 仍以$-6$为例，在它前面无论补多少个1，所表示的数值都还是$-6$。当然，前提是最高位始终作为符号位(规则一)。

![4-bit的1010与5-bit的11010表示同一个数-6](/assets/resource/Fixed-Point-Arithmetic/sign-extension.png){: width="720" }
_符号位向高位复制，数值不变_

③ **规则三：乘数的符号位这一路，其部分积等于被乘数的补码。** 这一条是规则一的直接推论：符号位的权重为负，与之相乘即得到相反数，也就是补码。

## 3.固定小数点的折算与其实现（C语言）

首先陈述一个事实：一个4-bit的数乘以一个4-bit的数，其结果为8-bit。若继续相乘下去，位宽迟早会不敷使用。

为了解决这个问题，可以引入小数点。以$0.9 \times 0.9 = 0.81$为例，乘数与被乘数在小数点后都只有1位，结果却有2位；但若同样只保留1位小数，取$0.8$也就足够了。按照这个思路，只要参与乘法的数其绝对值都在1以下，便可有效避免位宽不足——增长出来的位数只落在小数点右侧，而右侧是可以按需截断的。为此，我们引入固定小数点。

固定小数点对DSP而言并不存在，它只是一个假想的小数点。对于一个4-bit的数，小数点有以下几种取法。

| 小数点位置 | bit3 | bit2 | bit1 | bit0 | 格式 |
|:---|:---:|:---:|:---:|:---:|:---:|
| ① bit3之前 | $-1/2$ | $1/4$ | $1/8$ | $1/16$ | Q4 |
| ② bit3与bit2之间 | $-1$ | $1/2$ | $1/4$ | $1/8$ | Q3 |
| ③ bit2与bit1之间 | $-2$ | $1$ | $1/2$ | $1/4$ | Q2 |
| ④ bit1与bit0之间 | $-4$ | $2$ | $1$ | $1/2$ | Q1 |
| ⑤ bit0之后 | $-8$ | $4$ | $2$ | $1$ | Q0 |

按照前面的思路，要把数值压缩在绝对值小于1的范围内，可以选择小数点在②的位置。此时小数点后有3位，故称为Q3格式。不难看出，Q3格式下可以表示的数$x$，其范围为：

$$
\begin{aligned}
-1 \le x \le \frac{7}{8}
\end{aligned}
$$

根据选定的小数点位置与相应的权重，就可以进行折算。下面给出一个Q15格式的折算函数。

```c
unsigned short To_Q15_Fixed_Point(double Data_Float)
{
    unsigned short Data_Q15_Format = 0;

    if (Data_Float == 1)       return (unsigned short)0x7FFF;
    else if (Data_Float == -1) return (unsigned short)0x8000;
    else if (Data_Float < 0)
    {
        Data_Float = -Data_Float;
        Data_Q15_Format |= (unsigned short)0x8000;
    }

    Data_Q15_Format |= (short)(Data_Float * 0x8000);

    if (Data_Q15_Format & 0x8000)
    {
        Data_Q15_Format &= 0x7FFF;
        Data_Q15_Format = ((~Data_Q15_Format) + 0x0001);
    }

    return (unsigned short)Data_Q15_Format;
}
```

## 4.固定小数点的乘法与其实现（C语言）

固定小数点的乘法可以按如下方法实现。首先需要说明，两个Q3格式的数相乘，其结果为Q6格式。

![Q3乘Q3的竖式展开，结果为Q6](/assets/resource/Fixed-Point-Arithmetic/q3-multiplication.png){: width="760" }
_逐位展开的Q3乘法：符号位那一路取补码，其余各路做符号位扩展后相加_

此处有几点需要说明：

① 在进行乘法计算时，符号位代表的是负数，因此符号位这一路的部分积，就是被乘数的补码(规则三)。

② 由于乘法是分步进行的，各步的部分积最终都要对齐到8-bit。根据规则二，若部分积的符号位为1，则在它之前补1；若为0，则照常补0即可。

③ 结果是一个Q6格式的数，只需按照Q3的要求取出即可。由于结果为负，最高的那一位是冗余的符号位，取与不取并无影响。（注意，这里还有可能产生溢出，例如两个负数相乘。此时可以无视溢出，依旧按照Q3格式取出结果。）

同样地，下面给出Q15格式的乘法函数。

```c
unsigned short MUL_Q15(unsigned short a,
                       unsigned short b)
{
    int Count;
    unsigned int   Answer_Q30 = 0;
    unsigned short Answer_Q15 = 0;

    if (b & 0x8000)
    {
        Answer_Q30 += (~((unsigned int)a) + 0x0001) << 15;
        b = (b & 0x7FFF);
    }

    for (Count = 0; Count <= 15; Count++)
    {
        if (b & (0x0001 << Count))
        {
            if (a & 0x8000)
            {
                Answer_Q30 += ((unsigned int)a | 0xFFFF0000) << Count;
            }
            else Answer_Q30 += ((unsigned int)a) << Count;
        }
    }

    Answer_Q15 = (unsigned short)((Answer_Q30 & 0x7FFFFFFF) >> 15);

    return (unsigned short)Answer_Q15;
}
```

## 5.固定小数点实际的运用

下面来看固定小数点的实际运用。假设有如下FIR滤波器，其滤波器系数为

$$
\begin{aligned}
h(n) = \{\,0.25,\ 0.5,\ -0.25,\ -0.25,\ 0.5,\ 0.25\,\}
\end{aligned}
$$

输入信号为

$$
\begin{aligned}
x(n) = \{\,0.5,\ 0.75,\ 0.5,\ 0.25,\ 0,\ -0.25,\ -0.5,\ -0.75,\ -0.5,\ -0.25,\ 0\,\}
\end{aligned}
$$

求其输出。

计算的思路是：先将滤波器系数$h(n)$与输入$x(n)$折算为Q15格式，随后全程以整数完成运算，所得输出同样是Q15，最后再还原为小数。其代码如下。

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

double h[] = {0.25, 0.5, -0.25, -0.25, 0.5, 0.25};

unsigned short MUL_Q15(unsigned short a,
                       unsigned short b)
{
    int Count;
    unsigned int   Answer_Q30 = 0;
    unsigned short Answer_Q15 = 0;

    if (b & 0x8000)
    {
        Answer_Q30 += (~((unsigned int)a) + 0x0001) << 15;
        b = (b & 0x7FFF);
    }

    for (Count = 0; Count <= 15; Count++)
    {
        if (b & (0x0001 << Count))
        {
            if (a & 0x8000) Answer_Q30 += ((unsigned int)a | 0xFFFF0000) << Count;
            else            Answer_Q30 += ((unsigned int)a) << Count;
        }
    }

    Answer_Q15 = (unsigned short)((Answer_Q30 & 0x7FFFFFFF) >> 15);

    return (unsigned short)Answer_Q15;
}

unsigned short To_Q15_Fixed_Point(double Data_Float)
{
    unsigned short Data_Q15_Format = 0;

    if (Data_Float == 1)       return (unsigned short)0x7FFF;
    else if (Data_Float == -1) return (unsigned short)0x8000;
    else if (Data_Float < 0)
    {
        Data_Float = -Data_Float;
        Data_Q15_Format |= (unsigned short)0x8000;
    }

    Data_Q15_Format |= (short)(Data_Float * 0x8000);

    if (Data_Q15_Format & 0x8000)
    {
        Data_Q15_Format &= 0x7FFF;
        Data_Q15_Format = ((~Data_Q15_Format) + 0x0001);
    }

    return (unsigned short)Data_Q15_Format;
}

double To_Float(unsigned short Data_Q15)
{
    if (Data_Q15 == 0x8000) return (double)(-1);

    if (Data_Q15 & 0x8000)
    {
        Data_Q15 = ~(Data_Q15 - 0x0001);
        return (double)(-(Data_Q15 / (double)0x8000));
    }
    else return (double)(Data_Q15 / (double)0x8000);
}

unsigned short FIR_Filter_Q15(unsigned short *b_Q15,
                              int             b_Q15_Lenth,
                              unsigned short *Input_Buffer_Q15,
                              unsigned short  Input_data_Q15)
{
    int Count;
    double Output_Data_Q15 = 0;

    for (Count = 0; Count < b_Q15_Lenth - 1; Count++)
    {
        *(Input_Buffer_Q15 + Count) = *(Input_Buffer_Q15 + Count + 1);
    }
    *(Input_Buffer_Q15 + b_Q15_Lenth - 1) = Input_data_Q15;
    Input_Buffer_Q15 += b_Q15_Lenth - 1;

    for (Count = 0; Count < b_Q15_Lenth; Count++)
    {
        Output_Data_Q15 += MUL_Q15(*(b_Q15 + Count),
                                   *(Input_Buffer_Q15 - Count));
    }

    return (unsigned short)Output_Data_Q15;
}

int main(void)
{
    int Count;
    int h_Lenth = sizeof(h) / sizeof(double);

    unsigned short *h_Q15;
    h_Q15 = (unsigned short *)malloc(sizeof(unsigned short) * h_Lenth);
    memset(h_Q15, 0, sizeof(unsigned short) * h_Lenth);

//-----------------------------display h--------------------------------//
    printf("    h  : ");
    for (Count = 0; Count < h_Lenth; Count++) printf("% 9lf ", h[Count]);
    printf("\n");

    printf(" h_Q15 : ");
    for (Count = 0; Count < h_Lenth; Count++)
    {
        *(h_Q15 + Count) = To_Q15_Fixed_Point(h[Count]);
        printf("% 9X ", *(h_Q15 + Count));
    }
    printf("\n--------------------------------------------------\n");
//---------------------------------------------------------------------//

    double Input  = 0;
    double Output = 0;
    unsigned short Input_Q15  = 0;
    unsigned short Output_Q15 = 0;

    unsigned short *Input_Buffer_Q15;
    Input_Buffer_Q15 = (unsigned short *)malloc(sizeof(unsigned short) * h_Lenth);
    memset(Input_Buffer_Q15, 0, sizeof(unsigned short) * h_Lenth);

    FILE *Input_Pointer;
    Input_Pointer = fopen("input.dat", "r");

    while (1)
    {
        if (fscanf(Input_Pointer, "%lf", &Input) == EOF) break;

        printf("% lf --> ", Input);
        Input_Q15 = To_Q15_Fixed_Point(Input);
        printf("%4X | ", (unsigned short)Input_Q15);

        Output_Q15 = FIR_Filter_Q15(h_Q15,
                                    h_Lenth,
                                    Input_Buffer_Q15,
                                    Input_Q15);
        printf("%4X --> ", Output_Q15);

        Output = To_Float(Output_Q15);
        printf("% lf \n", Output);
    }

    printf("Finish \n");

    return (int)0;
}
```

输入序列$x(n)$以一行一个样本的形式存放在`input.dat`中。以上程序在GCC下编译通过，执行结果如下。

```console
$ gcc -o FIR FIR.c
$ ./FIR
    h  :  0.250000  0.500000 -0.250000 -0.250000  0.500000  0.250000
 h_Q15 :      2000      4000      E000      E000      4000      2000
--------------------------------------------------
 0.500000 --> 4000 | 1000 -->  0.125000
 0.750000 --> 6000 | 3800 -->  0.437500
 0.500000 --> 4000 | 3000 -->  0.375000
 0.250000 --> 2000 |    0 -->  0.000000
 0.000000 -->    0 |  800 -->  0.062500
-0.250000 --> E000 | 2000 -->  0.250000
-0.500000 --> C000 | 1000 -->  0.125000
-0.750000 --> A000 | F000 --> -0.125000
-0.500000 --> C000 | E000 --> -0.250000
-0.250000 --> E000 | F000 --> -0.125000
 0.000000 -->    0 | F000 --> -0.125000
Finish
```

作为对照，用MATLAB以浮点方式计算同一个滤波器：

```matlab
h = [0.25, 0.5, -0.25, -0.25, 0.5, 0.25];
x = [0.5, 0.75, 0.5, 0.25, 0, -0.25, -0.5, -0.75, -0.5, -0.25, 0];
y = filter(h, 1, x);
```

得到的结果如下。

```console
y =

  Columns 1 through 9

    0.1250    0.4375    0.3750         0    0.0625    0.2500    0.1250   -0.1250   -0.2500

  Columns 10 through 11

   -0.1250   -0.1250
```

两者逐点对照如下：

| $n$ | $x(n)$ | $x_{Q15}(n)$ | $y_{Q15}(n)$ | 还原后的$y(n)$ | MATLAB浮点结果 |
|:---:|---:|:---:|:---:|---:|---:|
| 0 | $0.5$ | `4000` | `1000` | $0.1250$ | $0.1250$ |
| 1 | $0.75$ | `6000` | `3800` | $0.4375$ | $0.4375$ |
| 2 | $0.5$ | `4000` | `3000` | $0.3750$ | $0.3750$ |
| 3 | $0.25$ | `2000` | `0000` | $0$ | $0$ |
| 4 | $0$ | `0000` | `0800` | $0.0625$ | $0.0625$ |
| 5 | $-0.25$ | `E000` | `2000` | $0.2500$ | $0.2500$ |
| 6 | $-0.5$ | `C000` | `1000` | $0.1250$ | $0.1250$ |
| 7 | $-0.75$ | `A000` | `F000` | $-0.1250$ | $-0.1250$ |
| 8 | $-0.5$ | `C000` | `E000` | $-0.2500$ | $-0.2500$ |
| 9 | $-0.25$ | `E000` | `F000` | $-0.1250$ | $-0.1250$ |
| 10 | $0$ | `0000` | `F000` | $-0.1250$ | $-0.1250$ |

可见定点计算的输出与MATLAB的浮点结果完全一致。
