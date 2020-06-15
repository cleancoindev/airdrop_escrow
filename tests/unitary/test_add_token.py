


def test_add_token(accounts, escrow, airdrop_token):
    escrow.add_token(airdrop_token, {'from': accounts[0]})


def test_add_token_with_pool(accounts, escrow, airdrop_token, pool):
    escrow.add_token(airdrop_token, pool, {'from': accounts[0]})
