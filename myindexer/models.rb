ActiveRecord::Base.establish_connection(ENV["DATABASE_URL"])

class Block < ActiveRecord::Base
  self.table_name = "block"
  self.primary_key = "hash"
  alias_attribute :created_at, :timestamp

  def created_at=(new_value)
    @attributes.write_from_user("timestamp", new_value.to_time.to_s)
  end
end

class MarketplaceAsk < ActiveRecord::Base
  self.table_name = "marketplace_ask"

  def readonly?
    true
  end
end

class MarketplaceBid < ActiveRecord::Base
  self.table_name = "marketplace_bid"

  def readonly?
    true
  end
end

class MarketplaceStat < ActiveRecord::Base
end

class Fa2 < ActiveRecord::Base
  self.table_name = "fa2"
  self.primary_key = "contract"
end

class Token < ActiveRecord::Base
  self.table_name = "token"
  self.primary_key = "pk_id"

  has_many :asks
  has_many :bids, primary_key: :pk_id, class_name: "Bid"
  has_many :fulfilled_asks
  has_many :english_auctions

  before_save :normalize_attributes

  def token_id
    attributes["id"]
  end

  def stats
    data = {}
    item = self.bids.concluded.where("artist_id=seller_id").select("sum(price) as total_bid, count(*) as count_bid").take
    data.merge!(item.attributes)

    item = self.fulfilled_asks.where("seller_id=?", creator_id).select("sum(amount*price) as total_fulfilled, sum(amount) as count_fulfilled").take
    data.merge!(item.attributes)

    item = self.english_auctions.concluded.where("artist_id=creator_id").select("sum(highest_bid) as total_english, count(*) as count_english").take
    data.merge!(item.attributes)
    data.symbolize_keys!
    data
  end

  def total_sales
    (primary_total.to_f / 1000000).round(2)
  end

  def refresh_stats!
    data = self.stats
    self.primary_total = data[:total_english].to_i + data[:total_bid].to_i + data[:total_fulfilled].to_i
    self.primary_count = data[:count_english].to_i + data[:count_bid].to_i + data[:count_fulfilled].to_i
    self.primary_price = primary_count > 0 ? (primary_total / primary_count).to_i : 0
    self.stats_updated_at = Time.now
    save!
  end

  def normalize_attributes
    self.title = "" unless title?
    self.description = "" unless description?
    self.artifact_uri = "" unless artifact_uri?
    self.display_uri = "" unless display_uri?
    self.thumbnail_uri = "" unless thumbnail_uri?
    self.mime = "" unless mime?
    self.extra = {} unless extra?
  end

  def token_id
    self[:id]
  end

  def token_id=(new_value)
    @attributes.write_from_user("id", new_value.to_s)
    self.pk_id = nil if new_record?
  end
end

class Holder < ActiveRecord::Base
  self.table_name = "holder"
  self.primary_key = "address"

  before_save :normalize_attributes
  validates_presence_of :address, message: "can't be blank"

  def normalize_attributes
    self.name = name? ? name.squish : ""
    self.description = "" unless description?
    self.metadata_file = "" unless metadata_file?
    self.metadata = {} unless metadata?
  end

  def refresh?
    return true if new_record?
    return true unless last_refresh?
    if name?
      last_refresh <= 1.week.ago
    else
      last_refresh <= 1.day.ago
    end
  end

  def set_attributes_from_data(data)
    return if data.blank?
    if name.blank?
      self.name = data["name"] unless data["name"].blank?
    end
    self.twitter = data["twitter"] unless data["twitter"].blank?
    self.last_refresh = Time.current.beginning_of_day
  end
end

class TokenHolder < ActiveRecord::Base
  self.table_name = "token_holder"
  self.primary_key = "id"
  belongs_to :token
  belongs_to :holder
end

class Ask < ActiveRecord::Base
  self.table_name = "ask"
  belongs_to :token
end

class Bid < ActiveRecord::Base
  self.table_name = "bid"
  self.primary_key = "pk_id"
  belongs_to :token
  scope :concluded, -> { where("bid.status=?", "concluded") }
end

class FulfilledAsk < ActiveRecord::Base
  self.table_name = "fulfilled_ask"
  belongs_to :ask
  belongs_to :token
end

class DutchAuction < ActiveRecord::Base
  self.table_name = "dutch_auction"
  belongs_to :token
  scope :concluded, -> { where("dutch_auction.status=?", "concluded") }
end

class EnglishAuction < ActiveRecord::Base
  self.table_name = "english_auction"
  belongs_to :token
  scope :concluded, -> { where("english_auction.status=?", "concluded") }
end
