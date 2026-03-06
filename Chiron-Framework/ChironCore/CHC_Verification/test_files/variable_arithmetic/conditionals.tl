:p = 15
:q = 9
:r = 0
:s = 0
if (:p > :q) [
    :r = :p - :q
    :s = :r * :r
] else [
    :r = :q - :p
    :s = :r + :q
]
:t = :p + :q + :r
if (:s > 40) [
    :u = :s - 40
] else [
    :u = :s + 40
]
:v = :t + :u
:w = :v - :p
