#!/bin/env ruby

require "active_record"
require "pg"
require "dotenv"
require "rest-client"
require "json"

puts "Connecting to db"
ActiveRecord::Base.establish_connection(ENV["DATABASE_URL"])

class Ask < ActiveRecord::Base
  self.table_name = "ask"
end

class Bid < ActiveRecord::Base
  self.table_name = "bid"
end

FA2_CONTRACT = "KT1FvqJwEDWb1Gwc55Jd1jjTHRVWbYKUUpyq"
LIMIT = 1000

module Tzkt
  module_function

  def retract_asks
    timestamp = Time.new.to_s
    lastId = 0
    page = 0
    processed = {}
    while true
      url = "https://api.tzkt.io/v1/accounts/#{FA2_CONTRACT}/operations?type=transaction&entrypoint=retract_ask"
      url += "&limit=#{LIMIT}"
      url += "&lastId=#{lastId}" if lastId > 0
      puts url
      sleep(2)
      data = http_request(url)
      data.each do |entry|
        lastId = entry["id"]
        timestamp = entry["timestamp"]
        ask_id = entry["parameter"]["value"]
        ask = Ask.where("id=? and platform=?", ask_id, "bid").first()
        if ask
          if (ask.status == "cancelled")
            puts "#{entry["timestamp"]} : Ask #{ask.id} already cancelled"
          else
            ask.status = "cancelled"
            ask.update_level = entry["level"]
            ask.update_timestamp = entry["timestamp"]
            ask.save!
            puts "#{entry["timestamp"]} : Ask #{ask.id} cancelled"
          end
        else
          puts "#{entry["timestamp"]} : Ask #{ask_id} NOT FOUND"
        end
      end
      break if timestamp < "2022-01-15T00:00:00Z"
    end
    puts "End fixing retract_ask"
  end

  def retract_bids
    timestamp = Time.new.to_s
    lastId = 0
    page = 0
    processed = {}
    while true
      url = "https://api.tzkt.io/v1/accounts/#{FA2_CONTRACT}/operations?type=transaction&entrypoint=retract_bid"
      url += "&limit=#{LIMIT}"
      url += "&lastId=#{lastId}" if lastId > 0
      puts url
      sleep(2)
      data = http_request(url)
      data.each do |entry|
        lastId = entry["id"]
        timestamp = entry["timestamp"]
        bid_id = entry["parameter"]["value"]
        bid = Bid.where("id=? and platform=?", bid_id, "bid").first()
        if bid
          if (bid.status == "cancelled")
            puts "#{entry["timestamp"]} : Bid #{bid.id} already cancelled"
          else
            bid.status = "cancelled"
            bid.update_level = entry["level"]
            bid.update_timestamp = entry["timestamp"]
            bid.save!
            puts "#{entry["timestamp"]} : Bid #{bid.id} cancelled"
          end
        else
          puts "#{entry["timestamp"]} : Bid #{bid_id} NOT FOUND"
        end
      end
      break if timestamp < "2022-01-15T00:00:00Z"
    end
    puts "End fixing retract_bid"
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

Tzkt.retract_asks
Tzkt.retract_bids
