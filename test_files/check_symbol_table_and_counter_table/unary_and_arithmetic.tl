:x = 10
:y = -5
:z = :x + :y
:w = :z * -1
:v = :w / 2
if (!(:v == 0)) [
    forward :v
] else [
    backward :w
]
:result = :x * :y + :z - :v
forward :result
