:a = 1
:b = 2
:c = 3
:d = 4
:e = 5
:f = 6
:g = 7
:h = 8
repeat 5 [
  :a = :a + 1
  :b = :b + :a
  :c = :c + :b
  :d = :d + :c
  :e = :e + :d
  :f = :f + :e
  :g = :g + :f
  :h = :h + :g
]
