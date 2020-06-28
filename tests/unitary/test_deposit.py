import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def module_setup(accounts, escrow, lp_token):
    for i in range(2):
        lp_token._mint_for_testing(10**24, {'from': accounts[i]})
        lp_token.approve(escrow, 10**24, {'from': accounts[i]})


def test_initial_getter_amounts(alice, escrow, lp_token):
    assert lp_token.balanceOf(alice) == 10**24
    assert escrow.balanceOf(alice) == 0
    assert escrow.totalSupply() == 0


def test_deposit(alice, escrow, lp_token):
    balance = lp_token.balanceOf(alice)
    escrow.deposit(10**18, {'from': alice})

    assert lp_token.balanceOf(alice) == balance - 10**18
    assert escrow.balanceOf(alice) == 10**18
    assert escrow.totalSupply() == 10**18


def test_multiple_deposits(alice, escrow, lp_token):
    balance = lp_token.balanceOf(alice)
    escrow.deposit(31337, {'from': alice})
    escrow.deposit(42, {'from': alice})

    assert lp_token.balanceOf(alice) == balance - 31337 - 42
    assert escrow.balanceOf(alice) == 31337 + 42
    assert escrow.totalSupply() == 31337 + 42


def test_deposit_zero(alice, escrow, lp_token):
    balance = lp_token.balanceOf(alice)
    escrow.deposit(0, {'from': alice})

    assert lp_token.balanceOf(alice) == balance
    assert escrow.balanceOf(alice) == 0
    assert escrow.totalSupply() == 0


def test_deposit_all(alice, escrow, lp_token):
    balance = lp_token.balanceOf(alice)
    escrow.deposit(balance, {'from': alice})

    assert lp_token.balanceOf(alice) == 0
    assert escrow.balanceOf(alice) == balance
    assert escrow.totalSupply() == balance


def test_deposit_multiple_accounts(alice, bob, escrow, lp_token):
    balance1 = lp_token.balanceOf(alice)
    balance2 = lp_token.balanceOf(bob)

    escrow.deposit(5318008, {'from': alice})
    escrow.deposit(71077345, {'from': bob})

    assert lp_token.balanceOf(alice) == balance1 - 5318008
    assert escrow.balanceOf(alice) == 5318008

    assert lp_token.balanceOf(bob) == balance2 - 71077345
    assert escrow.balanceOf(bob) == 71077345

    assert escrow.totalSupply() == 5318008 + 71077345


def test_deposit_amount_too_large(alice, escrow, lp_token):
    balance = lp_token.balanceOf(alice)
    with brownie.reverts():
        escrow.deposit(balance + 1, {'from': alice})
