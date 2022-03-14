require "rest-client"

module Tzprofile
  PROFILE_QUERY = <<-EOF
  query doRequest($wallet: String!) {
    tzprofiles_by_pk(account: $wallet) {
      valid_claims
    }
  }
  EOF

  PROFILES_QUERY = <<-EOF
  query doRequest($wallets: String!) {
    tzprofiles_aggregate(where: { account: { _in: $wallets }}) {
      nodes {
        account
        valid_claims
      }
    }
  }
  EOF

  module_function

  # NOT WORKING CURRENTLY ... Should ask to @tzprofiles
  # def get_profiles(wallets)
  #   data = (graph_request(PROFILES_QUERY, variables: { wallets: wallets }) || {})
  # end

  def get_profile(wallet)
    data = (graph_request(PROFILE_QUERY, variables: { wallet: wallet }) || {})["tzprofiles_by_pk"]
    data = data["valid_claims"] unless data.blank?
    profile = {}
    profile["address"] = wallet
    return profile if data.blank?
    data.each do |json|
      claim = JSON.parse(json[1])
      infos = claim["credentialSubject"] || {}
      if (claim["type"].include?("BasicProfile"))
        profile["name"] = infos["alias"]
        profile["website"] = infos["website"]
        profile["description"] = infos["description"]
      elsif (claim["type"].include?("TwitterVerification"))
        profile["twitter"] = claim["evidence"]["handle"]
      end
    end && true
    profile
  end

  def graph_request(query, variables: nil, raw: false, operation: nil)
    payload = {
      query: query,
      operationName: operation || "doRequest",
    }
    payload[:variables] = variables unless variables.blank?
    res = RestClient.post("https://indexer.tzprofiles.com/v1/graphql", payload.to_json, accept: :json, content_type: :json)
    data = JSON.parse(res.body)
    raw ? data : (data || {})["data"]
  end
end
