from acorn.utils import round_to_lot_size


def test_round_to_lot_size():
    assert round_to_lot_size(-0.29, 0.1) == -0.3
    assert round_to_lot_size(1.43243, 1) == 1
    assert round_to_lot_size(292, 10) == 290
    assert round_to_lot_size(292, 100) == 300

