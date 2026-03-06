:n = 5
:acc = 0
:step = 2
:power = 1
:max_step = 0
repeat 5 [
    :acc = :acc + :step
    :power = :power * 2
    :step = :step + 1
    if (:step > :max_step) [
        :max_step = :step
    ] else [
        :max_step = :max_step
    ]
]
:result = :acc + :power
:scaled = :result / 5
