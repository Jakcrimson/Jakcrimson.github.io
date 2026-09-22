# frozen_string_literal: true

source "https://rubygems.org"

# The site carries its own theme (see _layouts, _includes, _sass), so no theme gem.
gem "jekyll", "~> 4.3"

group :jekyll_plugins do
  gem "jekyll-paginate", "~> 1.1"
  gem "jekyll-seo-tag", "~> 2.8"
  gem "jekyll-sitemap", "~> 1.4"
  gem "jekyll-archives", "~> 2.2"
  gem "jekyll-redirect-from", "~> 0.16"
end

# Windows and JRuby do not include zoneinfo files.
platforms :mingw, :x64_mingw, :mswin, :jruby do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end

# Performance booster for watching directories on Windows.
gem "wdm", "~> 0.1", platforms: [:mingw, :x64_mingw, :mswin]

# Ruby 3.4 no longer ships these as default gems.
gem "csv"
gem "base64"
gem "bigdecimal"
gem "logger"

gem "webrick", "~> 1.8"
