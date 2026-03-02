:n = 4
:side = 50
:angle = 90
repeat 4 [
    if (:side > 30) [
        forward :side
        right :angle
        :side = :side - 5
    ] else [
        forward 10
        left :angle
    ]
]
