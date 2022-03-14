DROP VIEW IF EXISTS marketplace_ask;
CREATE VIEW marketplace_ask AS select fulfilled_ask.id, fulfilled_ask.token_id, fulfilled_ask.amount, fulfilled_ask.buyer_id, fulfilled_ask.seller_id, ask.artist_id, ask.price, ask.objkt_id, ask.fa2_id, ask.platform,
case
when fulfilled_ask.seller_id = ask.artist_id then 1
else 0
end primary_swap, fulfilled_ask.timestamp, date(fulfilled_ask.timestamp) buy_on
from fulfilled_ask inner join ask on fulfilled_ask.ask_id=ask.pk_id;



DROP VIEW IF EXISTS marketplace_bid;
CREATE VIEW marketplace_bid AS select bid.id, bid.token_id, 1 as amount, bid.creator_id as buyer_id, bid.seller_id, bid.artist_id, bid.price, bid.objkt_id, bid.fa2_id, bid.platform,
case
when bid.seller_id = bid.artist_id then 1
else 0
end primary_swap, bid.update_timestamp "timestamp", date(bid.update_timestamp) buy_on
from bid where bid.status='concluded';


DROP VIEW IF EXISTS fxhash_mint;
CREATE VIEW fxhash_mint AS select *, (supply-balance) as sold, 100*cast((supply-balance) as decimal) /supply as percentage_sold from token where fa2_id='KT1XCoGnfupWk7Sp8536EfrxcP73LmT68Nyr' and supply>0 and balance>0;


DROP MATERIALIZED VIEW IF EXISTS artist;
CREATE MATERIALIZED VIEW artist AS select
holder.address, holder.name, holder.twitter, holder.fxname, holder.last_buy, count(distinct token.id) as total_mint, min(token.timestamp) as first_mint, max(token.timestamp) as last_mint
from holder inner join token on holder.address = token.creator_id
where token.supply>0
group by address;


DROP VIEW IF EXISTS swap;
CREATE VIEW swap AS select id, price, amount, amount_left,
case
when ask.status = 'active' then 0
when ask.status = 'concluded' then 1
else 2
end status, ask.royalties, case
when ask.platform = 'hen1' then 1
else 2
end contract_version, is_valid, timestamp, creator_id, token_id
from ask where platform in ('hen1', 'hen2');


DROP VIEW IF EXISTS trade;
CREATE VIEW trade AS select id, amount, timestamp, buyer_id, seller_id, ask_id as swap_id, token_id
from fulfilled_ask where platform in ('hen1', 'hen2');


DROP MATERIALIZED VIEW IF EXISTS paperhand;
CREATE MATERIALIZED VIEW paperhand AS
SELECT ask.pk_id, ask.token_id, token.uuid, token.supply, ask.artist_id, ask.creator_id, ask.platform, ask.price as current_price, token.primary_price, 100*ask.price/token.primary_price as delta, ask."timestamp"
FROM ask inner join token on ask.token_id = token.pk_id
where ask.status='active' AND token.primary_price>0 AND ask.price<10000000000 and token.primary_price<10000000000 AND ask.creator_id<>ask.artist_id AND ask.platform not in ('hen1','fxhash');
CREATE INDEX idx_paperhand_delta on paperhand(delta);
CREATE INDEX idx_paperhand_timestamp on paperhand(timestamp);
