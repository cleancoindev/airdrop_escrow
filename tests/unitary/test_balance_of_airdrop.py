import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def module_setup(alice, bob, escrow, lp_token, airdrop_token):
    lp_token._mint_for_testing(10**24, {'from': bob})
    lp_token.approve(escrow, 10**24, {'from': bob})
    escrow.deposit(10**24, {'from': bob})
    airdrop_token._mint_for_testing(10**24, {'from': alice})


def test_airdrop_balance(alice, bob, escrow, airdrop_token, rpc, lp_token):
    airdrop_token.transfer(escrow, 10**18, {'from': alice})
    escrow.add_token(airdrop_token, {'from': alice})

    rpc.sleep(1)
    assert escrow.balanceOfAirdrop.call(airdrop_token, bob) == 10 ** 18

    escrow.claim(airdrop_token, {'from': bob})
    assert escrow.balanceOfAirdrop.call(airdrop_token, bob) == 0


def test_airdrop_balance_after_transfer(alice, bob, charlie, escrow, airdrop_token, rpc):
    airdrop_token.transfer(escrow, 10**18, {'from': alice})
    escrow.add_token(airdrop_token, {'from': alice})

    rpc.sleep(1)
    escrow.transfer(charlie, 10**24, {'from': bob})
    assert escrow.balanceOfAirdrop.call(airdrop_token, bob) == 10 ** 18

    escrow.claim(airdrop_token, {'from': bob})
    assert escrow.balanceOfAirdrop.call(airdrop_token, bob) == 0
