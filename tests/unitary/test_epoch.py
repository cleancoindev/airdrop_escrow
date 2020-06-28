import pytest


@pytest.fixture(scope="module")
def epoch(alice, escrow, lp_token):
    lp_token._mint_for_testing(10**24, {'from': alice})
    lp_token.approve(escrow, 10**24, {'from': alice})
    escrow.deposit(10**18, {'from': alice})

    yield escrow.epoch()


def test_transfer(alice, bob, escrow, lp_token, epoch):
    escrow.transfer(bob, 10**18, {'from': alice})

    assert escrow.epoch() == epoch + 1


def test_transferFrom(alice, bob, charlie, escrow, lp_token, epoch):
    escrow.approve(charlie, 10**18, {'from': alice})
    escrow.transferFrom(alice, bob, 10**18, {'from': charlie})

    assert escrow.epoch() == epoch + 1


def test_deposit(alice, escrow, lp_token, epoch):
    escrow.deposit(10**18, {'from': alice})

    assert escrow.epoch() == epoch + 1


def test_withdraw(alice, escrow, lp_token, epoch):
    escrow.withdraw(10**18, {'from': alice})

    assert escrow.epoch() == epoch + 1


def test_add_token(alice, escrow, airdrop_token, epoch):
    escrow.add_token(airdrop_token, {'from': alice})

    assert escrow.epoch() == epoch + 1


def test_remove_token(alice, escrow, airdrop_token, epoch):
    escrow.add_token(airdrop_token, {'from': alice})
    escrow.remove_token(1, {'from': alice})

    assert escrow.epoch() == epoch + 2


def test_claim(rpc, alice, bob, escrow, airdrop_token, epoch):
    airdrop_token._mint_for_testing(10**18, {'from': alice})
    airdrop_token.transfer(escrow, 10**18, {'from': alice})
    escrow.add_token(airdrop_token, {'from': alice})
    rpc.sleep(1)  # Need at least 1 second to have non-infinite rates
    escrow.claim(airdrop_token, {'from': alice})

    assert escrow.epoch() == epoch + 2


def test_transfer_zero(alice, bob, escrow, lp_token, epoch):
    escrow.transfer(bob, 0, {'from': alice})

    assert escrow.epoch() == epoch


def test_transferFrom_zero(alice, bob, charlie, escrow, lp_token, epoch):
    escrow.transferFrom(alice, bob, 0, {'from': charlie})

    assert escrow.epoch() == epoch


def test_deposit_zero(alice, escrow, lp_token, epoch):
    escrow.deposit(0, {'from': alice})

    assert escrow.epoch() == epoch


def test_withdraw_zero(alice, escrow, lp_token, epoch):
    escrow.withdraw(0, {'from': alice})

    assert escrow.epoch() == epoch
