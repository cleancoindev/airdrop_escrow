import brownie

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_admin_only(bob, escrow, airdrop_token):
    with brownie.reverts("dev: admin only"):
        escrow.add_token(airdrop_token, {'from': bob})


def test_add_token(alice, escrow, airdrop_token):
    escrow.add_token(airdrop_token, {'from': alice})

    assert escrow.airdropped_tokens(0) == airdrop_token
    assert escrow.token_to_pool(airdrop_token) == ZERO_ADDRESS
    assert escrow.token_epochs(airdrop_token, 0) == escrow.epoch()


def test_add_token_with_pool(alice, escrow, airdrop_token, pool):
    escrow.add_token(airdrop_token, pool, {'from': alice})

    assert escrow.airdropped_tokens(0) == airdrop_token
    assert escrow.token_to_pool(airdrop_token) == pool
    assert escrow.token_epochs(airdrop_token, 0) == escrow.epoch()
