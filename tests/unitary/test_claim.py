import brownie
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

    # Need to wait at least one second between epochs
    # (otherwise funds register in the next epoch)
    rpc.sleep(1)

    escrow.checkpoint()
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


def test_claim_no_balance(accounts, escrow, airdrop_token):
    airdrop_token.transfer(escrow, 10**18, {'from': accounts[0]})
    escrow.add_token(airdrop_token, {'from': accounts[0]})

    with brownie.reverts("User must have some deposits"):
        escrow.claim(airdrop_token, {'from': accounts[1]})


def test_claim_no_airdrop(accounts, escrow, airdrop_token):
    airdrop_token.transfer(escrow, 10**18, {'from': accounts[0]})

    with brownie.reverts("Airdrops in this token are not yet received"):
        escrow.claim(airdrop_token, {'from': accounts[0]})


def test_account_has_no_balance_at_airdrop(accounts, rpc, escrow, airdrop_token, lp_token):
    airdrop_token.transfer(escrow, 10**18, {'from': accounts[0]})

    lp_token._mint_for_testing(10**24, {'from': accounts[1]})
    lp_token.approve(escrow, 10**24, {'from': accounts[1]})
    escrow.deposit(10**24, {'from': accounts[1]})

    escrow.withdraw(10**24, {'from': accounts[0]})
    rpc.sleep(1)
    escrow.add_token(airdrop_token, {'from': accounts[0]})
    rpc.sleep(1)

    escrow.claim(airdrop_token, {'from': accounts[0]})

    assert airdrop_token.balanceOf(accounts[0]) == 0


def test_escrow_is_empty_at_airdrop(accounts, rpc, escrow, airdrop_token, lp_token):
    airdrop_token.transfer(escrow, 10**18, {'from': accounts[0]})

    escrow.withdraw(10**24, {'from': accounts[0]})
    rpc.sleep(1)
    escrow.add_token(airdrop_token, {'from': accounts[0]})
    rpc.sleep(1)

    escrow.claim(airdrop_token, {'from': accounts[0]})

    assert airdrop_token.balanceOf(accounts[0]) == 0
