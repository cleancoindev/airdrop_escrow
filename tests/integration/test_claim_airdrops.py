import pytest
from brownie.test import given, strategy
from hypothesis import settings, Phase


@pytest.fixture(scope="module", autouse=True)
def module_setup(accounts, escrow, lp_token, airdrop_token):
    for i in range(3):
        lp_token._mint_for_testing(10**24, {'from': accounts[i]})
        lp_token.approve(escrow, 10**24, {'from': accounts[i]})
    escrow.add_token(airdrop_token, {'from': accounts[0]})
    airdrop_token._mint_for_testing(10**24, {'from': accounts[3]})


@pytest.fixture(scope="module")
def airdrop_tokens(ERC20_Revert, accounts, airdrop_token, escrow):
    token_list = [airdrop_token]
    for i in range(2):
        token = ERC20_Revert.deploy("Airdrop", "AD", 18, {'from': accounts[0]})
        token._mint_for_testing(10**24, {'from': accounts[3]})
        escrow.add_token(token, {'from': accounts[0]})
        token_list.append(token)

    yield token_list


@given(
    st_deposits=strategy("uint256[3]", min_value=10**17, max_value=10**21, unique=True),
    st_airdrops=strategy("uint256[10]", min_value=10**10, max_value=10**18, unique=True)
)
@settings(max_examples=10, phases=[Phase.generate, Phase.target])
def test_many_airdrops_single_claim(accounts, rpc, escrow, airdrop_token, st_deposits, st_airdrops):
    """
    Verify correct claim amount from a single claim of many airdrops.
    """

    # initial deposits of `lp_token`
    total_deposited = sum(st_deposits)
    for i in range(3):
        escrow.deposit(st_deposits[i], {'from': accounts[i]})

    # ensure claims are in a new token epoch
    rpc.sleep(86400 * 7)

    # perform 10 airdrops
    for amount in st_airdrops:
        rpc.sleep(14)
        airdrop_token.transfer(escrow, amount, {'from': accounts[3]})
        escrow.checkpoint()

    # ensure claims are in a new token epoch
    rpc.sleep(86400 * 7)

    # claim the tokens
    received = [0, 0, 0]
    for i in range(3):
        escrow.claim(airdrop_token, {'from': accounts[i]})
        received[i] = airdrop_token.balanceOf(accounts[i])

    # total dust should be less than 1%
    assert 0.99 < sum(received) / sum(st_airdrops) <= 1

    # actual amounts received should be less than 1% off expected amounts
    for i in range(3):
        expected_pct = st_deposits[i] / total_deposited
        received_pct = received[i] / sum(received)
        assert abs(expected_pct - received_pct) < 0.01


@given(
    st_deposits=strategy("uint256[3]", min_value=10**17, max_value=10**21, unique=True),
    st_airdrops=strategy("uint256[10]", min_value=10**10, max_value=10**18, unique=True)
)
@settings(max_examples=10)
def test_many_airdrops_many_claims(accounts, rpc, escrow, airdrop_token, st_deposits, st_airdrops):
    """
    Verify correct claim amounts over multiple claims.
    """

    # make initial deposits of `lp_token`
    total_deposited = sum(st_deposits)
    for i in range(3):
        escrow.deposit(st_deposits[i], {'from': accounts[i]})

    for amount in st_airdrops:

        # ensure each claim is in a new token epoch
        rpc.sleep(86400 * 7)

        airdrop_token.transfer(escrow, amount, {'from': accounts[3]})

        received = [0, 0, 0]
        for i in range(3):
            balance = airdrop_token.balanceOf(accounts[i])
            escrow.claim(airdrop_token, {'from': accounts[i]})
            received[i] = airdrop_token.balanceOf(accounts[i]) - balance

        # dust should be less than 0.1%
        assert 0.999 < sum(received) / amount <= 1

        # actual amounts received should be less than 0.1% off expected amounts
        for i in range(3):
            expected_pct = st_deposits[i] / total_deposited
            received_pct = received[i] / sum(received)
            assert abs(expected_pct - received_pct) < 0.001


@given(
    st_deposits=strategy("uint256[3]", min_value=10**17, max_value=10**21, unique=True),
    st_airdrops=strategy("uint256[3][5]", min_value=10**10, max_value=10**18),
)
@settings(max_examples=10)
def test_multiple_airdrop_tokens(accounts, rpc, escrow, airdrop_tokens, st_deposits, st_airdrops):
    """
    Verify correct claim amount over multiple claims with several tokens.
    """

    # make initial deposits of `lp_token`
    total_deposited = sum(st_deposits)
    for i in range(3):
        escrow.deposit(st_deposits[i], {'from': accounts[i]})

    for amounts in st_airdrops:

        # ensure each claim is in a new token epoch
        rpc.sleep(86400 * 7)

        for i in range(3):
            airdrop_tokens[i].transfer(escrow, amounts[i], {'from': accounts[3]})
            escrow.checkpoint()

        for token, amount in zip(airdrop_tokens, amounts):
            received = [0, 0, 0]
            for i in range(3):
                balance = token.balanceOf(accounts[i])
                escrow.claim(token, {'from': accounts[i]})
                received[i] = token.balanceOf(accounts[i]) - balance

            # dust should be less than 0.1%
            assert 0.999 < sum(received) / amount <= 1

            # actual amounts received should be less than 0.1% off expected amounts
            for i in range(3):
                expected_pct = st_deposits[i] / total_deposited
                received_pct = received[i] / sum(received)
                assert abs(expected_pct - received_pct) < 0.001


@given(
    st_transfers=strategy("uint256[9]", min_value=10**17, max_value=10**18, unique=True),
    st_airdrops=strategy("uint256[9]", min_value=10**10, max_value=10**18, unique=True)
)
@settings(max_examples=10)
def test_claims_with_adjusted_deposits(
    accounts, rpc, alice, escrow, airdrop_token, st_transfers, st_airdrops
):
    """
    Verify correct amount over multiple claims, with changing `lp_token` balances.
    """

    # alice makes the only initial deposit
    escrow.deposit(10**19, {'from': alice})
    balances = [10**19]

    for receiver, transfer_amount, airdrop_amount in zip(accounts[1:], st_transfers, st_airdrops):

        # transfer a portion of alice's balance to another account
        rpc.sleep(1)
        escrow.transfer(receiver, transfer_amount, {'from': alice})
        balances[0] -= transfer_amount
        balances.append(transfer_amount)

        # perform an airdrop
        airdrop_token.transfer(escrow, airdrop_amount, {'from': accounts[3]})
        rpc.sleep(86400 * 7)

        # claim airdrop tokens
        received = []
        for i in range(len(balances)):
            balance = airdrop_token.balanceOf(accounts[i])
            escrow.claim(airdrop_token, {'from': accounts[i]})
            received.append(airdrop_token.balanceOf(accounts[i]) - balance)

        # dust should be less than 0.1%
        assert 0.999 < sum(received) / airdrop_amount <= 1

        # actual amounts received should be less than 0.1% off expected amounts
        for i in range(len(balances)):
            expected_pct = balances[i] / sum(balances)
            received_pct = received[i] / sum(received)
            assert abs(expected_pct - received_pct) < 0.001
