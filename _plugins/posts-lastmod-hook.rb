#!/usr/bin/env ruby
#
# Check for changed posts

Jekyll::Hooks.register :posts, :post_init do |post|

  # 以文件最近一次 git 提交的时间作为修订日期（只有一次提交的文章也算：
  # 旧文都是整理后才第一次提交进来的，那次提交就是修订）。
  commit_num = `git rev-list --count HEAD "#{ post.path }"`

  if commit_num.to_i >= 1
    lastmod_date = `git log -1 --pretty="%ad" --date=iso "#{ post.path }"`
    post.data['last_modified_at'] = lastmod_date
  end

end
