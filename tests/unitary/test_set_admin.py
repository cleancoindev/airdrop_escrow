import brownie


def test_deployer_is_initial_admin(alice, escrow):
    assert escrow.admin() == alice


def test_set_admin(alice, bob, escrow):
    escrow.set_admin(bob, {'from': alice})

    assert escrow.admin() == bob


def test_set_twice(alice, bob, charlie, escrow):
    escrow.set_admin(bob, {'from': alice})
    escrow.set_admin(charlie, {'from': bob})

    assert escrow.admin() == charlie


def test_admin_only(bob, escrow):
    with brownie.reverts("dev: admin only"):
        escrow.set_admin(bob, {'from': bob})
