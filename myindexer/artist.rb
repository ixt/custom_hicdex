#!/bin/env ruby

require "active_record"
require "pg"
require "dotenv"
require "rest-client"
require "json"
require "pp"

require "./models.rb"
require "./tzprofile.rb"
require "./tzkt.rb"

class Artist
  attr_accessor :wallet

  def initialize(wallet = nil)
    self.wallet = wallet
  end

  def call
    if wallet.blank?
      logger.info "Refresh artist data"
      refresh_empty
      refresh_recent_mint
      refresh_missing
      refresh_recent_buy
      refresh_old
      refresh_view
      logger.info "End refresh artist"
    else
      artist = Holder.find_by_address(wallet)
      refresh_artist(artist, true)
    end
  end

  def refresh_view
    ActiveRecord::Base.connection.execute("REFRESH MATERIALIZED VIEW artist")
  end

  def refresh_empty
    logger.info "Refresh artist never refreshed"
    while true
      scoped = Holder.where("address<>'' and last_refresh is null")
      list = scoped.order("last_refresh NULLS FIRST, address").limit(1000)
      break if list.blank?
      list.each do |artist|
        refresh_artist(artist)
      end
    end
    true
  end

  def refresh_missing
    logger.info "Refresh recent artist without name"
    scoped = Holder.where("address<>'' AND name='' AND last_refresh<=?", 1.week.ago)
    scoped.order("last_refresh NULLS FIRST, address").limit(2500).each do |artist|
      refresh_artist(artist)
    end
    true
  end

  def refresh_recent_mint(full = false)
    logger.info "Refresh wallets with recent mint"
    scoped = Holder.where("address<>'' AND last_mint>last_refresh")
    scoped = scoped.where("last_refresh<=?", 1.day.ago) unless full
    scoped.order("last_refresh NULLS FIRST, address").limit(2500).each do |artist|
      refresh_artist(artist, true)
    end
  end

  def refresh_recent_buy(full = false)
    logger.info "Refresh wallets with recent buy"
    scoped = Holder.where("last_buy>last_refresh")
    scoped = scoped.where("last_refresh<=?", 7.day.ago) unless full
    scoped.order("last_refresh NULLS FIRST, address").limit(2500).each do |artist|
      refresh_artist(artist, true)
    end
  end

  def refresh_old
    logger.info "Refresh old artist with a name"
    scoped = Holder.where("name<>'' AND last_refresh<=?", 1.month.ago)
    scoped.order("last_refresh NULLS FIRST, address").limit(2500).each do |artist|
      refresh_artist(artist)
    end
    true
  end

  def refresh_artist(artist, force = false)
    return unless force || artist.refresh?
    data = Tzprofile.get_profile(artist.address)
    artist.set_attributes_from_data(data) unless data.blank?
    unless artist.name? && artist.twitter?
      # retrieve info from tzkt
      data = Tzkt.artist(artist.address)
      artist.set_attributes_from_data(data) unless data.blank?
    end
    artist.last_refresh = Time.current.beginning_of_day
    artist.save!
    logger.info "Updated #{artist.address} # #{artist.name} - @#{artist.twitter}"
  end

  private

  def logger
    @logger ||= begin
        log = Logger.new(STDOUT)
        log.level = Logger::INFO
        ActiveRecord::Base.logger = log
        log
      end
  end
end

Artist.new(ARGV[0]).call
