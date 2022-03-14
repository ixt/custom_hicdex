require "active_record"
require "pg"
require "dotenv"
require "rest-client"
require "json"

puts "Connecting to db"
ActiveRecord::Base.establish_connection(ENV["DATABASE_URL"])

class Token < ActiveRecord::Base
  self.table_name = "token"
  self.primary_key = "pk_id"
end

class Holder < ActiveRecord::Base
  self.table_name = "holder"
  self.primary_key = "address"
end

FA2_CONTRACT = "KT1XCoGnfupWk7Sp8536EfrxcP73LmT68Nyr"

module Tzkt
  module_function

  def update_balances(limit = 500)
    url = "https://api.tzkt.io/v1/bigmaps/70072/keys?active=true&sort.desc=lastLevel&value.balance=0&limit=#{limit}"
    data = http_request(url)

    processed = {}
    data.each do |entry|
      token_id = entry["key"]
      next if processed[token_id]
      processed[token_id] = true

      token = Token.where("id=? and fa2_id=?", token_id, FA2_CONTRACT).first()
      if token
        infos = entry["value"]
        token.balance = infos["balance"] if (token.balance.to_s != infos["balance"])
        token.supply = infos["supply"] if (token.supply.to_s != infos["supply"])
        if token.changed?
          puts "Fix token #{token.attributes["id"]} - Supply: #{token.supply} - Balance: #{token.balance}"
          token.save
        end
      else
        puts "Token #{token_id} not found"
      end
    end
    puts "End fixing balances"
  end

  def update_moderation(limit = 500)
    # contract: KT1HgVuzNWVvnX16fahbV2LrnpwifYKoFMRd
    # moderated: 70061
    # report: 70063
    url = "https://api.tzkt.io/v1/bigmaps/70061/keys?sort.desc=lastLevel&limit=#{limit}"
    data = http_request(url)

    processed = {}
    data.each do |entry|
      token_id = entry["key"]
      next if processed[token_id]
      processed[token_id] = true

      moderated = entry["value"].to_i
      token = Token.where("id=? and fa2_id=?", token_id, FA2_CONTRACT).first()
      if (token && token.moderated != moderated)
        puts "Fix invalid report for #{token.attributes["id"]} - #{token.moderated} <> #{moderated}"
        token.moderated = moderated
        token.save
      end
    end
    puts "End fixing moderated token"
  end

  def user_moderation(limit = 500)
    # contract: KT1TWWQ6FtLoosVfZgTKV2q68TMZaENhGm54
    # moderated: 70065
    url = "https://api.tzkt.io/v1/bigmaps/70065/keys?sort.desc=lastLevel&limit=#{limit}"
    data = http_request(url)

    processed = {}
    data.each do |entry|
      wallet = entry["key"]
      next if processed[wallet]
      processed[wallet] = true

      fxflag = entry["value"].to_i
      fxflag = nil if fxflag.nil?
      holder = Holder.where("address=?", wallet).first()
      if (holder && holder.fxflag != fxflag)
        puts "Fix holder status for #{holder.address} - #{holder.fxflag} <> #{fxflag}"
        holder.fxflag = fxflag.to_i == 0 ? nil : fxflag
        holder.save
      end
    end
    puts "End fixing moderated users"
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

puts "Fxhash tokens: #{Token.where("fa2_id=?", FA2_CONTRACT).count}"
Tzkt.update_balances(1000)
Tzkt.update_moderation(1000)
Tzkt.user_moderation(1000)
