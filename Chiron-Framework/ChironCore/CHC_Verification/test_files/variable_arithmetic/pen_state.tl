:r = 8
:r_sq = :r * :r
:side = :r + 12
:perimeter = :side * 4
:half_p = :perimeter / 2
pendown
forward :side
penup
forward :half_p
pendown
forward :r
:remainder = :perimeter - :side - :r
:ratio = :side / :r
