:x = 10
:y = 20
if (:x < :y) [
    forward 50
] else [
    backward 50
]
if (:x == :y) [
    left 90
] else [
    right 90
]
:z = :x + :y
if (:z > 25) [
    forward :z
] else [
    forward 10
]
