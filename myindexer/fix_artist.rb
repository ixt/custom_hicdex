#!/bin/env ruby

require "active_record"
require "pg"
require "dotenv"
require "rest-client"
require "json"
require "pp"
require "cgi"

require "./models.rb"

class FixArtist
  def initialize()
  end

  def call()
    fix_collection_artist(0)
  end

  def fix_collection_artist(page = 0)
    limit = 1000
    timestamp = nil
    while true
      url = "https://api.tzkt.io/v1/operations/transactions?entrypoint=mint_artist&status=applied&target=KT1Aq4wWmVanpQhq4TTfjZXB5AjFpx15iQMM&select=id,timestamp,sender,target,parameter,diffs&limit=#{limit}"
      url += "&offset=#{page * limit}" if (page > 0)
      puts "Page #{page} - #{timestamp}: #{url}"
      data = http_request(url)
      break if data.blank?

      data.each do |entry|
        timestamp = entry["timestamp"]
        collection_id = entry["parameter"]["value"]["collection_id"]
        creator_id = entry["sender"]["address"]
        diff = entry["diffs"].detect { |e| e["path"] == "artist_collections" }
        content = diff["content"]["value"]

        token_id = content["token_id"].to_i - 1
        if token_id < 0
          log "ERROR INVALID TOKEN_ID"
          pp entry
          exit
        end

        fa2_id = content["contract"]

        token = Token.where("id=? AND fa2_id=?", token_id.to_s, fa2_id).first()
        next unless token # ignore missing token
        next if token.creator_id == creator_id
        log "Token: #{token.uuid.gsub(/_/i, "/")} - #{collection_id}: #{token.creator_id} -> #{creator_id}"
        creator = Holder.find_or_create_by(address: creator_id)
        token.creator_id = creator_id
        token.save!
      end
      break if data.blank?
      page += 1
    end
  end

  protected

  def log(txt)
    @logger ||= begin
        fd = IO.sysopen("/proc/1/fd/1", "w")
        a = IO.new(fd, "w")
        a.sync = true # send log message immediately, don't wait
        a
      end
    @logger.puts txt
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

if (ARGV[0].to_i > 0)
  FixArtist.new().fix_collection_artist(ARGV[0].to_i)
else
  FixArtist.new().call
end
