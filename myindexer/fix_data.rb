#!/bin/env ruby

require "active_record"
require "pg"
require "dotenv"
require "rest-client"
require "json"
require "pp"
require "cgi"

require "./models.rb"

class FixData
  BIGMAP_ENGLISH_V2 = 6210
  BIGMAP_ENGLISH_V1 = 5904

  def initialize()
  end

  def call
    # fix_sales_price
    # fix_english(BIGMAP_ENGLISH_V2)
    fix_english(BIGMAP_ENGLISH_V1)
  end

  def fix_sales_price
    while true
      data = FulfilledAsk.where("price is null").order("id").preload(:ask).limit(2000)
      break if data.blank?
      data.each do |sale|
        sale.price = sale.ask.price
        sale.save!
        log("#{sale.id} - #{(sale.price.to_f / 1000000).round(3)}tz")
      end
    end
  end

  def fix_english(bigmap, page = 0)
    limit = 500
    while true
      url = "https://api.tzkt.io/v1/bigmaps/#{bigmap}/keys?value.state=2&limit=#{limit}"
      url += "&offset=#{page * limit}" if page.to_i > 0
      puts url
      sleep(2)
      data = http_request(url)
      data.each do |entry|
        last_id = entry["id"]
        auction_id = entry["key"]
        infos = entry["value"]
        item = EnglishAuction.where("id=?", auction_id).first()
        next if item.highest_bidder_id?
        item.update_columns(highest_bidder_id: infos["highest_bidder"], highest_bid: infos["current_price"].to_i)
        puts "auction #{auction_id} updated - #{item.highest_bidder_id} - #{item.highest_bid}"
      end
      break if data.blank?
      page += 1
    end
    puts "End fixing retract_ask"
  end

  protected

  def log(txt)
    @logger ||= begin
        fd = IO.sysopen("/proc/1/fd/1", "w")
        a = IO.new(fd, "w")
        a.sync = true # send log message immediately, don't wait
        a
      end
    @logger.puts "#{Time.now.strftime("%Y-%m-%d %H:%M:%S")} - #{txt}"
  end

  def http_request(url)
    res = RestClient::Request.execute(
      url: url,
      method: :get,
      headers: { content_type: :json },
      verify_ssl: false,
    )
    return {} if res.body.blank?
    JSON.parse(res.body)
  end
end

FixData.new().call
