---
# the default layout is 'page'
icon: fas fa-info-circle
order: 4
math: true
---

<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&display=swap">

<style>
/* 签名样式 - 优雅手写体 */
.signature-1 {
  font-family: 'Dancing Script', 'Brush Script MT', 'Snell Roundhand', cursive;
  font-size: 42px;
  color: #333;
  line-height: 1.4;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
  margin: 20px 0;
}

/* 暗色模式下的签名样式 */
@media (prefers-color-scheme: dark) {
  .signature-1 {
    color: #e0e0e0;
    text-shadow: 1px 1px 3px rgba(255,255,255,0.15);
  }
}

/* 针对Chirpy主题的暗色模式 */
body[data-mode="dark"] .signature-1 {
  color: #e0e0e0;
  text-shadow: 1px 1px 3px rgba(255,255,255,0.15);
}

/* 链接系列样式 */
.series-link {
  display: inline-block;
  margin: 10px 0;
  padding: 10px 20px;
  background: linear-gradient(135deg, #6e8efb, #a777e3);
  border-radius: 6px;
  color: white !important;
  font-weight: bold;
  text-decoration: none;
  box-shadow: 0 3px 6px rgba(0,0,0,0.16);
  transition: all 0.3s ease;
}

.series-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 10px rgba(0,0,0,0.2);
  text-decoration: none;
}

.series-link::before {
  content: "📚 ";
}

/* 暗色模式下的链接系列样式 */
@media (prefers-color-scheme: dark) {
  .series-link {
    background: linear-gradient(135deg, #5a6fc0, #9163c9);
    box-shadow: 0 3px 6px rgba(0,0,0,0.3);
  }
}

body[data-mode="dark"] .series-link {
  background: linear-gradient(135deg, #5a6fc0, #9163c9);
  box-shadow: 0 3px 6px rgba(0,0,0,0.3);
}
</style>

![Desktop View](/assets/resource/about_me/Me_Rect_2023.jpg){: width="300" height="300"}

<div align="center" class="signature-1">Fan (Finn) Zhou</div>

<div align="center" style="font-size: 18px;"> Email : 🇨🇳 wheat1148158886[at]gmail.com</div>
<div align="center" style="font-size: 18px;"> Email : 🇯🇵 zhoufan1148158886[at]yahoo.co.jp</div>

### 关于我...
&nbsp;
我是Finn，硕士毕业于日本东北大学工学研究科电子工学专业，期间在川又・阿部研究室进行学习与研究。
目前从事计算机视觉相关工作，在传统信号处理、图像分析、特征检测与分割、生成模型以及色彩科学等领域积累了一些研发经验。

&nbsp;
Finn（フィン）と申します。日本の東北大学大学院工学研究科電子工学専攻にて修士課程を修了し、川又・阿部研究室にて画像処理技術の研究に取り組んでいました。
現在はコンピュータビジョン関連の業務に従事し、信号・画像処理技術の開発、特徴検出/セグメンテーション、生成モデルの応用、色彩科学分野などで経験を積んでおります。


&nbsp;
### 数字信号处理
这个部份的文字，大概写于2013年。这一年，我通过大学院入学考试后，从研修生正式成为川又研的M1学生（硕士一年级）。在川又・阿部研究室，所有学生都需要先完成以1D信号处理为核心的「研修A」课程，这是数字信号处理的入门必修课。

这是我第一次有了写一些东西的想法之后，将「研修A」的课程笔记和与阿部老师的Meeting的记录整理而成，当时（2013年）同步更新在CSDN博客。

最近（2024年）重新审阅这些旧文时，发现不少表述已显稚嫩。虽然已在不改变技术原意的前提下对文字进行重构，并用 $\LaTeX$ 重排了所有公式，但依然觉得行文不够理想。同时，也担心内容中可能存在一些技术上的不严谨之处。如您发现任何错误，欢迎通过邮件指正。

修订版现发布于此，原CSDN文章将择期归档。 - 📎 [Finn's CSDN 数字信号处理专栏]

[Finn's CSDN 数字信号处理专栏]: https://blog.csdn.net/zhoufan900428/category_1428367.html

<a href="{{ site.baseurl }}/categories/数字信号处理/" class="series-link">数字信号处理系列Posts</a>

&nbsp;
### 数字图像处理
2013年后半年的时候，为期大概不到一个学期的「研修A」的课程顺利完成。我选择图像处理方向为后续卒論的课题，并开始在阿部老师的指导下，系统的进行图像处理相关知识的学习。和「研修A」一样，当时我也定期整理笔记在CSDN博客进行更新（📎 [Finn's CSDN 数字图像处理专栏]）。

研究过程中主要参考冈萨雷斯教授的经典著作📎 [《Digital Image Processing》]（绿皮书），博文中所使用的实验图像均源自该教材配套网站。

虽说在AI浪潮的影响下，数字图像处理已经由经典的计算性学科，彻底变为了实验性学科。但是一些传统的经典的算法，仍然为很多AI算法提供了有力的理论支持。
「研修A」部份的内容整理完毕后，最近（2025年3月）也开始着手整理这部份的博文。同样的，这部份的内容也可能存在一些不够严谨的部份，如发现任何错误，欢迎通过邮件指正。

[《Digital Image Processing》]: https://www.imageprocessingplace.com/
[Finn's CSDN 数字图像处理专栏]: https://blog.csdn.net/zhoufan900428/category_1700021.html


目前仍在，施工中 ... 

<a href="{{ site.baseurl }}/categories/数字图像处理/" class="series-link">数字图像处理系列Posts</a>


&nbsp;
### 色彩科学
2015年我加入M社，从事ISP算法开发工作，主要负责色彩矫正和色彩恒常性相关算法的研发。在实际工作中，色彩理论是图像处理领域的基础且关键的组成部分，涉及物理学和光学等多学科知识。这些理论在相机成像、显示器、工业印刷和摄影等多个行业中有着广泛应用。

然而，我发现公司内许多同事并未系统学习过色彩科学理论。为此，我利用业余时间翻译整理了日本シーシーエス株式会社的📎 **[「光と色の話」]**系列文章，为团队提供了一些简单的色彩科学的入门科普。

我将该系列译为"话说光与色"，原文从2011年开始连载，至2016年5月完成第一部，共42篇。2016年6月，我从中精选了12篇核心内容，翻译整理后发布在M社内部知识库，供同事学习参考。这些内容主要从三个方面介绍色彩科学基础：
  - 色彩的本质与感知
  - 色彩的客观表达方法
  - 色差计算与色彩空间转换

近期整理学习笔记时，认为这部分内容具有较高参考价值。考虑到目标读者已不限于公司内部，且简单翻译可能存在版权问题，我计划重构这部分内容，融入个人理解并补充色彩科学的相关知识，形成更有价值的技术资料。

[「光と色の話」]: https://www.ccs-inc.co.jp/guide/column/light_color/

第一篇已整理完毕，其余部份仍在，施工中 ... 

<a href="{{ site.baseurl }}/categories/色彩科学/" class="series-link">色彩科学系列Posts</a>


