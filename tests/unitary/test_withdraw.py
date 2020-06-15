import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def module_setup(accounts, escrow, lp_token):
    for i in range(2):
        lp_token._mint_for_testing(10**24, {'from': accounts[i]})
        lp_token.approve(escrow, 10**24, {'from': accounts[i]})
        escrow.deposit(10**24, {'from': accounts[i]})


def test_initial_getter_amounts(accounts, escrow, lp_token):
    assert lp_token.balanceOf(accounts[0]) == 0
    assert escrow.balanceOf(accounts[0]) == 10**24
    assert escrow.totalSupply() == 10**24 * 2


def test_withdraw(accounts, escrow, lp_token):
    balance = escrow.balanceOf(accounts[0])
    total_supply = escrow.totalSupply()

    escrow.withdraw(10**18, {'from': accounts[0]})

    assert lp_token.balanceOf(accounts[0]) == 10**18
    assert escrow.balanceOf(accounts[0]) == balance - 10**18
    assert escrow.totalSupply() == total_supply - 10**18


def test_multiple_withdraw(accounts, escrow, lp_token):
    balance = escrow.balanceOf(accounts[0])
    total_supply = escrow.totalSupply()

    escrow.withdraw(31337, {'from': accounts[0]})
    escrow.withdraw(42, {'from': accounts[0]})

    assert lp_token.balanceOf(accounts[0]) == 31337 + 42
    assert escrow.balanceOf(accounts[0]) == balance - 31337 - 42
    assert escrow.totalSupply() == total_supply - 31337 - 42


def test_withdraw_zero(accounts, escrow, lp_token):
    balance = escrow.balanceOf(accounts[0])
    total_supply = escrow.totalSupply()
    escrow.withdraw(0, {'from': accounts[0]})

    assert lp_token.balanceOf(accounts[0]) == 0
    assert escrow.balanceOf(accounts[0]) == balance
    assert escrow.totalSupply() == total_supply


def test_withdraw_zero_balance_zero(accounts, escrow, lp_token):
    total_supply = escrow.totalSupply()
    escrow.withdraw(0, {'from': accounts[2]})

    assert lp_token.balanceOf(accounts[2]) == 0
    assert escrow.balanceOf(accounts[2]) == 0
    assert escrow.totalSupply() == total_supply


def test_withdraw_all(accounts, escrow, lp_token):
    balance = escrow.balanceOf(accounts[0])
    total_supply = escrow.totalSupply()
    escrow.withdraw(balance, {'from': accounts[0]})

    assert lp_token.balanceOf(accounts[0]) == balance
    assert escrow.balanceOf(accounts[0]) == 0
    assert escrow.totalSupply() == total_supply - balance


def test_deposit_multiple_accounts(accounts, escrow, lp_token):
    balance1 = escrow.balanceOf(accounts[0])
    balance2 = escrow.balanceOf(accounts[1])
    total_supply = escrow.totalSupply()

    escrow.withdraw(5318008, {'from': accounts[0]})
    escrow.withdraw(71077345, {'from': accounts[1]})

    assert lp_token.balanceOf(accounts[0]) == 5318008
    assert escrow.balanceOf(accounts[0]) == balance1 - 5318008

    assert lp_token.balanceOf(accounts[1]) == 71077345
    assert escrow.balanceOf(accounts[1]) == balance2 - 71077345

    assert escrow.totalSupply() == total_supply - 5318008 - 71077345


def test_withdraw_amount_too_large(accounts, escrow, lp_token):
    balance = escrow.balanceOf(accounts[0])
    with brownie.reverts():
        escrow.withdraw(balance + 1, {'from': accounts[0]})
