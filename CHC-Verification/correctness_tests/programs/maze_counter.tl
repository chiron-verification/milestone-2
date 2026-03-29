:a = 0
:b = 1
:x = 0
:y = 0
repeat 6 [
  :a = :a + :b
  if (:a > 6) [
    :x = :x + :a
    :y = :y + 2
  ] else [
    :x = :x + :b
    :y = :y + 1
  ]
  :b = :b + 1
]
