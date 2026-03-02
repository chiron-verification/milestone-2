:x = 5
:y = 10
:z = 3
if ((:x < :y) && (:z > 0)) [
    forward :x
]
if ((:x == 5) || !(:y > 20)) [
    right :z
] else [
    left :y
]
