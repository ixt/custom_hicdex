#!/bin/env ruby

require "active_record"
require "pg"
require "dotenv"
require "rest-client"
require "json"
require "pp"

require "./models.rb"

class Token
  MIN_HOURS = 4

  def call
    refresh_paperhand
    refresh_recent_english
    refresh_recent_bids
    refresh_recent_fulfilled
    refresh_stats
    logger.info("Done")
  end

  def all(start_id = 0)
    while true
      list = Token.where("pk_id>=?", start_id).order("pk_id").limit(500).all
      break if list.blank?
      list.each do |t|
        t.refresh_stats!
        logger.info "Token #{t.pk_id} - #{t.total_sales}tz - #{t.primary_count} sales"
      end
      start_id = list.map(&:pk_id).max + 1
    end
  end

  def refresh_stats(full = false)
    @seen = {}

    logger.info "Refresh marketplace stats"
    generic_stats(MarketplaceAsk, full, "ask", false) # normal
    generic_stats(MarketplaceAsk, full, "ask", true) # pfp

    generic_stats(MarketplaceBid, full, "ask", false) # normal
    generic_stats(MarketplaceBid, full, "ask", true) # pfp
  end

  def refresh_paperhand
    logger.info "Refresh paperhand view"
    ActiveRecord::Base.connection.execute("REFRESH MATERIALIZED VIEW paperhand")
  end

  def refresh_recent_english
    logger.info "Refresh token from recent english"
    scoped = EnglishAuction.concluded.where("token_id is not null AND update_timestamp>=?", MIN_HOURS.hours.ago)
    scoped = scoped.select("token_id, max(update_timestamp) as last_updated").group(:token_id)
    generic_refresh(scoped)
  end

  def refresh_recent_bids
    logger.info "Refresh token from recent bids"
    scoped = Bid.concluded.where("token_id is not null AND update_timestamp>=?", MIN_HOURS.hours.ago)
    scoped = scoped.select("token_id, max(update_timestamp) as last_updated").group(:token_id)
    generic_refresh(scoped)
  end

  def refresh_recent_fulfilled
    logger.info "Refresh token from recent fulfilled ask"
    scoped = FulfilledAsk.where("token_id is not null AND timestamp>=?", MIN_HOURS.hours.ago)
    scoped = scoped.select("token_id, max(timestamp) as last_updated").group(:token_id)
    generic_refresh(scoped)
  end

  protected

  def generic_refresh(scoped)
    list = {}
    scoped.all.each do |e|
      list[e.token_id] = e.last_updated
    end

    Token.where("pk_id in (?)", list.keys).all.each do |t|
      next if (t.stats_updated_at && t.stats_updated_at >= list[t.pk_id])
      t.refresh_stats!
      logger.info "Token #{t.uuid} - #{t.total_sales}tz - #{t.primary_count} sales"
    end
    true
  end

  def generic_stats(kls, full, type, pfp = false)
    scoped = kls.select("platform, primary_swap, buy_on, sum(amount) as sales_count, sum(price*amount) as sales_total")
    scoped = scoped.where("timestamp>=?", 1.week.ago.beginning_of_day) unless full
    if pfp
      scoped = scoped.where("token_id is null")
    else
      scoped = scoped.where("token_id is not null")
    end
    scoped = scoped.group("platform, primary_swap, buy_on")

    scoped.all.each do |entry|
      platform = normalized_platform(entry.platform)
      platform = "custom_#{platform}" if pfp

      item = MarketplaceStat.where(platform: platform, primary_swap: entry.primary_swap, buy_on: entry.buy_on).first_or_initialize
      if item.new_record? || !@seen[item.id]
        item.sales_count = entry.sales_count
        item.sales_total = entry.sales_total
      else
        item.sales_count += entry.sales_count
        item.sales_total += entry.sales_total
      end
      item.save!
      logger.info "#{item.buy_on} - #{item.platform} - #{item.primary_swap} : #{type} #{@seen[item.id] ? "updated" : "added"}"
      @seen[item.id] = true
    end
  end

  private

  def normalized_platform(platform)
    case
    when platform.match(/bid/i) then "bid"
    when platform.match(/hen/i) then "hen"
    else platform
    end
  end

  def logger
    @logger ||= begin
        log = Logger.new(STDOUT)
        log.level = Logger::INFO
        ActiveRecord::Base.logger = log
        log
      end
  end
end

# Token.new(ARGV[0]).call
if (ARGV[0] == "all")
  Token.new.all
elsif ARGV[0] == "full_stats"
  Token.new.refresh_stats(true)
elsif ARGV[0] == "stats"
  Token.new.refresh_stats
else
  Token.new.call
end
