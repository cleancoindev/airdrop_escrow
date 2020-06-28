import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def module_setup(alice, bob, charlie, escrow, lp_token, airdrop_token):
    lp_token._mint_for_testing(10**24, {'from': bob})
    lp_token.approve(escrow, 10**24, {'from': bob})
    escrow.deposit(10**24, {'from': bob})
    airdrop_token._mint_for_testing(10**24, {'from': alice})


def test_claim(alice, bob, charlie, escrow, airdrop_token, rpc):
    escrow.add_token(airdrop_token, {'from': alice})
    airdrop_token.transfer(escrow, 10**18, {'from': alice})

    # Need to wait at least one second between epochs
    # (otherwise funds register in the next epoch)
    rpc.sleep(1)

    escrow.checkpoint()
    escrow.claim(airdrop_token, {'from': bob})

    assert airdrop_token.balanceOf(bob) == 10**18


def test_claim_existing_balance(alice, bob, charlie, escrow, airdrop_token, rpc):
    airdrop_token.transfer(escrow, 10**18, {'from': alice})
    escrow.add_token(airdrop_token, {'from': alice})

    rpc.sleep(1)
    escrow.withdraw(10**24, {'from': bob})

    rpc.sleep(1)
    escrow.claim(airdrop_token, {'from': bob})

    assert airdrop_token.balanceOf(bob) == 10**18


def test_claim_multiple_accounts(alice, bob, charlie, rpc, escrow, airdrop_token, lp_token):
    lp_token._mint_for_testing(10**24, {'from': charlie})
    lp_token.approve(escrow, 10**24, {'from': charlie})
    escrow.deposit(10**24, {'from': charlie})

    rpc.sleep(1)
    escrow.add_token(airdrop_token, {'from': alice})
    airdrop_token.transfer(escrow, 2 * 10**18, {'from': alice})

    rpc.sleep(1)

    escrow.checkpoint()
    escrow.claim(airdrop_token, {'from': bob})
    escrow.claim(airdrop_token, {'from': charlie})

    assert airdrop_token.balanceOf(bob) == 10**18
    assert airdrop_token.balanceOf(charlie) == 10**18


def test_claim_no_balance(alice, bob, charlie, escrow, airdrop_token):
    airdrop_token.transfer(escrow, 10**18, {'from': alice})
    escrow.add_token(airdrop_token, {'from': alice})

    with brownie.reverts("User must have some deposits"):
        escrow.claim(airdrop_token, {'from': charlie})


def test_claim_no_airdrop(alice, bob, charlie, escrow, airdrop_token):
    airdrop_token.transfer(escrow, 10**18, {'from': alice})

    with brownie.reverts("Airdrops in this token are not yet received"):
        escrow.claim(airdrop_token, {'from': bob})


def test_no_account_balance_at_airdrop(alice, bob, charlie, rpc, escrow, airdrop_token, lp_token):
    airdrop_token.transfer(escrow, 10**18, {'from': alice})

    lp_token._mint_for_testing(10**24, {'from': charlie})
    lp_token.approve(escrow, 10**24, {'from': charlie})
    escrow.deposit(10**24, {'from': charlie})

    escrow.withdraw(10**24, {'from': bob})
    rpc.sleep(1)
    escrow.add_token(airdrop_token, {'from': alice})
    rpc.sleep(1)

    escrow.claim(airdrop_token, {'from': bob})

    assert airdrop_token.balanceOf(bob) == 0


def test_escrow_is_empty_at_airdrop(alice, bob, charlie, rpc, escrow, airdrop_token, lp_token):
    airdrop_token.transfer(escrow, 10**18, {'from': alice})

    escrow.withdraw(10**24, {'from': bob})
    rpc.sleep(1)
    escrow.add_token(airdrop_token, {'from': alice})
    rpc.sleep(1)

    escrow.claim(airdrop_token, {'from': bob})

    assert airdrop_token.balanceOf(bob) == 0
