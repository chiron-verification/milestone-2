:x = 10
:y = 5
:total = 0
penup
goto (:x, :y)
pendown
repeat 3 [
    if ((:x > 0) && (:y > 0)) [
        forward :x
        right 90
        :total = :total + :x
    ] else [
        backward :y
        left 90
    ]
    :x = :x - 2
    repeat 2 [
        forward :y
        right :x
    ]
]
penup
goto (:total, 0)
pendown
if (!(:total == 0)) [
    forward :total
]
