module Tzkt
  module_function

  def artist(wallet, reload = false)
    url = "https://api.tzkt.io/v1/accounts/#{wallet}/metadata"
    data = http_request(url)
    data["name"] = data.delete("alias")
    data["website"] = data.delete("website")
    data
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
