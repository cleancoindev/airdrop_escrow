import pytest


@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


@pytest.fixture(scope="module")
def lp_token(ERC20_Revert, accounts):
    yield ERC20_Revert.deploy("LP Token", "LP", 18, {'from': accounts[0]})


@pytest.fixture(scope="module")
def escrow(AirdropEscrow, accounts, lp_token):
    yield AirdropEscrow.deploy("Airdrop Escrow", "AIR", lp_token, {'from': accounts[0]})
