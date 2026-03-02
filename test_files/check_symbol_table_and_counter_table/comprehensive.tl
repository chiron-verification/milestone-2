:x = 10
:y = 20
:z = :x + :y
if (:x < :y) [
    forward :z
] else [
    backward :x
]
penup
goto (:x, :y)
pendown
:w = :z * 2
if (!(:w == 60)) [
    right :w
]
repeat 3 [
    forward :x
    left 90
]
