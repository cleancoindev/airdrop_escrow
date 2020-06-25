import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def module_setup(accounts, escrow, lp_token, airdrop_token):
    lp_token._mint_for_testing(10**24, {'from': accounts[0]})
    lp_token.approve(escrow, 10**24, {'from': accounts[0]})
    escrow.deposit(10**24, {'from': accounts[0]})
    airdrop_token._mint_for_testing(10**18, {'from': accounts[0]})


def test_claim(accounts, escrow, airdrop_token, rpc):
    escrow.add_token(airdrop_token, {'from': accounts[0]})
    airdrop_token.transfer(escrow, 10**18, {'from': accounts[0]})
    escrow.checkpoint()  # Now escrow is aware of tokens


    # TODO this tx triggers a checkpoint so that claim works - ideally the checkpoint
    # is handled within `add_token` or `claim` and we can remove it
    rpc.sleep(1)
    escrow.withdraw(1, {'from': accounts[0]})

    rpc.sleep(1)
    escrow.claim(airdrop_token, {'from': accounts[0]})

    assert airdrop_token.balanceOf(accounts[0]) == 10**18


def test_claim_existing_balance(accounts, escrow, airdrop_token, rpc):
    airdrop_token.transfer(escrow, 10**18, {'from': accounts[0]})
    escrow.add_token(airdrop_token, {'from': accounts[0]})

    rpc.sleep(1)
    escrow.withdraw(1, {'from': accounts[0]})

    rpc.sleep(1)
    escrow.claim(airdrop_token, {'from': accounts[0]})

    assert airdrop_token.balanceOf(accounts[0]) == 10**18
