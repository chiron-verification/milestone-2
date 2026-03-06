:threshold = 6
:cnt = 0
:running_sum = 0
:flag = 0
:draw_dist = 0
repeat 5 [
    :cnt = :cnt + 1
    :running_sum = :running_sum + :cnt
    if (:running_sum > :threshold) [
        :flag = :flag + 1
        pendown
        forward :cnt
        :draw_dist = :draw_dist + :cnt
    ] else [
        penup
    ]
]
:excess = :running_sum - :threshold
:flag_sq = :flag * :flag
:coverage = :draw_dist / 5
