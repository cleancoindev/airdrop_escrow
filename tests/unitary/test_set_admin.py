import brownie


def test_deployer_is_initial_admin(accounts, escrow):
    assert escrow.admin() == accounts[0]


def test_set_admin(accounts, escrow):
    escrow.set_admin(accounts[1], {'from': accounts[0]})

    assert escrow.admin() == accounts[1]


def test_set_twice(accounts, escrow):
    escrow.set_admin(accounts[1], {'from': accounts[0]})
    escrow.set_admin(accounts[2], {'from': accounts[1]})

    assert escrow.admin() == accounts[2]


def test_admin_only(accounts, escrow):
    with brownie.reverts("dev: admin only"):
        escrow.set_admin(accounts[1], {'from': accounts[1]})
