:speed = 10
:accel = 3
:dist = 0
:count = 0
:peak = 0
repeat 4 [
    forward :speed
    :dist = :dist + :speed
    :speed = :speed + :accel
    :count = :count + 1
    if (:speed > :peak) [
        :peak = :speed
    ] else [
        :peak = :peak
    ]
]
:avg = :dist / 4
:total_accel = :accel * :count
:gap = :peak - :speed
