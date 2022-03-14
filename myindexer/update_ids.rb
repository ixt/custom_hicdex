#!/bin/env ruby

require "active_record"
require "pg"
require "dotenv"
require "rest-client"
require "json"
require "pp"
require "cgi"

require "./models.rb"

class UpdateIds
  MAX_ITEMS = 1000

  def initialize()
  end

  def call
    update_dutch_auction
    update_english_auction
    update_asks
    update_bids
    update_fulfilled
    fix_holders
    log("End fixing ids")
  end

  def update_asks(min_id = -1)
    log("Fixing asks")
    generic_update("ask", Ask, min_id)
  end

  def update_bids(min_id = -1)
    log("Fixing bids")
    generic_update("bid", Bid, min_id)
  end

  def update_fulfilled(min_id = -1)
    log("Fixing fulfilled_asks")
    generic_update("fulfilled_ask", FulfilledAsk, min_id)
  end

  def update_english_auction(min_id = -1)
    log("Fixing english auction")
    generic_update("english_auction", EnglishAuction, min_id)
  end

  def update_dutch_auction(min_id = -1)
    log("Fixing dutch auction")
    generic_update("dutch_auction", DutchAuction, min_id)
  end

  def fix_holders
    log("Fixing holder names")
    Holder.where("name like '% '").each do |h|
      fix_holder(h)
    end
    Holder.where("name like ' %'").each do |h|
      fix_holder(h)
    end
    Holder.where("name like '%+%'").each do |h|
      fix_holder(h)
    end
  end

  protected

  def generic_update(type, kls, min_id)
    key_field = case type
      when "ask", "bid" then :pk_id
      else :id
      end

    while true
      log("processing from id #{min_id}")
      data = kls.where("token_id is null AND platform in ('bid', 'bid2') AND #{key_field}>?", min_id).order(key_field).limit(MAX_ITEMS).all()
      break if data.blank?
      new_id = process_data(type, key_field, data)
      break if new_id == min_id
      min_id = new_id
    end
    nb = kls.where("token_id is null").count
    log("#{nb} remaining #{type} without token")
  rescue PG::UndefinedTable, ActiveRecord::StatementInvalid
    log("Ignore fix for missing table #{type}")
  end

  def process_data(type, key_field, data)
    type = type.to_s
    min_id = 0
    data.each do |item|
      min_id = item.send(key_field) if item.send(key_field) >= min_id
      token = Token.find_by(fa2_id: item.fa2_id, id: item.objkt_id)
      next if token.blank?
      cols = { token_id: token.pk_id }
      if (type != "fulfilled_ask")
        cols[:royalties] = token.royalties unless item.royalties?
        cols[:artist_id] = token.creator_id unless item.artist_id?
      end
      item.update_columns(cols)
      log("#{type} #{item.id} linked to token #{token.pk_id}")
    end
    return min_id
  end

  def log(txt)
    @logger ||= begin
        fd = IO.sysopen("/proc/1/fd/1", "w")
        a = IO.new(fd, "w")
        a.sync = true # send log message immediately, don't wait
        a
      end
    @logger.puts "#{Time.now.strftime("%Y-%m-%d %H:%M:%S")} - #{txt}"
  end

  def fix_holder(holder)
    old = holder.name
    holder.name = CGI.unescape(holder.name).squish
    holder.save!
    log("fixed name '#{old}' -> '#{holder.name}'")
  end
end

UpdateIds.new().call
