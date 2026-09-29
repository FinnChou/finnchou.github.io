#!/usr/bin/env ruby
#
# Check for changed posts

Jekyll::Hooks.register :posts, :post_init do |post|

  # 以文件最近一次 git 提交的时间作为修订日期（只有一次提交的文章也算：
  # 旧文都是整理后才第一次提交进来的，那次提交就是修订）。
  # 标题以 [meta] 开头的提交只改 description、标签等元信息，不算修订。
  lastmod_date = `git log -1 --pretty="%ad" --date=iso --invert-grep --grep="^\\[meta\\]" -- "#{ post.path }"`.strip

  post.data['last_modified_at'] = lastmod_date unless lastmod_date.empty?

end
