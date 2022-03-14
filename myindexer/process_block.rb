#!/bin/env ruby

require "active_record"
require "pg"
require "dotenv"
require "rest-client"
require "json"
require "pp"

require "./models.rb"

class ProcessBlock
  attr_accessor :block_hash
  attr_accessor :block_level
  attr_accessor :block_timestamp
  attr_accessor :transactions
  attr_accessor :full

  FIRST_BLOCK = 1855000

  def initialize(block_level = nil)
    if block_level.to_s == "all"
      self.full = true
    else
      self.block_level = block_level.blank? ? nil : block_level
    end
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

  def wait_next_block
    log "pause ... waiting for next block"
    sleep(20)
    return http_request("https://api.tzkt.io/v1/blocks/count").to_i
  end

  def call
    if full
      last_block = http_request("https://api.tzkt.io/v1/blocks/count").to_i
      if last_block == 0
        log("Error unable to get last_block")
        return
      end
      while true
        set_block_level
        if block_level > 0 && block_level <= last_block
          if !process_block
            last_block = wait_next_block
          end
        else
          last_block = wait_next_block
        end
        self.block_level = nil
      end
    else
      set_block_level
      process_block
    end
  end

  def process_block
    self.transactions = retrieve_operations
    if transactions == false
      transactions = []
      return false
    end

    log "Processing block at level #{block_level} - #{block_timestamp}"
    ActiveRecord::Base.transaction do
      process_collections
      process_tokens
      memoize_block
    end
    return true
  end

  protected

  def process_collections
    transactions.each do |tx|
      params = tx["parameter"] || {}
      next if params.blank?
      next if params["entrypoint"] != "create_artist_collection"

      target = tx["target"] || {}
      next if target["address"] != "KT1Aq4wWmVanpQhq4TTfjZXB5AjFpx15iQMM"

      process_collection(tx)
    end
  end

  def clean_null_bytes(txt)
    return "" if txt.blank?
    txt.to_s.delete("\000")
  end

  def process_tokens
    transactions.each do |tx|
      params = tx["parameter"] || {}
      next if params.blank?
      next if params["entrypoint"] != "mint" && params["entrypoint"] != "transfer"

      fa2_id = tx["target"]["address"]
      ok = Fa2.where("contract=? and collection_id is not null", fa2_id).count > 0
      next unless ok

      case params["entrypoint"]
      when "mint" then process_mint(tx)
      when "transfer" then process_transfer(tx)
      end
    end
  end

  def process_collection(tx)
    # check if it's objkt minter factory
    params = tx["parameter"] || {}

    metadata = decode_hex(params["value"])

    # retrieve full operation infos
    tx = retrieve_operation(tx["hash"], "create_artist_collection")
    diff = tx["diffs"].find { |e| e["path"] == "artist_collections" }
    collection_id = diff["content"]["key"]
    infos = diff["content"]["value"]

    item = {
      contract: infos["contract"],
      creator_id: infos["creator"],
      collection_id: collection_id,
      metadata: clean_null_bytes(metadata),
      timestamp: tx["timestamp"],
    }
    holder = Holder.find_or_create_by(address: item[:creator_id])
    contract = Fa2.find_or_initialize_by(contract: item[:contract])
    contract.creator_id = holder.address
    contract.metadata = item[:metadata]
    contract.collection_id = item[:collection_id]
    contract.timestamp = item[:timestamp]
    contract.save!
    log "indexing contract #{item[:contract]} by #{holder.address}"
  end

  def process_mint(tx)
    mint = tx["parameter"]["value"]
    metadata = decode_hex(mint["metadata"][""])

    fa2_id = tx["target"]["address"]
    data = {
      fa2_id: fa2_id,
      token_id: mint["token_id"].to_s,
      creator_id: mint["address"],
      supply: mint["amount"].to_i,
      metadata: clean_null_bytes(metadata),
      level: tx["level"].to_i,
      timestamp: tx["timestamp"],
    }
    data[:uuid] = "#{data[:fa2_id]}_#{data[:token_id]}"
    holder_id = mint["address"]

    # retrieve creator infos
    mint_artist = retrieve_operation(tx["hash"], "mint_artist")
    creator_id = mint_artist["sender"]["address"]
    data[:creator_id] = creator_id if (creator_id && creator_id != holder_id)

    holder = Holder.find_or_create_by(address: holder_id)
    holder.last_buy = data[:timestamp]
    holder.last_mint = data[:timestamp] if holder_id == data[:creator_id]
    holder.save!

    if holder_id != data[:creator_id]
      creator = Holder.find_or_create_by(address: data[:creator_id])
      creator.last_mint = data[:timestamp]
      creator.save!
    end

    token = Token.find_or_initialize_by(fa2_id: data[:fa2_id], id: data[:token_id])
    if token.new_record?
      token.attributes = data
    else
      token.creator_id = data[:creator_id]
      token.supply = data[:supply]
      token.metadata = data[:metadata]
      token.level = data[:level]
      token.timestamp = data[:timestamp]
    end
    token.save!

    holding = TokenHolder.find_or_initialize_by(holder_id: holder_id, token_id: token.pk_id)
    if holding.new_record?
      holding.quantity = data[:supply]
      holding.save!
    end
    txt = data[:creator_id] != holder_id ? "for #{holder_id}" : ""
    log "token #{data[:uuid]} minted by #{data[:creator_id]} #{txt}"
  rescue StandardError => e
    puts tx.inspect
    raise(e)
  end

  def process_transfer(operation)
    fa2_id = operation["target"]["address"]
    operation["parameter"]["value"].each do |transfer|
      sender = Holder.find_or_create_by(address: transfer["from_"])
      transfer["txs"].each do |tx|
        amount = tx["amount"].to_i
        token = Token.where(fa2_id: fa2_id, id: tx["token_id"]).first

        receiver = Holder.find_or_create_by(address: tx["to_"])
        if (receiver.address != "tz1burnburnburnburnburnburnburjAYjjX")
          receiver.last_buy = operation["timestamp"]
          receiver.save!
        end

        sender_holding = TokenHolder.find_or_initialize_by(holder_id: sender.address, token_id: token.pk_id)
        if sender_holding.new_record?
          sender_holding.quantity = -amount
        else
          sender_holding.quantity -= amount
        end
        sender_holding.save!

        receiver_holding = TokenHolder.find_or_initialize_by(holder_id: receiver.address, token_id: token.pk_id)
        if receiver_holding.new_record?
          receiver_holding.quantity = amount
        else
          receiver_holding.quantity += amount
        end
        receiver_holding.save!

        if (receiver.address == "tz1burnburnburnburnburnburnburjAYjjX")
          token.supply -= amount
          token.save!
          log "burned #{amount}x#{token.pk_id} by #{sender.address}"
        else
          log "transferred #{amount}x#{token.pk_id} from #{sender.address} to #{receiver.address}"
        end
      end
    end
  end

  def memoize_block
    raise StandardError.new("missing block level") if block_level.blank?
    if block_level != FIRST_BLOCK
      previous = Block.find_by_level(block_level - 1)
      raise StandardError.new("previous block #{block_level - 1} not found") if previous.blank?
    end

    block = Block.find_or_initialize_by(hash: block_hash)
    if block.new_record?
      sql = "INSERT INTO \"public\".\"block\" (\"hash\", \"predecessor\", \"level\", \"timestamp\") VALUES ('#{block_hash}', '#{previous.hash}', #{block_level.to_i}, '#{block_timestamp}')"
      ActiveRecord::Base.connection.exec_query(sql)
    end
    self.block_level = block_level + 1
  end

  private

  def decode_hex(txt)
    [txt].pack("H*")
  end

  def set_block_level
    return unless block_level.blank?
    block = Block.order("level DESC").first
    if !block
      self.block_level = FIRST_BLOCK
    else
      self.block_level = block.level + 1
    end
    self.block_hash = nil
  end

  def retrieve_operation(hash, type)
    # retrieve full operation infos
    url = "https://api.tzkt.io/v1/operations/#{hash}"
    data = http_request(url)
    data.find { |e| (e["parameter"] || {})["entrypoint"] == type }
  end

  def retrieve_operations
    key = block_level.blank? ? block_hash : block_level
    url = "https://api.tzkt.io/v1/blocks/#{key}?operations=true"
    data = http_request(url)
    self.block_level = data["level"]
    self.block_hash = data["hash"]
    self.block_timestamp = data["timestamp"]
    return false if data.blank?
    return data["transactions"].select { |e| e["status"] == "applied" }
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

ProcessBlock.new(ARGV[0]).call
