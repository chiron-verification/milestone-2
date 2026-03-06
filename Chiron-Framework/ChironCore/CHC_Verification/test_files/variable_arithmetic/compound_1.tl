:base = 6
:mult = 4
:limit = 30
:computed = :base * :mult
:delta = :limit - :computed
if (:computed > :limit) [
    :result = :computed - :limit
    forward :result
] else [
    :result = :limit - :computed
    backward :result
]
:final = :base + :result
:check = :final * 2
:excess = :check - :limit
