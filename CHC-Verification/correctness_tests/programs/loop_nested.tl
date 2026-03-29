:x = 0
:acc = 0
repeat 4 [
  :x = :x + 3
  if (:x > 5) [
    :acc = :acc + :x
  ] else [
    :acc = :acc + 1
  ]
]
