:base = 30
:factor = 3
:angle_a = :base * :factor
:angle_b = :angle_a - :base
:angle_c = :base + :angle_b
:sum = :angle_a + :angle_b + :base
right :base
forward 50
right :angle_b
forward 50
left :angle_c
forward 50
:leftover = :sum - :angle_a
