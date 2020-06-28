import brownie
import pytest


@pytest.fixture(scope="module")
def epoch(alice, escrow, lp_token):
    lp_token._mint_for_testing(10**24, {'from': alice})
    lp_token.approve(escrow, 10**24, {'from': alice})
    escrow.deposit(10**18, {'from': alice})

    yield escrow.epoch()


def test_admin_only_enable_failsafe(alice, bob, escrow):
    with brownie.reverts("dev: admin only"):
        escrow.toggle_failsafe({'from': bob})

    escrow.toggle_failsafe({'from': alice})

    with brownie.reverts("dev: admin only"):
        escrow.toggle_failsafe({'from': bob})


def test_admin_only_disable_failsafe(alice, bob, escrow):
    escrow.toggle_failsafe({'from': alice})

    with brownie.reverts("dev: admin only"):
        escrow.toggle_failsafe({'from': bob})


def test_toggle_failsafe(alice, escrow):
    assert not escrow.failsafe()

    escrow.toggle_failsafe({'from': alice})
    assert escrow.failsafe()

    escrow.toggle_failsafe({'from': alice})
    assert not escrow.failsafe()


def test_transfer(alice, bob, escrow, lp_token, epoch):
    escrow.toggle_failsafe()
    escrow.transfer(bob, 10**18, {'from': alice})

    assert escrow.epoch() == epoch


def test_transferFrom(alice, bob, charlie, escrow, lp_token, epoch):
    escrow.toggle_failsafe()
    escrow.approve(charlie, 10**18, {'from': alice})
    escrow.transferFrom(alice, bob, 10**18, {'from': charlie})

    assert escrow.epoch() == epoch


def test_deposit(alice, escrow, lp_token, epoch):
    escrow.toggle_failsafe()
    escrow.deposit(10**18, {'from': alice})

    assert escrow.epoch() == epoch


def test_withdraw(alice, escrow, lp_token, epoch):
    escrow.toggle_failsafe()
    escrow.withdraw(10**18, {'from': alice})

    assert escrow.epoch() == epoch
