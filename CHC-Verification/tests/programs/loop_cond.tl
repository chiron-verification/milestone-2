:x = 0
:y = 100
repeat 5 [
  if (:x < 30) [
    :x = :x + 10
  ] else [
    :x = :x + 5
  ]
  :y = :y - :x
]
